#pragma once
#include <stdbool.h>
#include <stdint.h>
#define INPUT_EV_MSC 4
#define INPUT_EV_REL 2
struct input_event { uint8_t type; uint16_t code; int32_t value; bool sync; };
#define INPUT_CALLBACK_DEFINE(...)
