#!/usr/bin/env python3
"""Generate a right-hand pressure-fit tray with a raised Rev 1 PMW3610 pocket.

All dimensions are mm. Defaults to the bundled PCB snapshot; output stays here.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from extract_board import parse_sexpr, children, child, xy, rotate, reference
from generate import load_freecad, build, moved, export_verified
from generate_enclosures import box, local, wedge


def current_board(path):
    """Extract the current board, including its updated switch pad keepouts."""
    raw = path.read_bytes()
    tree = parse_sexpr(raw.decode())
    edges = []
    for n in tree:
        if not isinstance(n, list) or n[0] not in ("gr_line", "gr_arc"):
            continue
        if child(n, "layer") != ["layer", "Edge.Cuts"]:
            continue
        edges.append({"type": n[0][3:], **{
            k: xy(child(n, k)) for k in
            (("start", "mid", "end") if n[0] == "gr_arc" else ("start", "end"))
        }})
    fps = []
    for f in children(tree, "footprint"):
        at = child(f, "at")
        origin, angle = xy(at), float(at[3]) if len(at) > 3 else 0
        pads = []
        for pad in children(f, "pad"):
            delta = rotate(xy(child(pad, "at")), -angle)
            pads.append({"at": [origin[i] + delta[i] for i in (0, 1)],
                         "size": xy(child(pad, "size")), "shape": pad[3]})
        fps.append({"name": f[1], "reference": reference(f), "at": origin,
                    "rotation": angle, "pads": pads})
    return {"edges": edges, "footprints": fps,
            "thickness": float(child(child(tree, "general"), "thickness")[1]),
            "source_sha256": hashlib.sha256(raw).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    plain = parser.add_mutually_exclusive_group()
    plain.add_argument("--left-only", action="store_true",
                        help="Export the matching left pressure-fit tray without a sensor pocket")
    plain.add_argument("--right-only", action="store_true",
                       help="Export a mirrored right pressure-fit tray without a sensor pocket")
    parser.add_argument("--pcb", type=Path,
                        help="Use a KiCad PCB instead of the bundled board.json snapshot")
    args = parser.parse_args()
    p = json.loads((HERE / "parameters.json").read_text())
    App, Part, Mesh, MeshPart = load_freecad()
    board = (current_board(args.pcb) if args.pcb
             else json.loads((HERE / "board.json").read_text()))
    tray_p = json.loads((HERE.parent / "parameters.json").read_text())
    tray_p.update({k: p[k] for k in
                   ("floor_thickness", "under_pcb_clearance", "wall_thickness",
                     "pcb_clearance", "mesh_deflection", "wall_above_pcb_underside")})
    # Preserve the access notch's original bottom height as the rim rises.
    tray_p.update(adhesive_allowance=0.0,
                  power_switch_relief_depth=2.2+p["wall_above_pcb_underside"]-1.2)
    assert 0 < p["pcb_grip_height"] < board["thickness"]
    assert p["wall_above_pcb_underside"] > board["thickness"]
    assert p["sensor_peg_height"] > p["sensor_thickness"]
    assert 0 < p["sensor_grip_height"] < p["sensor_thickness"]
    mounts = [f["at"] for f in board["footprints"]
              if "thread_m2" in f["name"] and f["at"][0] < 100]
    controller = next(f for f in board["footprints"] if f["reference"] == "U1")
    # Current low-profile switch pads occupy the legacy (119,60) support site.
    base = build(board, tray_p, App, Part,
                 support_points=mounts+[[119,64],controller["at"]])
    case, frame, pcb = base["tray"], base["frame"], base["pcb"]
    outline = base["outline"]
    # Recover the existing generator's translation from the source outline.
    # Exact shift comes from reconstructing its source wire (arc extrema matter).
    from generate import board_wire
    original, _ = board_wire(board, App, Part)
    shift = App.Vector(outline.BoundBox.XMin - original.BoundBox.XMin,
                       outline.BoundBox.YMin - original.BoundBox.YMin, 0)
    pcb_z = base["pcb_z"]
    face = Part.Face(outline)
    ribs = []
    for seed in ((60.3, 61.15), (48.75, 100.64), (158.1165, 74), (110.25, 39.0314)):
        candidates = [e for e in board["edges"] if e["type"] == "line"]
        e = min(candidates, key=lambda e: math.dist(
            seed, [(e["start"][i] + e["end"][i]) / 2 for i in (0, 1)]))
        a = App.Vector(e["start"][0] + shift.x, -e["start"][1] + shift.y, 0)
        b = App.Vector(e["end"][0] + shift.x, -e["end"][1] + shift.y, 0)
        tangent = (b-a).normalize()
        normal = App.Vector(-tangent.y, tangent.x, 0)
        midpoint = (a+b)/2
        if face.isInside(midpoint + normal*0.1, 1e-7, True):
            tangent = -tangent
        for along in (-4, 4):
            anchor = midpoint + tangent*along
            # Grip most of the PCB edge, then taper outward for insertion.
            rib_top = pcb_z+p["wall_above_pcb_underside"]-0.05
            rib = wedge(-1, 2, [
                (-p["pcb_grip_interference"], pcb_z),
                (0.55, pcb_z), (0.55, rib_top),
                (p["pcb_clearance"]+0.15, rib_top),
                (-p["pcb_grip_interference"], pcb_z+p["pcb_grip_height"])], App, Part)
            ribs.append(local(rib, (anchor.x, anchor.y), (tangent.x, tangent.y), App))
    case = case.multiFuse(ribs).removeSplitter()
    frame = frame.multiFuse(ribs).removeSplitter()
    grip_volume = case.common(pcb).Volume
    assert 0 < grip_volume < 4, "Only localized pressure ribs should intersect PCB"

    if args.left_only or args.right_only:
        # The source geometry already has left-hand orientation.
        side = "right" if args.right_only else "left"
        if args.right_only:
            plane = App.Vector((case.BoundBox.XMin+case.BoundBox.XMax)/2,0,0)
            case, frame, pcb = [s.mirror(plane,App.Vector(1,0,0))
                                for s in (case,frame,pcb)]
        out = HERE / "output"
        out.mkdir(exist_ok=True)
        report = {"parameters":p, "source_sha256":board["source_sha256"],
                  "keyboard_pcb_underside_z":pcb_z,
                  "keyboard_pcb_top_above_desk":pcb_z+board["thickness"]+p["skate_thickness"],
                  "intentional_keyboard_grip_interference_mm3":grip_volume,
                  "base_checks":base["checks"], "parts":{}}
        for name, shape in ((f"yellowjacket-pressure-fit-{side}",case),
                            (f"yellowjacket-pressure-fit-{side}-frame",frame)):
            _, checks = export_verified(shape,out/f"{name}.stl",tray_p,Mesh,MeshPart)
            shape.exportStep(str(out/f"{name}.step"))
            report["parts"][name] = checks
        doc = App.newDocument(f"YellowjacketPressureFit{side.title()}")
        for name, shape in (("PrintableCase",case),("KeyboardPCBReference",pcb)):
            obj = doc.addObject("Part::Feature",name)
            obj.Shape = shape
        params = doc.addObject("Spreadsheet::Sheet","Dimensions")
        for row,key in enumerate(("floor_thickness","under_pcb_clearance","wall_thickness",
                                   "wall_above_pcb_underside","pcb_grip_height",
                                   "pcb_clearance","pcb_grip_interference","skate_thickness"),1):
            params.set(f"A{row}",key)
            params.set(f"B{row}",str(p[key]))
        doc.recompute()
        doc.saveAs(str(out/f"yellowjacket-pressure-fit-{side}.FCStd"))
        (out/f"{side}-validation.json").write_text(json.dumps(report,indent=2)+"\n")
        print(json.dumps(report["parts"],indent=2))
        return

    # Side extension beyond the straight edge beside U1, not in front of USB.
    controller = next(f for f in board["footprints"] if f["reference"] == "U1")
    edge_x = max(max(e["start"][0], e["end"][0]) for e in board["edges"])
    w, d = p["sensor_width"], p["sensor_depth"]
    cx = edge_x + p["sensor_board_gap"] + w/2 + shift.x
    cy = -controller["at"][1] + shift.y
    sensor_z = p["sensor_top_to_desk"] - p["skate_thickness"] - p["sensor_thickness"]
    assert sensor_z > pcb_z, "Sensor must sit higher than keyboard PCB"
    c, wall = p["sensor_clearance"], p["sensor_wall"]
    x0, y0 = cx-w/2-c-wall, cy-d/2-c-wall
    ow, od = w+2*(c+wall), d+2*(c+wall)
    top = sensor_z+p["sensor_thickness"]+p["sensor_wall_above_pcb_top"]
    pocket = box(x0,y0,0,ow,od,top,App,Part)
    # Open-top well, and a large through-window for the lens assembly.
    pocket = pocket.cut(box(cx-w/2-c,cy-d/2-c,1.2,w+2*c,d+2*c,top,App,Part))
    optical_window = box(cx-8,cy-12,-1,16,24,top+2,App,Part)
    pocket = pocket.cut(optical_window)
    supports = []
    sensor_board = box(cx-w/2,cy-d/2,sensor_z,w,d,p["sensor_thickness"],App,Part)
    cap_bottom = sensor_z+p["sensor_thickness"]+p["sensor_cap_clearance"]
    cap_top = cap_bottom+p["sensor_cap_thickness"]
    peg_top = sensor_z+p["sensor_peg_height"]
    assert abs(peg_top-cap_top-p["sensor_snap_head_height"]) < 1e-6
    assert p["sensor_snap_neck_diameter"] < p["sensor_cap_hole_diameter"] < p["sensor_peg_diameter"] < 3.2
    assert peg_top-p["sensor_snap_slot_depth"] > sensor_z+p["sensor_thickness"]
    for dx in (-8.75,8.75):
        for dy in (-12.75,12.75):
            # Rev 1: 3.2 mm holes at 17.5 x 25.5 mm pitch. Broad corner
            # supports contact only the mounting-hole keepout regions.
            supports.append(Part.makeCylinder(2.7,sensor_z,App.Vector(cx+dx,cy+dy,0)))
            # Split tips compress through the cap holes, then catch its top.
            # Heads stay at the proven 2.6 mm peg diameter to pass through PCB.
            peg = Part.makeCylinder(p["sensor_peg_diameter"]/2,cap_bottom,
                                    App.Vector(cx+dx,cy+dy,0))
            neck = Part.makeCylinder(p["sensor_snap_neck_diameter"]/2,
                                    p["sensor_cap_thickness"],
                                    App.Vector(cx+dx,cy+dy,cap_bottom))
            head = Part.makeCone(p["sensor_peg_diameter"]/2,
                                p["sensor_snap_neck_diameter"]/2,
                                p["sensor_snap_head_height"],
                                App.Vector(cx+dx,cy+dy,cap_top))
            peg = peg.multiFuse([neck,head])
            slot = box(cx+dx-p["sensor_snap_slot_width"]/2,cy+dy-2,
                       peg_top-p["sensor_snap_slot_depth"],
                       p["sensor_snap_slot_width"],4,
                       p["sensor_snap_slot_depth"]+0.1,App,Part)
            supports.append(peg.cut(slot))
            sensor_board = sensor_board.cut(Part.makeCylinder(
                1.6,3,App.Vector(cx+dx,cy+dy,sensor_z-0.5)))
    pocket = pocket.multiFuse(supports)
    sensor_ribs = []
    for sign in (-1,1):
        for dx in (-7,7):
            # Four localized pressure ribs on the short ends; tapered entry.
            rib = wedge(-1,2,[
                (-p["sensor_grip_interference"],sensor_z),
                (0.6,sensor_z),(0.6,top-0.05),(c+0.1,top-0.05),
                (-p["sensor_grip_interference"],sensor_z+p["sensor_grip_height"])],App,Part)
            tangent = (sign,0)
            sensor_ribs.append(local(rib,(cx+dx,cy+sign*d/2),tangent,App))
    pocket = pocket.multiFuse(sensor_ribs).removeSplitter()
    # Open-top wire exit on the keyboard-facing wall. No wire threading needed.
    wire_exit = box(x0-0.1,cy-4,sensor_z-1.3,wall+c+0.4,8,top,App,Part)
    pocket = pocket.cut(wire_exit).removeSplitter()
    # A thin continuous bridge joins the pocket to the tray wall.
    bridge = box(edge_x+shift.x-0.4,cy-d/2,0,
                 x0-(edge_x+shift.x)+0.8,d,p["floor_thickness"],App,Part)
    case = case.multiFuse([pocket,bridge]).removeSplitter()
    frame = frame.multiFuse([pocket,bridge]).removeSplitter()
    assert case.common(pcb).Volume < grip_volume+1e-5
    assert pcb.common(sensor_board).Volume < 1e-6
    assert pocket.common(sensor_board).Volume < 3
    # Verify a central clear optical path, excluding support posts at corners.
    beam = box(cx-4.5,cy-8,-0.1,9,16,1.9,App,Part)
    assert case.common(beam).Volume < 1e-6
    # Lens/body is an envelope only, not an optical/manufacturing model.
    lens_z = p["lens_reference_to_desk"]-p["skate_thickness"]
    lens = box(cx-4.125,cy-6.45,lens_z,8.25,12.9,sensor_z-lens_z,App,Part)
    assert case.common(lens).Volume < 1e-6

    # A separate cover seats on four tubular feet in the PCB mounting-hole
    # keepouts. Print roof-down, feet-up; the split pegs latch above its roof.
    cap = box(x0,y0,cap_bottom,ow,od,p["sensor_cap_thickness"],App,Part)
    # Continue the mount's walls up to the roof, seating flush on its rim.
    # Keep the existing lower wire exit; the header relief cuts only the roof.
    assert cap_bottom > top
    cap_walls = box(x0,y0,top,ow,od,cap_bottom-top,App,Part).cut(
        box(x0+wall,y0+wall,top-0.1,ow-2*wall,od-2*wall,
            cap_bottom-top+0.2,App,Part))
    cap = cap.fuse(cap_walls)
    for dx in (-8.75,8.75):
        for dy in (-12.75,12.75):
            foot = Part.makeCylinder(2.2,p["sensor_cap_clearance"],
                App.Vector(cx+dx,cy+dy,sensor_z+p["sensor_thickness"]))
            foot = foot.cut(Part.makeCylinder(1.4,p["sensor_cap_clearance"]+0.2,
                App.Vector(cx+dx,cy+dy,sensor_z+p["sensor_thickness"]-0.1)))
            cap = cap.fuse(foot)
            cap = cap.cut(Part.makeCylinder(p["sensor_cap_hole_diameter"]/2,
                p["sensor_cap_thickness"]+0.2,App.Vector(cx+dx,cy+dy,cap_bottom-0.1)))
    # Rev 1 J1 is a 1x06 2.54 mm header on a long edge, x=-10.25
    # from PCB centre, y=+-6.35. The header faces the keyboard (-X before mirroring).
    header_reliefs = []
    for side in (-1,):
        relief = box(cx-w/2-0.1 if side < 0 else cx+w/2-p["sensor_header_relief_width"],
                     cy-p["sensor_header_relief_length"]/2,cap_bottom,
                     p["sensor_header_relief_width"]+0.1,
                     p["sensor_header_relief_length"],peg_top,App,Part)
        # Continue the notch through the cap's outside edge.
        relief = relief.fuse(box(x0-0.1 if side < 0 else cx+w/2,
                     cy-p["sensor_header_relief_length"]/2,cap_bottom,
                     c+wall+0.2,p["sensor_header_relief_length"],peg_top,App,Part))
        cap = cap.cut(relief)
        header_reliefs.append(relief)
    cap = cap.removeSplitter()
    assert cap.isValid() and len(cap.Solids) == 1
    assert cap.common(case).Volume < 1e-6
    assert cap.common(sensor_board).Volume < 1e-6
    assert cap.common(lens).Volume < 1e-6
    assert cap_walls.distToShape(pocket)[0] < 1e-6
    assert all(cap.common(relief).Volume < 1e-6 for relief in header_reliefs)

    # Existing board is left-hand geometry. Reflect every assembly part together.
    mirror_x = case.BoundBox.XMax
    def right(shape):
        s = shape.mirror(App.Vector(mirror_x/2,0,0),App.Vector(1,0,0))
        return s
    shapes = {"yellowjacket-mouse-right": right(case),
              "yellowjacket-mouse-right-fit-frame": right(frame),
              "pmw3610-pocket-fit-test": right(pocket)}
    out = HERE / "output"
    out.mkdir(exist_ok=True)
    report = {"parameters":p, "source_sha256":board["source_sha256"],
              "keyboard_pcb_underside_z":pcb_z,
              "keyboard_pcb_top_above_desk":pcb_z+board["thickness"]+p["skate_thickness"],
              "sensor_pcb_underside_z":sensor_z,
              "sensor_raise_mm":sensor_z-pcb_z,
              "intentional_keyboard_grip_interference_mm3":grip_volume,
              "base_checks":base["checks"], "parts":{}}
    report["sensor_cap"] = {
        "pcb_top_clearance_mm":p["sensor_cap_clearance"],
        "wall_thickness_mm":wall,
        "wall_height_mm":cap_bottom-top,
        "wall_seating_z_mm":top,
        "wall_to_mount_gap_mm":cap_walls.distToShape(pocket)[0],
        "peg_extension_above_pcb_mm":p["sensor_peg_height"]-p["sensor_thickness"],
        "snap_radial_engagement_mm":(p["sensor_peg_diameter"]-p["sensor_cap_hole_diameter"])/2,
        "case_intersection_mm3":cap.common(case).Volume,
        "pcb_intersection_mm3":cap.common(sensor_board).Volume,
        "header_relief_side":"keyboard-facing",
        "header_relief_mm":[p["sensor_header_relief_width"],p["sensor_header_relief_length"]]}
    doc = App.newDocument("YellowjacketMouse")
    for name, shape in shapes.items():
        # Place the standalone coupon at XY origin; assembly remains registered.
        export_shape = shape
        if name.endswith("fit-test"):
            export_shape = moved(shape, App.Vector(-shape.BoundBox.XMin,-shape.BoundBox.YMin,0))
        _, checks = export_verified(export_shape,out/f"{name}.stl",tray_p,Mesh,MeshPart)
        export_shape.exportStep(str(out/f"{name}.step"))
        report["parts"][name] = checks
    printable_cap = right(cap)
    printable_cap.rotate(App.Vector(),App.Vector(1,0,0),180)
    bb = printable_cap.BoundBox
    printable_cap.translate(App.Vector(-bb.XMin,-bb.YMin,-bb.ZMin))
    _, checks = export_verified(printable_cap,out/"pmw3610-snap-cap.stl",tray_p,Mesh,MeshPart)
    printable_cap.exportStep(str(out/"pmw3610-snap-cap.step"))
    report["parts"]["pmw3610-snap-cap"] = checks
    cap_doc = App.newDocument("PMW3610SnapCap")
    cap_doc.addObject("Part::Feature","PrintableCap").Shape = printable_cap
    cap_doc.recompute()
    cap_doc.saveAs(str(out/"pmw3610-snap-cap.FCStd"))
    for name, shape in [("PrintableCase",right(case)),("KeyboardPCBReference",right(pcb)),
                        ("SensorCapInstalledReference",right(cap)),
                        ("SensorPCBReference",right(sensor_board)),("LensEnvelopeReference",right(lens))]:
        obj = doc.addObject("Part::Feature",name)
        obj.Shape = shape
        obj.addProperty("App::PropertyString","Notes")
        obj.Notes = "Reference envelope only" if "Reference" in name else "Print flat underside down"
    params = doc.addObject("Spreadsheet::Sheet","Dimensions")
    for row,(key,value) in enumerate(p.items(),1):
        params.set(f"A{row}",key)
        params.set(f"B{row}",str(value))
    doc.recompute()
    doc.saveAs(str(out/"yellowjacket-mouse-right.FCStd"))
    (out/"validation.json").write_text(json.dumps(report,indent=2)+"\n")
    (out/"board-snapshot.json").write_text(json.dumps(board,indent=2)+"\n")
    print(json.dumps({k:report[k] for k in ("keyboard_pcb_top_above_desk","sensor_raise_mm","parts")},indent=2))


if __name__ == "__main__":
    main()
