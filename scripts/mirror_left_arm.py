"""Rebuild the left arm of toddlerbot_3_0_2xc as a sagittal (Y) mirror of the
correct right arm, fixing the broken `left_arm` Onshape config (90 deg shoulder_roll
error) with no CAD edits / no Onshape calls.

Per standalone robot XML: delete left_shoulder_pitch_link subtree, insert a Y-mirror
of right_shoulder_pitch_link (right_*->left_*), mirror body/geom/inertial poses and
joint axes, and point left visual geoms at Y-mirrored copies of the right meshes.
Mirrored STLs (assets/lmir_*.stl) are created once. Keyframe is handled separately.
"""
import copy, os, xml.etree.ElementTree as ET
import trimesh

DIR = "toddlerbot/descriptions/toddlerbot_3_0_2xc"
ASSETS = os.path.join(DIR, "assets")
FILES = ["toddlerbot_3_0_2xc.xml", "toddlerbot_3_0_2xc_fixed.xml",
         "toddlerbot_3_0_2xc_pos.xml", "toddlerbot_3_0_2xc_pos_fixed.xml",
         "toddlerbot_3_0_2xc_mjx.xml", "toddlerbot_3_0_2xc_mjx_fixed.xml"]

def fnum(s): return [float(x) for x in s.split()]
def s_(v): return " ".join(repr(x) for x in v)
def mir_pos(s):  p=fnum(s); p[1]=-p[1]; return s_(p)
def mir_quat(s): w,x,y,z=fnum(s); return s_([w,-x,y,-z])
def mir_axis(s): a=fnum(s); return s_([-a[0],a[1],-a[2]])
def mir_fullinertia(s):
    i=fnum(s); i[3]=-i[3]; i[5]=-i[5]; return s_(i)   # ixx iyy izz ixy ixz iyz -> flip ixy,iyz

def rn(s): return s.replace("right_","left_") if s else s

def transform(el):
    if el.tag=="body":
        if el.get("name"): el.set("name", rn(el.get("name")))
        if el.get("pos"): el.set("pos", mir_pos(el.get("pos")))
        el.set("quat", mir_quat(el.get("quat","1 0 0 0")))
    elif el.tag=="joint":
        if el.get("name"): el.set("name", rn(el.get("name")))
        if el.get("pos"): el.set("pos", mir_pos(el.get("pos")))
        if el.get("axis"): el.set("axis", mir_axis(el.get("axis")))
    elif el.tag=="inertial":
        if el.get("pos"): el.set("pos", mir_pos(el.get("pos")))
        if el.get("fullinertia"): el.set("fullinertia", mir_fullinertia(el.get("fullinertia")))
        if el.get("quat"): el.set("quat", mir_quat(el.get("quat")))
    elif el.tag=="geom":
        if el.get("name"): el.set("name", rn(el.get("name")))
        if el.get("pos"): el.set("pos", mir_pos(el.get("pos")))
        el.set("quat", mir_quat(el.get("quat","1 0 0 0")))
        if el.get("mesh"): el.set("mesh", "lmir_"+el.get("mesh"))  # point at mirrored mesh
    elif el.tag=="site":
        if el.get("name"): el.set("name", rn(el.get("name")))
        if el.get("pos"): el.set("pos", mir_pos(el.get("pos")))
        if el.get("quat"): el.set("quat", mir_quat(el.get("quat")))
    else:
        if el.get("name"): el.set("name", rn(el.get("name")))  # catch-all rename
    for c in el: transform(c)

def find(root, name):
    for parent in root.iter():
        for ch in list(parent):
            if ch.tag=="body" and ch.get("name")==name: return parent, ch
    return None, None

def main():
    # mesh files used by the right arm (visual only)
    t0=ET.parse(os.path.join(DIR,FILES[0])); r0=t0.getroot()
    _, rb = find(r0,"right_shoulder_pitch_link")
    mesh_names=sorted({g.get("mesh") for g in rb.iter("geom") if g.get("mesh")})
    files=[n+".stl" for n in mesh_names]
    for f in files:
        out=os.path.join(ASSETS,"lmir_"+f)
        if not os.path.exists(out):
            m=trimesh.load(os.path.join(ASSETS,f),force="mesh")
            m.vertices[:,1]*=-1.0; m.invert(); m.export(out,file_type="stl")
    print(f"mirrored {len(files)} meshes -> lmir_*.stl")

    for fn in FILES:
        p=os.path.join(DIR,fn); tree=ET.parse(p); root=tree.getroot()
        parent,left_body=find(root,"left_shoulder_pitch_link")
        _,right_body=find(root,"right_shoulder_pitch_link")
        if left_body is None or right_body is None:
            print(f"{fn}: skip (no arm)"); continue
        new_left=copy.deepcopy(right_body); transform(new_left)
        i=list(parent).index(left_body); parent.insert(i,new_left); parent.remove(left_body)
        # assets: remove stale left arm mesh decls, add lmir_ decls
        asset=root.find("asset")
        for m in list(asset.findall("mesh")):
            base=os.path.basename(m.get("file",""))
            if base.startswith("left_") and any(k in base for k in("shoulder","elbow","wrist","hand")):
                asset.remove(m)
        existing={m.get("file") for m in asset.findall("mesh")}
        for f in files:
            lf="lmir_"+f
            if lf not in existing: ET.SubElement(asset,"mesh",{"file":lf})
        tree.write(p)
        print(f"{fn}: left arm mirrored")

if __name__=="__main__":
    main()
