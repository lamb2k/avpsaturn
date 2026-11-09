#!/usr/bin/env python
"""Per-frame pose timeline of a Wolverine MAME capture, matched to the poses of a remap.json (HOST tool, ROM-derived output stays private).
usage: timeline.py CAPTURE_DIR ASSETS_DIR FROM TO   -> run-length lines 'frame count pose' ('?n' = layout not in remap.json)
Pose layout is the assets.py one: tile offsets from the anchor (centre of the lowest 32 pixel rows, bottom), canonical tile index, flips, palette row."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from assets import frames, expand, tiles, flips, pens, BODY, PALS


def load(adir):
    A = json.loads((pathlib.Path(adir) / "remap.json").read_text())
    raw = (pathlib.Path(adir) / "gfx_wolverine.bin").read_bytes()
    canon = {pens(raw[k * 128:k * 128 + 128]): i for i, k in enumerate(A["keys"])}
    sig = {tuple(tuple(e) for e in sorted(p)): i for i, p in enumerate(A["poses"])}
    return A, canon, sig


def timeline(capdir, adir, lo, hi):
    A, canon, sig = load(adir)
    fr, T = frames(pathlib.Path(capdir) / "obj.txt"), tiles(pathlib.Path(capdir) / "tiles.bin")
    cache, unknown, out = {}, {}, []
    for f in range(lo, hi + 1):
        objs = [o for o in fr.get(f, []) if (o[3] & 0x1f) in PALS and BODY[0] <= o[2] < BODY[1]]
        tl = expand(objs)
        if not tl:
            out.append((f, None, None)); continue
        bottom = max(p[1] for p in tl) + 16
        feet = [p[0] for p in tl if p[1] + 16 > bottom - 32]
        ax = (min(feet) + max(feet) + 16) // 2
        ent = []
        for px, py, c, hf, vf, pal in tl:
            if c not in T:
                continue
            if all(p == 15 for r in T[c] for p in r):
                continue
            for (h, v), q in flips(T[c]).items():
                if q in canon:
                    ent.append((px - ax, py - bottom, canon[q], hf ^ h, vf ^ v, pal - PALS[0])); break
            else:
                ent.append((px - ax, py - bottom, -1, 0, 0, pal - PALS[0]))
        key = tuple(sorted(ent))
        pid = sig.get(key)
        if pid is None:
            pid = "?%d" % unknown.setdefault(key, len(unknown))
        out.append((f, pid, (ax, bottom)))
    return out, A


def runs(tl):
    r = []
    for f, p, a in tl:
        if r and r[-1][2] == p:
            r[-1][1] += 1
        else:
            r.append([f, 1, p, a])
    return r


if __name__ == "__main__":
    tl, A = timeline(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
    for f, n, p, a in runs(tl):
        print(f, n, p, a)
