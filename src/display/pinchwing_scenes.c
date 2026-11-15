/* SPDX-License-Identifier: MIT */
#include "pinchwing_scenes.h"
#include "cat_overlays.h"

#define TILE_LIMIT 24
struct scene_group {
    lv_obj_t *root;
    lv_obj_t *images[TILE_LIMIT];
    const struct cat_overlay_frame *current;
    int origin_x, origin_y;
};
static struct scene_group props, mouse, badge;
static lv_obj_t *sleep_label;

static void create_group(struct scene_group *group, lv_obj_t *screen) {
    group->root = lv_obj_create(screen);
    lv_obj_remove_style_all(group->root);
    lv_obj_set_size(group->root, 240, 240);
    lv_obj_remove_flag(group->root, LV_OBJ_FLAG_SCROLLABLE);
    /* Only allocate image objects when first needed. Reuse them thereafter. */
}

static void show(struct scene_group *group, const struct cat_overlay_frame *frame) {
    if (group->current == frame) {
        return;
    }
    group->current = frame;
    for (unsigned int i = 0; i < TILE_LIMIT; i++) {
        if (frame && i < frame->count) {
            if (!group->images[i]) {
                group->images[i] = lv_image_create(group->root);
            }
            const struct cat_overlay_tile *tile = &frame->tiles[i];
            lv_image_set_src(group->images[i], &cat_overlay_tiles[tile->image]);
            lv_obj_set_pos(group->images[i], tile->x - group->origin_x,
                           tile->y - group->origin_y);
            lv_obj_remove_flag(group->images[i], LV_OBJ_FLAG_HIDDEN);
        } else if (group->images[i]) {
            lv_obj_add_flag(group->images[i], LV_OBJ_FLAG_HIDDEN);
        }
    }
}

void pinchwing_scenes_create(lv_obj_t *screen) {
    create_group(&props, screen);
    create_group(&mouse, screen);
    mouse.origin_x = 72;
    mouse.origin_y = 144;
    lv_obj_set_size(mouse.root, 96, 48);
    create_group(&badge, screen);
    sleep_label = lv_label_create(screen);
    lv_label_set_text(sleep_label, "z Z");
    lv_obj_set_style_text_color(sleep_label, lv_color_hex(0x55ddff), 0);
    lv_obj_set_style_text_font(sleep_label, &lv_font_montserrat_14, 0);
    lv_obj_add_flag(sleep_label, LV_OBJ_FLAG_HIDDEN);
}

void pinchwing_scenes_foreground(void) {
    lv_obj_move_to_index(props.root, -1);
    lv_obj_move_to_index(mouse.root, -1);
    lv_obj_move_to_index(badge.root, -1);
    lv_obj_move_to_index(sleep_label, -1);
}

void pinchwing_scenes_update(unsigned int layer, bool recording, bool sleeping,
                            bool active, unsigned int frame) {
    if (layer > 10) {
        layer = 0;
    }
    unsigned int phase = sleeping ? 0 : (frame / (active ? 2 : 6)) % 2;
    show(&props, &cat_overlay_frames[layer][phase]);
    if (layer == 3) {
        /* Triangular scurry across the same foreground lane as the preview. */
        unsigned int step = frame % 48;
        int x = sleeping ? 49 : (step < 24 ? (int)step * 4 - 48 : 144 - (int)step * 4);
        show(&mouse, &cat_overlay_frames[11][sleeping || step >= 24]);
        lv_obj_set_pos(mouse.root, 72 + x, 144 + (sleeping ? 0 : (frame % 2)));
    } else {
        show(&mouse, NULL);
    }
    show(&badge, recording ? &cat_overlay_frames[12][(frame / 5) % 2] : NULL);
    if (sleeping) {
        lv_obj_remove_flag(sleep_label, LV_OBJ_FLAG_HIDDEN);
        lv_obj_set_pos(sleep_label, 182, 101 - (int)(frame % 20) / 3);
    } else {
        lv_obj_add_flag(sleep_label, LV_OBJ_FLAG_HIDDEN);
    }
}

const char *pinchwing_scenes_caption(unsigned int layer, bool active) {
    static const char *const captions[11][2] = {
        {"all paws on deck", "HYPERSPACE: MEOW"},
        {"counting on my paws", "carry the tuna"},
        {"ready for takeoff", "captain whiskers"},
        {"stay right there...", "almost had it!"},
        {"a little purrcery", "special powers!"},
        {"mission control", "all systems purring"},
        {"if I fits, I sits", "{ snug as a cat }"},
        {"just my type", "letters, paw by paw"},
        {"which reel? ?", "ready when you are"},
        {"pick a mixtape ?", "encore?"},
        {"saving every paw", "tape is rolling"},
    };
    return captions[layer <= 10 ? layer : 0][active];
}
