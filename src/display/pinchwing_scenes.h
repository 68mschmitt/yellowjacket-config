/* SPDX-License-Identifier: MIT */
#pragma once
#include <lvgl.h>

void pinchwing_scenes_create(lv_obj_t *screen);
void pinchwing_scenes_update(unsigned int layer, bool recording, bool sleeping,
                            bool active, unsigned int frame);
const char *pinchwing_scenes_caption(unsigned int layer, bool active);
/* Raise props above resting paws, before animated paws are raised above props. */
void pinchwing_scenes_foreground(void);
