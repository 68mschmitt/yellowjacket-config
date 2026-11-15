# Yellowjacket right-hand mouse tray — first-fit prototype

A one-piece, pressure-fit bottom tray with a raised sensor pocket **outside the
PCB outline, beside the controller**. The pocket extends from the controller-side
straight edge of the right half (the left edge when viewed in typing orientation).
The USB/power-switch access notch retains its original bottom height.

## Snap-on sensor cap

`output/pmw3610-snap-cap.stl` is the separate, print-oriented cover; matching
STEP and editable FreeCAD files are included. The main case FreeCAD document
also contains `SensorCapInstalledReference` for assembly inspection.

- Pegs now extend **9.0 mm above their seats / 7.4 mm above the sensor PCB**.
  Their split tips have 2.2 mm necks and tapered 2.6 mm heads, snapping through
  2.4 mm cap holes (0.1 mm nominal radial engagement).
- Four tubular cap feet seat around the PCB mounting holes. The 1.6 mm roof
  leaves **5 mm above the PCB** for components; this is a design clearance,
  not a measured envelope of your populated module.
- **1.6 mm thick perimeter walls** extend **4 mm down from the roof** and
  sit flush on the mount's 7.8 mm-high rim, closing the side gaps. The existing
  lower wire exit remains accessible. Use the underside lens insert to close
  the bottom surround; the optical aperture remains open.
- A **2.75 × 18 mm open edge relief** on the keyboard-facing long side clears
  the header. Install the sensor with its header toward the keyboard PCB.
  The notch continues through the roof edge, allowing upright pins to project
  above it. The cap wall below the notch remains intact.
- Header location comes from SideraKB Rev 1 J1: six pins at 2.54 mm pitch,
  centred 10.25 mm from the PCB centre on a long side. Source:
  `pmw3610_pcb.kicad_pcb` at upstream commit
  `3cfb40c96e02dbb858a15fb085580616548bf1f3`.

Print the cap **in its exported orientation: roof on the bed, walls and feet upwards**.
PETG is recommended for the split snap pegs. First print the updated sensor
pocket coupon and cap together to check peg flex, retention and your actual
header/connector clearance. Press the cap evenly over all four pegs after
installing the sensor PCB. The snaps are a CAD-checked prototype, not a
physically verified fit; connector housings wider than the relief need adjustment.
Cap settings are the `sensor_cap_*`, `sensor_snap_*` and
`sensor_header_relief_*` parameters. Peg height must equal sensor thickness +
cap clearance + cap thickness + snap-head height.

## Deeper-grip revision

Based on the printed fit feedback:

- Main keyboard rims rise from **4.4 to 5.4 mm** above the printed bottom,
  surrounding the full 1.6 mm PCB edge and extending 0.6 mm above it.
- The straight gripping portion of each keyboard rib increases from 0.35 to
  **1.4 mm**; the tapered entrance remains.
- Sensor walls extend **1.0 mm above the sensor PCB**, instead of 0.3 mm.
- Sensor pegs were extended to 2.2 mm above their seats in the deeper-grip
  revision; the snap-cap revision above now extends them to **9.0 mm**.
  Maximum diameter stays 2.6 mm.
- Sensor ribs now have **1.4 mm** of straight grip rather than 0.5 mm.

PCB support levels and the lens-to-desk height are unchanged. The PCBs sit
deeper relative to the taller rims, not closer to the desk. The existing
lens-cover insert still fits. Check the taller rims against your populated
board and keycap travel using the revised perimeter fit frame.

## Print files

Generated into `output/`:

- `yellowjacket-mouse-right.stl`: complete case.
- `yellowjacket-mouse-right-fit-frame.stl`: low-material keyboard perimeter and
  sensor pocket, for checking both fits before printing the complete case.
- `pmw3610-pocket-fit-test.stl`: standalone sensor-pocket coupon.
- Matching STEP files and `yellowjacket-mouse-right.FCStd`.
- `validation.json`: CAD, mesh, clearance and height checks.
- `board-snapshot.json`: exact extracted source geometry used.

### Matching left-hand case

The left tray uses the same floor, underside clearance, supports and eight
pressure ribs, without a sensor pocket:

- `output/yellowjacket-pressure-fit-left.stl`
- `output/yellowjacket-pressure-fit-left-frame.stl` (perimeter fit test)
- Matching STEP files and `output/yellowjacket-pressure-fit-left.FCStd`
- `output/left-validation.json`

Its keyboard PCB seating height matches the right tray. Use the same 0.6 mm
feet/skates on both halves to keep the keyboard heights equal.
Generate only the left files with:

```sh
python cases/yellowjacket/mouse/generate_mouse.py --left-only
```

### Plain right-hand case (no sensor)

An exact mirror of the left pressure-fit tray, including the taller rim and
extended gripping ribs:

- `output/yellowjacket-pressure-fit-right.stl`
- `output/yellowjacket-pressure-fit-right-frame.stl`
- Matching STEP files and `output/yellowjacket-pressure-fit-right.FCStd`
- `output/right-validation.json`

```sh
python cases/yellowjacket/mouse/generate_mouse.py --right-only
```

Print flat-bottom-down, using the same settings as the left case.

### Underside lens-cover insert

`output/pmw3610-lens-insert.stl` fills the large underside opening around the
lens. Matching STEP, FreeCAD and `insert-validation.json` files are provided.
It fits the existing sensor pocket and coupon; no case reprint is needed.

- Overall size: **20 × 28 × 1.8 mm**.
- Lens opening: **9.5 × 16.5 mm**, leaving clearance around the modeled lens
  envelope and optical path.
- Flange rests on the inner floor rim; four corner cutouts clear the PCB supports.
- Four small pressure ribs have 0.05 mm interference. The remainder has 0.2 mm
  clearance per side.
- Installed bottom is flush with the case underside; skate and sensor heights
  stay the same.

Print in the supplied STL orientation (**wide flange down**), preferably PETG,
0.2 mm layers, without supports. Remove the sensor PCB, turn the printed insert
over so its wide flange faces up, and press it into the opening from **inside
the pocket**. Reinstall the module with the lens facing through the aperture.
Check that the insert does not touch the actual lens or obstruct either optical
window. The lens geometry is a reference envelope, so physical fit and tracking
still need testing. This is an underside surround, not a top electronics lid.

Regenerate after changing the sensor case:

```sh
python cases/yellowjacket/mouse/generate_insert.py
```

The FreeCAD file contains both a print-oriented insert and installed assembly
references. Print only the exported STL, not the complete reference assembly.

Print **flat bottom down, openings upwards**, at 100% scale in millimetres.
Suggested first print: PETG, 0.4 mm nozzle, 0.2 mm layers, four perimeters,
six bottom layers. No support is intended inside the pocket or tray.
Localized tapered pressure ribs grip the board edges; there are no screws,
adhesive PCB mounts, separate top bezel, or overhanging PCB hooks.

Start with the sensor coupon and perimeter frame. The ribs have 0.08 mm nominal
interference, which depends on printer calibration and material. If too tight,
lightly scrape the ribs or lower the grip-interference parameters and regenerate;
do not force the PCB. This is a geometry-checked prototype, not a physically
fit-tested part.

## Low-height stack

Z=0 is the underside of the printed case; the desk is below it by the skate
thickness. Apply **0.6 mm total-thickness PTFE skates** to the flat underside,
including near the sensor pocket, with all contact points coplanar.

| Datum | Height |
| --- | ---: |
| Case floor thickness | 1.2 mm |
| Free space below keyboard PCB | 2.0 mm |
| Keyboard PCB underside above printed bottom | 3.2 mm |
| Keyboard PCB top above desk, including skates | 5.4 mm |
| Sensor PCB underside above printed bottom | 5.2 mm |
| Sensor PCB top above desk | 7.4 mm |
| Sensor raised relative to keyboard PCB | 2.0 mm |
| Lens reference plane above desk | 2.4 mm nominal |
| Main keyboard rim above printed bottom | 5.4 mm |
| Sensor pocket rim above printed bottom | 7.8 mm |
| Snap-cap roof above printed bottom | 13.4 mm |
| Snap-peg tips above printed bottom | 14.2 mm |

Switches, keycaps and your existing controller/socket/battery stack determine
the final assembled height; this is not a 7.8 mm total-height keyboard.
The 2 mm underside cavity assumes trimmed solder tails and no components
protruding farther than 2 mm below the keyboard PCB.

The optical height follows Figure 4 of the PMW3610 assembly drawing: 7.40 mm
PCB-top-to-surface with a 1.60 mm PCB and 2.40 mm lens-reference-to-surface.
The lens must already be correctly seated and retained on the sensor. This
case retains the module PCB, not a loose lens independently.

Changing skate thickness changes tracking height. Update `skate_thickness`
and regenerate if your feet are not 0.6 mm. Check the actual assembled lens
height before the full print; the source drawing assumes normal sensor seating.

## Sensor installation

Designed for **SideraKB PMW3610 PCB Rev 1**, 23.5 × 31.5 × 1.6 mm.
Four corner seats and 2.6 mm locating pegs match the 3.2 mm mounting holes on
a 17.5 × 25.5 mm pattern. Short-end interference ribs retain the board.
The first printed coupon fit the PCB outline, but its 2.9 mm pegs were too
wide. `sensor_peg_diameter` is now 2.6 mm (0.15 mm additional clearance per
side); the revised peg fit still needs a physical check.
The central 16 × 24 mm opening clears the lens and optical path.

Insert lens down, component side up. Route the wires through the 8 mm-wide
open-top notch toward the nice!nano. Keep wires above the keyboard PCB and
clear of the support posts and solder joints. The module's long dimension is
parallel to the controller's long dimension; the rectangular pocket accepts
either 180-degree orientation. Firmware axes may need adjustment.

Press the keyboard PCB gently into the tray, supporting it near the ribs.
There are eight small keyboard grip ribs, four clear-area support posts and
a perimeter ledge relieved around the current PCB's pad envelopes.

## Regenerate

From the `yellowjacket-config/` repository:

```sh
python cases/yellowjacket/mouse/generate_mouse.py
python cases/yellowjacket/mouse/preview_mouse.py
```

Requires FreeCAD Python modules; the preview additionally uses Pillow and
NumPy. `parameters.json` contains fit and height settings. The FreeCAD file
contains separate case/PCB/lens reference objects and a dimension spreadsheet;
change the JSON and rerun the generator to change the geometry.

The generator defaults to the bundled `board.json` mechanical snapshot, copied
from the PCB used for the printed prototypes. Its source SHA-256 was verified
against `bugs/pcbs/yellowjacket/yellowjacket.kicad_pcb` during migration. It
mirrors that geometry into right-hand orientation and records its source hash
in the output report. No checkout of `bugs` is required.

To explicitly use a newer board, pass `--pcb /absolute/path/to/board.kicad_pcb`.
This reads the board without modifying it; the extracted geometry is recorded
in `output/board-snapshot.json`. The bundled input snapshot is not overwritten.

The shared helper sources and tray defaults are in the parent directory.
They are copied from the original case tools; use the generators in this
directory as the supported entry points.

References:
- [Rev 1 PCB source, CERN-OHL-P v2](https://github.com/siderakb/pmw3610-pcb/tree/v1.0.0)
- [PMW3610 assembly drawing, Figure 4](https://trackballs.eu/media/Nakabayashi/Digio2/PMW3610DM-SUDU.pdf)
