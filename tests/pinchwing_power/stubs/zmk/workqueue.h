#pragma once
#include <zephyr/kernel.h>
struct k_work_q { int unused; };
static struct k_work_q lowprio;
static inline struct k_work_q *zmk_workqueue_lowprio_work_q(void) { return &lowprio; }
static inline int k_work_reschedule_for_queue(struct k_work_q *queue,
                                              struct k_work_delayable *work, int delay) {
    assert(queue == &lowprio); /* Serialize with ZMK battery ADC access. */
    return k_work_reschedule(work, delay);
}
#define k_work_schedule_for_queue k_work_reschedule_for_queue
