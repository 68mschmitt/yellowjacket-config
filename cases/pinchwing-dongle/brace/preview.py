#!/usr/bin/env python3
"""Depth-tested preview of the separate brace; original outputs are read-only."""
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent.parent/"yellowjacket"))
from generate import load_freecad
A,P,M,MP = load_freecad()
OUT = HERE/"output"


def shape(name):
    result = P.Shape()
    result.read(str(OUT/(name+".brep")))
    return result


def render(parts, elev, azim):
    triangles, colors = [], []
    light = np.array([-0.4,-0.5,0.8])
    light /= np.linalg.norm(light)
    for solid, color in parts:
        mesh = MP.meshFromShape(Shape=solid,LinearDeflection=0.08,
                                AngularDeflection=0.15,Relative=False)
        points, faces = mesh.Topology
        tri = np.array([[v.x,v.y,v.z] for v in points])[np.array(faces)]
        normals = np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
        normals /= np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
        triangles.append(tri)
        colors.append((0.62+0.38*np.abs(normals@light))[:,None]*np.array(to_rgb(color)))
    tri = np.concatenate(triangles)
    colors = np.concatenate(colors)
    e,a = np.radians([elev,azim])
    right = np.array([-np.sin(a),np.cos(a),0])
    up = np.array([-np.sin(e)*np.cos(a),-np.sin(e)*np.sin(a),np.cos(e)])
    toward = np.array([np.cos(e)*np.cos(a),np.cos(e)*np.sin(a),np.sin(e)])
    view = tri@np.stack((right,up,toward),axis=1)
    size = 900
    lo = view[:,:,:2].min(axis=(0,1))
    hi = view[:,:,:2].max(axis=(0,1))
    view[:,:,:2] = (view[:,:,:2]-(lo+hi)/2)*((size-80)/max(hi-lo))+size/2
    image = np.broadcast_to(np.array([244,246,248])/255,(size,size,3)).copy()
    depth = np.full((size,size),-np.inf)
    for points,color in zip(view,colors):
        x0,y0 = np.maximum(np.floor(points[:,:2].min(axis=0)).astype(int),0)
        x1,y1 = np.minimum(np.ceil(points[:,:2].max(axis=0)).astype(int),size-1)
        a,b,c = points
        denom = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(denom)<1e-10 or x1<x0 or y1<y0:
            continue
        xx,yy = np.meshgrid(np.arange(x0,x1+1)+0.5,np.arange(y0,y1+1)+0.5)
        w0 = ((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/denom
        w1 = ((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/denom
        w2 = 1-w0-w1
        z = w0*a[2]+w1*b[2]+w2*c[2]
        current = depth[y0:y1+1,x0:x1+1]
        visible = (w0>=-1e-8)&(w1>=-1e-8)&(w2>=-1e-8)&(z>current)
        current[visible] = z[visible]
        image[y0:y1+1,x0:x1+1][visible] = color
    return image


brace,base,retainer = [shape(n) for n in ("Brace","Bottom18_3","DisplayRetainer")]
nano,pcb,glass = [shape(n) for n in ("NanoPCB","DisplayPCB","DisplayGlass")]
cut = P.makeBox(60,120,100,A.Vector(-60,-20,0))
fig, axes = plt.subplots(1,3,figsize=(17,6),facecolor="#f4f6f8")
views = [
    ("One new part • floor-down print",[(brace,"#db8b36")],27,-60),
    ("Installed • housing hidden",[(base,"#273c4c"),(brace,"#db8b36"),
        (retainer,"#d4b65d"),(nano,"#347758"),(pcb,"#3455a2"),(glass,"#101921")],25,-130),
    ("Side cutaway • feet react against base lip",
        [(shape("Housing").cut(cut),"#426b80"),(base.cut(cut),"#273c4c"),
         (brace.cut(cut),"#db8b36"),(retainer.cut(cut),"#d4b65d"),
         (nano.cut(cut),"#347758"),(pcb.cut(cut),"#3455a2"),
         (glass.cut(cut),"#101921")],7,180),
]
for ax,(title,parts,elev,azim) in zip(axes,views):
    ax.imshow(render(parts,elev,azim),origin="lower",interpolation="antialiased")
    ax.set_title(title,fontsize=11,color="#182b3a")
    ax.set_axis_off()
fig.suptitle("ADD-ON DISPLAY BRACE  /  ORANGE = NEW PART\n"
             "Supports the existing retainer • no changes to the printed enclosure",
             fontsize=17,color="#182b3a")
fig.tight_layout(rect=(0,0,1,0.87))
fig.savefig(OUT/"preview.png",dpi=160,facecolor=fig.get_facecolor())
print(OUT/"preview.png")
