# Layer-aware cat display

## Source map

| Path | Responsibility |
| --- | --- |
| `src/display/pinchwing_status.c` | Layer/WPM/DPI/link/power dashboard |
| `src/display/pinchwing_pet.c` | Original cat, paw events, layer selection, idle and warp |
| `src/display/pinchwing_scenes.c` | Prop animation, mouse movement, recording overlay |
| `src/display/assets/bongo_cat/` | Unmodified upstream artwork and MIT attribution |
| `src/display/bongo_cat.c` | Generated indexed body/paw images |
| `src/display/cat_overlays.c` | Generated indexed, deduplicated prop tiles |
| `previews/cat-layers/` | Browser demo and overlay drawing source |
| `tests/pinchwing_display/` | Real LVGL render/heap regression harness |

Firmware reuses the original 192×96 cat and independent up/down paws. Layer
props are exported directly from the approved browser drawings into 24×24 I4
tiles. Identical tiles are shared. Each tile decodes to only 2,304 bytes.
Two prop poses alternate at 10 Hz timer boundaries, faster after key activity;
the mouse separately scurries across the scene. This is a compact two-pose
adaptation of the browser's continuous prop motion.

Layer names select scenes, rather than hard-coded active-layer indices.
Recording becomes an overlay on any other active working layer; on Base it
selects the tape-recorder scene. Layer changes wake the cat. After 15 seconds
without keypresses the paws rest down and props stop, while a Z caption floats.
The recording badge keeps blinking while recording. Base retains WPM warp.

Draw order: starfield → original body → resting paws → props → moving paws.
All LVGL changes run on the existing display queue. Sprite positions and poses
are reused; the frame loop does not continuously create/delete UI objects.

## Regeneration

```sh
python3 scripts/convert-bongo-cat.py       # Pillow
python3 scripts/convert-cat-overlays.py    # Pillow + Chromium
```

Generated C files are checked in, so ordinary firmware builds need neither
Pillow nor Chromium. The demo's `?export` mode emits transparent overlay frames.
Keep asset attribution beside the original sprites.

## Verification

```sh
LVGL_DIR=/path/to/workspace/modules/lib/gui/lvgl \
  bash tests/pinchwing_display/run.sh
python3 scripts/check-pinchwing-uf2.py /path/to/pinchwing_dongle_round.uf2
```

The display test compiles the actual renderer against the firmware's LVGL
checkout with a 48 KiB heap. It visits every scene, exercises keypresses,
recording over another layer, sleep/wake, and warp, and writes native-resolution
PPM captures under `build/tests/pinchwing-display/`. Hardware SPI timing and
on-device appearance still require a physical check.
