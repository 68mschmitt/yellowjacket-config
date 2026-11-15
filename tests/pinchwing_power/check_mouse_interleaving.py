#!/usr/bin/env python3
"""Run ZMK's actual mouse handler with power/DPI events inserted between X and Y."""
from pathlib import Path
import os
import re
import subprocess
import sys
import tempfile


if len(sys.argv) != 2:
    raise SystemExit(f"Usage: {sys.argv[0]} /path/to/zmk/app/src/pointing/input_listener.c")
repo = Path(__file__).resolve().parents[2]
upstream = Path(sys.argv[1]).read_text()


def helper(name):
    match = re.search(rf"static void {name}\([^{{]+\{{.*?^\}}", upstream,
                      re.MULTILINE | re.DOTALL)
    if not match:
        raise SystemExit(f"Cannot find mouse helper: {name}")
    return match.group(0)


source = r"""
#include <assert.h>
#include <stdio.h>
#include <stddef.h>
#include <zephyr/input/input.h>
#include <pinchwing_power.h>
#include <pinchwing_dpi.h>
#define IS_ENABLED(x) 0
#define BIT(x) (1U << (x))
#define LOG_ERR(...) ((void)0)
#define ZMK_INPUT_PROC_STOP 1
#define ZMK_HID_MOUSE_NUM_BUTTONS 5
#define INPUT_EV_KEY 1
#define INPUT_EV_ABS 3
#define INPUT_REL_X 0
#define INPUT_REL_Y 1
#define INPUT_REL_HWHEEL 6
#define INPUT_REL_WHEEL 8
"""
source += upstream[upstream.index("enum input_listener_xy_data_mode"):
                   upstream.index("static void handle_rel_code")]
source += r"""
static int reports, x, y, sent_x, sent_y;
static int filter_with_input_config(const struct input_listener_config *cfg,
                                   struct input_listener_data *data, struct input_event *evt) {
    return 0;
}
static void handle_abs_code(const struct input_listener_config *cfg,
                            struct input_listener_data *data, struct input_event *evt) {
    assert(false);
}
static void handle_key_code(const struct input_listener_config *cfg,
                            struct input_listener_data *data, struct input_event *evt) {
    assert(false);
}
static void zmk_hid_mouse_scroll_set(int h, int v) { assert(h == 0 && v == 0); }
static void zmk_hid_mouse_movement_set(int dx, int dy) { x = dx; y = dy; }
static void zmk_hid_mouse_button_press(int button) { assert(false); }
static void zmk_hid_mouse_button_release(int button) { assert(false); }
static void zmk_endpoint_send_mouse_report(void) { reports++; sent_x = x; sent_y = y; }
"""
source += "\n".join(helper(name) for name in ("handle_rel_code", "clear_xy_data", "input_handler"))
source += r"""
int main(void) {
    struct input_listener_config config = {0};
    struct input_listener_data data = {0};
    struct input_event event = {.type = INPUT_EV_REL, .code = INPUT_REL_X,
                                .value = 7, .sync = false};
    input_handler(&config, &data, &event);
    assert(reports == 0);
    event.type = INPUT_EV_MSC;
    event.code = PINCHWING_INPUT_MSC_POWER;
    event.value = PINCHWING_POWER_USB;
    input_handler(&config, &data, &event);
    assert(reports == 0);
    event.code = PINCHWING_INPUT_MSC_DPI;
    event.value = 1600;
    input_handler(&config, &data, &event);
    assert(reports == 0);
    event.type = INPUT_EV_REL;
    event.code = INPUT_REL_Y;
    event.value = -4;
    event.sync = true;
    input_handler(&config, &data, &event);
    assert(reports == 1 && sent_x == 7 && sent_y == -4);
    event.type = INPUT_EV_MSC;
    event.code = PINCHWING_INPUT_MSC_POWER;
    event.value = 67;
    event.sync = false;
    input_handler(&config, &data, &event);
    assert(reports == 1 && x == 0 && y == 0);
    puts("PASS: ZMK mouse handler preserves X/Y across interleaved power/DPI reports");
    return 0;
}
"""
with tempfile.TemporaryDirectory(prefix="pinchwing-mouse-", dir="/tmp/opencode") as directory:
    path = Path(directory)
    (path / "test.c").write_text(source)
    subprocess.run([os.environ.get("CC", "cc"), "-std=c11", "-Wall", "-Wextra", "-Werror",
                    "-Wno-unused-parameter", "-Wno-unused-variable",
                    "-I" + str(repo / "tests/pinchwing_power/stubs"),
                    "-I" + str(repo / "include"),
                    str(path / "test.c"), "-o", str(path / "test")], check=True)
    subprocess.run([str(path / "test")], check=True)
