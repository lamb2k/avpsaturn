#!/usr/bin/env python
"""Lane wv-native-gfx 11-09: draw his native records as the game will (pose assembly + the record's hurt and attack boxes from T') with the boxes outlined, to check the claws against the attack box.
Reads the generated block (WORK/gen/wv_native.bin and .inc from gen_native.py) and the guest assets; writes a contact sheet PNG. ROM-derived: the picture stays on this PC.
Geometry as the game draws it: object origin O at the actor's x; the emitter puts the feet line 11 px below the origin's row (D2 lo 0xfff5); the pose is the unflipped (facing 0, left) look. A box record is
x (backward positive, so on screen to the right of O when facing left), y up from the feet, half width, half height.
usage: native_overlay.py GEN_DIR ASSETS_DIR OUT.png [RECORD_ADDR ...]   default: the idle, walk and attack records, in chain order"""
import json, pathlib, re, sys
from PIL import Image, ImageDraw

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import assets

gen, adir, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3])
blk = (gen / "wv_native.bin").read_bytes()
inc = (gen / "wv_native.inc").read_text()
const = lambda n: int(re.search(r"#define %s (0x[0-9a-f]+|\d+)u?" % n, inc)[1], 0)
WIN, LO, END, T = const("WV_NAT_WIN"), const("WV_NAT_REC_LO"), const("WV_NAT_REC_END"), const("WV_NAT_T")
A = json.loads((adir / "remap.json").read_text())
raw = (adir / "gfx_wolverine.bin").read_bytes()
col = A["colours"][A["default_colour"]]
_m = re.search(r"wv_nat_p1\[\d+\] = \{([0-9,]*)\}", inc)
p1 = set(int(v) for v in _m[1].split(",")) if _m else None   # older blocks list the second-row tiles; current ones mark them in the assembly itself (attribute low byte 0 = second row, written by the runtime)
w = lambda o: int.from_bytes(blk[o:o + 2], "big")
l = lambda o: int.from_bytes(blk[o:o + 4], "big")
s16 = lambda v: v - 65536 if v >= 32768 else v
s8 = lambda v: v - 256 if v >= 128 else v
recs = []
o = LO - WIN
while o < END - WIN:
    recs.append(o)
    o += 20 if w(o + 2) & 0x8000 else 16
sel = [int(a, 0) - WIN for a in sys.argv[4:]] or recs
Wd, Ht, OX, FEET = 200, 190, 100, 160


def tile(k):
    return assets.pens(raw[k * 128:k * 128 + 128])


sheet = Image.new("RGB", (Wd * min(len(sel), 8), Ht * ((len(sel) + 7) // 8)), (40, 40, 48))
d = ImageDraw.Draw(sheet)
for n, r in enumerate(sel):
    cx, cy = (n % 8) * Wd, (n // 8) * Ht
    ap = l(r + 4) - WIN
    cnt = w(ap + 4)
    for i in range(cnt):
        po = ap + 12 + 8 * i
        key, at, dx, dy = w(po), w(po + 2), s16(w(po + 4)), s16(w(po + 6))
        hf, vf = at >> 5 & 1, at >> 6 & 1
        pal = col[1 if ((po + 3) in p1 if p1 is not None else not at & 1) else 0]
        px = tile(key)
        for y in range(16):
            for x in range(16):
                p = px[y][x ^ 15 if hf else x] if not vf else px[15 - y][x ^ 15 if hf else x]
                if p != 15:
                    X, Y = cx + OX + dx + x, cy + FEET - 16 + dy + 16 + x * 0 + y   # dy is relative to the pose's bottom row (-16 for the lowest tile)
                    if 0 <= X < sheet.width and 0 <= Y < sheet.height:
                        sheet.putpixel((X, Y), tuple(pal[p]))
    ho, ao = r and blk[r + 8], blk[r + 9]
    ta, tb = T + 0, T
    toff = T - WIN
    hurt0, atk0 = toff + s16(w(toff)), toff + s16(w(toff + 2))   # biased offsets (entries below the lowest used index are not stored)
    for idx, base, size, colr in ((blk[r + 8], hurt0, 8, (60, 200, 255)), (blk[r + 9], atk0, 16, (255, 60, 60))):
        if idx:
            e = base + idx * size
            xb, yb, hw, hh = s8(blk[e]), s8(blk[e + 1]), blk[e + 2], blk[e + 3]
            d.rectangle([cx + OX + xb - hw, cy + FEET - yb - hh, cx + OX + xb + hw, cy + FEET - yb + hh], outline=colr)
    d.line([cx + OX, cy + FEET - 6, cx + OX, cy + FEET + 4], fill=(255, 255, 0))   # the actor's x
    d.line([cx, cy + FEET, cx + Wd - 1, cy + FEET], fill=(90, 90, 90))
    d.text((cx + 3, cy + 3), "%x dur %d f %04x h%d a%d" % (WIN + r, w(r), w(r + 2), blk[r + 8], blk[r + 9]), fill=(255, 255, 255))
out.parent.mkdir(parents=True, exist_ok=True)
sheet.save(out)
print("records drawn", len(sel), "->", out)
