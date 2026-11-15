/* SPDX-License-Identifier: MIT */
#include <string.h>
#include <stdlib.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zmk/wpm.h>
#include <zmk/keymap.h>
#include "pinchwing_pet.h"
#include "bongo_cat.h"
#include "pinchwing_scenes.h"
#if IS_ENABLED(CONFIG_PINCHWING_DISPLAY_DIAGNOSTICS)
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(pinchwing_pet, LOG_LEVEL_INF);

static void render_complete(lv_event_t *event) {
    ARG_UNUSED(event);
    static unsigned int renders;
    if (++renders <= 3) {
        LOG_INF("Completed display render %u", renders);
    }
}
#endif

/* Hysteresis avoids repeatedly entering/exiting warp near a single threshold. */
#define WARP_ENTER_WPM 80
#define WARP_EXIT_WPM 65
#define FRAME_MS 100
#define STAR_COUNT 16

static atomic_t presses[2];
static atomic_val_t seen[2];
static uint32_t last_press, paw_until[2];
static lv_obj_t *cat, *caption;
static lv_obj_t *paw_images[2];
static unsigned int pose;
static lv_obj_t *stars[STAR_COUNT];
static unsigned int radius[STAR_COUNT], frame, warp;
static bool warping;
static unsigned int last_layer = UINT32_MAX;
static bool last_recording;
static unsigned int foreground_mask = UINT32_MAX;

/* Select by keymap names so transparent Recording doesn't hide a working layer. */
static unsigned int scene_layer(bool *recording) {
    static const char *const names[] = {
        "Base", "Number", "Arrows", "Mouse", "Functions", "System",
        "Brackets", "No Mods", "RecSel", "PlaySel", "Recording",
    };
    *recording = false;
    unsigned int selected = 0;
    for (unsigned int index = 0; index < ZMK_KEYMAP_LAYERS_LEN; index++) {
        zmk_keymap_layer_id_t id = zmk_keymap_layer_index_to_id(index);
        if (!zmk_keymap_layer_active(id)) {
            continue;
        }
        const char *name = zmk_keymap_layer_name(id);
        for (unsigned int i = 0; name && i < ARRAY_SIZE(names); i++) {
            if (strcmp(name, names[i]) == 0) {
                if (i == 10) {
                    *recording = true;
                } else {
                    selected = i;
                }
                break;
            }
        }
    }
    return *recording && selected == 0 ? 10 : selected;
}

/* Unit-ish radial vectors, scaled by 100; no floating point required. */
static const int8_t directions[STAR_COUNT][2] = {
    {100, 0}, {92, 38}, {71, 71}, {38, 92},
    {0, 100}, {-38, 92}, {-71, 71}, {-92, 38},
    {-100, 0}, {-92, -38}, {-71, -71}, {-38, -92},
    {0, -100}, {38, -92}, {71, -71}, {92, -38},
};

void pinchwing_pet_press(unsigned int side) {
    if (side < 2) {
        atomic_inc(&presses[side]);
    }
}

static lv_obj_t *shape(lv_obj_t *parent, int x, int y, int w, int h,
                       uint32_t color, int rounding) {
    lv_obj_t *obj = lv_obj_create(parent);
    lv_obj_remove_style_all(obj);
    lv_obj_set_pos(obj, x, y);
    lv_obj_set_size(obj, w, h);
    lv_obj_set_style_bg_color(obj, lv_color_hex(color), 0);
    lv_obj_set_style_bg_opa(obj, LV_OPA_COVER, 0);
    lv_obj_set_style_radius(obj, rounding, 0);
    lv_obj_remove_flag(obj, LV_OBJ_FLAG_SCROLLABLE);
    return obj;
}

static void animate(lv_timer_t *timer) {
    ARG_UNUSED(timer);
    uint32_t now = k_uptime_get_32();
    unsigned int wpm = zmk_wpm_get_state();
    bool recording;
    unsigned int layer = scene_layer(&recording);
    if (layer != last_layer || recording != last_recording) {
        last_press = now;
        last_layer = layer;
        last_recording = recording;
    }
    frame++;
    if (layer != 0) {
        warping = false;
        warp = 0;
    } else if (wpm >= WARP_ENTER_WPM) {
        warping = true;
    } else if (wpm < WARP_EXIT_WPM) {
        warping = false;
    }
    /* 1.7 seconds to accelerate, 2.5 seconds to settle back into cruise. */
    warp = warping ? MIN(100, warp + 6) : (warp > 4 ? warp - 4 : 0);
    for (int side = 0; side < 2; side++) {
        atomic_val_t count = atomic_get(&presses[side]);
        if (count != seen[side]) {
            seen[side] = count;
            last_press = now;
            paw_until[side] = now + 180;
        }
    }
    bool sleeping = (uint32_t)(now - last_press) > 15000 && warp == 0;
    int bob = (int)((frame / (sleeping ? 12 : 4)) % 3) - 1;
    int shake = warp > 50 ? (int)(frame % 3) - 1 : 0;
    lv_obj_set_pos(cat, 24 + shake, 92 + bob);
    unsigned int next_pose = 0;
    for (int side = 0; side < 2; side++) {
        bool hit = (int32_t)(paw_until[side] - now) > 0;
        /* Alternate return frames so sustained typing still visibly drums. */
        if (sleeping || (hit && !(pose & BIT(side)))) {
            next_pose |= BIT(side);
        }
    }
    if (next_pose != pose) {
        for (int side = 0; side < 2; side++) {
            if ((next_pose ^ pose) & BIT(side)) {
                const struct pinchwing_bongo_sprite *sprite =
                    &pinchwing_bongo_paws[side][!!(next_pose & BIT(side))];
                lv_image_set_src(paw_images[side], &sprite->image);
            }
        }
        pose = next_pose;
    }
    bool active = (uint32_t)(now - last_press) < 600;
    pinchwing_scenes_update(layer, recording, sleeping, active, frame);
    /* Siblings allow each paw to cross the prop plane independently. */
    unsigned int moving_mask = 0;
    for (int side = 0; side < 2; side++) {
        const struct pinchwing_bongo_sprite *sprite =
            &pinchwing_bongo_paws[side][!!(pose & BIT(side))];
        lv_obj_set_pos(paw_images[side], 24 + shake + sprite->x, 92 + bob + sprite->y);
        if (!sleeping && (int32_t)(paw_until[side] - now) > 0) {
            moving_mask |= BIT(side);
        }
    }
    if (moving_mask != foreground_mask) {
        for (int side = 0; side < 2; side++) {
            lv_obj_move_to_index(paw_images[side], -1);
        }
        pinchwing_scenes_foreground();
        for (int side = 0; side < 2; side++) {
            if (moving_mask & BIT(side)) {
                lv_obj_move_to_index(paw_images[side], -1);
            }
        }
        foreground_mask = moving_mask;
    }

    for (unsigned int i = 0; i < STAR_COUNT; i++) {
        /* Calm stars drift slowly; warp stars accelerate and become streaks. */
        radius[i] += warp ? 1 + warp / 9 : (frame % 4 == 0);
        if (radius[i] > 111) {
            radius[i] = 22 + i % 9;
        }
        int dx = directions[i][0], dy = directions[i][1];
        int length = 2 + warp * radius[i] / 650;
        int w = abs(dx) > abs(dy) ? length : 2;
        int h = abs(dx) > abs(dy) ? 2 : length;
        lv_obj_set_size(stars[i], w, h);
        lv_obj_set_pos(stars[i], 120 + dx * (int)radius[i] / 100 - w / 2,
                       120 + dy * (int)radius[i] / 100 - h / 2);
        lv_obj_set_style_bg_opa(stars[i], 60 + warp * 195 / 100, 0);
    }
    const char *text = sleeping ? (layer == 3 ? "truce until further notice" : "catnap on the job") :
                       warping ? (warp < 100 ? "ENGAGING NYAN DRIVE" : "HYPERSPACE: MEOW") :
                       warp ? "returning to orbit..." : pinchwing_scenes_caption(layer, active && layer != 0);
    if (strcmp(lv_label_get_text(caption), text) != 0) {
        lv_label_set_text(caption, text);
    }
}

void pinchwing_pet_create(lv_obj_t *screen) {
    lv_obj_remove_flag(screen, LV_OBJ_FLAG_SCROLLABLE);
#if IS_ENABLED(CONFIG_PINCHWING_DISPLAY_DIAGNOSTICS)
    LOG_INF("Creating starfield and cat image");
    lv_display_add_event_cb(lv_display_get_default(), render_complete,
                            LV_EVENT_REFR_READY, NULL);
#endif
    for (unsigned int i = 0; i < STAR_COUNT; i++) {
        radius[i] = 24 + i * 83 / STAR_COUNT;
        stars[i] = shape(screen, 120, 120, 2, 2, 0x8de4ff, 1);
    }
    /* Share the original body across poses. Small indexed tiles bound decode
     * allocations and keep the firmware within older UF2 bootloader limits. */
    cat = lv_obj_create(screen);
    lv_obj_remove_style_all(cat);
    lv_obj_set_size(cat, 192, 96);
    lv_obj_remove_flag(cat, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_pos(cat, 24, 92);
    for (int i = 0; i < 3; i++) {
        const struct pinchwing_bongo_sprite *sprite = &pinchwing_bongo_base[i];
        lv_obj_t *image = lv_image_create(cat);
        lv_image_set_src(image, &sprite->image);
        lv_obj_set_pos(image, sprite->x, sprite->y);
    }
    for (int side = 0; side < 2; side++) {
        const struct pinchwing_bongo_sprite *sprite = &pinchwing_bongo_paws[side][0];
        paw_images[side] = lv_image_create(screen);
        lv_image_set_src(paw_images[side], &sprite->image);
        lv_obj_set_pos(paw_images[side], 24 + sprite->x, 92 + sprite->y);
    }
    pinchwing_scenes_create(screen);
    caption = lv_label_create(screen);
    lv_obj_set_pos(caption, 20, 190);
    lv_obj_set_width(caption, 200);
    lv_obj_set_style_text_align(caption, LV_TEXT_ALIGN_CENTER, 0);
    lv_obj_set_style_text_font(caption, &lv_font_montserrat_14, 0);
    lv_obj_set_style_text_color(caption, lv_color_hex(0xffd879), 0);
    lv_label_set_long_mode(caption, LV_LABEL_LONG_CLIP);
    lv_label_set_text(caption, "all paws on deck");
    last_press = k_uptime_get_32();
    lv_timer_create(animate, FRAME_MS, NULL);
}
