#!/usr/bin/env python
"""Lane chars: one image for all routes. Unions OP read logs (tools/lift_runner/oplog.sh output and .ranges) and census oreads into WORK, ready for tools/satint_merge.py.
usage: rounds_union.py WORK CENSUS.json OPLOGDIR   Each OPLOGDIR/*.txt with its .ranges is one golden. Ranges for one base take the widest. ROM-derived: E:/AvP/learning only."""
import glob, json, pathlib, sys
W, C, D = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3]
seen, R = set(), {}
for f in glob.glob(D + "/*.txt"):
    seen |= set(open(f).read().split())
    for l in open(f + ".ranges"):
        b, lo, hi = (int(x, 16) for x in l.split())
        o = R.get(b, (lo, hi))
        R[b] = (min(lo, o[0]), max(hi, o[1]))
(W / "opdata.txt").write_text("\n".join(sorted(seen)) + "\n")
(W / "opdata.txt.ranges").write_text("".join(f"{b:x} {lo:x} {hi:x}\n" for b, (lo, hi) in sorted(R.items())))
p = W / "oreads/oreads.txt"
old = set(p.read_text().split())
new = {f"{a:x}" for a in json.load(open(C))["oreads"]}
p.write_text("\n".join(sorted(old | new)) + "\n")
print("op bytes", len(seen), "bases", len(R), "oreads", len(old), "->", len(old | new))
