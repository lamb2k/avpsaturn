#!/usr/bin/env python
"""Lane wv-native-gfx 11-09: check the decode of MSHvSF's own animation data against what MAME drew (data-source assessment, design note section 3b).
Inputs: the dump of tools/wolverine/mshvsf_dump.lua (prog_data.bin, ram_NNNNN.bin, obj_NNNNN.txt) under E:/AvP/learning; ROM-derived, never in git.
Format decoded (MSHvSF program ROM, data view, big-endian):
  player 1 block 0xff3800: +0x34 current frame record, +0x38 next, +0x3c timer, +0x68 box-id table base, +0x6c box geometry table, +0x70..0x7a current box ids
  frame record, 16 bytes (20 with a jump target): +0 u16 flags, +2 u16 duration (bit 15 = jump record, u32 target at +16), +4 u32 assembly, +8 u32 flags, +12 u32 box-set index
  assembly: [0002][cell budget][pair count n][u32 position table], then n + 1 parts of [code][attr] (attr: height-1 << 12, width-1 << 8, flips 0x60, palette 0x1f)
  position table: [0002][s16 x0][s16 y0] then n pairs of s8 (dx, dy): each part sits at the previous part's position plus the pair; a facing-left actor draws x = origin - width - cumulative x
For each given frame the part positions the table predicts are compared with the object list MAME wrote (relative to the first part).
usage: mshvsf_verify.py DUMP_DIR FRAME [FRAME ...]"""
import sys

D = sys.argv[1].rstrip("/") + "/"
d = open(D + "prog_data.bin", "rb").read()
w = lambda a: int.from_bytes(d[a:a + 2], "big")
l = lambda a: int.from_bytes(d[a:a + 4], "big")
s8 = lambda v: v - 256 if v >= 128 else v
s16 = lambda v: v - 65536 if v >= 32768 else v
ok = bad = 0
for f in map(int, sys.argv[2:]):
    ram = open(D + "ram_%05d.bin" % f, "rb").read()[0x3800:]
    rec = int.from_bytes(ram[0x34:0x38], "big")
    ap = l(rec + 4)
    n, tab = w(ap + 4), l(ap + 6)
    ps = [(w(ap + 10 + 4 * i), w(ap + 12 + 4 * i)) for i in range(n + 1)]
    pos = [(s16(w(tab + 2)), s16(w(tab + 4)))]
    for i in range(n):
        px, py = pos[-1]
        pos.append((px + s8(d[tab + 6 + 2 * i]), py + s8(d[tab + 7 + 2 * i])))
    objs = [tuple(int(v, 16) for v in ln.split()) for ln in open(D + "obj_%05d.txt" % f)]
    idx = [i for i, o in enumerate(objs) if o[2] == ps[0][0] and [x[2] for x in objs[i:i + len(ps)]] == [c for c, _ in ps]]
    if not idx:
        print(f, "record %x: its parts are not in the object list (the record changed after the draw)" % rec)
        continue
    seg = objs[idx[0]:idx[0] + len(ps)]
    hflip = (seg[0][3] >> 5 & 1) ^ (ps[0][1] >> 5 & 1)
    w0 = (((ps[0][1] >> 8) & 15) + 1) * 16
    for k, ((px, py), (c, at), o) in enumerate(zip(pos, ps, seg)):
        wd = (((at >> 8) & 15) + 1) * 16
        ex, ey = px - pos[0][0], py - pos[0][1]
        pred = (w0 - wd - ex, ey) if hflip else (ex, ey)
        got = ((o[0] & 0x3ff) - (seg[0][0] & 0x3ff), (o[1] & 0x3ff) - (seg[0][1] & 0x3ff))
        if pred == got: ok += 1
        else: bad += 1; print(f, "part", k, "predicted", pred, "drawn", got)
    print(f, "record %x assembly %x parts %d facing-left %d" % (rec, ap, len(ps), hflip))
print("part positions matching %d, not matching %d" % (ok, bad))
sys.exit(1 if bad else 0)
