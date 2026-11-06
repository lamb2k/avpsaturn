#!/usr/bin/env python
"""Rank the SH-2 PC samples from a SAT_PROF_PC run by symbol. Tier: EMULATOR PC samples, MODELLED timing.
usage: sat_pc_rank.py WORK [N]"""
import bisect, os, pathlib, struct, subprocess, sys
W = pathlib.Path(sys.argv[1]); top = int(sys.argv[2]) if len(sys.argv) > 2 else 40
NM = os.environ.get("NM", "E:/AvP/worktrees/saturn-hw/.deps/joengine/Compiler/WINDOWS/sh-elf/bin/nm.exe")
syms = sorted((int(p[0], 16), p[2]) for p in (l.split() for l in subprocess.run([NM, str(W / "sat.elf")], capture_output=True, text=True).stdout.splitlines()) if len(p) == 3 and p[1] in "tT")
keys = [s[0] for s in syms]
raw = (W / "pcs.bin").read_bytes()
pcs = struct.unpack(f">{len(raw) // 4}I", raw)
def name(a):
    i = bisect.bisect_right(keys, a) - 1
    return syms[i][1].lstrip("_") if i >= 0 else hex(a)
def region(a):
    return "hw" if 0x06000000 <= a < 0x06100000 else "lw" if 0x00200000 <= a < 0x00300000 else "cart" if 0x02400000 <= a < 0x02800000 else "other"
n, reg = {}, {}
for pc in pcs[::2]:
    k = name(pc); n[k] = n.get(k, 0) + 1
    r = region(pc); reg[r] = reg.get(r, 0) + 1
tot = len(pcs) // 2
print("samples", tot, "regions", reg)
cum = 0
for k, c in sorted(n.items(), key=lambda x: -x[1])[:top]:
    cum += c
    print(f"{k:24s} {c:5d} {100 * c / tot:5.1f}% cum {100 * cum / tot:5.1f}%")
