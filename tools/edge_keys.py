#!/usr/bin/env python
"""WORK/edge_keys.txt for home builds (saturn/rt/build.py): scroll 1 tile keys the census misses because it reads only the centre crop.
1. tools/edge_keys.lua over five saved routes (four characters' full games and the 2-player route): arcade columns 0, 1 and 47.
2. Both fonts' cells at both column parities, from the ROM: the 8 px font (codes 0x20-0x7f, writer 0xaba96) and the 16 px font
   (table 0xab8b4, writer 0xabbae: code, +1, +0x10, +0x11). Text the routes never showed at an edge (P2's PRESS START in the story,
   which needs a credit the routes spend at once) is then still drawn when the home fit moves it there.
usage: edge_keys.py WORK [RUNS_DIR]   (RUNS_DIR: where tools/edge_keys.lua wrote <route>/keys.txt; ROM-derived output stays in WORK)"""
import pathlib, struct, sys
WORK = pathlib.Path(sys.argv[1])
RUNS = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else WORK / "edge_runs"
keys = set()
for f in RUNS.glob("*/keys.txt"):
    keys |= {int(l.split()[1], 16) for l in open(f) if l.strip()}
rom = (WORK / "rom_final.bin").read_bytes()
codes = set(range(0x20, 0x80))
for v in range(0x60):
    c = struct.unpack(">H", rom[0xab8b4 + 2 * v:0xab8b6 + 2 * v])[0]
    if c:
        codes |= {c, c + 1, c + 0x10, c + 0x11}
keys |= {(c << 1) | p for c in codes for p in (0, 1)}
(WORK / "edge_keys.txt").write_text("".join(f"1 {k:x}\n" for k in sorted(keys)))
print(len(keys), "keys")
