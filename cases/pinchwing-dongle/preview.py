#!/usr/bin/env python3
"""Render generated CAD geometry with Matplotlib; no generated illustration."""
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

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
    # One collection per view gives consistent depth sorting across components.
    rgba=np.column_stack((np.clip(shade[:,None]*rgb,0,1),np.full(len(tris),alpha)))
    if not hasattr(ax,"cad_triangles"):
        ax.cad_triangles=[]; ax.cad_colors=[]
    ax.cad_triangles.append(tris); ax.cad_colors.append(rgba)

def setup(ax,title,elev,azim,exploded=False):
    ax.set_title(title,color="#182b3a",fontsize=12,pad=8)
    ax.set_xlim(-28,28); ax.set_ylim(-12,75); ax.set_zlim(-25 if exploded else 0,82)
    ax.set_box_aspect((56,87,107 if exploded else 82),zoom=1.25)
    ax.set_proj_type("ortho")
    ax.view_init(elev=elev,azim=azim)
    ax.set_axis_off()

fig=plt.figure(figsize=(15,11),facecolor="#f4f6f8")
axes=[fig.add_subplot(2,2,i+1,projection="3d",facecolor="#f4f6f8") for i in range(4)]
shell,base,ret=[read(n) for n in ("housing","bottom","retainer")]
glass,nano,pcb=[read(n) for n in ("DisplayGlass","NanoPCB","DisplayPCB")]
for i in (0,1):
    draw(axes[i],shell,"#426b80");draw(axes[i],base,"#273c4c")
    draw(axes[i],glass,"#101921")
setup(axes[0],"60° flat front • circular display opening",24,-115)
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
    ax.add_collection3d(Poly3DCollection(np.concatenate(ax.cad_triangles),
                        facecolors=np.concatenate(ax.cad_colors),linewidths=0,
                        rasterized=True))
fig.suptitle("PINCHWING  /  ROUND-DISPLAY DONGLE\nFirst-fit prototype · dimensions in millimeters",
             fontsize=19,color="#182b3a",y=0.98)
fig.tight_layout(rect=(0,0,1,0.93))
fig.savefig(out/"preview.png",dpi=150)
print(out/"preview.png")
