# Pinchwing v4 — layer cats

## Flash this

`build/firmware/pinchwing-dongle/current/pinchwing_dongle_round.uf2`

The versioned copy is:
`build/firmware/pinchwing-dongle/releases/v4/pinchwing_dongle_round.uf2`.

For the working charging-v3 setup, **update only the round-display dongle**.
Double-tap its reset button, copy the UF2 to its bootloader drive, then let it
restart. **Do not use settings reset.** Existing pairing, 180° orientation,
DPI, mouse transport, and USB/battery reporting are retained.

The bundle also includes the compatible left charging image and right
charging-v3 image, named `pinchwing_dongle_left.uf2` and
`pinchwing_dongle_right.uf2`. These are byte-identical copies of the previously
working half builds, supplied for a complete set, not new half firmware.

## Changes

| Layer | Scene |
| --- | --- |
| Base | Original raised-paw bongo cat and WPM hyperspace |
| Number | Glasses, calculator, math symbols |
| Arrows | Pilot stick and direction indicators |
| Mouse | Scurrying mouse and swatting paws |
| Functions | Wizard hat, wand, sparks |
| System | Headset and control console |
| Brackets | Cat in a bracket-sided box |
| No Mods | Typewriter and moving carriage |
| RecSel | Clapperboard waiting for a register |
| PlaySel | Cassette and play indicator |
| Recording | Tape recorder, spinning reels, blinking REC |

Original body and paw assets are shared across all scenes. Moving paws draw
above props. Layer changes wake the cat; after 15 seconds idle it lowers its
paws and dozes with props visible. Recording overlays the current working layer
rather than obscuring Mouse/Number/etc.

Firmware uses compact two-pose prop animations derived from the approved
desktop demo, plus independently moving mouse and stars. The desktop demo
remains available at `previews/cat-layers/index.html`.

## Bundle layout

```text
build/firmware/pinchwing-dongle/
  current -> releases/v4
  releases/v4/
    pinchwing_dongle_round.uf2
    pinchwing_dongle_left.uf2
    pinchwing_dongle_right.uf2
    SHA256SUMS
    metadata/
  archive/pre-v4/       # All earlier local images and diagnostic revisions
  development/         # Future local rebuild output
```

Release verification and exact dependency/source information are recorded in
the bundle's `metadata/`. The real-LVGL display test exercises every scene with
a 48 KiB heap. UF2 integrity and legacy size limits are checked before publishing.
The v4 receiver uses 491,528 bytes of flash and 153,470 bytes of static RAM.
Its UF2 has 1,921 blocks (491,776 payload bytes), below the conservative
2,048-block limit, and ends at `0x9E100`.
On-device appearance, display throughput, and keyboard responsiveness still
need confirmation after flashing.

Older build notes are preserved in
[the history archive](../archive/pinchwing-dongle-history.md).
