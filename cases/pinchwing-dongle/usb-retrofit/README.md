# MCU keeper and recessed USB-C bezel — retrofit prototypes

Two small add-ons for the existing **18.3 mm nice!nano base** and housing.
They are compatible with the [display brace](../brace/README.md). No original
STL, STEP, or FreeCAD assembly is regenerated or modified.

| Print | Purpose |
| --- | --- |
| [mcu-keeper.stl](output/mcu-keeper.stl) | Captures the MCU's front corners and hooks around the cradle |
| [usb-bezel.stl](output/usb-bezel.stl) | Hides the board around the socket while retaining cable-body access |

[Preview](output/preview.png) · [Bundle](output/usb-retrofit-package.zip) ·
[Validation](output/validation.json)

## MCU keeper

- Small corner caps limit board lifting at the end opposite USB.
- Front stops resist the board being pushed forward by USB insertion.
- Rear U-hooks engage the existing rear corner stops.
- Two long front spring latches hook beneath the existing cradle bridge.
- The middle stays open for components; the side members run outside the rails.

The design uses mechanical stops, not just a tighter friction fit. Nominal
clearance is 0.15 mm at the new corner caps and mating stops. The original
rails still constrain the rear board edges; this is not a zero-play clamp.

It targets the modeled **18.3 × 34.1 × 1.6 mm PCB**. The width was confirmed
by your earlier fit test; the length, thickness, and bare front-corner contact
areas still need physical confirmation. A shorter board can retain end play.

## USB bezel

The outer recess is **11.6 × 8.0 mm**. At the socket, a **9.4 × 3.8 mm**
opening in a 0.4 mm-thick mask exposes the connector rather than the surrounding
PCB. The wide frame remains **inside** the housing. The mask sits close to the
socket so the cable body can enter the recess before its metal plug bottoms out.

The bezel is captive **when used with the keeper**:

- Its inside flange stops it pulling outward through the housing.
- The keeper's rear hooks stop it being pushed inward.
- Reliefs fit around the existing rails and rear stops.

It is deliberately a recessed socket mask, not a narrow hole at the outside
wall that could prevent a normal plug seating.

### Explicit first-fit assumptions

The USB socket itself was not measured. The current model assumes:

| Item | Assumption |
| --- | --- |
| Socket metal shell | 9.0 × 3.2 mm, 6.0 mm long |
| Socket center height | 0.8 mm above PCB underside |
| Socket front face | Aligned with the PCB's rear edge |
| Cable molded body | 10.5 × 6.5 mm, rounded corners |
| Plug metal section | 8.4 × 2.6 mm, protruding 6.5 mm from the molded body |
| Full plug engagement | 5.5 mm |

The modeled cable clears both add-ons when fully inserted. This is not a
universal cable-clearance guarantee: bulkier plugs or a different socket
position may need a different bezel. Change only this add-on's
`parameters.json` after checking the actual hardware. Do not globally scale
the keeper or bezel.

## Print the keeper first

1. Print the keeper and test MCU retention with the housing open.
2. Then print the bezel and confirm the USB cable seats fully.
3. Close the housing only after both individual checks work.

Both parts are exported in their intended print orientation:

- **Keeper:** flat upper rail caps on the bed (upside down from its installed
  position). Approximately **25.1 × 37.7 × 17.6 mm**.
  Use PLA, 0.16–0.20 mm layers and 3 walls. Enable local supports beneath the
  free front-latch ends and rear-hook overhangs. These features are intentionally
  flexible; remove support remnants carefully and inspect all hook throats.
- **Bezel:** wide inside retaining frame on the bed. Approximately
  **29 × 12.8 × 3.8 mm**. The shallow mask/tube requires short bridges from the
  frame; inspect the slicer's bridge paths. PLA cooling and 0.16–0.20 mm layers
  are suitable starting points; use local supports if those bridges sag.
- Use a brim if narrow keeper rails lift. Inspect the thin corner caps and
  0.8 mm rear hooks in the layer preview so they are not omitted by the slicer.

These are first-fit parts. Printed clip strength, repeated cycling, and actual
USB retention have not been physically tested.

## Assembly

“Front” below means the end **opposite USB**.

1. Unplug USB, remove the housing, and seat the nano in its existing cradle.
2. With the keeper's front end slightly raised, engage the two rear U-hooks
   around the cradle's rear corner stops. The small hooks face inward.
3. Lower the front. Gently deflect the two long front latch tongues toward the
   front as needed, then let them catch underneath the cradle's front bridge.
   Press the printed keeper, not the PCB components or USB socket.
4. Confirm both front corner caps overlap bare PCB and both latches engage.
   Try plugging/unplugging with the housing open. If it requires substantial
   force to install or bears on solder/components, stop and adjust the keeper.
5. Slide the bezel inward from the USB side onto the rear of the keeper.
   Its large frame faces the interior; the shallow tube faces outward.
   The lower frame notches straddle the original rail ends.
6. Install the existing display brace and arrange wires through the open
   center, clear of the latches.
7. Engage the **rear of the housing first**, with its front slightly raised,
   so the USB opening comes over the bezel. Then lower the front and close
   the existing snaps. Do not force the bezel through a closed housing.
8. Check the socket alignment and full cable engagement again.

To remove the keeper, open the housing, slide the bezel back out, release both
front tongues, raise the front, and unhook the rear. Avoid repeatedly bending
the small rear U-hooks themselves.

## Repository structure and regeneration

This follows the reorganized repository:

- `cases/pinchwing-dongle/usb-retrofit/`: this add-on's source, parameters, CAD,
  STLs, preview, and validation.
- `cases/pinchwing-dongle/brace/`: the existing separate display brace.
- [`docs/hardware/pinchwing-dongle.md`](../../../docs/hardware/pinchwing-dongle.md):
  current hardware guide and links to case add-ons.
- `scripts/`: firmware build/release tooling.
- `build/firmware/`: firmware artifacts, not printable case models.

From the repository root:

```sh
python3 cases/pinchwing-dongle/usb-retrofit/generate.py
python3 cases/pinchwing-dongle/usb-retrofit/preview.py
```

Dependencies are the existing system FreeCAD modules, NumPy and Matplotlib.
The generator reads the shipped enclosure FCStd and the brace's committed
assembly STEP/validation, so it does not require ignored BREP intermediates.
Individual STEP files match the print-oriented STLs. `output/assembly.step`
contains reference copies of existing parts plus the new parts.

Validation covers:

- Both new meshes: single solid, watertight, no self-intersections.
- No modeled collisions with the old parts, display brace, hardware envelopes,
  central component keep-out, socket, or fully inserted modeled cable.
- Positive-stop displacement probes for PCB lift/sliding, keeper retention,
  and bezel retention in both directions.
- Sampled rear-first housing-closing positions at 1°, 3°, 5°, 8°, and 12°.
- SHA-256 preservation of the existing enclosure and brace outputs.

The closing samples are not a full swept-motion or flex simulation. The keeper
installation requires the front latches to flex, and printed fit is still unverified.
