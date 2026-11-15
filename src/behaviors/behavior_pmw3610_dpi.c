/* SPDX-License-Identifier: MIT */
#define DT_DRV_COMPAT zmk_behavior_pmw3610_dpi

#include <zephyr/device.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/logging/log.h>
#include <drivers/behavior.h>
#include <zmk/behavior.h>
#if IS_ENABLED(CONFIG_SHIELD_PINCHWING_DONGLE_RIGHT)
#include <pinchwing_dpi.h>
#endif
#if DT_NODE_HAS_STATUS(DT_NODELABEL(mouse_sensor), okay)
#include "pmw3610.h"
#endif

LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

/* Track only successfully applied changes; reboot restores the DT default. */
#if DT_NODE_HAS_STATUS(DT_NODELABEL(mouse_sensor), okay) && \
    !IS_ENABLED(CONFIG_SHIELD_PINCHWING_DONGLE_RIGHT)
static int current_cpi = DT_PROP(DT_NODELABEL(mouse_sensor), cpi);
#endif

static int pressed(struct zmk_behavior_binding *binding,
                   struct zmk_behavior_binding_event event) {
    if (binding->param1 > 1) {
        return -EINVAL;
    }
#if IS_ENABLED(CONFIG_SHIELD_PINCHWING_DONGLE_RIGHT)
    int err = pinchwing_dpi_adjust(binding->param1 != 0);
    if (err) {
        LOG_WRN("Unable to set sensor CPI: %d", err);
        return err;
    }
#elif DT_NODE_HAS_STATUS(DT_NODELABEL(mouse_sensor), okay)
    const struct device *sensor = DEVICE_DT_GET(DT_NODELABEL(mouse_sensor));
    if (!device_is_ready(sensor)) {
        return -ENODEV;
    }
    int next = CLAMP(current_cpi + (binding->param1 ? 200 : -200),
                     PMW3610_MIN_CPI, PMW3610_MAX_CPI);
    if (next == current_cpi) {
        return ZMK_BEHAVIOR_OPAQUE;
    }
    struct sensor_value value = {.val1 = next};
    int err = sensor_attr_set(sensor, SENSOR_CHAN_ALL,
                              (enum sensor_attribute)PMW3610_ALT_ATTR_CPI, &value);
    if (err) {
        LOG_WRN("Unable to set sensor CPI: %d", err);
        return err;
    }
    current_cpi = next;
    LOG_INF("Sensor CPI: %d", current_cpi);
#endif
    return ZMK_BEHAVIOR_OPAQUE;
}

static int released(struct zmk_behavior_binding *binding,
                    struct zmk_behavior_binding_event event) {
    return ZMK_BEHAVIOR_OPAQUE;
}

static const struct behavior_driver_api api = {
    /* Forward presses from either half to all parts; only the sensor owner acts. */
    .locality = BEHAVIOR_LOCALITY_GLOBAL,
    .binding_pressed = pressed,
    .binding_released = released,
};

BEHAVIOR_DT_INST_DEFINE(0, NULL, NULL, NULL, NULL, POST_KERNEL,
                        CONFIG_KERNEL_INIT_PRIORITY_DEFAULT, &api);
