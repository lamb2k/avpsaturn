#!/usr/bin/env python
"""Print a LEARN_DELTA golden's IRQ records: interrupted PC, registers, and changed words in a window of work RAM.
usage: golden_delta_show.py PROBE.TSV FIRST LAST [LO HI]   LO, HI: hex work RAM addresses (default ff0058 ff0a80). Output has RAM values: not for commit."""
import struct, sys
first, last = int(sys.argv[2]), int(sys.argv[3])
lo, hi = (int(sys.argv[4], 16), int(sys.argv[5], 16)) if len(sys.argv) > 5 else (0xff0058, 0xff0a80)
with open(sys.argv[1], "rb") as f:
    while True:
        h = f.read(8 + 64 + 4)
        if len(h) < 76:
            break
        n = struct.unpack_from(">I", h, 4)[0]
        r = struct.unpack_from(">16I", h, 8)
        runs = struct.unpack_from(">I", h, 72)[0]
        ch = []
        for _ in range(runs):
            b, w = struct.unpack(">HH", f.read(4))
            d = f.read(w * 4)
            if first <= n <= last and b < 0x4000:
                for i in range(w):
                    a = 0xff0000 + (b + i) * 4
                    if lo <= a < hi:
                        ch.append(f"{a:x}={d[i * 4:i * 4 + 4].hex()}")
        if first <= n <= last:
            print(n, f"pc {r[0]:x} d0 {r[1]:x} d1 {r[2]:x} a0 {r[9]:x} a4 {r[13]:x} a6 {r[15]:x}", " ".join(ch))
        if n > last:
            break
