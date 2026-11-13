#!/usr/bin/env python3
"""Generate snap cases, a back-to-back carrier, and its accessories.

Keeps the original tray generator and its output unchanged. Dimensions are mm;
the original Choc board.json snapshot is the only PCB input. No KiCad required.
"""

import argparse
import json
import math
from pathlib import Path

from generate import (HERE, board_wire, build, check_parameters, export_verified,
                      load_freecad, moved, offset_wire, printable_wire)


EPS = 1e-6
CAP_CLIP_THICKNESS_MM = 0.8


def check_enclosure_parameters(p, tray, board):
    for group in ("snap", "travel"):
        for name, value in p[group].items():
            if name == "edge_seeds_source_xy":
                if (not isinstance(value, list) or len(value) != 4
                        or any(not isinstance(point, list) or len(point) != 2
                               or any(isinstance(n, bool) or not isinstance(n, (int, float))
                                      or not math.isfinite(n) for n in point)
                               for point in value)):
                    raise ValueError("Provide four finite XY edge seed pairs")
                continue
            minimum_ok = (isinstance(value, (int, float)) and not isinstance(value, bool)
                          and math.isfinite(value)
                          and (value >= 0 if name == "feet_height" else value > 0))
            if not minimum_ok:
                raise ValueError(f"{group}.{name} must be finite and positive (feet_height may be zero)")
    s, t = p["snap"], p["travel"]
    pcb_z = tray["floor_thickness"] + tray["under_pcb_clearance"]
    bezel_z = pcb_z + board["thickness"] + s["pcb_vertical_clearance"]
    if s["retaining_lip_width"] >= 2 or s["pcb_vertical_clearance"] > 0.5:
        raise ValueError("Keep the lip below 2 mm and PCB vertical play at most 0.5 mm")
    if s["skirt_bottom_z"] <= tray["floor_thickness"]:
        raise ValueError("Snap skirts and catches must remain above the bottom floor")
    if s["skirt_bottom_z"] + s["hook_height"] + s["catch_clearance"] >= pcb_z:
        raise ValueError("Snap catch must remain below the PCB support plane")
    if s["skirt_bottom_z"] >= bezel_z:
        raise ValueError("The skirt must reach below the bezel")
    if s["skirt_clearance"] <= 0.1 or s["hook_height"] <= s["hook_projection"]:
        raise ValueError("Allow skirt clearance and a positive hook retaining shoulder")
    for label, projection, gap, thickness, length, catch in (
            ("snap", s["hook_projection"], s["skirt_clearance"],
             s["flexure_thickness"], s["flexure_length"], s["catch_clearance"]),
            ("travel", t["clip_hook_projection"], t["clip_clearance"],
             t["clip_thickness"], t["clip_length"], t["catch_clearance"])):
        if projection <= gap:
            raise ValueError(f"{label}: hook does not engage its catch")
        if projection - gap + catch >= tray["wall_thickness"] - 0.8:
            raise ValueError(f"{label}: catch leaves too little wall material")
        # Small-deflection cantilever estimate, not a material/strength guarantee.
        strain = 1.5 * thickness * (projection - gap + 0.1) / length ** 2
        if strain > 0.012:
            raise ValueError(f"{label}: estimated snap strain exceeds 1.2%; lengthen the beam")
    cap_clip_length = t["clip_overlap"] + t["tongue_height"]
    cap_clip_strain = (1.5 * CAP_CLIP_THICKNESS_MM *
                       (t["clip_hook_projection"] - t["clip_clearance"] + 0.1) /
                       cap_clip_length ** 2)
    if cap_clip_strain > 0.012:
        raise ValueError("travel cap: estimated snap strain exceeds 1.2%; lengthen the beam")
    if s["hook_width"] >= s["flexure_length"] / 2:
        raise ValueError("The desk hook must occupy less than half the flexure")
    if t["clip_overlap"] <= t["clip_hook_height"] + t["catch_clearance"]:
        raise ValueError("Travel catch must be completely below the seam")
    if t["tongue_height"] >= t["clip_length"] - t["clip_overlap"]:
        raise ValueError("Travel clip root must be above the locating tongue")
    if t["clip_length"] - t["clip_overlap"] + t["clip_root_height"] >= t["keyboard_height"] + t["divider_foam"] + t["key_clearance"]:
        raise ValueError("Keyboard height must allow the travel clip root to fit below the roof")
    if t["corner_radius"] <= t["ledge_width"]:
        raise ValueError("Travel corner radius must exceed the ledge width")
    if t["ledge_width"] <= t["tongue_clearance"] + t["tongue_thickness"] + 0.8:
        raise ValueError("Divider needs at least 0.8 mm bearing on the ledge")
    if t["cradle_wall_inset"] + t["cradle_contact_width"] >= tray["wall_thickness"]:
        raise ValueError("Cradle contact must remain on the fixed case wall")
    if t["cradle_wall_inset"] <= s["flexure_gap"] - s["skirt_clearance"]:
        raise ValueError("Cradle contact would hit a bezel flexure clearance slot")
    if t["key_clearance"] <= t["cradle_floor"]:
        raise ValueError("Keys need clearance above the cradle floor")
    if t["keyboard_height"] <= bezel_z + s["bezel_thickness"] + t["feet_height"] + t["cradle_pad"]:
        raise ValueError("Keyboard height leaves no room for a lower cradle")


def prism(face, z, height, App):
    return moved(face.extrude(App.Vector(0, 0, height)), App.Vector(0, 0, z))


def box(x, y, z, dx, dy, dz, App, Part):
    return Part.makeBox(dx, dy, dz, App.Vector(x, y, z))


def require_solid(shape, label):
    if not shape.isValid() or len(shape.Solids) != 1 or shape.Volume <= EPS:
        raise ValueError(f"{label}: expected one valid connected solid")


def no_collision(a, b, label):
    volume = a.common(b).Volume
    if volume > EPS:
        raise ValueError(f"{label}: {volume:.6f} mm^3 interference")
    return volume


def rounded_face(width, depth, radius, App, Part):
    """Centered rounded rectangle, with analytic quarter-circle corners."""
    if width <= 2 * radius or depth <= 2 * radius:
        raise ValueError("Corner radius is too large for rounded rectangle")
    x, y, r = width / 2, depth / 2, radius
    points = [(-x + r, -y), (x - r, -y), (x, -y + r), (x, y - r),
              (x - r, y), (-x + r, y), (-x, y - r), (-x, -y + r)]
    centers = [(x - r, -y + r), (x - r, y - r),
               (-x + r, y - r), (-x + r, -y + r)]
    edges = []
    for i in range(4):
        start, end = points[2 * i], points[2 * i + 1]
        edges.append(Part.makeLine(App.Vector(*start, 0), App.Vector(*end, 0)))
        next_point = points[(2 * i + 2) % 8]
        c = centers[i]
        middle = (c[0] + (end[0] + next_point[0] - 2 * c[0]) / math.sqrt(2),
                  c[1] + (end[1] + next_point[1] - 2 * c[1]) / math.sqrt(2))
        edges.append(Part.Arc(App.Vector(*end, 0), App.Vector(*middle, 0),
                              App.Vector(*next_point, 0)).toShape())
    return Part.Face(Part.Wire(edges))


def local(shape, anchor, tangent, App):
    """Local X runs along the edge; local +Y points out of the case."""
    result = shape.copy()
    result.rotate(App.Vector(), App.Vector(0, 0, 1),
                  math.degrees(math.atan2(tangent[1], tangent[0])))
    result.translate(App.Vector(anchor[0], anchor[1], 0))
    return result


def wedge(x, width, profile_yz, App, Part):
    points = [App.Vector(x, y, z) for y, z in profile_yz]
    return Part.Face(Part.makePolygon(points + [points[0]])).extrude(App.Vector(width, 0, 0))


def component_envelopes(board, s, z, height, shift, App, Part, keys=False, travel=None):
    shapes = []
    for fp in board["footprints"]:
        ref = fp["reference"]
        if ref.startswith("SW"):
            width, depth = ((travel["keycap_width"], travel["keycap_depth"]) if keys
                            else (s["switch_body_width"], s["switch_body_depth"]))
        elif ref == "U1":
            width, depth = s["controller_width"], s["controller_depth"]
        elif ref == "BT1":
            width, depth = s["battery_width"], s["battery_depth"]
        elif ref == "PSW1":
            width, depth = 8.5, 5.5
        else:
            continue
        margin = travel["keycap_margin"] if keys else s["component_margin"]
        width, depth = width + 2 * margin, depth + 2 * margin
        shape = box(-width / 2, -depth / 2, z, width, depth, height, App, Part)
        shape.rotate(App.Vector(), App.Vector(0, 0, 1), fp["rotation"])
        shape.translate(App.Vector(fp["at"][0] + shift.x, -fp["at"][1] + shift.y, 0))
        shapes.append(shape)
    return Part.makeCompound(shapes)


def pad_envelopes(board, margin, z, height, shift, App, Part):
    sizes = {}
    for fp in board["footprints"]:
        for pad in fp["pads"]:
            radius = (max(pad["size"]) / 2 if pad["shape"] == "circle"
                      else math.hypot(*pad["size"]) / 2)
            key = tuple(round(v, 5) for v in pad["at"])
            sizes[key] = max(sizes.get(key, 0), radius + margin)
    return Part.makeCompound([Part.makeCylinder(
        radius, height, App.Vector(x + shift.x, -y + shift.y, z))
        for (x, y), radius in sizes.items()])


def edge_locations(board, wire, shift, distance, s, App, Part):
    """Use four explicit long straight edges, never the power/USB opening."""
    locations, chosen = [], set()
    for seed in s["edge_seeds_source_xy"]:
        lines = [(math.dist(seed, [(e["start"][i] + e["end"][i]) / 2 for i in (0, 1)]), i, e)
                 for i, e in enumerate(board["edges"]) if e["type"] == "line"]
        _, index, edge = min(lines)
        if index in chosen:
            raise ValueError("Snap edge seeds must select four distinct edges")
        chosen.add(index)
        a = App.Vector(edge["start"][0] + shift.x, -edge["start"][1] + shift.y, 0)
        b = App.Vector(edge["end"][0] + shift.x, -edge["end"][1] + shift.y, 0)
        length = (b - a).Length
        if length < s["flexure_length"] + s["root_length"] + 2:
            raise ValueError("Selected edge is too short for a flexure and its root")
        tangent = (b - a).normalize()
        normal = App.Vector(-tangent.y, tangent.x, 0)
        midpoint = (a + b) / 2
        if Part.Face(wire).isInside(midpoint + normal * 0.1, 1e-7, True):
            tangent, normal = -tangent, -normal
        anchor = midpoint + normal * distance - tangent * (s["flexure_length"] - s["root_length"]) / 2
        locations.append({"anchor": [anchor.x, anchor.y], "tangent": [tangent.x, tangent.y],
                          "midpoint": [midpoint.x, midpoint.y],
                          "source_edge_index": index, "edge_length": length})
    return locations


def desk_latch(s, top, App, Part):
    length, gap, thick = s["flexure_length"], s["skirt_clearance"], s["flexure_thickness"]
    bottom, height = s["skirt_bottom_z"], s["hook_height"]
    # Deliberately overlap the offset skirt by 0.05 mm. Coincident planes from
    # legacy outline rounding otherwise leave micron-wide faces in the STL.
    root = box(-s["root_length"], gap - 0.05, bottom, s["root_length"] + 0.05,
               s["skirt_thickness"] + 0.1, top - bottom, App, Part)
    beam = box(0, gap, bottom, length, thick, top - bottom, App, Part)
    hook = wedge(length - s["hook_width"], s["hook_width"],
                 [(gap + 0.05, bottom), (gap, bottom),
                  (gap - s["hook_projection"], bottom + s["hook_projection"]),
                  (gap - s["hook_projection"], bottom + height),
                  (gap + 0.05, bottom + height)], App, Part)
    latch = root.multiFuse([beam, hook]).removeSplitter()
    # Round the re-entrant corner where the thin horizontal beam leaves its
    # wider root. Select by geometry rather than unstable edge indices.
    root_edges = [edge for edge in latch.Edges
                  if abs(edge.CenterOfMass.x - 0.05) < EPS
                  and abs(edge.CenterOfMass.y - gap - thick) < EPS
                  and edge.BoundBox.ZLength > top - bottom - EPS]
    if len(root_edges) != 1:
        raise ValueError("Could not identify the desk latch root edge")
    latch = latch.makeFillet(0.3, root_edges)
    c = s["catch_clearance"]
    pocket = box(length - s["hook_width"] - c, gap - s["hook_projection"] - c, bottom - c,
                 s["hook_width"] + 2 * c, s["hook_projection"] + c + 0.1,
                 height + 2 * c, App, Part)
    slot = box(0, gap - s["flexure_gap"], bottom - 1, length + s["flexure_gap"],
               6, top - bottom + 2, App, Part)
    return latch, pocket, slot


def build_snap(board, tray_p, s, App, Part):
    # The base is the original verified outline/support design, with supports at
    # the actual PCB underside: no adhesive or drilled PCB holes are required.
    base_p = dict(tray_p, adhesive_allowance=0.0)
    result = build(board, base_p, App, Part)
    base = result["tray"]
    original = result["outline"]
    wire = printable_wire(original, tray_p["outline_chord_error"], Part)
    clearance = tray_p["pcb_clearance"] + 2 * tray_p["outline_chord_error"]
    outer_distance = clearance + tray_p["wall_thickness"]
    pcb_top = result["pcb_z"] + board["thickness"]
    lip_z = pcb_top + s["pcb_vertical_clearance"]
    top = lip_z + s["bezel_thickness"]
    outer = Part.Face(offset_wire(wire, outer_distance, Part))
    cavity = Part.Face(offset_wire(wire, clearance, Part))
    skirt_outer = Part.Face(offset_wire(wire, outer_distance + s["skirt_clearance"] + s["skirt_thickness"], Part))
    skirt_inner = Part.Face(offset_wire(wire, outer_distance + s["skirt_clearance"], Part))
    lip_inner = Part.Face(offset_wire(wire, -s["retaining_lip_width"], Part))
    ring = prism(skirt_outer.cut(lip_inner), lip_z, s["bezel_thickness"], App)
    skirt = prism(skirt_outer.cut(skirt_inner), s["skirt_bottom_z"], lip_z - s["skirt_bottom_z"], App)
    base_top = base.BoundBox.ZMax
    stops = prism(outer.cut(cavity), base_top, lip_z - base_top, App)
    bezel = ring.multiFuse([skirt, stops]).removeSplitter()
    # Recover the same translation used by the tray generator.
    source_wire, _ = board_wire(board, App, Part)
    shift = App.Vector(original.BoundBox.XMin - source_wire.BoundBox.XMin,
                       original.BoundBox.YMin - source_wire.BoundBox.YMin, 0)
    components = component_envelopes(board, s, pcb_top, top - pcb_top + 1, shift, App, Part)
    pads = pad_envelopes(board, tray_p["pad_keepout_margin"], pcb_top,
                         top - pcb_top + 1, shift, App, Part)
    bezel = bezel.cut(components).cut(pads)
    notch = result["checks"]["power_switch_relief"]
    switch_x = notch["switch_centre_source_xy_mm"][0] + shift.x
    edge_y = -notch["upper_pcb_edge_source_y_mm"] + shift.y
    opening = box(switch_x - s["power_usb_opening_width"] / 2, edge_y - 6, s["skirt_bottom_z"] - 0.1,
                  s["power_usb_opening_width"], 14, top - s["skirt_bottom_z"] + 1, App, Part)
    bezel = bezel.cut(opening)
    locations = edge_locations(board, original, shift, outer_distance, s, App, Part)
    latch, pocket, slot = desk_latch(s, top, App, Part)
    hooks = []
    for location in locations:
        anchor, tangent = location["anchor"], location["tangent"]
        bezel = bezel.cut(local(slot, anchor, tangent, App))
        hooks.append(local(latch, anchor, tangent, App))
        base = base.cut(local(pocket, anchor, tangent, App))
    bezel = bezel.multiFuse(hooks).removeSplitter()
    base = base.removeSplitter()
    require_solid(base, "Snap bottom")
    require_solid(bezel, "Snap bezel")
    # A slab just above the PCB measures actual capture after all keepouts.
    bearing = bezel.common(prism(Part.Face(original), lip_z, s["bezel_thickness"], App))
    capture_area = bearing.Volume / s["bezel_thickness"]
    if capture_area < 60:
        raise ValueError("Not enough bare-PCB edge capture remains")
    bounds = original.BoundBox
    quadrant_areas = []
    for x in (bounds.XMin, (bounds.XMin + bounds.XMax) / 2):
        for y in (bounds.YMin, (bounds.YMin + bounds.YMax) / 2):
            quadrant = box(x, y, lip_z, bounds.XLength / 2, bounds.YLength / 2,
                           s["bezel_thickness"], App, Part)
            area = bearing.common(quadrant).Volume / s["bezel_thickness"]
            if area < 5:
                raise ValueError("The PCB needs retaining lip capture in every quadrant")
            quadrant_areas.append(area)
    checks = {
        "base_pcb_intersection_mm3": no_collision(base, result["pcb"], "Base / PCB"),
        "bezel_pcb_intersection_mm3": no_collision(bezel, result["pcb"], "Bezel / PCB"),
        "base_bezel_intersection_mm3": no_collision(base, bezel, "Snap assembly"),
        "bezel_component_intersection_mm3": no_collision(bezel, components, "Bezel / components"),
        "bezel_pad_intersection_mm3": no_collision(bezel, pads, "Bezel / pads"),
        "retaining_lip_projected_area_mm2": capture_area,
        "retaining_lip_area_by_quadrant_mm2": quadrant_areas,
        "pcb_underside_z_mm": result["pcb_z"], "pcb_top_z_mm": pcb_top,
        "bezel_top_z_mm": top, "snap_count": len(locations),
        "hook_wall_engagement_mm": s["hook_projection"] - s["skirt_clearance"],
        "pcb_vertical_play_seated_mm": s["pcb_vertical_clearance"],
        "maximum_nominal_pcb_vertical_play_mm": s["pcb_vertical_clearance"] + s["catch_clearance"],
        "estimated_flexure_strain_percent": 150 * s["flexure_thickness"] *
            (s["hook_projection"] - s["skirt_clearance"] + 0.1) / s["flexure_length"] ** 2,
        "support_count": result["checks"]["tape_support_count"],
        "support_centres_source_xy_mm": result["checks"]["support_centres_source_xy_mm"],
        "power_usb_opening_width_mm": s["power_usb_opening_width"],
        "tray_checks_no_adhesive": result["checks"], "latch_locations": locations,
    }
    # Matching local wall coupon and a strip of the bezel carrying one latch.
    coupon_base = box(-s["root_length"] - 2, -tray_p["wall_thickness"], 0,
                      s["flexure_length"] + s["root_length"] + 4,
                      tray_p["wall_thickness"] + 2, tray_p["floor_thickness"], App, Part)
    coupon_wall = box(-s["root_length"] - 2, -tray_p["wall_thickness"], 0,
                      s["flexure_length"] + s["root_length"] + 4,
                      tray_p["wall_thickness"], base_top, App, Part)
    coupon_base = coupon_base.fuse(coupon_wall).cut(pocket).removeSplitter()
    coupon_top = box(-s["root_length"] - 2, -tray_p["wall_thickness"], lip_z,
                     s["flexure_length"] + s["root_length"] + 4,
                     tray_p["wall_thickness"] + s["skirt_clearance"] + s["skirt_thickness"],
                     s["bezel_thickness"], App, Part).cut(slot)
    coupon_stop = box(-s["root_length"] - 2, -tray_p["wall_thickness"], base_top,
                      s["flexure_length"] + s["root_length"] + 4,
                      tray_p["wall_thickness"] + s["skirt_clearance"] - s["flexure_gap"],
                      lip_z - base_top, App, Part)
    coupon_top = coupon_top.multiFuse([coupon_stop, latch]).removeSplitter()
    no_collision(coupon_base, coupon_top, "Desk coupon assembly")
    return {"bottom": base, "top": bezel, "pcb": result["pcb"],
            "old_tray": result["tray"], "old_tray_height": base_top,
            "outline": original, "shift": shift, "locations": locations,
            "coupon_bottom": coupon_base, "coupon_top": coupon_top, "checks": checks}


def travel_latch(t, seam, App, Part):
    gap, thick = t["clip_clearance"], t["clip_thickness"]
    bottom = seam - t["clip_overlap"]
    root_z = bottom + t["clip_length"]
    width = t["clip_width"]
    beam = box(-width / 2, gap, bottom, width, thick, t["clip_length"] + t["clip_root_height"], App, Part)
    root = box(-width / 2, -0.6, root_z, width,
               0.6 + gap + thick, t["clip_root_height"], App, Part)
    hook = wedge(-width / 2, width,
                 [(gap + 0.05, bottom), (gap, bottom),
                  (gap - t["clip_hook_projection"], bottom + t["clip_hook_projection"]),
                  (gap - t["clip_hook_projection"], bottom + t["clip_hook_height"]),
                  (gap + 0.05, bottom + t["clip_hook_height"])], App, Part)
    c = t["catch_clearance"]
    pocket = box(-width / 2 - c, gap - t["clip_hook_projection"] - c, bottom - c,
                 width + 2 * c, t["clip_hook_projection"] + c + 0.1,
                 t["clip_hook_height"] + 2 * c, App, Part)
    return beam.multiFuse([root, hook]).removeSplitter(), pocket


def build_travel_cap(t, width, depth, seam, locations, App, Part):
    """Build a shallow snap cap that mates with the existing travel base."""
    clearance = t["clip_clearance"]
    skirt_thickness = t["wall_thickness"]
    cap_height = t["tongue_height"]
    plate_thickness = t["clip_root_height"]
    cap_z = seam + cap_height
    wall_width = width + 2 * t["wall_thickness"]
    wall_depth = depth + 2 * t["wall_thickness"]
    wall_radius = t["corner_radius"] + t["wall_thickness"]

    skirt_inner = rounded_face(wall_width + 2 * clearance,
                                wall_depth + 2 * clearance,
                                wall_radius + clearance, App, Part)
    skirt_outer = rounded_face(wall_width + 2 * (clearance + skirt_thickness),
                                wall_depth + 2 * (clearance + skirt_thickness),
                                wall_radius + clearance + skirt_thickness, App, Part)
    cap = prism(skirt_outer, cap_z, plate_thickness, App)
    cap = cap.fuse(prism(skirt_outer.cut(skirt_inner), seam, cap_height, App))

    # Reuse the base's catch pockets, but shorten/thin the cantilevers so they
    # root directly into the flat plate.  The 8 mm beam stays within the same
    # estimated 1.2% strain limit as the taller carrier lid's clips.
    cap_latch_params = dict(t, clip_length=t["clip_overlap"] + cap_height,
                            clip_thickness=CAP_CLIP_THICKNESS_MM)
    latch, _ = travel_latch(cap_latch_params, seam, App, Part)
    # Clear the whole beam from the skirt up to the roof/root plane. Without
    # this cut the skirt shortens the free cantilever from 8 to 5 mm.
    relief = box(-t["clip_width"] / 2 - 0.6, clearance - 0.1, seam - 0.1,
                 t["clip_width"] + 1.2, skirt_thickness + 0.2,
                 cap_height + 0.1, App, Part)
    for location in locations:
        cap = cap.cut(local(relief, location["anchor"], location["tangent"], App))
        cap = cap.fuse(local(latch, location["anchor"], location["tangent"], App))
    cap = cap.removeSplitter()
    require_solid(cap, "Travel flat cap")

    # Matching one-latch test pieces.  The base coupon includes a short
    # locating tongue; the cap coupon includes its shallow skirt and flat roof.
    coupon_x = -t["clip_width"] / 2 - 3
    coupon_width = t["clip_width"] + 6
    coupon_base = box(coupon_x, -t["wall_thickness"], seam - t["clip_overlap"] - 2,
                      coupon_width, t["wall_thickness"],
                      t["clip_overlap"] + 2, App, Part)
    coupon_tongue = box(coupon_x,
                        -t["wall_thickness"] - t["tongue_clearance"] - t["tongue_thickness"],
                        seam - t["ledge_thickness"], coupon_width, t["tongue_thickness"],
                        cap_height + t["ledge_thickness"], App, Part)
    coupon_shoulder = box(coupon_x,
                          -t["wall_thickness"] - t["tongue_clearance"],
                          seam - t["ledge_thickness"], coupon_width,
                          t["tongue_clearance"], t["ledge_thickness"],
                          App, Part)
    _, pocket = travel_latch(t, seam, App, Part)
    coupon_base = (coupon_base.fuse(coupon_shoulder).fuse(coupon_tongue)
                   .cut(pocket).removeSplitter())

    cap_skirt = box(coupon_x, clearance, seam, coupon_width, skirt_thickness, cap_height,
                    App, Part)
    cap_plate = box(coupon_x,
                    -t["wall_thickness"] - t["tongue_clearance"] - t["tongue_thickness"],
                    cap_z, coupon_width,
                    t["wall_thickness"] + 2 * t["tongue_clearance"]
                    + t["tongue_thickness"] + skirt_thickness,
                    plate_thickness, App, Part)
    coupon_latch, _ = travel_latch(cap_latch_params, seam, App, Part)
    coupon_top = cap_skirt.cut(relief).fuse(cap_plate).fuse(coupon_latch).removeSplitter()
    require_solid(coupon_base, "Travel flat-cap coupon bottom")
    require_solid(coupon_top, "Travel flat-cap coupon top")

    checks = {
        "coupon_intersection_mm3": no_collision(
            coupon_base, coupon_top, "Travel flat-cap coupon assembly"),
        "clip_length_mm": cap_latch_params["clip_length"],
        "clip_thickness_mm": cap_latch_params["clip_thickness"],
        "estimated_flexure_strain_percent": 150 * cap_latch_params["clip_thickness"] *
            (t["clip_hook_projection"] - clearance + 0.1) /
            cap_latch_params["clip_length"] ** 2,
    }
    return cap, coupon_base, coupon_top, checks


def build_power_switch_tool(App, Part):
    """A handheld fork-tip pusher for the low-profile Alps slide switch."""
    handle = box(0, -4, 0, 30, 8, 2.4, App, Part)
    stem = box(28, -1.2, 0, 18, 2.4, 1.6, App, Part)
    fork = box(44, -2.5, 0, 5, 5, 1.6, App, Part)
    # 1.4 mm opening clears the switch's nominal 1.1 mm actuator.  The slot is
    # open at the tip so the tool can be placed on and removed from the slider.
    slot = box(46, -0.7, -0.1, 4, 1.4, 1.8, App, Part)
    tool = handle.fuse([stem, fork]).cut(slot).removeSplitter()
    require_solid(tool, "Power-switch pusher")
    return tool


def build_power_switch_cap(App, Part, parameters=None):
    """A larger clip-on thumb cap for the nominal SSSS811101 actuator."""
    # Local X follows switch travel, +Y faces the USB connector, and +Z runs
    # from the socket opening to the flat thumb face.  Offset only the outer
    # shoe/pad toward -Y (the bottom shell); keep the proven socket and lip
    # centered on the actuator.  Install with the broader side toward the shell.
    p = parameters or json.loads((HERE / "enclosure_parameters.json").read_text())["switch_cap"]
    for name, value in p.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError(f"switch_cap.{name} must be finite and positive")
    if p["height"] < 2 or p["shell_offset"] > 0.6:
        raise ValueError("Switch cap needs a roof and adequate offset-side wall")
    shell_offset = -p["shell_offset"]
    shoe = box(-2.1, -2.1 + shell_offset, 0, 4.2, 4.2, 1.7, App, Part)
    button_face = rounded_face(6.0, 5.0, 0.8, App, Part)
    button = moved(prism(button_face, 1.4, p["height"] - 1.4, App), App.Vector(0, shell_offset, 0))
    cap = shoe.fuse(button)
    # Unchanged 3.4 x 1.5 mm cavity and narrower retaining mouth.
    sw, sd, mw, md = (p[k] for k in ("socket_width", "socket_depth", "mouth_width", "mouth_depth"))
    c = p["entry_chamfer"]
    if not (mw < sw < 3.6 and md < sd < 1.8 and c < 0.2):
        raise ValueError("Socket dimensions must preserve walls and retaining lip")
    socket = box(-sw / 2, -sd / 2, 0.25, sw, sd, 1.2, App, Part)
    mouth = box(-mw / 2, -md / 2, -0.01, mw, md, 0.27, App, Part)
    # Four tapered entrance faces ease insertion without enlarging the throat.
    for sign in (-1, 1):
        bevel = wedge(-mw / 2 - c, mw + 2 * c,
                      [(sign * md / 2, 0), (sign * (md / 2 + c), 0),
                       (sign * md / 2, c)], App, Part)
        mouth = mouth.fuse(bevel)
        bevel = wedge(-md / 2 - c, md + 2 * c,
                      [(sign * mw / 2, 0), (sign * (mw / 2 + c), 0),
                       (sign * mw / 2, c)], App, Part)
        bevel.rotate(App.Vector(), App.Vector(0, 0, 1), 90)
        mouth = mouth.fuse(bevel)
    cap = cap.cut(socket.fuse(mouth)).removeSplitter()
    # Recessed orientation mark on the broad shell-facing edge, off the bed face.
    cap = cap.cut(box(-0.4, -2.6, 0, 0.8, 0.3, 0.3, App, Part)).removeSplitter()
    require_solid(cap, "Clip-on power-switch cap")
    bounds = cap.BoundBox
    if bounds.XLength >= 14 or bounds.YLength >= 14:
        raise ValueError("Power-switch cap exceeds the existing access opening")
    return cap


def build_travel(board, tray_p, s, t, desk, App, Part):
    combined = Part.makeCompound([desk["bottom"], desk["top"]]).BoundBox
    center = App.Vector((combined.XMin + combined.XMax) / 2,
                        (combined.YMin + combined.YMax) / 2, 0)
    width = combined.XLength + 2 * (t["lateral_clearance"] + t["side_foam"])
    depth = combined.YLength + 2 * (t["lateral_clearance"] + t["side_foam"])
    wall, floor, radius = t["wall_thickness"], t["floor_thickness"], t["corner_radius"]
    outer = rounded_face(width + 2 * wall, depth + 2 * wall, radius + wall, App, Part)
    inner = rounded_face(width, depth, radius, App, Part)
    # Both halves are referenced from their foot-bottom planes, not keycaps.
    lower_foot = floor + t["key_clearance"] + t["keyboard_height"]
    divider_z = lower_foot + t["divider_foam"]
    seam = divider_z + t["divider_thickness"]
    upper_foot = seam + t["divider_foam"]
    roof_z = upper_foot + t["keyboard_height"] + t["key_clearance"]
    total_height = roof_z + floor
    lower_back = lower_foot - t["feet_height"]
    upper_back = upper_foot + t["feet_height"]
    base = prism(outer, 0, floor, App).fuse(prism(outer.cut(inner), floor, seam - floor, App))
    lid = prism(outer.cut(inner), seam, roof_z - seam, App).fuse(prism(outer, roof_z, floor, App))
    inset = t["tongue_clearance"] + t["tongue_thickness"]
    tongue_outer = rounded_face(width - 2 * t["tongue_clearance"], depth - 2 * t["tongue_clearance"],
                                radius - t["tongue_clearance"], App, Part)
    tongue_inner = rounded_face(width - 2 * inset, depth - 2 * inset, radius - inset, App, Part)
    ledge_inner = rounded_face(width - 2 * t["ledge_width"], depth - 2 * t["ledge_width"],
                               radius - t["ledge_width"], App, Part)
    ledge = prism(inner.cut(ledge_inner), divider_z - t["ledge_thickness"], t["ledge_thickness"], App)
    # A stepped <=45-degree underside avoids a 3 mm unsupported shelf.
    ramps = []
    steps = math.ceil(t["ledge_width"] / 0.2)
    step_height = t["ledge_width"] / steps
    for step in range(steps):
        reach = (step + 1) * step_height
        ramp_inner = rounded_face(width - 2 * reach, depth - 2 * reach,
                                  radius - reach, App, Part)
        ramps.append(prism(inner.cut(ramp_inner), divider_z - t["ledge_thickness"] - t["ledge_width"]
                           + step * step_height, step_height, App))
    ledge = ledge.multiFuse(ramps)
    # This shoulder connects the inward-offset tongue to the base wall.
    shoulder = prism(inner.cut(tongue_inner), divider_z - t["ledge_thickness"],
                     seam - divider_z + t["ledge_thickness"], App)
    tongue = prism(tongue_outer.cut(tongue_inner), seam, t["tongue_height"], App)
    base = base.multiFuse([ledge, shoulder, tongue])
    # An asymmetric pin/hole indexes the lower cradle so its four bearings
    # cannot accidentally be rotated to the wrong PCB edges.
    pin_center = App.Vector(width / 2 - radius, depth / 2 - radius, floor)
    pin = Part.makeCylinder(1.2, t["cradle_floor"], pin_center)
    base = base.fuse(pin)
    divider_inset = inset + t["divider_clearance"]
    divider_face = rounded_face(width - 2 * divider_inset, depth - 2 * divider_inset,
                               radius - divider_inset, App, Part)
    divider = prism(divider_face, divider_z, t["divider_thickness"], App)
    # Two lifting holes, outside the keyboard's bounding rectangle.
    # A small edge scallop is safer than placing a finger hole under its feet.
    hole = Part.makeCylinder(4, t["divider_thickness"] + 2,
                             App.Vector(0, depth / 2 - divider_inset, divider_z - 1))
    divider = divider.cut(hole).removeSplitter()
    latch, pocket = travel_latch(t, seam, App, Part)
    locations = []
    for sign in (-1, 1):
        for x in (-width / 4, width / 4):
            # Tangents are chosen so local +Y is outward on each long side.
            anchor = [x, sign * (depth / 2 + wall)]
            tangent = [sign, 0]
            locations.append({"anchor": anchor, "tangent": tangent})
            lid = lid.fuse(local(latch, anchor, tangent, App))
            base = base.cut(local(pocket, anchor, tangent, App))
    base, lid = base.removeSplitter(), lid.removeSplitter()
    keys = component_envelopes(board, s, floor + t["key_clearance"],
                               lower_back - floor - t["key_clearance"], desk["shift"],
                               App, Part, keys=True, travel=t)
    keys.translate(-center)
    keys = keys.mirror(App.Vector(), App.Vector(1, 0, 0))
    cradles, contacts, contact_probes = {}, {}, {}
    for name, rim_height in (("trays", desk["old_tray_height"]), ("snap", desk["top"].BoundBox.ZMax)):
        # A thin floor connects four outward-flared towers. They only bear on
        # fixed wall material; the spaces occupied by keys/electronics are cut.
        plate_face = rounded_face(width - 1.0, depth - 1.0, radius - 0.5, App, Part)
        plate = prism(plate_face, floor, t["cradle_floor"], App)
        index_hole = Part.makeCylinder(1.4, t["cradle_floor"] + 2,
                                        pin_center - App.Vector(0, 0, 1))
        plate = plate.cut(index_hole)
        contact_z = lower_back - rim_height - t["cradle_pad"]
        if contact_z <= floor + t["cradle_floor"] + 2:
            raise ValueError("Cradle towers are too short; increase keyboard_height")
        towers, contact_checks, probes = [], [], []
        for loc in desk["locations"]:
            tangent = loc["tangent"]
            midpoint = App.Vector(*loc["midpoint"], 0)
            normal = App.Vector(-tangent[1], tangent[0], 0)
            anchor = midpoint + normal * (tray_p["pcb_clearance"] + 2 * tray_p["outline_chord_error"] + tray_p["wall_thickness"])
            v_inner = -t["cradle_wall_inset"] - t["cradle_contact_width"]
            v_outer = -t["cradle_wall_inset"]
            half = t["cradle_contact_length"] / 2
            # A sloped outside braces the tall, narrow bearing surface.
            tower = wedge(-half, 2 * half,
                          [(v_inner, floor), (v_inner + t["cradle_outer_width"], floor),
                           (v_outer, contact_z), (v_inner, contact_z)], App, Part)
            tower = local(tower, [anchor.x, anchor.y], tangent, App)
            tower.translate(-center)
            tower = tower.mirror(App.Vector(), App.Vector(1, 0, 0)).cut(keys)
            require_solid(tower, f"{name} cradle tower")
            pad = box(-half, v_inner, contact_z, 2 * half, v_outer - v_inner, t["cradle_pad"], App, Part)
            pad = local(pad, [anchor.x, anchor.y], tangent, App)
            pad.translate(-center)
            pad = pad.mirror(App.Vector(), App.Vector(1, 0, 0))
            no_collision(pad, keys, "Cradle pad / key or controller envelope")
            probes.append(moved(pad, App.Vector(0, 0, t["cradle_pad"])))
            towers.append(tower)
            contact_checks.append({"size_mm": [2 * half, v_outer - v_inner, t["cradle_pad"]],
                                   "center_xy_mm": [pad.CenterOfMass.x, pad.CenterOfMass.y],
                                   "top_z_mm": contact_z + t["cradle_pad"]})
        cradle = plate.multiFuse(towers).removeSplitter()
        require_solid(cradle, f"{name} cradle")
        no_collision(cradle, keys, f"{name} cradle / populated envelope")
        cradles[name] = cradle
        contacts[name] = contact_checks
        contact_probes[name] = probes
    for label, shape in (("Travel base", base), ("Travel lid", lid), ("Divider", divider)):
        require_solid(shape, label)
    shell = base.fuse(lid)
    upper_keys = moved(keys, App.Vector(0, 0, upper_foot + t["keyboard_height"] - lower_back))
    checks = {
        "base_lid_intersection_mm3": no_collision(base, lid, "Travel shell assembly"),
        "base_divider_intersection_mm3": no_collision(base, divider, "Base / divider"),
        "lid_divider_intersection_mm3": no_collision(lid, divider, "Lid / divider"),
        "lower_populated_envelope_shell_intersection_mm3": no_collision(keys, shell, "Lower keys / shell"),
        "upper_populated_envelope_shell_intersection_mm3": no_collision(upper_keys, shell, "Upper keys / shell"),
        "inner_width_depth_mm": [width, depth], "closed_height_mm": total_height,
        "keyboard_height_allowance_each_mm": t["keyboard_height"],
        "feet_height_assumption_mm": t["feet_height"],
        "key_to_shell_allowance_each_mm": t["key_clearance"],
        "minimum_key_to_cradle_floor_mm": t["key_clearance"] - t["cradle_floor"],
        "divider_bottom_z_mm": divider_z, "seam_z_mm": seam,
        "lower_case_back_z_mm": lower_back, "upper_case_back_z_mm": upper_back,
        "snap_count": len(locations),
        "hook_wall_engagement_mm": t["clip_hook_projection"] - t["clip_clearance"],
        "estimated_flexure_strain_percent": 150 * t["clip_thickness"] *
            (t["clip_hook_projection"] - t["clip_clearance"] + 0.1) / t["clip_length"] ** 2,
        "cradle_contacts": contacts, "compatibility": {},
        "cradle_index_pin_xy_mm": [pin_center.x, pin_center.y],
    }
    references = {}
    for name, shape in (("trays", desk["old_tray"]), ("snap", desk["bottom"].fuse(desk["top"]))):
        centered = moved(shape, -center)
        lower = centered.copy()
        lower.rotate(App.Vector(), App.Vector(0, 1, 0), 180)
        lower.translate(App.Vector(0, 0, lower_back))
        upper = centered.mirror(App.Vector(), App.Vector(1, 0, 0))
        upper.translate(App.Vector(0, 0, upper_back))
        # Reject both wall collisions and corner clipping of the bounding box.
        bearing_ratios = []
        for probe in contact_probes[name]:
            # Check the whole bearing footprint, not merely its center. The
            # thin slab lies immediately inside the inverted case's rim.
            slab = probe.common(box(-width, -depth, probe.BoundBox.ZMin,
                                     2 * width, 2 * depth, 0.01, App, Part))
            ratio = lower.common(slab).Volume / slab.Volume
            if ratio < 0.98:
                raise ValueError(f"{name}: cradle bearing is only {ratio:.1%} supported")
            bearing_ratios.append(ratio)
        checks["compatibility"][name] = {
            "bearing_footprint_supported_fractions": bearing_ratios,
            "lower_case_shell_intersection_mm3": no_collision(lower, shell, f"{name} lower / shell"),
            "upper_case_shell_intersection_mm3": no_collision(upper, shell, f"{name} upper / shell"),
            "lower_case_cradle_intersection_mm3": no_collision(lower, cradles[name], f"{name} / cradle"),
            "upper_case_divider_intersection_mm3": no_collision(upper, divider, f"{name} / divider"),
            "lower_case_divider_intersection_mm3": no_collision(lower, divider, f"{name} lower / divider"),
            "cradle_shell_intersection_mm3": no_collision(cradles[name], base, f"{name} cradle / base"),
        }
        references[f"{name}_lower"] = lower
        references[f"{name}_upper"] = upper
    # Full-height travel coupon avoids shortening the beam (which changes fit).
    coupon_base = box(-t["clip_width"] / 2 - 3, -wall, seam - t["clip_overlap"] - 2,
                      t["clip_width"] + 6, wall, t["clip_overlap"] + 2, App, Part).cut(pocket)
    coupon_lid_wall = box(-t["clip_width"] / 2 - 3, -wall, seam,
                          t["clip_width"] + 6, wall,
                          t["clip_length"] - t["clip_overlap"] + t["clip_root_height"], App, Part)
    coupon_lid = coupon_lid_wall.fuse(latch).removeSplitter()
    no_collision(coupon_base, coupon_lid, "Travel coupon assembly")
    cap, cap_coupon_bottom, cap_coupon_top, cap_checks = build_travel_cap(
        t, width, depth, seam, locations, App, Part)
    cap_checks["base_cap_intersection_mm3"] = no_collision(
        base, cap, "Travel base / flat cap")
    return {"base": base, "lid": lid, "divider": divider, "cradle_trays": cradles["trays"],
            "cradle_snap": cradles["snap"], "coupon_bottom": coupon_base,
            "coupon_top": coupon_lid, "flat_cap": cap,
            "cap_coupon_bottom": cap_coupon_bottom, "cap_coupon_top": cap_coupon_top,
            "cap_checks": cap_checks, "references": references, "checks": checks}


def print_orientation(shape, face_down, App):
    result = shape.copy()
    if face_down:
        result.rotate(App.Vector(), App.Vector(1, 0, 0), 180)
    bounds = result.BoundBox
    result.translate(App.Vector(-bounds.XMin, -bounds.YMin, -bounds.ZMin))
    return result


def save_document(desk, travel, board, p, output, App, Part):
    doc = App.newDocument("YellowjacketEnclosures")
    doc.Label = "Yellowjacket V2 - snap cases, carrier and switch accessories"
    for name, result, offset in (("Desk", desk, App.Vector()), ("Travel", travel, App.Vector(220, 65, 0))):
        group = doc.addObject("App::DocumentObjectGroup", name)
        keys = (("bottom", "top", "pcb") if name == "Desk" else
                ("base", "lid", "flat_cap", "divider", "cradle_trays", "cradle_snap"))
        for key in keys:
            obj = doc.addObject("Part::Feature", f"{name}{key.title().replace('_', '')}")
            obj.Label = f"{name}: {key.replace('_', ' ')}" + (" (reference only)" if key == "pcb" else "")
            obj.Shape = moved(result[key], offset)
            group.addObject(obj)
            if obj.ViewObject:
                obj.ViewObject.Visibility = key not in ("lid", "flat_cap", "cradle_snap")
        if name == "Desk":
            center = (desk["bottom"].BoundBox.XMin + desk["bottom"].BoundBox.XMax) / 2
            for key in ("bottom", "top", "pcb"):
                obj = doc.addObject("Part::Feature", f"Right{key.title()}")
                obj.Label = f"Right: {key}" + (" (reference only)" if key == "pcb" else "")
                obj.Shape = moved(desk[key].mirror(App.Vector(center, 0, 0), App.Vector(1, 0, 0)),
                                  App.Vector(0, 110, 0))
                group.addObject(obj)
        else:
            references = doc.addObject("App::DocumentObjectGroup", "CarrierCaseReferences")
            references.Label = "Carrier: case bodies only - references, not populated keyboards"
            group.addObject(references)
            for key, shape in travel["references"].items():
                obj = doc.addObject("Part::Feature", f"Reference{key.title().replace('_', '')}")
                obj.Label = key.replace("_", " ") + " case body (reference only)"
                obj.Shape = moved(shape, offset)
                references.addObject(obj)
                if obj.ViewObject:
                    obj.ViewObject.Visibility = False
    source = doc.addObject("App::FeaturePython", "GeneratorInputs")
    source.addProperty("App::PropertyString", "ParametersJSON", "Source")
    source.ParametersJSON = json.dumps(p, sort_keys=True)
    source.setEditorMode("ParametersJSON", 1)
    source.addProperty("App::PropertyString", "SourceCommit", "Source")
    source.SourceCommit = board["source"]["commit"]
    switch_tool = doc.addObject("Part::Feature", "PowerSwitchTool")
    switch_tool.Label = "Handheld power-switch pusher (accessory)"
    switch_tool.Shape = build_power_switch_tool(App, Part)
    if switch_tool.ViewObject:
        switch_tool.ViewObject.Visibility = False
    switch_cap = doc.addObject("Part::Feature", "PowerSwitchCap")
    switch_cap.Label = "Clip-on enlarged power-switch actuator (first fit)"
    switch_cap.Shape = build_power_switch_cap(App, Part, p["switch_cap"])
    if switch_cap.ViewObject:
        switch_cap.ViewObject.Visibility = False
    doc.recompute()
    doc.saveAs(str(output / "yellowjacket-enclosures.FCStd"))
    App.closeDocument(doc.Name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parameters", type=Path, default=HERE / "enclosure_parameters.json")
    parser.add_argument("--tray-parameters", type=Path, default=HERE / "parameters.json")
    parser.add_argument("--output", type=Path, default=HERE / "v2")
    parser.add_argument("--freecad-lib", type=Path)
    args = parser.parse_args()
    board = json.loads((HERE / "board.json").read_text())
    tray_p = json.loads(args.tray_parameters.read_text())
    p = json.loads(args.parameters.read_text())
    check_parameters(tray_p, board)
    check_enclosure_parameters(p, tray_p, board)
    App, Part, Mesh, MeshPart = load_freecad(args.freecad_lib)
    print("Building screwless PCB-capturing snap case...", flush=True)
    desk = build_snap(board, tray_p, p["snap"], App, Part)
    print("Building stacked carrier and rim-supporting cradles...", flush=True)
    travel = build_travel(board, tray_p, p["snap"], p["travel"], desk, App, Part)
    shapes = {}
    for side in ("left", "right"):
        for key in ("bottom", "top"):
            shape = desk[key]
            if side == "right":
                shape = shape.mirror(App.Vector(desk["bottom"].BoundBox.XLength / 2, 0, 0), App.Vector(1, 0, 0))
            shapes[f"snap-{side}-{key}"] = (shape, key == "top")
    shapes.update({f"travel-{key.replace('_', '-')}": (travel[key], key == "lid")
                   for key in ("base", "lid", "divider", "cradle_trays", "cradle_snap")})
    shapes["travel-cap"] = (travel["flat_cap"], True)
    for family, result in (("snap", desk), ("travel", travel)):
        shapes[f"{family}-coupon-bottom"] = (result["coupon_bottom"], False)
        shapes[f"{family}-coupon-top"] = (result["coupon_top"], True)
    shapes["travel-cap-coupon-bottom"] = (travel["cap_coupon_bottom"], False)
    shapes["travel-cap-coupon-top"] = (travel["cap_coupon_top"], True)
    shapes["power-switch-tool"] = (build_power_switch_tool(App, Part), False)
    shapes["power-switch-cap"] = (build_power_switch_cap(App, Part, p["switch_cap"]), True)
    args.output.mkdir(parents=True, exist_ok=True)
    report = {"revision": "v2", "source": board["source"], "freecad_version": App.Version(), "parameters_mm": p,
              "tray_parameters_mm": tray_p, "snap_checks": desk["checks"],
              "travel_checks": travel["checks"], "travel_cap_checks": travel["cap_checks"],
              "artifacts": {},
              "status": "V2 prototype: geometry checked; physical fit and durability untested.",
              "fit_evidence": {
                  "photos": ["reference_pics/20261108_155634.jpg", "reference_pics/20261108_155647.jpg",
                             "reference_pics/20261108_155658.jpg"],
                  "switch_socket": "User confirmed V1 fit; throat and cavity retained with entry bevel",
                  "switch_usb_swept_clearance": "Pending measured switch/controller location and USB plug envelope",
                  "two_halves_under_flat_cap": "Pending packing photo and stack dimensions",
                  "switch_cap_guides_and_stops": "Not implemented; cap remains actuator-mounted"
              }}
    for name, (shape, face_down) in shapes.items():
        printable = print_orientation(shape, face_down, App)
        filename = f"yellowjacket-{name}.stl"
        _, checks = export_verified(printable, args.output / filename, p["travel"], Mesh, MeshPart)
        checks["orientation"] = "outer/top face on bed" if face_down else "flat underside on bed"
        report["artifacts"][filename] = checks
        printable.exportStep(str(args.output / f"yellowjacket-{name}.step"))
        print(f"Verified {filename}: {checks['size_mm']}", flush=True)
    save_document(desk, travel, board, p, args.output, App, Part)
    from preview_enclosures import preview
    preview(desk, travel, args.output / "preview.png", App, MeshPart)
    (args.output / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Done: {args.output}", flush=True)


if __name__ == "__main__":
    main()
