#!/usr/bin/env python3
"""Z-buffered preview of the actual CAD solids, using the enclosure renderer style."""
from pathlib import Path
import json
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from generate import load_freecad

App, Part, Mesh, MeshPart = load_freecad()
doc = App.openDocument(str(HERE/"output/yellowjacket-mouse-right.FCStd"))
image = Image.new("RGB",(1600,900),"#f2f4f7")
draw = ImageDraw.Draw(image)
font = "/usr/share/fonts/TTF/DejaVuSans.ttf"
title = ImageFont.truetype(font,28)
small = ImageFont.truetype(font,20)
draw.text((35,25),"Yellowjacket / PMW3610 Rev 1 — pressure-fit mouse tray",
          fill="#182238",font=title)


def panel(objects, left, heading):
    draw.text((left+20,110),heading,fill="#182238",font=small)
    points, faces, colors = [], [], []
    for name,color in objects:
        shape = doc.getObject(name).Shape
        mesh = MeshPart.meshFromShape(Shape=shape,LinearDeflection=.1,
                                      AngularDeflection=.18,Relative=False)
        verts,tris = mesh.Topology
        start = len(points)
        points.extend([tuple(v) for v in verts])
        faces.extend([tuple(i+start for i in t) for t in tris])
        colors.extend([color]*len(tris))
    points = np.array(points)
    # Orthographic view from front/right/above; exact z-buffering avoids
    # painter-sort artifacts across the large planar tray floor.
    screen_x = np.array([.94,.342,0])
    depth = np.array([.342,-.94,1.7])
    depth /= np.linalg.norm(depth)
    screen_y = np.cross(screen_x,depth)
    uv = np.column_stack((points@screen_x, points@screen_y))
    lo,hi = uv.min(axis=0),uv.max(axis=0)
    scale = min(720/(hi[0]-lo[0]),550/(hi[1]-lo[1]))
    screen = (uv-lo)*scale + (np.array([760,590])-(hi-lo)*scale)/2
    depths = points@depth
    pixels = np.full((590,760,3),(242,244,247),dtype=np.uint8)
    zbuffer = np.full((590,760),-np.inf)
    light=np.array([-.25,-.35,.9]); light/=np.linalg.norm(light)
    for face,color in zip(faces,colors):
        a,b,c=points[list(face)]
        normal=np.cross(b-a,c-a)
        norm=np.linalg.norm(normal)
        if norm<1e-12:
            continue
        rgb=np.array(color)*(.62+.35*abs(normal@light/norm))
        triangle=screen[list(face)]
        x0,y0=np.floor(triangle.min(axis=0)).astype(int)
        x1,y1=np.ceil(triangle.max(axis=0)).astype(int)
        x0,y0,x1,y1=max(0,x0),max(0,y0),min(759,x1),min(589,y1)
        if x0>x1 or y0>y1:
            continue
        (ax,ay),(bx,by),(cx,cy)=triangle
        den=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
        if abs(den)<1e-10:
            continue
        xs,ys=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
        wa=((by-cy)*(xs-cx)+(cx-bx)*(ys-cy))/den
        wb=((cy-ay)*(xs-cx)+(ax-cx)*(ys-cy))/den
        wc=1-wa-wb
        z=wa*depths[face[0]]+wb*depths[face[1]]+wc*depths[face[2]]
        old=zbuffer[y0:y1+1,x0:x1+1]
        mask=(wa>=-1e-8)&(wb>=-1e-8)&(wc>=-1e-8)&(z>old)
        old[mask]=z[mask]
        pixels[y0:y1+1,x0:x1+1][mask]=rgb.astype(np.uint8)
    image.paste(Image.fromarray(pixels),(left,150))


blue=("PrintableCase",(130,174,206))
panel([blue],20,"Printable case • right hand")
panel([blue,("KeyboardPCBReference",(65,118,90)),
       ("SensorPCBReference",(222,181,85)),("LensEnvelopeReference",(177,221,225)),
       ("SensorCapInstalledReference",(196,202,216))],
      820,"Assembly • snap cap and header relief")
p = json.loads((HERE/"parameters.json").read_text())
bounds = doc.getObject("PrintableCase").Shape.BoundBox
draw.text((35,780),f"{bounds.XLength:.1f} × {bounds.YLength:.1f} mm footprint • {p['floor_thickness']:.1f} mm floor • {bounds.ZLength:.1f} mm maximum shell height",
          fill="#334155",font=small)
draw.text((35,815),"Blue: case   Green: keyboard PCB   Gold: sensor PCB   Grey: snap cap",
          fill="#334155",font=small)
draw.text((35,850),"Switches/controller omitted. Optical height assumes 0.6 mm mouse skates.",
          fill="#334155",font=small)
image.save(HERE/"output/preview.png")
