"""Interactive MJCF (MuJoCo XML) viewer in the browser via Viser, headless.

Loads a MuJoCo model, pushes each mesh geom into a Viser scene, and adds a
slider per actuated joint. Moving a slider sets qpos, runs mj_forward, and
updates every geom's world pose -- so you inspect the *actual MJCF* kinematics
(not the derived URDF). No display needed; open the printed URL in a browser.

Usage:
    python scripts/view_mjcf.py \
        --mjcf toddlerbot/descriptions/toddlerbot_2xc/scene.xml --port 8082
"""

import argparse
import time

import mujoco
import numpy as np
import viser
import viser.transforms as vtf


def mesh_geoms(model):
    """Yield (geom_id, vertices, faces) for every mesh geom in the model."""
    for g in range(model.ngeom):
        if model.geom_type[g] != mujoco.mjtGeom.mjGEOM_MESH:
            continue
        mid = model.geom_dataid[g]
        v0, vn = model.mesh_vertadr[mid], model.mesh_vertnum[mid]
        f0, fn = model.mesh_faceadr[mid], model.mesh_facenum[mid]
        verts = model.mesh_vert[v0 : v0 + vn].reshape(-1, 3)
        faces = model.mesh_face[f0 : f0 + fn].reshape(-1, 3)
        yield g, verts.astype(np.float32), faces.astype(np.uint32)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mjcf", default="toddlerbot/descriptions/toddlerbot_2xc/scene.xml")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8082)
    args = p.parse_args()

    model = mujoco.MjModel.from_xml_path(args.mjcf)
    data = mujoco.MjData(model)
    if model.nkey > 0:
        mujoco.mj_resetDataKeyframe(model, data, 0)
    mujoco.mj_forward(model, data)

    server = viser.ViserServer(host=args.host, port=args.port)
    server.scene.add_grid("/grid", width=2.0, height=2.0)

    handles = []  # (geom_id, viser handle)
    for g, verts, faces in mesh_geoms(model):
        rgba = model.geom_rgba[g]
        color = tuple((rgba[:3] * 255).astype(int)) if rgba[3] > 0 else (180, 180, 190)
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, g) or f"geom_{g}"
        h = server.scene.add_mesh_simple(
            f"/robot/{name}", vertices=verts, faces=faces, color=color
        )
        handles.append((g, h))

    def refresh_poses():
        for g, h in handles:
            h.position = tuple(data.geom_xpos[g])
            h.wxyz = vtf.SO3.from_matrix(data.geom_xmat[g].reshape(3, 3)).wxyz

    refresh_poses()

    # One slider per (1-DoF) actuated joint, driving qpos via the joint's qposadr.
    sliders = []
    with server.gui.add_folder("Joints"):
        reset_btn = server.gui.add_button("Reset")
        for j in range(model.njnt):
            if model.jnt_type[j] not in (
                mujoco.mjtJoint.mjJNT_HINGE,
                mujoco.mjtJoint.mjJNT_SLIDE,
            ):
                continue  # skip free/ball joints
            jname = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, j) or f"j{j}"
            qadr = model.jnt_qposadr[j]
            if model.jnt_limited[j]:
                lo, hi = model.jnt_range[j]
            else:
                lo, hi = -np.pi, np.pi
            init = float(np.clip(data.qpos[qadr], lo, hi))
            s = server.gui.add_slider(
                jname, min=float(lo), max=float(hi), step=1e-3, initial_value=init
            )

            def _cb(_, qadr=qadr, s=s):
                data.qpos[qadr] = s.value
                mujoco.mj_forward(model, data)
                refresh_poses()

            s.on_update(_cb)
            sliders.append((qadr, s, init))

    @reset_btn.on_click
    def _(_):
        for qadr, s, init in sliders:
            s.value = init
            data.qpos[qadr] = init
        mujoco.mj_forward(model, data)
        refresh_poses()

    print(f"\nViser MJCF viewer for: {args.mjcf}")
    print(f"mesh geoms: {len(handles)}   joint sliders: {len(sliders)}")
    print(f"Open:  http://192.168.1.118:{args.port}  (forward the port in Antigravity)\n")
    while True:
        time.sleep(1.0)


if __name__ == "__main__":
    main()
