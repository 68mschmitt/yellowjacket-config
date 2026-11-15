#pragma once
/* Reuse the existing host work, clock and lock stubs. */
#include "../../../pinchwing_dpi/stubs/zephyr/kernel.h"
#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))
