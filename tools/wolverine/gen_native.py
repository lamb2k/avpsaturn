#!/usr/bin/env python
"""Lane wv-native-gfx 11-09: Wolverine's native animation data block (plan V2 sections 4 and 5), as C tables for saturn/guests/wolverine (build time, ROM-derived, never in git).
The block is one 64 KB window of the 68000 address space (0x300000, PAGE[0x30]):
  0x0000..  Schaefer's index tables and frame records relocated verbatim (the donor span of reloc_block.py; its assemblies stay in the ROM image). Only named pointer fields change:
            the jump targets (+ delta), and every index-table entry or jump target that names Schaefer's stand, walk or first claw attack chain, which now names the native chain.
  native    records of his idle (the 17 records of MSHvSF's standing loop), walk (Schaefer's 12-record skeleton, his poses by phase of MSHvSF's 16-record walk cycle) and first claw
            attack (MSHvSF's light punch, 6 records) read directly from his program ROM (a MAME dump, tools/wolverine/mshvsf_dump.lua), then his pose assemblies (family 0xA, one tile a part
            drawn as the game's own emitter 0xaa38a reads them), then his box table T' (donor copy plus his hurt and attack boxes).
Tile keys: each ROM cell's pixels are matched to a key of the guest asset set (gfx_wolverine.bin, flips included); a record whose cells are not all resident keys of the stage packs
(remap.json stage_keys) is dropped and its ticks go to the record before it, as assets.py THIN does.
usage: gen_native.py WORK ASSETS_DIR MSHVSF_DUMP OUT.inc"""
import json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import assets

WORK, ASSETS, MV, OUT = (pathlib.Path(a) for a in sys.argv[1:5])
rom = (WORK / "rt.bin").read_bytes()
mv = (MV / "prog_data.bin").read_bytes()
gfx = (MV / "gfx_a000.bin").read_bytes()
A = json.loads((ASSETS / "remap.json").read_text())
keyraw = (ASSETS / "gfx_wolverine.bin").read_bytes()
resident = set(A["stage_keys"]["02"])
w = lambda b, a: int.from_bytes(b[a:a + 2], "big")
l = lambda b, a: int.from_bytes(b[a:a + 4], "big")
s16 = lambda v: v - 65536 if v >= 32768 else v
s8 = lambda v: v - 256 if v >= 128 else v

# ---- the donor span and its named changes
LO, END, WIN, FIRST_REC = 0x162f90, 0x167580, 0x300000, 0x163158
D = WIN - LO
TABLES = ((0x162f90, 80), (0x163032, 33), (0x163074, 65), (0x1630f6, 49))
STAND, WALK, LP = 0x163158, 0x1631b0, 0x163644
blk = bytearray(rom[LO:END])


def chain_ok(a):
    for _ in range(200):
        if not (LO <= a < END): return False
        if w(rom, a + 2) & 0x8000: return LO <= l(rom, a + 16) < END
        a += 16
    return False


recs, todo = {}, []
for b, n in TABLES:
    for i in range(n):
        a = b + s16(w(rom, b + 2 * i))
        if a >= FIRST_REC and chain_ok(a): todo.append(a)
while todo:
    a = todo.pop()
    while a not in recs:
        fl = w(rom, a + 2); recs[a] = fl
        if fl & 0x8000:
            t = l(rom, a + 16)
            if t not in recs: todo.append(t)
            break
        a += 16
donor_chain = lambda a: [x for x in range(a, a + 16 * 40, 16)][:next(k for k in range(40) if w(rom, a + 16 * k + 2) & 0x8000) + 1]

# ---- tile mapping (the weighted pixel distance of tilemerge.py: a colour change 1, opaque against transparent 3; resident tiles within K of a ROM tile stand for it)
import numpy as np
K = int(__import__("os").environ.get("WV_MERGE_K", "12"))
ALPHA = 3
rk = sorted(resident)
RX = np.stack([np.array(assets.pens(keyraw[k * 128:k * 128 + 128]), dtype=np.uint8).reshape(256) for k in rk])
miss = {"near": 0, "exact": 0}
_kc = {}


def key_of(code):
    """(key, hflip, vflip) such that the resident key's tile drawn with those flips is within K of the ROM tile, or None for a blank tile; "far" when none is within K."""
    if code in _kc: return _kc[code]
    px = np.array(assets.pens(gfx[code * 128:code * 128 + 128]), dtype=np.uint8)
    if (px == 15).all():
        _kc[code] = None; return None
    best = None
    for f, (h, v) in enumerate(((0, 0), (1, 0), (0, 1), (1, 1))):
        q = px[:, ::-1] if h else px
        q = q[::-1, :] if v else q
        u = q.reshape(1, 256)
        d = (((u != RX) & (u != 15) & (RX != 15)).sum(1) + ALPHA * ((u == 15) != (RX == 15)).sum(1))
        i = int(d.argmin())
        if best is None or d[i] < best[0]: best = (int(d[i]), rk[i], h, v)
    miss["exact" if best[0] == 0 else "near"] += 1
    _kc[code] = (best[1], best[2], best[3]) if best[0] <= K else "far"
    return _kc[code]


# ---- MSHvSF's data
FEET = 13


def mv_rect(i):
    x, xr, y, yr = s16(w(mv, 0x3a2000 + (i & 0x1fff) * 8)), w(mv, 0x3a2000 + (i & 0x1fff) * 8 + 2), s16(w(mv, 0x3a2000 + (i & 0x1fff) * 8 + 4)), w(mv, 0x3a2000 + (i & 0x1fff) * 8 + 6)
    return (-x - xr, -x + xr, -y - yr + FEET, -y + yr + FEET)


def union(a, b):
    return b if a is None else (min(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), max(a[3], b[3]))


def mv_chain(a):
    out = []
    while True:
        out.append(a)
        if w(mv, a + 2) & 0x8000: return out
        a += 16


def mv_boxes(rec):
    e = 0x1ce0f2 + l(mv, rec + 12) * 16
    ids = [w(mv, e + 2 * k) for k in range(8)]
    hit = next((i for i in ids[:2] if i and not i & 0x8000), None)
    hurt = None
    for i in ids[2:6]:
        if i: hurt = union(hurt, mv_rect(i))
    return (mv_rect(hit) if hit else None), hurt


def mv_pose(rec):
    """cells of a record's assembly: [(x, y, key, hflip, vflip, pal)] with x, y relative to his origin (MSHvSF draws facing left unflipped, as the AvP emitter does for facing 0)."""
    ap = l(mv, rec + 4)
    n = w(mv, ap + 4); tab = l(mv, ap + 6)
    px, py = s16(w(mv, tab + 2)), s16(w(mv, tab + 4))
    cells = []; far = []
    for i in range(n + 1):
        if i:
            px += s8(mv[tab + 6 + 2 * (i - 1)]); py += s8(mv[tab + 7 + 2 * (i - 1)])
        code, at = w(mv, ap + 10 + 4 * i), w(mv, ap + 12 + 4 * i)
        wd, ht, hf, vf, pal = ((at >> 8) & 15) + 1, ((at >> 12) & 15) + 1, (at >> 5) & 1, (at >> 6) & 1, at & 0x1f
        for by in range(ht):
            for bx in range(wd):
                kk = key_of(code + bx + 16 * by)
                if kk is None: continue
                if kk == "far": far.append(code + bx + 16 * by); continue
                cx = px + 16 * ((wd - 1 - bx) if hf else bx)
                cy = py + 16 * ((ht - 1 - by) if vf else by)
                cells.append((cx, cy, kk[0], hf ^ kk[1], vf ^ kk[2], pal))
    mv_pose.far = len(far)
    return cells


def resident_pose(rec):
    """False when a cell had to take a non-exact tile (its picture is not in the stage packs)."""
    c = mv_pose(rec)
    return c, mv_pose.far == 0


# ---- native chains
asm_blob, asm_at = bytearray(), {}


def assembly(cells):
    """family 0xA assembly bytes for the cells; palette 12 -> row 1 (Schaefer's, WV_SCH_PAL), 13 -> the second row (patched per stage)."""
    b = bytearray()
    be = lambda v: (v & 0xffff).to_bytes(2, "big")
    b += be(0x000a) + be(len(cells)) + be(len(cells)) + be(0) + be(0) + be(0xfff5)
    for cx, cy, k, hf, vf, pal in cells:
        b += be(k) + be(vf << 6 | hf << 5 | 1) + be(cx) + be(cy - FEET)
    return bytes(b)


p1_marks = []   # (asm index, byte offset in that assembly) of attr low bytes that are second-row tiles
poses = []      # unique assemblies
pose_of = {}


def pose_id(cells):
    key = tuple(cells)
    if key not in pose_of:
        pose_of[key] = len(poses); poses.append(cells)
    return pose_of[key]


def thin(chain, want_flags=None):
    """keep the records whose poses are fully resident; a dropped record's ticks go to the one before it"""
    keep = []
    for r in chain:
        cells, ok = resident_pose(r)
        dur = w(mv, r + 2) & 0x7fff
        if ok or not keep:
            keep.append([r, cells, dur])
        else:
            keep[-1][2] += dur
    return keep


idle_src = thin(mv_chain(0xd1c90))
walk_src = thin(mv_chain(0xd1da4))
lp_chain = mv_chain(0xd2878)
lp_src = thin(lp_chain)
print("idle %d of %d records kept, walk %d of %d, lp %d of %d; tile cells exact %d, merged-near %d" % (
    len(idle_src), len(mv_chain(0xd1c90)), len(walk_src), len(mv_chain(0xd1da4)), len(lp_src), len(lp_chain), miss["exact"], miss["near"]))

# hurt and attack box entries of T'
hurt_new, atk_new = [], []   # unique (fwd0, fwd1, up0, up1) rectangles -> indexes after the donor's


def cwbytes(r):
    c = lambda a, b: max(-128, min(127, (a + b) // 2))
    h = lambda a, b: max(1, min(255, (b - a + 1) // 2))
    return ((-c(r[0], r[1])) & 0xff, c(r[2], r[3]) & 0xff, h(r[0], r[1]), h(r[2], r[3]))


def hurt_index(r):
    if r is None: return 0
    if r not in hurt_new: hurt_new.append(r)
    return 12 + hurt_new.index(r)


def atk_index(r):
    if r is None: return 0
    if r not in atk_new: atk_new.append(r)
    return 38 + atk_new.index(r)


# donor skeletons
def skel(start):
    return donor_chain(start)


recs_out = []   # native records as dicts, chains laid out later
idle_recs = [dict(src=r, cells=c, dur=min(d, 4095), flags=0, hurt=hurt_index(mv_boxes(r)[1]), atk=0, b10=0, b11=rom[STAND + 11], tail=rom[STAND + 12:STAND + 16]) for r, c, d in idle_src]
idle_recs[-1]["jump"] = "idle"
idle_recs[-1]["flags"] = 0x8000

# walk: Schaefer's 12 records give duration, flags, event bytes and shadow; the pose is his walk pose at the same phase of the cycle
wd = skel(WALK)
wtot = sum(w(rom, a) for a in wd[:-1]) or 1
mtot = sum(r[2] for r in walk_src)
walk_recs = []
cum = 0
for a in wd:
    dur = w(rom, a); last = bool(w(rom, a + 2) & 0x8000)
    mid = cum + dur / 2.0
    cum += dur
    t = (mid / wtot) * mtot
    acc = 0
    pick = walk_src[-1]
    for r in walk_src:
        if acc + r[2] > t: pick = r; break
        acc += r[2]
    walk_recs.append(dict(src=pick[0], cells=pick[1], dur=dur, flags=w(rom, a + 2), hurt=hurt_index(mv_boxes(pick[0])[1]), atk=0, b10=rom[a + 10], b11=rom[a + 11], tail=rom[a + 12:a + 16], jump=("walk" if last else None)))
# the donor chain's last record is the loop-back record (flags bit 15 + its own target); keep the target as the walk start

# first claw attack: Schaefer's chain flags skeleton (startup 0, live 1, terminal 0x8001), his six records' durations and poses, his boxes
lp_recs = []
for i, (r, c, d) in enumerate(lp_src):
    hit, hurt = mv_boxes(r)
    lp_recs.append(dict(src=r, cells=c, dur=d, flags=0 if i == 0 else 1, hurt=hurt_index(hurt), atk=atk_index(hit), b10=0, b11=rom[LP + 11] if i == 0 else rom[LP + 16 + 11], tail=rom[LP + 12:LP + 16]))
# the terminal record: the last pose held, 4095 ticks, flags 0x8001, jump to itself (the donor's own shape)
last = dict(lp_recs[-1]); last.update(dur=4095, flags=0x8001, jump="self", atk=0)
lp_recs.pop()   # MSHvSF's own hold record (6 ticks, jump to itself) is the terminal
lp_recs.append(last)

# ---- layout
off = (len(blk) + 15) & ~15
REC_LO = off
layout = {}
for name, rs in (("idle", idle_recs), ("walk", walk_recs), ("lp", lp_recs)):
    layout[name] = off
    for r in rs: r["at"] = off; off += 20 if (r["flags"] & 0x8000) else 16
REC_END = off
assert REC_END < 0x7000, "records must stay within the 16-bit offsets of the tables"
asm_off = (off + 3) & ~3
asm_where = {}
for rs in (idle_recs, walk_recs, lp_recs):
    for r in rs:
        pid = pose_id(r["cells"])
        r["pose"] = pid
for pid, cells in enumerate(poses):
    asm_where[pid] = asm_off
    ab = assembly(cells)
    for i, c in enumerate(cells):
        if c[5] == 13: p1_marks.append(asm_off + 12 + 8 * i + 3)
    asm_blob += ab; asm_off += len(ab)
T_off = (asm_off + 3) & ~3

# T': the donor table with the new hurt boxes after its 12 entries, then the attack table (38 donor entries and the new ones)
donor_T_addr = 0x11b166
hurt_d = [rom[donor_T_addr + 4 + 8 * i:donor_T_addr + 12 + 8 * i] for i in range(12)]
atk_d = [rom[donor_T_addr + 0x64 + 16 * i:donor_T_addr + 0x74 + 16 * i] for i in range(38)]
htmpl, atmpl = hurt_d[1], atk_d[1]
hurt_b = hurt_d + [bytes(cwbytes(r)) + htmpl[4:8] for r in hurt_new]
atk_b = atk_d + [bytes(cwbytes(r)) + atmpl[4:16] for r in atk_new]
T = bytearray()
T += (4).to_bytes(2, "big") + (4 + 8 * len(hurt_b)).to_bytes(2, "big")
for b in hurt_b: T += b
for b in atk_b: T += b
T_end = T_off + len(T)
assert T_end <= 0x10000

# ---- write the block
full = bytearray(0x10000)
full[:len(blk)] = blk
# donor jump targets and the chain names
chain_at = {STAND: WIN + layout["idle"], WALK: WIN + layout["walk"], LP: WIN + layout["lp"]}
for a, fl in recs.items():
    if fl & 0x8000:
        t = l(rom, a + 16)
        full[a + 16 - LO:a + 20 - LO] = (chain_at.get(t, t + D)).to_bytes(4, "big")
tchanged = 0
for b, n in TABLES:
    for i in range(n):
        tgt = b + s16(w(rom, b + 2 * i))
        if tgt in chain_at:
            nv = chain_at[tgt] - (b + D)
            assert -32768 <= nv < 32768
            full[b + 2 * i - LO:b + 2 * i - LO + 2] = (nv & 0xffff).to_bytes(2, "big"); tchanged += 1
for rs in (idle_recs, walk_recs, lp_recs):
    for r in rs:
        o = r["at"]
        full[o:o + 2] = r["dur"].to_bytes(2, "big")
        full[o + 2:o + 4] = r["flags"].to_bytes(2, "big")
        full[o + 4:o + 8] = (WIN + asm_where[r["pose"]]).to_bytes(4, "big")
        full[o + 8] = r["hurt"]; full[o + 9] = r["atk"]; full[o + 10] = r["b10"]; full[o + 11] = r["b11"]
        full[o + 12:o + 16] = bytes(r["tail"])
        if r["flags"] & 0x8000:
            tgt = {"idle": WIN + layout["idle"], "walk": WIN + layout["walk"], "self": WIN + o}[r["jump"]]
            full[o + 16:o + 20] = tgt.to_bytes(4, "big")
pos = (REC_END + 3) & ~3
full[pos:pos + len(asm_blob)] = asm_blob
assert pos == (REC_END + 3) & ~3 and pos + len(asm_blob) <= T_off
full[T_off:T_off + len(T)] = T
size = T_end
# ---- OPX slots (the target patches them), the box-table slot
ox = (WORK / "opx.bin").read_bytes()
oj = json.loads((WORK / "opx.json").read_text())
inv = sorted((v, int(k, 16)) for k, v in oj.items())
slots = [i for i in range(0, len(ox) - 3, 2) if int.from_bytes(ox[i:i + 4], "big") in {t for t, _ in TABLES}]
tslot = None
for i in range(0, len(ox) - 3, 2):
    if int.from_bytes(ox[i:i + 4], "big") == donor_T_addr:
        a = max((o, ad) for o, ad in inv if o <= i); src = a[1] + i - a[0]
        if src == 0x19744 + 4: tslot = i
assert tslot is not None, "the per-character box table slot (0x19748) is not in the opcode store"
lines = [
    "/* Generated by tools/wolverine/gen_native.py: do not commit (ROM-derived). */",
    "#define WV_NAT_DELTA 0x%xu" % D,
    "#define WV_NAT_WIN 0x%xu" % WIN,
    "#define WV_NAT_REC_LO 0x%xu   /* first native record (window address) */" % (WIN + layout["idle"]),
    "#define WV_NAT_REC_END 0x%xu" % (WIN + REC_END),
    "#define WV_NAT_SIZE %d" % size,
    "#define WV_NAT_T 0x%xu   /* his box table T' */" % (WIN + T_off),
    "#define WV_NAT_T_DONOR 0x%xu" % donor_T_addr,
    "#define WV_NAT_TSLOT %du   /* opcode-store offset of the per-character box table entry of character 1 */" % tslot,
    "#define WV_RELOC_SLOTS %d" % len(slots),
    "static const unsigned int wv_reloc_slots[%d] = {%s};" % (len(slots), ",".join(map(str, slots))),
    "#define WV_NAT_NP1 %d" % len(p1_marks),
    "static const unsigned short wv_nat_p1[%d] = {%s};" % (max(1, len(p1_marks)), ",".join(map(str, p1_marks)) if p1_marks else "0"),
    "static unsigned char wv_blk[WV_NAT_SIZE] __attribute__((aligned(4))) = {%s};" % ",".join(map(str, full[:size])),
]
OUT.write_text("\n".join(lines) + "\n")
print("block: donor span %d bytes, native records %d..%d (%d B), assemblies %d (%d B, %d second-row tiles), T' %d B (hurt %d + %d new, attack %d + %d new); %d table entries and %d donor jump targets renamed; total %d bytes" % (
    len(blk), REC_LO, REC_END, REC_END - REC_LO, len(poses), len(asm_blob), len(p1_marks), len(T), 12, len(hurt_new), 38, len(atk_new), tchanged,
    sum(1 for a, fl in recs.items() if fl & 0x8000 and l(rom, a + 16) in chain_at), size))
print("slots", len(slots), "tslot", tslot)
