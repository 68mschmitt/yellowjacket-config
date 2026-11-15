# Pinchwing BLE-to-USB dongle

A third nice!nano v2-compatible nRF52840 acts as central for both keyboard
halves and sends keyboard and mouse reports to the computer over USB.

## Firmware

Use the [current release guide](../releases/pinchwing-v4.md). Local bundles are
under `build/firmware/pinchwing-dongle/releases/`; `current/` points at the latest.
Display-only upgrades require flashing the dongle only, retaining split bonds.

For a completely new three-board setup, flash `settings_reset.uf2` on each
board, let it run briefly, then flash each board's assigned image. The halves
bond to the receiver automatically; do not pair them through the computer.
For existing working devices, normal updates do not require settings reset.

## Printable enclosure and add-ons

- [60° round-display enclosure](../../cases/pinchwing-dongle/README.md).
- [Internal display brace](../../cases/pinchwing-dongle/brace/README.md).
- [MCU keeper and recessed USB-C bezel](../../cases/pinchwing-dongle/usb-retrofit/README.md):
  two retrofit prototypes for the existing 18.3 mm nano base and housing.
  Test the keeper first, then verify bezel/socket alignment and cable seating.

Printable sources and outputs live under `cases/`; firmware build tools remain
under `scripts/`, with release artifacts under `build/firmware/`.

## Round GC9A01 display (240×240)

With USB unplugged:

| Display pin | nice!nano / Pro Micro pad | nRF52840 GPIO |
| --- | --- | --- |
| RST | D6 / 6 | P1.00 |
| CS | D4 / 4 | P0.22 |
| DC | D5 / 5 | P0.24 |
| SDA | D3 / 3 | P0.20 |
| SCL | D2 / 2 | P0.17 |
| GND | GND | Ground |
| VCC | VCC | 3.3 V |

SDA/SCL mean SPI MOSI/clock, not I2C. RST goes to D6, not the dongle's reset pad.
There is no MISO or backlight-control connection. The panel is rotated 180°
in hardware. The existing driver uses inversion, 8 MHz SPI, and RGB565.

The screen shows active layer, WPM, confirmed optical DPI, USB/BLE endpoint,
split links, and per-half power. A lightning bolt means USB power is present,
not measured charge current. Unplugged halves show estimated battery level;
missing/stale reports show `--`. Physical left/right are independent of pairing
order. Current half firmware reports every two seconds and expires after five.

The original Bongo Cat now has [layer-specific scenes](../development/display.md).
Paws respond to each half, layer changes wake the cat, and Base retains the
80-WPM warp / 65-WPM exit thresholds. The scene timer is 100 ms; status is 250 ms.

## SHARP 2.7" display (400×240)

| Adafruit pin | nice!nano / Pro Micro pad | nRF52840 GPIO |
| --- | --- | --- |
| VIN | VCC | 3.3 V |
| GND | GND | Ground |
| CLK | D2 / 2 | P0.17 |
| DI / MOSI | D3 / 3 | P0.20 |
| CS | D4 / 4 | P0.22 |

Build `pinchwing_dongle_receiver pinchwing_sharp`. Its monochrome dashboard
shows layer, WPM, output, connections, and batteries. The cat scenes are for
the round TFT only.

## Build

Initialize a west workspace from `config/west.yml`, install its dependencies,
and activate the west/CMake environment. From the repository root:

```sh
export ZMK_APP=/absolute/path/to/workspace/zmk/app
export ZEPHYR_TOOLCHAIN_VARIANT=zephyr
export ZEPHYR_SDK_INSTALL_DIR="$HOME/zephyr-sdk-0.17.0"
make build-dongle
```

This builds left, right, plain receiver, SHARP, round, and settings-reset
targets for `nice_nano@2.0.0//zmk`, with logs, configuration, devicetree,
dependency revisions, and checksums. Output defaults to
`build/firmware/pinchwing-dongle/development/`.
Override `PINCHWING_BUILD_DIR` and `PINCHWING_OUTPUT_DIR` as needed.

For just the round receiver, from the west workspace:

```sh
west build -b nice_nano@2.0.0//zmk -d /absolute/path/to/build/round "$ZMK_APP" -- \
  -DSHIELD="pinchwing_dongle_receiver pinchwing_round" \
  -DZMK_CONFIG=/absolute/path/to/yellowjacket-config/config \
  -DZMK_EXTRA_MODULES=/absolute/path/to/yellowjacket-config
```

## Source and troubleshooting

- `boards/shields/pinchwing_dongle/`: split roles, transport, and sensor wiring.
- `boards/shields/pinchwing_round/`: panel, rotation, render buffer, LVGL heap.
- `config/pinchwing_dongle.keymap`: shared mouse keymap and dynamic macros.
- `src/display/`: dashboard, cat renderer, and artwork.
- `src/pointing/pinchwing_dpi.c`, `src/pinchwing_power.c`: private split reports.

If a new UF2 fails to run, recover through the dongle bootloader with a known
working receiver image, retaining bonds. Always run `scripts/check-pinchwing-uf2.py`
on a release: older bootloaders have stricter limits than the linker region.
See [historical build/diagnostic notes](../archive/pinchwing-dongle-history.md)
for earlier charging revisions, DPI transport, and blank-screen investigations.
