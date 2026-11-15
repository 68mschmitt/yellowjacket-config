/* SPDX-License-Identifier: MIT */
#pragma once

#include <stdint.h>

#define PINCHWING_INPUT_MSC_POWER 0x5057
#define PINCHWING_POWER_REPORT_MS 2000
#define PINCHWING_POWER_STALE_MS 5000

/* Wire values: 0..100 are battery percentages; USB carries no percentage. */
#define PINCHWING_POWER_UNKNOWN (-1)
#define PINCHWING_POWER_USB 101

/* Receiver: physical side 0 = left, 1 = right. Stale reports return UNKNOWN. */
int pinchwing_power_get(unsigned int side);
