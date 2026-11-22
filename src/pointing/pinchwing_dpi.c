/* SPDX-License-Identifier: MIT */
#include <zephyr/device.h>
#include <zephyr/input/input.h>
#include <zephyr/kernel.h>
#include <pinchwing_dpi.h>

#if IS_ENABLED(CONFIG_SHIELD_PINCHWING_DONGLE_RIGHT)

#include <string.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/init.h>
#include <zephyr/logging/log.h>
#include <zephyr/settings/settings.h>
#include <zmk/split/peripheral.h>
#include "pmw3610.h"

LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

#define DPI_SAVE_DELAY_MS 1000

static const struct device *sensor = DEVICE_DT_GET(DT_NODELABEL(mouse_sensor));
static int current_cpi = DT_PROP(DT_NODELABEL(mouse_sensor), cpi);
static uint16_t saved_cpi = DT_PROP(DT_NODELABEL(mouse_sensor), cpi);
static bool confirmed;
K_MUTEX_DEFINE(dpi_lock);

static void announce(struct k_work *work);
K_WORK_DELAYABLE_DEFINE(announce_work, announce);

static void save_dpi(struct k_work *work);
K_WORK_DELAYABLE_DEFINE(save_work, save_dpi);

static int dpi_settings_set(const char *name, size_t len, settings_read_cb read_cb, void *cb_arg) {
    if (strcmp(name, "cpi") != 0) {
        return -ENOENT;
    }
    uint16_t cpi;
    if (len != sizeof(cpi)) {
        return -EINVAL;
    }
    int err = read_cb(cb_arg, &cpi, sizeof(cpi));
    if (err < 0) {
        return err;
    }
    if (err != (int)sizeof(cpi) || cpi < PMW3610_MIN_CPI || cpi > PMW3610_MAX_CPI ||
        cpi % 200 != 0) {
        return -EINVAL;
    }
    k_mutex_lock(&dpi_lock, K_FOREVER);
    current_cpi = saved_cpi = cpi;
    /* Settings load may precede asynchronous sensor initialization. Let the
     * announcement worker retry until the restored value is actually applied. */
    confirmed = false;
    k_work_reschedule(&announce_work, K_NO_WAIT);
    k_mutex_unlock(&dpi_lock);
    return 0;
}

SETTINGS_STATIC_HANDLER_DEFINE(pinchwing_dpi, "pinchwing_dpi", NULL, dpi_settings_set, NULL, NULL);

static void save_dpi(struct k_work *work) {
    ARG_UNUSED(work);
    k_mutex_lock(&dpi_lock, K_FOREVER);
    if (confirmed && current_cpi != saved_cpi) {
        uint16_t cpi = current_cpi;
        int err = settings_save_one("pinchwing_dpi/cpi", &cpi, sizeof(cpi));
        if (err) {
            LOG_WRN("Unable to save sensor CPI: %d", err);
            k_work_reschedule(&save_work, K_MSEC(DPI_SAVE_DELAY_MS));
        } else {
            saved_cpi = cpi;
        }
    }
    k_mutex_unlock(&dpi_lock);
}

/* Called with dpi_lock held. The sensor initializes asynchronously: a successful
 * write, rather than device_is_ready alone, confirms the initial setting. */
static int apply(int cpi) {
    if (!device_is_ready(sensor)) {
        return -ENODEV;
    }
    struct sensor_value value = {.val1 = cpi};
    int err = sensor_attr_set(sensor, SENSOR_CHAN_ALL,
                              (enum sensor_attribute)PMW3610_ALT_ATTR_CPI, &value);
    if (!err) {
        current_cpi = cpi;
        confirmed = true;
    }
    return err;
}

int pinchwing_dpi_adjust(bool increase) {
    k_mutex_lock(&dpi_lock, K_FOREVER);
    int next = CLAMP(current_cpi + (increase ? 200 : -200),
                     PMW3610_MIN_CPI, PMW3610_MAX_CPI);
    bool changed = next != current_cpi;
    int err = next == current_cpi && confirmed ? 0 : apply(next);
    if (!err) {
        if (changed) {
            k_work_reschedule(&save_work, K_MSEC(DPI_SAVE_DELAY_MS));
        }
        k_work_reschedule(&announce_work, K_NO_WAIT);
    }
    k_mutex_unlock(&dpi_lock);
    return err;
}

static void announce(struct k_work *work) {
    ARG_UNUSED(work);
    k_mutex_lock(&dpi_lock, K_FOREVER);
    if (!confirmed) {
        (void)apply(current_cpi);
    }
    if (confirmed) {
        const struct zmk_split_transport_peripheral_event event = {
            .type = ZMK_SPLIT_TRANSPORT_PERIPHERAL_EVENT_TYPE_INPUT_EVENT,
            .data.input_event = {
                .reg = DT_REG_ADDR(DT_NODELABEL(mouse_split)),
                .type = INPUT_EV_MSC,
                .code = PINCHWING_INPUT_MSC_DPI,
                .value = current_cpi,
                /* Never flush a partially collected X/Y mouse report. */
                .sync = false,
            },
        };
        /* Use the transport directly so heartbeats don't count as local input
         * activity and prevent the peripheral's normal idle sleep. Retries also
         * cover connection setup, receiver reboot, and missed notifications. */
        (void)zmk_split_peripheral_report_event(&event);
    }
    k_work_reschedule(&announce_work, K_MSEC(PINCHWING_DPI_REPORT_MS));
    k_mutex_unlock(&dpi_lock);
}

static int dpi_init(void) {
    k_work_schedule(&announce_work, K_MSEC(PINCHWING_DPI_REPORT_MS));
    return 0;
}

SYS_INIT(dpi_init, APPLICATION, CONFIG_APPLICATION_INIT_PRIORITY);

#else /* Dongle */

static struct k_spinlock dpi_lock;
static uint16_t reported_cpi;
static uint32_t reported_at;

static void receive_dpi(struct input_event *event, void *user_data) {
    ARG_UNUSED(user_data);
    if (event->type != INPUT_EV_MSC || event->code != PINCHWING_INPUT_MSC_DPI ||
        event->value < 200 || event->value > 3200 || event->value % 200 != 0) {
        return;
    }
    k_spinlock_key_t key = k_spin_lock(&dpi_lock);
    reported_cpi = event->value;
    reported_at = k_uptime_get_32();
    k_spin_unlock(&dpi_lock, key);
}

INPUT_CALLBACK_DEFINE(DEVICE_DT_GET(DT_NODELABEL(mouse_split)), receive_dpi, NULL);

uint16_t pinchwing_dpi_get(void) {
    k_spinlock_key_t key = k_spin_lock(&dpi_lock);
    uint16_t value = (uint32_t)(k_uptime_get_32() - reported_at) < PINCHWING_DPI_STALE_MS
                         ? reported_cpi : 0;
    k_spin_unlock(&dpi_lock, key);
    return value;
}

#endif
