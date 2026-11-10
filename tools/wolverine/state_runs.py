#!/usr/bin/env python
"""Run lengths (vblanks) of player-1 states in host PDUMP files (host_kernel.c PDUMP): state_runs.py STATE FILE [FILE ...]  STATE = 6 hex digits, e.g. 020004"""
import sys
st = tuple(int(sys.argv[1][i:i + 2], 16) for i in (0, 2, 4))
for f in sys.argv[2:]:
    d = open(f, "rb").read(); n = len(d) // 532
    out, cur = [], 0
    for k in range(n):
        b = d[k * 532:k * 532 + 256]
        if (b[4], b[5], b[6]) == st: cur += 1
        elif cur: out.append(cur); cur = 0
    print(f.split("/")[-1], sys.argv[1], "runs", out[:16], "total", sum(out))
