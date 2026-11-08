#!/usr/bin/env python
"""Lane avp-megaman: Mega Man's frames (with Rush and Mega Buster effects), portraits and colour sets from the user's MvC ROM set, as a build input.
Copied from tools/wolverine/assets.py (lane avp-wolverine) and kept per guest so the two branches share no file.
Reads the MAME captures of tools/megaman/run_mame.sh (obj.txt, pal.bin, tiles.bin) and writes, under OUT (ROM-derived, never in git):
  remap.json        poses (per tile: dx dy key hflip vflip palette row 0=Mega Man 1=Rush 2=effects), moves, portraits, colour sets, keys
  gfx_megaman.bin   the AvP graphics region with his canonical tiles written at the remapped sprite keys (packer input)
  strips/*.png      a strip per move and the brightness options, for review
Tiles are deduped across all poses with H/V flips counted as the same tile. Keys come from sprite keys no AvP stage file uses
(EXCLUDE_KEYS_FROM: another guest's remap.json, so the two guests never share a key).
usage: assets.py FULL_CAPTURE WIN_CAPTURE SELECT_CAPTURE WINDOWS_JSON AVP_WORK OUT [AVP_GFX] [EXCLUDE_KEYS_FROM]"""
import colorsys, json, os, pathlib, struct, sys
from PIL import Image

HUD_CODE = 0x16000               # MvC HUD/portrait bank and above
ROW = {0: 0, 1: 1, 14: 2}        # MvC palette (attr & 0x1f) -> guest row: Mega Man, Rush, Mega Buster shot (pal 16 is shared dust: not taken)
RUSH_MOVES = ("rush",)           # Rush is on screen all match in MvC; only his own move keeps him
FX_MOVES = ()
WIN_WINDOWS = dict(win=(5160, 5560), shoot=(2160, 2700), shot=(2160, 2700))   # shot: the projectile alone (pal 14)
PORTRAITS = dict(vs_face=(1820, (0, 0, 200, 112), None), stage_card=(1500, (0, 150, 90, 224), {2}))   # select capture: frame, box, palettes
# Brightness options for the owner (toned toward AvP's 1994 art, still Mega Man blue): value scale, saturation scale
TONES = dict(capcom=(1.0, 1.0), soft=(0.86, 0.80), avp=(0.76, 0.66), dark=(0.66, 0.55))
DEFAULT_TONE = "avp"


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


def tone(row, v, s):
    out = []
    for r, g, b in row:
        h, ss, vv = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        r2, g2, b2 = colorsys.hsv_to_rgb(h, ss * s, vv * v)
        out.append((round(r2 * 255) & 0xf8, round(g2 * 255) & 0xf8, round(b2 * 255) & 0xf8))   # Saturn 5:5:5
    return out


def main():
    full, win, sel, wjson, work, out = (pathlib.Path(a) for a in sys.argv[1:7])
    gfx = pathlib.Path(sys.argv[7] if len(sys.argv) > 7 and sys.argv[7] else "E:/AvP/learning/lane-satgfx/gfx.bin")
    excl = set()
    if len(sys.argv) > 8 and pathlib.Path(sys.argv[8]).exists():
        excl = set(json.loads(pathlib.Path(sys.argv[8]).read_text())["keys"])
    out.mkdir(parents=True, exist_ok=True)
    caps = {k: (frames(d / "obj.txt"), tiles(d / "tiles.bin")) for k, d in (("full", full), ("win", win), ("sel", sel))}
    T = {**caps["sel"][1], **caps["win"][1], **caps["full"][1]}
    windows = [("full", n, a, b) for n, (a, b) in json.loads(wjson.read_text()).items()] + [("win", n, a, b) for n, (a, b) in WIN_WINDOWS.items()]
    canon, ckey = {}, {}

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
        body = [p for p in tl if p[5] == 0] or tl
        bottom = max(p[1] for p in body) + 16
        feet = [p[0] for p in body if p[1] + 16 > bottom - 32]
        ax = (min(feet) + max(feet) + 16) // 2
        ent = []
        for px, py, c, hf, vf, pal in tl:
            k = tile(c)
            if k:
                ent.append((px - ax, py - bottom, k[0], hf ^ k[1], vf ^ k[2], ROW[pal]))
        return tuple(sorted(ent)), (ax, bottom)

    def body_only(tl):
        """Palette 0 also carries his dust and afterimage objects: keep the largest 16-px-connected group of
        palette 0 tiles (his body), and Rush/effect tiles as captured."""
        rest = [t for t in tl if t[5] not in (0, 14)]
        return largest(tl, 0) + largest(tl, 14) + rest     # palette 14: one Mega Buster shot on screen (owner fit rule)

    def largest(tl, pal):
        b = [t for t in tl if t[5] == pal]
        rest = []
        if not b:
            return rest
        left, groups = set(range(len(b))), []
        while left:
            st = [left.pop()]; g = set(st)
            while st:
                i = st.pop()
                for j in [j for j in left if abs(b[i][0] - b[j][0]) <= 16 and abs(b[i][1] - b[j][1]) <= 16]:
                    left.discard(j); g.add(j); st.append(j)
            groups.append(g)
        return [b[i] for i in max(groups, key=len)] + rest

    poses, moves = {}, {}
    for cap, name, a, b in windows:
        fr = caps[cap][0]
        pals = {0} | ({1} if name in RUSH_MOVES else set()) | ({16} if name in FX_MOVES else set())
        if name == "shot":
            pals = {14}
        seq = []
        for f in range(a, b + 1):
            tl = body_only(list(expand(o for o in fr.get(f, []) if (o[3] & 0x1f) in pals and 0 < o[2] < HUD_CODE)))
            if not tl:
                continue
            p, anc = pose_of(tl)
            pid = poses.setdefault(p, len(poses))
            if seq and seq[-1][0] == pid:
                seq[-1][1] += 1
            else:
                seq.append([pid, 1, list(anc)])
        moves[name] = seq
    # Throw: MvC's throw window is mostly walking and punches; keep only poses no other move shows (owner: real throw frames only).
    other = {pid for m, sq in moves.items() if m != "throw" for pid, *_ in sq}
    moves["throw"] = [x for x in moves["throw"] if x[0] not in other]

    def thin(seq, n):
        """Keep the first and last pose, holds of 5+ frames (start-up/active/end), and every n-th pose between;
        a cut pose's frames go to the kept pose before it, so the move's timing is unchanged. No move is dropped."""
        out = []
        for i, (pid, d, anc) in enumerate(seq):
            if i == 0 or i == len(seq) - 1 or d >= 5 or i % n == 0:
                out.append([pid, d, anc])
            else:
                out[-1][1] += d
        return out
    def trim_to_budget(budget, keyof):
        """Owner 11-08: one set for every stage, no bigger than the Hunter's own tiles. Every move keeps its first pose,
        its longest hold (active frame) and its last pose; then poses are added back, longest holds first, while the
        total stays within budget, one rank per move at a time. Cut poses give their frames to the kept pose before them, so timing is unchanged."""
        keep = {}
        for m, sq in moves.items():
            mid = [max(sq[1:-1], key=lambda x: x[1])[0]] if len(sq) > 2 else []
            keep[m] = {x[0] for x in sq[:1] + sq[-1:]} | set(mid)
        have = set().union(*(keyof(p) for ks in keep.values() for p in ks)) if keep else set()
        # round robin over moves (each move's longest holds first), so no move is starved
        ranked = {m: sorted(((d, pid) for pid, d, _ in sq), reverse=True) for m, sq in moves.items()}
        cand = sorted(((r, -d, m, pid) for m, lst in ranked.items() for r, (d, pid) in enumerate(lst)))
        for r, d, m, pid in cand:
            if pid in keep[m]:
                continue
            new = keyof(pid) - have
            if len(have) + len(new) <= budget:
                keep[m].add(pid); have |= new
        out = {}
        for m, sq in moves.items():
            o = []
            for pid, d, anc in sq:
                if pid in keep[m] or not o:
                    o.append([pid, d, anc])
                else:
                    o[-1][1] += d
            out[m] = o
        return out
    BUDGET = int(os.environ.get("MM_BUDGET", "795"))     # smallest Hunter own-tile figure over the play stages (fit_all.log)
    fr = caps["sel"][0]

    def group(f, box, pals):
        tl = [t for t in expand(fr.get(f, [])) if box[0] <= t[0] < box[2] and box[1] <= t[1] < box[3] and (pals is None or t[5] in pals)]
        ent = []
        for px, py, c, hf, vf, pal in tl:
            k = tile(c) if c in T else None
            if k:
                ent.append((px - box[0], py - box[1], k[0], hf ^ k[1], vf ^ k[2], pal))
        rows = {pal: palrow(sel / "pal.bin", f, pal) for *_, pal in ent}
        return dict(tiles=ent, palettes={str(k): v for k, v in rows.items()})
    portraits = {nm: group(f, box, pals) for nm, (f, box, pals) in PORTRAITS.items()}
    R = json.loads((work / "rounds.json").read_text())
    used = set(excl)
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
    (out / "gfx_megaman.bin").write_bytes(raw)
    base = [palrow(full / "pal.bin", 2400, 0), palrow(full / "pal.bin", 2400, 1), palrow(win / "pal.bin", 2400, 14)]
    cols = {nm: [tone(r, v, s) for r in base] for nm, (v, s) in TONES.items()}
    P = [[list(e) for e in p] for p, _ in sorted(poses.items(), key=lambda x: x[1])]

    def keyset(names):
        return sorted({keys[e[2]] for m in names for pid, _, _ in moves.get(m, []) for e in P[pid]})
    pkeys = {keys[e[2]] for v in portraits.values() for e in v["tiles"]}
    loose = sorted(set(keyset(moves)) | pkeys)
    tight_moves = trim_to_budget(BUDGET - len(pkeys), lambda pid: {keys[e[2]] for e in P[pid]})
    tight = sorted({keys[e[2]] for m, sq in tight_moves.items() for pid, *_ in sq for e in P[pid]} | pkeys)
    # Owner 11-08: ONE trimmed set on every stage, sized to the tightest stage, so he behaves the same everywhere.
    A = dict(keys=tight, all_keys=keys, untrimmed_keys=len(loose), thinned_moves=tight_moves, budget=BUDGET, poses_kept={m: len(sq) for m, sq in tight_moves.items()}, tiles=len(canon), poses=P, moves=moves, portraits=portraits, colours=cols, default_colour=DEFAULT_TONE,
             codes_seen=len(ckey), source="MvC (user ROM set mvsc) via tools/megaman/run_mame.sh",
             move_keys={m: len(keyset([m])) for m in moves}, portrait_keys=len({e[2] for v in portraits.values() for e in v["tiles"]}))
    (out / "remap.json").write_text(json.dumps(A))
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
    pick = [moves[m][len(moves[m]) // 2][0] for m in ("idle", "walk", "hp", "hk", "shoot", "shot", "rush", "crouch", "win") if moves.get(m)]
    img = Image.new("RGB", (130 * len(pick), 150 * len(TONES)), (40, 40, 48))
    for r, (nm, pal) in enumerate(cols.items()):
        for j, pid in enumerate(pick):
            draw(P[pid], pal, img, 65 + 130 * j, 145 + 150 * r)
    img.save(strips / "tones.png")
    for m, seq in moves.items():
        ids = [s[0] for s in seq][:40]
        if not ids:
            continue
        img = Image.new("RGB", (130 * len(ids), 160), (40, 40, 48))
        for j, pid in enumerate(ids):
            draw(P[pid], cols[DEFAULT_TONE], img, 65 + 130 * j, 155)
        img.save(strips / f"move_{m}.png")
    print(json.dumps(dict(loose_keys=len(loose), tight_keys=len(tight), tiles=len(canon), codes=len(ckey), poses=len(poses), moves={m: (len(s), sum(x[1] for x in s)) for m, s in moves.items()},
                          move_keys=A["move_keys"], portraits={k: len(v["tiles"]) for k, v in portraits.items()}, free_keys=len(free))))


if __name__ == "__main__":
    main()
