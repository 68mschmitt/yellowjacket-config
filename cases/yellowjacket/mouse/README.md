# Yellowjacket right-hand mouse tray — first-fit prototype

A one-piece, pressure-fit bottom tray with a raised sensor pocket **outside the
PCB outline, beside the controller**. The pocket extends from the controller-side
straight edge of the right half (the left edge when viewed in typing orientation).
USB and the power-switch opening remain above the low tray rim.

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
| Sensor pocket rim above printed bottom | 7.1 mm |

Switches, keycaps and your existing controller/socket/battery stack determine
the final assembled height; this is not a 7.1 mm total-height keyboard.
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
