#!/usr/bin/env python
"""Native Wolverine: the current mapping of every Schaefer state or role to an MSHvSF animation, the PROPOSED mapping (owner 11-10: "pull in the sprite that corresponds to the Schaefer states"), the frames added
and dropped and the net tiles. OFFLINE, ROM-derived, local only; nothing is built from this: it is the review sheet before any remap.
usage: baseline_swap.py MSHVSF_DUMP_DIR ASSETS_DIR GEN_DIR OUT_PREFIX WORK_DIR   (WORK_DIR: a build work dir with rt.bin, Schaefer's donor chains)
Rows are role groups (the slots of Schaefer's index tables that one animation serves). Per row: state word(s), current MSHvSF animation (sub.ent, frames, resident frames, a frame), the proposed one (same),
frames added (frames of the proposal that are not resident), tiles added (16x16 cells with no resident tile within the merge distance, pixel-distinct), tiles freed (keys only the replaced role used), one reason.
Totals: the keys his native records use today, after the swap, and the stage pack's 1,474 keys (the pack is built from D11, not from what the native records use).
Names are provisional (see mshvsf_catalog.py): the proposals marked ? are picks by pose that the owner or MAME should confirm."""
import csv, json, pathlib, re, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import mvlib, assets

dump, adir, gen, outp = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]), sys.argv[4]
mv = mvlib.MV(dump, adir)
col = mv.remap["colours"][mv.remap["default_colour"]]
subs = mv.tables()
entry = {(si, ei): a0 for si, (b, ents) in enumerate(subs) for ei, a0 in enumerate(ents)}
blk = (gen / "wv_native.bin").read_bytes()
bw = lambda o: int.from_bytes(blk[o:o + 2], "big")
bl = lambda o: int.from_bytes(blk[o:o + 4], "big")
s16 = lambda v: v - 65536 if v >= 32768 else v
WIN = 0x300000
TAB = {"T1": 0, "T0": 0x163032 - 0x162f90, "T2": 0x163074 - 0x162f90, "T3": 0x1630f6 - 0x162f90}
PACK_KEYS = len(set(mv.remap["stage_keys"]["02"]))


def wv_keys(slots):
    keys = set()
    for sl in slots:
        t, i = sl.split(".")
        a = TAB[t] + s16(bw(TAB[t] + 2 * int(i)))
        for _ in range(60):
            ap = bl(a + 4) - WIN
            for p in range(bw(ap + 4)): keys.add(bw(ap + 12 + 8 * p))
            if bw(a + 2) & 0x8000: break
            a += 16
    return keys


def canon(code):
    px = np.array(assets.pens(mv.gfx[code * 128:code * 128 + 128]), dtype=np.uint8)
    return min(f.tobytes() for f in (px, px[:, ::-1], px[::-1, :], px[::-1, ::-1]))


def anim_info(se, picks=None):
    """frames, resident frames, keys of the resident cells (near match), canonical far tiles of the PICKED frames (all frames when picks is None)"""
    ch = mv.chain(entry[se]); keys = set(); far = set(); res = 0
    allch = ch
    if picks is not None: ch = [allch[i] for i in sorted(picks)]
    for r in ch:
        cells, nfar = mv.pose(r)
        res += nfar == 0
        keys |= {c[2] for c in cells}
        ap = mv.l(r + 4); n = mv.w(ap + 4)
        for i in range(n + 1):
            code, at = mv.w(ap + 10 + 4 * i), mv.w(ap + 12 + 4 * i)
            for by in range(((at >> 12) & 15) + 1):
                for bx in range(((at >> 8) & 15) + 1):
                    c = code + bx + 16 * by
                    if mv.key_of(c) == "far": far.add(canon(c))
    return dict(frames=len(allch), res=sum(1 for r in allch if mv.pose(r)[1] == 0), picked=len(ch), nonres=sum(1 for r in ch if mv.pose(r)[1] != 0), keys=keys, far=far, ticks=sum(mv.w(r + 2) & 0x7fff for r in allch), chain=allch)


FW, FH, OX, GY = 128, 190, 64, 150


rom = (pathlib.Path(sys.argv[3]).parent.parent / "w1" / "rt.bin") if False else None


def donor_picks(slots, n_src, wrom):
    """the source frames gen_native.make_chain picks for the donor chains of these slots: a donor record at the middle of its share of the donor's ticks takes the source frame at the same share"""
    w2 = lambda o: int.from_bytes(wrom[o:o + 2], "big")
    out = set()
    for sl in slots:
        t, i = sl.split("."); base = {"T1": 0x162f90, "T0": 0x163032, "T2": 0x163074, "T3": 0x1630f6}[t]
        a = base + s16(w2(base + 2 * int(i))); recs = []
        for _ in range(60):
            recs.append(a)
            if w2(a + 2) & 0x8000: break
            a += 16
        durs = [w2(r) for r in recs]; dtot = sum(d for d in durs if d < 255) or 1; cum = 0
        for k, d in enumerate(durs):
            if d >= 255: out.add(n_src - 1); continue
            out.add(min(n_src - 1, int((cum + d / 2.0) / dtot * n_src))); cum += d
    return out


def thumb(se, frame=None, sc=0.5):
    ch = mv.chain(entry[se]); r = ch[min(len(ch) - 1, frame if frame is not None else len(ch) // 3)]
    img = Image.new("RGB", (FW, FH), (40, 40, 48)); d = ImageDraw.Draw(img)
    ap = mv.l(r + 4); n = mv.w(ap + 4); tab = mv.l(ap + 6)
    px, py = mv.s16(mv.w(tab + 2)), mv.s16(mv.w(tab + 4)); ox, oy = OX, GY - 13
    for i in range(n + 1):
        if i: px += mv.s8(mv.mv[tab + 6 + 2 * (i - 1)]); py += mv.s8(mv.mv[tab + 7 + 2 * (i - 1)])
        code, at = mv.w(ap + 10 + 4 * i), mv.w(ap + 12 + 4 * i)
        wd, ht, hf, vf, pal = ((at >> 8) & 15) + 1, ((at >> 12) & 15) + 1, (at >> 5) & 1, (at >> 6) & 1, at & 0x1f
        palette = col[1 if pal == 13 else 0]
        for by in range(ht):
            for bx in range(wd):
                tile = assets.pens(mv.gfx[(code + bx + 16 * by) * 128:(code + bx + 16 * by) * 128 + 128])
                tx = px + 16 * ((wd - 1 - bx) if hf else bx); ty = py + 16 * ((ht - 1 - by) if vf else by)
                for y in range(16):
                    for x in range(16):
                        p = tile[15 - y if vf else y][15 - x if hf else x]
                        X, Y = ox + tx + x, oy + ty + y
                        if p != 15 and 0 <= X < FW and 0 <= Y < FH: img.putpixel((X, Y), tuple(palette[p % len(palette)]))
    return img.resize((int(FW * sc), int(FH * sc)), Image.NEAREST)


# role groups: (label, state words, slots served, current MSHvSF (sub, ent), proposed MSHvSF or None = keep, reason)
G = [
    ("stand", "020000 (also 080000 entrance stand)", ["T1.0", "T1.29", "T1.30", "T1.1"], (0, 0), None, "already his idle (12 of 17 frames resident)"),
    ("walk", "020002", ["T1.2"], (0, 1), None, "already his walk"),
    ("attack stage 1", "020006 (T1.32; T1.33 is an alias of the same chain)", ["T1.32"], (8, 0), (8, 1), "owner: the main attack is the double claw (medium punch twice, MP MP; MAME-confirmed 11-10): first hit 8.1 (inferred by pose: a wide two-claw thrust, 20 ticks)"),
    ("attack stage 2", "020006 (T1.33, aliased to stage 1 today: needs its own chain)", ["T1.33"], (8, 0), (8, 4), "second hit of the double claw: 8.4, the twin of 8.1 with a different start (inferred by pose)"),
    ("attack stage 3", "020006 (T1.34)", ["T1.34"], (8, 2), None, "heavy punch 8.2 stays unless the owner wants a third claw hit; chain B timing kept"),
    ("finisher, lunge", "02000e (T1.14, T1.16), 02000a (T1.41)", ["T1.14", "T1.16", "T1.41"], (8, 2), None, "stay claw slashes (no kicks)"),
    ("leap launch, landing, crouch holds", "020004 (T1.3, T1.10, T1.4-6), 080000 entrance (T0.3, T0.10)", ["T1.3", "T1.10", "T1.4", "T1.5", "T1.6"], (1, 3), None, "knees-bent landing frames serve both"),
    ("leap arc", "020004 (T1.37)", ["T1.37"], (1, 0), None, "his jump 1.0 (6 of 12 frames resident), arc lifted by the game's physics"),
    ("jump attack", "020004 (T1.38, T1.40)", ["T1.38", "T1.40"], (1, 0), (18, 0), "an air normal 18.0 instead of jump pose / idle pose with a box (candidate, check in the catalog)"),
    ("Berserker", "020008 (own chain, 12 strikes, 4 ticks)", [], (22, 10), (23, 1), "owner: Berserker Barrage is the QCF+P flurry; 22.10 is Tornado Claw. 23.1 (56 frames of rapid claw thrusts) is the best fit by pose (inferred, MAME to confirm)"),
    ("grab hold, lift", "020400-020406 (T1.48-55)", ["T1.48", "T1.52", "T1.55"], (8, 3), (16, 2), "claw hold / throw wind-up: 16.2 (11 frames, rising claw slash) is the candidate throw; 16.x are the arcade's air and throw moves (inferred)"),
    ("grab slam", "020408 (T1.56)", ["T1.56"], (8, 2), (16, 0), "slam: 16.0 (7 frames, downward slash with an attack box) (inferred)"),
    ("hit flinch", "020202 (T2.1-12, 13, 15, 17-19, 46, 50)", ["T2.1", "T2.13", "T2.15", "T2.17", "T2.19", "T2.46"], (14, 2), None, "already his reactions 14.x"),
    ("knockdown flight", "0402xx (T2.14, 16, 20 and aliases)", ["T2.14", "T2.16", "T2.20"], (14, 4), None, "already the heavy-hit tumble 14.4 (7 of 7 frames resident)"),
    ("ground, getup", "0402xx / 0208xx (T2.22-24)", ["T2.22", "T2.23", "T2.24"], (1, 3), (22, 5), "his getup 22.5 (5 of 5 frames resident) instead of the landing crouch"),
    ("KO tumble", "0402xx (T2.54)", ["T2.54"], (14, 5), (14, 8), "knockdown KO tumble 14.8 (3 frames, 3 resident)"),
    ("stage entrance", "080000 (T0.*)", ["T0.2"], (0, 1), (23, 3), "his intro/taunt 23.3 (5 of 5 resident) as the entrance pose (inferred)"),
]
wrom = (pathlib.Path(sys.argv[5]) / "rt.bin").read_bytes()
info = {}
for se in {g[3] for g in G}: info[se] = anim_info(se)
pinfo = {}
for g in G:
    if g[4]:
        n = len(mv.chain(entry[g[4]]))
        picks = set(range(0, n, max(1, n // 6))) if g[0] == "Berserker" else donor_picks(g[2], n, wrom)   # the Berserker takes about six distinct poses of the barrage, looped over its 12 strikes
        pinfo[g[0]] = anim_info(g[4], picks)
group_keys = {g[0]: wv_keys(g[2]) if g[2] else set() for g in G}
all_native = set()
for t, b, n in (("T1", 0, 80), ("T0", 0, 33), ("T2", 0, 65), ("T3", 0, 49)):
    all_native |= wv_keys(["%s.%d" % (t, i) for i in range(n)])
replaced = [g for g in G if g[4]]
keep = set()
for g in G:
    if not g[4]: keep |= group_keys[g[0]]
# keys every other chain (not in any group) still uses: all native keys minus the keys of replaced groups, conservatively: the replaced groups' keys are freed only if no kept group uses them
rep_keys = set().union(*[group_keys[g[0]] for g in replaced])
other_keys = all_native - set().union(*group_keys.values())
prop_keys = set().union(*[pinfo[g[0]]["keys"] for g in replaced]); far_all = set().union(*[pinfo[g[0]]["far"] for g in replaced])
after_keys = keep | other_keys | prop_keys
freed = (rep_keys - after_keys)
rows = []
for g in G:
    label, sw, slots, cur, prop, why = g
    ci = info[cur]; pi = pinfo[label] if prop else None
    freed_g = (group_keys[label] - after_keys) if prop else set()
    rows.append(dict(role=label, state=sw, current="%d.%d (%d frames, %d resident)" % (cur[0], cur[1], ci["frames"], ci["res"]), proposed=("%d.%d (%d frames, %d resident; %d picked)" % (prop[0], prop[1], pi["frames"], pi["res"], pi["picked"])) if prop else "unchanged",
                     frames_added=pi["nonres"] if prop else 0, tiles_added=len(pi["far"]) if prop else 0, tiles_freed=len(freed_g), reason=why))
with open(outp + "_swap.csv", "w", newline="", encoding="utf-8") as fh:
    wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
tot = ("Keys his native records use today: %d (pack carries %d). After the swap: %d resident keys + %d new tiles = %d; keys freed (used only by replaced roles): %d. Net against today's use %+d, against the pack %+d."
       % (len(all_native), PACK_KEYS, len(after_keys), len(far_all), len(after_keys) + len(far_all), len(freed), len(after_keys) + len(far_all) - len(all_native), len(after_keys) + len(far_all) - PACK_KEYS))
with open(outp + "_swap.md", "w", encoding="utf-8") as fh:
    fh.write("# Current vs proposed MSHvSF mapping per Schaefer state (review sheet, offline, local; nothing built)\n\n%s\n\n" % tot)
    fh.write("| Role | State word(s) | CURRENT (sub.ent, frames) | PROPOSED | Frames added | Tiles added | Tiles freed | Reason |\n|---|---|---|---|---|---|---|---|\n")
    for r in rows: fh.write("| %s | %s | %s | %s | %d | %d | %d | %s |\n" % (r["role"], r["state"], r["current"], r["proposed"], r["frames_added"], r["tiles_added"], r["tiles_freed"], r["reason"]))
# picture
RH = 112
img = Image.new("RGB", (1900, 70 + RH * len(rows)), (40, 40, 48)); d = ImageDraw.Draw(img)
d.text((8, 8), "Current vs proposed MSHvSF mapping per Schaefer state (review sheet; thumbnails are the arcade frames; amber = proposed change)", fill=(255, 255, 255))
d.text((8, 24), tot, fill=(200, 220, 255))
for i, (g, r) in enumerate(zip(G, rows)):
    y = 50 + RH * i
    d.line([0, y - 4, 1900, y - 4], fill=(80, 80, 90))
    d.text((8, y), r["role"], fill=(255, 255, 255)); d.text((8, y + 14), r["state"][:48], fill=(160, 200, 255))
    d.text((8, y + 30), "frames added %d, tiles added %d, freed %d" % (r["frames_added"], r["tiles_added"], r["tiles_freed"]), fill=(255, 200, 90) if g[4] else (150, 150, 160))
    d.text((8, y + 46), r["reason"][:60], fill=(200, 200, 210)); d.text((8, y + 60), r["reason"][60:120], fill=(200, 200, 210)); d.text((8, y + 74), r["reason"][120:180], fill=(200, 200, 210))
    d.text((380, y), "CURRENT " + r["current"], fill=(255, 255, 255))
    for k, fr in enumerate((0, None)): img.paste(thumb(g[3], fr), (380 + k * 70, y + 14))
    d.text((820, y), "PROPOSED " + r["proposed"], fill=(255, 200, 90) if g[4] else (150, 150, 160))
    if g[4]:
        n = pinfo[g[0]]["frames"]
        for k, fr in enumerate((0, n // 3, 2 * n // 3, n - 1)): img.paste(thumb(g[4], fr), (820 + k * 70, y + 14))
img.save(outp + "_swap.png")
print(tot)
