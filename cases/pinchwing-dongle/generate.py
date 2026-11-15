#!/usr/bin/env python3
"""Parametric first-fit Pinchwing round-display enclosure. Units: mm."""
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "yellowjacket"))
from generate import load_freecad, export_verified


def main():
    p = json.loads((HERE / "parameters.json").read_text())
    A, P, M, MP = load_freecad()
    V = A.Vector
    out = HERE / "output"
    out.mkdir(exist_ok=True)
    wall, floor = p["wall"], p["base_thickness"]
    angle = p["display_angle"]
    center = V(0, p["display_center_y"], p["display_center_z"])
    seat = p["display_seat_depth"]
    lip = p["display_front_lip"]
    glass_front = seat - p["display_glass_height"]
    board_bottom = p["display_width"] / 2 - p["display_height"]
    hole_v = board_bottom + p["display_hole_from_header_edge"]
    hole_x = p["display_hole_spacing"] / 2
    tail_width = p["display_tail_pocket_width"]
    tail_start = board_bottom - p["display_tail_end_clearance"]
    tail_front = p["display_tail_pocket_front_depth"]
    pcbz, rear = p["nano_pcb_underside_z"], p["nano_rear_y"]
    front = rear - p["nano_length"]

    def box(x, y, z, w, d, h):
        return P.makeBox(w, d, h, V(x, y, z))

    def fuse(shapes):
        return shapes[0].multiFuse(shapes[1:]).removeSplitter() if len(shapes) > 1 else shapes[0]

    def rounded(w, d, r, y=0, z=0):
        # True circular corner arcs, not a faceted outline.
        x = -w / 2
        pts = [(x+r,y), (x+w-r,y), (x+w,y+r), (x+w,y+d-r),
               (x+w-r,y+d), (x+r,y+d), (x,y+d-r), (x,y+r)]
        q = [V(a,b,z) for a,b in pts]
        k = math.sqrt(0.5)
        mid = [V(x+w-r+r*k,y+r-r*k,z), V(x+w-r+r*k,y+d-r+r*k,z),
               V(x+r-r*k,y+d-r+r*k,z), V(x+r-r*k,y+r-r*k,z)]
        edges = []
        for i in range(4):
            edges += [P.makeLine(q[2*i],q[2*i+1]),
                      P.Arc(q[2*i+1],mid[i],q[(2*i+2)%8]).toShape()]
        return P.Wire(edges)

    def placed(shape):
        s = shape.copy()
        s.rotate(V(),V(1,0,0),angle)
        s.translate(center)
        return s

    def board_placed(shape):
        s = shape.copy()
        s.rotate(V(),V(0,0,1),180)
        return placed(s)

    def radial_wire(kind, inset=0, z=0):
        # Matching vertices prevent OCC's automatic loft-edge correspondence
        # from twisting the inner and outer skins at the front shoulders.
        def sdf(x,y,w,h,r,cy):
            qx, qy = abs(x)-(w/2-r), abs(y-cy)-(h/2-r)
            return math.hypot(max(qx,0),max(qy,0))+min(max(qx,qy),0)-r
        pts = []
        for i in range(96):
            a = 2*math.pi*i/96
            dx,dy = math.cos(a),math.sin(a)
            cy = p["body_depth"]/2 if kind == "base" else 0
            lo,hi = 0,100
            for _ in range(45):
                radius = (lo+hi)/2
                x,y = radius*dx,radius*dy+cy
                if kind == "base":
                    inside = sdf(x,y,p["body_width"]-2*inset,
                                 p["body_depth"]-2*inset,8-inset,cy) <= 0
                else:
                    inside = sdf(x,y,48-2*inset,55-2*inset,
                                 5-inset,3.5) <= 0
                if inside:
                    lo = radius
                else:
                    hi = radius
            yy = lo*dy+cy
            zz = (p["body_front_shoulder_height"] +
                  (p["body_shoulder_height"]-p["body_front_shoulder_height"]) *
                  yy/p["body_depth"]) if z == "shoulder" else z
            pts.append(V(lo*dx,yy,zz))
        return P.Wire(P.makePolygon(pts+[pts[0]]).Edges)

    def depth_box(x, v, t, w, h, depth):
        return box(x,v,-t-depth,w,h,depth)

    def cyl(r,t,h,x=0,v=0):
        return P.makeCylinder(r,h,V(x,v,-t),V(0,0,-1))

    def skin_loft(lower, upper):
        # Explicit planar panels also avoid crossed tessellation on strongly
        # warped ruled quads between a horizontal and a tilted section.
        aa = [e.Vertexes[0].Point for e in lower.OrderedEdges]
        bb = [e.Vertexes[0].Point for e in upper.OrderedEdges]
        assert len(aa) == len(bb) == 96
        bottom_face = P.Face(lower)
        bottom_face.reverse()
        faces = [bottom_face, P.Face(upper)]
        for i in range(len(aa)):
            j = (i+1)%len(aa)
            for pts in ([aa[i],aa[j],bb[j]],[aa[i],bb[j],bb[i]]):
                faces.append(P.Face(P.makePolygon(pts+[pts[0]])))
        solid = P.makeSolid(P.makeShell(faces))
        if solid.Volume < 0:
            solid.reverse()
        assert solid.isValid()
        return solid

    front_face = P.Face(radial_wire("front"))
    # A clipped rounded prism gives a single planar front and continuous
    # side walls, without converging lofts around the PCB's header extension.
    roof = p["body_height"]
    outside = P.Face(rounded(p["body_width"],p["body_depth"],8,z=floor)).extrude(
        V(0,0,roof-floor))
    outside = outside.common(placed(depth_box(-100,-100,0,200,200,200)))
    outside = outside.common(placed(depth_box(-100,-100,0,200,
                                             100+p["roof_front_v"],200)))
    normal = V(0,math.sin(math.radians(angle)),-math.cos(math.radians(angle)))
    up = V(0,math.cos(math.radians(angle)),math.sin(math.radians(angle)))
    # A real tangent radius blends the front into the sloping roof.
    top_front_edges = [e for e in outside.Edges if all(
        abs((v.Point-center).dot(normal)) < 1e-6 and
        abs((v.Point-center).dot(up)-p["roof_front_v"]) < 1e-6
        for v in e.Vertexes)]
    assert len(top_front_edges) == 1
    outside = outside.makeFillet(p["roof_front_radius"],top_front_edges)
    # Retain small chamfers on the remaining front perimeter; the tangent
    # edge of the roof blend must not be chamfered.
    front_edges = [e for e in outside.Edges if all(
        abs((v.Point-center).dot(normal)) < 1e-6 for v in e.Vertexes)
        and not all(abs((v.Point-center).dot(up) -
                        (p["roof_front_v"]-p["roof_front_radius"])) < 1e-6
                    for v in e.Vertexes)]
    outside = outside.makeChamfer(0.8,front_edges)
    inside = P.Face(rounded(p["body_width"]-2*wall,p["body_depth"]-2*wall,
                            8-wall,y=wall,z=floor-0.1)).extrude(
        V(0,0,roof-wall-floor+0.1))
    inside = inside.common(placed(depth_box(-100,-100,seat+4.8,200,200,200)))
    inside = inside.common(placed(depth_box(-100,-100,0,200,
                                           100+p["roof_front_v"]-wall,200)))
    shell = outside.cut(inside)
    cuts = [
        cyl(p["display_window_diameter"]/2,-1,seat+3),
        # Full PCB clearance behind the thin front lip, rather than a
        # glass-sized step that can stop the module before it seats.
        cyl(p["display_pcb_pocket_diameter"]/2,lip,seat-lip+0.01),
        cyl(22.25,seat,4.8),
        # The square PCB extension needs the same uninterrupted seating path
        # as the circle. Previously its recess only started at the PCB seat,
        # leaving a broad ledge around the mounting ears and header.
        depth_box(-tail_width/2,tail_start,tail_front,tail_width,
                  -13-tail_start,seat+4.8-tail_front),
        depth_box(-9.5,p["display_header_center_v"]-1.9,seat+1.6,
                  19.0,3.8,p["display_plug_rear_depth"]-seat-1.6+0.5)]
    # Reference bezel has an 18 mm-wide central relief. Add 0.3 mm per
    # side and extend it to 19.3 mm from center, beneath the front lip.
    ribbon = depth_box(-p["display_ribbon_relief_width"]/2,
                       p["display_ribbon_relief_end_v"],lip,
                       p["display_ribbon_relief_width"],
                       -14-p["display_ribbon_relief_end_v"],seat-lip)
    header_top = depth_box(-9.5,p["display_header_center_v"]-1.9,
                           lip,19,3.8,seat-lip)
    cuts += [ribbon,header_top]
    shell = shell.cut(board_placed(fuse(cuts)))
    # Straight locating shafts run all the way to the pocket floor.
    # Only the insertion tips taper inward; there is no widened base.
    pegs = [cyl(p["display_peg_diameter"]/2,0,seat+3.05,x,hole_v)
            .fuse(P.makeCone(p["display_peg_diameter"]/2,0.6,0.7,
                            V(x,hole_v,-seat-3.05),V(0,0,-1)))
            for x in (-hole_x,hole_x)]
    shell = fuse([shell,board_placed(fuse(pegs))])
    shell = shell.cut(board_placed(fuse([ribbon,header_top])))
    # USB opening accepts a molded plug, not merely the metal connector.
    usb = P.Face(rounded(p["usb_opening_width"],p["usb_opening_height"],2))
    usb.rotate(V(),V(1,0,0),90)
    usb.translate(V(0,p["body_depth"]+1,pcbz-4.6))
    usb = usb.extrude(V(0,-8,0))
    shell = shell.cut(usb)

    # Four releasable side snap windows.
    release_windows = [box(22.3 if sign>0 else -26,y-4.5,12.1,3.7,9,3.2)
                       for sign in (-1,1) for y in (19,55)]
    for window in release_windows:
        shell = shell.cut(window)
    # Keep the entire enclosure behind the display plane. This also makes the
    # front bezel a flat print-bed contact surface when the case is face-down.
    shell = shell.common(placed(depth_box(-100,-100,0,200,200,200))).removeSplitter()

    # Display retainer: grips the housing, touches only the PCB rim/ear regions.
    ret_t = seat + p["display_pcb_thickness"] + 0.2
    retainer = cyl(22.0,ret_t,2.4).cut(cyl(18.2,ret_t-0.1,2.6))
    pads = [cyl(2.2,ret_t,2.4,x,hole_v) for x in (-hole_x,hole_x)]
    retainer = fuse([retainer]+pads)
    for x in (-hole_x,hole_x):
        retainer = retainer.cut(cyl(1.0,ret_t-0.2,3,x,hole_v))
    # Localized tapered crush ribs: replaceable retainer absorbs fit adjustment.
    for deg in (25,90,155,220,320):
        a = math.radians(deg)
        retainer = retainer.fuse(cyl(0.45,ret_t+0.7,1.3,
                                    21.9*math.cos(a),21.9*math.sin(a)))
    retainer = retainer.cut(depth_box(-9.6,p["display_header_center_v"]-2.0,
                                      ret_t-0.1,19.2,4.0,2.6))
    retainer = retainer.removeSplitter()

    def cradle(width, z, y0, length):
        half = width/2
        gap = p["nano_side_clearance"]
        end = y0+length
        # Open underside: connector banks and wires can pass between supports.
        rails = [box(-half-1.8,y0,floor,1.65,length,z+3.2-floor),
                 box(half+gap,y0,floor,1.65,length,z+3.2-floor)]
        # End bridges are outside the two pin rows. USB underside is relieved.
        rails += [box(-half-1.8,y0,z-1.2,width+3.6,1.2,1.2),
                  box(-4,y0,z-1.2,8,2.8,1.2),
                  box(-half-1.8,end-0.8,z-1.2,half-3.5,0.8,1.2),
                  box(5.3,end-0.8,z-1.2,half-3.5,0.8,1.2)]
        for sign in (-1,1):
            rails.append(box(half-0.6 if sign>0 else -half-1.8,y0+2,
                             z+p["nano_slot_height"],2.4,length-2,1.0))
            for y in (y0+9,y0+23):
                rails.append(box(half-p["nano_grip_interference"] if sign>0 else -half-gap,
                                 y,z, gap+p["nano_grip_interference"],1.0,1.6))
            # Positive USB insertion stop at the rear corners.
            rails.append(box(5.3 if sign>0 else -half-1.8,end,z-1.2,
                             half-3.5,1,4.4))
        return fuse(rails)

    def bottom(width):
        base = P.Face(rounded(p["body_width"],p["body_depth"],8)).extrude(V(0,0,floor))
        lipouter = rounded(p["body_width"]-2*wall-0.6,
                           p["body_depth"]-2*wall-0.6,5.3,y=wall+0.3,z=floor)
        lipinner = rounded(p["body_width"]-2*wall-3.0,
                           p["body_depth"]-2*wall-3.0,4.1,y=wall+1.5,z=floor-0.1)
        lip = P.Face(lipouter).extrude(V(0,0,2.8)).cut(
            P.Face(lipinner).extrude(V(0,0,3)))
        tabs = []
        for sign in (-1,1):
            for y in (19,55):
                lip = lip.cut(box(20 if sign>0 else -25,y-6,floor-0.1,5,12,3))
                tab = box(21.4 if sign>0 else -22.4,y-3.5,floor,1.0,7,12)
                # Ramp faces upward; flat underside catches the window.
                pts = [V(sign*22.35,y-3.5,12.4),
                       V(sign*(22.4+p["snap_hook_projection"]),y-3.5,12.4),
                       V(sign*22.35,y-3.5,14.4)]
                hook = P.Face(P.makePolygon(pts+[pts[0]])).extrude(V(0,7,0))
                tabs += [tab.fuse(hook)]
        # Flexible front stop resists USB plug insertion pushing the board out.
        # Hold it toward the front while sliding the controller into its slot.
        nano_stop = box(-3,front-1.3,floor,6,1.2,pcbz+1.0-floor)
        base = fuse([base,lip,nano_stop,cradle(width,pcbz,front,p["nano_length"])]+tabs)
        # Access at the forward PCB edge for pushing it out of the slot.
        return base.removeSplitter()

    base = bottom(p["nano_width"])
    alternate = bottom(p["nano_alternate_width"])
    # Rear corner stops need 0.2 mm clearance inside the USB wall.
    shell = shell.cut(box(-13,rear-0.2,pcbz-1.4,26,1.4,5.0)).removeSplitter()
    retainer_world = board_placed(retainer)

    # Approximate hardware and explicit connector keep-outs, used in verification
    # and the assembly file only (never exported as printable parts).
    display = cyl(p["display_width"]/2,seat,p["display_pcb_thickness"]).fuse(
        depth_box(-12.5,board_bottom,seat,25,12.5,p["display_pcb_thickness"]))
    for x in (-hole_x,hole_x):
        display = display.cut(cyl(p["display_hole_diameter"]/2,seat-0.1,2,x,hole_v))
    glass = cyl(17.8,glass_front,p["display_glass_height"])
    header = depth_box(-8.9,p["display_header_center_v"]-1.4,seat+1.6,
                       17.8,2.8,p["display_pin_projection"])
    display_plugs = depth_box(-9.1,p["display_header_center_v"]-1.6,
                             seat+1.6,18.2,3.2,
                             p["display_plug_rear_depth"]-seat-1.6)
    nano = box(-p["nano_width"]/2,front,pcbz,p["nano_width"],
               p["nano_length"],p["nano_pcb_thickness"])
    nano_plugs = fuse([box(x-1.45,front+3,pcbz-14.5,2.9,
                          p["nano_length"]-5,14.5) for x in (-7.62,7.62)])
    hardware = {"DisplayPCB":board_placed(display), "DisplayGlass":board_placed(glass),
                "DisplayPins":board_placed(header), "DisplayPlugEnvelope":board_placed(display_plugs),
                "DisplayHeaderTops":board_placed(depth_box(-8.9,p["display_header_center_v"]-1.4,
                                                          glass_front,17.8,2.8,p["display_glass_height"])),
                "DisplayRibbon":board_placed(depth_box(-9,-19,glass_front,18,5,p["display_glass_height"])),
                "NanoPCB":nano, "NanoPlugEnvelopes":nano_plugs}
    # Additional front-side clearance around the square PCB area, including
    # space beside the pegs for solder/unevenness that the bare-PCB model misses.
    # The 1.2 mm envelope is a fit allowance, not a measured component height.
    tail_clearance = depth_box(-12.5,board_bottom,seat-1.2,25,12.5,1.2)
    for x in (-hole_x,hole_x):
        tail_clearance = tail_clearance.cut(cyl(p["display_hole_diameter"]/2,seat-1.3,1.5,x,hole_v))

    # Print-oriented exports. Retainer lies face-down, peg ends are not printed.
    ret_print = retainer.copy()
    ret_print.translate(V(0,0,ret_t+2.4))
    shell_print = shell.copy()
    shell_print.translate(-center)
    shell_print.rotate(V(),V(1,0,0),-angle)
    shell_print.rotate(V(),V(1,0,0),180)
    parts = {"housing":shell_print, "bottom-nano-18_3":base,
             "bottom-nano-17_8":alternate, "display-retainer":ret_print}
    for key, shape in parts.items():
        s = shape.copy()
        s.translate(V(0,0,-s.BoundBox.ZMin))
        parts[key] = s

    # Low-material full-size display fit coupon: identical face/pegs/pocket.
    local_shell = shell.copy()
    local_shell.translate(-center)
    local_shell.rotate(V(),V(1,0,0),-angle)
    coupon = local_shell.common(front_face.extrude(V(0,0,-9)))
    # Front-face down for this coupon: mirror z by rotating 180 around X.
    coupon.rotate(V(),V(1,0,0),180)
    coupon.translate(V(0,0,-coupon.BoundBox.ZMin))
    parts["display-fit-test"] = coupon.removeSplitter()

    # Nano fit coupons preserve both complete rails but shorten the legs.
    for width, name in ((18.3,"18_3"),(17.8,"17_8")):
        sample = cradle(width,pcbz,front,p["nano_length"])
        sample = sample.common(box(-20,front-1,pcbz-2,40,p["nano_length"]+3,8))
        sample = sample.fuse(box(-width/2-1.8,front,pcbz-2,width+3.6,1.2,2))
        sample.translate(V(0,-front,-sample.BoundBox.ZMin))
        parts["nano-fit-test-"+name] = sample.removeSplitter()

    clip_coupon = base.common(box(19,11,0,7,16,18))
    parts["snap-test-tongue"] = clip_coupon.removeSplitter()
    wall_coupon = shell.common(box(20,11,floor,7,16,16))
    wall_coupon.rotate(V(),V(0,1,0),90)
    wall_coupon.translate(V(0,0,-wall_coupon.BoundBox.ZMin))
    parts["snap-test-wall"] = wall_coupon.removeSplitter()

    report = {"parameters":p, "hole_local_centers_mm":[[-hole_x,hole_v],[hole_x,hole_v]],
              "assumptions":{"display_pcb_thickness":1.6,"glass_diameter":35.6,
                             "header_center_from_header_edge":p["display_header_center_v"]-board_bottom,
                             "nano_dimensions_source":"https://mechboards.co.uk/products/nice-nano-v2"},
              "parts":{}, "intersections_mm3":{}}
    for name, shape in parts.items():
        shape.exportBrep(str(out/(name+"-print.brep")))
        _, checks = export_verified(shape,out/(name+".stl"),p,M,MP)
        shape.exportStep(str(out/(name+".step")))
        report["parts"][name] = checks
        print(name,checks["size_mm"],checks["volume_mm3"],flush=True)
    for name, hw in hardware.items():
        report["intersections_mm3"][name] = {
            "housing":shell.common(hw).Volume,
            "bottom":base.common(hw).Volume,
            "retainer":retainer_world.common(hw).Volume}
    report["intersections_mm3"]["case_parts"] = {
        "shell_bottom":shell.common(base).Volume,
        "shell_retainer_intentional_grip":shell.common(retainer_world).Volume,
        "bottom_retainer":base.common(retainer_world).Volume}
    report["outside_housing_envelope_mm3"] = {
        name: hw.cut(outside).Volume for name, hw in hardware.items()}
    report["outside_housing_envelope_mm3"]["DisplayRetainer"] = retainer_world.cut(outside).Volume
    report["assembled_size_mm"] = [outside.BoundBox.XLength,
                                   outside.BoundBox.YLength,outside.BoundBox.ZMax]
    report["display_seating"] = {
        "pocket_diameter_mm":p["display_pcb_pocket_diameter"],
        "pcb_diameter_mm":p["display_width"],
        "radial_clearance_mm":(p["display_pcb_pocket_diameter"]-p["display_width"])/2,
        "front_lip_mm":lip,
        "glass_face_recess_mm":glass_front,
        "pcb_front_depth_mm":seat,
        "pocket_obstruction_mm3":shell.common(board_placed(
            cyl(p["display_pcb_pocket_diameter"]/2,lip+0.01,seat-lip-0.02))).Volume}
    assert report["display_seating"]["pocket_obstruction_mm3"] < 0.02
    report["square_extension_clearance"] = {
        "pocket_width_mm":tail_width,
        "pocket_front_depth_mm":tail_front,
        "peg_shaft_diameter_mm":p["display_peg_diameter"],
        "front_side_allowance_mm":1.2,
        "front_side_obstruction_mm3":shell.common(board_placed(tail_clearance)).Volume}
    assert report["square_extension_clearance"]["front_side_obstruction_mm3"] < 0.02
    peg_base_clearance = fuse([
        cyl(1.8,tail_front+0.01,seat-tail_front-0.02,x,hole_v).cut(
            cyl(p["display_peg_diameter"]/2,tail_front,seat-tail_front,x,hole_v))
        for x in (-hole_x,hole_x)])
    report["square_extension_clearance"]["peg_base_flare_mm3"] = shell.common(
        board_placed(peg_base_clearance)).Volume
    assert report["square_extension_clearance"]["peg_base_flare_mm3"] < 0.02
    report["display_controller_clearance_mm3"] = {
        name: hw.common(fuse([nano,nano_plugs])).Volume
        for name, hw in hardware.items() if name.startswith("Display")}
    assert max(report["display_controller_clearance_mm3"].values()) < 0.02
    front_skin = outside.common(placed(depth_box(-100,-100,0.05,200,200,lip-0.1)))
    front_skin = front_skin.cut(placed(cyl(p["display_window_diameter"]/2,0,lip)))
    report["front_panel_missing_material_mm3"] = front_skin.cut(shell).Volume
    assert report["front_panel_missing_material_mm3"] < 0.02
    exterior = P.makeCompound([face for face in outside.Faces if not all(
        abs(v.Point.z-floor) < 1e-6 for v in face.Vertexes)])
    openings = fuse([board_placed(cyl(p["display_window_diameter"]/2,-1,seat+3)),
                     usb]+release_windows)
    report["unintended_exterior_opening_mm2"] = exterior.cut(shell).cut(openings).Area
    assert report["unintended_exterior_opening_mm2"] < 0.05, report["unintended_exterior_opening_mm2"]
    (out/"validation.json").write_text(json.dumps(report,indent=2)+"\n")
    # These must have no solid interference, independent of assumed PCB details.
    for name in ("DisplayPCB","DisplayGlass","DisplayPlugEnvelope","DisplayHeaderTops","DisplayRibbon","NanoPlugEnvelopes"):
        assert max(report["intersections_mm3"][name].values()) < 0.02, (name,report["intersections_mm3"][name])
    assert report["intersections_mm3"]["case_parts"]["shell_bottom"] < 0.02
    assert report["intersections_mm3"]["case_parts"]["bottom_retainer"] < 0.02
    assert max(report["outside_housing_envelope_mm3"].values()) < 0.02
    (out/"validation.json").write_text(json.dumps(report,indent=2)+"\n")
    doc = A.newDocument("PinchwingDongle")
    for name, shape in {"Housing":shell,"Bottom18_3":base,
                        "DisplayRetainer":retainer_world,**hardware}.items():
        obj = doc.addObject("Part::Feature",name)
        obj.Shape = shape
    doc.saveAs(str(out/"pinchwing-dongle.FCStd"))
    P.makeCompound([shell,base,retainer_world]).exportStep(str(out/"assembly.step"))
    # OCC adds trailing spaces to STEP entity continuations.
    for path in out.glob("*.step"):
        path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines())+"\n")
    # BREP geometry in assembly coordinates for the renderer.
    for name, shape in {"housing":shell,"bottom":base,"retainer":retainer_world,**hardware}.items():
        shape.exportBrep(str(out/(name+".brep")))


if __name__ == "__main__":
    main()
