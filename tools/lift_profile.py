#!/usr/bin/env python
"""Rank lifted functions from a host instruction profile (host_kernel PROF=...). Tier: HOST 68000 instruction counts, not time.
usage: lift_profile.py PROF.tsv FRAMES [N]"""
import bisect, json, sys
funcs = sorted(json.load(open("E:/AvP/learning/cfg.json"))["funcs"])
frames, top = int(sys.argv[2]), int(sys.argv[3]) if len(sys.argv) > 3 else 40
n, seen = {}, {}
for l in open(sys.argv[1]):
    a, c = l.split()
    a, c = int(a, 16), int(c)
    f = funcs[bisect.bisect_right(funcs, a) - 1]
    n[f] = n.get(f, 0) + c
    seen[f] = max(seen.get(f, 0), c)
tot = sum(n.values())
print(f"total {tot} instructions, {tot / frames:.0f} per frame, {len(n)} functions")
cum = 0
for f, c in sorted(n.items(), key=lambda x: -x[1])[:top]:
    cum += c
    print(f"{f:6x} {c / frames:9.1f}/frame {100 * c / tot:5.1f}% cum {100 * cum / tot:5.1f}% entries~{seen[f] / frames:7.1f}")
