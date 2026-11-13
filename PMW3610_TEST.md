# Right-half PMW3610 test

Printable cases, fit coupons, and the lens-cover insert are in
[cases/yellowjacket/mouse/](cases/yellowjacket/mouse/README.md).

Branch: `test/pmw3610-right`

Host Bluetooth name: **YJ Mouse Test**. The left half remains the central;
the right half forwards sensor events over the existing BLE split connection.
The test keymap includes `config/yellowjacket.keymap`.

## Hardware

SideraKB PMW3610 PCB **Rev 1**, with LM18-LSI lens, on the right nice!nano v2:

| Sensor signal | nice!nano |
| --- | --- |
| VIN | VCC (3.3 V) |
| GND | GND |
| SCLK | P0.06 (TX position) |
| SDIO | P0.08 (RX position) |
| nCS | P1.01 (extra pad) |
| MOTION | P1.02 (extra pad) |

JP1 bridges pads 1–2 for 3.3 V logic; pad 3 remains disconnected.
No reset wire is used. Rev 1 has an internal reset pull-up, with optional R1.
Header and FFC connector pin orders differ; follow the signal labels.

Mount the lens facing the desk, approximately 2.4 mm from its lowest reference
plane to the tracking surface. Include the height of the mouse skates in this
measurement.

## Build and flash

Local compilation succeeded for all three mouse-test images with CMake 3.31.10,
Zephyr SDK 0.17.0, and ZMK `6a7590c`. The UF2 files are in `build/firmware/`,
alongside build logs, resolved configs, SHA-256 checksums, and a frozen dependency
manifest. The UF2 block format and nRF52840 family ID were verified. Physical
sensor operation still needs testing on the keyboard.

The isolated local workspace is `/tmp/opencode/yellowjacket-mouse-build`, with
Python tools in `/tmp/opencode/yellowjacket-mouse-venv`. Rebuild using that
environment's `west`, `ZEPHYR_TOOLCHAIN_VARIANT=zephyr`, and
`ZEPHYR_SDK_INSTALL_DIR=/home/mschmitt/zephyr-sdk-0.17.0`. SDK 0.17.1 failed
with a Picolibc lock type conflict against this Zephyr revision.

The existing GitHub Actions workflow runs on branch pushes and supports manual
dispatch. Commit and push this branch, then download the firmware archive from
the successful build:

| Artifact | Flash onto |
| --- | --- |
| `yj_mouse_left` | Left half |
| `yj_mouse_right` | Right half |
| `yj_mouse_right_logging` | Right half, instead of the normal image, for debugging |

Flash **both** mouse-test halves. Connect the computer to the **left** half over
USB or Bluetooth for keyboard/mouse input. USB on the right logging build is for
logs; it does not make the right half the host-facing central.

Existing bonds/settings survive a firmware flash. The new name does not create
a new Bluetooth identity, and the host may retain the old display name. If
pairing or split reconnection fails, use the existing `settings_reset` image on
both halves, then reflash their respective mouse-test images and pair the left
half again. This clears saved Bluetooth pairings.

For a local build, use a west workspace initialized from this branch's
`config/west.yml`, run `west update`, and pass this repository as
`ZMK_EXTRA_MODULES`. For example, from this repository, with `ZMK_APP` pointing
to that workspace's ZMK app:

```sh
make build-yj1-left SHIELD=yellowjacket_mouse_left \
  WEST_BUILD_DIR="$PWD/build/mouse-left" ZMK_APP=/path/to/workspace/zmk/app
make build-yj1-left SHIELD=yellowjacket_mouse_right \
  WEST_BUILD_DIR="$PWD/build/mouse-right" ZMK_APP=/path/to/workspace/zmk/app
make build-logging SHIELD=yellowjacket_mouse_right \
  WEST_BUILD_DIR="$PWD/build/mouse-right-logging" ZMK_APP=/path/to/workspace/zmk/app \
  CMAKE_ARGS=-DCONFIG_PMW3610_ALT_LOG_LEVEL_DBG=y
```

The Makefile's existing target name can be overridden with `SHIELD`; these
commands build the new mouse shields.

## Initial behavior and tuning

- Sensor movement is always enabled, including on the base layer.
- Initial resolution is **1000 CPI**.
- `invert-y` is an initial orientation assumption. In
  `boards/shields/yellowjacket_mouse/yellowjacket_mouse_right.overlay`, adjust
  `invert-x`, `invert-y`, and/or `swap-xy` to match the mounting.
- Existing mouse-layer buttons and scrolling still work. Hold the Backspace
  thumb key to access the mouse layer; the base-layer L position is left click,
  and the Y position is right click on that layer.
- The right-half config adds a 1000 ms sensor startup delay for switched VCC.
- Existing sleep settings are retained. Press a key to wake from deep sleep;
  sensor-only wake is not established by this configuration.

## Hardware checks

1. Verify typing from both halves and USB/Bluetooth input through the left.
2. Slide right, left, forward, and backward; adjust axes if needed.
3. Check clicks, dragging, and scrolling through the existing mouse layer.
4. Lift and reposition the keyboard, then confirm tracking resumes.
5. Test after idle, deep sleep, and a power cycle, including battery-only use.

If typing works but motion does not, flash the right logging image and read its
USB serial logs. An incorrect product ID (especially `0xFF`) points toward
power, chip select, or SPI wiring/initialization; the startup delay is already
enabled. If initialization succeeds, check lens clearance, surface, and MOTION
wiring.

The driver is pinned in `config/west.yml`; ZMK and its reusable build workflow
continue following `main`. Local firmware builds passed; physical behavior must
still be verified before treating this as a working hardware configuration.

References:
- [Rev 1 module documentation](https://github.com/siderakb/pmw3610-pcb/blob/v1.0.0/README.md)
- [PMW3610 driver](https://github.com/badjeff/zmk-pmw3610-driver)
- [ZMK pointing integration](https://zmk.dev/docs/hardware-integration/pointing)
