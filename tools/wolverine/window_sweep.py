#!/usr/bin/env python
"""Next-input window sweep. gen: writes a pad script of trials; each trial presses attack for 4 frames at offset 0 and again at the offsets of its list
(4-frame presses), then rests 120 frames. check: reads a guest trace (pacing.py format) and prints, for each trial, the attacks that started
(offset from the first press, stage). Stage 1->2 trials sweep the second press K = 6..40; stage 2->3 trials put the second press at P2 (first K that gave
an LP2 in the 1->2 sweep, argument --p2) and sweep the third; 3->4 likewise with --p3.
Each trial is its own host run from the start of stage 02 (enemies reach the player about 240 vblanks after the pad script starts, so a trial is
short): gen DIR writes DIR/t<N>.pad and DIR/trials.json, the runner writes DIR/tr_<N>.txt, check DIR reads them.
usage: window_sweep.py gen DIR [--p2 N --p3 N]    |    window_sweep.py check DIR PADSTART"""
import argparse, json, pathlib, sys
ap = argparse.ArgumentParser()
ap.add_argument("mode"); ap.add_argument("a"); ap.add_argument("b", nargs="?"); ap.add_argument("c", nargs="?")
ap.add_argument("--p2", type=int, default=0); ap.add_argument("--p3", type=int, default=0)
ap.add_argument("--hold", type=int, default=4)
ap.add_argument("--k0", type=int, default=6); ap.add_argument("--k1", type=int, default=40)
a = ap.parse_args()
H = a.hold
if a.mode == "gen":
    d = pathlib.Path(a.a); d.mkdir(parents=True, exist_ok=True)
    trials = []
    def trial(offs):
        tok, cur = ["00:30"], 0
        for o in offs:
            if o > cur: tok.append("00:%d" % (o - cur)); cur = o
            tok.append("20:%d" % H); cur += H
        tok.append("00:140")
        (d / ("t%d.pad" % len(trials))).write_text(" ".join(tok))
        trials.append(offs)
    for k in range(a.k0, a.k1 + 1): trial([0, k])
    if a.p2:
        for k in range(a.p2 + a.k0, a.p2 + a.k1 + 1): trial([0, a.p2, k])
    if a.p2 and a.p3:
        for k in range(a.p2 + a.p3 + a.k0, a.p2 + a.p3 + a.k1 + 1): trial([0, a.p2, a.p2 + a.p3, k])
    (d / "trials.json").write_text(json.dumps(trials))
    print("trials", len(trials))
else:
    d = pathlib.Path(a.a); trials = json.loads((d / "trials.json").read_text()); padstart = int(a.b)
    for n, offs in enumerate(trials):
        f = d / ("tr_%d.txt" % n)
        rec = {}
        if f.exists():
            for l in open(f):
                p = l.split()
                if len(p) >= 16 and int(p[2]) == 0: rec[int(p[0])] = (int(p[6]), int(p[12]), int(p[10]))
        starts, prev = [], None
        for v in sorted(rec):
            cur, cstg, wall = rec[v]
            if cur in (3, 4, 5) and (prev is None or prev[0] + 1 != v or prev[1] != cur or (wall <= 2 and prev[3] > wall)):
                starts.append((v, "LP1" if cur == 3 and cstg == 0 else "LP2" if cur == 3 else "HP" if cur == 4 else "HK"))
            prev = (v, cur, cstg, wall)
        got = [(s - padstart - 30, nm) for s, nm in starts]
        print("presses at %s -> %s" % (offs, " ".join("%s@%d" % (nm, dd) for dd, nm in got)))
