# Yellowjacket ZMK Config

ZMK user configuration and custom shield definitions for the 32-key split Yellowjacket keyboard.

This repository targets `nice_nano@2.0.0//zmk` and builds firmware for two named variants, `yellowjacket_yj1` and `yellowjacket_yj2`, plus utility and debug images defined in `build.yaml`.

The `test/pmw3610-right` branch also includes **Pinchwing V0**, a named variant
with a right-half PMW3610 sensor. See [PMW3610_TEST.md](PMW3610_TEST.md) for wiring,
firmware artifacts, flashing, and tuning.

For a third nice!nano acting as a BLE-to-USB receiver for both Pinchwing halves,
see [PINCHWING_DONGLE.md](PINCHWING_DONGLE.md) for firmware and flashing instructions.

Printable pressure-fit cases, sensor fit coupons, and the lens-cover insert
are in [cases/yellowjacket/mouse/](cases/yellowjacket/mouse/README.md).

## Repository Layout

- `config/` contains the ZMK user config entry points: `west.yml`, `yellowjacket.conf`, and `yellowjacket.keymap`.
- `boards/shields/yellowjacket/` contains the shared Yellowjacket shield definition, physical layout, matrix transform, and GPIO scan wiring.
- `boards/shields/yellowjacket_yj1/` defines the YJ1 left/right shield names.
- `boards/shields/yellowjacket_yj2/` defines the YJ2 left/right shield names.
- `zephyr/module.yml` exposes this repo as a Zephyr module with `board_root: .`.
- `build.yaml` defines the firmware build matrix.
- `.github/workflows/build.yml` delegates builds to ZMK's shared `build-user-config.yml` workflow.
- `DYNAMIC_MACROS.md` documents the Vim-style runtime macro implementation, trigger flow, limits, and verification.
- `tests/dynamic_macro/` contains the host-side dynamic macro driver test harness.
- `FRICTION.md` tracks known reproducibility, local-build, dynamic-macro, and hardware-verification follow-ups.

## Firmware Targets

`build.yaml` currently defines these artifacts:

| Artifact | Board | Shield | Notes |
| --- | --- | --- | --- |
| `yj1_left` | `nice_nano@2.0.0//zmk` | `yellowjacket_yj1_left` | Left half, split central |
| `yj1_right` | `nice_nano@2.0.0//zmk` | `yellowjacket_yj1_right` | Standard right-half build |
| `yj2_left` | `nice_nano@2.0.0//zmk` | `yellowjacket_yj2_left` | Left half, split central |
| `yj2_right` | `nice_nano@2.0.0//zmk` | `yellowjacket_yj2_right` | Standard right-half build |
| `settings_reset` | `nice_nano@2.0.0//zmk` | `settings_reset` | Utility image for clearing saved settings |
| `yj1_left_logging` | `nice_nano@2.0.0//zmk` | `yellowjacket_yj1_left` | Debug image with `zmk-usb-logging` |

The `yellowjacket_yj1` and `yellowjacket_yj2` shields currently reuse the same base hardware definition in `boards/shields/yellowjacket/yellowjacket.dtsi`, and differ only in their advertised BLE names (`YJ1`/`YJ1_R` and `YJ2`/`YJ2_R`). The right-half overlays add a column offset for the split transform.

ZMK Studio is not enabled on any target. Keymap changes are made by editing `config/yellowjacket.keymap` and reflashing.

## Keymap Summary

`config/yellowjacket.keymap` defines a custom non-QWERTY base layer and several utility layers:

| Index | Layer |
| --- | --- |
| 0 | `Base` |
| 1 | `Number` |
| 2 | `Arrows` |
| 3 | `Mouse` |
| 4 | `Functions` |
| 5 | `System` |
| 6 | `Brackets` |
| 7 | `No Mods` |
| 8 | `RecSel` (`REC_L`) |
| 9 | `PlaySel` (`PLY_L`) |
| 10 | `Recording` (`DMR_L`) |

Layer indices are declared as `#define`s at the top of the keymap and must stay in sync with the declaration order of the nodes in the `keymap` block. Layers 8-10 implement the dynamic macro state machine: `Z+X` opens record selection, `C+D` opens playback selection, and the transparent recording layer keeps normal typing available until `Z+X` stops recording. See [DYNAMIC_MACROS.md](DYNAMIC_MACROS.md) for the register map, limits, and verification details.

Notable behaviors in the keymap:

- home-row mods (`hm`) on the base alpha layer
- hold-tap thumb keys (`lt_qk`) for layer access
- 51 combos: escape, punctuation, quotes, quick numbers, quick symbols, caps word, one-shot shift, layer toggles, macOS shortcuts, and dynamic macro triggers
- combos default to a 30 ms timeout via the `COMBO` macro; `combo_lower_q` deliberately uses 60 ms because it stands in for a real alpha key, and the dynamic macro trigger combos use 50 ms
- macOS Mission Control gestures via `Ctrl`+arrow macros
- Bluetooth profile selection and clear actions on the system layer
- media controls and output toggle on the system layer
- Vim-style dynamic macros with 25 letter registers (`a`-`z` except `q`): `Z+X` records/stops and `C+D` plays back
- `No Mods` is a toggled clone of the base alphas without home-row mods, for when hold-tap timing gets in the way; its thumb keys are `&trans` so they inherit the base layer's layer-taps

## Configuration Summary

`config/yellowjacket.conf` enables and configures:

- split keyboard support over BLE
- pointing support (`CONFIG_ZMK_POINTING`)
- long idle and sleep timeouts (50 min idle, 4 h deep sleep)
- higher controller transmit power (`CONFIG_BT_CTLR_TX_PWR_PLUS_8`)
- 10 ms kscan debounce on press and release
- an enlarged split position queue for the central half
- dynamic macro storage sized for 25 registers x 64 events, with a 20 ms playback event delay

No combo Kconfig tuning is needed. `CONFIG_ZMK_COMBO_MAX_COMBOS_PER_KEY` was deprecated upstream in [zmk#2849](https://github.com/zmkfirmware/zmk/pull/2849) (April 2025) — combo storage is now sized automatically from the devicetree, and setting the option emits a deprecation warning. Since `config/west.yml` tracks `zmkfirmware/zmk@main`, the option has been removed. If this config is ever pinned to a ZMK revision older than that, the option must come back, or the key positions carrying more than five combos will be silently dropped at runtime.

Display support is not enabled. The user config no longer carries display options, and the i2c pin control fragment has been removed from the shield. Some `ZMK_DISPLAY`/`LVGL` scaffolding is still present in the shield `Kconfig.defconfig` files but is inert unless `CONFIG_ZMK_DISPLAY` is turned on.

## Building

### GitHub Actions

Every push, pull request, and manual workflow dispatch runs `.github/workflows/build.yml`, which uses ZMK's shared user-config build workflow and the targets listed in `build.yaml`. These CI firmware builds are the primary full-firmware verification path for this repository.

### Local Builds

Follow the official ZMK setup guide to prepare a local west workspace, including `west`, Zephyr SDK/toolchain prerequisites, and `west update`:

- https://zmk.dev/docs/development/setup

When building locally, use the exact board, shield, snippet, and extra CMake options shown in `build.yaml`. From a west workspace root, a typical build looks like:

```sh
west build -p -b nice_nano@2.0.0//zmk zmk/app -- \
  -DSHIELD=yellowjacket_yj1_left \
  -DZMK_CONFIG="$HOME/projects/yellowjacket-config/config" \
  -DZMK_EXTRA_MODULES="$HOME/projects/yellowjacket-config"
```

If you run the command from inside `zmk/app`, omit the `zmk/app` source argument. `ZMK_EXTRA_MODULES` is required for local builds because this repository is also a Zephyr module: it supplies the out-of-tree dynamic macro behavior, devicetree binding, and module metadata consumed by the firmware build. For the `yj1_left_logging` debug target, add `-S zmk-usb-logging` before `--`, matching the snippet shown in `build.yaml`.

### Host Dynamic Macro Tests

The dynamic macro driver has a host-side harness that compiles the real driver against stubs, without a Zephyr SDK:

```sh
cd tests/dynamic_macro
make clean && make && ./test && make clean
```

This test covers the dynamic macro driver only. It complements, but does not replace, CI firmware builds and on-hardware validation.

### Upstream Tracking and Reproducibility

Current policy is to track upstream ZMK `main`: `config/west.yml` uses `revision: main`, and the GitHub Actions workflow delegates to `zmkfirmware/zmk/.github/workflows/build-user-config.yml@main`. That keeps the config close to upstream fixes and API changes, but it means rebuilds are not guaranteed to be byte-for-byte reproducible over time.

For a reproducible release or bisect, record the ZMK commit reported in the CI logs/artifacts. If deterministic rebuilds become more important than tracking latest upstream, pin both `config/west.yml` and the workflow reference to tested commits, then rerun the dynamic macro host test and all firmware builds before publishing artifacts.

## Notes

- The shared shield definition describes a 32-key physical layout (positions 0-31). The matrix transform declares 34 columns to cover split overhead.
- `tests/dynamic_macro` is a host-only test suite for the dynamic macro driver; CI firmware builds remain the primary full-firmware verification path.
- The `yellowjacket_yj1.*` and `yellowjacket_yj2.*` files in `config/` are symlinks to the `yellowjacket.*` originals, so editing the base file updates both variants. Replace a symlink with a real file only when a variant genuinely needs to diverge.
