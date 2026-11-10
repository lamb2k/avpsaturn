#!/usr/bin/env python
"""Native Wolverine: the tile cost of using arcade animations (MSHvSF) whose frames are not resident. OFFLINE.
usage: tile_cost.py MSHVSF_DUMP_DIR ASSETS_DIR SUB.ENT [SUB.ENT ...]
For each animation: frames, resident frames, the 16x16 cells that have no resident tile within the merge distance K (mvlib.key_of 'far'), distinct after removing pixel-identical cells (flips included),
and the union over all animations named. A tile is 128 bytes (4 bits a pixel) in a stage's sprite pack; the sheet prints bytes per stage file (tiles x 128) and the 4 KB cart-tail step equivalent
(32 tiles = one step of the cart tail, build.py)."""
import pathlib, sys
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import mvlib, assets

dump, adir = (pathlib.Path(a) for a in sys.argv[1:3])
mv = mvlib.MV(dump, adir)
subs = mv.tables()
entry = {(si, ei): a0 for si, (b, ents) in enumerate(subs) for ei, a0 in enumerate(ents)}


def far_codes(rec):
    ap = mv.l(rec + 4)
    n = mv.w(ap + 4)
    res = []
    for i in range(n + 1):
        code, at = mv.w(ap + 10 + 4 * i), mv.w(ap + 12 + 4 * i)
        wd, ht = ((at >> 8) & 15) + 1, ((at >> 12) & 15) + 1
        for by in range(ht):
            for bx in range(wd):
                c = code + bx + 16 * by
                if mv.key_of(c) == "far": res.append(c)
    return res


def canon(code):
    px = np.array(assets.pens(mv.gfx[code * 128:code * 128 + 128]), dtype=np.uint8)
    forms = [px, px[:, ::-1], px[::-1, :], px[::-1, ::-1]]
    return min(f.tobytes() for f in forms)


union = {}
for arg in sys.argv[3:]:
    si, ei = (int(x) for x in arg.split("."))
    ch = mv.chain(entry[(si, ei)])
    frames_far = [far_codes(r) for r in ch]
    distinct = {canon(c) for fc in frames_far for c in fc}
    for fc in frames_far:
        for c in fc: union.setdefault(canon(c), c)
    print("%d.%d  %d frames, %d resident, far cells %d, distinct tiles %d (%d bytes per stage file)" % (si, ei, len(ch), sum(1 for f in frames_far if not f), sum(len(f) for f in frames_far), len(distinct), 128 * len(distinct)))
print("union: %d distinct tiles, %d bytes per stage file, %.1f cart-tail steps of 32 tiles" % (len(union), 128 * len(union), len(union) / 32.0))
