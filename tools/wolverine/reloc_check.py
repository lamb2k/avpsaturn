#!/usr/bin/env python
"""Lane wv-native-gfx 11-09: data-level identity of a RELOCATED copy of Schaefer's animation block (plan V2 section 5, "relocated records holding donor-equivalent data").
Copies the block 0x162f90..0x167f20 (index tables, frame records, pose assemblies) verbatim to a window address (default 0x300000), changing only named pointer fields:
the 32-bit assembly pointer (record +4) and the jump target (record +16 of a jump record), each by the block's delta when it points into the block. Then, for every slot of the
index tables T1/T2/T3, walks the record chains through BOTH views (original image; relocated window) and compares, per record: duration, flags, box indexes, shadow, event bytes
(everything but the two pointer fields) and the object entries the game's emitter produces for the assembly (families 2, 4, 6, 0xA as avsp_emit.c) for several actor states
(facing 0/1, positions, camera, or_value). The decoded chain structure of a slot must also agree (same number of records, same jump shape).
This is a DATA tier check on the decrypted program image; it does not run the game, the page table or the lifted code (that is the HOST identity run, plan V2 section 5).
Nothing from the image is written out; the report has addresses and counts only.
usage: reloc_check.py ROM_IMAGE [WINDOW_HEX]"""
import json, sys

rom = open(sys.argv[1], "rb").read()
WIN = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x300000
LO, HI = 0x162f90, 0x167f20
D = WIN - LO
blk = bytearray(rom[LO:HI])


def w(b, a): return int.from_bytes(b[a:a + 2], "big")
def l(b, a): return int.from_bytes(b[a:a + 4], "big")
def s16(v): return v - 65536 if v >= 32768 else v


def view_orig(a, n): return rom[a:a + n]
def view_reloc(a, n):
    if WIN <= a < WIN + len(blk): return bytes(blk[a - WIN:a - WIN + n])
    assert not (LO <= a < HI), "read of the donor range through the relocated view: %x" % a
    return rom[a:a + n]


def rd16(v, a): return int.from_bytes(v(a, 2), "big")
def rd32(v, a): return int.from_bytes(v(a, 4), "big")


# ---- the relocation: walk every chain reachable from the tables, rewrite the two pointer fields
TABLES = ((0x162f90, 80), (0x163032, 32), (0x163074, 64), (0x1630f6, 16))
recs = {}
todo = [b + s16(w(rom, b + 2 * i)) for b, n in TABLES for i in range(n)]
while todo:
    a = todo.pop()
    while a not in recs:
        fl = w(rom, a + 2)
        recs[a] = fl
        if fl & 0x8000:
            t = l(rom, a + 16)
            if t not in recs: todo.append(t)
            break
        a += 16
changed = []
for a, fl in recs.items():
    off = a - LO
    p = l(rom, a + 4)
    if LO <= p < HI:
        blk[off + 4:off + 8] = (p + D).to_bytes(4, "big"); changed.append((a + 4, "asm"))
    if fl & 0x8000:
        t = l(rom, a + 16)
        assert LO <= t < HI
        blk[off + 16:off + 20] = (t + D).to_bytes(4, "big"); changed.append((a + 16, "jump"))
# a pointer outside the block (shared data) stays as is
outside = sum(1 for a in recs if not (LO <= l(rom, a + 4) < HI))
diff = sum(1 for i in range(len(blk)) if blk[i] != rom[LO + i])
named = len(changed) * 4
print("block %x..%x (%d bytes) -> %x; records %d; pointer fields rewritten %d (%d asm, %d jump); assembly pointers left outside the block %d; bytes differing from the donor %d (limit %d)" % (
    LO, HI, HI - LO, WIN, len(recs), len(changed), sum(1 for c in changed if c[1] == "asm"), sum(1 for c in changed if c[1] == "jump"), outside, diff, named))
assert diff <= named


# ---- the emitter (avsp_emit.c) through a view
def emit(v, asm, st):
    def origin(d2a):
        d2 = rd32(v, d2a); hi, lo = d2 >> 16, d2 & 0xffff
        y = (st["cz"] - st["z"] + 0x100) & 0xffff
        y = (y + lo if st["face"] & 2 else y - lo) & 0xffff
        x = (st["x"] - st["cx"] + 0x40) & 0xffff
        x = (x + hi if st["face"] & 1 else x - hi) & 0xffff
        return x, y
    def attr_final(r):
        flip = (st["face"] & 1) << 5
        if 1 <= st["mode"] <= 0x7f: return (r & 0xff00) | ((((r & 0xe0) + st["pal"]) ^ flip) & 0xff)
        return (r & 0xff00) | ((r ^ flip) & 0xff)
    def put(ox, oy, code, ar, dx, dy):
        a = attr_final(ar)
        if st["face"] & 1: x = (ox - ((((ar >> 8) & 15) + 1) * 16) - dx) & 0x3ff
        else: x = (ox + dx) & 0x3ff
        return (x | st["or"], (oy + dy) & 0x3ff, code, a)
    out = []
    top = rd16(v, asm); pos = asm; n = 1
    if top == 0xc: pos += 2; n = 2
    for _ in range(n):
        tag = rd16(v, pos)
        if tag in (4, 6):
            hdr = pos + 2; cnt = rd16(v, hdr + 2); sel = rd16(v, hdr + 4); adv = tag == 6
            a2 = 0x1fd1c8 + rd16(v, 0x1fd1c8 + sel * 2)
            ox, oy = origin(hdr + 6); a0 = hdr + 10
            for i in range(cnt):
                code, ar = rd16(v, a0), rd16(v, a0 + 2)
                ad = s16(rd16(v, a0 + 4)) if adv else 0
                out.append(put(ox, oy, code, ar, rd16(v, a2), rd16(v, a2 + 2)))
                a0 += 6 if adv else 4; a2 = a2 + 4 + ad
            pos = hdr + 10 + cnt * (6 if adv else 4)
        elif tag == 0xa:
            cnt = rd16(v, pos + 4); ox, oy = origin(pos + 8); p = pos + 12
            for i in range(cnt):
                out.append(put(ox, oy, rd16(v, p), rd16(v, p + 2), rd16(v, p + 4), rd16(v, p + 6))); p += 8
            pos = p
        elif tag == 2:
            pl = pos + 4; ar = rd16(v, pl); sel = rd16(v, pl + 2)
            a2 = 0x1fd1c8 + rd16(v, 0x1fd1c8 + sel * 2); ox, oy = origin(pl + 4)
            out.append(put(ox, oy, rd16(v, pl + 8), ar, rd16(v, a2), rd16(v, a2 + 2))); pos += 14
        elif tag == 8: pos += 4
        else: raise ValueError("tag %x at %x" % (tag, pos))
    return out


STATES = [dict(x=x, z=z, cx=cx, cz=0x100, face=f, mode=0, pal=0, **{"or": o}) for x in (0x3b0, 0x9c0) for z in (0x14, 0x40) for cx in (0, 0x200) for f in (0, 1) for o in (0, 0x8000)]


def chain(v, a):
    out, seen = [], set()
    while a not in seen:
        seen.add(a)
        rec = v(a, 16)
        out.append((a, rec))
        fl = int.from_bytes(rec[2:4], "big")
        if fl & 0x8000: out.append(("jump", rd32(v, a + 16))); break
        a += 16
    return out


bad = 0; checked = 0; objs = 0
for tb, n in TABLES:
    for i in range(n):
        so = tb + s16(w(rom, tb + 2 * i))
        sr = (tb + D) + s16(rd16(view_reloc, tb + D + 2 * i))
        co, cr = chain(view_orig, so), chain(view_reloc, sr)
        if len(co) != len(cr): bad += 1; print("slot shape differs", hex(tb), i); continue
        for (ao, ro), (ar, rr) in zip(co, cr):
            if ao == "jump":
                if rr != ro + D: bad += 1; print("jump target", hex(tb), i)
                continue
            # everything but the two pointer fields must be equal
            if ro[:4] != rr[:4] or ro[8:] != rr[8:]: bad += 1; print("record content", hex(ao)); continue
            po, pr = int.from_bytes(ro[4:8], "big"), int.from_bytes(rr[4:8], "big")
            for st in STATES:
                eo, er = emit(view_orig, po, st), emit(view_reloc, pr, st)
                objs += len(eo)
                if eo != er: bad += 1; print("objects differ", hex(ao)); break
            checked += 1
print("slots %d, records compared %d, emitted object entries compared %d, mismatches %d" % (sum(n for _, n in TABLES), checked, objs, bad))
sys.exit(1 if bad else 0)
