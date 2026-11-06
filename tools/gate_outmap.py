#!/usr/bin/env python
"""Classify fetched ROM words that the code map does not cover (exec_r1 probe, MAME). Prints counts and clusters."""
import json

d = json.load(open("E:/AvP/learning/cfg.json"))
S = {int(k, 16): v for k, v in d["seen"].items()}
cover = set()
for a, n in S.items():
    cover.update(range(a, a + n, 2))
c = {}
for l in open("E:/AvP/learning/mame/exec_r1/probe.tsv"):
    p = l.split()
    if p[0] != "F":
        c[int(p[0], 16)] = int(p[1])
tab = set()
for k, tg in d["tables"].items():
    t = int(k, 16)
    tab.update(range(t, t + max(len(tg) * 4, 2), 2))
import re, sys
sys.argv = ["x", "style"]
import importlib.util as iu
sp = iu.spec_from_file_location("cfg", "E:/AvP/worktrees/decomp-main/tools/learn_cfg68k.py")
m = iu.module_from_spec(sp)
sp.loader.exec_module(m)
pcd = set()
for a in S:
    for x in re.finditer(r"\$([0-9a-f]+)\(pc", m.insn(a).op_str):
        t = int(x[1], 16)
        if t not in S:
            e = t
            while e < t + 256 and e not in S:
                pcd.add(e)
                e += 2
out = sorted(a for a in c if a not in cover and a not in tab and a not in pcd)
pref = []
real = []
for a in out:
    near = any((a - k) in cover for k in (2, 4))
    (pref if near else real).append(a)
print("fetched words", len(c), "outside map", len(out), "within 4 bytes after mapped code (prefetch)", len(pref), "other", len(real))
print("prefetch-looking with count > 1000:", sum(1 for a in pref if c[a] > 1000))
cl = []
for a in real:
    if cl and a - cl[-1][1] <= 8:
        cl[-1][1] = a
    else:
        cl.append([a, a])
print("clusters of other", len(cl), [(hex(x), hex(y), max(c[k] for k in real if x <= k <= y)) for x, y in cl[:40]])
open("E:/AvP/learning/outmap_roots.txt", "w").write(" ".join(f"{x:x}" for x, _ in cl))
