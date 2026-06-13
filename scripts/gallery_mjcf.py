"""Render every MJCF under descriptions/ to a thumbnail and build an HTML gallery.

Headless (EGL). Each model is loaded, framed with a 3/4 camera at its home
keyframe (if any), and rendered to a PNG. An index.html groups thumbnails by
robot directory. Serve the output dir with `python -m http.server` to browse.

Usage:
    MUJOCO_GL=egl python scripts/gallery_mjcf.py --out /tmp/mjcf_gallery
"""

import argparse
import glob
import os
import traceback

os.environ.setdefault("MUJOCO_GL", "egl")

import mediapy as media
import mujoco
import numpy as np


def render_model(path, w, h):
    model = mujoco.MjModel.from_xml_path(path)
    data = mujoco.MjData(model)
    if model.nkey > 0:
        mujoco.mj_resetDataKeyframe(model, data, 0)
    mujoco.mj_forward(model, data)
    cam = mujoco.MjvCamera()
    cam.lookat[:] = model.stat.center
    cam.distance = 1.6 * model.stat.extent
    cam.azimuth, cam.elevation = 130, -20
    with mujoco.Renderer(model, height=h, width=w) as r:
        r.update_scene(data, camera=cam)
        return r.render(), model


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="toddlerbot/descriptions")
    p.add_argument("--out", default="/tmp/mjcf_gallery")
    p.add_argument("--extra", nargs="*", default=[],
                   help="extra standalone .xml files to include (grouped by parent dir name)")
    p.add_argument("--width", type=int, default=420)
    p.add_argument("--height", type=int, default=360)
    args = p.parse_args()

    os.makedirs(args.out, exist_ok=True)
    xmls = sorted(glob.glob(os.path.join(args.root, "**", "*.xml"), recursive=True))

    # (xml_path, group, label, png_name)
    jobs = []
    for x in xmls:
        rel = os.path.relpath(x, args.root)
        jobs.append((x, os.path.dirname(rel), os.path.basename(rel),
                     rel.replace("/", "__").replace(".xml", ".png")))
    for x in args.extra:
        grp = os.path.basename(os.path.dirname(os.path.abspath(x)))
        jobs.append((x, grp, os.path.basename(x),
                     "extra__" + grp + "__" + os.path.basename(x).replace(".xml", ".png")))

    rows = {}  # dir -> list of (label, png_name, info/err)
    ok = fail = 0
    for x, group, label, png in jobs:
        try:
            img, model = render_model(x, args.width, args.height)
            media.write_image(os.path.join(args.out, png), img)
            info = f"nq={model.nq} nu={model.nu} njnt={model.njnt} ngeom={model.ngeom}"
            rows.setdefault(group, []).append((label, png, info, True))
            ok += 1
            print(f"OK   {rel}")
        except Exception as e:  # noqa: BLE001
            short = str(e).splitlines()[0][:120]
            rows.setdefault(group, []).append((label, None, short, False))
            fail += 1
            print(f"FAIL {rel}: {short}")

    # build index.html
    html = [
        "<html><head><meta charset='utf-8'><title>ToddlerBot MJCF gallery</title>",
        "<style>body{font-family:sans-serif;background:#111;color:#ddd;margin:20px}"
        "h2{border-bottom:1px solid #444;margin-top:32px}"
        ".grid{display:flex;flex-wrap:wrap;gap:14px}"
        ".card{background:#1c1c1c;border:1px solid #333;border-radius:8px;padding:8px;width:300px}"
        ".card img{width:100%;border-radius:4px;background:#000}"
        ".lbl{font-size:13px;font-weight:bold;margin:6px 0 2px;word-break:break-all}"
        ".info{font-size:11px;color:#8a8}.err{font-size:11px;color:#e77}</style></head><body>",
        f"<h1>ToddlerBot MJCF gallery — {ok} rendered, {fail} failed</h1>",
    ]
    for group in sorted(rows):
        html.append(f"<h2>{group}</h2><div class='grid'>")
        for label, png, info, good in rows[group]:
            html.append("<div class='card'>")
            if good:
                html.append(f"<img src='{png}' loading='lazy'>")
                html.append(f"<div class='lbl'>{label}</div><div class='info'>{info}</div>")
            else:
                html.append("<div style='height:200px;display:flex;align-items:center;"
                            "justify-content:center;color:#e77'>render failed</div>")
                html.append(f"<div class='lbl'>{label}</div><div class='err'>{info}</div>")
            html.append("</div>")
        html.append("</div>")
    html.append("</body></html>")
    with open(os.path.join(args.out, "index.html"), "w") as f:
        f.write("\n".join(html))
    print(f"\n{ok} ok, {fail} failed -> {args.out}/index.html")


if __name__ == "__main__":
    main()
