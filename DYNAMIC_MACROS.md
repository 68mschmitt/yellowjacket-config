# Vim-Style Dynamic Macros

Runtime-recordable macros with a Vim register workflow:

```
Z+X  a  <keystrokes>  Z+X      record into register a
Z+X  b  <keystrokes>  Z+X      record into register b
C+D  a                         play register a
C+D  b                         play register b
```

`Z+X` is the `q` analogue (record start/stop), `C+D` is the `@` analogue (playback).

## Upstream status (verified 2026)

| Source | State | Verdict |
| --- | --- | --- |
| ZMK `main` | no dynamic macro support | — |
| [PR #2678](https://github.com/zmkfirmware/zmk/pull/2678) (calvinhenderson) | **open, mergeable: dirty**, last touched 2026‑01‑15 | API is a good fit; used as the design basis |
| [PR #1351](https://github.com/zmkfirmware/zmk/pull/1351) (nickconway) | **open** since 2022, 27 files | rejected — see below |
| [Issue #1346](https://github.com/zmkfirmware/zmk/issues/1346) | open feature request since 2022 | — |

Neither PR is merged and neither applies cleanly. **PR #1351 was rejected** for this
use case for a concrete reason: it keys active recordings by the *key position* that
started them (`find_recording_macro(event.position)`), so a recording started from a
register-select layer can never be stopped from a different key. It also calls the
removed `device_get_binding()` API. PR #2678's `&dm <command> <slot>` API passes the
slot explicitly at every call site, which is what makes the Vim flow expressible.

**Chosen approach: out-of-tree module, hosted inside this repo.** This repo already
declares itself a Zephyr module (`zephyr/module.yml`) to provide its shields, so the
behavior was added to that same module. Consequences:

- no ZMK fork to maintain and rebase
- **no `config/west.yml` changes** — the config stays pinned to upstream `revision: main`
- nothing extra to clone; GitHub Actions builds it as-is

## Files added

```
CMakeLists.txt                                    module build entry
Kconfig                                           tunables
zephyr/module.yml                                 + cmake / kconfig / dts_root
dts/bindings/behaviors/zmk,behavior-dynamic-macro.yaml
include/dt-bindings/zmk/dynamic_macro.h           DM_REC / DM_PLY / DM_STP
src/behaviors/behavior_dynamic_macro.c            the driver
config/yellowjacket.keymap                        behavior, wrappers, combos, 3 layers
config/yellowjacket.conf                          Kconfig values
```

`config/yellowjacket_yj{1,2}.{keymap,conf}` are symlinks to the shared files, so **both
keyboards get this feature**.

## Behavior API

```dts
&dm DM_REC <slot>   // clear <slot> and start recording
&dm DM_STP <slot>   // stop recording (slot argument ignored, see below)
&dm DM_PLY <slot>   // play <slot>
```

Include `<dt-bindings/zmk/dynamic_macro.h>` in the keymap.

### Divergences from PR #2678 (all deliberate)

1. **At most one slot records at a time**, and `DM_STP` stops whichever slot that is.
   This is the key change: without it you need one "recording" layer *per register* so
   the stop key knows its slot. With it, **one** recording layer serves any number of
   registers. `DM_STP`'s slot argument is accepted (for API compatibility and Studio
   metadata) but ignored.
2. **Playback output is never re-recorded.** An `in_playback` flag is held across the
   `raise_zmk_keycode_state_changed()` call, so the recording listener ignores the
   driver's own output. Without this, playing into an active recording grows the buffer
   from its own output.
3. **Recordings are always balanced.** Stopping appends a synthetic release for every
   still-held key, most-recent-first. Playback therefore cannot strand a modifier — the
   single worst failure mode of a naive implementation.
4. **Safe capacity handling.** Recording auto-stops (and balances) while there is still
   headroom, instead of dropping events once full — dropping a *release* while keeping
   its press is exactly what causes a stuck key.
5. **Mutation during playback is refused**, so the playback cursor can never point into
   a slot that is being rewritten. `play_index` is also bounds-checked every tick.
6. **12-byte compact event records** instead of storing whole `zmk_keycode_state_changed`
   structs (24 bytes), halving RAM.
7. Fixed the duplicate `k_timer` definition (a tentative definition plus `K_TIMER_DEFINE`
   of the same symbol).

## Keymap state machine

Layers 8–10 were added; layers 0–7 are untouched.

| Layer | Name | Role |
| --: | --- | --- |
| 8 | `REC_L` | after `q`: waiting for a register key |
| 9 | `PLY_L` | after `@`: waiting for a register key |
| 10 | `DMR_L` | recording; all bindings `&trans` |

All transitions use `&to`, never `&sl`. This was chosen specifically to avoid the
sticky-layer race the handoff worried about: `&to` is a single deterministic
"deactivate everything, activate one layer" operation with no pending-release state.

On `REC_L` / `PLY_L`, position 8 (physical `A`) and position 3 (physical `B`) select the
register; **every other position is `&to BASE_L`**, so a mistyped register aborts
cleanly rather than leaving the board unusable.

`DMR_L` is fully transparent, so normal typing, hold-taps and all 40+ existing combos
keep working while recording.

### Why the same chord can both start and stop

```dts
dm_combo_record { key-positions = <18 19>; layers = <BASE_L>; bindings = <&to REC_L>; };
dm_combo_stop   { key-positions = <18 19>; layers = <DMR_L>;  bindings = <&dm_stop>; };
```

Two combos may share key positions when their `layers` filters are disjoint.
`app/src/combo.c` filters candidates through `combo_active_on_layer()` against
`zmk_keymap_highest_layer_active()`, so exactly one is ever eligible. Because `DMR_L`
(10) is numerically the highest layer, the stop chord stays available even while a
momentary layer is held during recording.

### Trigger placement — the one thing you may want to change

The base layer has all 32 positions occupied, so the triggers are combos:

| Trigger | Positions | Physical keys |
| --- | --- | --- |
| record / stop (`q`) | `18 19` | `Z` `X` |
| play (`@`) | `20 21` | `C` `D` |

Both chords were verified free of collisions with the existing combos, and no key
exceeds `CONFIG_ZMK_COMBO_MAX_COMBOS_PER_KEY` (default 5). Edit `key-positions` in the
three `dm_combo_*` nodes to move them.

## Configuration

```conf
CONFIG_ZMK_BEHAVIOR_DYNAMIC_MACRO_MAX_SLOTS=2     # registers
CONFIG_ZMK_BEHAVIOR_DYNAMIC_MACRO_MAX_EVENTS=128  # ~64 keystrokes per slot
CONFIG_ZMK_BEHAVIOR_DYNAMIC_MACRO_TAP_DELAY=20    # ms between events on playback
CONFIG_ZMK_BEHAVIOR_DYNAMIC_MACRO_MAX_HELD=10     # max keys held at once (default)
```

RAM cost is `SLOTS * EVENTS * 12` bytes, statically allocated **on the central half
only** — 3 KB at these values. One ordinary key tap is **two** events (press +
release). Playback does *not* use the ZMK behavior queue, so
`CONFIG_ZMK_BEHAVIORS_QUEUE_SIZE` does not need raising.

## Adding more registers

1. Raise `CONFIG_ZMK_BEHAVIOR_DYNAMIC_MACRO_MAX_SLOTS`.
2. Add `#define REG_C 2`.
3. Add a `dm_rec_c` / `dm_ply_c` macro pair.
4. Replace `XXX` at the desired position on `REC_L` and `PLY_L`.

No new layers are needed — that is what change (1) above buys. `dm_stop` is shared.

## Build and flash

No new dependencies. Push and let GitHub Actions build, or locally:

```sh
west build -p -b nice_nano@2.0.0//zmk -- \
  -DSHIELD=yellowjacket_yj1_left \
  -DZMK_CONFIG="$HOME/projects/yellowjacket-config/config" \
  -DZMK_EXTRA_MODULES="$HOME/projects/yellowjacket-config"
```

`ZMK_EXTRA_MODULES` is required locally because this config is also a module.

**Only the left half needs reflashing** — it is `ZMK_SPLIT_ROLE_CENTRAL` for both YJ1
and YJ2, and all of this code is central-only. The right half is unchanged.

For logging, build the `yj1_left_logging` artifact already in `build.yaml` and watch for
`dynamic macro` lines.

## Test procedure

| # | Steps | Expected |
| --: | --- | --- |
| 1 | `Z+X` `a` `a b c` `Z+X`, then `C+D` `a` | `abc` |
| 2 | `Z+X` `b` `x y z` `Z+X`, then `C+D` `b` | `xyz`; then `C+D` `a` still gives `abc` |
| 3 | Re-record `a` as `123`, play `a` | `123` only |
| 4 | `C+D` on a never-recorded register | nothing, no lockup |
| 5 | `Z+X` `a` `Z+X` (immediate stop), play | nothing |
| 6 | Record `Shift+h e l l o` | `Hello` |
| 7 | Record `Ctrl` down, `c`, `Ctrl` up | host sees a real Ctrl+C |
| 8 | Start recording, hold `Shift`+`a`, stop **while still held** | playback leaves nothing stuck |
| 9 | `Z+X` then a non-register key | returns to base, key does not type |
| 10 | Record >64 keystrokes | recording auto-stops, playback balanced |
| 11 | Trigger playback during playback | second request ignored |
| 12 | Type normally: `a`, `b`, `Z`, `X`, `C`, `D` alone | completely unchanged |

Cases 1–8, 10 and 11 are covered by the host test suite below; 9 and 12 are keymap
behavior and need hardware.

## Verification performed

The driver was compiled and executed **on the host** against stub Zephyr/ZMK headers
(`/tmp/dmtest/`), with playback output routed back into the recording listener exactly
as ZMK's event manager would. 16/16 assertions pass, including: basic recording,
playback-not-re-recorded, register independence, overwrite, empty slot, immediate stop,
`Ctrl+C` round trip, synthetic releases in reverse order, play-while-recording refused,
record-while-playing refused with buffer intact, capacity truncation to a balanced
sequence, held-key-limit auto-stop still balanced, out-of-range slot rejected, and
recovery after auto-stop.

Also statically verified against ZMK `main` (v0.3.0, Zephyr 4.1):

- `struct zmk_behavior_binding.behavior_dev` is still `const char *`; metadata structs,
  `BEHAVIOR_DT_INST_DEFINE` and `zmk_keycode_state_changed` all match the driver's use
- all 11 keymap layers have exactly 32 bindings
- `layers` is a valid property on `zmk,combos`; `combo_active_on_layer()` confirms the
  shared-position combo trick
- `dts_root: .` puts `include/` on `DTS_ROOT_SYSTEM_INCLUDE_DIRS` and `dts/bindings` on
  `DTS_ROOT_BINDINGS` (`zephyr/cmake/modules/pre_dt.cmake`), so the keymap's
  `#include <dt-bindings/zmk/dynamic_macro.h>` and the binding YAML both resolve
- `post_boards_shields.cmake` resolves `yellowjacket_yj1_left` → `yellowjacket_yj1` →
  `yellowjacket`, confirming the edited files are the ones the build consumes
- `src/events/keycode_state_changed.c` is itself central-only upstream, so the
  central-only CMake guard is mandatory, not merely an optimisation

**Not yet done: no firmware was built and nothing was tested on hardware** — there is no
Zephyr SDK or west workspace on this machine. Treat the first CI build as the remaining
gate.

## Known limitations

- **Recordings live in RAM only.** They are lost on reboot, firmware update, power loss
  and deep sleep (`CONFIG_ZMK_SLEEP=y` here). Persistence would need ZMK settings
  storage and was out of scope.
- **Timing is not preserved.** Playback uses a fixed `TAP_DELAY` between events.
- **Only keycodes are recorded.** Layer changes, Bluetooth/output/RGB commands, mouse
  movement and scrolling are *not* captured, because recording taps
  `zmk_keycode_state_changed`. A hold-tap is recorded as whatever keycode it resolved
  to; a key pressed on another layer records the resolved keycode, not the position.
- **Nested playback is refused**, not queued — a macro cannot call another macro. This
  is deliberate: it makes runaway recursion structurally impossible.
- **One recording at a time**, by design (see divergence 1).
- Recording is not silent: keystrokes reach the host as you record, as in Vim.
- `&dm` is central-only. The trigger *keys* may live on either half (positions are
  forwarded to the central before keycode resolution), but the buffers and playback are
  on the left half. Changing which half is central discards all recordings. A right-half
  disconnect does not affect playback of already-recorded macros.
- No `app/tests`-style ZMK snapshot tests were added; verification is the host harness
  above.
