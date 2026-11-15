#!/usr/bin/env python3
"""Separate retainer-to-base brace. Existing enclosure files are read-only."""
import hashlib
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
CASE = HERE.parent
sys.path.insert(0, str(CASE.parent / "yellowjacket"))
from generate import load_freecad, export_verified


def main():
    original_files = [f for f in CASE.rglob("*") if f.is_file() and
                      HERE not in f.parents and "__pycache__" not in f.parts]
    before = {str(f.relative_to(CASE)): hashlib.sha256(f.read_bytes()).hexdigest()
              for f in original_files}
    p = json.loads((CASE / "parameters.json").read_text())
    b = json.loads((HERE / "parameters.json").read_text())
    A, P, M, MP = load_freecad()
    V = A.Vector
    out = HERE / "output"
    out.mkdir(exist_ok=True)
    # Read the shipped assembly rather than regenerating any existing part.
    source = A.openDocument(str(CASE / "output/pinchwing-dongle.FCStd"))
    original = {o.Name: o.Shape.copy() for o in source.Objects if hasattr(o, "Shape")}
    A.closeDocument(source.Name)
    base, shell, retainer = (original[n] for n in ("Bottom18_3", "Housing", "DisplayRetainer"))
    floor, wall = p["base_thickness"], p["wall"]
    angle = math.radians(p["display_angle"])
    depth = p["display_seat_depth"] + p["display_pcb_thickness"] + 0.2 + 2.4 + b["retainer_gap"]

    def display_point(x, v, t):
        return V(x, p["display_center_y"] + v*math.cos(angle) + t*math.sin(angle),
                 p["display_center_z"] + v*math.sin(angle) - t*math.cos(angle))

    def rounded(w, d, r, y, z):
        x = -w/2
        q = [V(a, c, z) for a, c in [
            (x+r,y), (x+w-r,y), (x+w,y+r), (x+w,y+d-r),
            (x+w-r,y+d), (x+r,y+d), (x,y+d-r), (x,y+r)]]
        k = math.sqrt(0.5)
        mid = [V(x+w-r+r*k,y+r-r*k,z), V(x+w-r+r*k,y+d-r+r*k,z),
               V(x+r-r*k,y+d-r+r*k,z), V(x+r-r*k,y+r-r*k,z)]
        edges = []
        for i in range(4):
            edges += [P.makeLine(q[2*i],q[2*i+1]),
                      P.Arc(q[2*i+1],mid[i],q[(2*i+2)%8]).toShape()]
        return P.Wire(edges)

    plates = []
    for sign in (-1, 1):
        x = sign*b["side_center_x"] - b["side_thickness"]/2
        low = display_point(x, -b["retainer_contact_half_height"], depth)
        high = display_point(x, b["retainer_contact_half_height"], depth)
        # Solid triangular gussets rise directly from their feet: no floating
        # arms or internal bridges in the exported floor-down orientation.
        points = [V(x,low.y,floor), V(x,p["body_depth"],floor),
                  V(x,p["body_depth"],floor+b["rear_foot_height"]), high, low]
        plates.append(P.Face(P.makePolygon(points+[points[0]])).extrude(V(b["side_thickness"],0,0)))
    crossbar = P.makeBox(2*b["side_center_x"]+b["side_thickness"],
                        b["crossbar_depth"],b["crossbar_height"],
                        V(-b["side_center_x"]-b["side_thickness"]/2,
                          b["crossbar_front_y"],floor))
    brace = plates[0].multiFuse([plates[1],crossbar]).removeSplitter()
    # The rear toes nest just inside the existing raised base lip. It stops
    # backward sliding under pressure on the screen; no glue or screws.
    gap = b["base_lip_clearance"]
    footprint = P.Face(rounded(p["body_width"]-2*wall-3-2*gap,
                              p["body_depth"]-2*wall-3-2*gap,4.1-gap,
                              wall+1.5+gap,floor)).extrude(V(0,0,100))
    brace = brace.common(footprint).removeSplitter()

    intersections = {name: brace.common(shape).Volume for name,shape in original.items()}
    assert max(intersections.values()) < 0.02, intersections
    # Hardware components above the bare nice!nano PCB are not in the source
    # assembly. A conservative full-board box checks the brace avoids them.
    nano_top = P.makeBox(p["nano_width"],p["nano_length"],5,
                        V(-p["nano_width"]/2,p["nano_rear_y"]-p["nano_length"],
                          p["nano_pcb_underside_z"]))
    assert brace.common(nano_top).Volume < 0.02
    contact_distance = brace.distToShape(retainer)[0]
    assert contact_distance <= b["retainer_gap"]+0.01, contact_distance
    assert brace.distToShape(base)[0] < 0.01
    # A small rearward displacement must hit the lip, proving there is a
    # positive load stop instead of relying on friction against the floor.
    shifted = brace.copy()
    shifted.translate(V(0,0.4,0))
    stop_overlap = shifted.common(base).Volume
    assert stop_overlap > 0.02, stop_overlap
    # Each pad meets the back plane of the retainer, rather than its glass.
    contact_probe = brace.copy()
    contact_probe.translate(V(0,-math.sin(angle)*0.02,math.cos(angle)*0.02))
    contact_area = contact_probe.common(retainer).Volume/0.02
    assert contact_area > 20, contact_area

    printed = brace.copy()
    printed.translate(V(0,0,-floor))
    _, checks = export_verified(printed,out/"display-brace.stl",p,M,MP)
    printed.exportStep(str(out/"display-brace.step"))
    P.makeCompound([brace,base,shell,retainer]).exportStep(str(out/"brace-assembly.step"))
    for path in out.glob("*.step"):
        path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines())+"\n")
    for name,shape in {"Brace":brace,**original}.items():
        shape.exportBrep(str(out/(name+".brep")))
    after = {str(f.relative_to(CASE)): hashlib.sha256(f.read_bytes()).hexdigest()
             for f in original_files}
    assert before == after, "Existing enclosure files changed"
    report = {
        "brace_parameters":b,
        "source_assembly_sha256":before["output/pinchwing-dongle.FCStd"],
        "original_files_unchanged":True,
        "print":checks,
        "intersections_mm3":intersections,
        "nano_component_clearance_intersection_mm3":brace.common(nano_top).Volume,
        "retainer_distance_mm":contact_distance,
        "retainer_contact_area_from_0_02_mm_probe_mm2":contact_area,
        "rear_stop_overlap_after_0_4_mm_displacement_mm3":stop_overlap,
        "retainer_pcb_nominal_gap_mm":0.2,
        "physical_fit_verified":False,
    }
    (out/"validation.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    main()
