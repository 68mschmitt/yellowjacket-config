#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <lvgl.h>
#include "pinchwing_pet.h"
#include "cat_overlays.h"
#include "bongo_cat.h"

uint32_t test_now;
unsigned int test_wpm, test_layers = 1;
static unsigned int flushes;
static uint16_t pixels[240 * 240];
static void flush(lv_display_t *display, const lv_area_t *area, uint8_t *data) {
    const uint16_t *src = (const uint16_t *)data;
    for (int y = area->y1; y <= area->y2; y++)
        for (int x = area->x1; x <= area->x2; x++)
            pixels[y * 240 + x] = *src++;
    flushes++;
    lv_display_flush_ready(display);
}
static void step(unsigned int ms) {
    test_now += ms;
    lv_tick_inc(ms);
    lv_timer_handler();
    lv_refr_now(NULL);
    assert(lv_mem_test() == LV_RESULT_OK);
}
static bool has_caption(lv_obj_t *screen, const char *caption) {
    for (unsigned int i = 0; i < lv_obj_get_child_count(screen); i++) {
        lv_obj_t *child = lv_obj_get_child(screen, i);
        if (lv_obj_check_type(child, &lv_label_class) &&
            strcmp(lv_label_get_text(child), caption) == 0) return true;
    }
    return false;
}
static void check_paw_order(lv_obj_t *screen) {
    int left = -1, right = -1;
    for (unsigned int i = 0; i < lv_obj_get_child_count(screen); i++) {
        lv_obj_t *child = lv_obj_get_child(screen, i);
        if (!lv_obj_check_type(child, &lv_image_class)) continue;
        const void *src = lv_image_get_src(child);
        for (unsigned int pose = 0; pose < 2; pose++) {
            if (src == &pinchwing_bongo_paws[0][pose].image) left = i;
            if (src == &pinchwing_bongo_paws[1][pose].image) right = i;
        }
    }
    assert(left >= 0 && right >= 0);
    unsigned int groups = 0;
    for (unsigned int i = 0; i < lv_obj_get_child_count(screen); i++) {
        lv_obj_t *child = lv_obj_get_child(screen, i);
        if (lv_obj_check_type(child, &lv_obj_class) && lv_obj_get_width(child) == 240) {
            /* Left is swatting, right is resting: all prop planes lie between. */
            assert(right < (int)i && (int)i < left);
            groups++;
        }
    }
    assert(groups == 2); /* Scene props and recording badge; mouse has a smaller root. */
}
static void screenshot(unsigned int layer) {
    char path[40];
    snprintf(path, sizeof(path), "layer-%02u.ppm", layer);
    FILE *out = fopen(path, "wb");
    assert(out);
    fprintf(out, "P6\n240 240\n255\n");
    for (unsigned int i = 0; i < 240 * 240; i++) {
        uint16_t p = pixels[i];
        unsigned char rgb[] = {(p >> 11) * 255 / 31, ((p >> 5) & 63) * 255 / 63, (p & 31) * 255 / 31};
        fwrite(rgb, 1, 3, out);
    }
    fclose(out);
}
int main(void) {
    lv_init();
    lv_display_t *display = lv_display_create(240, 240);
    static uint16_t buffer[240 * 24];
    lv_display_set_buffers(display, buffer, NULL, sizeof(buffer), LV_DISPLAY_RENDER_MODE_PARTIAL);
    lv_display_set_flush_cb(display, flush);
    lv_obj_t *screen = lv_screen_active();
    lv_obj_set_style_bg_color(screen, lv_color_hex(0x07101c), 0);
    lv_obj_set_style_pad_all(screen, 0, 0);
    lv_obj_set_style_border_width(screen, 0, 0);
    pinchwing_pet_create(screen);
    /* Match the dashboard's seven additional labels and their font allocations. */
    static const char *const labels[] = {"Mouse", "92 WPM", "1600 DPI", "USB ready", "2/2 linked", "85%", "92%"};
    static const int positions[][3] = {{45,15,150}, {45,34,150}, {45,58,150},
        {25,75,110}, {135,75,80}, {50,211,70}, {120,211,70}};
    for (unsigned int i = 0; i < 7; i++) {
        lv_obj_t *label = lv_label_create(screen);
        lv_label_set_text(label, labels[i]);
        lv_obj_set_pos(label, positions[i][0], positions[i][1]);
        lv_obj_set_width(label, positions[i][2]);
        lv_obj_set_style_text_align(label, LV_TEXT_ALIGN_CENTER, 0);
        lv_obj_set_style_text_color(label, lv_color_white(), 0);
        lv_obj_set_style_text_font(label, i == 1 ? &lv_font_montserrat_20 : &lv_font_montserrat_14, 0);
    }
    for (unsigned int scene = 0; scene < 13; scene++)
        for (unsigned int phase = 0; phase < 2; phase++)
            assert(cat_overlay_frames[scene][phase].count <= 24);
    for (unsigned int round = 0; round < 3; round++) {
        for (unsigned int layer = 0; layer < 11; layer++) {
            test_layers = 1 | (1U << layer);
            test_wpm = 95;
            for (unsigned int frame = 0; frame < 40; frame++) {
                pinchwing_pet_press(frame % 2);
                step(100);
            }
            screenshot(layer);
            test_layers |= 1U << 10;
            for (unsigned int frame = 0; frame < 20; frame++) step(100);
            test_wpm = 0;
            step(16000);
            step(3000);
            pinchwing_pet_press(0);
            pinchwing_pet_press(1);
            step(100);
        }
    }
    /* Recording remains an overlay when another working layer is active. */
    test_layers = 1 | (1U << 3) | (1U << 10);
    step(100);
    assert(has_caption(screen, "almost had it!"));
    step(1000);
    assert(has_caption(screen, "stay right there..."));
    step(16000);
    assert(has_caption(screen, "truce until further notice"));
    pinchwing_pet_press(0);
    step(100);
    check_paw_order(screen);
    test_layers = 1;
    test_wpm = 0;
    pinchwing_pet_press(0);
    step(100);
    assert(has_caption(screen, "all paws on deck"));
    lv_mem_monitor_t memory;
    lv_mem_monitor(&memory);
    printf("PASS: all layers, recording overlay, idle/wake, warp; %u flushes; heap free %zu, largest %zu\n",
           flushes, memory.free_size, memory.free_biggest_size);
    return 0;
}
