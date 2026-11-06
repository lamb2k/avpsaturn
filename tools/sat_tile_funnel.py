#!/usr/bin/env python
"""VDP1 tile funnel and live sprite banks per frame over a golden MAME run, with sat_gfx's own rules. Tier: MAME data, counts only, no timing.
usage: sat_tile_funnel.py GOLDEN/probe.tsv PACK.BIN   Output counts only."""
import struct, sys
REC, OBJ = 8 + 64 + 0x10000 + 0x2000, 72 + 0x10000
pack = open(sys.argv[2], "rb").read()
n, ko, _ = struct.unpack_from(">III", pack, 4)
solid, blank = set(), set()
for i in range(n):
    v = struct.unpack_from(">I", pack, ko + i * 4)[0]
    (blank if (v & 0x3fff) == 0x3fff else solid).add(v >> 14)
rows = []
with open(sys.argv[1], "rb") as f:
    frame = 0
    while True:
        r = f.read(REC)
        if len(r) < REC: break
        o = r[OBJ:OBJ + 0x2000]
        tiles = off = empty = cmds = runs = 0
        banks = set()
        for i in range(0x400):
            xw, yw, cw, aw = struct.unpack_from(">4H", o, i * 8)
            if yw >= 0x8000 or aw >= 0xff00: break
            code = cw + ((yw & 0x6000) << 3)
            nx, ny, fx, fy = ((aw >> 8) & 15) + 1, ((aw >> 12) & 15) + 1, (aw >> 5) & 1, (aw >> 6) & 1
            x, y = xw, yw
            if aw & 0x80: x += 0x40; y += 0x10
            x += 64 - 0x40; y += 16 - 0x10
            for ty in range(ny):
                prev = -2
                for tx in range(nx):
                    tiles += 1
                    sx, sy = ((x + tx * 16) & 0x3ff) - 80, ((y + ty * 16) & 0x3ff) - 16
                    if sx <= -16 or sx >= 352 or sy <= -16 or sy >= 224: off += 1; continue
                    if fx or fy: t = code + (nx - 1 - tx if fx else tx) + 0x10 * (ny - 1 - ty if fy else ty)
                    else: t = (code & ~0xf) + ((code + tx) & 0xf) + 0x10 * ty
                    if t not in solid: empty += 1; continue
                    cmds += 1
                    if prev != tx - 1: runs += 1
                    prev = tx
                    banks.add(aw & 31)
        rows.append((cmds, tiles, off, empty, runs, len(banks), frame))
        frame += 1
def pct(k, p): return sorted(x[k] for x in rows)[int(len(rows) * p) - 1]
print("frames", len(rows))
for k, name in enumerate(("commands", "tiles", "offscreen", "empty", "runs", "banks")):
    print(name, "mean", round(sum(x[k] for x in rows) / len(rows), 1), "p95", pct(k, .95), "max", max(x[k] for x in rows))
for x in sorted(rows, reverse=True)[:6]:
    print("worst", dict(zip("commands tiles offscreen empty runs banks frame".split(), x)))
print("frames over 293 / 331 / 500:", [sum(x[0] > t for x in rows) for t in (293, 331, 500)])
