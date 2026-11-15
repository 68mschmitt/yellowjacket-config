#pragma once
typedef unsigned int atomic_t;
typedef unsigned int atomic_val_t;
static inline void atomic_inc(atomic_t *v) { ++*v; }
static inline atomic_val_t atomic_get(const atomic_t *v) { return *v; }
