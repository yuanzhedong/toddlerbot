"""Headless render of the ToddlerBot model to PNG images.

Uses MuJoCo's offscreen EGL renderer (no display needed). Renders the robot
from each named camera in the scene at its default keyframe/home pose.

Usage:
    MUJOCO_GL=egl python scripts/render_robot.py \
        --scene toddlerbot/descriptions/toddlerbot_2xc/scene.xml \
        --out /tmp/toddler_render
"""

import argparse
import os

os.environ.setdefault("MUJOCO_GL", "egl")

import mediapy as media
import mujoco


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scene",
        default="toddlerbot/descriptions/toddlerbot_2xc/scene.xml",
    )
    parser.add_argument("--out", default="/tmp/toddler_render")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    model = mujoco.MjModel.from_xml_path(args.scene)
    data = mujoco.MjData(model)

    # Settle to the model's keyframe "home" if present, else just forward.
    if model.nkey > 0:
        mujoco.mj_resetDataKeyframe(model, data, 0)
    mujoco.mj_forward(model, data)

    cam_names = [
        mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_CAMERA, i)
        for i in range(model.ncam)
    ]
    if not cam_names:
        cam_names = [None]  # free camera fallback

    with mujoco.Renderer(model, height=args.height, width=args.width) as renderer:
        for cam in cam_names:
            if cam is not None:
                renderer.update_scene(data, camera=cam)
                fname = os.path.join(args.out, f"robot_{cam}.png")
            else:
                renderer.update_scene(data)
                fname = os.path.join(args.out, "robot_free.png")
            pixels = renderer.render()
            media.write_image(fname, pixels)
            print(f"wrote {fname}")


if __name__ == "__main__":
    main()
