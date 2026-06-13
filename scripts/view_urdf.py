"""Interactive URDF viewer in the browser (headless-friendly) via Viser.

Loads a ToddlerBot URDF and serves a 3D web viewer with a slider per actuated
joint, so you can pose the robot interactively. No display needed — open the
printed URL in your browser (forward the port over SSH if remote).

Usage:
    python scripts/view_urdf.py \
        --urdf toddlerbot/descriptions/toddlerbot_2xc/toddlerbot_2xc.urdf \
        --port 8080
"""

import argparse
import time
from pathlib import Path

import numpy as np
import viser
from viser.extras import ViserUrdf


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--urdf", default="toddlerbot/descriptions/toddlerbot_2xc/toddlerbot_2xc.urdf"
    )
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8080)
    args = p.parse_args()

    server = viser.ViserServer(host=args.host, port=args.port)
    server.scene.add_grid("/grid", width=2.0, height=2.0)

    urdf = ViserUrdf(server, urdf_or_path=Path(args.urdf), root_node_name="/robot")

    limits = urdf.get_actuated_joint_limits()
    sliders = []
    initial = []
    with server.gui.add_folder("Joints"):
        reset_btn = server.gui.add_button("Reset to zero")
        for name, (lo, hi) in limits.items():
            lo = -np.pi if lo is None else lo
            hi = np.pi if hi is None else hi
            init = float(np.clip(0.0, lo, hi))
            initial.append(init)
            s = server.gui.add_slider(
                name, min=float(lo), max=float(hi), step=1e-3, initial_value=init
            )
            s.on_update(lambda _: urdf.update_cfg(np.array([sl.value for sl in sliders])))
            sliders.append(s)

    @reset_btn.on_click
    def _(_):
        for s, v in zip(sliders, initial):
            s.value = v
        urdf.update_cfg(np.array(initial))

    urdf.update_cfg(np.array(initial))

    print(f"\nViser URDF viewer for: {args.urdf}")
    print(f"Actuated joints: {len(sliders)}")
    print(f"Open in browser:  http://<host>:{args.port}  (e.g. http://192.168.1.118:{args.port})")
    print("Forward the port over SSH if remote, then Ctrl-C to stop.\n")

    while True:
        time.sleep(1.0)


if __name__ == "__main__":
    main()
