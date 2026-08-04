# Yellowjacket ZMK Config

ZMK user configuration and custom shield definitions for the 32-key split Yellowjacket keyboard.

This repository targets `nice_nano/nrf52840/zmk` and builds firmware for two named variants, `yellowjacket_yj1` and `yellowjacket_yj2`, plus utility and debug images defined in `build.yaml`.

## Repository Layout

- `config/` contains the ZMK user config entry points: `west.yml`, `yellowjacket.conf`, and `yellowjacket.keymap`.
- `boards/shields/yellowjacket/` contains the shared Yellowjacket shield definition, physical layout, matrix transform, and GPIO scan wiring.
- `boards/shields/yellowjacket_yj1/` defines the YJ1 left/right shield names.
- `boards/shields/yellowjacket_yj2/` defines the YJ2 left/right shield names.
- `zephyr/module.yml` exposes this repo as a Zephyr module with `board_root: .`.
- `build.yaml` defines the firmware build matrix.
- `.github/workflows/build.yml` delegates builds to ZMK's shared `build-user-config.yml` workflow.

## Firmware Targets

`build.yaml` currently defines these artifacts:

| Artifact | Board | Shield | Notes |
| --- | --- | --- | --- |
| `yj1_left` | `nice_nano/nrf52840/zmk` | `yellowjacket_yj1_left` | Left half, split central |
| `yj1_right` | `nice_nano/nrf52840/zmk` | `yellowjacket_yj1_right` | Standard right-half build |
| `yj2_left` | `nice_nano/nrf52840/zmk` | `yellowjacket_yj2_left` | Left half, split central |
| `yj2_right` | `nice_nano/nrf52840/zmk` | `yellowjacket_yj2_right` | Standard right-half build |
| `settings_reset` | `nice_nano/nrf52840/zmk` | `settings_reset` | Utility image for clearing saved settings |
| `yj1_left_logging` | `nice_nano/nrf52840/zmk` | `yellowjacket_yj1_left` | Debug image with `zmk-usb-logging` |

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

Layer indices are declared as `#define`s at the top of the keymap and must stay in sync with the declaration order of the nodes in the `keymap` block.

Notable behaviors in the keymap:

- home-row mods (`hm`) on the base alpha layer
- hold-tap thumb keys (`lt_qk`) for layer access
- 43 combos: escape, punctuation, quotes, quick numbers, quick symbols, caps word, one-shot shift, and layer toggles
- combos default to a 30 ms timeout via the `COMBO` macro; `combo_lower_q` deliberately uses 60 ms because it stands in for a real alpha key
- macOS Mission Control gestures via `Ctrl`+arrow macros
- Bluetooth profile selection and clear actions on the system layer
- media controls and output toggle on the system layer
- `No Mods` is a toggled clone of the base alphas without home-row mods, for when hold-tap timing gets in the way; its thumb keys are `&trans` so they inherit the base layer's layer-taps

## Configuration Summary

`config/yellowjacket.conf` enables and configures:

- split keyboard support over BLE
- pointing support (`CONFIG_ZMK_POINTING`)
- long idle and sleep timeouts (50 min idle, 4 h deep sleep)
- higher controller transmit power (`CONFIG_BT_CTLR_TX_PWR_PLUS_8`)
- 10 ms kscan debounce on press and release
- an enlarged split position queue for the central half

No combo Kconfig tuning is needed. `CONFIG_ZMK_COMBO_MAX_COMBOS_PER_KEY` was deprecated upstream in [zmk#2849](https://github.com/zmkfirmware/zmk/pull/2849) (April 2025) — combo storage is now sized automatically from the devicetree, and setting the option emits a deprecation warning. Since `config/west.yml` tracks `zmkfirmware/zmk@main`, the option has been removed. If this config is ever pinned to a ZMK revision older than that, the option must come back, or the key positions carrying more than five combos will be silently dropped at runtime.

Display support is not enabled. The user config no longer carries display options, and the i2c pin control fragment has been removed from the shield. Some `ZMK_DISPLAY`/`LVGL` scaffolding is still present in the shield `Kconfig.defconfig` files but is inert unless `CONFIG_ZMK_DISPLAY` is turned on.

## Building

### GitHub Actions

Every push, pull request, and manual workflow dispatch runs `.github/workflows/build.yml`, which uses ZMK's shared user-config build workflow and the targets listed in `build.yaml`.

### Local Builds

Follow the official ZMK setup guide to prepare a local workspace:

- https://zmk.dev/docs/development/setup

When building locally, use the board, shield, snippet, and extra CMake options shown in `build.yaml`. For example, the debug target uses the `zmk-usb-logging` snippet.

## Notes

- The shared shield definition describes a 32-key physical layout (positions 0-31). The matrix transform declares 34 columns to cover split overhead.
- CI is the primary verification path in this repository; there is no separate test suite in the repo itself.
- The `yellowjacket_yj1.*` and `yellowjacket_yj2.*` files in `config/` are symlinks to the `yellowjacket.*` originals, so editing the base file updates both variants. Replace a symlink with a real file only when a variant genuinely needs to diverge.
