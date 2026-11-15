#pragma once
#include <zephyr/device.h>
#include <stdint.h>
#define INPUT_EV_MSC 4
#define INPUT_EV_REL 2
struct input_event {
    const struct device *dev;
    uint8_t type;
    uint16_t code;
    int32_t value;
    bool sync;
};
struct test_input_callback {
    const struct device *device;
    void (*fn)(struct input_event *, void *);
    void *user_data;
};
#define INPUT_CALLBACK_DEFINE_NAMED(dev, callback, data, name) \
    static struct test_input_callback callback_##name = {dev, callback, data}
#define INPUT_CALLBACK_DEFINE(dev, callback, data) \
    INPUT_CALLBACK_DEFINE_NAMED(dev, callback, data, callback)
