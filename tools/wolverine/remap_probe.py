#!/usr/bin/env python
"""Lane wv-native3 11-10: probe of MSHvSF animation entries for the essentials remap (offline, ROM-derived output, never in git).
For each requested entry "sub.ent" it lists every record (index, ticks, tile cells, cells with no resident tile within the merge distance = tiles a swap would add) and writes a picture of
every record drawn from the raw arcade tiles (far tiles included), so the picks can be checked against the arcade frames.
usage: remap_probe.py WORK ASSETS_DIR MSHVSF_DUMP OUT_PREFIX SUB.ENT[,SUB.ENT...]     (the first four arguments as gen_native.py; the fifth is not used by gen_native: it is stripped here)"""
import sys, pathlib

src = pathlib.Path(__file__).resolve().parent / "gen_native.py"
wk, assets_dir, mvdir, outp, want = sys.argv[1:6]
sys.argv = [str(src), wk, assets_dir, mvdir, outp + ".unused.inc"]
text = src.read_text()
head = text.split("# first slot naming each distinct donor chain")[0]
head = head.split("if os.environ.get(\"WV_EXPLORE\"):")[0] + "\nSUBS = mv_tables()\nSRC_ADDR = {(si, ei): ts[ei] for si, (b, ts) in enumerate(SUBS) for ei in range(len(ts))}\n"
g = {"__name__": "gen_probe", "__file__": str(src)}
exec(compile(head, str(src), "exec"), g)
from PIL import Image, ImageDraw
import numpy as np

col = g["A"]["colours"][g["A"]["default_colour"]]
w, l, s16, s8, mv, gfx, assets, key_of, mv_chain, mv_boxes = (g[k] for k in ("w", "l", "s16", "s8", "mv", "gfx", "assets", "key_of", "mv_chain", "mv_boxes"))


def cells_of(rec):
    """[(cx, cy, code, hf, vf, pal, status)] status: 'blank', 'res' (resident key within K) or 'far' (no resident tile near)"""
    ap = l(mv, rec + 4); n = w(mv, ap + 4); tab = l(mv, ap + 6)
    px, py = s16(w(mv, tab + 2)), s16(w(mv, tab + 4))
    out = []
    for i in range(n + 1):
        if i:
            px += s8(mv[tab + 6 + 2 * (i - 1)]); py += s8(mv[tab + 7 + 2 * (i - 1)])
        code, at = w(mv, ap + 10 + 4 * i), w(mv, ap + 12 + 4 * i)
        wd, ht, hf, vf, pal = ((at >> 8) & 15) + 1, ((at >> 12) & 15) + 1, (at >> 5) & 1, (at >> 6) & 1, at & 0x1f
        for by in range(ht):
            for bx in range(wd):
                c = code + bx + 16 * by
                kk = key_of(c)
                cx = px + 16 * ((wd - 1 - bx) if hf else bx); cy = py + 16 * ((ht - 1 - by) if vf else by)
                out.append((cx, cy, c, hf, vf, pal, "blank" if kk is None else ("far" if kk == "far" else "res")))
    return out


def draw(cells, im, ox, oy):
    for cx, cy, c, hf, vf, pal, st in cells:
        if st == "blank": continue
        pxs = assets.pens(gfx[c * 128:c * 128 + 128])
        for yy in range(16):
            for xx in range(16):
                pv = pxs[15 - yy if vf else yy][15 - xx if hf else xx]
                if pv != 15:
                    X, Y = ox + cx + xx, oy + cy + yy
                    if 0 <= X < im.width and 0 <= Y < im.height:
                        rgb = col[1 if pal == 13 else 0][pv]
                        im.putpixel((X, Y), tuple(rgb) if st == "res" else (min(255, rgb[0] // 2 + 128), rgb[1] // 2, rgb[2] // 2 + 40))


rows = []
for t in want.split(","):
    si, ei = (int(x) for x in t.split("."))
    ch = mv_chain(g["SRC_ADDR"][(si, ei)])
    fr = []
    for k, r in enumerate(ch):
        cs = cells_of(r)
        far = sorted({x[2] for x in cs if x[6] == "far"})
        hit, hurt = mv_boxes(r)
        fr.append(dict(k=k, rec=hex(r), dur=w(mv, r + 2) & 0x7fff, cells=sum(1 for x in cs if x[6] != "blank"), far=len(far), far_codes=far, hit=hit))
        rows.append((t, k, cs))
    print("ENTRY %s: %d records; per record (index: ticks, cells, far, hit):" % (t, len(ch)))
    print("   " + "  ".join("%d:%dt/%dc/%df%s" % (f["k"], f["dur"], f["cells"], f["far"], "H" if f["hit"] else "") for f in fr))
W, H = 150, 140
img = Image.new("RGB", (W * 12, H * ((len(rows) + 11) // 12)), (40, 40, 48)); dr = ImageDraw.Draw(img)
for i, (t, k, cs) in enumerate(rows):
    ox, oy = (i % 12) * W + 75, (i // 12) * H + 105
    draw(cs, img, ox, oy)
    dr.text(((i % 12) * W + 2, (i // 12) * H + 2), "%s #%d" % (t, k), fill=(255, 255, 255))
img.save(outp + ".png"); print("png", outp + ".png", len(rows))
