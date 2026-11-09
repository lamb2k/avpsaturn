#!/usr/bin/env python
"""Wolverine v4.1: re-derive idle, lp and the hit moves of an assets.py output from the MAME capture (private, never in git).

1. Anchor: his origin (+0c, boxes.txt) is the pose anchor in x, 64 px left of it in object space (boxes.py). assets.py estimates the anchor from
   the feet tiles, which is 8 px (one half tile) off on poses whose lowest rows end on a different tile (the ready stance's claw frames), so the
   idle loop and lp jumped sideways by 8 px for one frame (owner v3 report: he slides back and forth standing still). idle and lp are rebuilt here
   with the anchor taken from the origin.
2. Hits: assets.py's hit_etc window began mid-knockdown, so every hit showed a tumble. hit_etc, hit_m and hit_h are now standing hitstun
   reactions of the capture (state +06 = 12, no knockdown), each taken from the origin as well. WINDOWS below are capture frames.
usage: hitpatch.py ONE4_DIR CAPTURE_DIR BOXES_TXT WORK_DIR OUT_DIR [BASE_GFX]"""
import json, os, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import assets as A

NEW = dict(idle=(1990, 1999), lp=(2180, 2239), hit_etc=(3711, 3730), hit_m=(3436, 3457), hit_h=(3735, 3757))
WIN_OVERRIDE = os.environ.get("HP_WINDOWS")
if WIN_OVERRIDE:
    for part in WIN_OVERRIDE.split(","):
        n, r = part.split("="); a, b = r.split("-"); NEW[n] = (int(a), int(b))


def main():
    one4, cap, boxes, work, out = (pathlib.Path(a) for a in sys.argv[1:6])
    base = pathlib.Path(sys.argv[6] if len(sys.argv) > 6 else "E:/AvP/learning/lane-satgfx/gfx.bin")
    out.mkdir(parents=True, exist_ok=True)
    R = json.loads((one4 / "remap.json").read_text())
    G = bytearray((one4 / "gfx_wolverine.bin").read_bytes())
    keys = list(R["keys"])
    canon = {}
    for i, k in enumerate(keys):
        canon[A.pens(bytes(G[k * 128:(k + 1) * 128]))] = i
    assert len(canon) == len(keys), "canonical tiles must be distinct"
    # Free sprite keys exactly as assets.py chooses them: the keys already assigned must be its first len(keys).
    rounds = json.loads((work / "rounds.json").read_text())
    used = set()
    for f in rounds["files"]:
        used |= set(f["keys"][0])
    for l in open(work / "screen_keys.txt"):
        if l.strip() and l.split()[0] == "0":
            used.add(int(l.split()[1], 16))
    raw = base.read_bytes()
    free = [k for k in range(1, 0x10000) if k not in used]
    free.sort(key=lambda k: (raw[k * 128:k * 128 + 128] != b"\xff" * 128, k))
    assert free[:len(keys)] == keys, "free-key order differs from the one4 allocation: wrong work dir or base gfx"
    fr, T = A.frames(cap / "obj.txt"), A.tiles(cap / "tiles.bin")
    org = {}
    for l in boxes.read_text().splitlines():
        t = l.split()
        if t[0] == "b":
            org[int(t[1])] = int(t[2])
    ckey = {}

    def tile(code):
        if code not in ckey:
            px = T[code]
            if all(p == 15 for r in px for p in r):
                ckey[code] = None
            else:
                for (h, v), q in A.flips(px).items():
                    if q in canon:
                        ckey[code] = (canon[q], h, v); break
                else:
                    canon[px] = len(canon); ckey[code] = (canon[px], 0, 0)
        return ckey[code]

    poses = {tuple(tuple(e) for e in p): i for i, p in enumerate(R["poses"])}
    assert len(poses) == len(R["poses"]), "duplicate poses in the source"
    newposes = []

    def seq_of(a, b):
        seq = []
        for f in range(a, b + 1):
            tl = [t for t in A.expand(o for o in fr.get(f, []) if (o[3] & 0x1f) in A.PALS and A.BODY[0] <= o[2] < A.BODY[1])]
            if not tl:
                continue
            assert f in org, "no origin for frame %d (boxes.txt starts at 1990)" % f
            bottom = max(p[1] for p in tl) + 16
            ax = org[f] + 64
            ent = tuple(sorted((px - ax, py - bottom, tile(c)[0], hf ^ tile(c)[1], vf ^ tile(c)[2], pal - A.PALS[0])
                               for px, py, c, hf, vf, pal in tl if tile(c)))
            if ent not in poses:
                poses[ent] = len(poses); newposes.append(ent)
            pid = poses[ent]
            if seq and seq[-1][0] == pid:
                seq[-1][1] += 1
            else:
                seq.append([pid, 1, [ax, bottom]])
        return seq

    new_moves = {name: seq_of(*w) for name, w in NEW.items()}
    # New canonical tiles take the next free keys.
    n_old = len(keys)
    for i in range(len(keys), len(canon)):
        keys.append(free[i])
    inv = {i: px for px, i in canon.items()}
    for i in range(n_old, len(canon)):
        G[keys[i] * 128:(keys[i] + 1) * 128] = A.unpens(inv[i])
    R["poses"] = [[list(e) for e in p] for p, _ in sorted(poses.items(), key=lambda x: x[1])]
    R["keys"] = keys
    R["tiles"] = len(canon)
    for name, seq in new_moves.items():
        R["moves"][name] = seq
    for stale in ("moves_one", "one_set", "stage_keys"):
        R.pop(stale, None)
    R["boxes_pending"] = True
    (out / "remap.json").write_text(json.dumps(R))
    (out / "gfx_wolverine.bin").write_bytes(bytes(G))
    print("new tiles", len(canon) - n_old, "total tiles", len(canon), "new poses", len(newposes))
    for name, seq in new_moves.items():
        print(name, "steps", len(seq), "frames", sum(s[1] for s in seq), [(s[0], s[1], s[2][0]) for s in seq])


if __name__ == "__main__":
    main()
