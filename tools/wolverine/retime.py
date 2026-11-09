#!/usr/bin/env python
"""Wolverine animation pass over a reselected assets directory (private data, never in git): idle breathing loop, walk poses, no dash.

usage: retime.py IN_DIR OUT_DIR [ADD_POSES]    ADD_POSES: comma-separated pose ids made resident (e.g. walk steps; each costs its new tiles)
1. idle: MSHvSF's standing loop is 17 poses in 59 frames (capture frames 1843-1901: 17 18 19 20 21 22 23 24 0 1 2 3 4 35 46 47 48), not the 4 poses
   in 10 frames the one-frame idle capture gave. Pose 0 is its origin-anchored twin 118 (pose 0 sits 8 px off the origin). The loop is trimmed to
   the poses already resident for other moves, so it costs no tiles.
2. dash: the runtime never selects it (Schaefer's dash is the walk state), so its tiles are not resident any more.
3. Every move is trimmed again by the resident set (a dropped pose's frames go to the pose shown before it), then residency, stage_keys and
   one_set are recomputed. boxes.py must be run on the result (boxes_pending).
"""
import json, pathlib, shutil, sys

IDLE_LOOP = [(17, 4), (18, 4), (19, 3), (20, 4), (21, 3), (22, 3), (23, 4), (24, 3), (118, 4), (1, 3), (2, 4), (3, 3), (4, 3), (35, 4), (46, 3), (47, 4), (48, 3)]
DROP = ("dash",)


def trim(seq, resident):
    out = []
    for pose, frames, anchor in seq:
        if (pose in resident or not out) and not (out and out[-1][0] == pose):
            out.append([pose, frames, anchor])
        else:
            out[-1][1] += frames
    return out


def main(argv):
    src, dst = pathlib.Path(argv[0]), pathlib.Path(argv[1])
    add = {int(v) for v in argv[2].split(",") if v} if len(argv) > 2 else set()
    A = json.loads((src / "remap.json").read_text())
    P, keys, old = A["poses"], A["keys"], A["moves_one"]
    full = A["moves"]
    anchor = full["idle"][0][2] if full["idle"] else [0, 0]
    full["idle"] = [[p, n, anchor] for p, n in IDLE_LOOP]
    names = [m for m in old if m not in DROP]
    emitted = {s[0] for m in names for s in old[m]}
    keep_dash_only = {s[0] for m in DROP for s in old.get(m, [])} - {s[0] for m in names for s in old[m]}
    resident = (emitted | add) - keep_dash_only
    for _ in range(4):   # first poses of moves are always emitted; settle
        moves = {m: trim(full[m], resident) for m in names}
        now = {s[0] for seq in moves.values() for s in seq}
        if now <= resident:
            break
        resident |= now
    resident = {s[0] for seq in moves.values() for s in seq}
    tiles = {t[2] for p in resident for t in P[p]}
    A["moves_one"] = moves
    A["boxes_pending"] = True
    A["one_set"] = dict(A.get("one_set", {}), tiles=len(tiles), poses=len(resident), residency="emitted_moves", retime=sorted(add))
    A["stage_keys"] = {"%02x" % st: sorted(keys[t] for t in tiles) for st in range(2, 0x28, 2)}
    dst.mkdir(parents=True, exist_ok=True)
    if src.resolve() != dst.resolve():
        shutil.copyfile(src / "gfx_wolverine.bin", dst / "gfx_wolverine.bin")
    (dst / "remap.json").write_text(json.dumps(A))
    print("poses", len(resident), "tiles", len(tiles), {m: (len(s), sum(x[1] for x in s)) for m, s in moves.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
