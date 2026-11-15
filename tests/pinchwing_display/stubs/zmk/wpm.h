#pragma once
extern unsigned int test_wpm;
static inline unsigned int zmk_wpm_get_state(void) { return test_wpm; }
