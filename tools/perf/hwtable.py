#!/usr/bin/env python
"""Summary of a profiling-Ymir dump (hwprof_*.txt): where each CPU's modelled cycles went, by phase and kind of stall, as a share of the window.

usage: hwtable.py PROF.txt [PROF2.txt ...]   (several dumps side by side: before and after)

Phases of the master: tasks (the game tick and the other tasks), irq (the vblank handler), idle (the task walk is done and the master spins). The slave has one.
Kinds: ifill/dfill = cache line fills of code/data, thru = cache-through reads, wstall = waits for the one-longword write buffer. The base cycles are what Ymir charged without
any memory wait. MODELLED figures need HW_MODEL=1 in the run; with it off the stall columns are 0 and only the access counts mean anything (EMULATED)."""
import collections
import sys

PH = {0: "master tasks", 2: "master irq", 3: "master idle", 1: "slave"}
KINDS = ["ifill", "dfill", "thru", "wstall"]


def load(path):
    cyc = collections.defaultdict(int)
    tot, ins, win = {}, {}, ""
    for l in open(path):
        t = l.split()
        if not t:
            continue
        if t[0] == "WINDOW":
            win = l.strip()
        elif t[0] == "CPU":
            ins[int(t[1])] = int(t[3]); tot[int(t[1])] = int(t[5])
        elif t[0] == "K" and t[2] in KINDS:
            cyc[(int(t[1]), t[2], t[3])] += int(t[7])
    return win, tot, ins, cyc


def main():
    files = sys.argv[1:]
    data = [load(f) for f in files]
    for f, (win, tot, ins, cyc) in zip(files, data):
        print(f"== {f}: {win}")
        master = tot.get(0, 0) + tot.get(2, 0) + tot.get(3, 0)
        print(f"   master cycles in the window {master} ({tot.get(0,0)} tasks, {tot.get(2,0)} irq, {tot.get(3,0)} idle); slave {tot.get(1,0)}")
        for c in (0, 2, 3, 1):
            if c not in tot:
                continue
            pen = sum(v for (cc, k, r), v in cyc.items() if cc == c)
            base = tot[c] - pen
            print(f"   {PH[c]:13s} instr {ins[c]:>11d}  base {base:>11d}  memory stalls {pen:>11d} ({100.0*pen/max(tot[c],1):.0f}% of its time)")
            for k in KINDS:
                row = {r: v for (cc, kk, r), v in cyc.items() if cc == c and kk == k and v}
                if row:
                    print(f"        {k:7s} " + "  ".join(f"{r} {v/1e6:.1f}M" for r, v in sorted(row.items(), key=lambda x: -x[1])))


main()
