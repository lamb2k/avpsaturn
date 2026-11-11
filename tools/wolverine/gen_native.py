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
Step 2 (11-09): every chain of the 227 index entries is native. Idle, walk and the first claw attack keep their ROM-timed chains; every other chain keeps the donor's
skeleton (durations, flags = root-motion index and sub-state trigger, +10/+11/+12..15 bytes, jump structure) and takes its poses and boxes from a role's MSHvSF chain
(ROLE table below; resident tiles only, a dropped record's ticks go to the record before it). Nothing of Schaefer's records is copied; only his index tables are.
usage: gen_native.py WORK ASSETS_DIR MSHVSF_DUMP OUT.inc"""
import json, os, pathlib, sys

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
blk = bytearray(rom[LO:FIRST_REC])   # the index tables only; the records are rebuilt below


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
FEET = int(os.environ.get("WV_FEET", "14"))   # the feet line below the origin's row. 13 put his soles 2 screen px (stand) to 7 px (walk) lower than stock Schaefer's against the game's shadow (Yaba 11-10, shad1): the ellipse is the stock one (same rows, same order), so the poses move up one row


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


MASS_RECS = set()   # records whose pose keeps only its largest connected group of cells (arcade effect sprites drawn apart from the body are dropped: 12.2, which would otherwise carry a slash spark far below the body and raise the whole pose)


def main_mass(items):
    """items: [(cx, cy, ...)]; keeps the largest group of cells connected by touching (16 px) neighbours"""
    n = len(items); comp = list(range(n))
    def find(a):
        while comp[a] != a: comp[a] = comp[comp[a]]; a = comp[a]
        return a
    for i in range(n):
        for j in range(i + 1, n):
            if abs(items[i][0] - items[j][0]) <= 16 and abs(items[i][1] - items[j][1]) <= 16: comp[find(i)] = find(j)
    groups = {}
    for i in range(n): groups.setdefault(find(i), []).append(items[i])
    return max(groups.values(), key=len) if groups else []


def mv_pose(rec):
    """cells of a record's assembly: [(x, y, key, hflip, vflip, pal)] with x, y relative to his origin (MSHvSF draws facing left unflipped, as the AvP emitter does for facing 0)."""
    ap = l(mv, rec + 4)
    n = w(mv, ap + 4); tab = l(mv, ap + 6)
    px, py = s16(w(mv, tab + 2)), s16(w(mv, tab + 4))
    allc = []
    for i in range(n + 1):
        if i:
            px += s8(mv[tab + 6 + 2 * (i - 1)]); py += s8(mv[tab + 7 + 2 * (i - 1)])
        code, at = w(mv, ap + 10 + 4 * i), w(mv, ap + 12 + 4 * i)
        wd, ht, hf, vf, pal = ((at >> 8) & 15) + 1, ((at >> 12) & 15) + 1, (at >> 5) & 1, (at >> 6) & 1, at & 0x1f
        for by in range(ht):
            for bx in range(wd):
                kk = key_of(code + bx + 16 * by)
                if kk is None: continue
                cx = px + 16 * ((wd - 1 - bx) if hf else bx)
                cy = py + 16 * ((ht - 1 - by) if vf else by)
                allc.append((cx, cy, code + bx + 16 * by, kk, hf, vf, pal))
    if rec in MASS_RECS: allc = main_mass(allc)
    cells = []; far = []
    for cx, cy, c, kk, hf, vf, pal in allc:
        if kk == "far": far.append(c); continue
        cells.append((cx, cy, kk[0], hf ^ kk[1], vf ^ kk[2], pal))
    mv_pose.far = len(far); mv_pose.far_codes = far
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
        b += be(k) + be(vf << 6 | hf << 5 | (0 if pal == 13 else 1)) + be(cx) + be(cy - FEET)   # second-row tiles carry palette 0 until the runtime writes the stage's row (the first row is always 1)
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


def thin_strict(chain):
    """records whose tiles are all resident; a dropped record's ticks go to the previous kept one (the first kept one takes the leading ticks)"""
    keep, lead = [], 0
    for r in chain:
        cells, ok = resident_pose(r)
        dur = w(mv, r + 2) & 0x7fff
        if ok and cells:
            keep.append([r, cells, dur + lead]); lead = 0
        elif keep: keep[-1][2] += dur
        else: lead += dur
    return keep



# MSHvSF entry addresses: the 27 sub-tables at 0xd1a7e (mvlib.MV.tables)
def mv_tables():
    subs, cur, a = [], None, 0xd1a7e
    while a < 0xd1c90:
        v = w(mv, a)
        if v == 0: cur = None
        else:
            if cur is None:
                cur = [a, []]; subs.append(cur)
            cur[1].append(cur[0] + s16(v))
        a += 2
    return subs


SUBS = mv_tables()
SRC_ADDR = {(si, ei): ts[ei] for si, (b, ts) in enumerate(SUBS) for ei in range(len(ts))}

WV_REMAP = os.environ.get("WV_REMAP", "1") != "0"   # owner-approved essentials remap; WV_REMAP=0 builds the 11-10 mapping (comparison only)
SRC = dict(IDLE=(0, 0), WALK=(0, 1), JUMP=(1, 0), LAND=(1, 3), LP1=(8, 0), LP2=(8, 3), HP=(8, 2), GRAB_HOLD=(8, 3), GRAB_SLAM=(8, 2), HK=(9, 2), HIT_M=(14, 2), HIT_E=(14, 3), HIT_H=(14, 4), BERS=(22, 10), BERS3=(22, 10), JATK=(1, 0), GRAB_LIFT=(8, 3), LYING=(1, 3), GETUP=(1, 3), ENTR=(0, 1))
if WV_REMAP:   # essentials remap (REVIEW_ANSWER.md 11-10, MAME-confirmed identities): (sub, entry, record indexes); records not named are not used, so their tiles are not added to the pack
    SRC.update(LP1=(8, 1, (2, 5, 6)),          # standing medium punch, the double claw's first thrust and its hold (the second hit, 8.4, reuses these frames)
               JATK=(12, 2, (1, 2)),           # jumping heavy punch: the downward claw slash
               GRAB_HOLD=(16, 2, (3, 5)),      # forward + heavy punch throw: the 48-tick hold and the stab
               GRAB_LIFT=(16, 0, (1,)),        # forward + medium punch throw: the hop up (Schaefer's code leaps off the held enemy, state 020406)
               GRAB_SLAM=(16, 0, (5,)),        # ... and the stab down (state 020408)
               LYING=(14, 31, (0,)),           # lying on the ground after a knockdown
               GETUP=(22, 5), ENTR=(23, 3),    # all records already resident
               BERS=(22, 23, (1,)), BERS3=(22, 24, (1,)),
               HIT_H=((14, 4) + ((tuple(int(x) for x in os.environ.get("WV_HITH_SUB", "0,2,4,6").split(",")),) if os.environ.get("WV_HITH_SUB", "0,2,4,6") != "all" else ())),   # the heavy-hit tumble (flight and heavy flinch) draws 4 of its 7 poses: 424 B of the cart tail (WV_HITH_SUB=all: every pose)
               HIT_E=((14, 3) + ((tuple(int(x) for x in os.environ["WV_HITE_SUB"].split(",")),) if os.environ.get("WV_HITE_SUB") else ())),
               BZ_START=(22, 22, (1,)), BZ_A=(22, 23, (1,)), BZ_B=(22, 24, (1,)), BZ_END=(22, 25, (0,)))   # the Berserker Barrage (QCF + punch, then taps): 22.22 start, 22.24 / 22.23 strikes, 22.25 end

if WV_REMAP:
    for _a in mv_chain(SRC_ADDR[(12, 2)]): MASS_RECS.add(_a)

if os.environ.get("WV_ADD"):
    # make_d12.py step 1: write ASSETS + the tiles the remap frames need (a tile with no resident tile within the merge distance, deduplicated among themselves) at free AvP sprite keys.
    # Output dir WV_ADD = a copy of ASSETS with gfx_wolverine.bin carrying the new tiles, remap.json keys + stage_keys (every stage) extended. Nothing else changes.
    import shutil
    frames = sorted({(v[0], v[1], i) for v in SRC.values() if len(v) > 2 for i in v[2]})
    codes = []
    for si, ei, idx in frames:
        mv_pose(mv_chain(SRC_ADDR[(si, ei)])[idx])
        for c in mv_pose.far_codes:
            if c not in codes: codes.append(c)
    added, ax = [], []   # representative code, pens
    for c in codes:
        px = np.array(assets.pens(gfx[c * 128:c * 128 + 128]), dtype=np.uint8)
        hit = False
        for h, v in ((0, 0), (1, 0), (0, 1), (1, 1)):
            q = px[:, ::-1] if h else px
            q = q[::-1, :] if v else q
            u = q.reshape(1, 256)
            for o in ax:
                if (((u != o) & (u != 15) & (o != 15)).sum() + ALPHA * ((u == 15) != (o == 15)).sum()) <= K: hit = True; break
            if hit: break
        if not hit:
            added.append(c); ax.append(px.reshape(1, 256))
    R = json.loads((WORK / "rounds.json").read_text())
    used = set()
    for f in R["files"]: used |= set(f["keys"][0])
    for ln in open(WORK / "screen_keys.txt"):
        if ln.strip() and ln.split()[0] == "0": used.add(int(ln.split()[1], 16))
    have = set(A["keys"])
    free = [k for k in range(1, 0x10000) if k not in used and k not in have]
    free.sort(key=lambda k: (keyraw[k * 128:k * 128 + 128] != b"\xff" * 128, k))
    if len(free) < len(added): raise SystemExit("not enough free sprite keys")
    newkeys = free[:len(added)]
    outd = pathlib.Path(os.environ["WV_ADD"])
    if outd.exists(): shutil.rmtree(outd)
    shutil.copytree(ASSETS, outd)
    raw = bytearray(keyraw)
    for k, c in zip(newkeys, added): raw[k * 128:k * 128 + 128] = gfx[c * 128:c * 128 + 128]
    (outd / "gfx_wolverine.bin").write_bytes(raw)
    B = json.loads((ASSETS / "remap.json").read_text())
    B["keys"] = B["keys"] + newkeys
    B["stage_keys"] = {st: sorted(set(v) | set(newkeys)) for st, v in B["stage_keys"].items()}
    B["wv_added"] = dict(keys=newkeys, codes=added, frames=["%d.%d#%d" % f for f in frames])
    (outd / "remap.json").write_text(json.dumps(B))
    print("ADD: %d frames, %d far cells' codes, %d new tiles at keys %d..%d -> %s" % (len(frames), len(codes), len(added), min(newkeys) if newkeys else 0, max(newkeys) if newkeys else 0, outd))
    raise SystemExit(0)


idle_src = thin(mv_chain(0xd1c90))
walk_src = thin(mv_chain(0xd1da4))
if WV_REMAP:
    # The main attack is the double claw: standing medium punch 8.1 (the arcade's MP, MP is 8.1 then 8.4; the second hit reuses the first's frames). Frames 2 and 5 are the thrust and its hold; 6 is resident.
    lp_chain = mv_chain(SRC_ADDR[(8, 1)]); lp_src = thin_strict([lp_chain[i] for i in (2, 5, 6)])
else:
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


# ---- donor skeletons and the role table (step 2)
def skel(start):
    return donor_chain(start)


_sole_cache = {}


def tile_rows(key):
    """(first, last) opaque pixel row of a resident tile as stored (None for an empty tile)"""
    if key not in _sole_cache:
        px = assets.pens(keyraw[key * 128:key * 128 + 128])
        rows = [y for y in range(16) if any(px[y][x] != 15 for x in range(16))]
        _sole_cache[key] = (rows[0], rows[-1]) if rows else None
    return _sole_cache[key]


def sole_of(cells):
    """lowest opaque pixel row of a pose in its own coordinates (the pose's feet line)"""
    best = None
    for cx, cy, k, hf, vf, pal in cells:
        r = tile_rows(k)
        if r is None: continue
        low = cy + (15 - r[0] if vf else r[1])
        best = low if best is None else max(best, low)
    return best


# Hurt boxes (owner-visible, 11-10): the engine lets a hit land only when the target's record names a hurt box (index 0 = none: the collision pass f_1cf54 refuses at once). Schaefer's records name none
# during hit reactions, knockdown, getup, landing and his special, so he is not hittable there; a record whose donor names none keeps none (the box also floated above the lying poses). A named MSHvSF box is
# used only where it covers the pose it belongs to (tucked jump poses carry a box 45 px above the pose).
def hurt_or_donor(rom_hurt, rect, cells):
    """hurt index for a floor-aligned record: 0 where the donor names none; the MSHvSF box where it covers at least half of the pose's height; else the donor's own index
    (MSHvSF's box of a tucked jump pose stands 45 px above the pose: leap launch and landing): the idle's standing box, as the donor's index 1 is
    (only reached for records whose donor names a box, so the lying/flight states stay at 0)"""
    if rom_hurt == 0: return 0
    if rect is None: return idle_recs[0]["hurt"]
    rows = [(cy - FEET + (15 - tile_rows(k)[1] if vf else tile_rows(k)[0]), cy - FEET + (15 - tile_rows(k)[0] if vf else tile_rows(k)[1])) for cx, cy, k, hf, vf, pal in cells if tile_rows(k)]
    if rows:
        top, bot = min(r[0] for r in rows), max(r[1] for r in rows)
        ov = min(bot, -rect[2]) - max(top, -rect[3])
        if ov * 2 < bot - top:
            report.append('hurt box of a pose off its body: standing box kept (donor index %d)' % rom_hurt)
            return idle_recs[0]["hurt"]
    return hurt_index(rect)


def floor_cells(cells, lift=0):
    """MSHvSF puts its own height into a pose (jump, hit flight, getup); AvP's game moves the actor for those, so a state the game lifts shows his pose with the sole on the stance's
    floor line (the idle's first pose). lift = extra px up (the leap arc, which the game does not move)"""
    d = FLOOR_SOLE - sole_of(cells) - lift
    return [(cx, cy + d, k, hf, vf, pal) for cx, cy, k, hf, vf, pal in cells]


# MSHvSF animation index entries (sub-table, entry), tools/wolverine/mvlib.py MV.tables(); provenance by tile match of D11's poses (census note section 5)
# (SRC: defined with the MSHvSF entry tables above)
# role: donor chain -> (source, hold_at): hold_at = where in the source (0..1) the donor's long hold record (255+ ticks) takes its pose; None = the last pose
# first slot naming the chain decides; the table below is the first assignment (provisional where the state is not identified, listed in the census note)
ROLE_T1 = {1: "IDLE", 3: "JUMP", 4: "LAND", 5: "LAND", 6: "LAND", 7: "IDLE", 8: "IDLE", 9: "IDLE", 10: "JUMP", 11: "IDLE", 12: "IDLE", 13: "IDLE", 14: "HK", 16: "HK",
           17: "IDLE", 18: "HP", 19: "IDLE", 20: "LAND", 21: "IDLE", 22: "IDLE", 23: "IDLE", 29: "IDLE", 30: "IDLE", 31: "IDLE", 34: "LP2", 35: "HP", 36: "BERS",
           37: "IDLE", 38: "JUMP", 39: "IDLE", 40: "IDLE", 41: "HK", 42: "BERS", 43: "IDLE", 48: "HIT_H", 49: "HIT_H", 50: "HIT_H", 51: "HIT_H", 52: "HIT_H", 53: "HIT_H",
           54: "HIT_H", 55: "HIT_H", 56: "LAND", 57: "IDLE", 59: "WALK", 61: "IDLE", 62: "IDLE", 63: "IDLE", 64: "IDLE", 65: "IDLE", 66: "IDLE", 67: "HP", 68: "HP", 69: "HP",
           70: "HP", 71: "IDLE", 72: "IDLE", 73: "IDLE", 74: "IDLE", 75: "IDLE", 76: "HP", 77: "HP", 78: "IDLE", 79: "IDLE"}
HOLD_AT = dict(JUMP=0.45, LAND=1.0, IDLE=0.0)
# Comparison knobs (owner 11-09: every timing change ships as a comparison first). Defaults are the standing decisions.
#   Owner 11-10 ("ok all slashes"): the default is variant B, LP LP HP with the 12-tick heavy punch; A (WV_HP_TICKS=0) and C (WV_CHAIN=4) stay as switches for comparison only.
#   WV_CHAIN=3 (default): the attack chain is LP, LP, HP. Schaefer's state routine has four stages (0..3, slots T1.32..35, stage 3 follows only after a connect on stage 2); stages 0 and 1 are the
#                         first claw attack, stage 2 (slot T1.34) his heavy punch, and the stage counter wraps after stage 2 (build.py rewrites its two `& 3` sites to the count wolverine.c sets).
#   WV_CHAIN=4          : LP, LP, HP, HK (stage 3, slot T1.35, is his kick).
#   WV_HP_TICKS=N       : the heavy punch's length in ticks. 0 = the donor's heavy stage skeleton (variant A) (slot T1.35: 2, 2, 6, 5, 3 = 18 ticks, no cancel flags); N rescales its durations to N ticks (default 12, as quick as
#                         the planned light punches).
WV_CHAIN = int(os.environ.get("WV_CHAIN", "3"))
WV_HP_TICKS = int(os.environ.get("WV_HP_TICKS", "12"))
WV_T3_SHARE = int(os.environ.get("WV_T3_SHARE", "1"))   # 1: the 48 T3 slots (the stock gun action's aim chains, unused by his native Berserker) share one chain; 0: one chain each (3.2 KB more)
t3_shared = []
assert WV_CHAIN in (3, 4)
HP_SLOT, HK_SLOT = 0x163688, 0x1636dc   # donor chain starts of T1.34 (stage 2) and T1.35 (stage 3)
# Owner 11-10 ("why does wolverine still kick": all slashes means no kick anywhere): the three slots Schaefer's donor uses for a kick-like swing take claw slashes of his resident set.
#   T1.41  state 02000a, the air attack (jump + attack; donor records 2 and 3 carry attack boxes 12 and 21): HP slash
#   T1.16  state 02000e, entered by the player action-request path (f_1ab1a; donor attack box 8 on its second record): HP slash
#   T1.14  the 2-record pose of the stand handler f_198b0 (no attack box): the first light slash
# WV_KICK=1 (comparison build only) restores the MSHvSF kick poses (role HK) in all three, as chain C does for the stage-3 slot.
if os.environ.get("WV_KICK") != "1":
    ROLE_T1[41] = ROLE_T1[16] = "HP"; ROLE_T1[14] = "LP1"
# Owner 11-10 ("he shouldn't be randomly jumping"): the donor's leap launch (T1.3, also the stage entrance T0.3) and landing (T1.10, T0.10) chains are 2-record knee-bend holds, not the airborne part (the arc is
# T1.37, only with a jump press). With his JUMP poses (the tucked flight) they showed him jumping at every stage entrance; they take his crouch (LAND) poses. WV_LEAP_TUCK=1 restores the tucked poses.
if os.environ.get("WV_LEAP_TUCK") != "1":
    ROLE_T1[3] = ROLE_T1[10] = "LAND"
# Owner 11-10 ("keep his grab and just find a better pose"): the grab states keep the stock timing, flags and boxes; their poses were hit recoils (HIT_H) and a landing crouch: now claw holds
# (T1.48 to 54, state 0204xx: the grab and the hold; T1.55, 020406: the lift) take his second light slash, and the slam (T1.56, 020408, the stomp with the donor's attack box 24) his heavy punch.
# WV_GRAB_OLD=1 restores the recoil and crouch poses.
if os.environ.get("WV_GRAB_OLD") != "1":
    for _i in range(48, 56): ROLE_T1[_i] = "GRAB_HOLD"
    ROLE_T1[56] = "GRAB_SLAM"
if WV_REMAP:
    # Essentials remap (REVIEW_ANSWER.md 11-10). The auto grab is 020400 (hold: T1.48..54), 020406 (T1.55: Schaefer's code leaps off the held enemy) and 020408 (T1.56: the stomp), then T1.57.
    # The arcade's two throws give the poses: the heavy-punch throw 16.2 holds and stabs, the medium-punch throw 16.0 hops up (T1.55) and stabs down (T1.56); after the stomp he lands (1.3).
    ROLE_T1[55] = "GRAB_LIFT"; ROLE_T1[56] = "GRAB_SLAM"; ROLE_T1[57] = "LAND"
    ROLE_T1[41] = "LP1"      # the lunge (02000a) is a forward thrust: the double claw's frames, no longer the tall upward slash 8.2
    ROLE_T1[38] = "JATK"     # the air attack of the leap (T1.40 is never reached in the census and keeps its idle)
    for _i in range(64, 80): ROLE_T1[_i] = "LP1"   # state 020014 (T1.64..79): the attack pressed while an enemy has seized him (the player block's +0x5a link word is set), a break-free attack: the 8.1 thrust (their attack boxes stay the donor's)
    HOLD_AT["GRAB_HOLD"] = 0.0   # the donor's long hold record shows the held pose (16.2 frame 3), the timed records after it show the stabs
ROLE_T1[34] = "HP"
ROLE_T1[35] = "HK" if WV_CHAIN == 4 else "HP"
role_of = {}   # donor chain start -> (role name, source key)


def chain_role(start, first):
    t, i = first
    if t == "T1" and i in ROLE_T1: return ROLE_T1[i]
    if WV_REMAP and t == "T0" and i == 24: return "ENTR"   # the entrance's closing chain: the landing after Weapon X (23.3), resident and free
    if t == "T3": return "BERS3"   # T3 = the gun action's aim chains (state 02000c = Berserker for him): the flurry poses, one per slot, so the rapid slot cycling animates it
    if t == "T2":
        ch = skel(start)
        sh = {rom[a + 11] for a in ch}
        if i == 0: return "HIT_H"
        if len(ch) >= 9: return "GETUP" if WV_REMAP else "LAND"   # the 9-record chains (getup): 22.5 (crouch to stand) with the remap
        if sh & {13, 15}: return "JUMP" if os.environ.get("WV_KD_JUMP") == "1" else "HIT_H"   # knockdown flight (shadow 13 / 15): the heavy-hit tumble poses (owner 11-10: being knocked down must not look like jumping); WV_KD_JUMP=1 = the old jump poses, comparison only
        if len(ch) == 2 and i in (16, 20, 21, 22, 28, 36, 49, 57): return "LYING" if WV_REMAP else "LAND"   # ground states of the knockdown family
        if i in (54, 63): return "HIT_E"
        return "HIT_M"
    return "IDLE"


def pick_sources(src_key, donor_recs):
    """MSHvSF chain of a role, thinned to the records whose tiles are all resident: [[rec, cells, dur]]"""
    v = SRC[src_key]
    ch = mv_chain(SRC_ADDR[(v[0], v[1])])
    if len(v) > 2: ch = [ch[i] for i in v[2] if i < len(ch)]   # the frames the remap names
    out = thin_strict(ch)
    if len(v) > 2 and not out: raise SystemExit("NO-GO: the remap frames of %s are not resident: GUEST_ASSETS must be a make_d12.py output (or WV_REMAP=0)" % src_key)
    return out


if os.environ.get("WV_EXPLORE"):   # diagnostics: every MSHvSF animation entry, how many of its records are drawable from resident tiles (WV_EXPLORE=<json path>)
    ex = []
    for (si, ei), a0 in sorted(SRC_ADDR.items()):
        ch = mv_chain(a0)
        keep = thin_strict(ch)
        ex.append(dict(sub=si, ent=ei, addr=hex(a0), records=len(ch), resident=len(keep), ticks=sum(w(mv, r + 2) & 0x7fff for r in ch), res_addrs=[hex(k[0]) for k in keep]))
    json.dump(ex, open(os.environ["WV_EXPLORE"], "w"), indent=0)
    print("explore written", len(ex))
    if os.environ.get("WV_EXPLORE_MOVES"):   # which MSHvSF records the skin build's resident poses (D11 remap.json moves) were taken from: same multiset of tile keys
        sig = lambda cells: tuple(sorted(c[2] for c in cells))
        cand = {}
        for (si, ei), a0 in SRC_ADDR.items():
            for r in mv_chain(a0):
                cells, ok = resident_pose(r)
                if ok and cells: cand.setdefault(sig(cells), []).append((si, ei, hex(r)))
        for mv_name in os.environ["WV_EXPLORE_MOVES"].split(","):
            res = []
            for pi, ticks, off in A["moves"][mv_name]:
                pc = A["poses"][pi]
                res.append((pi, ticks, sorted(set((a, b) for a, b, c in cand.get(tuple(sorted(c[2] for c in pc)), [])))[:3]))
            print("MOVE", mv_name, res)
    if os.environ.get("WV_EXPLORE_PNG"):   # pictures of the resident records of the entries named in WV_EXPLORE_SET ("sub.ent,sub.ent")
        from PIL import Image, ImageDraw
        col = A["colours"][A["default_colour"]]
        want = [tuple(int(x) for x in t.split(".")) for t in os.environ["WV_EXPLORE_SET"].split(",")]
        W, H = 110, 120
        rows_ = []
        for se in want:
            keep = thin_strict(mv_chain(SRC_ADDR[se]))
            rows_.append((se, keep[:12]))
        img = Image.new("RGB", (W * 12, H * len(rows_)), (40, 40, 48)); dr = ImageDraw.Draw(img)
        for ri, (se, keep) in enumerate(rows_):
            for ci, (ra, cells, dur) in enumerate(keep):
                ox, oy = ci * W + 55, ri * H + 95
                sole = sole_of(cells)
                for cx, cy, k, hf, vf, pal in cells:
                    px = assets.pens(keyraw[k * 128:k * 128 + 128])
                    for yy in range(16):
                        for xx in range(16):
                            pv = px[15 - yy if vf else yy][15 - xx if hf else xx]
                            if pv != 15:
                                X, Y = ox + cx + xx, oy + cy - (sole or 0) + yy - 16
                                if 0 <= X < img.width and 0 <= Y < img.height: img.putpixel((X, Y), tuple(col[1 if pal == 13 else 0][pv]))
                dr.text((ci * W + 2, ri * H + 2), "%d.%d #%d t%d" % (se[0], se[1], ci, dur), fill=(255, 255, 255))
        img.save(os.environ["WV_EXPLORE_PNG"]); print("explore png", len(rows_))
    raise SystemExit(0)
# first slot naming each distinct donor chain, in table order
first_slot, order = {}, []
for t, (b, n) in (("T1", TABLES[0]), ("T0", TABLES[1]), ("T2", TABLES[2]), ("T3", TABLES[3])):
    for i in range(n):
        a = b + s16(w(rom, b + 2 * i))
        if a >= FIRST_REC and chain_ok(a) and a not in first_slot:
            first_slot[a] = (t, i); order.append(a)

new_chains = {}      # donor chain start -> list of record dicts
report = []


def rescale(recs_, total):
    """durations of a chain's timed records (not the 4095-tick terminal) scaled to `total` ticks, each at least 1"""
    timed = [r for r in recs_ if r["dur"] < 255]
    cur = sum(r["dur"] for r in timed) or 1
    d = [max(1, int(round(r["dur"] * total / cur))) for r in timed]
    k = 0
    while sum(d) != total and k < 100:
        i = max(range(len(d)), key=lambda j: d[j]) if sum(d) > total else min(range(len(d)), key=lambda j: d[j])
        d[i] += -1 if sum(d) > total else 1; k += 1
    for r, v in zip(timed, d): r["dur"] = v


def make_chain(start, role, skel_from=None):
    """donor skeleton + the role's MSHvSF poses by phase; boxes from the same MSHvSF records. skel_from: take the skeleton of another donor chain (the heavy punch of the 3-stage chain sits in
    stage 2's slot and uses the heavy stage's skeleton)"""
    ch = skel(skel_from if skel_from is not None else start)
    src = pick_sources(role, ch)
    dropped = 0
    if not src:
        src = pick_sources("IDLE", ch); role = role + "->IDLE"
    stot = sum(r[2] for r in src) or 1
    dtot = sum(w(rom, a) for a in ch if w(rom, a) < 255) or 1
    has_atk = [k for k, r in enumerate(src) if mv_boxes(r[0])[0] is not None]
    out, cum = [], 0
    if role == "BERS3":   # every record of a T3 chain shows the flurry pose of its slot; the last (hold) record carries that pose's attack box
        k3 = first_slot[start][1] % len(src)
        pk3 = src[k3]
        hit3, hurt3 = mv_boxes(pk3[0])
        for k, a in enumerate(ch):
            last = bool(w(rom, a + 2) & 0x8000)
            out.append(dict(src=pk3[0], cells=floor_cells(pk3[1]), dur=w(rom, a), flags=w(rom, a + 2), hurt=hurt_or_donor(rom[a + 8], hurt3, floor_cells(pk3[1])),
                            atk=atk_index(hit3) if (last and hit3) else rom[a + 9], b10=rom[a + 10], b11=rom[a + 11], tail=rom[a + 12:a + 16], donor=a, jump=("donor" if last else None)))
        return out, role
    hold_at = HOLD_AT.get(role.split("-")[0], 1.0 if role not in HOLD_AT else 0.0)
    for k, a in enumerate(ch):
        dur = w(rom, a); fl = w(rom, a + 2); last = bool(fl & 0x8000)
        if dur >= 255:
            t = hold_at * stot
        else:
            t = (cum + dur / 2.0) / dtot * stot
            cum += dur
        if len(ch) == 1:
            t = hold_at * stot
        acc, pick, pk = 0, src[-1], len(src) - 1
        for j, r in enumerate(src):
            if acc + r[2] > t or (t >= stot and j == len(src) - 1): pick, pk = r, j; break
            acc += r[2]
        atk = rom[a + 9]
        hit, hurt = mv_boxes(pick[0])
        if atk:
            if has_atk:
                j = min(has_atk, key=lambda x: abs(x - pk)); hit = mv_boxes(src[j][0])[0]
                if role.split("-")[0] == "HK" and hit: hit = (hit[0], hit[1], min(hit[2], 13), min(hit[3], 85))   # MSHvSF's kick box (hit id 39) is up 103..127, above a standing AvP enemy's head: it never connected; reach kept, height lowered to the heavy punch's body band (owner-visible)
                pick = src[j] if abs(j - pk) <= 1 else pick
                atk_i = atk if role.startswith("GRAB") else atk_index(hit)   # the grab states keep the donor's attack box (index 24 on the slam)
            else:
                atk_i = atk   # no attack box in his chain: the donor's index into T' (kept donor entries)
                report.append("%x rec %d keeps donor attack box %d" % (start, k, atk))
        else:
            atk_i = 0
        out.append(dict(src=pick[0], cells=floor_cells(pick[1]), dur=dur, flags=fl, hurt=(idle_recs[0]["hurt"] if (role.startswith("GRAB") and rom[a + 8]) else hurt_or_donor(rom[a + 8], hurt, floor_cells(pick[1]))), atk=atk_i, b10=rom[a + 10], b11=rom[a + 11],
                        tail=rom[a + 12:a + 16], donor=a, jump=("donor" if last else None)))
    return out, role


# The leap (state 020004, slots T1.3 -> T1.37 -> T1.10): Schaefer's does not rise (census note: the floor line holds, the body travels sideways); the arc is Wolverine's own. The launch
# record (7 ticks) keeps the donor shape, the 4095-tick hold record is replaced by arc records of 2 to 3 ticks, each with his MSHvSF jump pose (the six resident records of the chain
# 1.0 and the landing chain 1.3, the poses D11's jump move shows) lifted by the owner's apex (SAT_WV_JUMP=1: 88 px, x0.838; WV_JUMP_SCALE overrides), then the terminal hold.
# The state routine ends the leap by itself (the hold lasts about 25 ticks in the host trace), so the arc is laid over 25 ticks.
ARC_CHAIN = 0x164e40
ARC_RECS = (0xd1fac, 0xd1fdc, 0xd1ffc, 0xd1fdc, 0xd205c, 0xd1fac, 0xd2208, 0xd2218, 0xd2228)
ARC_STEPS = [(5, 0, 74), (4, 74, 105), (6, 105, 76), (3, 76, 60), (8, 60, 0), (1, 0, 0), (3, 0, 0), (2, 0, 0), (1, 0, 0)]   # D11 remap.json jumpair: frames, sole lift at the start and end of each step (px)
ARC_TICKS, ARC_SCALE = 25, float(os.environ.get("WV_JUMP_SCALE", "0.838"))


def apply_arc(start):
    recs_ = new_chains[start]
    launch, hold = recs_[0], recs_[-1]
    tot = sum(f for f, _, _ in ARC_STEPS)
    arcs, t0 = [], 0.0
    for (f, l0, l1), rec in zip(ARC_STEPS, ARC_RECS):
        cells, ok = resident_pose(rec)
        assert ok and cells, "arc pose %x is not resident" % rec
        n = max(1, round(f * ARC_TICKS / tot / 3.0))      # sub-records of about 3 ticks
        span = f * ARC_TICKS / tot
        for k in range(n):
            a_, b_ = k / n, (k + 1) / n
            lift = int(round(ARC_SCALE * (l0 + (l1 - l0) * (a_ + b_) / 2)))   # sole height above the floor (D11 jumpair): the pose is floor-aligned first
            dur = max(1, int(round(span * b_)) - int(round(span * a_)))
            arcs.append([cells, lift, dur, rec])
    first = recs_[0]
    first["cells"] = floor_cells(resident_pose(ARC_RECS[0])[0])
    out = [first]
    for cells, lift, dur, rec in arcs:
        out.append(dict(src=rec, cells=floor_cells(cells, lift), dur=dur, flags=0, hurt=launch["hurt"], atk=0,
                        b10=hold["b10"], b11=hold["b11"], tail=hold["tail"], donor=None, jump=None))
    last_cells = resident_pose(ARC_RECS[-1])[0]
    hold.update(cells=floor_cells(last_cells), src=ARC_RECS[-1])
    out.append(hold)
    new_chains[start] = out


FLOOR_SOLE = sole_of(idle_src[0][1])

# the three chains with ROM timing (milestone 1)
new_chains[STAND] = idle_recs
new_chains[WALK] = walk_recs
new_chains[LP] = lp_recs
for r in idle_recs + walk_recs + lp_recs: r.setdefault("donor", None)

def walk_like(start):
    """T1.59 (a second 12-record walk loop of Schaefer's, 4 ticks a record, never reached in the census): his walk poses by phase of the same cycle, drawn as the walk draws them (not floor-aligned),
    so every pose is one of the walk's own assemblies (WV_WALK59=0 keeps the floor-aligned WALK role: 8 assemblies and 1.5 KB more)"""
    ch = skel(start); tot = sum(w(rom, x) for x in ch[:-1]) or 1; cum = 0; out = []
    for x in ch:
        dur = w(rom, x); last = bool(w(rom, x + 2) & 0x8000)
        t = ((cum + dur / 2.0) / tot) * mtot; cum += dur
        acc, pick = 0, walk_src[-1]
        for r in walk_src:
            if acc + r[2] > t: pick = r; break
            acc += r[2]
        out.append(dict(src=pick[0], cells=pick[1], dur=dur, flags=w(rom, x + 2), hurt=hurt_index(mv_boxes(pick[0])[1]), atk=0, b10=rom[x + 10], b11=rom[x + 11], tail=rom[x + 12:x + 16], donor=x, jump=("donor" if last else None)))
    used_by_walk = {id(r["cells"]) for r in walk_recs}   # snap to the poses T1.2 already draws: no assembly of its own (about 500 B of the cart tail)
    order_ = [k for k, r in enumerate(walk_src)]
    for r in out:
        if id(r["cells"]) not in used_by_walk:
            k = next(k for k, q in enumerate(walk_src) if q[1] is r["cells"])
            near = min((j for j, q in enumerate(walk_src) if id(q[1]) in used_by_walk), key=lambda j: abs(j - k))
            r["cells"], r["src"] = walk_src[near][1], walk_src[near][0]
            r["hurt"] = hurt_index(mv_boxes(r["src"])[1])
    return out


for a in order:
    if a in new_chains: continue
    if WV_REMAP and os.environ.get("WV_WALK59") != "0" and first_slot[a] == ("T1", 59):
        new_chains[a] = walk_like(a); role_of[a] = "WALK(phase)"
        continue
    role = chain_role(a, first_slot[a])
    if role == "BERS3" and WV_T3_SHARE and t3_shared:   # the gun action's aim chains are dead for him (his Berserker has its own chain): one chain answers every T3 slot
        new_chains[a] = new_chains[t3_shared[0]]; role_of[a] = "BERS3(shared)"
        continue
    new_chains[a], used = make_chain(a, role, HK_SLOT if a == HP_SLOT else None)
    role_of[a] = used
    if role == "BERS3": t3_shared.append(a)
    if a == HP_SLOT and WV_HP_TICKS: rescale(new_chains[a], WV_HP_TICKS)
apply_arc(ARC_CHAIN)
role_of[ARC_CHAIN] = "JUMP(arc)"
role_of[STAND], role_of[WALK], role_of[LP] = "IDLE(ROM)", "WALK(ROM)", "LP1(ROM)"

# ---- Berserker (plan V2 section 6): his own native action (wolverine.c wv_bz_run) with its own chain, not the gun's T3 slot cycling. The flurry poses are the ones the T3 chains of the gun action
# showed (SRC BERS3, one pose per slot) in the order the stock gun burst visits them (the aim sweep table of Schaefer's 02000c routine, 0x25ac6: T3 slots 6 6 5 5 4 3 3 4 5 5 6 6), 4 ticks
# each = 48 ticks, one record per strike; every record that has an MSHvSF attack box carries it (a new strike id is taken at each record, so each strike can connect), then a terminal record
# that the action reads as the end. No donor chain: bytes +10/+11/+12..15 come from the stand record and T3's first chain.
BZ_SLOTS = (6, 6, 5, 5, 4, 3, 3, 4, 5, 5, 6, 6)
# Contact box of every strike: the MSHvSF record of these poses (the 6 resident ones of sub-table 22 entry 10, a rising spin) carries one box, a column above his head (forward -12..12, up 108..144,
# hit id 97), which cannot touch a standing enemy of AvP's size. The strikes use the light punch's reach (forward 26..84, MSHvSF hit id 31) at the heavy punch's body height (up 13..85, ids 70
# and 112's low edge), a deliberate approximation (rect = forward x0, x1, up y0, y1). Owner-visible: contact geometry of the flurry.
BZ_BOX = (26, 84, 13, 85)
BZ_TICKS = int(os.environ.get("WV_BZ_TICKS", "4"))
BZ_HURT = int(os.environ.get("WV_BZ_HURT", "0"))   # owner 11-10 ("he shouldn't be hittable during the berserker, should be consistent with stock characters"): 0 (default) = no hurt box on the Berserker records, as Schaefer's own special (donor chain T1.42 names none, so no hit lands on him); 1 = his flurry poses' hurt box (hittable), comparison switch only
BZ = "BZ"
bz_src = pick_sources("BERS3", None)
t3b, t3n = TABLES[3]
bz_recs = []
t3_donor = None
if WV_REMAP:
    # The real Berserker Barrage (22.22 to 22.25 of MSHvSF, MAME-confirmed): the start pose, ten alternating strikes (22.24, 22.23) and the end pose; 12 records of BZ_TICKS ticks as before, every one with the strike box.
    bz_seq = (["BZ_START"] + ["BZ_B", "BZ_A"] * 5 + ["BZ_END"]) if os.environ.get("WV_BZ_START") == "1" else (["BZ_B", "BZ_A"] * 5 + ["BZ_B", "BZ_END"])   # the start pose (22.22) costs an assembly (240 B of the cart tail): off by default, the flurry opens on its first strike
    for key in bz_seq:
        pk = pick_sources(key, None)[0]
        bz_recs.append(dict(src=pk[0], cells=floor_cells(pk[1]), dur=BZ_TICKS, flags=0, hurt=(hurt_index(mv_boxes(pk[0])[1]) if mv_boxes(pk[0])[1] else rom[STAND + 8]) if BZ_HURT else 0, atk=atk_index(BZ_BOX),
                            b10=0, b11=rom[STAND + 11], tail=rom[STAND + 12:STAND + 16], donor=None))
for sl in (() if WV_REMAP else BZ_SLOTS):
    a_ = t3b + s16(w(rom, t3b + 2 * sl))
    t3_donor = t3_donor or a_
    k = first_slot[a_][1] % len(bz_src)
    pk = bz_src[k]
    hit_, hurt_ = mv_boxes(pk[0])
    if os.environ.get('WV_DEBUG'): print('BZ slot', sl, 'pose', k, hex(pk[0]), 'hit rect', hit_, 'hurt', hurt_, 'ids', [w(mv, 0x1ce0f2 + l(mv, pk[0] + 12) * 16 + 2 * j) for j in range(8)])
    bz_recs.append(dict(src=pk[0], cells=floor_cells(pk[1]), dur=BZ_TICKS, flags=0, hurt=(hurt_index(hurt_) if hurt_ else rom[STAND + 8]) if BZ_HURT else 0, atk=atk_index(BZ_BOX),
                        b10=0, b11=rom[STAND + 11], tail=rom[STAND + 12:STAND + 16], donor=None))
bz_last = dict(bz_recs[-1]); bz_last.update(dur=1, flags=0x8000, atk=0, jump="self", donor=None)
bz_recs.append(bz_last)
new_chains[BZ] = bz_recs
role_of[BZ] = "BERSERKER(own)"
if WV_T3_SHARE and t3_shared:   # the 48 T3 slots (the stock gun's aim chains, never entered by his native Berserker) answer with the Berserker's own chain instead of a chain of their own
    t3list = new_chains[t3_shared[0]]
    for a_, v_ in list(new_chains.items()):
        if v_ is t3list: new_chains[a_] = bz_recs

# Chains with byte-identical records (same durations, flags, poses, boxes, event bytes, and a terminal that jumps to itself or to the same record) are stored once: the index tables of every slot
# that named a duplicate point at the first copy. Lossless (a terminal jumping to itself behaves the same in either copy); WV_DEDUPE=0 keeps every chain.
def chain_key(rs):
    k = []
    for r in rs:
        jump = None
        if r["flags"] & 0x8000:
            if r.get("jump") == "donor":
                t = l(rom, r["donor"] + 16); jump = "self" if t == r["donor"] else ("tgt", t)
            else: jump = r.get("jump")
        k.append((r["dur"], r["flags"], tuple(r["cells"]), r["hurt"], r["atk"], r["b10"], r["b11"], bytes(r["tail"]), jump))
    return tuple(k)


if int(os.environ.get("WV_DEDUPE", "1")):
    first_of, ndup, dupbytes = {}, 0, 0
    for a in list(new_chains):
        rs = new_chains[a]
        if a in (STAND, WALK, LP, BZ): continue
        kk = chain_key(rs)
        if kk in first_of and first_of[kk] is not rs:
            new_chains[a] = first_of[kk]; ndup += 1; dupbytes += sum(20 if (r["flags"] & 0x8000) else 16 for r in rs)
        else: first_of.setdefault(kk, rs)
    print("duplicate chains aliased: %d (%d bytes)" % (ndup, dupbytes))

# ---- layout
off = (len(blk) + 15) & ~15
REC_LO = off
at_of = {}            # donor chain start -> window offset of its first record
rec_at = {}           # donor record address -> window offset
seen_chain = {}
for a in [STAND, WALK, LP] + [x for x in order if x not in (STAND, WALK, LP)] + [BZ]:
    rs = new_chains[a]
    if id(rs) in seen_chain:   # shared chain: same records
        at_of[a] = seen_chain[id(rs)]; continue
    seen_chain[id(rs)] = off
    at_of[a] = off
    for r in rs:
        r["at"] = off
        if r.get("donor") is not None: rec_at[r["donor"]] = off
        off += 20 if (r["flags"] & 0x8000) else 16
REC_END = off
assert REC_END < 0x7000, "records must stay within the 16-bit offsets of the tables (%x)" % REC_END
# donor record addresses that were not a chain's own records (jump targets in the middle of another chain)
for a, fl in recs.items():
    if a not in rec_at:
        for st in order:
            ch = skel(st)
            if a in ch and st in at_of:
                rec_at[a] = at_of[st] + sum(20 if (new_chains[st][k]["flags"] & 0x8000) else 16 for k in range(min(ch.index(a), len(new_chains[st]) - 1)))
                break
# the stand / walk / lp records have no donor addresses of their own: map the donor chains' first records
for st in (STAND, WALK, LP):
    ch = skel(st)
    for k, a in enumerate(ch):
        rec_at.setdefault(a, at_of[st] + sum(20 if (new_chains[st][j]["flags"] & 0x8000) else 16 for j in range(min(k, len(new_chains[st]) - 1))))
asm_off = (off + 3) & ~3
ASM_START = asm_off
asm_where = {}
for a, rs in new_chains.items():
    for r in rs:
        r["pose"] = pose_id(r["cells"])
for pid, cells in enumerate(poses):
    asm_where[pid] = asm_off
    ab = assembly(cells)
    for i, c in enumerate(cells):
        assert c[5] in (12, 13), "palette rows of his tiles are 12 and 13"
        if c[5] == 13: p1_marks.append(asm_off + 12 + 8 * i + 3)
    asm_blob += ab; asm_off += len(ab)
T_off = (asm_off + 3) & ~3
if os.environ.get("WV_KEYS_OUT"):   # the keys his native records draw (make_d12.py prunes the pack's key list to these plus filler)
    json.dump(sorted({c[2] for cells in poses for c in cells}), open(os.environ["WV_KEYS_OUT"], "w"))

# T': the donor table with the new hurt boxes after its 12 entries, then the attack table (38 donor entries and the new ones)
donor_T_addr = 0x11b166
hurt_d = [rom[donor_T_addr + 4 + 8 * i:donor_T_addr + 12 + 8 * i] for i in range(12)]
atk_d = [rom[donor_T_addr + 0x64 + 16 * i:donor_T_addr + 0x74 + 16 * i] for i in range(38)]
htmpl, atmpl = hurt_d[1], atk_d[1]
hurt_b = hurt_d + [bytes(cwbytes(r)) + htmpl[4:8] for r in hurt_new]
atk_b = atk_d + [bytes(cwbytes(r)) + atmpl[4:16] for r in atk_new]
# Entries below the lowest index any native record names are not stored: the collision pass reads T + s16(T[0]) + 8 * hurt index and T + s16(T[2]) + 16 * attack index (the offsets are
# sign-extended words), and index 0 means none and is never read, so the tables start at the first used index and the offsets are biased. No index is renumbered (donor indices keep their
# meaning for any code that tests them), only the unused leading entries go (his own records name hurt 12..20 and attack 1, 16..42: 12 hurt and 1 attack entry, 112 bytes).
_uniq = {id(v): v for v in new_chains.values()}.values()
used_h = sorted({r["hurt"] for v in _uniq for r in v} - {0}); used_a = sorted({r["atk"] for v in _uniq for r in v} - {0})
hlo, alo = used_h[0], used_a[0]
hurt_s, atk_s = hurt_b[hlo:max(used_h) + 1], atk_b[alo:max(used_a) + 1]
T = bytearray()
T += ((4 - 8 * hlo) & 0xffff).to_bytes(2, "big") + ((4 + 8 * len(hurt_s) - 16 * alo) & 0xffff).to_bytes(2, "big")
for b in hurt_s: T += b
for b in atk_s: T += b
_s16 = lambda b, o: int.from_bytes(T[o:o + 2], "big", signed=True)
assert all(bytes(T[_s16(T, 0) + 8 * i:_s16(T, 0) + 8 * i + 8]) == hurt_b[i] for i in used_h), "hurt table biasing"
assert all(bytes(T[_s16(T, 2) + 16 * i:_s16(T, 2) + 16 * i + 16]) == atk_b[i] for i in used_a), "attack table biasing"
T_end = T_off + len(T)
assert T_end <= 0x10000, "block %x" % T_end
assert len(hurt_b) <= 255 and len(atk_b) <= 255 and all(1 <= x < len(hurt_b) for x in used_h) and all(1 <= x < len(atk_b) for x in used_a)

# ---- write the block
full = bytearray(0x10000)
full[:len(blk)] = blk
tchanged = 0
for b, n in TABLES:
    for i in range(n):
        tgt = b + s16(w(rom, b + 2 * i))
        nv = (WIN + (at_of[tgt] if tgt in at_of else at_of[STAND])) - (b + D)
        assert -32768 <= nv < 32768
        full[b + 2 * i - LO:b + 2 * i - LO + 2] = (nv & 0xffff).to_bytes(2, "big"); tchanged += 1
for a, rs in new_chains.items():
    for r in rs:
        o = r["at"]
        full[o:o + 2] = r["dur"].to_bytes(2, "big")
        full[o + 2:o + 4] = r["flags"].to_bytes(2, "big")
        full[o + 4:o + 8] = (WIN + asm_where[r["pose"]]).to_bytes(4, "big")
        full[o + 8] = r["hurt"]; full[o + 9] = r["atk"]; full[o + 10] = r["b10"]; full[o + 11] = r["b11"]
        full[o + 12:o + 16] = bytes(r["tail"])
        if r["flags"] & 0x8000:
            j = r["jump"]
            if j == "donor":
                t = l(rom, r["donor"] + 16)
                tgt = rec_at[t]
            else:
                tgt = {"idle": at_of[STAND], "walk": at_of[WALK], "self": o}[j]
            full[o + 16:o + 20] = (WIN + tgt).to_bytes(4, "big")
pos = (REC_END + 3) & ~3
full[pos:pos + len(asm_blob)] = asm_blob
assert pos + len(asm_blob) <= T_off
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
assert all((b - a) % 2 == 0 and (b - a) >> 1 < 65536 for a, b in zip([0] + slots, slots)), "reloc slot steps must fit a 16-bit word of 2-byte units"
lines = [
    "/* Generated by tools/wolverine/gen_native.py: do not commit (ROM-derived). */",
    "#define WV_NAT_DELTA 0x%xu" % D,
    "#define WV_NAT_WIN 0x%xu" % WIN,
    "#define WV_NAT_REC_LO 0x%xu   /* first native record (window address) */" % (WIN + REC_LO),
    "#define WV_NAT_REC_END 0x%xu" % (WIN + REC_END),
    "#define WV_NAT_SIZE %d" % size,
    "#define WV_BZ_CHAIN 0x%xu   /* his Berserker chain: first record (window address) */" % (WIN + at_of[BZ]),
    "#define WV_BZ_N %d   /* strike records before the terminal one */" % (len(bz_recs) - 1),
    "#define WV_CHAIN %d   /* attack chain length (stages of Schaefer's counter that his slots use), see the knobs in gen_native.py */" % WV_CHAIN,
    "#define WV_HP_TICKS %d" % (sum(r["dur"] for r in new_chains[HP_SLOT] if r["dur"] < 255)),
    "#define WV_NAT_T 0x%xu   /* his box table T' */" % (WIN + T_off),
    "#define WV_NAT_T_DONOR 0x%xu" % donor_T_addr,
    "#define WV_NAT_TSLOT %du   /* opcode-store offset of the per-character box table entry of character 1 */" % tslot,
    "#define WV_RELOC_SLOTS %d" % len(slots),
    "static const unsigned short wv_reloc_delta[%d] = {%s};   /* opcode-store offsets, ascending, in steps of 2 */" % (len(slots), ",".join(str((b - a) >> 1) for a, b in zip([0] + slots, slots))),
    "#define WV_NAT_ASM %d   /* block offset of the first pose assembly; WV_NAT_ASMN assemblies follow back to back (12 byte header, count at +2, 8 bytes a tile: the attribute low byte at +3 of a tile is 1 for his first row, 0 for the second until the stage row is written) */" % ASM_START,
    "#define WV_NAT_ASMN %d" % len(poses),
    "static unsigned char wv_blk[WV_NAT_SIZE] __attribute__((aligned(4))) = {%s};" % ",".join(map(str, full[:size])),
]
OUT.write_text("\n".join(lines) + "\n")
OUT.with_suffix(".bin").write_bytes(bytes(full))   # HOST runner: WVBLOCK (tools/lift_runner/host_reloc.c) with WVTNEW = WV_NAT_T
if os.environ.get('WV_DEBUG'):
    uniq = {id(v): v for v in new_chains.values()}.values()
    uh = sorted({r['hurt'] for v in uniq for r in v}); ua = sorted({r['atk'] for v in uniq for r in v})
    print('used hurt idx', len(uh), uh); print('used atk idx', len(ua), ua)
nrec = sum(len(v) for v in new_chains.values())
print("block: index tables %d bytes, %d native chains / %d records %d..%d (%d B), %d assemblies (%d B, %d second-row tiles), T' %d B (hurt %d + %d new, attack %d + %d new); %d table entries; total %d bytes" % (
    len(blk), len(new_chains), nrec, REC_LO, REC_END, REC_END - REC_LO, len(poses), len(asm_blob), len(p1_marks), len(T), 12, len(hurt_new), 38, len(atk_new), tchanged, size))
print("slots", len(slots), "tslot", tslot)
rep = OUT.with_suffix(".roles.txt")
rep.write_text("\n".join("%s %s %s %d recs %s" % (a if isinstance(a, str) else "%x" % a, first_slot.get(a, ("T1", 0)), role_of.get(a, "?"), len(new_chains[a]), "+".join(str(r["dur"]) for r in new_chains[a])) for a in new_chains) + "\n" + "\n".join(report) + "\n")
import collections
print("roles:", dict(collections.Counter(v.split("(")[0] for v in role_of.values())))
print("donor attack boxes kept for", len(report), "records (his chain has no attack box)")
