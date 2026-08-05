/* Minimal Zephyr/ZMK stubs so behavior_dynamic_macro.c can be compiled and
 * exercised on the host. Only enough surface to run the state machine. */
#pragma once

#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdio.h>
#include <errno.h>

/* ---- Kconfig ---- */
#define CONFIG_ZMK_BEHAVIOR_DYNAMIC_MACRO_MAX_SLOTS 2
#define CONFIG_ZMK_BEHAVIOR_DYNAMIC_MACRO_MAX_EVENTS 16 /* small, to test overflow */
#define CONFIG_ZMK_BEHAVIOR_DYNAMIC_MACRO_MAX_HELD 4
#define CONFIG_ZMK_BEHAVIOR_DYNAMIC_MACRO_TAP_DELAY 20
#define CONFIG_ZMK_LOG_LEVEL 4
#define CONFIG_KERNEL_INIT_PRIORITY_DEFAULT 40

#define IS_ENABLED(x) 0 /* disables the metadata block */
#define DT_HAS_COMPAT_STATUS_OKAY(x) 1
#define ARG_UNUSED(x) (void)(x)
#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))

/* ---- logging ---- */
#define LOG_MODULE_DECLARE(...)
extern int g_warn_count;
#define LOG_DBG(...)                                                                               \
    do {                                                                                           \
        printf("  [dbg] ");                                                                        \
        printf(__VA_ARGS__);                                                                        \
        printf("\n");                                                                              \
    } while (0)
#define LOG_WRN(...)                                                                               \
    do {                                                                                           \
        g_warn_count++;                                                                            \
        printf("  [wrn] ");                                                                        \
        printf(__VA_ARGS__);                                                                        \
        printf("\n");                                                                              \
    } while (0)
#define LOG_ERR(...)                                                                               \
    do {                                                                                           \
        printf("  [err] ");                                                                        \
        printf(__VA_ARGS__);                                                                        \
        printf("\n");                                                                              \
    } while (0)

/* ---- kernel ---- */
struct k_timer {
    int running;
};
struct k_work {
    int dummy;
};
typedef struct {
    int ms;
} k_timeout_t;
#define K_NO_WAIT ((k_timeout_t){0})
#define K_MSEC(x) ((k_timeout_t){(x)})

#define K_TIMER_DEFINE(name, expiry, stop) static struct k_timer name
#define K_WORK_DEFINE(name, handler) static struct k_work name

static inline void k_timer_start(struct k_timer *t, k_timeout_t a, k_timeout_t b) {
    (void)a;
    (void)b;
    t->running = 1;
}
static inline void k_timer_stop(struct k_timer *t) { t->running = 0; }

extern int g_work_submits;
static inline void k_work_submit(struct k_work *w) {
    (void)w;
    g_work_submits++;
}
static inline int64_t k_uptime_get(void) { return 1000; }

/* ---- ZMK events ---- */
#define HID_USAGE_KEY 0x07
struct zmk_keycode_state_changed {
    uint16_t usage_page;
    uint32_t keycode;
    uint8_t implicit_modifiers;
    uint8_t explicit_modifiers;
    bool state;
    int64_t timestamp;
};
typedef struct zmk_keycode_state_changed zmk_event_t;
#define ZMK_EV_EVENT_BUBBLE 0
static inline const struct zmk_keycode_state_changed *
as_zmk_keycode_state_changed(const zmk_event_t *eh) {
    return eh;
}

/* Captures what playback emitted to the "host". */
#define MAX_OUT 256
extern struct zmk_keycode_state_changed g_out[MAX_OUT];
extern int g_out_len;
int raise_zmk_keycode_state_changed(struct zmk_keycode_state_changed ev);

#define ZMK_LISTENER(a, b)
#define ZMK_SUBSCRIPTION(a, b)

/* ---- behaviors ---- */
#define ZMK_BEHAVIOR_OPAQUE 0
struct device {
    void *data;
};
struct zmk_behavior_binding {
    const char *behavior_dev;
    uint32_t param1;
    uint32_t param2;
};
struct zmk_behavior_binding_event {
    int layer;
    uint32_t position;
    int64_t timestamp;
};
struct behavior_driver_api {
    int (*binding_pressed)(struct zmk_behavior_binding *, struct zmk_behavior_binding_event);
    int (*binding_released)(struct zmk_behavior_binding *, struct zmk_behavior_binding_event);
};
#define BEHAVIOR_DT_INST_DEFINE(inst, init, pm, data, cfg, lvl, prio, api)                         \
    static int (*const unused_init_##inst)(const struct device *) = init
