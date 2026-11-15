/* SPDX-License-Identifier: MIT */
#pragma once
#include <lvgl.h>

struct cat_overlay_tile {
    uint16_t image;
    uint8_t x, y;
};
struct cat_overlay_frame {
    uint8_t count;
    const struct cat_overlay_tile *tiles;
};
extern const lv_image_dsc_t cat_overlay_tiles[];
/* Keymap layers 0–10, mouse sprite 11, recording badge 12; two poses each. */
extern const struct cat_overlay_frame cat_overlay_frames[13][2];
