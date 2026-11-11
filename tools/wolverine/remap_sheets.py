#!/usr/bin/env python
"""Lane wv-native3 11-10: before / after pose sheets of the essentials remap, one row per changed state (offline, ROM-derived output, never in git).
Columns: ARCADE (the MSHvSF frames the row maps to, drawn from the raw arcade tiles), BEFORE (the records of the state's slot in the 11-10 block, WV_REMAP=0 on D11) and AFTER (the same slot in the
remapped block, D12). Each native pose is drawn as the game draws it (pose assembly, palette rows, feet line); the arcade frames use the same feet line.
usage: remap_sheets.py WORK BEFORE_GEN BEFORE_ASSETS AFTER_GEN AFTER_ASSETS MSHVSF_DUMP OUT.png     (GEN dirs hold wv_native.bin, .inc and .roles.txt of gen_native.py)"""
import json, pathlib, re, sys

wk, bgen, bas, agen, aas, mvdir, outp = sys.argv[1:8]
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
src = pathlib.Path(__file__).resolve().parent / "gen_native.py"
sys.argv = [str(src), wk, bas, mvdir, outp + ".unused.inc"]
head = src.read_text().split("# first slot naming each distinct donor chain")[0]
head = head.split("if os.environ.get(\"WV_EXPLORE\"):")[0].split("if os.environ.get(\"WV_ADD\"):")[0]
g = {"__name__": "gen_sheets", "__file__": str(src)}
exec(compile(head, str(src), "exec"), g)
from PIL import Image, ImageDraw
import assets

w_, l_, s16, s8, mv, gfx = (g[k] for k in ("w", "l", "s16", "s8", "mv", "gfx"))
mv_chain, SRC_ADDR = g["mv_chain"], g["SRC_ADDR"]
FEETLINE = 118   # canvas row of the feet line
CW, CH = 130, 140

TABLES = {"T1": 0, "T0": 0x163032 - 0x162f90, "T2": 0x163074 - 0x162f90, "T3": 0x1630f6 - 0x162f90}


def load(gdir, adir):
    gdir, adir = pathlib.Path(gdir), pathlib.Path(adir)
    blk = (gdir / "wv_native.bin").read_bytes()
    inc = (gdir / "wv_native.inc").read_text()
    WIN = int(re.search(r"#define WV_NAT_WIN (0x[0-9a-f]+)", inc)[1], 0)
    A = json.loads((adir / "remap.json").read_text())
    return dict(blk=blk, WIN=WIN, raw=(adir / "gfx_wolverine.bin").read_bytes(), col=A["colours"][A["default_colour"]])


def native_chain(S, slot):
    t, i = slot.split("."); i = int(i)
    blk = S["blk"]; w = lambda o: int.from_bytes(blk[o:o + 2], "big"); l = lambda o: int.from_bytes(blk[o:o + 4], "big")
    base = TABLES[t]
    a = base + s16(w(base + 2 * i))
    out = []
    for _ in range(40):
        out.append(a)
        if w(a + 2) & 0x8000: break
        a += 16
    return out


def draw_native(S, r, im, ox, oy):
    blk, WIN, raw, col = S["blk"], S["WIN"], S["raw"], S["col"]
    w = lambda o: int.from_bytes(blk[o:o + 2], "big"); l = lambda o: int.from_bytes(blk[o:o + 4], "big")
    ap = l(r + 4) - WIN
    for i in range(w(ap + 4)):
        po = ap + 12 + 8 * i
        key, at, dx, dy = w(po), w(po + 2), s16(w(po + 4)), s16(w(po + 6))
        hf, vf = at >> 5 & 1, at >> 6 & 1
        pal = col[0 if at & 1 else 1]   # attribute low byte 1 = row 1; 0 = the second row (written by the runtime)
        px = assets.pens(raw[key * 128:key * 128 + 128])
        for y in range(16):
            for x in range(16):
                p = px[15 - y if vf else y][15 - x if hf else x]
                if p != 15:
                    X, Y = ox + dx + x, oy + dy + 16 + y   # dy is relative to the feet line less 16 (the emitter's 0xfff5 offset is part of the stored dy)
                    if 0 <= X < im.width and 0 <= Y < im.height: im.putpixel((X, Y), tuple(pal[p]))


def draw_arcade(rec, im, ox, oy):
    col = g["A"]["colours"][g["A"]["default_colour"]]
    ap = l_(mv, rec + 4); n = w_(mv, ap + 4); tab = l_(mv, ap + 6)
    px, py = s16(w_(mv, tab + 2)), s16(w_(mv, tab + 4))
    for i in range(n + 1):
        if i:
            px += s8(mv[tab + 6 + 2 * (i - 1)]); py += s8(mv[tab + 7 + 2 * (i - 1)])
        code, at = w_(mv, ap + 10 + 4 * i), w_(mv, ap + 12 + 4 * i)
        wd, ht, hf, vf, pal = ((at >> 8) & 15) + 1, ((at >> 12) & 15) + 1, (at >> 5) & 1, (at >> 6) & 1, at & 0x1f
        for by in range(ht):
            for bx in range(wd):
                c = code + bx + 16 * by
                tp = assets.pens(gfx[c * 128:c * 128 + 128])
                cx = px + 16 * ((wd - 1 - bx) if hf else bx); cy = py + 16 * ((ht - 1 - by) if vf else by)
                for y in range(16):
                    for x in range(16):
                        p = tp[15 - y if vf else y][15 - x if hf else x]
                        if p != 15:
                            X, Y = ox + cx + x, oy + cy + y - 14   # MSHvSF cell y is relative to his origin; the native stores cy - FEET (14) from the feet line, drawn the same here
                            if 0 <= X < im.width and 0 <= Y < im.height: im.putpixel((X, Y), tuple(col[1 if pal == 13 else 0][p]))


ROWS = [
    ("attack stage 1 and 2 (T1.32)", "T1.32", (8, 1, (2, 5, 6))),
    ("lunge (T1.41)", "T1.41", (8, 1, (2, 5, 6))),
    ("jump attack (T1.38)", "T1.38", (12, 2, (1, 2))),
    ("Berserker (T3 slots)", "T3.3", [(22, 22, (1,)), (22, 24, (1,)), (22, 23, (1,)), (22, 25, (0,))]),
    ("grab hold (T1.48)", "T1.48", (16, 2, (3, 5))),
    ("auto-grab leap (T1.55)", "T1.55", (16, 0, (1,))),
    ("auto-grab stomp (T1.56)", "T1.56", (16, 0, (5,))),
    ("after the stomp (T1.57)", "T1.57", (1, 3, (0, 1))),
    ("lying (T2.22)", "T2.22", (14, 31, (0,))),
    ("getup (T2.23)", "T2.23", (22, 5, (0, 2, 4))),
    ("entrance close (T0.24)", "T0.24", (23, 3, (0, 2, 4))),
]


def uniq_poses(S, slot):
    seen, out = set(), []
    for r in native_chain(S, slot):
        ap = int.from_bytes(S["blk"][r + 4:r + 8], "big")
        if ap not in seen: seen.add(ap); out.append(r)
    return out


B, Aa = load(bgen, bas), load(agen, aas)
maxn = 5
img = Image.new("RGB", (CW * maxn * 3 + 230, CH * len(ROWS)), (40, 40, 48)); dr = ImageDraw.Draw(img)
for ri, (label, slot, arc) in enumerate(ROWS):
    y0 = ri * CH
    dr.text((4, y0 + 4), label, fill=(255, 255, 255)); dr.text((4, y0 + 18), slot, fill=(160, 200, 255))
    specs = arc if isinstance(arc, list) else [arc]
    frames = []
    for sub, ent, idx in specs:
        ch = mv_chain(SRC_ADDR[(sub, ent)])
        for i in idx: frames.append((sub, ent, i, ch[i]))
    for col_i, (title, items) in enumerate((("ARCADE", frames), ("BEFORE", [(None, None, None, r) for r in uniq_poses(B, slot)]), ("AFTER", [(None, None, None, r) for r in uniq_poses(Aa, slot)]))):
        x0 = 230 + col_i * CW * maxn
        dr.text((x0 + 2, y0 + 4), title, fill=(255, 200, 80))
        for n, (sub, ent, i, r) in enumerate(items[:maxn]):
            ox = x0 + n * CW + 70
            if title == "ARCADE":
                draw_arcade(r, img, ox, y0 + FEETLINE); dr.text((x0 + n * CW + 2, y0 + CH - 12), "%d.%d #%d" % (sub, ent, i), fill=(200, 200, 200))
            else:
                S = B if title == "BEFORE" else Aa
                draw_native(S, r, img, ox, y0 + FEETLINE - 16)
                dr.text((x0 + n * CW + 2, y0 + CH - 12), "%x" % (S["WIN"] + r), fill=(200, 200, 200))
        dr.line([x0, y0 + FEETLINE, x0 + CW * maxn - 4, y0 + FEETLINE], fill=(80, 80, 80))
pathlib.Path(outp).parent.mkdir(parents=True, exist_ok=True)
img.save(outp); print("sheet", outp, img.size)
