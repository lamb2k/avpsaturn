#!/usr/bin/env python
"""Lane satint: the full Round 1 tile pack from the MAME census (tools/satint_census.py).
Main part (header, keys, sprite and scroll 2 tiles) goes on the cart at PACK_ADDR; scroll 1 and 3 tiles go into a stretch of ROM the Round 1 route never read.
usage: satint_pack.py WORK CENSUSDIR PACK_ADDR  ROM-derived: output stays in WORK, never commit."""
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
main, hole, hdr = bytearray(), bytearray(), [struct.pack(">I", 0x53475031)]
main += b"\0" * (4 + 12 * 4)
for i in range(4):
    n, ko, do = secs[i]
    k, d = data[ko:do], data[do:ends[i]]
    nk = len(main)
    main += k
    if i in (1, 3):
        nd = (ROMB + HOLE + len(hole) - PACK) & 0xffffffff
        hole += d
    else:
        nd = len(main)
        main += d
    hdr.append(struct.pack(">III", n, nk, nd))
main[:4 + 12 * 4] = b"".join(hdr)
assert len(hole) <= HOLE_SIZE, len(hole)
(W / "pack.bin").write_bytes(main)
(W / "pack_hole.bin").write_bytes(hole)
print("pack main", len(main), "in ROM hole", len(hole), "of", HOLE_SIZE, "keys per section", [s[0] for s in secs])
