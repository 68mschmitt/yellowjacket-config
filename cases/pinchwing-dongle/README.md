# Pinchwing round-display dongle enclosure — first-fit prototype

Screwless PLA enclosure for the photographed **38 × 45.5 mm GC9A01 module**
and a nice!nano / Pro Micro nRF52840 controller with downward-facing headers.

- Display plane: **60° above the desk**, looking forward.
- Display header: **top**, inside the enclosure (PCB rotated 180°).
- USB-C: rear, opposite the display.
- Controller: horizontal in the lower housing, components up.
- Continuous flat 60° front panel with a circular display opening, rounded
  side corners, and a **5 mm tangent radius** blending the front into the roof.
  Other front edges have 0.8 mm chamfers. The roof is perpendicular to the
  display face (sloping down 30° toward the rear).
- Four releasable PLA cantilever snaps hold the bottom.
- Two straight 1.75 mm locating pegs align the display. A separate push-fit
  retainer captures the PCB behind the front lip.
- The front pocket clears the full **38 mm PCB** with a **38.6 mm diameter**.
  The glass sits nominally **0.6 mm behind the front face**, beside a 0.4 mm lip.
- A **28 mm-wide rectangular relief** surrounds the square header extension.
  The pegs stay 1.75 mm diameter down to the pocket floor, without flared bases.

## Print files

### Add-ons for already printed cases

- [Internal display brace](brace/README.md): supports the retaining ring against
  the base.
- [MCU keeper and USB-C bezel](usb-retrofit/README.md): positive MCU retention
  and a recessed socket mask, using the existing housing and larger nano base.

All files are in [`output/`](output/). STL units are millimeters.

### Print fit tests first

1. **`display-fit-test.stl`** and **`display-retainer.stl`**:
   check the window, PCB depth, 19.5 mm hole spacing, pegs and header clearance.
   Reprint the display coupon for the straight-peg revision. The rectangular
   relief includes straight peg bases so the mounting holes can slide fully down.
2. The **18.3 mm nano** has been confirmed by the printed fit test.
   Use **`bottom-nano-18_3.stl`**. The 17.8 mm files are alternate-board options.
3. **`snap-test-tongue.stl`** and **`snap-test-wall.stl`**:
   test insertion and release before printing the large housing.
   The wall coupon is laid on its outer side for printing; turn it upright,
   with the window at the top, to test against the tongue.

### Final printed assembly

| File | Quantity | Purpose |
| --- | --- | --- |
| `housing.stl` | 1 | Angled display surround and rounded outer shell |
| `bottom-nano-18_3.stl` | 1 | Confirmed-width base with lowered controller cradle |
| `display-retainer.stl` | 1 | Push-fit PCB retaining ring |

The retainer used for the fit test is also the final retainer.

`pinchwing-dongle.FCStd` contains the assembled parts and separate hardware
reference envelopes. `assembly.step` is the printable assembly in assembled
coordinates; individual STEP files match the print-oriented STLs. Do not slice
the assembly STEP as one fused object. `preview.png` shows the assembly, rear,
cutaway, and exploded views.

## Ender 3 V3 KE / PLA / 0.4 mm nozzle

- 0.20 mm layers; 0.16 mm is useful for the fit coupons.
- The 0.4 mm front lip is two 0.20 mm layers; inspect those layers in the slicer.
- 3–4 walls, 4 bottom/top layers, approximately 15% infill.
- Print at **100% scale**. Global scaling changes the mounting-hole spacing.
- Bottom and nano coupons: flat underside on the bed, as exported.
- Retainer: flat, as exported. No supports should be needed.
- Display coupon: bezel/front face down, as exported. Its pegs point upward.
- Housing: **display/bezel face down**, as exported, so the small locating
  pegs print upward rather than dangling below an inclined face.
  The perpendicular roof prints vertically in this orientation. Its new 5 mm
  front blend curves outward from the bed, so inspect its first few layers
  as well as the rear wall before attempting a supports-off print.
  For a single-piece, supports-off trial, use a 5 mm brim and tuned PLA cooling.
  Inspect the rear wall and USB bridge in the slicer: the rear wall still reaches
  a 60° overhang from vertical in this orientation, and the USB opening bridges
  14 mm. Support-free success on those features is not yet print-verified.
- Avoid elephant-foot buildup on mating edges. Deburr gently.

PLA snap arms are intended for occasional assembly/release, not constant flexing.
Press the side tabs inward through their windows to release the bottom;
do not pry the shell apart against the hooks.

## Assembly

1. Test the display and controller electrically before installing them.
2. Remove all support material and check the fit coupons.
3. Feed the display into the housing from the open bottom. Face forward,
   header at the top. Align both PCB holes with the locating pegs.
   The header tops and ribbon transition sit in the new recessed clearances.
4. Press the retainer into the circular pocket behind the PCB, matching its
   two peg holes and the relieved edge beside the header. Its small crush
   ribs grip the housing. Press the printed ring, not the LCD glass.
5. With the bottom separate, hold the small front controller-stop tongue
   forward and slide the nice!nano into its side slots, USB first toward
   the rear. Release the tongue after the board reaches the rear stops.
6. Fit the female jumpers to the downward-facing controller pins through
   the open front beneath the board. Tweezers may help with the rear pins.
   Support the board rather than pulling on the wires.
7. Connect the other ends to the display. Route the 3-inch wires loosely in
   the cavity between the display and controller, away from the four snaps.
   Test USB and display operation again before closing.
8. Align the rear USB opening and lower the housing onto the base. Engage
   the four snaps with light pressure. No screws or adhesive are required.

The USB opening is **14 × 10 mm**, sized for a molded plug. The socket is
slightly recessed, so check your actual cable in the base/housing before
committing to the final print.

## Dimensions, references and remaining first-fit assumptions

The housing's assembled nominal envelope is approximately **50 × 68 × 59 mm**
(width × depth × height). Print-oriented bounding boxes differ because the
housing is exported face-down.

The header-up revision lowers the nano PCB by **4 mm** (underside at 18.4 mm
above the desk, 16 mm above the inner floor). The USB opening follows it.
The display center is at 35 mm above the desk. Modeled display and controller
connector envelopes are checked for mutual interference.

The current PCB pocket has **0.3 mm radial clearance** for the measured
38 mm board. The PCB's front surface seats 3.7 mm behind the housing face.
With the assumed 3.1 mm glass height, its surface is 0.6 mm behind the face,
with nominally 0.2 mm clearance behind the 0.4 mm retaining lip. The straight
pegs align the mounting holes; the front lip and rear retainer limit axial travel.
There is no shoulder on the pegs setting a hard PCB depth, so the actual seating
depth depends on the module's glass/PCB stack.
The display plane moved 1 mm rearward to keep the enlarged pocket enclosed
at the lower front edge. The opening diameter and peg sizes/spacing are unchanged.

The square-extension pocket now starts **1.0 mm behind the front face** and
continues through to the interior, instead of starting only at the 3.7 mm PCB
seat. It is 28 mm wide, with 0.6 mm clearance past the header-side PCB edge.
The locating pins are **1.75 mm diameter continuously down to the pocket floor**,
on 19.5 mm centers. Their small inward-tapered insertion tips remain at the same
height. There are no wider collars or conical bases below the PCB holes.
Validation includes a 1.2 mm front-side allowance around this
section for solder/unevenness, excluding the mounting holes; this is
a clearance allowance rather than a measured component envelope.

User-measured display dimensions:

| Property | Value |
| --- | --- |
| Maximum PCB width | 38 mm |
| Overall PCB height, including header extension | 45.5 mm |
| Pins below PCB | 11.32 mm |
| Hole diameter | 2 mm |
| Hole centers | ±9.75 mm from center, 19.5 mm apart |
| Hole center from header-side PCB edge | 5.8 mm |

With the circular PCB center as the origin and the header downward, the
header-side edge is at **v = -26.5 mm** and the two hole centers are
**(±9.75, -20.7) mm**. This is the interpretation of “hole to PCB bottom.”
The assembled board is rotated 180° about its face normal so these features
are now above the display. The tested 33 mm opening, 1.75 mm pegs, and
19.5 mm peg spacing are preserved.

The supplied `1.28+LCD+XIAO+Mount+2+v9.stl` was inspected as a reference
(35 × 38 × 6 mm overall, four mounting features). Its mount pattern differs
from this two-hole PCB, so the measured PCB dimensions above control this model.
Cross-sections through its thickness show an 18 mm-wide central relief reaching
approximately 19 mm from center. The new ribbon pocket uses that envelope plus
0.3 mm clearance: **18.6 mm wide, reaching 19.3 mm from center**. It is recessed
behind the front lip so the circular opening remains unchanged.
The header-top pocket is 19 × 3.8 mm, with the same front clearance as the glass.

Published controller dimensions are inconsistent:

- [Mechboards nice!nano v2](https://mechboards.co.uk/products/nice-nano-v2):
  34.1 × 18.3 mm, 1.6 mm PCB thickness.
- [Elecrow compatible nRF52840 board](https://www.elecrow.com/pro-micro-nrf52840-development-board-compatible-with-nice-nano-v2-0.html):
  33 × 17.8 mm.

The two bottom variants accommodate the two published widths. The controller
slot uses a 34.1 mm length envelope; a shorter clone can have some fore/aft
play. The local pressure ribs provide friction, and the front/rear stops limit
travel. A snug width coupon is the deciding check, not the label on the board.

Still **assumed**, not measured on your hardware:

- Display PCB thickness: 1.6 mm.
- Glass outer diameter: 35.6 mm; visible opening: 33 mm.
- Glass height above PCB: 3.1 mm. This controls the nominal 0.6 mm face recess;
  exact flushness depends on the actual module thickness.
- Header center: 2.5 mm from the header-side PCB edge.
- Female connector bank: 18.2 mm wide, 3.2 mm tall, extending to 26 mm behind
  the front display plane (20.7 mm behind the PCB underside).
- Controller female connectors: 2.9 mm width envelope per pin row, 14.5 mm
   below the PCB. The lowered board is 16 mm above the inner floor, leaving
   1.5 mm below this modeled connector envelope. Wire-bend clearance has not
   been measured; lowering the board was requested without that measurement.

These assumptions are why the fit coupons are supplied. Printed fit and actual
wire routing remain to be confirmed. Do not use the snap closure to force
connectors or wires into a space they do not fit.

## Regenerate / adjust

Edit `parameters.json`, then:

```sh
python3 cases/pinchwing-dongle/generate.py
python3 cases/pinchwing-dongle/preview.py
```

Requires the system FreeCAD Python modules. The preview also uses NumPy and
Matplotlib. The generator reuses the repository's CAD/STL validation helpers.

`output/validation.json` records solid validity, watertightness, connected mesh
count, self-intersection checks, dimensions and modeled component clearances.
It also verifies the full-diameter pocket is unobstructed and checks all outer
faces for unintended openings beyond the display, USB, and snap windows.
`square_extension_clearance` records the front-side relief check and verifies
that there is no flared material around the peg bases.
Small, intentional intersections are used for controller pressure ribs and
retainer crush ribs. Connector and glass envelopes must not intersect any
printed component.
