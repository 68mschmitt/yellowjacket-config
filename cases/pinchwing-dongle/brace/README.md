# Add-on internal display brace

Print **one new part**: [`output/display-brace.stl`](output/display-brace.stl).
It fits the existing enclosure and **18.3 mm nano base**, using the existing
display-retaining ring. The housing, bottom, pegs, and retainer need no changes.

## How it works

Two upright side gussets support the **back of the retaining ring**, beside the
PCB rather than against the glass, solder joints, or header pins. Their feet
rest on the base floor. The curved rear toes sit just inside the base's raised
lip, which stops the brace sliding backward when the screen is pressed.
A low front crossbar joins the two sides into one printable piece.

The load path is **PCB → retainer → brace → base floor and rear lip**.
The screwless base snaps retain the assembly. The center remains open for the
nano and jumper wiring. This is a positive brace, not an additional friction ring.

There is nominally 0.2 mm PCB-to-retainer clearance in the original CAD plus
0.15 mm clearance at the rear toe fit. Some small take-up movement is expected;
this part prevents the retainer and display being pushed farther into the case.
Actual printed fit and stiffness still need checking.

## Print

- PLA, 0.4 mm nozzle, 0.20 mm layers, 3–4 walls.
- **100% scale, flat feet and crossbar on the bed**, as exported.
- **No supports designed in:** the full-height side gussets grow from their
  footprint, the crossbar is on the bed, and the contact faces slope 30° from
  vertical. Inspect your sliced layers before printing.
- A brim is optional if the long narrow feet lift on your printer.
- The STEP has the same floor-down print orientation as the STL.

## Install

1. Disconnect USB and release the bottom snaps.
2. Seat the display and its **existing retaining ring** in the housing.
3. Set the brace on the base around the nano cradle. The tall, angled ends face
   the display; the long low toes point toward the rear USB opening.
4. Slide the rear toes gently against the inside of the base lip. The crossbar
   sits forward of the nano's flexible front stop.
5. Route the jumpers through the open center, clear of the two contact pads.
6. Lower the housing onto the base, ensuring both angled pads meet the back of
   the retaining ring. Close the snaps with light pressure.
7. Check the screen with gentle pressure. If the bottom will not close easily,
   reopen it and check seating and wire routing rather than forcing the brace.

This brace requires the supplied retaining ring; it is not a substitute for it.
The PCB/retainer can still be removed after lifting the housing off the brace.

## Files and verification

- [`output/preview.png`](output/preview.png): standalone, installed, and side cutaway.
- [`output/display-brace.step`](output/display-brace.step): editable brace geometry.
- [`output/brace-assembly.step`](output/brace-assembly.step): brace with copies of the
  existing housing, base, and retaining ring, in assembled coordinates.
- [`output/validation.json`](output/validation.json): mesh validity, original-part
  collisions, retainer contact, rear-stop check, and original-file preservation.

The generator reads the existing `../output/pinchwing-dongle.FCStd` without
saving it. SHA-256 hashes verify that all pre-existing enclosure files remain
unchanged. The brace has been CAD-checked against the shell, both modeled
connector banks, the controller cradle, snap arms, and hardware envelopes.
Flexible wire routing and printed strength are not simulated.

From the repository root:

```sh
python3 cases/pinchwing-dongle/brace/generate.py
python3 cases/pinchwing-dongle/brace/preview.py
```

Dependencies match the enclosure generator: system FreeCAD modules, plus NumPy
and Matplotlib for the preview. `parameters.json` controls only this add-on.
