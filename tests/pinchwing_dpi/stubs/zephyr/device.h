#pragma once
#include <stdbool.h>
struct device { int unused; };
static const struct device test_device;
static bool ready = true;
#define DT_NODELABEL(x) 0
#define DT_PROP(node, prop) 1600
#define DT_REG_ADDR(node) 0
#define DEVICE_DT_GET(node) (&test_device)
static inline bool device_is_ready(const struct device *dev) { (void)dev; return ready; }
