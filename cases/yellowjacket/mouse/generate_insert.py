#!/usr/bin/env python3
"""Removable underside lens surround for the existing PMW3610 pocket."""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from generate import load_freecad, moved, export_verified
from generate_enclosures import box, wedge, local


def main():
    App, Part, Mesh, MeshPart = load_freecad()
    out = HERE / "output"
    assembly = App.openDocument(str(out/"yellowjacket-mouse-right.FCStd"))
    case = assembly.getObject("PrintableCase").Shape
    sensor = assembly.getObject("SensorPCBReference").Shape
    lens = assembly.getObject("LensEnvelopeReference").Shape
    cx, cy = sensor.BoundBox.Center.x, sensor.BoundBox.Center.y
    clearance = 0.2
    aperture_width, aperture_depth = 9.5, 16.5
    # The plug fills the existing 16 x 24 bottom opening. A flange rests
    # on its interior rim, making it impossible to push through to the desk.
    plug = box(cx-8+clearance,cy-12+clearance,0,
               16-2*clearance,24-2*clearance,1.2,App,Part)
    flange = box(cx-10,cy-14,1.2,20,28,0.6,App,Part)
    insert = plug.fuse(flange)
    # Clear the existing 5.4 mm-diameter PCB support columns.
    for dx in (-8.75,8.75):
        for dy in (-12.75,12.75):
            insert = insert.cut(Part.makeCylinder(
                2.95,3,App.Vector(cx+dx,cy+dy,-0.5)))
    # Four small pressure ribs, away from the corner support columns.
    ribs = []
    for side in (-1,1):
        for dy in (-4,4):
            rib = wedge(-1,2,[
                (-0.35,0.2),(-0.2,0.2),(0.05,0.65),
                (0.05,1.1),(-0.35,1.1)],App,Part)
            ribs.append(local(rib,(cx+side*8,cy+dy),(0,-side),App))
    insert = insert.multiFuse(ribs)
    opening = box(cx-aperture_width/2,cy-aperture_depth/2,-1,
                  aperture_width,aperture_depth,4,App,Part)
    insert = insert.cut(opening).removeSplitter()
    # Only the intentional rib interference is allowed to overlap the case.
    ribs_shape = Part.makeCompound(ribs)
    unintended = insert.cut(ribs_shape).common(case).Volume
    interference = insert.common(case).Volume
    assert unintended < 1e-6, f"Insert body collides with case: {unintended}"
    assert 0 < interference < 1, f"Unexpected grip interference: {interference}"
    assert insert.common(sensor).Volume < 1e-6
    assert insert.common(lens).Volume < 1e-6
    assert insert.common(opening).Volume < 1e-6
    # Print the wider flange against the bed: no support under its overhang.
    printable = insert.copy()
    printable.rotate(App.Vector(),App.Vector(1,0,0),180)
    bb = printable.BoundBox
    printable.translate(App.Vector(-bb.XMin,-bb.YMin,-bb.ZMin))
    _, checks = export_verified(printable,out/"pmw3610-lens-insert.stl",
                                {"mesh_deflection":0.04},Mesh,MeshPart)
    printable.exportStep(str(out/"pmw3610-lens-insert.step"))
    doc = App.newDocument("PMW3610LensInsert")
    for name,shape in (("InsertPrintOrientation",printable),
                       ("InsertInstalledReference",insert),("CaseReference",case),
                       ("SensorPCBReference",sensor),("LensEnvelopeReference",lens)):
        obj = doc.addObject("Part::Feature",name)
        obj.Shape = shape
        obj.addProperty("App::PropertyString","Notes")
        obj.Notes = ("Print this object only, supplied orientation" if name=="InsertPrintOrientation"
                     else "Assembly reference; do not print")
    doc.recompute()
    doc.saveAs(str(out/"pmw3610-lens-insert.FCStd"))
    report = {"part":checks,"aperture_mm":[aperture_width,aperture_depth],
              "body_clearance_per_side_mm":clearance,
              "rib_interference_mm":0.05,"case_intersection_mm3":interference,
              "unintended_case_intersection_mm3":unintended,
              "sensor_intersection_mm3":insert.common(sensor).Volume,
              "lens_envelope_intersection_mm3":insert.common(lens).Volume,
              "installed_bottom_z":insert.BoundBox.ZMin,
              "installed_top_z":insert.BoundBox.ZMax}
    (out/"insert-validation.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    main()
