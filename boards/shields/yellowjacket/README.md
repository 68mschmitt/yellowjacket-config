# Yellowjacket shared shield

This directory is the shared/common Yellowjacket hardware definition for the
32-key split keyboard. The YJ1 and YJ2 wrapper shields in the sibling
`yellowjacket_yj1/` and `yellowjacket_yj2/` directories reuse these common
files instead of duplicating matrix, layout, and GPIO wiring details.

## Common hardware files

- `yellowjacket.dtsi` defines the physical layout binding, matrix transform,
  split kscan wiring, and `chosen` nodes shared by all Yellowjacket variants.
- `yellowjacket-layouts.dtsi` defines the physical key layout and position map.
- `yellowjacket.keymap` and the empty `yellowjacket.conf` files are legacy
  direct-shield entry points; the active user config lives under `config/`.

## Variant boundaries

- `../yellowjacket_yj1/` declares `yellowjacket_yj1_left` and
  `yellowjacket_yj1_right`, then includes this directory's shared DTSI files.
- `../yellowjacket_yj2/` declares `yellowjacket_yj2_left` and
  `yellowjacket_yj2_right`, then includes this directory's shared DTSI files.
- The wrapper shields currently differ only in their advertised keyboard names
  (`YJ1`/`YJ1_R` and `YJ2`/`YJ2_R`). Right-half overlays set the common split
  transform column offset.

The direct shield names `yellowjacket_left` and `yellowjacket_right` remain
available from this directory for backwards-compatible/manual builds, but the
normal firmware matrix uses the YJ1/YJ2 wrapper shield names.

Display support is intentionally inactive: no display node or user config is
enabled for the current Yellowjacket builds. Reintroduce display/LVGL Kconfig
defaults only with matching active devicetree and config changes for the
intended variant.
