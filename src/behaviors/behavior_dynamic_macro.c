/*
 * Copyright (c) 2024 The ZMK Contributors
 *
 * SPDX-License-Identifier: MIT
 *
 * Dynamic (runtime-recordable) macro behavior.
 *
 * Derived from the approach in zmkfirmware/zmk#2678 (calvinhenderson), with
 * substantial hardening:
 *   - at most one slot may record at a time; DM_STP stops whichever slot is
 *     recording (its slot parameter is ignored), so a single "recording" layer
 *     works for any number of registers
 *   - events raised by playback are never captured back into a recording
 *   - stopping a recording appends synthetic releases for any still-held keys,
 *     so playback can never leave a key or modifier logically stuck
 *   - recording auto-stops (with balancing releases) before the buffer fills,
 *     rather than silently dropping a release
 *   - a new record/play request is rejected while playback is running, so the
 *     playback cursor can never reference mutated slot data
 *   - compact 12-byte event storage instead of storing whole ZMK events
 */

#define DT_DRV_COMPAT zmk_behavior_dynamic_macro

#include <string.h>

#include <zephyr/device.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include <drivers/behavior.h>
#include <zmk/behavior.h>
#include <zmk/event_manager.h>
#include <zmk/events/keycode_state_changed.h>

#include <dt-bindings/zmk/dynamic_macro.h>

LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

#if DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT)

#define DM_MAX_SLOTS CONFIG_ZMK_BEHAVIOR_DYNAMIC_MACRO_MAX_SLOTS
#define DM_MAX_EVENTS CONFIG_ZMK_BEHAVIOR_DYNAMIC_MACRO_MAX_EVENTS
#define DM_MAX_HELD CONFIG_ZMK_BEHAVIOR_DYNAMIC_MACRO_MAX_HELD
#define DM_TAP_DELAY CONFIG_ZMK_BEHAVIOR_DYNAMIC_MACRO_TAP_DELAY

enum dm_slot_state {
    DM_SLOT_IDLE = 0,
    DM_SLOT_RECORDING,
    DM_SLOT_PLAYING,
};

/* Compact recorded event. Timestamps are not retained; playback uses a fixed
 * inter-event delay of DM_TAP_DELAY milliseconds. */
struct dm_event {
    uint32_t keycode;
    uint16_t usage_page;
    uint8_t implicit_modifiers;
    uint8_t explicit_modifiers;
    bool state;
};

struct dm_held {
    uint32_t keycode;
    uint16_t usage_page;
};

struct dm_slot {
    enum dm_slot_state state;
    uint32_t event_count;
    uint32_t play_index;
    uint8_t held_count;
    struct dm_held held[DM_MAX_HELD];
    struct dm_event events[DM_MAX_EVENTS];
};

struct dm_data {
    struct dm_slot slots[DM_MAX_SLOTS];
    /* Set only while this driver is re-raising a recorded event, so that the
     * recording listener cannot capture our own playback output. */
    bool in_playback;
};

static struct dm_data dynamic_macro_data;

static void dm_timer_expiry(struct k_timer *timer);
K_TIMER_DEFINE(dm_play_timer, dm_timer_expiry, NULL);

/* ------------------------------------------------------------------------- */
/* held-key bookkeeping                                                      */
/* ------------------------------------------------------------------------- */

static int dm_held_find(const struct dm_slot *slot, uint16_t usage_page, uint32_t keycode) {
    for (int i = 0; i < slot->held_count; i++) {
        if (slot->held[i].usage_page == usage_page && slot->held[i].keycode == keycode) {
            return i;
        }
    }
    return -1;
}

static void dm_held_remove(struct dm_slot *slot, int index) {
    for (int i = index; i + 1 < slot->held_count; i++) {
        slot->held[i] = slot->held[i + 1];
    }
    slot->held_count--;
}

/* ------------------------------------------------------------------------- */
/* recording                                                                 */
/* ------------------------------------------------------------------------- */

static bool dm_append(struct dm_slot *slot, const struct dm_event *ev) {
    if (slot->event_count >= DM_MAX_EVENTS) {
        return false;
    }
    slot->events[slot->event_count++] = *ev;
    return true;
}

/* Append a release for every key still logically held, most-recent first, so
 * that a recording is always balanced and playback cannot strand a modifier. */
static void dm_balance(struct dm_slot *slot, int slot_index) {
    while (slot->held_count > 0) {
        const struct dm_held *h = &slot->held[slot->held_count - 1];
        struct dm_event rel = {
            .keycode = h->keycode,
            .usage_page = h->usage_page,
            .implicit_modifiers = 0,
            .explicit_modifiers = 0,
            .state = false,
        };
        if (!dm_append(slot, &rel)) {
            LOG_WRN("dynamic macro %d: no room to balance %d held key(s); slot cleared to stay safe",
                    slot_index, slot->held_count);
            slot->event_count = 0;
            slot->held_count = 0;
            return;
        }
        slot->held_count--;
    }
}

static void dm_stop_slot(struct dm_slot *slot, int slot_index) {
    if (slot->state != DM_SLOT_RECORDING) {
        return;
    }
    slot->state = DM_SLOT_IDLE;
    dm_balance(slot, slot_index);
    LOG_DBG("dynamic macro %d: stopped recording, %u event(s)", slot_index, slot->event_count);
}

/* Stop whichever slot is recording. Returns the slot index, or -1 if none. */
static int dm_stop_active(struct dm_data *data) {
    for (int i = 0; i < DM_MAX_SLOTS; i++) {
        if (data->slots[i].state == DM_SLOT_RECORDING) {
            dm_stop_slot(&data->slots[i], i);
            return i;
        }
    }
    return -1;
}

static bool dm_any_playing(const struct dm_data *data) {
    for (int i = 0; i < DM_MAX_SLOTS; i++) {
        if (data->slots[i].state == DM_SLOT_PLAYING) {
            return true;
        }
    }
    return false;
}

static void dm_record(struct dm_data *data, int slot_index) {
    if (dm_any_playing(data)) {
        LOG_WRN("dynamic macro: refusing to record while playback is running");
        return;
    }

    /* Enforce the single-recording invariant: DM_STP does not need to know the
     * slot, which is what lets one "recording" layer serve every register. */
    dm_stop_active(data);

    struct dm_slot *slot = &data->slots[slot_index];
    slot->state = DM_SLOT_RECORDING;
    slot->event_count = 0;
    slot->play_index = 0;
    slot->held_count = 0;
    LOG_DBG("dynamic macro %d: recording", slot_index);
}

static void dm_play(struct dm_data *data, int slot_index) {
    struct dm_slot *slot = &data->slots[slot_index];

    if (slot->state == DM_SLOT_RECORDING) {
        LOG_WRN("dynamic macro %d: refusing to play a slot that is recording", slot_index);
        return;
    }
    if (dm_any_playing(data)) {
        LOG_WRN("dynamic macro: playback already running, ignoring request");
        return;
    }
    if (slot->event_count == 0) {
        LOG_DBG("dynamic macro %d: empty, nothing to play", slot_index);
        return;
    }

    slot->state = DM_SLOT_PLAYING;
    slot->play_index = 0;
    LOG_DBG("dynamic macro %d: playing %u event(s)", slot_index, slot->event_count);
    k_timer_start(&dm_play_timer, K_NO_WAIT, K_MSEC(DM_TAP_DELAY));
}

/* ------------------------------------------------------------------------- */
/* playback                                                                  */
/* ------------------------------------------------------------------------- */

static void dm_play_work_handler(struct k_work *work) {
    ARG_UNUSED(work);
    struct dm_data *data = &dynamic_macro_data;
    bool progressed = false;

    for (int i = 0; i < DM_MAX_SLOTS; i++) {
        struct dm_slot *slot = &data->slots[i];

        if (slot->state != DM_SLOT_PLAYING) {
            continue;
        }

        /* Defensive bounds check: play_index must always be inside the buffer. */
        if (slot->play_index >= slot->event_count || slot->play_index >= DM_MAX_EVENTS) {
            slot->state = DM_SLOT_IDLE;
            slot->play_index = 0;
            continue;
        }

        const struct dm_event *ev = &slot->events[slot->play_index++];
        struct zmk_keycode_state_changed out = {
            .usage_page = ev->usage_page,
            .keycode = ev->keycode,
            .implicit_modifiers = ev->implicit_modifiers,
            .explicit_modifiers = ev->explicit_modifiers,
            .state = ev->state,
            .timestamp = k_uptime_get(),
        };

        data->in_playback = true;
        raise_zmk_keycode_state_changed(out);
        data->in_playback = false;

        if (slot->play_index >= slot->event_count) {
            slot->state = DM_SLOT_IDLE;
            slot->play_index = 0;
            LOG_DBG("dynamic macro %d: playback complete", i);
        } else {
            progressed = true;
        }
    }

    if (!progressed) {
        k_timer_stop(&dm_play_timer);
    }
}

K_WORK_DEFINE(dm_play_work, dm_play_work_handler);

static void dm_timer_expiry(struct k_timer *timer) {
    ARG_UNUSED(timer);
    k_work_submit(&dm_play_work);
}

/* ------------------------------------------------------------------------- */
/* event listener                                                            */
/* ------------------------------------------------------------------------- */

static int dm_keycode_listener(const zmk_event_t *eh) {
    const struct zmk_keycode_state_changed *ev = as_zmk_keycode_state_changed(eh);
    struct dm_data *data = &dynamic_macro_data;

    if (ev == NULL || data->in_playback) {
        return ZMK_EV_EVENT_BUBBLE;
    }

    for (int i = 0; i < DM_MAX_SLOTS; i++) {
        struct dm_slot *slot = &data->slots[i];
        if (slot->state != DM_SLOT_RECORDING) {
            continue;
        }

        struct dm_event rec = {
            .keycode = ev->keycode,
            .usage_page = ev->usage_page,
            .implicit_modifiers = ev->implicit_modifiers,
            .explicit_modifiers = ev->explicit_modifiers,
            .state = ev->state,
        };

        /* Leave enough headroom that stopping can always balance held keys. */
        if (slot->event_count + slot->held_count + 1 >= DM_MAX_EVENTS) {
            LOG_WRN("dynamic macro %d: buffer full at %u event(s), auto-stopping", i,
                    slot->event_count);
            dm_stop_slot(slot, i);
            continue;
        }

        int held_idx = dm_held_find(slot, rec.usage_page, rec.keycode);

        if (rec.state) {
            if (held_idx < 0) {
                if (slot->held_count >= DM_MAX_HELD) {
                    LOG_WRN("dynamic macro %d: more than %d keys held, auto-stopping", i,
                            DM_MAX_HELD);
                    dm_stop_slot(slot, i);
                    continue;
                }
                slot->held[slot->held_count].usage_page = rec.usage_page;
                slot->held[slot->held_count].keycode = rec.keycode;
                slot->held_count++;
            }
        } else if (held_idx >= 0) {
            dm_held_remove(slot, held_idx);
        }

        dm_append(slot, &rec);
    }

    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(behavior_dynamic_macro, dm_keycode_listener);
ZMK_SUBSCRIPTION(behavior_dynamic_macro, zmk_keycode_state_changed);

/* ------------------------------------------------------------------------- */
/* behavior driver                                                           */
/* ------------------------------------------------------------------------- */

static int on_keymap_binding_pressed(struct zmk_behavior_binding *binding,
                                     struct zmk_behavior_binding_event event) {
    ARG_UNUSED(event);
    struct dm_data *data = &dynamic_macro_data;
    const uint32_t slot_index = binding->param2;

    if (slot_index >= DM_MAX_SLOTS) {
        LOG_ERR("dynamic macro: slot %u out of range (max %d); raise "
                "CONFIG_ZMK_BEHAVIOR_DYNAMIC_MACRO_MAX_SLOTS",
                slot_index, DM_MAX_SLOTS);
        return ZMK_BEHAVIOR_OPAQUE;
    }

    switch (binding->param1) {
    case DM_REC_CMD:
        dm_record(data, slot_index);
        break;
    case DM_PLY_CMD:
        dm_play(data, slot_index);
        break;
    case DM_STP_CMD:
        /* The slot parameter is intentionally ignored: only one slot can be
         * recording, so a single stop binding serves every register. */
        if (dm_stop_active(data) < 0) {
            LOG_DBG("dynamic macro: stop requested but nothing was recording");
        }
        break;
    default:
        LOG_ERR("dynamic macro: unknown command %u", binding->param1);
        return -ENOTSUP;
    }

    return ZMK_BEHAVIOR_OPAQUE;
}

static int on_keymap_binding_released(struct zmk_behavior_binding *binding,
                                      struct zmk_behavior_binding_event event) {
    ARG_UNUSED(binding);
    ARG_UNUSED(event);
    return ZMK_BEHAVIOR_OPAQUE;
}

#if IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)

static const struct behavior_parameter_value_metadata dm_cmd_values[] = {
    {
        .display_name = "Record",
        .type = BEHAVIOR_PARAMETER_VALUE_TYPE_VALUE,
        .value = DM_REC_CMD,
    },
    {
        .display_name = "Play",
        .type = BEHAVIOR_PARAMETER_VALUE_TYPE_VALUE,
        .value = DM_PLY_CMD,
    },
    {
        .display_name = "Stop recording",
        .type = BEHAVIOR_PARAMETER_VALUE_TYPE_VALUE,
        .value = DM_STP_CMD,
    },
};

static const struct behavior_parameter_value_metadata dm_slot_values[] = {
    {
        .display_name = "Slot",
        .type = BEHAVIOR_PARAMETER_VALUE_TYPE_RANGE,
        .range = {.min = 0, .max = DM_MAX_SLOTS - 1},
    },
};

static const struct behavior_parameter_metadata_set dm_metadata_set = {
    .param1_values = dm_cmd_values,
    .param1_values_len = ARRAY_SIZE(dm_cmd_values),
    .param2_values = dm_slot_values,
    .param2_values_len = ARRAY_SIZE(dm_slot_values),
};

static const struct behavior_parameter_metadata_set dm_metadata_sets[] = {dm_metadata_set};

static const struct behavior_parameter_metadata dm_metadata = {
    .sets_len = ARRAY_SIZE(dm_metadata_sets),
    .sets = dm_metadata_sets,
};

#endif // IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)

static const struct behavior_driver_api behavior_dynamic_macro_driver_api = {
    .binding_pressed = on_keymap_binding_pressed,
    .binding_released = on_keymap_binding_released,
#if IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)
    .parameter_metadata = &dm_metadata,
#endif // IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)
};

static int behavior_dynamic_macro_init(const struct device *dev) {
    ARG_UNUSED(dev);
    memset(&dynamic_macro_data, 0, sizeof(dynamic_macro_data));
    return 0;
}

BEHAVIOR_DT_INST_DEFINE(0, behavior_dynamic_macro_init, NULL, &dynamic_macro_data, NULL, POST_KERNEL,
                        CONFIG_KERNEL_INIT_PRIORITY_DEFAULT, &behavior_dynamic_macro_driver_api);

#endif /* DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT) */
