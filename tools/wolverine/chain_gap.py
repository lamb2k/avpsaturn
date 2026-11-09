#!/usr/bin/env python
"""Which presses of tools/wolverine/chain_pacing.pad start a chain attack, from a guest trace (pacing.py trace format).
The pad script is four-press chains at gap g = 8..42 (step 2), then a held button and a 3-frame mash. For each chain group this prints the
stage each press produced (LP1 LP2 HP HK) or '-' when the press produced no new attack (still inside the previous one, i.e. the next-input
window had not opened or the chain ended). Ticks are vblanks from the pad script start (printed by the host runner as 'padscript start').
usage: chain_gap.py TRACE PADSTART [--pad chain_pacing.pad]"""
import argparse, pathlib
ap = argparse.ArgumentParser(); ap.add_argument("trace"); ap.add_argument("padstart", type=int)
ap.add_argument("--pad", default=str(pathlib.Path(__file__).with_name("chain_pacing.pad"))); ap.add_argument("--player", type=int, default=0)
a = ap.parse_args()
toks = pathlib.Path(a.pad).read_text().split()
t, presses = 0, []   # (script offset, group id)
grp, gap = -1, None
seq = []
for tok in toks:
    m, n = tok.split(":"); n = int(n)
    if m == "20" and n in (4, 2, 80) and (not seq or t - seq[-1] >= 2): seq.append(t)
    t += n
# groups of presses: first is the lone tap, then 18 chains of 4, then the held and mash ones
groups = [[seq[0]]]; i = 1
for g in range(8, 44, 2):
    groups.append(seq[i:i + 4]); i += 4
groups.append(seq[i:])  # mash
rec = {}
for l in open(a.trace):
    p = l.split()
    if len(p) >= 16 and int(p[2]) == a.player: rec[int(p[0])] = (int(p[1]), int(p[6]), int(p[12]), int(p[10]))
starts = []
prev = None
for v in sorted(rec):
    k, cur, cstg, wall = rec[v]
    if cur in (3, 4, 5) and (prev is None or prev[0] + 1 != v or prev[1] != cur or wall <= 2 and prev[3] > wall):
        starts.append((v, ("LP1", "LP2")[cstg] if cur == 3 and cstg < 2 else "LP2" if cur == 3 else "HP" if cur == 4 else "HK"))
    prev = (v, cur, cstg, wall)
def stage_for(v0):
    for s, n in starts:
        if v0 <= s <= v0 + 3: return n
    return "-"
print("gap  presses -> stages")
for gi, ps in enumerate(groups):
    names = [stage_for(a.padstart + p) for p in ps]
    label = "tap" if gi == 0 else ("g=%d" % (6 + 2 * gi) if gi <= 18 else "mash")
    if gi == 0: label = "single"
    print("%-7s %s" % (label, " ".join("%-3s" % n for n in names[:12])))
