#!/usr/bin/env python
"""Lane satint: the full Round 1 tile pack from the MAME census (tools/satint_census.py).
Main part (header, keys, sprite and scroll 2 tiles) goes on the cart at PACK_ADDR; scroll 1 and 3 tiles go into a stretch of ROM the Round 1 route never read.
Sprite and scroll 2 tiles past MAIN_ROOM spill into their own ROM stretches (SPILL), written to WORK/pack_spill.bin as a whole image of those stretches; the header gives each section's split index and spill offset.
usage: satint_pack.py WORK CENSUSDIR PACK_ADDR [MAIN_ROOM]  ROM-derived: output stays in WORK, never commit."""
import pathlib, struct, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import satgfx_pack
W, C, PACK = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), int(sys.argv[3], 16)
ROMB = 0x02400000
HOLE, HOLE_SIZE = 0x198000, 200 * 1024
keys = [set(), set(), set(), set()]
for l in open(C / "keys.txt"):
    a, b = l.split()
    if a != "irq":
        keys[int(a)].add(int(b, 16))
data, _ = satgfx_pack.pack(pathlib.Path("E:/AvP/learning/lane-satgfx/gfx.bin").read_bytes(), keys)
secs = [struct.unpack_from(">III", data, 4 + i * 12) for i in range(4)]
ends = [secs[i + 1][1] if i < 3 else len(data) for i in range(4)]
SPILL = {0: (0x105000, 60 * 1024), 2: (0x171000, 60 * 1024)}
SLOT = {0: 128, 2: 128}
ROOM = int(sys.argv[4]) if len(sys.argv) > 4 else 1 << 30
HEAD = 4 + 12 * 4 + 8 * 4
key_bytes = sum(ends_k for ends_k in (secs[i][2] - secs[i][1] for i in range(4)))
main_data = {i: ends[i] - secs[i][2] for i in (0, 2)}
over = max(0, HEAD + key_bytes + sum(main_data.values()) - ROOM)
move = {0: 0, 2: 0}
for i in (0, 2):   # sprites spill first, then scroll 2, whole tiles
    take = min((over + 127 & ~127), main_data[i] // 128 * 128, SPILL[i][1])
    move[i] = take; over = max(0, over - take)
assert not over, over
main, hole, hdr, spill = bytearray(), bytearray(), [struct.pack(">I", 0x53475031)], {}
main += bytes(HEAD)
tail = []
for i in range(4):
    n, ko, do = secs[i]
    k, d = data[ko:do], data[do:ends[i]]
    nk = len(main)
    main += k
    split, sp = 0xffffffff, 0
    if i in (1, 3):
        nd = (ROMB + HOLE + len(hole) - PACK) & 0xffffffff
        hole += d
    else:
        nd = len(main)
        keep = len(d) - move[i]
        main += d[:keep]
        if move[i]:
            split = keep // SLOT[i]
            sp = (ROMB + SPILL[i][0] - PACK) & 0xffffffff
            spill[SPILL[i][0]] = d[keep:]
    hdr.append(struct.pack(">III", n, nk, nd))
    tail.append(struct.pack(">II", split, sp))
main[:HEAD] = b"".join(hdr) + b"".join(tail)
assert len(hole) <= HOLE_SIZE, len(hole)
assert len(main) <= ROOM, len(main)
(W / "pack.bin").write_bytes(main)
(W / "pack_hole.bin").write_bytes(hole)
(W / "pack_spill.json").write_text(__import__("json").dumps({hex(a): len(b) for a, b in spill.items()}))
(W / "pack_spill.bin").write_bytes(b"".join(struct.pack(">II", a, len(b)) + b for a, b in spill.items()))
print("pack main", len(main), "in ROM hole", len(hole), "of", HOLE_SIZE, "spill", {hex(a): len(b) for a, b in spill.items()}, "keys per section", [s[0] for s in secs])
