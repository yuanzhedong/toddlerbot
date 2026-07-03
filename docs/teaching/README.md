# Teaching RL with ToddlerBot — High-School Curriculum

A ready-to-run course that teaches reinforcement learning, deep learning, and
sim-to-real robotics to high-school students using the ToddlerBot humanoid. Three
3-hour sessions, designed for intro-CS Python students with a GPU per group and a
physical robot per group in the final session.

All materials are **self-contained HTML** (inline CSS/SVG, embedded repo clips) —
no build step, no dependencies. Open them in a browser.

## View the materials

GitHub does not render HTML in the file view, so serve the folder locally:

```bash
python -m http.server 8000 -d docs/teaching
# then open http://localhost:8000/
```

Or in VS Code / Antigravity, use the **Live Preview** extension. Every page is
also print-friendly (Ctrl/Cmd-P) — the worksheets, lab sheet, cheat sheet, and
run-of-show are meant to be printed.

**Start at [`index.html`](index.html)** — it links everything below.

## Contents

| File | What it is | Audience |
|------|------------|----------|
| [`index.html`](index.html) | Landing page linking all materials | Everyone |
| [`rl_highschool.html`](rl_highschool.html) | The full 3-session curriculum (RL loop, the neural-network brain, reward shaping, training, sim-to-real) with diagrams and demo clips | Instructor |
| [`rl_reward_worksheet.html`](rl_reward_worksheet.html) | Session 2 fill-in worksheet on the 10 active reward terms, with an instructor answer key | Student · printable |
| [`session3_run_of_show.html`](session3_run_of_show.html) | Session 3 minute-by-minute timeline + gotcha playbook | Instructor · printable |
| [`sim2real_lab_sheet.html`](sim2real_lab_sheet.html) | Session 3 bench worksheet (safety check-off, predict/observe, diagnose table, before/after) | Student · printable |
| [`sim2real_cheatsheet.html`](sim2real_cheatsheet.html) | One-page bench reference for the deploy→measure→fix→retrain loop | Student · printable |
| [`system_id.html`](system_id.html) | Deep dive: system identification ("make the simulator honest") | Instructor / advanced |
| [`../../toddlerbot/locomotion/walk_class.gin`](../../toddlerbot/locomotion/walk_class.gin) | Scaled-down training config for ~10–15 min classroom runs | Config |

## The three sessions

1. **Meet the robot and the RL loop** — RL intuition, the AI→ML→DL→RL ladder, the
   84→12 neural-network policy, and hands-on time in the MuJoCo simulator.
2. **Shape the reward, train the robot** — how PPO learns, launch real training
   runs, and a reward-shaping experiment (uses the reward worksheet).
3. **Sim-to-real: make it walk in the room** — deploy a trained policy on the
   physical robot, measure the gap, and iterate (uses the run-of-show, lab sheet,
   and cheat sheet).

## Hardware assumptions

- **Sessions 1–2:** one GPU per group (e.g. an RTX 3080) for fast training;
  stronger GPUs (e.g. RTX 6000) for the instructor to pre-train "gold" checkpoints
  and run longer retrains on demand.
- **Session 3:** one physical ToddlerBot per group.

Adjust the pacing and the `walk_class.gin` budget to your actual hardware — time a
run before class.

---

Built on the [ToddlerBot](https://toddlerbot.github.io/) platform.
