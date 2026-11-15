#!/usr/bin/env python3
"""Add-on MCU keeper and captive recessed USB mask; existing CAD is read-only."""
import hashlib
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
CASE = HERE.parent
sys.path.insert(0,str(CASE.parent/"yellowjacket"))
from generate import load_freecad, export_verified


def main():
    p = json.loads((CASE/"parameters.json").read_text())
    q = json.loads((HERE/"parameters.json").read_text())
    A,P,M,MP = load_freecad()
    V = A.Vector
    out = HERE/"output"
    out.mkdir(exist_ok=True)
    protected = list((CASE/"output").glob("*")) + list((CASE/"brace/output").glob("*"))
    protected = [f for f in protected if f.is_file()]
    before = {str(f.relative_to(CASE)):hashlib.sha256(f.read_bytes()).hexdigest()
              for f in protected}
    doc = A.openDocument(str(CASE/"output/pinchwing-dongle.FCStd"))
    originals = {o.Name:o.Shape.copy() for o in doc.Objects if hasattr(o,"Shape")}
    A.closeDocument(doc.Name)
    # Identify the brace in its committed assembly by the validated volume
    # and width, rather than relying on STEP child order or ignored BREPs.
    brace_assembly = P.read(str(CASE/"brace/output/brace-assembly.step"))
    expected = json.loads((CASE/"brace/output/validation.json").read_text())["print"]
    candidates = [s for s in brace_assembly.Solids
                  if abs(s.Volume-expected["volume_mm3"])<1 and
                  abs(s.BoundBox.XLength-expected["size_mm"][0])<0.01]
    assert len(candidates)==1, "Cannot identify the existing display brace"
    brace = candidates[0]
    originals["DisplayBrace"] = brace
    base, shell, pcb = (originals[n] for n in ("Bottom18_3","Housing","NanoPCB"))
    z, rear, half = p["nano_pcb_underside_z"],p["nano_rear_y"],p["nano_width"]/2
    front = rear-p["nano_length"]
    gap = q["fit_clearance"]
    rail_top = z+3.2
    cap_z = rail_top+gap
    cap_top = cap_z+q["keeper_top_thickness"]
    outer, inner = q["keeper_outer_x"],q["keeper_side_inner_x"]

    def box(x,y,z,w,d,h):
        return P.makeBox(w,d,h,V(x,y,z))

    def fuse(shapes):
        return shapes[0].multiFuse(shapes[1:]).removeSplitter()

    def both(shape):
        # Reflect in the center plane; every keeper feature is symmetric.
        mat = A.Matrix()
        mat.A11 = -1
        return [shape,shape.transformGeometry(mat)]

    def section(w,h,r,y,center_z):
        x, zz = -w/2,center_z-h/2
        points = [(x+r,zz),(x+w-r,zz),(x+w,zz+r),(x+w,zz+h-r),
                  (x+w-r,zz+h),(x+r,zz+h),(x,zz+h-r),(x,zz+r)]
        verts = [V(a,y,b) for a,b in points]
        k = math.sqrt(0.5)
        mid = [V(x+w-r+r*k,y,zz+r-r*k),V(x+w-r+r*k,y,zz+h-r+r*k),
               V(x+r-r*k,y,zz+h-r+r*k),V(x+r-r*k,y,zz+r-r*k)]
        edges = []
        for i in range(4):
            edges += [P.makeLine(verts[2*i],verts[2*i+1]),
                      P.Arc(verts[2*i+1],mid[i],verts[(2*i+2)%8]).toShape()]
        return P.Wire(edges)

    def tunnel(w,h,r,y,depth,center_z):
        return P.Face(section(w,h,r,y,center_z)).extrude(V(0,depth,0))

    # Long side members run OUTSIDE the existing cradle. The front roof
    # overlaps only the two bare PCB corners ahead of the first header row.
    parts = [box(-outer,front-1.5,cap_z,2*outer,1.35,q["keeper_top_thickness"])]
    one_side = [
        box(inner,front-1.5,cap_z,outer-inner,rear+0.25-(front-1.5),q["keeper_top_thickness"]),
        box(inner,front-1.5,q["front_latch_bottom_z"],outer-inner,3.2,
            cap_top-q["front_latch_bottom_z"]),
        box(half-0.6,front-1.5,z,0.6,1.35,cap_top-z),
        box(half-0.6,front-0.15,z+p["nano_pcb_thickness"]+gap,0.6,1.85,
            cap_top-(z+p["nano_pcb_thickness"]+gap)),
        box(half-0.6,front-0.15,cap_z,outer-(half-0.6),1.85,q["keeper_top_thickness"]),
        # Front latch is a long spring, anchored low and free at the hook.
        box(5.0,front-1.4,q["front_latch_bottom_z"],outer-5.0,1.0,1.4),
        box(5.0,front-1.4,q["front_latch_bottom_z"],2.0,q["front_latch_thickness"],
            z-1.35-q["front_latch_bottom_z"]),
    ]
    latch_pts = [V(5,front-0.45,z-2.75),V(5,front+0.8,z-1.35),
                 V(5,front-0.45,z-1.35)]
    one_side.append(P.Face(P.makePolygon(latch_pts+[latch_pts[0]])).extrude(V(2,0,0)))
    hx, hw = q["rear_hook_inner_x"],q["rear_hook_width"]
    hook_end = q["rear_hook_end_y"]
    one_side += [
        box(hx,rear-1.2,cap_z,outer-hx,1.45,q["keeper_top_thickness"]),
        box(hx,rear-0.7,cap_z,hw,hook_end-(rear-0.7),0.7),
        box(hx,rear+1.15,z-2.35,hw,hook_end-(rear+1.15),cap_z+0.7-(z-2.35)),
        box(hx,rear-0.7,z-2.35,hw,hook_end-(rear-0.7),1.0),
    ]
    for part in one_side:
        parts += both(part)
    keeper = fuse(parts)

    # Socket position was not measured; keep these inputs explicit.
    socket_z = z+q["socket_center_above_pcb_underside"]
    socket_face = rear+q["socket_face_offset_from_pcb_rear"]
    socket = tunnel(q["socket_width"],q["socket_height"],1.1,
                    socket_face-q["socket_length"],q["socket_length"],socket_z)
    metal = tunnel(q["cable_metal_width"],q["cable_metal_height"],1.0,
                   socket_face-q["cable_insertion_depth"],q["cable_metal_projection"],socket_z)
    body_front = socket_face-q["cable_insertion_depth"]+q["cable_metal_projection"]
    cable_body = tunnel(q["cable_body_width"],q["cable_body_height"],
                        q["cable_body_corner_radius"],body_front,18,socket_z)
    components = box(-8,front+1.8,z+p["nano_pcb_thickness"],16,
                     rear-q["socket_length"]-(front+1.8),4.0)
    # The thin port mask is NEXT TO the socket, not at the outer wall.
    # A full-size recess in front of it lets the molded cable body approach.
    bezel_y = socket_face+0.15
    hole_z = z+0.4
    clearance = q["bezel_outer_clearance"]
    tube = tunnel(p["usb_opening_width"]-2*clearance,
                  p["usb_opening_height"]-2*clearance,2-clearance,
                  bezel_y,p["body_depth"]-bezel_y,hole_z)
    # A wide inside frame stops the bezel pulling out through the old hole.
    # Rear keeper hooks form the opposing stop when both parts are installed.
    frame_y, frame_d = rear-1.0,1.2
    bezel = fuse([
        tube,
        box(-14.5,frame_y,z-6.2,29,frame_d,2.4),
        box(-14.5,frame_y,z+4.6,29,frame_d,2.0),
        box(-14.5,frame_y,z-6.2,1.5,frame_d,12.8),
        box(13.0,frame_y,z-6.2,1.5,frame_d,12.8),
    ])
    port = tunnel(q["bezel_port_width"],q["bezel_port_height"],1.3,
                  bezel_y-0.1,p["body_depth"]-bezel_y+0.2,socket_z)
    mouth = tunnel(q["bezel_mouth_width"],q["bezel_mouth_height"],1.5,
                   bezel_y+q["bezel_mask_thickness"],
                   p["body_depth"]-bezel_y+1,hole_z)
    bezel = bezel.cut(fuse([port,mouth]))
    # Clearance around original rear corner stops and the new keeper hooks.
    for part in [
        box(half+0.15-gap,rear-1.3,p["base_thickness"],
            1.65+2*gap,1.7,rail_top+gap-p["base_thickness"]),
        box(5.15,rear-0.15,z-1.35,6.0,1.5,4.7),
        box(hx-gap,rear-1.35,z-2.5,hw+2*gap,hook_end+gap-(rear-1.35),6.9),
        box(hx-gap,rear-1.35,cap_z-gap,outer-hx+2*gap,1.75,1.7),
    ]:
        for cut in both(part):
            bezel = bezel.cut(cut)
    bezel = bezel.removeSplitter()

    shapes = {"mcu-keeper":keeper,"usb-bezel":bezel}
    report = {
        "parameters":q,"source_assembly_sha256":before["output/pinchwing-dongle.FCStd"],
        "assumptions":["18.3 x 34.1 x 1.6 mm MCU PCB",
                       "USB socket centered on PCB, dimensions/position not physically measured",
                       "10.5 x 6.5 mm cable body with 6.5 mm metal projection and 5.5 mm engagement",
                       "Bare PCB front-corner contact patches ahead of header pins"],
        "intersections_mm3":{},"parts":{},
    }
    # Write diagnostics even when one of the checks fails during iteration.
    for name,shape in shapes.items():
        shape.exportBrep(str(out/(name+".brep")))
        report["intersections_mm3"][name] = {
            **{n:shape.common(s).Volume for n,s in originals.items()},
            "UsbSocket":shape.common(socket).Volume,
            "McuCentralComponents":shape.common(components).Volume,
            "CableMetal":shape.common(metal).Volume,
            "CableBody":shape.common(cable_body).Volume}
    report["intersections_mm3"]["keeper_bezel"] = keeper.common(bezel).Volume
    (out/"validation.json").write_text(json.dumps(report,indent=2)+"\n")
    for name in shapes:
        assert max(report["intersections_mm3"][name].values())<0.02, (name,report["intersections_mm3"][name])
    assert report["intersections_mm3"]["keeper_bezel"]<0.02

    # Positive-stop probes: motions must encounter plastic, not just friction.
    def overlap_after(moving, fixed, delta):
        trial = moving.copy()
        trial.translate(V(*delta))
        return trial.common(fixed).Volume
    probes = {
        "pcb_forward_into_keeper":overlap_after(pcb,keeper,(0,-0.4,0)),
        "pcb_lift_into_keeper":overlap_after(pcb,keeper,(0,0,0.4)),
        "keeper_forward_into_rear_stops":overlap_after(keeper,base,(0,-0.4,0)),
        "keeper_backward_into_front_bridge":overlap_after(keeper,base,(0,0.4,0)),
        "keeper_lift_into_front_and_rear_hooks":overlap_after(keeper,base,(0,0,0.4)),
        "bezel_inward_into_keeper":overlap_after(bezel,keeper,(0,-0.4,0)),
        "bezel_outward_into_housing":overlap_after(bezel,shell,(0,0.4,0)),
    }
    report["positive_stop_probes_mm3"] = probes
    (out/"validation.json").write_text(json.dumps(report,indent=2)+"\n")
    assert min(probes.values())>0.02, probes
    closing = {}
    for degrees in (1,3,5,8,12):
        tilted = shell.copy()
        tilted.rotate(V(0,p["body_depth"],p["base_thickness"]),V(1,0,0),-degrees)
        closing[str(degrees)] = {
            name:tilted.common(shape).Volume for name,shape in shapes.items()}
    report["rear_first_housing_closure_sample_intersections_mm3"] = closing
    assert max(v for sample in closing.values() for v in sample.values())<0.02,closing
    for name,shape in shapes.items():
        printed = shape.copy()
        if name=="mcu-keeper":
            printed.rotate(V(),V(1,0,0),180)  # Flat rail caps on the bed.
        else:
            printed.rotate(V(),V(1,0,0),90)   # Wide interior frame on the bed.
        printed.translate(V(0,0,-printed.BoundBox.ZMin))
        _,checks = export_verified(printed,out/(name+".stl"),p,M,MP)
        report["parts"][name] = checks
        printed.exportStep(str(out/(name+".step")))
    P.makeCompound([*originals.values(),keeper,bezel,socket]).exportStep(str(out/"assembly.step"))
    for path in out.glob("*.step"):
        path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines())+"\n")
    for name,shape in {**originals,"UsbSocket":socket,"CableBody":cable_body,
                       "CableMetal":metal,"McuCentralComponents":components}.items():
        shape.exportBrep(str(out/(name+".brep")))
    after = {str(f.relative_to(CASE)):hashlib.sha256(f.read_bytes()).hexdigest()
             for f in protected}
    assert before==after, "Existing enclosure or brace outputs changed"
    report["original_outputs_unchanged"] = True
    report["physical_fit_verified"] = False
    (out/"validation.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    main()
