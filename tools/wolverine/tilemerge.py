#!/usr/bin/env python
"""Merge near-duplicate resident tiles of a Wolverine assets directory (private data, never in git; needs numpy).

usage: tilemerge.py IN_DIR OUT_DIR [K]
Each resident tile (a tile an emitted move pose uses) that equals another resident tile, or its mirror, in all but K weighted pixels (default 4; a colour change is 1, opaque against transparent is 3)
is drawn as that tile instead (the pose entry takes the representative's key with the flips of the match composed in). Representatives are chosen
greedily by how many tiles they absorb. This frees stage tile slots that cost no art-wide changes: K 4 is 1.5 percent of a tile's pixels, almost
always an outline or shading pixel. Moves, timings and boxes are untouched (boxes.py need not be rerun); stage_keys and one_set are recomputed.
"""
import json, pathlib, shutil, sys
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import assets as A


ALPHA = 3


def main(argv):
    src, dst = pathlib.Path(argv[0]), pathlib.Path(argv[1])
    k = int(argv[2]) if len(argv) > 2 else 4
    R = json.loads((src / "remap.json").read_text())
    G = (src / "gfx_wolverine.bin").read_bytes()
    P, keys = R["poses"], R["keys"]
    emit = {s[0] for m in R["moves_one"].values() for s in m}
    tiles = sorted({t[2] for p in emit for t in P[p]})
    n = len(tiles)
    X = np.stack([np.array(A.pens(G[keys[t] * 128:keys[t] * 128 + 128]), dtype=np.uint8).reshape(256) for t in tiles])
    a = X.reshape(n, 16, 16)
    V = [a.reshape(n, 256), a[:, :, ::-1].reshape(n, 256), a[:, ::-1, :].reshape(n, 256), a[:, ::-1, ::-1].reshape(n, 256)]
    flips = [(0, 0), (1, 0), (0, 1), (1, 1)]
    best = np.full((n, n), 999, dtype=np.int16)
    which = np.zeros((n, n), dtype=np.int8)
    for f, v in enumerate(V):
        for i in range(0, n, 100):
            u, w = v[i:i + 100, None, :], X[None, :, :]
            # a colour change costs 1, an opaque pixel against a transparent one (a speck appearing or a bit of outline lost) costs ALPHA
            d = (((u != w) & (u != 15) & (w != 15)).sum(2) + ALPHA * ((u == 15) != (w == 15)).sum(2)).astype(np.int16)   # flip f of tile i against tile j
            blk = best[i:i + 100]
            better = d < blk
            blk[better] = d[better]
            which[i:i + 100][better] = f
    np.fill_diagonal(best, 999)
    near = best <= k
    order = np.argsort(-near.sum(1), kind="stable")
    covered = np.zeros(n, bool)
    target = {}   # tile index -> (representative index, flip of the representative that reproduces it)
    for i in order:
        if covered[i]:
            continue
        covered[i] = True
        target[i] = (i, 0, 0)
        for j in np.nonzero(near[i] & ~covered)[0]:
            covered[j] = True
            # best[j, i] compares flip f of j against i: j flipped by f ~ i, so j ~ i flipped by f
            target[j] = (i, *flips[which[j, i]])
    idx = {t: i for i, t in enumerate(tiles)}
    for p in P:
        for e in p:
            if e[2] in idx:
                r, fh, fv = target[idx[e[2]]]
                e[2] = tiles[r]; e[3] ^= fh; e[4] ^= fv
    used = {t[2] for p in emit for t in P[p]}
    R["one_set"] = dict(R.get("one_set", {}), tiles=len(used), merge_k=k, merged=len(tiles) - len(used))
    R["stage_keys"] = {"%02x" % st: sorted(keys[t] for t in used) for st in range(2, 0x28, 2)}
    dst.mkdir(parents=True, exist_ok=True)
    if src.resolve() != dst.resolve():
        shutil.copyfile(src / "gfx_wolverine.bin", dst / "gfx_wolverine.bin")
        if (src / "boxes.json").exists():
            shutil.copyfile(src / "boxes.json", dst / "boxes.json")
    (dst / "remap.json").write_text(json.dumps(R))
    print("tiles", len(tiles), "->", len(used), "(K=%d)" % k)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
