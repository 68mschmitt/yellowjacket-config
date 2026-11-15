#pragma once
#include <stdbool.h>
#define NRF_POWER NULL
static bool usb_present;
static inline bool nrf_power_usbregstatus_vbusdet_get(const void *reg) {
    (void)reg;
    return usb_present;
}
