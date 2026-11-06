#!/usr/bin/env python
"""Choose the tile keys for the pack by priority, up to the room on the cart, and write census keys for satint_pack.py.
usage: satint_fit.py WORK MAIN_ROOM HOLE_ROOM OUTDIR TIER [TIER...]
A tier is a census keys.txt ("section hexkey" lines) or a key log from a SAT_KEYLOG build (.bin), optionally suffixed :SECTIONS as in file.bin:13. Earlier tiers win. Sprite and scroll 2 data share MAIN_ROOM
with all key tables; scroll 1 and 3 data share HOLE_ROOM. ROM-derived output: stays in the work directory."""
import pathlib, struct, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import satgfx_pack
W, MAIN, HOLE, OUT = pathlib.Path(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), pathlib.Path(sys.argv[4])
raw = pathlib.Path("E:/AvP/learning/lane-satgfx/gfx.bin").read_bytes()
LOG = ((0, 0x8000), (0x8000, 0xc000), (0xc000, 0xe000), (0xe000, 0x10000))
BYTES = (128, 32, 128, 512)


def load(p):
    out = [set() for _ in range(4)]
    if p.endswith(".bin"):
        b = pathlib.Path(p).read_bytes()
        for s, (a, e) in enumerate(LOG):
            for i, x in enumerate(b[a:e]):
                for k in range(8):
                    if x >> k & 1:
                        out[s].add(i * 8 + k)
    else:
        for l in open(p):
            a, c = l.split()
            if a != "irq":
                out[int(a)].add(int(c, 16))
    return out


chosen = [set() for _ in range(4)]
seen = [dict() for _ in range(4)]
used_main, used_hole = 84, 0
stats = []
for tier in sys.argv[5:]:
    got = [0] * 4; left = [0] * 4
    name, _, only = tier.partition(":") if not tier[1:3] == ":/" else (tier, "", "")
    keys = load(name)
    for s in (range(4) if not only else map(int, only)):
        for k in sorted(keys[s]):
            if k in chosen[s]:
                continue
            try:
                pl, vis = satgfx_pack.payload(raw, s, k)
            except IndexError:
                continue
            new = vis and pl not in seen[s]
            cost_main = 4 + (BYTES[s] if new and s in (0, 2) else 0)
            cost_hole = BYTES[s] if new and s in (1, 3) else 0
            if used_main + cost_main > MAIN or used_hole + cost_hole > HOLE:
                left[s] += 1
                continue
            used_main += cost_main; used_hole += cost_hole
            chosen[s].add(k); got[s] += 1
            if new:
                seen[s][pl] = 1
    stats.append((tier, got, left))
OUT.mkdir(parents=True, exist_ok=True)
with open(OUT / "keys.txt", "w") as f:
    for s in range(4):
        for k in sorted(chosen[s]):
            f.write(f"{s} {k:x}\n")
for t in stats:
    print(pathlib.Path(t[0]).name, "added per section", t[1], "left out", t[2])
print("keys", [len(c) for c in chosen], "main", used_main, "of", MAIN, "hole", used_hole, "of", HOLE)
