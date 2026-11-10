#!/usr/bin/env python
"""Native Wolverine: motion comparison sheets (owner 11-10, a map of his motions next to the stock characters). OFFLINE, ROM-derived: the PNGs stay on this PC, never in git.
usage: motion_compare.py GEN_DIR ASSETS_DIR WORK_DIR OUT_DIR
  GEN_DIR    a build's gen dir (wv_native.bin / .inc / .roles.txt): his native frame records, drawn as the game's emitter draws them, with the record's hurt (blue) and attack (red) boxes
  ASSETS_DIR the guest asset directory (remap.json, gfx_wolverine.bin)
  WORK_DIR   a build work dir (rt.bin): Schaefer's stock records (the donor of his skeleton): ticks, hurt and attack box indexes per frame
Rows are the game states and the slots of the per-character index tables that each state selects (T1 = states 02xxxx, T0 = entrance, T2 = hit reactions, knockdown, getup, KO). One PNG per state
group plus index.png and jump_arcs.png. Columns: Wolverine (art, boxes, ticks), Schaefer donor (ticks and boxes as strips; art not rendered here), Linn / Warrior / Hunter (not rendered offline).
All frames share one scale (1 px = 1 px) and one ground line, so heights compare directly."""
import json, pathlib, re, sys
from PIL import Image, ImageDraw
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import assets

gen, adir, work, out = (pathlib.Path(a) for a in sys.argv[1:5])
out.mkdir(parents=True, exist_ok=True)
blk = (gen / "wv_native.bin").read_bytes()
inc = (gen / "wv_native.inc").read_text()
rom = (work / "rt.bin").read_bytes()
const = lambda n: int(re.search(r"#define %s (0x[0-9a-f]+|\d+)u?" % n, inc)[1], 0)
WIN, T = const("WV_NAT_WIN"), const("WV_NAT_T")
A = json.loads((adir / "remap.json").read_text())
raw = (adir / "gfx_wolverine.bin").read_bytes()
col = A["colours"][A["default_colour"]]
w = lambda b, o: int.from_bytes(b[o:o + 2], "big")
l = lambda b, o: int.from_bytes(b[o:o + 4], "big")
s16 = lambda v: v - 65536 if v >= 32768 else v
s8 = lambda v: v - 256 if v >= 128 else v
TABLES = (("T1", 0, 0x162f90), ("T0", 0x163032 - 0x162f90, 0x163032), ("T2", 0x163074 - 0x162f90, 0x163074), ("T3", 0x1630f6 - 0x162f90, 0x1630f6))
base_of = {t: (b, rb) for t, b, rb in TABLES}
toff = T - WIN
hurt0, atk0 = toff + s16(w(blk, toff)), toff + s16(w(blk, toff + 2))
FW, FH, OXC, FEET = 96, 190, 48, 170   # frame cell width and height, origin column, ground line row


def wv_chain(slot):
    t, i = slot.split(".")
    b, rb = base_of[t]
    a = b + s16(w(blk, b + 2 * int(i)))
    res = []
    for _ in range(40):
        res.append(a)
        if w(blk, a + 2) & 0x8000: break
        a += 16
    return res


def sch_chain(slot):
    t, i = slot.split(".")
    b, rb = base_of[t]
    a = rb + s16(w(rom, rb + 2 * int(i)))
    res = []
    for _ in range(40):
        res.append(a)
        if w(rom, a + 2) & 0x8000: break
        a += 16
    return res


def draw_record(img, d, ox, oy, r):
    ap = l(blk, r + 4) - WIN
    for i in range(w(blk, ap + 4)):
        po = ap + 12 + 8 * i
        key, at, dx, dy = w(blk, po), w(blk, po + 2), s16(w(blk, po + 4)), s16(w(blk, po + 6))
        hf, vf = at >> 5 & 1, at >> 6 & 1
        pal = col[1 if not at & 1 else 0]
        px = assets.pens(raw[key * 128:key * 128 + 128])
        for y in range(16):
            for x in range(16):
                p = px[15 - y if vf else y][x ^ 15 if hf else x]
                if p != 15:
                    X, Y = ox + dx + x, oy + dy + y
                    if 0 <= X < img.width and 0 <= Y < img.height: img.putpixel((X, Y), tuple(pal[p]))
    for idx, base, size, colr in ((blk[r + 8], hurt0, 8, (60, 200, 255)), (blk[r + 9], atk0, 16, (255, 60, 60))):
        if idx:
            e = base + idx * size
            xb, yb, hw, hh = s8(blk[e]), s8(blk[e + 1]), blk[e + 2], blk[e + 3]
            d.rectangle([ox + xb - hw, oy - yb - hh, ox + xb + hw, oy - yb + hh], outline=colr)


GROUPS = {
    "1_stand_walk": ("Stand and walk", [("T1.0", "020000 stand"), ("T1.2", "020002 walk")]),
    "2_attack_chain": ("Attack chain, finisher, lunge", [("T1.32", "020006 stage 1 (LP)"), ("T1.33", "020006 stage 2 (LP)"), ("T1.34", "020006 stage 3 (HP)"), ("T1.16", "02000e finisher (was kick)"), ("T1.41", "02000a lunge (was kick)")]),
    "3_jump_leap": ("Jump, leap, landing", [("T1.3", "020004 launch (knees bent)"), ("T1.37", "020004 arc (rise, apex, fall)"), ("T1.38", "020004 jump attack hold"), ("T1.40", "020004 air attack"), ("T1.10", "020004 landing"), ("T1.4", "020004 crouch hold"), ("T1.6", "020004 crouch hold 2")]),
    "4_special": ("Special (stock chain; his Berserker is its own chain)", [("T1.42", "020008 stock special chain")]),
    "5_grab_held_throw": ("Grab, held, thrown (his own grab is off)", [("T1.48", "020400 grab"), ("T1.52", "020404 hold"), ("T1.53", "020404 hold 2"), ("T1.55", "020406 lift"), ("T1.56", "020408 slam"), ("T1.57", "020004 after")]),
    "6_hit_knockdown": ("Hit flinch, knockdown flight, ground, getup", [("T2.1", "020202 flinch light"), ("T2.0", "020202 flinch heavy"), ("T2.13", "020202 flinch"), ("T2.14", "0402xx knockdown flight"), ("T2.16", "0402xx flight/ground"), ("T2.20", "0402xx flight"), ("T2.22", "ground"), ("T2.23", "getup"), ("T2.24", "getup 2")]),
    "7_ko_entrance": ("KO and stage entrance", [("T2.54", "0402xx KO tumble"), ("T0.2", "080000 entrance walk"), ("T0.3", "080000 entrance launch"), ("T0.4", "080000 entrance land"), ("T0.10", "080000 entrance")]),
}
BG = (40, 40, 48)


def group_sheet(name, title, rows):
    LW, CW = 150, FW * 9
    stock = ("Schaefer donor (ticks, boxes)", "Linn (stock)", "Warrior (stock)", "Hunter (stock)")
    W = LW + CW + 4 * 150 + 20
    H = 40 + FH * len(rows)
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((6, 6), "%s   (Wolverine: native records of this build; frame = ticks; blue hurt box, red attack box)" % title, fill=(255, 255, 255))
    d.text((LW, 22), "Wolverine", fill=(255, 220, 120))
    for k, nm in enumerate(stock): d.text((LW + CW + 10 + k * 150, 22), nm, fill=(160, 160, 170))
    for ri, (slot, label) in enumerate(rows):
        y0 = 40 + ri * FH
        d.line([0, y0, W, y0], fill=(80, 80, 90))
        d.text((4, y0 + 4), label, fill=(255, 255, 255))
        d.text((4, y0 + 18), slot, fill=(160, 200, 255))
        for ci, r in enumerate(wv_chain(slot)[:9]):
            ox, oy = LW + ci * FW + OXC, y0 + FEET
            d.line([LW + ci * FW, oy, LW + ci * FW + FW - 2, oy], fill=(90, 90, 90))
            draw_record(img, d, ox, oy, r)
            dur = w(blk, r)
            d.text((LW + ci * FW + 2, y0 + 4), "%d t%s" % (ci, "hold" if dur >= 255 else dur), fill=(255, 255, 255))
        sc = sch_chain(slot)
        sx = LW + CW + 10
        d.text((sx, y0 + 4), "%d rec, %d ticks" % (len(sc), sum(w(rom, a) for a in sc if w(rom, a) < 255)), fill=(200, 200, 200))
        bx = sx
        for a in sc[:9]:
            dur = w(rom, a)
            wd = max(6, min(14, dur * 2)) if dur < 255 else 14
            d.rectangle([bx, y0 + 24, bx + wd, y0 + 34], outline=(120, 120, 130))
            if rom[a + 9]: d.rectangle([bx, y0 + 36, bx + wd, y0 + 40], fill=(255, 60, 60))
            if rom[a + 8]: d.rectangle([bx, y0 + 42, bx + wd, y0 + 46], fill=(60, 200, 255))
            bx += wd + 2
        for k in range(1, 4): d.text((LW + CW + 10 + k * 150, y0 + 60), "not rendered offline", fill=(110, 110, 120))
    p = out / ("%s.png" % name)
    img.save(p)
    return p


def jump_arcs():
    src = (pathlib.Path(__file__).resolve().parent / "gen_native.py").read_text()
    steps = eval(re.search(r"^ARC_STEPS = (\[.*?\])", src, re.M)[1])
    ticks = int(re.search(r"ARC_TICKS, ARC_SCALE = (\d+)", src)[1])
    scale = 0.838
    tot = sum(f for f, _, _ in steps)
    arc = []
    for f, l0, l1 in steps:
        n = int(round(f * ticks / tot))
        for k in range(n): arc.append(scale * (l0 + (l1 - l0) * (k + 0.5) / max(1, n)))
    W, H = 900, 420
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((6, 6), "Jump arcs: height above the ground line per tick (px)", fill=(255, 255, 255))
    gy = 380
    d.line([40, gy, W - 20, gy], fill=(120, 120, 120))
    for hgt in (50, 100, 150, 200):
        d.line([40, gy - hgt, W - 20, gy - hgt], fill=(60, 60, 70))
        d.text((4, gy - hgt - 6), str(hgt), fill=(160, 160, 160))
    pts = [(40 + k * 18, gy - v) for k, v in enumerate(arc)]
    d.line(pts, fill=(255, 220, 120), width=2)
    d.text((50, 22), "Wolverine leap (drawn arc): apex %.0f px over %d ticks; the game does not lift the actor, the lift is the drawn sprite arc" % (max(arc), len(arc)), fill=(255, 220, 120))
    consts = [(0x90000, 0x6000), (0xc0000, 0x6000), (0x90000, 0x7000), (0x70000, 0x8000), (0x80000, 0x8000)]   # (velocity at +0x34, gravity magnitude at +0x3c = 0x10000 - 0xe000 style negatives) as written by the lifted jump and hit routines
    colors = [(120, 200, 255), (160, 255, 160), (255, 160, 160), (220, 160, 255), (200, 200, 200)]
    for n, ((v0, g), c) in enumerate(zip(consts, colors)):
        v, g_, hgt, pts = v0 / 65536.0, g / 65536.0, 0.0, []
        for k in range(60):
            pts.append((40 + k * 8, gy - hgt))
            hgt += v
            v -= g_
            if hgt < 0: break
        apex = (v0 / 65536.0) ** 2 / (2 * g / 65536.0)
        d.line(pts, fill=c)
        d.text((40, 38 + 13 * n), "stock velocity 0x%x gravity 0x%x (16.16 per tick, written by the game's jump routines): apex %.0f px, not attributed to a character here" % (v0, g, apex), fill=c)
    p = out / "jump_arcs.png"
    img.save(p)
    return p


paths = [group_sheet(k, t, r) for k, (t, r) in GROUPS.items()]
paths.append(jump_arcs())
idx = Image.new("RGB", (1200, 60 + 36 * len(paths)), BG)
d = ImageDraw.Draw(idx)
d.text((8, 8), "Wolverine motion map (this build). Columns: Wolverine native art; Schaefer donor ticks and boxes; Linn / Warrior / Hunter art not rendered offline.", fill=(255, 255, 255))
for i, p in enumerate(paths): d.text((8, 40 + 36 * i), str(p), fill=(160, 220, 255))
idx.save(out / "index.png")
print("sheets", len(paths))
