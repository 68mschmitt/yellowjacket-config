#!/usr/bin/env bash
# Build in an initialized west workspace. west, cmake and ninja must be on PATH.
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
: "${ZMK_APP:?Set ZMK_APP to the absolute path of zmk/app in your west workspace}"
build_root="${PINCHWING_BUILD_DIR:-$repo/build/pinchwing-dongle}"
output="${PINCHWING_OUTPUT_DIR:-$repo/build/firmware/pinchwing-dongle}"
mkdir -p "$build_root" "$output"
cd "$ZMK_APP"

for shield in pinchwing_dongle_left pinchwing_dongle_right pinchwing_dongle_receiver settings_reset; do
    echo "Building $shield"
    if ! west build -p -b nice_nano@2.0.0//zmk \
        -d "$build_root/$shield" "$ZMK_APP" -- \
        -DSHIELD="$shield" -DZMK_CONFIG="$repo/config" \
        -DZMK_EXTRA_MODULES="$repo" > "$output/$shield.log" 2>&1; then
        tail -n 80 "$output/$shield.log"
        exit 1
    fi
    cp "$build_root/$shield/zephyr/zmk.uf2" "$output/$shield.uf2"
    cp "$build_root/$shield/zephyr/.config" "$output/$shield.config"
    cp "$build_root/$shield/zephyr/zephyr.dts" "$output/$shield.dts"
done

# Record the exact checked-out revisions of the modules available to this build.
python - "$output/west-frozen.yml" <<'PY'
import subprocess
import sys
import yaml
from west.manifest import Manifest

manifest = Manifest.from_file()
frozen = manifest.as_dict()
cloned = {p.name: p for p in manifest.projects
          if p.name != "manifest" and p.is_cloned()}
projects = []
for project in frozen["manifest"]["projects"]:
    if project["name"] in cloned:
        p = cloned[project["name"]]
        project["revision"] = subprocess.check_output(
            ["git", "-C", p.abspath, "rev-parse", "HEAD"], text=True).strip()
        projects.append(project)
frozen["manifest"]["projects"] = projects
with open(sys.argv[1], "w") as f:
    yaml.safe_dump(frozen, f, sort_keys=False)
PY
(cd "$output" && sha256sum ./*.uf2 > SHA256SUMS)
echo "Firmware saved to $output"
