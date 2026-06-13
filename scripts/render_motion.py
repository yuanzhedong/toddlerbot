"""Render a ToddlerBot keyframe motion (.lz4) to an MP4 video, headless.

Kinematically plays back the recorded `qpos` trajectory into the MuJoCo scene
and renders each frame via the offscreen EGL renderer (no display needed).

Usage:
    MUJOCO_GL=egl python scripts/render_motion.py \
        --motion motion/push_up_2xc.lz4 \
        --scene toddlerbot/descriptions/toddlerbot_2xc/scene.xml \
        --camera perspective --out /tmp/toddler_motion.mp4
"""

import argparse
import os

os.environ.setdefault("MUJOCO_GL", "egl")

import joblib
import mediapy as media
import mujoco
import numpy as np


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--motion", default="motion/push_up_2xc.lz4")
    p.add_argument("--scene", default="toddlerbot/descriptions/toddlerbot_2xc/scene.xml")
    p.add_argument("--camera", default="perspective")
    p.add_argument("--out", default="/tmp/toddler_motion.mp4")
    p.add_argument("--width", type=int, default=960)
    p.add_argument("--height", type=int, default=540)
    p.add_argument("--stride", type=int, default=1, help="render every Nth frame")
    args = p.parse_args()

    data_dict = joblib.load(args.motion)
    qpos = np.asarray(data_dict["qpos"], dtype=np.float64)
    time_arr = np.asarray(data_dict["time"], dtype=np.float64)
    dt = float(np.mean(np.diff(time_arr)))
    fps = max(1, round(1.0 / dt / args.stride))

    model = mujoco.MjModel.from_xml_path(args.scene)
    data = mujoco.MjData(model)
    assert qpos.shape[1] == model.nq, f"qpos {qpos.shape[1]} != model nq {model.nq}"

    frames = []
    with mujoco.Renderer(model, height=args.height, width=args.width) as renderer:
        for i in range(0, qpos.shape[0], args.stride):
            data.qpos[:] = qpos[i]
            mujoco.mj_forward(model, data)
            renderer.update_scene(data, camera=args.camera)
            frames.append(renderer.render())

    media.write_video(args.out, frames, fps=fps)
    print(f"wrote {args.out}  ({len(frames)} frames @ {fps} fps, {len(frames)/fps:.1f}s)")


if __name__ == "__main__":
    main()
