/* SPDX-License-Identifier: MIT */
#pragma once
#include <lvgl.h>

struct pinchwing_bongo_sprite {
    lv_image_dsc_t image;
    int16_t x, y;
};

extern const struct pinchwing_bongo_sprite pinchwing_bongo_base[3];
/* Screen side (left/right), then state (up/down). */
extern const struct pinchwing_bongo_sprite pinchwing_bongo_paws[2][2];
