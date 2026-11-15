#!/usr/bin/env bash
set -euo pipefail
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
out="$(mktemp -d /tmp/opencode/pinchwing-power-tests.XXXXXX)"
trap 'rm -rf "$out"' EXIT
for target in left right receiver; do
    central=0
    left=0
    right=0
    if [[ "$target" == receiver ]]; then central=1; fi
    if [[ "$target" == left ]]; then left=1; fi
    if [[ "$target" == right ]]; then right=1; fi
    "${CC:-cc}" -std=c11 -Wall -Wextra -Werror -Wno-unused-variable \
        -DCONFIG_ZMK_SPLIT_ROLE_CENTRAL="$central" \
        -DCONFIG_SHIELD_PINCHWING_DONGLE_RIGHT="$right" \
        -DCONFIG_SHIELD_PINCHWING_DONGLE_LEFT="$left" \
        -I"$repo/tests/pinchwing_power/stubs" \
        -I"$repo/tests/pinchwing_dpi/stubs" -I"$repo/include" \
        "$repo/tests/pinchwing_power/main.c" -o "$out/$target"
    "$out/$target"
done
