#!/usr/bin/env python
"""Per-vblank diff of two host-runner PDUMP files (tools/lift_runner/host_kernel.c): Schaefer against the fork, same pad script.

Each record is 532 bytes: player 1 block (ff8380, 256 B), player 2 block (ff8480, 256 B), five FNV hashes of the outbound regions
(collision lists, effect spawns, globals, enemy/object blocks, projectile pool). The 61 interface fields are the word rows of
docs/guests/PLAYER_INTERFACE.md (the player-block census). A field is compared as the 16-bit word at its offset, so the long fields
(+0e/+0f, +1c/+1e, +50/+52, ...) are covered by their two halves; the whole 256-byte block is also compared.

usage: fielddiff.py A.bin B.bin [--json OUT] [--allow allowlist.json] [--player 0,1]
exit 0 when identical (no field, block or region differs), else 1.
An allowlist maps a field name ("+2c") to the largest tolerated divergent-frame count and is used from Stage 1 on."""
import argparse
import json
import pathlib
import re
import sys

REC = 532
HERE = pathlib.Path(__file__).resolve().parent
OUTBOUND = ["collision_lists", "effect_spawns", "globals", "enemy_object_blocks", "projectile_pool"]


def fields():
    t = (HERE.parents[1] / "docs/guests/PLAYER_INTERFACE.md").read_text()
    out = []
    for m in re.finditer(r"^\| \+([0-9a-f]{2}) \|", t, re.M):
        out.append(int(m.group(1), 16))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--json")
    ap.add_argument("--allow")
    ap.add_argument("--player", default="0,1")
    ap.add_argument("--frames", type=int, default=0)
    args = ap.parse_args()
    F = fields()
    assert len(F) == 61, len(F)
    allow = json.loads(pathlib.Path(args.allow).read_text()) if args.allow else {}
    players = [int(x) for x in args.player.split(",")]
    fa, fb = open(args.a, "rb"), open(args.b, "rb")
    n = min(pathlib.Path(args.a).stat().st_size, pathlib.Path(args.b).stat().st_size) // REC
    if args.frames:
        n = min(n, args.frames)
    size_note = None
    if pathlib.Path(args.a).stat().st_size != pathlib.Path(args.b).stat().st_size:
        size_note = "record counts differ: %d vs %d" % (pathlib.Path(args.a).stat().st_size // REC, pathlib.Path(args.b).stat().st_size // REC)
    first, count = {}, {}
    block_first, block_count = {}, {}
    out_first, out_count = {}, {}
    CH = 4096
    f = 0
    while f < n:
        k = min(CH, n - f)
        da, db = fa.read(k * REC), fb.read(k * REC)
        if da != db:
            for i in range(k):
                ra, rb = da[i * REC:(i + 1) * REC], db[i * REC:(i + 1) * REC]
                if ra == rb:
                    continue
                for p in players:
                    pa, pb = ra[p * 256:(p + 1) * 256], rb[p * 256:(p + 1) * 256]
                    if pa == pb:
                        continue
                    block_first.setdefault(p, f + i)
                    block_count[p] = block_count.get(p, 0) + 1
                    for off in F:
                        if pa[off:off + 2] != pb[off:off + 2]:
                            key = (p, off)
                            first.setdefault(key, f + i)
                            count[key] = count.get(key, 0) + 1
                for j, nm in enumerate(OUTBOUND):
                    if ra[512 + 4 * j:516 + 4 * j] != rb[512 + 4 * j:516 + 4 * j]:
                        out_first.setdefault(nm, f + i)
                        out_count[nm] = out_count.get(nm, 0) + 1
        f += k
    rows = []
    bad = 0
    for p in players:
        for off in F:
            c = count.get((p, off), 0)
            lim = allow.get("+%02x" % off, 0)
            if c > lim:
                bad += 1
            rows.append(dict(player=p + 1, field="+%02x" % off, first=first.get((p, off)), frames=c, allowed=lim))
    res = dict(frames=n, note=size_note, fields_differing=bad, fields_checked=len(F) * len(players),
               block_frames={str(p + 1): block_count.get(p, 0) for p in players},
               block_first={str(p + 1): block_first.get(p) for p in players},
               outbound={nm: dict(first=out_first.get(nm), frames=out_count.get(nm, 0)) for nm in OUTBOUND}, rows=[r for r in rows if r["frames"]])
    print("frames %d, fields checked %d (61 x %d players), fields differing %d" % (n, len(F) * len(players), len(players), bad))
    print("whole-block frames differing:", res["block_frames"], "first:", res["block_first"])
    print("outbound regions differing:", {k: v["frames"] for k, v in res["outbound"].items()})
    if size_note:
        print(size_note)
    for r in res["rows"][:70]:
        print("  P%d %s first frame %s, %d frames (allowed %d)" % (r["player"], r["field"], r["first"], r["frames"], r["allowed"]))
    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(res, indent=1))
    ident = bad == 0 and not any(block_count.values()) and not any(out_count.values()) and not size_note
    print("IDENTICAL" if ident else "DIFFERENT")
    return 0 if ident else 1


if __name__ == "__main__":
    sys.exit(main())
