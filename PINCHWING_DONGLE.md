# Pinchwing BLE-to-USB dongle

A third nice!nano v2-compatible nRF52840 board is the split central. Both
keyboard halves connect to it over BLE; the dongle sends keyboard and mouse
reports to the computer over USB.

## Firmware and flashing

Build artifacts are in `build/firmware/pinchwing-dongle/`:

| File | Device |
| --- | --- |
| `pinchwing_dongle_left.uf2` | Left keyboard half |
| `pinchwing_dongle_right.uf2` | Right keyboard half with PMW3610 |
| `pinchwing_dongle_receiver.uf2` | USB dongle |
| `pinchwing_dongle_display.uf2` | USB dongle with Adafruit 2.7" SHARP display |
| `pinchwing_dongle_round.uf2` | USB dongle with 1.28" GC9A01 round TFT |
| `settings_reset.uf2` | Temporary reset firmware for **each of the three boards** |

These target `nice_nano@2.0.0//zmk`, matching the existing halves. A clone
must have compatible pin mapping and a compatible nRF52840 UF2 bootloader.

1. Turn off the halves. Connect one board at a time with a USB data cable.
2. Enter its UF2 bootloader (normally double-tap reset, or briefly bridge
   RST to GND twice). Copy `settings_reset.uf2` to the bootloader drive.
3. Let the board reboot and run reset firmware for a few seconds.
4. Re-enter its bootloader and copy its assigned firmware from the table.
5. Repeat for all three boards. The same reset image works on all three.
6. Plug the receiver into the computer and power on both halves. They
   automatically establish their split BLE bonds; do not pair the halves
   through the computer's Bluetooth settings.

The reset clears stored settings and Bluetooth bonds. You can remove the old
`Pinchwing V0` pairing from the computer. For USB use, the new receiver needs
no host Bluetooth pairing.

Test typing from each half, combos spanning halves, mouse movement, dragging,
scrolling, and DPI up/down from both sides. Press a key to wake a sleeping
half; sensor-only wake is not established. If USB input is absent after
switching outputs, use the existing output-toggle key to select USB.

## Configuration

- Shields: `boards/shields/pinchwing_dongle/`.
- Shared configuration: `config/pinchwing_dongle.conf`.
- Keymap: `config/pinchwing_dongle.keymap` includes the existing Pinchwing
  mouse keymap, retaining layers, combos and dynamic macros.
- Receiver: central with two peripheral slots, mock key scanner, and sleep
  disabled. USB output uses ZMK's normal USB preference.
- Halves: peripherals, with the existing debounce and sleep timing.
- Right sensor: existing wiring, axis orientation, 1600 CPI startup setting
  and power-up delay. A `zmk,input-split` node forwards motion to the receiver.
- DPI behavior: global split command; only the board with `mouse_sensor`
  applies it. This lets DPI keys on either half change the right sensor.
  Changes remain volatile and reset to 1600 CPI on reboot.

The receiver runs the keymap and macro logic. Ordinary keymap changes usually
need only a receiver flash; changes to shared behavior definitions or hardware
configuration can require reflashing the halves too. The halves require the
receiver with these images, including when their own USB cable is connected.

## Rebuild

The dongle targets, optional SHARP/GC9A01 display images, and reset target are in `build.yaml` for CI.
For a local build, initialize a west workspace using `config/west.yml`, install
its dependencies, and use:

```sh
export ZMK_APP=/absolute/path/to/workspace/zmk/app
export ZEPHYR_TOOLCHAIN_VARIANT=zephyr
export ZEPHYR_SDK_INSTALL_DIR="$HOME/zephyr-sdk-0.17.0"
# Activate the Python environment with west and CMake 3.31.10 first.
bash scripts/build-pinchwing-dongle.sh
```

The script builds all six UF2 files and saves logs, resolved Kconfig and
devicetree files, checked-out dependency revisions, and SHA-256 checksums.
Override `PINCHWING_BUILD_DIR` and `PINCHWING_OUTPUT_DIR` with absolute paths
if desired.

The initial local build uses the previous Pinchwing dependency snapshot:
ZMK `6a7590c1157480c96fa82340f1f6baef169e3116`, Zephyr SDK 0.17.0,
and CMake 3.31.10. CI continues to follow the repository's upstream `main`
policy. The dongle setup has been reported working on hardware. The individual
checks above remain useful when changing firmware or wiring.

Reference: [ZMK dongles](https://zmk.dev/docs/hardware-integration/dongle)
and [split pointing devices](https://zmk.dev/docs/hardware-integration/pointing).

## Adafruit 2.7" 400x240 SHARP display

Flash `build/firmware/pinchwing-dongle/pinchwing_dongle_display.uf2` onto the
**dongle only**, instead of `pinchwing_dongle_receiver.uf2`. The existing half
firmware already advertises battery levels and needs no update.
**Do not flash settings reset for this upgrade:** existing split bonds are kept.

With the dongle unplugged, connect the Adafruit breakout as follows:

| Adafruit display pin | nice!nano / Pro Micro pad | nRF52840 GPIO |
| --- | --- | --- |
| `VIN` | `VCC` (3.3 V) | Power, not GPIO |
| `GND` | `GND` | Ground |
| `CLK` | `D2` / `2` | `P0.17` |
| `DI` / `MOSI` | `D3` / `3` | `P0.20` |
| `CS` | `D4` / `4` | `P0.22` |

Use **VCC**, not the battery/B+ pad. These are Pro Micro **pad names**, not
physical pin counts from the USB connector. Clones sometimes print the nRF
GPIO numbers instead; use the third column in that case. There is no MISO
connection. Any optional display control pins remain unconnected with the
Adafruit breakout's normal serial-control configuration.

The breakout accepts 3.3 V power and logic; its onboard boost converter supplies
the panel. This wiring is for the **Adafruit breakout**, not a bare LCD ribbon.
Use short wires, then reconnect the dongle to USB.

The black-on-white landscape dashboard shows:

- Active layer name and number.
- Words per minute.
- USB readiness or Bluetooth host-profile connection.
- Number of connected half links (`0/2`, `1/2`, or `2/2`).
- Battery percentage for both peripheral slots.

BLE pairing order does not determine left/right. Initially the battery rows
are labeled **Half 1** and **Half 2**; pressing a key on each half identifies
them as **Left** and **Right** until the dongle reboots. Rows stay in BLE slot
order. `--` means no usable battery reading (including disconnected/zero-level
slots); battery percentages are estimates and are not charging indicators.
The link count is the number of established BLE connections, not a guarantee
that service discovery has finished.

The screen checks status every 250 ms and redraws changed labels only on a
dedicated display work queue. The Sharp driver maintains VCOM inversion every
500 ms even while the screen is static. Idle blanking is disabled.

Implementation:

- `boards/shields/pinchwing_sharp/`: SPI pins, 400x240 panel, LVGL configuration.
- `src/display/pinchwing_status.c`: custom dashboard.
- CI shield combination: `pinchwing_dongle_receiver pinchwing_sharp`.

Local build (from the west workspace, with the same environment as above):

```sh
west build -p -b nice_nano@2.0.0//zmk -d build/pinchwing-display "$ZMK_APP" -- \
  -DSHIELD="pinchwing_dongle_receiver pinchwing_sharp" \
  -DZMK_CONFIG=/absolute/path/to/yellowjacket-config/config \
  -DZMK_EXTRA_MODULES=/absolute/path/to/yellowjacket-config
```

The display image has been compiled and its pin mapping checked, but physical
display operation still needs verification. After flashing, check all four
dashboard sections, both batteries after typing on each side, and normal
typing/mouse movement while the screen updates. The display has no backlight.

## 1.28" GC9A01 round TFT (240x240)

For the photographed blue board labeled `1.28"TFT VER1.0 / 240*240 /
IC:GC9A01`, use:

`build/firmware/pinchwing-dongle/pinchwing_dongle_round.uf2`

For current battery/USB-power support, flash all three images listed under
[Battery and USB-power indicator](#battery-and-usb-power-indicator), without
settings reset. Disconnect the SHARP display before replacing it.

With USB unplugged, wire these seven connections:

| GC9A01 module label | nice!nano / Pro Micro pad | nRF52840 GPIO |
| --- | --- | --- |
| `RST` | `D6` / `6` | `P1.00` |
| `CS` | `D4` / `4` | `P0.22` |
| `DC` | `D5` / `5` | `P0.24` |
| `SDA` | `D3` / `3` | `P0.20` |
| `SCL` | `D2` / `2` | `P0.17` |
| `GND` | `GND` | Ground |
| `VCC` | `VCC` (3.3 V) | Power, not GPIO |

The table follows the header order visible in the photo. **SDA/SCL mean SPI
MOSI/clock here, not I2C.** The display's RST connects to **D6**, not to the
dongle's own RST pad. No MISO wire is required. Use the 3.3 V supply; the photo
does not establish 5 V tolerance. This module has no exposed BL/BLK control pin,
so this configuration does not provide backlight dimming.

The round display shows the artist-drawn white Bongo Cat from
[BongoCat-mac](https://github.com/Gamma-Software/BongoCat-mac), with pink paw
pads, over a spaceship starfield. Left/right keypresses animate the corresponding
screen-side paw, including a both-paws pose. After 15 seconds without keypresses
the cat gently bobs with a catnap caption. WPM, layer, USB/BLE host status,
connected-half count, and both batteries remain visible.

Each half shows a **lightning-bolt charging indicator while USB power is present**,
with no percentage, and its estimated battery percentage when unplugged.
Physical left is always on the left and physical right always on the right,
regardless of BLE slot order; no identifying keypress is needed with the current
half firmware. Missing or stale power reports show `--`.

At 80 WPM the starfield accelerates into warp over approximately 1.7 seconds:
stars brighten and stretch, the cat shakes, and the caption announces hyperspace.
Below 65 WPM it decelerates back to calm over approximately 2.5 seconds.
The separate thresholds prevent mode flicker. These use ZMK's reported WPM,
so changes follow its measurement window rather than instantaneous typing.
Tune `WARP_ENTER_WPM` and `WARP_EXIT_WPM` in `src/display/pinchwing_pet.c`.
Animation runs at a target 10 frames per second on the dedicated display queue;
actual smoothness needs hardware verification.

Artwork source, revision, and license are in `src/display/assets/bongo_cat/`.
`scripts/convert-bongo-cat.py` reproducibly downsamples the original sprites onto
a 192x96 canvas and stores the body and independent paws as indexed-color layers.
The body is tiled to bound decode allocations. Artwork occupies about 38 KB of
flash instead of four duplicated RGB565A8 poses occupying 221 KB. The generated
`src/display/bongo_cat.c` is checked in; firmware builds do not require Pillow.
The compact local Bongo Cat firmware is saved as
`build/firmware/pinchwing-dongle/pinchwing_dongle_round_cat_compact.uf2`.

### Diagnosing a blank screen with no USB input

If a display update stops both the screen and keyboard, double-tap the dongle's
reset button and restore a previously working receiver UF2. Do **not** use
settings reset; recovering the firmware does not require clearing split bonds.

The original full-pose Bongo Cat UF2 stayed in the bootloader after copying.
Its firmware extended to `0xC2F00`, beyond the `0xAD000` application boundary
in older Adafruit nRF52 bootloaders (for example v0.6.0). The exact installed
bootloader version has not been read, but a smaller older image restored the
device. A failed transfer must not be mistaken for a rendering crash.

The compact version ends at `0x96500` (460,032 payload bytes / 920,064 UF2 bytes).
`scripts/check-pinchwing-uf2.py` validates block integrity, family, and address
continuity and enforces a conservative budget below 512 KiB of payload. The local
build script runs it before publishing round-display firmware. Desktop rendering
and Cortex-M4/QEMU tests pass with the 48 KB LVGL heap and 4 KB display stack;
physical flashing and display operation still need confirmation.

`config/pinchwing_round_diagnostics.conf`, appended with `EXTRA_CONF_FILE` and
the `zmk-usb-logging` snippet, enables display startup checkpoints and stack
sentinel checks. It delays screen creation by ten seconds on the display queue
so the receiver can enumerate over USB before rendering starts. The diagnostic
artifact is `pinchwing_dongle_round_cat_diagnostics.uf2` in the firmware directory.
This is an investigation build, not a confirmed fix. It logs through the USB
serial port (typically `/dev/ttyACM0`); open the port before display startup.

The configuration uses the existing Zephyr GC9x01 driver with its default
initialization sequence, display inversion, 8 MHz SPI, and RGB565 with
high-byte-first pixel transfers. A 10% render buffer takes approximately
11.5 KB, with a 48 KB LVGL object/decode pool. Status updates run on the dedicated
display queue every 250 ms.

The round panel is rotated 180 degrees using the controller's hardware
orientation setting in `boards/shields/pinchwing_round/pinchwing_round.overlay`.
The rotated local image is
`build/firmware/pinchwing-dongle/pinchwing_dongle_round_cat_180.uf2`.

### Optical DPI readout

The round screen now shows the right optical sensor's reported DPI setting
beneath WPM. This is the configured sensor CPI (labeled DPI), not a measurement
of cursor speed or host-side sensitivity.

Flash these two images, without settings reset:

| Device | File in `build/firmware/pinchwing-dongle/` |
| --- | --- |
| Right half | `pinchwing_dongle_right_dpi.uf2` |
| Round-display dongle | `pinchwing_dongle_round_cat_180_dpi.uf2` |

The left half needs no update. The receiver image retains the 180-degree panel
orientation, Bongo Cat, warp transitions, and physical-left/right battery layout.
Both builds pass the legacy UF2-size check.

The right half confirms its startup setting (1600 CPI) by successfully applying
it after asynchronous sensor initialization. DPI keys on either half still
adjust it in 200-CPI steps from 200 to 3200; failed writes do not advance the
reported setting. A report is scheduled after each successful adjustment and
repeated every two seconds, so receiver reboot/reconnection recovers the value.
Reports expire after five seconds: `-- DPI` means no recent confirmed setting,
including with old right-half firmware, an unavailable sensor, or a sleeping/
disconnected right half. A right-half reboot restores its default DPI.

Implementation: `src/pointing/pinchwing_dpi.c` sends a private, non-synchronizing
MSC event through the existing optical split transport. It neither flushes mouse
reports nor generates local input activity that would prevent peripheral sleep.
No new GATT characteristic or pairing reset is needed. The receiver reads the
reported value independently of the active mouse layer.

Run `bash tests/pinchwing_dpi/run.sh` for host regression checks. Compilation
and host tests pass; verify on hardware that the value appears after connection,
changes from keys on both halves, expires when the right half is powered off,
and returns to 1600 after reboot.

Source: `boards/shields/pinchwing_round/` and
`src/display/pinchwing_status.c`. The CI shield combination is
`pinchwing_dongle_receiver pinchwing_round`. For a local build, use the
SHARP command above with that shield combination and a separate build directory.

Compilation and resolved wiring are verified; the module still needs a
physical test. Confirm the screen lights, text orientation, colors, both
battery readings, typing, and mouse movement. If the panel is lit but blank,
first check DC/RST and the SPI connections. Report any rotation or color issue
so the panel configuration can be adjusted to this module.

### Battery and USB-power indicator

Flash these three images from `build/firmware/pinchwing-dongle/`, without
settings reset, then restart all three devices:

| Device | File |
| --- | --- |
| Left half | `pinchwing_dongle_left_charging.uf2` |
| Right half | `pinchwing_dongle_right_charging_v3.uf2` |
| Round-display dongle | `pinchwing_dongle_round_cat_180_dpi_charging_v3.uf2` |

If an earlier charging firmware is already installed, update **only the right
half and dongle** to these `v3` images. Keep the left half's charging firmware.
Restart the right half and dongle after updating both.

The first charging release left the right battery at `--`. Its extra right-side
input channel exposed a pending-subscription collision with channel zero in
the pinned ZMK code. Changing the optical channel to 3 in `v2` passed an isolated
discovery test, but hardware testing still showed no battery and also lost
optical motion/DPI. That test did not establish end-to-end Bluetooth operation.

Version 3 restores the original right-side channel 0 and its single-characteristic
GATT layout. Power reports share that channel with DPI and motion, distinguished
by their event codes; there is no separate right-side power subscription.
Both right half and dongle must be updated together. The builds and host checks
pass, and version 3 has been confirmed working on hardware.

The cat display replaces a half's percentage with a lightning bolt whenever
that half detects USB power. This includes charge-only USB supplies and a fully
charged battery still connected to USB: the indicator means **USB power present**,
not a measurement of charging current or charge completion.

Unplugging restores a fresh voltage-based percentage, rather than the cached
USB-era 100%. Reports repeat every two seconds and the display refreshes every
250 ms. Unavailable readings and reports older than five seconds show `--`;
an actual zero-percent reading shows `0%`. Old half firmware cannot provide
these reports and shows `--` on the updated cat display.

`src/pinchwing_power.c` reads the nRF52840's VBUS detector directly, so the halves
keep USB data disabled. While unplugged, it samples the battery sensor on ZMK's
low-priority work queue, serializing ADC use with the normal battery worker.
Split input channel 1 identifies left power reports. The right half uses its
original channel 0 for optical motion, DPI, and power reports. Power and DPI use
distinct private MSC codes with `sync = false`, so neither flushes partial mouse
reports. Heartbeats use the split transport
directly and do not generate local input activity that would prevent half sleep.
The ordinary BLE Battery Service and SHARP dashboard retain their existing
voltage-based behavior.

Run `bash tests/pinchwing_power/run.sh` for host checks covering USB detection,
plugging in during a sample, unplugging, sensor failures, physical-side routing,
zero/full readings, lost reports, and clock wraparound. The three images compile
and pass the legacy UF2-size check. On hardware, check each half independently:
plug into a charger to see only the bolt, unplug to restore its percentage, and
turn it off to see `--` within five seconds. Also check typing, pointer motion,
and DPI reporting after reconnecting.

The discovery regression check verifies the built devicetrees expose exactly
one channel per half, then exercises the actual ZMK subscription helpers with
both connection orders and reconnects. The mouse check runs ZMK's actual mouse
handler with power and DPI reports inserted between the X and Y events:

```sh
python3 tests/pinchwing_power/check_split_discovery.py \
    "$ZMK_APP/src/split/bluetooth/central.c" \
    build/pinchwing-power/left/zephyr/zephyr.dts \
    build/pinchwing-power/right/zephyr/zephyr.dts \
    build/pinchwing-power/round/zephyr/zephyr.dts
python3 tests/pinchwing_power/check_mouse_interleaving.py \
    "$ZMK_APP/src/pointing/input_listener.c"
```
