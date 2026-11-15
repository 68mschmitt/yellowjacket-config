#pragma once
#include <stdbool.h>
struct device { int unused; };
static const struct device test_devices[3];
static bool ready = true;
#define DT_NODELABEL(x) x
#define power_left 1
#define mouse_split 0
#define DT_CHOSEN(x) 2
#define DT_REG_ADDR(node) (node)
#define DEVICE_DT_GET(node) (&test_devices[node])
static inline bool device_is_ready(const struct device *dev) { (void)dev; return ready; }
