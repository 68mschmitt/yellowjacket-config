# Development follow-ups

Known friction, limitations, and follow-up checks for this config.

## Upstream-main reproducibility policy

Current policy is to track upstream ZMK `main` in both places that select upstream code:

- `config/west.yml` uses `revision: main` for `zmkfirmware/zmk`.
- `.github/workflows/build.yml` delegates to `build-user-config.yml@main`.

This is intentional for now: it keeps the config close to upstream ZMK API changes and fixes. The trade-off is that a rebuild at a later date may use different upstream code even if this repository has not changed.

Follow-up checklist:

- Record the upstream ZMK commit from CI logs/artifacts when keeping a firmware build for later reproduction.
- Before important flashes or releases, check recent upstream ZMK changes that affect combos, behaviors, split, board revisions, or Zephyr versions.
- If deterministic rebuilds become the priority, pin both `config/west.yml` and the workflow reference to tested commits, rerun all firmware builds, and document the pin/update procedure before publishing artifacts.
- When unpinning or advancing a pin, rerun the dynamic macro host test and let CI rebuild every target in `build.yaml`.

## Local build prerequisites

Local firmware builds need a full ZMK/west workspace and Zephyr toolchain, not just this repository. They also need `ZMK_EXTRA_MODULES` because this repository is both the user config and a Zephyr module that provides the out-of-tree dynamic macro behavior and devicetree binding.

Follow-up checklist:

- Follow the ZMK development setup guide and run `west update` in the workspace.
- Use board target strings exactly as shown in `build.yaml`, currently `nice_nano@2.0.0//zmk`.
- Pass `-DZMK_CONFIG=<repo>/config` and `-DZMK_EXTRA_MODULES=<repo>` on local `west build` commands.
- For debug firmware, add `-S zmk-usb-logging`, matching the snippet used by the `yj1_left_logging` artifact.
- After local builds, inspect RAM usage in the build log because dynamic macros allocate 25 x 64 event slots on the central half.

## Dynamic macro limitations

Dynamic macro recordings are intentionally simple and RAM-backed:

- Recordings live in RAM only and are lost on reboot, firmware update, power loss, or deep sleep (`CONFIG_ZMK_SLEEP=y`).
- Playback uses a fixed event delay; original timing is not preserved.
- Only resolved keycode events are recorded. Layer changes, Bluetooth/output commands, mouse movement, and scrolling are not captured.
- Nested playback is refused rather than queued, and only one register can record at a time.
- Recording is not silent; keys are sent to the host while being recorded.

Follow-up checklist:

- Decide whether RAM-only behavior is acceptable before relying on macros across long idle/deep-sleep periods.
- If persistence is needed, design a ZMK settings-backed storage format and a migration story for existing volatile slots.
- If longer recordings are needed, adjust `CONFIG_ZMK_BEHAVIOR_DYNAMIC_MACRO_MAX_EVENTS` only after checking central-half RAM headroom in firmware build logs.
- Re-run `cd tests/dynamic_macro && make clean && make && ./test && make clean` after any driver, Kconfig, or keymap changes that affect dynamic macros.

## Register-select layer combo caveat

Existing combos are mostly not layer-restricted, so they are also eligible on the dynamic macro register-select layers. A deliberate single register tap is safe, but a sloppy simultaneous press of two register keys can trigger an existing combo instead of selecting a register. The current behavior self-heals by staying on the select layer until the next key selects a register or aborts.

Follow-up checklist:

- If this becomes annoying on hardware, add an explicit `layers = <...>` whitelist to the general combo helper so combos only run on intended typing/recording layers.
- When adding any new layer after such a whitelist, remember that `layers` is opt-in; new layers will not receive combos until the whitelist is updated.
- Hardware-test the `Z+X` record/stop and `C+D` playback triggers after moving or layer-restricting combos.

## Hardware verification gap

The repository has a host test for the dynamic macro driver and CI firmware builds for every `build.yaml` target, but it does not currently have automated on-device coverage for the split keyboard, BLE behavior, pointing, deep sleep/wake, or physical combo ergonomics.

Follow-up checklist:

- Flash at least the left/central half after firmware changes that affect keymap behavior, split settings, dynamic macros, sleep, or Bluetooth/output handling.
- Smoke-test each hardware variant (`yellowjacket_yj1` and `yellowjacket_yj2`) before treating CI artifacts as release-ready.
- Verify dynamic macros across sleep/wake expectations, register selection, recording stop while keys are held, and playback while normal layers/hold-taps are used.
- Capture manual hardware-test notes with the firmware artifact or PR so future regressions have a comparison point.
