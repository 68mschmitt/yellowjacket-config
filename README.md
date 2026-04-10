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
| `yj1_left` | `nice_nano/nrf52840/zmk` | `yellowjacket_yj1_left` | Left half with `studio-rpc-usb-uart` and `CONFIG_ZMK_STUDIO=y` |
| `yj1_right` | `nice_nano/nrf52840/zmk` | `yellowjacket_yj1_right` | Standard right-half build |
| `yj2_left` | `nice_nano/nrf52840/zmk` | `yellowjacket_yj2_left` | Left half with `studio-rpc-usb-uart` and `CONFIG_ZMK_STUDIO=y` |
| `yj2_right` | `nice_nano/nrf52840/zmk` | `yellowjacket_yj2_right` | Standard right-half build |
| `settings_reset` | `nice_nano/nrf52840/zmk` | `settings_reset` | Utility image for clearing saved settings |
| `yj1_left_logging` | `nice_nano/nrf52840/zmk` | `yellowjacket_yj1_left` | Debug image with `zmk-usb-logging` |

The `yellowjacket_yj1` and `yellowjacket_yj2` shields currently reuse the same base hardware definition in `boards/shields/yellowjacket/yellowjacket.dtsi`. The right-half overlays add a column offset for the split transform.

## Keymap Summary

`config/yellowjacket.keymap` defines a custom non-QWERTY base layer and several utility layers:

- `Base`
- `Number`
- `Arrows`
- `Mouse`
- `Functions`
- `System`
- `Brackets`
- `Gaming`
- `Mouse 2`

Notable behaviors in the keymap:

- home-row mods on the base alpha layer
- hold-tap thumb keys for layer access
- 30 ms combos for escape, punctuation, quick numbers, quick symbols, caps word, and layer toggles
- Bluetooth profile selection and clear actions on the system layer
- media controls, output toggle, and `studio_unlock` on the system layer

## Configuration Summary

`config/yellowjacket.conf` enables and configures:

- split keyboard support over BLE
- pointing support
- increased combo density with `CONFIG_ZMK_COMBO_MAX_COMBOS_PER_KEY=50`
- long idle and sleep timeouts
- higher controller transmit power

Display-related options are present in the config and shield Kconfig files, but they are currently commented out in the user config.

## Building

### GitHub Actions

Every push, pull request, and manual workflow dispatch runs `.github/workflows/build.yml`, which uses ZMK's shared user-config build workflow and the targets listed in `build.yaml`.

### Local Builds

Follow the official ZMK setup guide to prepare a local workspace:

- https://zmk.dev/docs/development/setup

When building locally, use the board, shield, snippet, and extra CMake options shown in `build.yaml`. For example, the left-hand builds enable ZMK Studio, while the debug target uses the `zmk-usb-logging` snippet.

## Notes

- The shared shield definition describes a 32-key physical layout.
- CI is the primary verification path in this repository; there is no separate test suite in the repo itself.
