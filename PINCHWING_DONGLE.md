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

The three dongle targets and existing reset target are in `build.yaml` for CI.
For a local build, initialize a west workspace using `config/west.yml`, install
its dependencies, and use:

```sh
export ZMK_APP=/absolute/path/to/workspace/zmk/app
export ZEPHYR_TOOLCHAIN_VARIANT=zephyr
export ZEPHYR_SDK_INSTALL_DIR="$HOME/zephyr-sdk-0.17.0"
# Activate the Python environment with west and CMake 3.31.10 first.
bash scripts/build-pinchwing-dongle.sh
```

The script builds all four UF2 files and saves logs, resolved Kconfig and
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
