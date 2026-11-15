#!/usr/bin/env python3
"""Check built channel topology and exercise the installed ZMK discovery helpers."""
from itertools import permutations
from pathlib import Path
import os
import re
import subprocess
import sys
import tempfile


repo = Path(__file__).resolve().parents[2]
if len(sys.argv) != 5:
    raise SystemExit(f"Usage: {sys.argv[0]} central.c left.dts right.dts receiver.dts")
upstream = Path(sys.argv[1]).read_text()


def helper(name):
    match = re.search(rf"static (?:bool|int) {name}\([^{{]+\{{.*?^\}}",
                      upstream, re.MULTILINE | re.DOTALL)
    if not match:
        raise SystemExit(f"Cannot find ZMK discovery helper: {name}")
    return match.group(0)


def channel(filename, label):
    text = (repo / "boards/shields/pinchwing_dongle" / filename).read_text()
    match = re.search(rf"\b{label}:\s*[^{{]+\{{[^}}]*\breg\s*=\s*<(0x[0-9a-fA-F]+|\d+)>",
                      text)
    if not match:
        raise SystemExit(f"Cannot find channel {label} in {filename}")
    return int(match.group(1), 0)


mouse = channel("pinchwing-input.dtsi", "mouse_split")
left = channel("pinchwing-power.dtsi", "power_left")
assert mouse == 0 and left == 1, "Preserve the original optical channel and left power channel"


def built_channels(path):
    channels = {}
    for label, body in re.findall(r"(\w+):[^{};]+\{([^{}]*)\};", Path(path).read_text()):
        if '"zmk,input-split"' not in body or 'status = "disabled"' in body:
            continue
        match = re.search(r"\breg\s*=\s*<\s*(0x[0-9a-fA-F]+|\d+)\s*>", body)
        assert match, f"Missing input channel ID for {label}"
        channels[label] = int(match.group(1), 0)
    return channels


expected = [{"power_left": left}, {"mouse_split": mouse},
            {"power_left": left, "mouse_split": mouse}]
for path, topology in zip(sys.argv[2:], expected):
    actual = built_channels(path)
    assert actual == topology, f"{path}: expected {topology}, got {actual}"

# One subscription per half, regardless of connection order, including reconnects.
cases = ",\n".join("{" + ", ".join(f"{{{side}, {reg}}}" for side, reg in order) + "}"
                   for order in permutations([(0, left), (1, mouse)]))
source = r"""
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <errno.h>
#include <string.h>
#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))
struct bt_conn { int unused; };
struct bt_gatt_subscribe_params { uint16_t value_handle, ccc_handle; };
struct peripheral_input_slot {
    struct bt_conn *conn;
    struct bt_gatt_subscribe_params sub;
    uint8_t reg;
};
static struct peripheral_input_slot peripheral_input_slots[2];
"""
source += "\n".join(helper(name) for name in (
    "input_slot_is_open", "input_slot_is_pending",
    "reserve_next_open_input_slot", "find_pending_input_slot"))
source += """
int main(void) {
    struct bt_conn connections[2];
    struct { unsigned int side; uint8_t reg; } cases[][2] = {
""" + cases + r"""
    };
    for (size_t c = 0; c < ARRAY_SIZE(cases); c++) {
        memset(peripheral_input_slots, 0, sizeof(peripheral_input_slots));
        for (int reconnect = 0; reconnect < 2; reconnect++) {
            for (size_t i = 0; i < ARRAY_SIZE(peripheral_input_slots); i++) {
                struct bt_conn *conn = &connections[cases[c][i].side];
                struct peripheral_input_slot *reserved = NULL, *pending = NULL;
                if (reserve_next_open_input_slot(&reserved, conn) < 0) return 1;
                reserved->sub.value_handle = 10 + i * 4;
                /* The CCC and CPF discovery callbacks both look up the pending slot. */
                if (find_pending_input_slot(&pending, conn) < 0 || pending != reserved) {
                    fprintf(stderr, "FAIL: channel %u selected an earlier channel's "
                            "subscription (case %zu, reconnect %d)\n",
                            cases[c][i].reg, c, reconnect);
                    return 1;
                }
                pending->sub.ccc_handle = reserved->sub.value_handle + 1;
                if (find_pending_input_slot(&pending, conn) < 0 || pending != reserved)
                    return 1;
                pending->reg = cases[c][i].reg;
            }
            for (size_t i = 0; i < ARRAY_SIZE(peripheral_input_slots); i++) {
                if (peripheral_input_slots[i].reg != cases[c][i].reg) return 1;
                /* Disconnect, then rediscover with the retained subscription structs. */
                peripheral_input_slots[i].conn = NULL;
            }
        }
    }
    puts("PASS: built single-channel halves, ZMK discovery in both orders and reconnects");
    return 0;
}
"""
with tempfile.TemporaryDirectory(prefix="pinchwing-discovery-", dir="/tmp/opencode") as directory:
    path = Path(directory)
    (path / "test.c").write_text(source)
    subprocess.run([os.environ.get("CC", "cc"), "-std=c11", "-Wall", "-Wextra", "-Werror",
                    str(path / "test.c"), "-o", str(path / "test")], check=True)
    subprocess.run([str(path / "test")], check=True)
