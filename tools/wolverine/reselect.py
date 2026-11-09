#!/usr/bin/env python
"""Lane avp-wolverine-b: pick Wolverine's pose set again from an assets.py output, without a new MAME capture.
assets.py writes every pose's tiles into gfx_wolverine.bin and the whole move lists ("moves") into remap.json, then trims the set to one budget
("moves_one", "stage_keys"). The trimmed walk had 5 poses held 18-21 frames each, and the trimmed hp lost its middle poses (owner 11-08: his walk and
slash stutter). Here the moves named in FULL keep every pose of their capture (the required poses of every other move stay, as in assets.py), then the
rest fill up to BUDGET tiles in assets.py's order. The fit gate is tools/wolverine/fit.py on the result.
HIT8=0 leaves out the hitstun poses held 8+ frames that assets.py keeps (188 tiles).
usage: reselect.py IN_DIR OUT_DIR FULL_MOVES(comma list, or 'all'; 'walk/2' keeps every 2nd pose of walk) [BUDGET (tiles, default: no fill)]
OUT_DIR gets remap.json (new moves_one, stage_keys, one_set) and a copy of gfx_wolverine.bin; run boxes.py on it after (boxes.json follows moves_one)."""
import json, os, pathlib, shutil, sys

src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
full_names = sys.argv[3].split(",") if sys.argv[3] != "all" else None
budget = int(sys.argv[4]) if len(sys.argv) > 4 else 0
A = json.loads((src / "remap.json").read_text())
P, moves, keys = A["poses"], A["moves"], A["keys"]
if full_names is None:
    full_names = list(moves)
por = {e[2] for v in A["portraits"].values() for e in v}
seen, fresh = set(), {}
for name, seq in moves.items():
    fresh[name] = [x for x in dict.fromkeys(q[0] for q in seq) if x not in seen] if name != "idle" else list(dict.fromkeys(q[0] for q in seq))
    seen |= {q[0] for q in seq}
hold = {}
for seq in moves.values():
    for pid, n, _ in seq:
        hold[pid] = max(hold.get(pid, 0), n)
need = set()
for name, fr_ in fresh.items():
    if fr_:
        need |= {fr_[0], max(fr_, key=lambda i: hold[i]), fr_[-1]}
        if name == "hit_etc" and os.environ.get("HIT8", "1") == "1":
            need |= {i for i in fr_ if hold[i] >= 8}
cost = lambda ids: len(por | {e[2] for i in ids for e in P[i]})
for spec in full_names:   # "walk/2": every 2nd pose of that move's own poses (plus its first and last), the rest merge into the pose before
    m, _, every = spec.partition("/")
    plist = list(dict.fromkeys(p for p, _, _ in moves[m]))
    step = int(every) if every else 1
    need |= {p for j, p in enumerate(plist) if j % step == 0 or j == len(plist) - 1}
print("required + full", full_names, "poses", len(need), "tiles", cost(need))
if budget:
    names = ["walk"] + [m for m in fresh if m != "walk"]
    progress = True
    while progress:
        progress = False
        for m in names:
            fr_ = fresh[m]
            cand = [j for j, i in enumerate(fr_) if i not in need]
            if not cand:
                continue
            kept = [j for j, i in enumerate(fr_) if i in need]
            j = max(cand, key=lambda j: min(abs(j - k) for k in kept) if kept else 0)
            if cost(need | {fr_[j]}) <= budget:
                need.add(fr_[j]); progress = True
have = por | {e[2] for i in need for e in P[i]}
mt = {}
for name, seq in moves.items():
    o = []
    for pid, n, anc in seq:
        if pid in need or not o:
            o.append([pid, n, anc])
        else:
            o[-1][1] += n
    mt[name] = o
A["moves_one"] = mt
A["stance_pose"] = 17   # the capture's ready stance (loop 17..24 then idle 0..4 follows every attack): an attack's recovery ends where it first appears after the last attack frame
A["one_set"] = dict(budget=budget, full=full_names, tiles=len(have), poses=len(need))
A["stage_keys"] = {f"{st:02x}": sorted(keys[i] for i in have) for st in range(2, 0x28, 2)}
out.mkdir(parents=True, exist_ok=True)
(out / "remap.json").write_text(json.dumps(A))
if not (out / "gfx_wolverine.bin").exists():
    shutil.copy(src / "gfx_wolverine.bin", out / "gfx_wolverine.bin")
print("one set", A["one_set"], {m: (len({x[0] for x in q}), len(moves[m])) for m, q in mt.items()})
