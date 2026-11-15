#!/usr/bin/env python3
"""Render generated CAD geometry with Matplotlib; no generated illustration."""
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"yellowjacket"))
from generate import load_freecad
A,P,M,MP=load_freecad()
out=HERE/"output"

def read(name):
    s=P.Shape()
    s.read(str(out/(name+".brep")))
    return s

def draw(ax,s,color,alpha=1,offset=(0,0,0)):
    mesh=MP.meshFromShape(Shape=s,LinearDeflection=0.08,
                          AngularDeflection=0.15,Relative=False)
    verts,faces=mesh.Topology
    verts=np.array([[v.x,v.y,v.z] for v in verts])+np.array(offset)
    faces=np.array(faces)
    tris=verts[faces]
    normals=np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0])
    normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
    light=np.array([-0.4,-0.5,0.8]); light/=np.linalg.norm(light)
    shade=0.62+0.38*np.abs(normals@light)
    import matplotlib.colors as colors
    rgb=np.array(colors.to_rgb(color))
    # Keep actual CAD triangles for per-pixel depth testing below.
    rgba=np.column_stack((np.clip(shade[:,None]*rgb,0,1),np.full(len(tris),alpha)))
    if not hasattr(ax,"cad_triangles"):
        ax.cad_triangles=[]; ax.cad_colors=[]
    ax.cad_triangles.append(tris); ax.cad_colors.append(rgba)

def setup(ax,title,elev,azim,exploded=False):
    ax.set_title(title,color="#182b3a",fontsize=12,pad=8)
    ax.cad_view=(elev,azim)
    ax.set_axis_off()

def render(ax):
    # Matplotlib's 3D painter sorting shows interior triangles through large
    # front panels. An orthographic z-buffer resolves each pixel correctly.
    tris=np.concatenate(ax.cad_triangles)
    colors=np.concatenate(ax.cad_colors)
    elev,azim=np.radians(ax.cad_view)
    right=np.array([-np.sin(azim),np.cos(azim),0])
    up=np.array([-np.sin(elev)*np.cos(azim),-np.sin(elev)*np.sin(azim),np.cos(elev)])
    toward=np.array([np.cos(elev)*np.cos(azim),np.cos(elev)*np.sin(azim),np.sin(elev)])
    view=tris@np.stack((right,up,toward),axis=1)
    size=900
    lo=view[:,:,:2].min(axis=(0,1)); hi=view[:,:,:2].max(axis=(0,1))
    scale=(size-70)/max(hi-lo)
    view[:,:,:2]=(view[:,:,:2]-(lo+hi)/2)*scale+size/2
    bg=np.array([244,246,248])/255
    image=np.broadcast_to(bg,(size,size,3)).copy()
    depth=np.full((size,size),-np.inf)
    for tri,color in zip(view,colors):
        x0,y0=np.maximum(np.floor(tri[:,:2].min(axis=0)).astype(int),0)
        x1,y1=np.minimum(np.ceil(tri[:,:2].max(axis=0)).astype(int),size-1)
        if x1<x0 or y1<y0:
            continue
        a,b,c=tri
        denom=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(denom)<1e-10:
            continue
        xx,yy=np.meshgrid(np.arange(x0,x1+1)+0.5,np.arange(y0,y1+1)+0.5)
        w0=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/denom
        w1=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/denom
        w2=1-w0-w1
        z=w0*a[2]+w1*b[2]+w2*c[2]
        current=depth[y0:y1+1,x0:x1+1]
        visible=(w0>=-1e-8)&(w1>=-1e-8)&(w2>=-1e-8)&(z>current)
        current[visible]=z[visible]
        # Clearance volumes are tinted; geometry remains depth-correct.
        image[y0:y1+1,x0:x1+1][visible]=color[:3]*color[3]+bg*(1-color[3])
    ax.imshow(image,origin="lower",interpolation="antialiased")

fig=plt.figure(figsize=(15,11),facecolor="#f4f6f8")
axes=[fig.add_subplot(2,2,i+1,facecolor="#f4f6f8") for i in range(4)]
shell,base,ret=[read(n) for n in ("housing","bottom","retainer")]
glass,nano,pcb=[read(n) for n in ("DisplayGlass","NanoPCB","DisplayPCB")]
for i in (0,1):
    draw(axes[i],shell,"#426b80");draw(axes[i],base,"#273c4c")
    draw(axes[i],glass,"#101921")
setup(axes[0],"5 mm roof blend • recessed PCB pocket",24,-115)
setup(axes[1],"Rear USB-C cable opening • side release windows",22,60)
cut=P.makeBox(60,120,100,A.Vector(-60,-20,0))
draw(axes[2],shell.cut(cut),"#426b80")
draw(axes[2],base,"#273c4c")
draw(axes[2],pcb,"#284eb0")
draw(axes[2],glass,"#101921")
draw(axes[2],ret,"#d4a550")
draw(axes[2],nano,"#226c4e")
draw(axes[2],read("DisplayPlugEnvelope"),"#de9d42",0.55)
draw(axes[2],read("DisplayHeaderTops"),"#de9d42")
draw(axes[2],read("DisplayRibbon"),"#de9d42")
draw(axes[2],read("NanoPlugEnvelopes"),"#de9d42",0.55)
setup(axes[2],"Cutaway • orange = jumper-connector clearance",20,-135)
draw(axes[3],shell,"#426b80")
draw(axes[3],base,"#273c4c",offset=(0,0,-22))
draw(axes[3],ret,"#d4a550",offset=(0,-25,10))
setup(axes[3],"Header-up mount • lowered 18.3 mm nano base",20,-65,True)
for ax in axes:
    render(ax)
fig.suptitle("PINCHWING  /  ROUND-DISPLAY DONGLE\nFirst-fit prototype · dimensions in millimeters",
             fontsize=19,color="#182b3a",y=0.98)
fig.tight_layout(rect=(0,0,1,0.93))
fig.savefig(out/"preview.png",dpi=150)
print(out/"preview.png")
