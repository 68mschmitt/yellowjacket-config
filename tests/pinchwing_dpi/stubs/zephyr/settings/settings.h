#pragma once
#include <assert.h>
#include <stdint.h>
#include <string.h>
#include <sys/types.h>

typedef ssize_t (*settings_read_cb)(void *, void *, size_t);
#define SETTINGS_STATIC_HANDLER_DEFINE(id, subtree, get, set, commit, export) \
    static int (*registered_settings_set)(const char *, size_t, settings_read_cb, void *) = set

static int save_calls, save_result;
static uint16_t flash_cpi;
static inline int settings_save_one(const char *name, const void *value, size_t len) {
    assert(strcmp(name, "pinchwing_dpi/cpi") == 0);
    assert(len == sizeof(flash_cpi));
    save_calls++;
    if (!save_result) {
        memcpy(&flash_cpi, value, len);
    }
    return save_result;
}
