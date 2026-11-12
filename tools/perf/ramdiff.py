#!/usr/bin/env python
"""Exactness check of a placement or speed change: compares the game RAM images (RAMB, 64 KB, the 68000's work RAM) that the profiling Ymir dumps at the start of chosen game ticks
(HW_DUMP_TICKS=n,n,...; ram_<TAG>_<tick>.bin in the Ymir directory). Same disc source, same scripted pad (SAT_INPUT_SCRIPT), same tick: the images must be equal.

usage: ramdiff.py DIR TAG_A TAG_B [tick ...]   (all ticks both tags have)
Prints, per tick, the number of differing bytes and the first differing ranges (offset in the 68000's space, 0xff0000 + offset). A few bytes owned by the vblank interrupt
(its tick and countdown counters, ff8018 and neighbours) can differ when a build's timing moves a vblank across a tick start; anything else differing is a behaviour change."""
import glob
import os
import re
import sys


def main():
    d, a, b = sys.argv[1], sys.argv[2], sys.argv[3]
    want = {int(x) for x in sys.argv[4:]}
    ticks = lambda t: {int(m.group(1)): f for f in glob.glob(os.path.join(d, f"ram_{t}_*.bin")) for m in [re.fullmatch(re.escape(f"ram_{t}_") + r"(\d+)\.bin", os.path.basename(f))] if m}
    ta, tb = ticks(a), ticks(b)
    common = sorted(set(ta) & set(tb))
    if want:
        common = [t for t in common if t in want]
    if not common:
        print("no common ticks", sorted(ta), sorted(tb))
        sys.exit(2)
    bad = 0
    for t in common:
        x, y = open(ta[t], "rb").read(), open(tb[t], "rb").read()
        diff = [i for i in range(min(len(x), len(y))) if x[i] != y[i]]
        runs, st = [], None
        for i in diff:
            if st is None or i > st[1] + 3:
                if st: runs.append(st)
                st = [i, i]
            else:
                st[1] = i
        if st: runs.append(st)
        print(f"tick {t}: {len(diff)} differing bytes in {len(runs)} runs; sizes {len(x)} {len(y)}" + ("" if not runs else "; first " + ", ".join(f"ff{r[0]:04x}-ff{r[1]:04x}" for r in runs[:12])))
        bad += len(diff)
    print("IDENTICAL" if not bad else f"DIFFERENT ({bad} bytes)")
    sys.exit(1 if bad else 0)


main()
