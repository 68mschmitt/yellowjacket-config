#pragma once
#include <stdint.h>
#include <stdbool.h>
#define ARG_UNUSED(x) (void)(x)
#define IS_ENABLED(x) 0
#define BIT(x) (1U << (x))
#define ARRAY_SIZE(x) (sizeof(x) / sizeof((x)[0]))
#define MIN(a, b) ((a) < (b) ? (a) : (b))
extern uint32_t test_now;
static inline uint32_t k_uptime_get_32(void) { return test_now; }
