#!/usr/bin/env python
"""Wolverine ground contact (lane wolverine-ground, 11-09): per-step y offsets that put each drawn pose's feet on Schaefer's floor line,
and the sole-exact jump arc, from the MSHvSF capture. Build input, ROM-derived output, never in git.

Why. Poses are anchored by the bottom row of their tile grid (assets.py pose_of). The lowest OPAQUE row of a pose (its sole) sits 0..N rows above
that grid bottom, and N differs per pose (stance 7, hp lunge 1, ...), so a bottom-anchored pose floats or sinks by the difference. The sole of the
standing stance (pose 17, 7 rows above its grid bottom) is the calibrated floor line (Yaba: within 1 px of Schaefer's own feet).
  d_p   = how far pose p's sole sits above the stance's, in px, down positive (pose 17: 0). A pose drawn bottom-anchored has its sole at d_p.
  a_f   = the original's art offset of the sole at capture frame f: sole_f - (origin_y_f + 22). 22 = the stance's sole below the origin; this holds
          while the camera scrolls (origin_y is on screen) and when he is knocked down.
  t     = the offset a step should have: 0 (on the floor) unless the original deliberately lifts him (a_f < -TOL: the heavy punch's hop, the kick,
          the high-hit pop-up): then the lift is kept. A pose is never put below the floor line.
  g     = t - d_p, the generated per-step offset (down positive) added to his draw y.
usage: [GROUND_TIMELINE_ASSETS=PRE_MERGE_DIR] ground.py CAPTURE_DIR ASSETS_DIR [--report FILE]   (needs capture of tools/wolverine/run_mame.sh with WV_BOXES=1: obj.txt, tiles.bin, boxes.txt, origin.txt)
Writes ASSETS_DIR/remap.json keys:
  ground  {move: [g per step]}   (SAT_WV_GROUND=1: the original's deliberate lifts kept)
  ground_floor {move: [g per step]}   (SAT_WV_GROUND=2: strict, every pose's lowest opaque row on the floor line)
  jumpair {"steps": [[pose, frames, air_from, air_to]...], "dp": [...]}: the sole-exact jump (air = floor-line height of the original's sole, px, screen
          space incl. the camera's scroll, as the pose-bottom lift of retime.py was), for gen_c.py to scale (SAT_WV_JUMP)."""
import json, os, pathlib, statistics, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from assets import frames, tiles, flips, pens, expand, BODY, PALS, WINDOWS
import timeline as TL

TOL = 4
SOLE_BELOW_ORIGIN = 22     # stance sole row minus origin screen y (capture: 223 - 201)
STANCE_SOLE_ROW = 223
JUMP_FRAMES = (2103, 2157)
JUMP_TICKS = 33
SKIP = {"jump"}            # own arc
FLOOR_ONLY = {"idle", "walk", "crouch", "throw", "dash"}   # always on the floor (the original's walk bob is not kept)


def pose_sole(A, raw):
    """per pose: lowest opaque row relative to the tile grid bottom (negative), top row"""
    canon = {}
    out = []
    for p in A["poses"]:
        lo, hi = -10**9, 10**9
        for dx, dy, t, hf, vf, prow in p:
            px = pens(raw[A["keys"][t] * 128:A["keys"][t] * 128 + 128])
            px = flips(px)[(hf, vf)]
            for ry in range(16):
                if any(q != 15 for q in px[ry]):
                    lo = max(lo, dy + ry)
                    hi = min(hi, dy + ry)
        out.append((lo, hi))
    return out


def load_capture(cap):
    fr, T = frames(cap / "obj.txt"), tiles(cap / "tiles.bin")
    org, box = {}, {}
    for line in open(cap / "origin.txt"):
        t = line.split()
        org[int(t[1])] = [int(v) for v in t[2:]]
    for line in open(cap / "boxes.txt"):
        t = line.split()
        box[int(t[1])] = int(t[3])        # origin y on screen (boxes.txt col 3)
    return fr, T, org, box


def sole_of(fr, T, f):
    objs = [o for o in fr.get(f, []) if (o[3] & 0x1f) in PALS and BODY[0] <= o[2] < BODY[1]]
    tl = expand(objs)
    s = None
    for px, py, c, hf, vf, pal in tl:
        if c not in T:
            continue
        t = T[c]
        for ry in range(16):
            if any(q != 15 for q in t[15 - ry if vf else ry]):
                s = py + ry if s is None else max(s, py + ry)
    return s


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    cap, adir = pathlib.Path(args[0]), pathlib.Path(args[1])
    rep = None
    if "--report" in sys.argv:
        rep = pathlib.Path(sys.argv[sys.argv.index("--report") + 1])
    A = json.loads((adir / "remap.json").read_text())
    raw = (adir / "gfx_wolverine.bin").read_bytes()
    sole = pose_sole(A, raw)
    stance = A.get("stance_pose", 17)
    base = sole[stance][0]
    dp = [s[0] - base for s in sole]              # down positive: sole above the stance's sole is negative
    fr, T, org, box = load_capture(cap)
    moves = A["moves_one"]
    ground, floor, lines = {}, {}, []
    for name, seq in moves.items():
        if name in SKIP:
            ground[name] = [0] * len(seq)
            floor[name] = [0] * len(seq)
            continue
        gs, fs = [], []
        f = WINDOWS[name][0] if name in WINDOWS and WINDOWS[name][0] < 100000 else None
        for pose, n, _a in seq:
            t = 0
            frames_a = []
            if f is not None and name not in FLOOR_ONLY:
                for g in range(f, f + n):
                    s = sole_of(fr, T, g)
                    if s is None or g not in box:
                        continue
                    frames_a.append(s - (box[g] + SOLE_BELOW_ORIGIN))
                if frames_a:
                    a = statistics.median(frames_a)
                    t = int(round(a)) if a < -TOL else 0
            if f is not None:
                f += n
            gv = t - dp[pose]
            gs.append(gv)
            fs.append(-dp[pose])
            lines.append((name, pose, n, dp[pose], t, gv, frames_a[:1] and (min(frames_a), max(frames_a))))
        ground[name] = gs
        floor[name] = fs
    # sole-exact jump (retime.build_jump's ticks, with the sole of the sampled frame instead of the pose bottom)
    tl, _ = TL.timeline(str(cap), os.environ.get("GROUND_TIMELINE_ASSETS", str(adir)), JUMP_FRAMES[0], JUMP_FRAMES[1])
    resident = {s[0] for m in moves.values() for s in m}
    n = len(tl)
    ticks, last = [], 25
    for t in range(JUMP_TICKS):
        f, p, _anc = tl[min(n - 1, t * n // JUMP_TICKS)]
        s = sole_of(fr, T, f)
        air = max(0, STANCE_SOLE_ROW - s) if s is not None else 0
        if isinstance(p, int) and p in resident:
            last = p
        ticks.append((last, air))
    steps = []
    for t, (p, air) in enumerate(ticks):
        if steps and steps[-1][0] == p:
            steps[-1][1] += 1
        else:
            steps.append([p, 1, air, air])
    for k in range(len(steps) - 1):
        steps[k][3] = steps[k + 1][2]
    steps[-1][3] = 0
    mj = moves["jump"]
    if [(s[0], s[1]) for s in steps] != [(s[0], s[1]) for s in mj]:
        raise SystemExit("jump steps of the capture do not match moves_one['jump']: %s vs %s" % (steps, mj))
    A["ground"] = ground          # feet on the floor, the original's deliberate lifts kept (hop, kick, pop-up)
    A["ground_floor"] = floor     # strict: every step's lowest opaque row on the floor line, no lifts
    A["jumpair"] = dict(steps=steps, dp=[dp[s[0]] for s in steps])
    (adir / "remap.json").write_text(json.dumps(A))
    if rep:
        out = ["move\tpose\tframes\tdp\tt\tg\tart_a(min,max)"] + ["\t".join(str(x) for x in l) for l in lines]
        out.append("jump steps [pose frames air_from air_to] dp: " + json.dumps(steps) + " " + json.dumps(A["jumpair"]["dp"]))
        rep.write_text("\n".join(out) + "\n")
    print("ground offsets", {m: g for m, g in ground.items()})
    print("jump air steps", steps)


if __name__ == "__main__":
    main()
