#pragma once
#include <zephyr/device.h>
enum sensor_attribute { PMW3610_ALT_ATTR_CPI };
#define SENSOR_CHAN_ALL 0
struct sensor_value { int val1, val2; };
static int driver_result, writes, applied_cpi;
static inline int sensor_attr_set(const struct device *dev, int channel,
                                 enum sensor_attribute attr, const struct sensor_value *value) {
    (void)dev; (void)channel; (void)attr;
    writes++;
    if (!driver_result) applied_cpi = value->val1;
    return driver_result;
}
