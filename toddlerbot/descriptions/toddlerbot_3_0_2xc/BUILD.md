# toddlerbot_3_0_2xc — build & provenance

Full-DOF MuJoCo (MJCF) + URDF model for **ToddlerBot 3.0** (2xc / palm config),
generated from the Onshape CAD on 2026-06-13.

## Source CAD (single source of truth)

Onshape document **"ToddlerBot - 3.0 - 05-25-2026"** (owner: Yuanzhe Dong).
The robot is split across three documents (same structure as 2.0):

| Piece | Onshape document id | assembly element | configuration (display) |
|-------|---------------------|------------------|--------------------------|
| body/trunk | `04eb7c216d6ade2f7c1f82bf` | `toddlerbot` (`47f1da75bdfc3037706600d2`) | `Configuration=2xc_430_palm` |
| leg (L/R)  | `cb8da3f8510f3b10492c943e` (`ToddlerBotLegs`) | `leg` (`129a4dc5b5a03c98786eef81`) | `Configuration=left_2xc_430_2` / `right_2xc_430_2` |
| arm (L/R)  | `9d5acd05cb0e8be60d56ce56` (`ToddlerBotArms`) | `arm` (`dfea5f660c08aa88eb6767e9`) | `Configuration=left_palm` / `right_palm` |

### ⚠️ Leg config-name trap
The leg `Configuration` parameter's **display names are offset from their internal
values**. The real `2xc_430_palm` robot resolves its legs to internal value
`Copy_of_left_2xc_430` / `Copy_of_right_2xc_430`, which corresponds to the
**display name `left_2xc_430_2` / `right_2xc_430_2`** — *not* `left_2xc_430`.
Using `left_2xc_430` silently yields a different (2.0-era) hip_yaw orientation.
Always export the legs with the `_2` display configs (or the internal
`Copy_of_left_2xc_430` value).

## What changed vs 2.0 (confirmed against CAD)
1. **Shoulder angle** — arm COM shifts ~10.5 mm (same 0.481 kg mass, changed
   inertia); the arm is mounted/posed at a different shoulder angle.
2. **hip_yaw XC330 install direction** — `hip_yaw_link` rotated ~12.9° and the
   XC330 gear drive ~75° vs the 2.0 orientation (this is the `_2` leg variant).

## How it was built
1. Export the 5 pieces with `onshape-to-robot` (needs `pymeshlab` for STL
   simplification, and `ONSHAPE_ACCESS_KEY`/`ONSHAPE_SECRET_KEY`). Configs as in
   the table above, written into `toddlerbot/descriptions/assemblies/<name>/config.json`
   for: `2xc_430_palm`, `left_leg_2xc_430`, `right_leg_2xc_430`, `left_arm_palm`,
   `right_arm_palm`. (Body config.json also sets the passive neck/waist joints and
   the `closing_neck_pitch*` equality, matching `get_xml.py`.)
2. Stitch:
   ```
   python toddlerbot/descriptions/assemble_xml.py --robot toddlerbot_3_0_2xc \
       --torso-name 2xc_430_palm --arm-name palm --leg-name 2xc_430
   ```
   This regenerates every `scene*` / `*_mjx` / `*_pos` / `*_fixed` variant,
   convex-hull collisions, the home keyframe, and `robot.yml`.

> Note: the repo's `onshape_to_robot.py` `ASSEMBLY_DOC_MAP` still points at the
> 2.0 documents; it was intentionally **not** modified (the 3.0 docs reuse the
> same assembly names with different ids, which would break 2.0 regen). Use the
> configs in this file to regenerate 3.0.

## Verification (all passed)
- **Total mass = CAD exactly**: 3.4522 kg (0.0 g diff vs Onshape mass properties).
- **DOF**: `nq=51, nu=30, njnt=45` — all 30 actuators present (legs+arms+neck+waist).
- **robot.yml**: every value reproduces from the assembled model; 3.0-specific
  changes captured (`com_z` 0.2969, `hip_to_ankle_roll_z` 0.1676, `foot_to_com_y`
  0.0396).
- **Motor map** (`default.yml`) consistent with CAD inventory: `2XC430`×2 (hip
  dual-axis), `2XL430`×6 (arm dual-axis), `XC430`×4, plus `XC330` (neck/waist/
  hip_yaw) and `XM430` (knee/ankle).
- **Physics**: loads + 500 steps, no NaN; home keyframe base height 0.310 m.

## Caveats (inherited from 2.0 `default.yml`, not from CAD)
- **`XM430` W210 vs W350**: not derivable from CAD (same physical motor, differs
  only in internal gear ratio); `default.yml` uses W210 for knee/ankle. Confirm
  from the hardware BOM if needed.
- **`home_pos` joint angles and `kp` gains** are 2.0-tuned; the home pose stands,
  but gains may want retuning for 3.0's mass distribution.
