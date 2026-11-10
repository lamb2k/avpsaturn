#!/usr/bin/env python
"""Wolverine's MSHvSF animations from the arcade ROM, as a REFERENCE catalog (owner 11-10: "pull in his poses and attacks from the main arcade source so that we can compare it against his other moves").
OFFLINE, ROM-derived: the PNGs stay on this PC, never in git; nothing here adds a tile to the disc. Decoder: mvlib.py (animation index 0xd1a7e..0xd1c90, 27 sub-tables, 238 entries; frame records of 16 bytes;
box table 0x3a2000; box sets 0x1ce0f2). Every frame is drawn with the arcade's own tile pixels (not the near-match of the resident set), at 1 px = 1 px, on a ground line 13 px below the origin row,
with the hurt box (blue) and the attack box (red). R marks a frame whose tiles are all resident or within the merge distance of a resident tile (usable in the native block today), - marks a frame that would need tiles.
usage: mshvsf_catalog.py MSHVSF_DUMP_DIR ASSETS_DIR OUT_DIR
Names are provisional: the family (sub-table) comes from the decode (census note section 5), the move name only where the entry's provenance is known (D11's idle, walk, jump, light/heavy punch, kick, Berserker);
the rest are labelled by what the record data shows (attack box present, tick count, frame count) and need an owner's eye."""
import pathlib, sys
from PIL import Image, ImageDraw
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import mvlib, assets

dump, adir, out = (pathlib.Path(a) for a in sys.argv[1:4])
out.mkdir(parents=True, exist_ok=True)
mv = mvlib.MV(dump, adir)
col = mv.remap["colours"][mv.remap["default_colour"]]
FAMILY = {0: "idle and walk", 1: "jump and landing", 2: "crouch / stand-up", 3: "turn", 8: "light, medium, heavy punch (standing)", 9: "kick family", 10: "heavy normals / launchers", 11: "crouching normals",
          14: "hit reactions", 15: "idle alias", 16: "throws / grabs (candidate)", 17: "single-frame poses", 18: "air normals (candidate)", 19: "air normals 2 (candidate)", 21: "long animation", 22: "specials, supers, knockdown, getup",
          23: "taunts, win poses, intro", 24: "effect objects", 25: "misc", 26: "misc"}
KNOWN = {(0, 0): "idle (stand)", (0, 1): "walk", (1, 0): "jump forward", (1, 3): "landing", (8, 0): "standing light punch (D11 lp)", (8, 2): "standing heavy punch (D11 hp)", (9, 2): "kick (D11 hk)", (22, 10): "Berserker Barrage (flurry, D11 berserker)"}
FW, FH, OX, GY = 128, 190, 64, 150   # frame cell, origin column, ground line row in the cell
subs = mv.tables()
rows_total = frames_total = res_total = 0
index = []


def draw_frame(img, d, cx0, cy0, rec):
    ap = mv.l(rec + 4)
    n = mv.w(ap + 4)
    tab = mv.l(ap + 6)
    px, py = mv.s16(mv.w(tab + 2)), mv.s16(mv.w(tab + 4))
    ox, oy = cx0 + OX, cy0 + GY - 13
    for i in range(n + 1):
        if i:
            px += mv.s8(mv.mv[tab + 6 + 2 * (i - 1)]); py += mv.s8(mv.mv[tab + 7 + 2 * (i - 1)])
        code, at = mv.w(ap + 10 + 4 * i), mv.w(ap + 12 + 4 * i)
        wd, ht, hf, vf, pal = ((at >> 8) & 15) + 1, ((at >> 12) & 15) + 1, (at >> 5) & 1, (at >> 6) & 1, at & 0x1f
        palette = col[1 if pal == 13 else 0]
        for by in range(ht):
            for bx in range(wd):
                tile = assets.pens(mv.gfx[(code + bx + 16 * by) * 128:(code + bx + 16 * by) * 128 + 128])
                tx = px + 16 * ((wd - 1 - bx) if hf else bx)
                ty = py + 16 * ((ht - 1 - by) if vf else by)
                for y in range(16):
                    for x in range(16):
                        p = tile[15 - y if vf else y][15 - x if hf else x]
                        if p != 15:
                            X, Y = ox + tx + x, oy + ty + y
                            if 0 <= X < img.width and 0 <= Y < img.height and cx0 <= X < cx0 + FW and cy0 <= Y < cy0 + FH: img.putpixel((X, Y), tuple(palette[p % len(palette)]))
    hit, hurt = mv.boxes(rec)
    for r, colr in ((hurt, (60, 200, 255)), (hit, (255, 60, 60))):
        if r:
            d.rectangle([cx0 + OX - r[1], cy0 + GY - r[3], cx0 + OX - r[0], cy0 + GY - r[2]], outline=colr)


for si, (base, ents) in enumerate(subs):
    seen = {}
    rows = []
    for ei, a0 in enumerate(ents):
        seen.setdefault(a0, []).append(ei)
    for a0, eis in seen.items():
        rows.append((eis, a0, mv.chain(a0)))
    W = 40 + FW * 14
    H = 36 + (FH + 14) * len(rows)
    img = Image.new("RGB", (W, H), (40, 40, 48))
    d = ImageDraw.Draw(img)
    d.text((6, 6), "Sub-table %d: %s   (%d entries, %d distinct animations).  Frames: ticks, R = resident now, - = needs tiles; blue hurt box, red attack box; ground line at the cell's lower third" % (si, FAMILY.get(si, "?"), len(ents), len(rows)), fill=(255, 255, 255))
    for ri, (eis, a0, ch) in enumerate(rows):
        y0 = 30 + ri * (FH + 14)
        ticks = sum(mv.w(r + 2) & 0x7fff for r in ch)
        atk = any(mv.boxes(r)[0] for r in ch)
        res = [mv.pose(r)[1] == 0 for r in ch]
        name = next((KNOWN[(si, e)] for e in eis if (si, e) in KNOWN), "")
        d.text((4, y0), "%d.%s  @%x  %d frames, %d ticks, %s, %d of %d frames resident  %s" % (si, ",".join(str(e) for e in eis), a0, len(ch), ticks, "has an attack box" if atk else "no attack box", sum(res), len(res), name), fill=(255, 220, 120) if name else (200, 200, 210))
        for k, r in enumerate(ch[:14]):
            cx0, cy0 = 20 + k * FW, y0 + 14
            d.rectangle([cx0, cy0, cx0 + FW - 1, cy0 + FH - 1], outline=(70, 70, 80))
            d.line([cx0, cy0 + GY, cx0 + FW - 1, cy0 + GY], fill=(90, 90, 90))
            draw_frame(img, d, cx0, cy0, r)
            ok = mv.pose(r)[1] == 0
            d.text((cx0 + 2, cy0 + 2), "%d t%d %s" % (k, mv.w(r + 2) & 0x7fff, "R" if ok else "-"), fill=(120, 255, 120) if ok else (255, 120, 120))
        rows_total += 1
        frames_total += len(ch)
        res_total += sum(res)
    p = out / ("sub%02d_%s.png" % (si, FAMILY.get(si, "x").replace(" ", "_").replace(",", "").replace("/", "-")[:28]))
    img.save(p)
    index.append((si, FAMILY.get(si, "?"), len(rows), p))
    print("sub", si, len(rows), "animations", p.name, flush=True)


# ---- the AvP roles against the arcade animations: what each role uses now (gen_native.py SRC) and the best candidates (reference only)
ROLES = [
    ("stand 020000 (T1.0)", (0, 0), [(0, 3), (15, 1), (23, 9)]),
    ("walk 020002 (T1.2)", (0, 1), [(0, 5)]),
    ("attack stage 1, 2 (LP) 020006", (8, 0), [(8, 3), (8, 1), (8, 4)]),
    ("attack stage 3 (HP) 020006", (8, 2), [(8, 5), (10, 0), (10, 3)]),
    ("finisher 02000e / lunge 02000a (slashes now; was kick)", (8, 2), [(9, 1), (9, 2), (9, 4), (10, 1)]),
    ("jump / leap arc 020004", (1, 0), [(1, 1), (1, 2), (1, 6), (1, 7)]),
    ("landing / crouch 020004", (1, 3), [(1, 4), (1, 5)]),
    ("special: Berserker 020008 (own chain)", (22, 10), [(22, 18), (10, 5), (10, 2)]),
    ("grab hold 0204xx (now: second light slash)", (8, 3), [(16, 0), (16, 2), (16, 4), (16, 5), (22, 4)]),
    ("grab slam 020408 (now: heavy punch)", (8, 2), [(16, 0), (16, 3), (16, 2), (22, 0)]),
    ("hit flinch light 020202", (14, 1), [(14, 2), (14, 3), (14, 5)]),
    ("hit heavy / knockdown flight 0402xx (now: heavy-hit recoil)", (14, 4), [(14, 8), (22, 25), (22, 29), (22, 33), (16, 1)]),
    ("ground / getup", (1, 3), [(22, 5), (22, 6), (22, 7), (22, 8), (23, 8)]),
    ("KO / tumble", (14, 8), [(14, 4), (22, 21), (22, 22)]),
]
entry = {}
for si, (base, ents) in enumerate(subs):
    for ei, a0 in enumerate(ents): entry[(si, ei)] = a0
FW2 = 100
rows = []
for label, cur, cands in ROLES:
    rows.append((label, cur, True)); rows.extend((label, c, False) for c in cands)
H = 40 + (FH * 3 // 4 + 10) * len(rows)
img = Image.new("RGB", (30 + FW2 * 12 + 260, H), (40, 40, 48))
d = ImageDraw.Draw(img)
d.text((6, 6), "AvP role -> MSHvSF animation: the one it uses now (gold) and candidates (grey). Frames R = resident (usable in the native block today), - = needs tiles. Candidates are guesses to look at, names provisional.", fill=(255, 255, 255))
y0 = 30
last = None
for label, se, is_cur in rows:
    a0 = entry.get(se)
    if a0 is None: continue
    ch = mv.chain(a0)
    if label != last: d.text((6, y0 - 2), label, fill=(255, 255, 255)); last = label
    d.text((6, y0 + 12), "%s %d.%d @%x (%d frames, %d resident)" % ("USES" if is_cur else "cand", se[0], se[1], a0, len(ch), sum(1 for r in ch if mv.pose(r)[1] == 0)), fill=(255, 220, 120) if is_cur else (170, 170, 180))
    sc = 0.75
    for k, r in enumerate(ch[:11]):
        tile = Image.new("RGB", (FW, FH), (40, 40, 48)); td = ImageDraw.Draw(tile)
        draw_frame(tile, td, 0, 0, r)
        ok = mv.pose(r)[1] == 0
        td.text((2, 2), "%d t%d %s" % (k, mv.w(r + 2) & 0x7fff, "R" if ok else "-"), fill=(120, 255, 120) if ok else (255, 120, 120))
        tile = tile.resize((int(FW * sc), int(FH * sc)), Image.NEAREST)
        img.paste(tile, (260 + k * int(FW * sc), y0))
    y0 += FH * 3 // 4 + 10
img.crop((0, 0, img.width, min(img.height, y0 + 10))).save(out / "role_candidates.png")
print("role candidates written")

import os
if os.environ.get("PICK"):   # PICK="22.12,22.14,..." PICK_NAME=x: one picture of just those animations (first 18 frames, 3/4 scale) to look at
    es = [tuple(int(x) for x in t.split(".")) for t in os.environ["PICK"].split(",")]
    sc = 0.75
    pk = Image.new("RGB", (30 + int(FW * sc) * 18, 22 + (int(FH * sc) + 16) * len(es)), (40, 40, 48))
    pd = ImageDraw.Draw(pk)
    for ri, se in enumerate(es):
        a0 = entry[se]; ch = mv.chain(a0); y0 = 6 + ri * (int(FH * sc) + 16)
        pd.text((4, y0), "%d.%d @%x %d frames, %d resident" % (se[0], se[1], a0, len(ch), sum(1 for r in ch if mv.pose(r)[1] == 0)), fill=(255, 220, 120))
        for k, r in enumerate(ch[:18]):
            t = Image.new("RGB", (FW, FH), (40, 40, 48)); td = ImageDraw.Draw(t); draw_frame(t, td, 0, 0, r)
            ok = mv.pose(r)[1] == 0
            td.text((2, 2), "%d t%d %s" % (k, mv.w(r + 2) & 0x7fff, "R" if ok else "-"), fill=(120, 255, 120) if ok else (255, 120, 120))
            pk.paste(t.resize((int(FW * sc), int(FH * sc)), Image.NEAREST), (14 + k * int(FW * sc), y0 + 14))
    pk.save(out / ("pick_%s.png" % os.environ.get("PICK_NAME", "x")))
    print("pick written")
    raise SystemExit(0)

idx = Image.new("RGB", (1500, 80 + 26 * len(index)), (40, 40, 48))
d = ImageDraw.Draw(idx)
d.text((8, 8), "Wolverine MSHvSF animation catalog (reference only, ROM-derived, local): %d distinct animations, %d frames, %d resident today (%d percent)" % (rows_total, frames_total, res_total, 100 * res_total // max(1, frames_total)), fill=(255, 255, 255))
d.text((8, 28), "One PNG per sub-table of the animation index; role_candidates.png maps each AvP role to the animation it uses and the candidates; names are provisional except where marked in gold (provenance known from D11).", fill=(200, 200, 210))
for i, (si, fam, n, p) in enumerate(index): d.text((8, 60 + 26 * i), "sub-table %2d  %-40s %3d animations   %s" % (si, fam, n, p.name), fill=(160, 220, 255))
idx.save(out / "index.png")
print("catalog", rows_total, "animations", frames_total, "frames", res_total, "resident")
