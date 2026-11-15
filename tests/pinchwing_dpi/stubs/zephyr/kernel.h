#pragma once
#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#define IS_ENABLED(x) (x)
#define ARG_UNUSED(x) (void)(x)
#define CLAMP(v, lo, hi) ((v) < (lo) ? (lo) : (v) > (hi) ? (hi) : (v))
#define K_FOREVER (-1)
#define K_NO_WAIT 0
#define K_MSEC(x) (x)
struct k_work { int unused; };
struct k_work_delayable { void (*handler)(struct k_work *); };
#define K_WORK_DELAYABLE_DEFINE(name, cb) struct k_work_delayable name = {.handler = cb}
static int scheduled_delay;
static inline int k_work_reschedule(struct k_work_delayable *work, int delay) {
    (void)work;
    scheduled_delay = delay;
    return 0;
}
#define k_work_schedule k_work_reschedule
#define K_MUTEX_DEFINE(name) int name
static inline void k_mutex_lock(int *lock, int timeout) {
    (void)timeout;
    assert(!*lock);
    *lock = 1;
}
static inline void k_mutex_unlock(int *lock) { assert(*lock); *lock = 0; }
struct k_spinlock { int unused; };
typedef int k_spinlock_key_t;
static inline int k_spin_lock(struct k_spinlock *lock) { (void)lock; return 0; }
static inline void k_spin_unlock(struct k_spinlock *lock, int key) { (void)lock; (void)key; }
static uint32_t now;
static inline uint32_t k_uptime_get_32(void) { return now; }
