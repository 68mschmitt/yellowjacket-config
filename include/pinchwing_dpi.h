/* SPDX-License-Identifier: MIT */
#pragma once

#include <stdbool.h>
#include <stdint.h>

/* Private MSC code on the existing optical input split; never a mouse axis. */
#define PINCHWING_INPUT_MSC_DPI 0x5044
#define PINCHWING_DPI_REPORT_MS 2000
#define PINCHWING_DPI_STALE_MS 5000

/* Right half: changes the sensor setting, returning the driver's result. */
int pinchwing_dpi_adjust(bool increase);

/* Receiver: zero means no fresh, valid report from the right half. */
uint16_t pinchwing_dpi_get(void);
