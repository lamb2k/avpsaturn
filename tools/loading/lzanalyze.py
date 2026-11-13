#!/usr/bin/env python
"""lzanalyze.py ROUNDS_DIR: per round file, why a tile region does or does not take the compressed path: sizes, blocks, groups on the disc, in-place tail."""
import sys, pathlib, struct
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import lzstore
d = pathlib.Path(sys.argv[1]); files = [p.read_bytes() for p in sorted(d.glob("R[0-9][0-9][0-9].BIN"))]
store, streams, info = lzstore.build_lz(files)
print(info)
n = len(files)
for i in range(n):
    s = lzstore.rebuild_stream(store, i)
    regs, _ = lzstore.split_round(s)
    flagged = [k for k, (dd, b) in enumerate(regs) if dd != 1 and b & 1]
    f = files[i]; r0, o0 = lzstore.split_round(f); t = lzstore.tile_index(r0)
    if not flagged:
        print("RAW", i, "tile", None if t is None else (r0[t][1] // 2048), "sectors")
    else:
        k = flagged[0]; nb = struct.unpack_from(">I", s, 1024 + 12)[0]; T = struct.unpack_from(">I", s, 1024 + 8)[0]
        raw_total = regs[k][1] & ~1
        comp = struct.unpack_from(">%dI" % (2 * nb), s, 1024 + 16)
        secs = struct.unpack_from(">%dI" % nb, s, 1024 + 16 + 8 * nb)
        groups = 1 + sum(1 for j in range(1, nb) if secs[j] != secs[j - 1] + (comp[2 * (j - 1) + 1] + 2047) // 2048)
        runs = 0
        print("LZ ", i, "tile", raw_total // 2048, "blocks", nb, "groups", groups, "comp sectors", sum((comp[2 * j + 1] + 2047) // 2048 for j in range(nb)), "tail", T)
