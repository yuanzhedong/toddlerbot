"""Mirror one limb subtree onto the other side (sagittal/Y mirror) to fix a
broken per-side Onshape config, with no CAD edits / Onshape calls.

Usage:
  python scripts/mirror_limb.py --src right --dst left  --root shoulder_pitch_link
  python scripts/mirror_limb.py --src left  --dst right --root hip_pitch_link

Copies the SRC limb subtree, mirrors poses (pos.y*=-1, quat=(w,-x,y,-z)),
joint axes (pseudovector) and inertials, renames SRC_->DST_, points visual
geoms at Y-mirrored mesh copies (assets/<mir>_*.stl), across all 6 robot
variants. Run the keyframe retune separately.
"""
import argparse, copy, os, xml.etree.ElementTree as ET
import trimesh

DIR = "toddlerbot/descriptions/toddlerbot_3_0_2xc"
ASSETS = os.path.join(DIR, "assets")
FILES = ["toddlerbot_3_0_2xc.xml", "toddlerbot_3_0_2xc_fixed.xml",
         "toddlerbot_3_0_2xc_pos.xml", "toddlerbot_3_0_2xc_pos_fixed.xml",
         "toddlerbot_3_0_2xc_mjx.xml", "toddlerbot_3_0_2xc_mjx_fixed.xml"]

def fn(s): return [float(x) for x in s.split()]
def s_(v): return " ".join(repr(x) for x in v)
def mp(s):  p=fn(s); p[1]=-p[1]; return s_(p)
def mq(s):  w,x,y,z=fn(s); return s_([w,-x,y,-z])
def ma(s):  a=fn(s); return s_([-a[0],a[1],-a[2]])
def mi(s):  i=fn(s); i[3]=-i[3]; i[5]=-i[5]; return s_(i)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--src", required=True); ap.add_argument("--dst", required=True)
    ap.add_argument("--root", required=True, help="root link suffix, e.g. hip_pitch_link")
    ap.add_argument("--prefix", default=None, help="mesh prefix (default <dst>mir_)")
    a=ap.parse_args()
    SRC,DST=a.src,a.dst; ROOT_S=f"{SRC}_{a.root}"; ROOT_D=f"{DST}_{a.root}"
    PFX=a.prefix or f"{DST}mir_"
    def rn(s): return s.replace(f"{SRC}_",f"{DST}_") if s else s

    def transform(el):
        if el.tag in ("body","site"):
            if el.get("name"): el.set("name", rn(el.get("name")))
            if el.get("pos"): el.set("pos", mp(el.get("pos")))
            if el.tag=="body": el.set("quat", mq(el.get("quat","1 0 0 0")))
            elif el.get("quat"): el.set("quat", mq(el.get("quat")))
        elif el.tag=="joint":
            if el.get("name"): el.set("name", rn(el.get("name")))
            if el.get("pos"): el.set("pos", mp(el.get("pos")))
            if el.get("axis"): el.set("axis", ma(el.get("axis")))
        elif el.tag=="inertial":
            if el.get("pos"): el.set("pos", mp(el.get("pos")))
            if el.get("fullinertia"): el.set("fullinertia", mi(el.get("fullinertia")))
            if el.get("quat"): el.set("quat", mq(el.get("quat")))
        elif el.tag=="geom":
            if el.get("name"): el.set("name", rn(el.get("name")))
            if el.get("pos"): el.set("pos", mp(el.get("pos")))
            el.set("quat", mq(el.get("quat","1 0 0 0")))
            if el.get("mesh"): el.set("mesh", PFX+el.get("mesh"))
        else:
            if el.get("name"): el.set("name", rn(el.get("name")))
        for c in el: transform(c)

    def find(root,name):
        for p in root.iter():
            for c in list(p):
                if c.tag=="body" and c.get("name")==name: return p,c
        return None,None

    # mesh files used by SRC limb (visual)
    t0=ET.parse(os.path.join(DIR,FILES[0])); _,sb=find(t0.getroot(),ROOT_S)
    mesh_names=sorted({g.get("mesh") for g in sb.iter("geom") if g.get("mesh")})
    files=[n+".stl" for n in mesh_names]
    for f in files:
        out=os.path.join(ASSETS,PFX+f)
        if not os.path.exists(out):
            m=trimesh.load(os.path.join(ASSETS,f),force="mesh")
            m.vertices[:,1]*=-1.0; m.invert(); m.export(out,file_type="stl")
    print(f"mirrored {len(files)} {SRC} meshes -> {PFX}*")

    for fnm in FILES:
        p=os.path.join(DIR,fnm); tree=ET.parse(p); root=tree.getroot()
        parent,dst_body=find(root,ROOT_D); _,src_body=find(root,ROOT_S)
        if dst_body is None or src_body is None: print(f"{fnm}: skip"); continue
        old_dst_meshes={g.get("mesh") for g in dst_body.iter("geom") if g.get("mesh")}
        new=copy.deepcopy(src_body); transform(new)
        i=list(parent).index(dst_body); parent.insert(i,new); parent.remove(dst_body)
        asset=root.find("asset")
        for mm in list(asset.findall("mesh")):
            implied=os.path.splitext(os.path.basename(mm.get("file","")))[0]
            if implied in old_dst_meshes:   # remove exactly the old dst-limb meshes
                asset.remove(mm)
        ex={mm.get("file") for mm in asset.findall("mesh")}
        for f in files:
            if PFX+f not in ex: ET.SubElement(asset,"mesh",{"file":PFX+f})
        tree.write(p); print(f"{fnm}: {SRC}->{DST} {a.root} mirrored")

if __name__=="__main__":
    main()
