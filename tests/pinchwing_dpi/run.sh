#!/usr/bin/env bash
set -euo pipefail
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
out="$(mktemp -d)"
trap 'rm -rf "$out"' EXIT
for right in 0 1; do
    "${CC:-cc}" -std=c11 -Wall -Wextra -Werror -Wno-unused-variable \
        -DCONFIG_SHIELD_PINCHWING_DONGLE_RIGHT="$right" \
        -I"$repo/tests/pinchwing_dpi/stubs" -I"$repo/include" \
        "$repo/tests/pinchwing_dpi/main.c" -o "$out/test-$right"
    "$out/test-$right"
done
