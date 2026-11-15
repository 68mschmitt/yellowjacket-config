#pragma once
#include <zephyr/device.h>
#include <hal/nrf_power.h>
#define SENSOR_CHAN_GAUGE_STATE_OF_CHARGE 1
struct sensor_value { int val1, val2; };
static int sample_result, channel_result, battery_level = 42, samples;
static bool usb_during_sample;
static inline int sensor_sample_fetch_chan(const struct device *dev, int channel) {
    (void)dev;
    assert(channel == SENSOR_CHAN_GAUGE_STATE_OF_CHARGE);
    samples++;
    if (usb_during_sample) usb_present = true;
    return sample_result;
}
static inline int sensor_channel_get(const struct device *dev, int channel,
                                     struct sensor_value *value) {
    (void)dev;
    assert(channel == SENSOR_CHAN_GAUGE_STATE_OF_CHARGE);
    value->val1 = battery_level;
    value->val2 = 0;
    return channel_result;
}
