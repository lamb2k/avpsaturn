#!/usr/bin/env python
"""Lane avp-wolverine: Wolverine's frames, portraits and colour sets from the user's MSHvSF ROM set, as a build input.
Reads the MAME captures of tools/wolverine/run_mame.sh (obj.txt, pal.bin, tiles.bin) and writes, under OUT (ROM-derived, never in git):
  remap.json         poses (per tile: dx dy key hflip vflip palette row), moves (pose, frames), portraits, colour sets, remapped keys
  gfx_wolverine.bin  the AvP graphics region with his canonical tiles written at the remapped sprite keys (packer input)
  strips/*.png       a strip per colour set and per move, for review
Tiles are deduped across all poses with H/V flips counted as the same tile. Keys come from sprite keys no AvP stage file uses.
usage: assets.py CAPTURE_DIR COLOUR_DIR_PUNCH COLOUR_DIR_KICK AVP_WORK OUT [AVP_GFX]"""
import json, os, pathlib, struct, sys
from PIL import Image

BODY = (0x6000, 0xa000)          # his own sprite bank in MSHvSF
PALS = (12, 13)                  # player 1 rows in the capture
# Capture schedule windows (frames of full.txt / seq2.txt); hit_etc holds hitstun, knockdown, getup and the KO.
# Windows by content (bounding-box timeline of full.txt, 11-08): the opponent knocked him down at 2580, so the old dash (2600) and crouch
# (2660) windows held knockdown frames; dash and crouch now come from their own runs (dash.txt, crouch.txt via WV_EXTRA).
WINDOWS = dict(idle=(1990, 1999), walk=(2000, 2062), jump=(2063, 2179), lp=(2180, 2239), hp=(2240, 2309), hk=(2310, 2399),
               berserker=(2400, 2519), tornado=(2520, 2579), knockdown=(2580, 2739),
               hit_etc=(3711, 3730), hit_m=(3436, 3457), hit_h=(3735, 3757))   # standing hitstun reactions (v4.1; was (3100, 4500), which began mid-knockdown)
# Owner 11-08: the throw-attempt windows (2740-3099) are dropped; no real throw was captured.
SELECT_FRAME, HUD_FRAME = 900, 2000
TIGHT = (0x06, 0x0e, 0x1c, 0x1e, 0x24)   # stages that drop the most with his tiles (fit_thin, 11-08)


def sx(v):
    v &= 0x3ff
    return v - 1024 if v >= 768 else v


def frames(path):
    fr, cur = {}, None
    for l in open(path):
        if l.startswith("f "):
            cur = int(l[2:]); fr[cur] = []; continue
        x, y, c, a = (int(v, 16) for v in l.split())
        if c or a:
            fr[cur].append((x, y, c | ((y & 0x6000) << 3), a))
    return fr


def expand(objs):
    """Per tile: screen x, y, code, hflip, vflip, palette."""
    out = []
    for x, y, c, a in objs:
        xs, ys, hf, vf = ((a >> 8) & 15) + 1, ((a >> 12) & 15) + 1, (a >> 5) & 1, (a >> 6) & 1
        for by in range(ys):
            for bx in range(xs):
                px = sx(x) + 16 * ((xs - 1 - bx) if hf else bx)
                py = sx(y) + 16 * ((ys - 1 - by) if vf else by)
                out.append((px, py, c + bx + 16 * by, hf, vf, a & 0x1f))
    return out


def pens(b):
    rows = []
    for y in range(16):
        r = []
        for g in range(2):
            q = b[y * 8 + g * 4:y * 8 + g * 4 + 4]
            for x in range(8):
                m = 0x80 >> x
                r.append((q[3] & m != 0) << 3 | (q[2] & m != 0) << 2 | (q[1] & m != 0) << 1 | (q[0] & m != 0))
        rows.append(tuple(r))
    return tuple(rows)


def unpens(px):
    out = bytearray(128)
    for y in range(16):
        for x in range(16):
            p = px[y][x]
            o = y * 8 + (x // 8) * 4
            m = 0x80 >> (x & 7)
            for bit in range(4):
                if p >> bit & 1:
                    out[o + bit] |= m
    return bytes(out)


def flips(px):
    h = tuple(r[::-1] for r in px)
    return {(0, 0): px, (1, 0): h, (0, 1): px[::-1], (1, 1): h[::-1]}


def tiles(path):
    d, t = pathlib.Path(path).read_bytes(), {}
    for i in range(0, len(d), 132):
        t[struct.unpack_from(">I", d, i)[0]] = pens(d[i + 4:i + 132])
    return t


def palrow(path, frame, row):
    d = pathlib.Path(path).read_bytes()
    for i in range(0, len(d), 4 + 512 * 3):
        if struct.unpack_from(">I", d, i)[0] >= frame:
            o = i + 4 + row * 48
            return [tuple(d[o + 3 * k:o + 3 * k + 3]) for k in range(16)]


def main():
    cap, cp, ck, work, out = (pathlib.Path(a) for a in sys.argv[1:6])
    gfx = pathlib.Path(sys.argv[6] if len(sys.argv) > 6 else "E:/AvP/learning/lane-satgfx/gfx.bin")
    out.mkdir(parents=True, exist_ok=True)
    fr, T = frames(cap / "obj.txt"), tiles(cap / "tiles.bin")
    # Extra captures: WV_EXTRA="DIR:name=a-b,..." (frames of that run, kept apart by an offset), e.g. the throw run (throw.txt).
    for n, spec in enumerate(x for x in os.environ.get("WV_EXTRA", "").split(";") if x):
        d, ws = spec.rsplit(":", 1)
        off = 100000 * (n + 1)
        fr.update({f + off: v for f, v in frames(pathlib.Path(d) / "obj.txt").items()})
        T.update(tiles(pathlib.Path(d) / "tiles.bin"))
        for w in ws.split(","):
            nm, r = w.split("=")
            a, b = (int(v) for v in r.split("-"))
            WINDOWS[nm] = (a + off, b + off)
    canon, ckey = {}, {}         # canonical pixels -> index; code -> (index, hflip, vflip)

    def tile(code):
        if code not in ckey:
            px = T[code]
            if all(p == 15 for r in px for p in r):
                ckey[code] = None
            else:
                for (h, v), q in flips(px).items():
                    if q in canon:
                        ckey[code] = (canon[q], h, v); break
                else:
                    canon[px] = len(canon); ckey[code] = (canon[px], 0, 0)
        return ckey[code]

    def pose_of(tl):
        """Anchor: centre of the lowest 32 pixel rows, and the bottom."""
        bottom = max(p[1] for p in tl) + 16
        feet = [p[0] for p in tl if p[1] + 16 > bottom - 32]
        ax = (min(feet) + max(feet) + 16) // 2
        ent = []
        for px, py, c, hf, vf, pal in tl:
            k = tile(c)
            if k:
                ent.append((px - ax, py - bottom, k[0], hf ^ k[1], vf ^ k[2], pal - PALS[0]))
        return tuple(sorted(ent)), (ax, bottom)

    poses, moves = {}, {}
    for name, (a, b) in WINDOWS.items():
        seq = []
        for f in range(a, b + 1):
            tl = [t for t in expand(o for o in fr.get(f, []) if (o[3] & 0x1f) in PALS and BODY[0] <= o[2] < BODY[1])]
            if not tl:
                continue
            p, anc = pose_of(tl)
            pid = poses.setdefault(p, len(poses))
            if seq and seq[-1][0] == pid:
                seq[-1][1] += 1
            else:
                seq.append([pid, 1, list(anc)])
        moves[name] = seq
    # THIN=1 (fit rule step 2): in each move keep its first and last pose, holds of 5+ frames (key and attack frames), and every other pose
    # between; a dropped pose's frames go to the pose shown before it. Poses an earlier move kept cost nothing.
    if os.environ.get("THIN") == "1":
        kept = set()
        for name, seq in moves.items():
            order = []
            for pid, n, _ in seq:
                if pid not in order:
                    order.append(pid)
            hold = {}
            for pid, n, _ in seq:
                hold[pid] = max(hold.get(pid, 0), n)
            fresh = [q for q in order if q not in kept]
            for j, q in enumerate(fresh):
                if j == 0 or j == len(fresh) - 1 or hold[q] >= 5 or j % 2 == 0:
                    kept.add(q)
        for name, seq in moves.items():
            out_seq = []
            for pid, n, anc in seq:
                if pid in kept or not out_seq:
                    out_seq.append([pid, n, anc])
                else:
                    out_seq[-1][1] += n
            moves[name] = out_seq
        live = {i for p, i in poses.items() if i in kept or any(s[0] == i for m in moves.values() for s in m)}
        keepc = {e[2] for p, i in poses.items() if i in live for e in p}
        for pt in ("hud", "select_cell", "select_big", "name"):
            pass
    # Portraits: HUD face (top left in play), select grid cell, big select picture, name.
    def group(f, box, body=False):
        tl = [t for t in expand(fr[f]) if box[0] <= t[0] < box[2] and box[1] <= t[1] < box[3] and not (BODY[0] <= t[2] < BODY[1] and t[5] in PALS)]
        ent = []
        for px, py, c, hf, vf, pal in tl:
            k = tile(c)
            if k:
                ent.append((px - box[0], py - box[1], k[0], hf ^ k[1], vf ^ k[2], pal))
        return ent
    portraits = dict(hud=group(HUD_FRAME, (0, 0, 40, 32)), select_cell=group(SELECT_FRAME, (160, 120, 220, 170)),
                     select_big=group(SELECT_FRAME, (0, 0, 130, 120)), name=group(SELECT_FRAME, (40, 195, 170, 224)))
    if os.environ.get("THIN") == "1":
        keepc |= {e[2] for v in portraits.values() for e in v}
        ren = {o: n for n, o in enumerate(sorted(keepc))}
        canon = {px: ren[i] for px, i in canon.items() if i in ren}
        poses = {tuple((a, b, ren[c], d, e, f) for a, b, c, d, e, f in p): i for p, i in poses.items() if i in live}
        idmap = {old: n for n, old in enumerate(sorted(poses.values()))}
        poses = {p: idmap[i] for p, i in poses.items()}
        moves = {m: [[idmap[a], n, anc] for a, n, anc in seq] for m, seq in moves.items()}
        portraits = {k: [(a, b, ren[c], d, e, f) for a, b, c, d, e, f in v] for k, v in portraits.items()}
    # AvP sprite keys no stage file uses; AvP-blank keys first.
    R = json.loads((work / "rounds.json").read_text())
    used = set()
    for f in R["files"]:
        used |= set(f["keys"][0])
    for l in open(work / "screen_keys.txt"):
        if l.strip() and l.split()[0] == "0":
            used.add(int(l.split()[1], 16))
    raw = bytearray(gfx.read_bytes())
    free = [k for k in range(1, 0x10000) if k not in used]
    free.sort(key=lambda k: (raw[k * 128:k * 128 + 128] != b"\xff" * 128, k))
    if len(free) < len(canon):
        raise SystemExit(f"not enough free sprite keys: {len(free)} < {len(canon)}")
    keys = free[:len(canon)]
    for px, i in canon.items():
        raw[keys[i] * 128:keys[i] * 128 + 128] = unpens(px)
    (out / "gfx_wolverine.bin").write_bytes(raw)
    cols = {}
    for nm, d, fno in (("punch", cp, 1995), ("kick", ck, 1995)):
        cols[nm] = [palrow(d / "pal.bin", fno, r) for r in PALS]
    lum = {nm: sum(0.3 * r + 0.59 * g + 0.11 * b for row in c for r, g, b in row) for nm, c in cols.items()}
    default = min(lum, key=lum.get)
    A = dict(keys=keys, tiles=len(canon), poses=[[list(e) for e in p] for p, _ in sorted(poses.items(), key=lambda x: x[1])],
             moves=moves, portraits=portraits, colours=cols, default_colour=default, luma=lum,
             codes_seen=len(ckey), source="MSHvSF (user ROM set) via tools/wolverine/run_mame.sh")
    # One trimmed set for every stage (owner 11-08), no bigger than BUDGET tiles (Schaefer's smallest own count). Every move kept: its first,
    # its longest-held (active) and its last pose are required; in hit_etc (hitstun, knockdown, getup, KO) every pose held 8+ frames too.
    # Then other poses are added, walk first, cheapest new tiles first, while the total stays within BUDGET. A removed pose's frames go to
    # the pose before it, so timing is unchanged.
    budget = int(os.environ.get("BUDGET", "971"))
    P = A["poses"]
    por = {e[2] for v in portraits.values() for e in v}
    # A move's own poses: those an earlier window (idle first) did not show; windows start and end in idle, so those frames say nothing.
    seen, fresh = set(), {}
    for name, seq in moves.items():
        fresh[name] = [x for x in dict.fromkeys(q[0] for q in seq) if x not in seen] if name != "idle" else list(dict.fromkeys(q[0] for q in seq))
        seen |= {q[0] for q in seq}
    hold = {}
    for seq in moves.values():
        for pid, n, _ in seq:
            hold[pid] = max(hold.get(pid, 0), n)
    # Every sequence's first pose is retained by trimming, including poses
    # shared with an earlier move. Include those tiles in the budget up front.
    need = {seq[0][0] for seq in moves.values() if seq}
    for name, fr_ in fresh.items():
        if fr_:
            need |= {fr_[0], max(fr_, key=lambda i: hold[i]), fr_[-1]}
            if name == "hit_etc":
                need |= {i for i in fr_ if hold[i] >= 8}
    # Current gameplay emits body poses only. Portrait/select art stays in the
    # asset source, without occupying the stage's finite resident tile set.
    cost = lambda ids: len({e[2] for i in ids for e in P[i]})
    floor = cost(need)
    if floor > budget:
        raise SystemExit(f"required gameplay poses need {floor} tiles, exceeding BUDGET {budget}")
    # Fill: round robin over moves (walk first), each time the move's unkept pose farthest from its kept ones in the timeline.
    names = ["walk"] + [m for m in fresh if m != "walk"]
    progress = True
    while progress:
        progress = False
        for m in names:
            fr_ = fresh[m]
            cand = [j for j, i in enumerate(fr_) if i not in need]
            if not cand:
                continue
            kept = [j for j, i in enumerate(fr_) if i in need]
            j = max(cand, key=lambda j: min(abs(j - k) for k in kept) if kept else 0)
            if cost(need | {fr_[j]}) <= budget:
                need.add(fr_[j]); progress = True
    mt = {}
    for name, seq in moves.items():
        o = []
        for pid, n, anc in seq:
            if pid in need or not o:
                o.append([pid, n, anc])
            else:
                o[-1][1] += n
        mt[name] = o
    emitted = {step[0] for seq in mt.values() for step in seq}
    have = {e[2] for i in emitted for e in P[i]}
    A["moves_one"] = mt
    A["one_set"] = dict(budget=budget, floor=floor, tiles=len(have), poses=len(emitted),
                       residency="emitted_moves", portrait_only_tiles_omitted=len(por - have))
    A["stage_keys"] = {f"{st:02x}": sorted(keys[i] for i in have) for st in range(2, 0x28, 2)}
    print("one set", A["one_set"], {m: (len({x[0] for x in q}), len(moves[m])) for m, q in mt.items()})
    (out / "remap.json").write_text(json.dumps(A))
    # Strips: each colour set on idle/walk/lp/hp/tornado first poses; every move's poses in the default colours.
    strips = out / "strips"; strips.mkdir(exist_ok=True)
    inv = {i: px for px, i in canon.items()}

    def draw(pose, pal, img, ox, oy):
        for dx, dy, i, hf, vf, prow in pose:
            px = flips(inv[i])[(hf, vf)]
            row = pal[prow] if 0 <= prow < len(pal) else pal[0]
            for y in range(16):
                for x in range(16):
                    p = px[y][x]
                    X, Y = ox + dx + x, oy + dy + y
                    if p != 15 and 0 <= X < img.width and 0 <= Y < img.height:
                        img.putpixel((X, Y), row[p])
    P = A["poses"]
    for nm, pal in cols.items():
        pick = [moves[m][len(moves[m]) // 2][0] for m in ("idle", "walk", "lp", "hp", "hk", "tornado", "crouch", "hit_etc") if moves[m]]
        img = Image.new("RGB", (160 * len(pick), 200), (40, 40, 48))
        for j, pid in enumerate(pick):
            draw(P[pid], pal, img, 80 + 160 * j, 195)
        img.save(strips / f"colour_{nm}.png")
    for m, seq in moves.items():
        ids = [s[0] for s in seq][:40]
        if not ids:
            continue
        img = Image.new("RGB", (160 * len(ids), 200), (40, 40, 48))
        for j, pid in enumerate(ids):
            draw(P[pid], cols[default], img, 80 + 160 * j, 195)
        img.save(strips / f"move_{m}.png")
    print(json.dumps(dict(tiles=len(canon), codes=len(ckey), poses=len(poses), default=default, luma=lum,
                          moves={m: (len(s), sum(x[1] for x in s)) for m, s in moves.items()},
                          portraits={k: len(v) for k, v in portraits.items()}, free_keys=len(free))))


if __name__ == "__main__":
    main()
