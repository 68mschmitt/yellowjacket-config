/* SPDX-License-Identifier: MIT */
#include <stdio.h>
#include <string.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/bluetooth/conn.h>
#include <lvgl.h>
#include <zmk/event_manager.h>
#include <zmk/events/position_state_changed.h>
#include <zmk/split/central.h>
#include <zmk/keymap.h>
#include <zmk/endpoints.h>
#include <zmk/ble.h>
#include <zmk/usb.h>
#include <zmk/wpm.h>
#if IS_ENABLED(CONFIG_PINCHWING_DISPLAY_DIAGNOSTICS)
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(pinchwing_display, LOG_LEVEL_INF);
#endif
#if IS_ENABLED(CONFIG_SHIELD_PINCHWING_ROUND)
#include "pinchwing_pet.h"
#include <pinchwing_dpi.h>
#include <pinchwing_power.h>
static lv_obj_t *dpi_label;
#endif

/* BLE slots are assigned by pairing order, not handedness. Learn each side
 * from an actual key position. Atomics bridge event and display threads. */
static atomic_t side_by_source[2];
static const uint32_t positions[] = DT_PROP(DT_NODELABEL(default_transform), map);

static int identify_half(const zmk_event_t *eh) {
    const struct zmk_position_state_changed *ev = as_zmk_position_state_changed(eh);
    if (ev && ev->source < ARRAY_SIZE(side_by_source) &&
        ev->position < ARRAY_SIZE(positions)) {
        /* Matrix-transform entries encode the column in the low byte. */
        atomic_set(&side_by_source[ev->source], (positions[ev->position] & 0xff) < 16 ? 1 : 2);
#if IS_ENABLED(CONFIG_SHIELD_PINCHWING_ROUND)
        if (ev->state) {
            pinchwing_pet_press((positions[ev->position] & 0xff) < 16 ? 0 : 1);
        }
#endif
    }
    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(pinchwing_display_side, identify_half);
ZMK_SUBSCRIPTION(pinchwing_display_side, zmk_position_state_changed);

static lv_obj_t *layer_label, *wpm_label, *output_label, *links_label;
static lv_obj_t *battery_labels[2];

static void set_text(lv_obj_t *label, const char *text) {
    if (strcmp(lv_label_get_text(label), text) != 0) {
        lv_label_set_text(label, text);
    }
}

static void count_split_links(struct bt_conn *conn, void *user_data) {
    struct bt_conn_info info;
    if (bt_conn_get_info(conn, &info) == 0 && info.type == BT_CONN_TYPE_LE &&
        info.role == BT_CONN_ROLE_CENTRAL && info.state == BT_CONN_STATE_CONNECTED) {
        (*(unsigned int *)user_data)++;
    }
}

/* LVGL runs this on the dedicated display queue; no UI calls in BLE callbacks.
 * Only changed labels are invalidated, limiting SPI traffic while typing. */
static void refresh(lv_timer_t *timer) {
    char text[80];
    zmk_keymap_layer_index_t index = zmk_keymap_highest_layer_active();
    const char *name = zmk_keymap_layer_name(zmk_keymap_layer_index_to_id(index));
    if (IS_ENABLED(CONFIG_SHIELD_PINCHWING_ROUND) && name && name[0]) {
        snprintf(text, sizeof(text), "%s", name);
    } else {
        snprintf(text, sizeof(text), "Layer %u  %s", (unsigned int)index, name ? name : "");
    }
    set_text(layer_label, text);
    snprintf(text, sizeof(text), "%u WPM", (unsigned int)zmk_wpm_get_state());
    set_text(wpm_label, text);
#if IS_ENABLED(CONFIG_SHIELD_PINCHWING_ROUND)
    uint16_t dpi = pinchwing_dpi_get();
    if (dpi) {
        snprintf(text, sizeof(text), "%u DPI", dpi);
    } else {
        snprintf(text, sizeof(text), "-- DPI");
    }
    set_text(dpi_label, text);
#endif

    struct zmk_endpoint_instance endpoint = zmk_endpoint_get_selected();
    if (endpoint.transport == ZMK_TRANSPORT_USB) {
        snprintf(text, sizeof(text), "USB  %s",
                 zmk_usb_get_conn_state() == ZMK_USB_CONN_HID ? "ready" : "waiting");
    } else {
        snprintf(text, sizeof(text), "BLE %d  %s", zmk_ble_active_profile_index() + 1,
                 zmk_ble_active_profile_is_connected() ? "connected" : "waiting");
    }
    set_text(output_label, text);

    unsigned int links = 0;
    bt_conn_foreach(BT_CONN_TYPE_LE, count_split_links, &links);
    snprintf(text, sizeof(text), IS_ENABLED(CONFIG_SHIELD_PINCHWING_ROUND) ?
             "%u/2 linked" : "Halves: %u/2 linked", links);
    set_text(links_label, text);

#if IS_ENABLED(CONFIG_SHIELD_PINCHWING_ROUND)
    /* Power reports identify physical sides without a keypress.
     * A USB report intentionally contains no battery percentage. */
    for (unsigned int side = 0; side < 2; side++) {
        int power = pinchwing_power_get(side);
        if (power == PINCHWING_POWER_USB) {
            snprintf(text, sizeof(text), LV_SYMBOL_CHARGE);
        } else if (power >= 0 && power <= 100) {
            snprintf(text, sizeof(text), "%d%%", power);
        } else {
            snprintf(text, sizeof(text), "--");
        }
        set_text(battery_labels[side], text);
    }
    return;
#endif

    for (int source = 0; source < 2; source++) {
        uint8_t level = 0;
        int side = atomic_get(&side_by_source[source]);
        const char *label = side == 1 ? "Left" : side == 2 ? "Right" :
                            source == 0 ? "Half 1" : "Half 2";
        zmk_split_central_get_peripheral_battery_level(source, &level);
        /* ZMK uses zero for both unknown and disconnected battery slots. */
        if (level > 0 && level <= 100) {
            snprintf(text, sizeof(text), "%s battery: %u%%", label, level);
        } else {
            snprintf(text, sizeof(text), "%s battery: --", label);
        }
        set_text(battery_labels[source], text);
    }
}

static lv_obj_t *label_at(lv_obj_t *screen, int x, int y, int width,
                          const lv_font_t *font, const char *text) {
    lv_obj_t *label = lv_label_create(screen);
    lv_obj_set_pos(label, x, y);
    lv_obj_set_width(label, width);
    lv_label_set_long_mode(label, LV_LABEL_LONG_CLIP);
    lv_obj_set_style_text_font(label, font, 0);
    if (IS_ENABLED(CONFIG_SHIELD_PINCHWING_ROUND)) {
        lv_obj_set_style_text_color(label, lv_color_white(), 0);
        lv_obj_set_style_text_align(label, LV_TEXT_ALIGN_CENTER, 0);
    } else {
        lv_obj_set_style_text_color(label, lv_color_black(), 0);
    }
    lv_label_set_text(label, text);
    return label;
}

lv_obj_t *zmk_display_status_screen(void) {
#if IS_ENABLED(CONFIG_PINCHWING_DISPLAY_DIAGNOSTICS)
    LOG_INF("Waiting 10 seconds before display startup; USB input can start now");
    k_sleep(K_SECONDS(10));
    LOG_INF("Creating status screen");
#endif
    lv_obj_t *screen = lv_obj_create(NULL);
    lv_obj_set_style_bg_color(screen, IS_ENABLED(CONFIG_SHIELD_PINCHWING_ROUND)
                                         ? lv_color_black() : lv_color_white(), 0);
    lv_obj_set_style_bg_opa(screen, LV_OPA_COVER, 0);
    lv_obj_set_style_pad_all(screen, 0, 0);
    lv_obj_set_style_border_width(screen, 0, 0);
    lv_obj_remove_flag(screen, LV_OBJ_FLAG_SCROLLABLE);

    if (IS_ENABLED(CONFIG_SHIELD_PINCHWING_ROUND)) {
#if IS_ENABLED(CONFIG_SHIELD_PINCHWING_ROUND)
        lv_obj_set_style_bg_color(screen, lv_color_hex(0x07101c), 0);
        pinchwing_pet_create(screen);
#if IS_ENABLED(CONFIG_PINCHWING_DISPLAY_DIAGNOSTICS)
        LOG_INF("Cat and animation timer created; creating status labels");
#endif
        layer_label = label_at(screen, 45, 15, 150, &lv_font_montserrat_14, "");
        lv_obj_set_style_text_color(layer_label, lv_color_hex(0x55ddff), 0);
        wpm_label = label_at(screen, 45, 34, 150, &lv_font_montserrat_20, "");
        dpi_label = label_at(screen, 45, 58, 150, &lv_font_montserrat_14, "");
        lv_obj_set_style_text_color(dpi_label, lv_color_hex(0x55ddff), 0);
        output_label = label_at(screen, 25, 75, 110, &lv_font_montserrat_14, "");
        links_label = label_at(screen, 135, 75, 80, &lv_font_montserrat_14, "");
        battery_labels[0] = label_at(screen, 50, 211, 70, &lv_font_montserrat_14, "");
        battery_labels[1] = label_at(screen, 120, 211, 70, &lv_font_montserrat_14, "");
#endif
    } else {
        label_at(screen, 12, 10, 240, &lv_font_montserrat_28, "PINCHWING");
        wpm_label = label_at(screen, 265, 14, 130, &lv_font_montserrat_20, "");
        layer_label = label_at(screen, 12, 55, 376, &lv_font_montserrat_28, "");
        output_label = label_at(screen, 12, 102, 190, &lv_font_montserrat_20, "");
        links_label = label_at(screen, 205, 102, 190, &lv_font_montserrat_20, "");
        battery_labels[0] = label_at(screen, 12, 145, 376, &lv_font_montserrat_20, "");
        battery_labels[1] = label_at(screen, 12, 176, 376, &lv_font_montserrat_20, "");
        label_at(screen, 12, 215, 376, &lv_font_montserrat_14,
                 "Press a key on each half to identify left / right");
    }
    refresh(NULL);
    lv_timer_create(refresh, 250, NULL);
#if IS_ENABLED(CONFIG_PINCHWING_DISPLAY_DIAGNOSTICS)
    LOG_INF("Status screen ready for first render");
#endif
    return screen;
}
