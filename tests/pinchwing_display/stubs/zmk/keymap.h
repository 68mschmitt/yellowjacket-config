#pragma once
#include <stdint.h>
#include <stdbool.h>
#define ZMK_KEYMAP_LAYERS_LEN 11
typedef uint8_t zmk_keymap_layer_id_t;
extern unsigned int test_layers;
static inline uint8_t zmk_keymap_layer_index_to_id(unsigned int i) { return i; }
static inline bool zmk_keymap_layer_active(uint8_t id) { return (test_layers & (1U << id)) != 0; }
static inline const char *zmk_keymap_layer_name(uint8_t id) {
    static const char *const names[] = {"Base", "Number", "Arrows", "Mouse", "Functions",
        "System", "Brackets", "No Mods", "RecSel", "PlaySel", "Recording"};
    return names[id];
}
