#!/usr/bin/env python3
"""Build and verify shallow PLA trays for the original Yellowjacket v0.1.2.

Requires the FreeCAD Python modules. No KiCad installation is needed: board.json
is an extracted, pinned snapshot of the original board's mechanical geometry.
"""

import argparse
import json
import math
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent


def load_freecad(module_path=None):
    if module_path:
        sys.path.insert(0, str(module_path))
    try:
        import FreeCAD
    except ImportError:
        for location in ("/usr/lib/freecad/lib", "/usr/lib/freecad-python3/lib",
                         "/usr/local/lib/freecad/lib"):
            if Path(location).is_dir():
                sys.path.append(location)
        try:
            import FreeCAD
        except ImportError as exc:
            raise SystemExit("FreeCAD modules not found. Pass --freecad-lib PATH, "
                             "or run with FreeCAD's Python environment.") from exc
    import Part
    import Mesh
    import MeshPart
    return FreeCAD, Part, Mesh, MeshPart


def moved(shape, vector):
    result = shape.copy()
    result.translate(vector)
    return result


def board_wire(board, App, Part):
    """Order edges and join their sub-0.01 mm legacy export rounding gaps."""
    remaining = [dict(edge) for edge in board["edges"]]
    ordered = [remaining.pop(0)]
    gaps = []
    while remaining:
        last = ordered[-1]["end"]
        candidates = [(math.dist(last, edge[end]), i, end)
                      for i, edge in enumerate(remaining) for end in ("start", "end")]
        gap, index, end = min(candidates)
        if gap > 0.01:
            raise ValueError(f"PCB outline is not continuous: {gap:.6f} mm gap")
        edge = remaining.pop(index)
        if end == "end":
            edge["start"], edge["end"] = edge["end"], edge["start"]
        ordered.append(edge)
        gaps.append(gap)
    gaps.append(math.dist(ordered[-1]["end"], ordered[0]["start"]))
    if max(gaps) > 0.01:
        raise ValueError("PCB outline does not close")
    junctions = [[(ordered[i - 1]["end"][axis] + edge["start"][axis]) / 2
                  for axis in (0, 1)] for i, edge in enumerate(ordered)]
    curves = []
    for i, edge in enumerate(ordered):
        start = App.Vector(junctions[i][0], -junctions[i][1], 0)
        end = App.Vector(junctions[(i + 1) % len(ordered)][0],
                         -junctions[(i + 1) % len(ordered)][1], 0)
        if edge["type"] == "arc":
            middle = App.Vector(edge["mid"][0], -edge["mid"][1], 0)
            curves.append(Part.Arc(start, middle, end).toShape())
        else:
            curves.append(Part.makeLine(start, end))
    wire = Part.Wire(curves)
    face = Part.Face(wire)
    if not wire.isClosed() or not face.isValid():
        raise ValueError("Invalid PCB outline")
    if face.normalAt(0, 0).z < 0:
        wire.reverse()
    return wire, max(gaps)


def offset_wire(wire, distance, Part):
    # The print outline is already chord-approximated; miter joins avoid
    # microscopic circular caps at almost-collinear sample points.
    result = wire.makeOffset2D(distance, join=2)
    if len(result.Wires) != 1 or not result.Wires[0].isClosed():
        raise ValueError(f"Offset {distance} mm did not produce one closed wire")
    result = result.Wires[0]
    if not Part.Face(result).isValid():
        raise ValueError(f"Invalid offset at {distance} mm")
    return result


def printable_wire(wire, chord_error, Part):
    # The legacy outline contains almost-tangent arc/line junctions. Exact
    # offsets create nanometre-sized sliver faces there, which cannot survive
    # STL's float32 coordinates. A bounded chord approximation avoids them.
    points = wire.discretize(Deflection=chord_error)
    clean = [points[0]]
    for point in points[1:]:
        if (point - clean[-1]).Length > 1e-5:
            clean.append(point)
    if (clean[-1] - clean[0]).Length < 1e-5:
        clean[-1] = clean[0]
    else:
        clean.append(clean[0])
    return Part.makePolygon(clean)


def check_parameters(p, board):
    if any(not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0
           for value in p.values()):
        raise ValueError("Every parameter must be a positive finite number in mm")
    if p["wall_above_pcb_underside"] >= board["thickness"]:
        raise ValueError("Keep the tray rim below the PCB top surface")
    if p["power_switch_relief_depth"] >= p["under_pcb_clearance"] + p["wall_above_pcb_underside"]:
        raise ValueError("The power-switch relief must stop above the floor")
    support_height = p["under_pcb_clearance"] - p["adhesive_allowance"]
    if support_height <= p["ledge_thickness"]:
        raise ValueError("Not enough space for the ledge below the PCB")
    if p["ledge_thickness"] < p["ledge_width"] + p["pcb_clearance"] + 2 * p["outline_chord_error"]:
        raise ValueError("Ledge underside would exceed a 45 degree overhang")


def build(board, p, App, Part, support_points=None):
    original_wire, max_gap = board_wire(board, App, Part)
    face = Part.Face(original_wire)
    wire = printable_wire(original_wire, p["outline_chord_error"], Part)
    # Allow twice the discretizer's requested deflection, then measure the
    # actual minimum clearance to the original arcs before accepting the tray.
    clearance = p["pcb_clearance"] + 2 * p["outline_chord_error"]
    cavity_wire = offset_wire(wire, clearance, Part)
    outer_wire = offset_wire(wire, clearance + p["wall_thickness"], Part)
    ledge_wire = offset_wire(wire, -p["ledge_width"], Part)
    cavity, outer = Part.Face(cavity_wire), Part.Face(outer_wire)
    if not outer.Area > cavity.Area > face.Area > Part.Face(ledge_wire).Area:
        raise ValueError("Unexpected PCB offset direction")
    floor_z = p["floor_thickness"]
    pcb_z = floor_z + p["under_pcb_clearance"]
    support_z = pcb_z - p["adhesive_allowance"]
    top_z = pcb_z + p["wall_above_pcb_underside"]
    floor = outer.extrude(App.Vector(0, 0, floor_z))
    walls = moved(outer.cut(cavity).extrude(App.Vector(0, 0, top_z - floor_z)),
                  App.Vector(0, 0, floor_z))

    # Small <=0.2 mm rises approximate a <=45 degree underside. Lofting whole
    # offset outlines is unreliable where the original's tiny edges disappear;
    # these stepped rings also line up with a normal 0.2 mm FDM layer height.
    ledge_bottom = support_z - p["ledge_thickness"]
    steps = math.ceil(p["ledge_thickness"] / 0.2)
    step_height = p["ledge_thickness"] / steps
    rings = []
    for step in range(steps):
        inset = clearance - (clearance + p["ledge_width"]) * (step + 1) / steps
        inner = Part.Face(offset_wire(wire, inset, Part))
        ring = cavity.cut(inner).extrude(App.Vector(0, 0, step_height))
        rings.append(moved(ring, App.Vector(0, 0, ledge_bottom + step * step_height)))
    ledge = rings[0].multiFuse(rings[1:]).removeSplitter()

    mounts = [fp["at"] for fp in board["footprints"]
              if "thread_m2" in fp["name"] and fp["at"][0] < 100]
    controller = next(fp for fp in board["footprints"] if fp["reference"] == "U1")
    # The third 'thread_m2' reference at (126.344678, 56.84275) actually
    # overlaps a reversible switch pad. Use a verified clear area instead.
    if support_points is None:
        support_points = mounts + [[119.0, 60.0], controller["at"]]
    posts = [Part.makeCylinder(p["support_diameter"] / 2, support_z - floor_z,
                              App.Vector(point[0], -point[1], floor_z))
             for point in support_points]

    # Conservatively keep clear of BOTH alternatives in reversible footprints.
    # Circular envelopes include pad corners and a margin for solder fillets.
    pad_sizes = {}
    for fp in board["footprints"]:
        for pad in fp["pads"]:
            radius = (max(pad["size"]) / 2 if pad["shape"] == "circle"
                      else math.hypot(*pad["size"]) / 2)
            key = tuple(round(value, 5) for value in pad["at"])
            pad_sizes[key] = max(pad_sizes.get(key, 0), radius + p["pad_keepout_margin"])
    envelopes = [Part.makeCylinder(radius, pcb_z - floor_z,
                                   App.Vector(x, -y, floor_z))
                 for (x, y), radius in pad_sizes.items()]
    keepouts = Part.makeCompound(envelopes)
    ledge = ledge.cut(keepouts)
    trimmed_posts = [post.cut(keepouts) for post in posts]
    board_column = face.extrude(App.Vector(0, 0, pcb_z))
    for point, post, original in zip(support_points, trimmed_posts, posts):
        if not post.isValid() or len(post.Solids) != 1 or post.Volume < 0.9 * original.Volume:
            raise ValueError(f"Tape support at {point} overlaps pads "
                             f"({post.Volume / original.Volume:.1%} remaining); "
                             "choose a smaller support diameter")
        if post.cut(board_column).Volume > 1e-6:
            raise ValueError(f"Tape support at {point} extends outside the PCB")
    tray = floor.multiFuse([walls, ledge, *trimmed_posts]).removeSplitter()

    # A floorless perimeter print checks the entire outline with less filament.
    frame_inner = Part.Face(offset_wire(wire, -3.0, Part))
    frame_floor = outer.cut(frame_inner).extrude(App.Vector(0, 0, floor_z))
    frame = frame_floor.multiFuse([walls, ledge]).removeSplitter()

    # Centre an open-top notch on PSW1 at the upper edge of the MCU area.
    # Anchor it to the actual switch footprint rather than the tray bounds.
    switch = next(fp for fp in board["footprints"] if fp["reference"] == "PSW1")
    switch_x, switch_y = switch["at"]
    upper_edges = [edge for edge in board["edges"] if edge["type"] == "line"
                   and abs(edge["start"][1] - edge["end"][1]) < 0.01
                   and max(edge["start"][1], edge["end"][1]) < switch_y
                   and min(edge["start"][0], edge["end"][0]) <= switch_x
                   <= max(edge["start"][0], edge["end"][0])]
    if not upper_edges:
        raise ValueError("No upper PCB edge found beside the power switch")
    edge_y = max((edge["start"][1] + edge["end"][1]) / 2 for edge in upper_edges)
    relief_bottom = top_z - p["power_switch_relief_depth"]
    relief = Part.makeBox(
        p["power_switch_relief_width"],
        p["ledge_width"] + clearance + p["wall_thickness"] + 2,
        p["power_switch_relief_depth"] + 1,
        App.Vector(switch_x - p["power_switch_relief_width"] / 2,
                   -edge_y - p["ledge_width"] - 1, relief_bottom))
    relief_removed = tray.common(relief).Volume
    tray = tray.cut(relief).removeSplitter()
    frame = frame.cut(relief).removeSplitter()
    walls = walls.cut(relief)
    relief_remaining = tray.common(relief).Volume
    if relief_removed <= 1e-6 or relief_remaining > 1e-6:
        raise ValueError("The power-switch relief was not cut through the upper rim")

    pcb = moved(face.extrude(App.Vector(0, 0, board["thickness"])),
                App.Vector(0, 0, pcb_z))
    collision = tray.common(pcb).Volume
    solder_collision = tray.common(keepouts).Volume
    edge_at_board = moved(original_wire, App.Vector(0, 0, pcb_z + 0.1))
    edge_clearance = edge_at_board.distToShape(walls)[0]
    if collision > 1e-6 or solder_collision > 1e-6:
        raise ValueError(f"Interference: PCB {collision}, pad envelopes {solder_collision} mm^3")
    if edge_clearance < p["pcb_clearance"] - 0.002:
        raise ValueError(f"PCB-to-wall clearance {edge_clearance:.6f} mm is smaller than requested")

    shift = App.Vector(-outer.BoundBox.XMin, -outer.BoundBox.YMin, 0)
    return {
        "tray": moved(tray, shift), "frame": moved(frame, shift),
        "pcb": moved(pcb, shift), "outline": moved(original_wire, shift),
        "support_points": [[x + shift.x, -y + shift.y] for x, y in support_points],
        "pcb_z": pcb_z, "support_z": support_z,
        "checks": {"maximum_source_endpoint_gap_mm": max_gap,
                   "pcb_intersection_mm3": collision,
                   "pad_envelope_intersection_mm3": solder_collision,
                   "minimum_pcb_to_wall_mm": edge_clearance,
                   "pcb_size_mm": [face.BoundBox.XLength, face.BoundBox.YLength],
                   "tape_support_count": len(trimmed_posts),
                   "support_centres_source_xy_mm": support_points,
                   "power_switch_relief": {
                       "switch_centre_source_xy_mm": switch["at"],
                       "upper_pcb_edge_source_y_mm": edge_y,
                       "bottom_z_mm": relief_bottom,
                       "removed_material_mm3": relief_removed,
                       "remaining_material_mm3": relief_remaining}},
    }


def export_verified(shape, path, p, Mesh, MeshPart):
    if not shape.isValid() or len(shape.Solids) != 1 or shape.Volume <= 0:
        raise ValueError(f"{path.stem}: CAD shape is not one valid solid")
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=p["mesh_deflection"],
                                  AngularDeflection=0.15, Relative=False)
    mesh.write(str(path))
    # Check the exported file, rather than only trusting the in-memory mesh.
    saved = Mesh.Mesh(str(path))
    checks = {
        "size_mm": [shape.BoundBox.XLength, shape.BoundBox.YLength, shape.BoundBox.ZLength],
        "cad_valid": shape.isValid(), "solid_count": len(shape.Solids),
        "watertight": saved.isSolid(), "mesh_components": saved.countComponents(),
        "self_intersections": saved.hasSelfIntersections(),
        "facets": saved.CountFacets, "volume_mm3": saved.Volume,
    }
    if (not checks["watertight"] or checks["mesh_components"] != 1
            or checks["self_intersections"] or checks["volume_mm3"] <= 0):
        raise ValueError(f"{path.name}: failed mesh validation: {checks}")
    return saved, checks


def save_document(shapes, board, p, output, App):
    doc = App.newDocument("YellowjacketTray")
    doc.Label = "Yellowjacket v0.1.2 - shallow tray prototype"
    width = shapes["left"].BoundBox.XLength
    for side in ("left", "right"):
        offset = App.Vector((width + 15) if side == "right" else 0, 0, 0)
        obj = doc.addObject("Part::Feature", f"{side.title()}Tray")
        obj.Label = f"{side.title()} tray - printable"
        obj.Shape = moved(shapes[side], offset)
        for name, value in p.items():
            prop = "".join(word.title() for word in name.split("_"))
            obj.addProperty("App::PropertyLength", prop, "Generator inputs")
            setattr(obj, prop, value)
            obj.setEditorMode(prop, 1)
        obj.addProperty("App::PropertyString", "SourceCommit", "Source")
        obj.SourceCommit = board["source"]["commit"]
        obj.addProperty("App::PropertyString", "Adjustment", "Source")
        obj.Adjustment = "Edit parameters.json and rerun generate.py to rebuild."
        pcb = doc.addObject("Part::Feature", f"{side.title()}PCBReference")
        pcb.Label = f"{side.title()} PCB envelope - reference only"
        pcb.Shape = moved(shapes[f"{side}_pcb"], offset)
    doc.recompute()
    doc.saveAs(str(output / "yellowjacket-trays.FCStd"))
    App.closeDocument(doc.Name)


def preview(meshes, shapes, result, p, path):
    """Small offline preview; Pillow is optional and not needed to build CAD."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np
    except ImportError:
        print("Pillow/numpy unavailable; skipping preview.png")
        return
    image = Image.new("RGB", (1600, 1000), "#f2f3f5")
    draw = ImageDraw.Draw(image)
    font_path = "/usr/share/fonts/TTF/DejaVuSans.ttf"
    try:
        title = ImageFont.truetype(font_path, 34)
        label = ImageFont.truetype(font_path, 22)
    except OSError:
        title = label = ImageFont.load_default(size=24)
    draw.text((48, 26), "Yellowjacket v0.1.2 | shallow PLA tray", fill="#182238", font=title)
    draw.text((48, 74), "First-fit prototype / top-mounted controller / battery above PCB",
              fill="#536175", font=label)

    def project(v):
        return (0.866 * v[0] + 0.5 * v[1], 0.35 * v[0] - 0.606 * v[1] - 1.4 * v[2])

    for side, start_x in (("left", 40), ("right", 820)):
        points, facets = meshes[side].Topology
        projected = [project(v) for v in points]
        min_x, max_x = min(v[0] for v in projected), max(v[0] for v in projected)
        min_y, max_y = min(v[1] for v in projected), max(v[1] for v in projected)
        scale = min(720 / (max_x - min_x), 380 / (max_y - min_y))
        screen = np.array([((u - min_x) * scale, (v - min_y) * scale)
                           for u, v in projected])
        depths = [0.5 * v[0] - 0.866 * v[1] + 0.5 * v[2] for v in points]
        panel = np.full((400, 740, 3), (242, 243, 245), dtype=np.uint8)
        depth_buffer = np.full((400, 740), -np.inf)
        for facet in facets:
            a, b, c = (points[i] for i in facet)
            normal = (b - a).cross(c - a)
            if normal.Length:
                normal.normalize()
            if normal.dot(type(a)(0.5, -0.866, 0.5)) <= 0:
                continue
            brightness = 0.62 + 0.32 * max(0, normal.dot(type(a)(-0.25, -0.35, 0.9)))
            color = tuple(int(channel * brightness) for channel in (245, 190, 57))
            triangle = screen[list(facet)]
            x0, y0 = np.floor(triangle.min(axis=0)).astype(int)
            x1, y1 = np.ceil(triangle.max(axis=0)).astype(int)
            x0, x1 = max(0, x0), min(739, x1)
            y0, y1 = max(0, y0), min(399, y1)
            if x0 > x1 or y0 > y1:
                continue
            (ax, ay), (bx, by), (cx, cy) = triangle
            denominator = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
            if abs(denominator) < 1e-10:
                continue
            xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5,
                                 np.arange(y0, y1 + 1) + 0.5)
            wa = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / denominator
            wb = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / denominator
            wc = 1 - wa - wb
            depth = wa * depths[facet[0]] + wb * depths[facet[1]] + wc * depths[facet[2]]
            old_depth = depth_buffer[y0:y1 + 1, x0:x1 + 1]
            mask = (wa >= -1e-7) & (wb >= -1e-7) & (wc >= -1e-7) & (depth > old_depth)
            old_depth[mask] = depth[mask]
            panel[y0:y1 + 1, x0:x1 + 1][mask] = color
        image.paste(Image.fromarray(panel), (start_x + 15, 158))
        draw.text((start_x + 20, 122), f"{side.title()} tray / power-switch access notch",
                  fill="#182238", font=label)

        # Top view shows the board envelope and the tape support positions.
        tray_wire = shapes["left_outline"]
        if side == "right":
            tray_wire = tray_wire.mirror(type(a)(shapes[side].BoundBox.XLength / 2, 0, 0),
                                         type(a)(1, 0, 0))
        # A direct outline from the reference board avoids selecting a side face.
        outline = tray_wire.discretize(Deflection=0.08)
        box = shapes[side].BoundBox
        top_scale = min(660 / box.XLength, 340 / box.YLength)

        def top(v):
            return (start_x + 40 + v[0] * top_scale, 950 - v[1] * top_scale)

        draw.polygon([top(v) for v in outline], fill="#e1e3ec", outline="#56637a", width=2)
        width = box.XLength
        for x, y in result["support_points"]:
            if side == "right":
                x = width - x
            u, v = top((x, y))
            radius = p["support_diameter"] / 2 * top_scale
            draw.ellipse((u - radius, v - radius, u + radius, v + radius),
                         fill="#f0b735", outline="#79560d", width=2)
        draw.text((start_x + 20, 580), "PCB outline + adhesive support locations",
                  fill="#536175", font=label)
    box = shapes["left"].BoundBox
    draw.text((48, 966), f"Each tray: {box.XLength:.1f} x {box.YLength:.1f} x {box.ZLength:.1f} mm"
              f"  |  {p['wall_thickness']:g} mm walls  |  {p['pcb_clearance']:g} mm nominal PCB gap",
              fill="#536175", font=label)
    image.save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parameters", type=Path, default=HERE / "parameters.json")
    parser.add_argument("--output", type=Path, default=HERE / "output")
    parser.add_argument("--freecad-lib", type=Path)
    args = parser.parse_args()
    board = json.loads((HERE / "board.json").read_text())
    p = json.loads(args.parameters.read_text())
    check_parameters(p, board)
    App, Part, Mesh, MeshPart = load_freecad(args.freecad_lib)
    print("Building original Yellowjacket v0.1.2 tray...", flush=True)
    result = build(board, p, App, Part)
    left = result["tray"]
    centre, normal = App.Vector(left.BoundBox.XLength / 2, 0, 0), App.Vector(1, 0, 0)
    shapes = {"left": left, "right": left.mirror(centre, normal),
              "left_frame": result["frame"], "right_frame": result["frame"].mirror(centre, normal),
              "left_pcb": result["pcb"], "right_pcb": result["pcb"].mirror(centre, normal),
              "left_outline": result["outline"]}
    args.output.mkdir(parents=True, exist_ok=True)
    report = {"source": board["source"], "parameters_mm": p,
              "freecad_version": App.Version(), "clearance_checks": result["checks"],
              "artifacts": {}}
    meshes = {}
    for key in ("left", "right", "left_frame", "right_frame"):
        name = f"yellowjacket-{key.replace('_', '-')}.stl"
        meshes[key], report["artifacts"][name] = export_verified(
            shapes[key], args.output / name, p, Mesh, MeshPart)
        if not key.endswith("frame"):
            shapes[key].exportStep(str(args.output / f"yellowjacket-{key}.step"))
        print(f"Verified {name}: {report['artifacts'][name]['size_mm']}", flush=True)
    save_document(shapes, board, p, args.output, App)
    preview(meshes, shapes, result, p, args.output / "preview.png")
    (args.output / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Done: {args.output}")


if __name__ == "__main__":
    main()
