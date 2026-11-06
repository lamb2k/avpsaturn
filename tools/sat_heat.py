#!/usr/bin/env python
"""Chunk heat for build.py's placement from a host instruction profile (host_kernel PROF=...). Tier: HOST 68000 instruction counts.
usage: sat_heat.py WORK PROF.tsv     writes WORK/heat.json; keeps the old file as heat_census.json."""
import bisect, json, pathlib, re, shutil, sys
W = pathlib.Path(sys.argv[1])
ent = []
for s in W.glob("src/c*.c"):
    ent += [(int(m, 16), s.stem) for m in re.findall(r"^void f_([0-9a-f]+)\(void\)\{", s.read_text(), re.M)]
ent.sort()
keys = [e[0] for e in ent]
heat = {e[1]: 0 for e in ent}
for l in open(sys.argv[2]):
    a, c = l.split()
    i = bisect.bisect_right(keys, int(a, 16)) - 1
    if i >= 0:
        heat[ent[i][1]] += int(c)
if not (W / "heat_census.json").exists():
    shutil.copy(W / "heat.json", W / "heat_census.json")
(W / "heat.json").write_text(json.dumps(heat))
for k, v in sorted(heat.items(), key=lambda x: -x[1]):
    print(k, v)
