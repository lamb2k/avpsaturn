#!/usr/bin/env python
"""Jump table entries the code map did not follow, from a whole-game fatal 0xe1 at 0x4d698 (table 0x4d5a4 not in the map; only entries reached by MAME were seen).
For each pc-indexed jmp/jsr in seen code: read word offsets from the table base up to its lowest forward target. An entry counts when it is even, unseen, follows a terminator and decodes as code.
usage: table_gap_roots.py CFG.json OP.bin   prints roots, one hex per line; details on stderr."""
import json, sys
d = json.load(open(sys.argv[1])); o = open(sys.argv[2], "rb").read()
key = lambda k: int(k, 16) if isinstance(k, str) else k
seen = {key(k) for k in d["seen"]}; funcs = {key(k) for k in d["funcs"]}
u16 = lambda a: int.from_bytes(o[a:a + 2], "big")
s16 = lambda a: u16(a) - 0x10000 if u16(a) >= 0x8000 else u16(a)
TERM = {0x4e75, 0x4e73, 0x4e77}
new = {}
for a in sorted(seen):
    if u16(a) not in (0x4efb, 0x4ebb):
        continue
    x = o[a + 3]; base = a + 2 + (x - 256 if x >= 128 else x)
    lim = base + 512; i = 0; got = []
    while base + i * 2 < lim:
        t = base + s16(base + i * 2)
        if t & 1 or not 0x400 <= t < 0x200000:
            break
        if t > base and t < lim:
            lim = t
        got.append(t); i += 1
    for t in got:
        if t in seen or t in funcs:
            continue
        p = u16(t - 2)
        if p in TERM or u16(t - 4) in (0x6000, 0x4efa) or p & 0xff00 == 0x6000:   # rts, bra.w or bra.s just before
            new.setdefault(t, hex(a))
for t, a in sorted(new.items()):
    print(f"{t:x}")
    print(f"{t:x} from {a}", file=sys.stderr)
