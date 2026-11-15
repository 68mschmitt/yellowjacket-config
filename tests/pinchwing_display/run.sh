#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/../.." && pwd)"
: "${LVGL_DIR:?Set LVGL_DIR to the firmware LVGL checkout}"
build="$root/build/tests/pinchwing-display"
cmake -S "$root/tests/pinchwing_display" -B "$build" -G Ninja -DLVGL_DIR="$LVGL_DIR"
cmake --build "$build" --parallel
cd "$build"
./display_test
