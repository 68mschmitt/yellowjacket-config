#pragma once
#include <zephyr/input/input.h>
#define ZMK_SPLIT_TRANSPORT_PERIPHERAL_EVENT_TYPE_INPUT_EVENT 1
struct zmk_split_transport_peripheral_event {
    int type;
    union { struct { uint8_t reg, type; uint16_t code; int32_t value; bool sync; } input_event; } data;
};
static struct zmk_split_transport_peripheral_event last_report;
static int reports, transport_result;
static inline int zmk_split_peripheral_report_event(
    const struct zmk_split_transport_peripheral_event *event) {
    reports++;
    last_report = *event;
    return transport_result;
}
