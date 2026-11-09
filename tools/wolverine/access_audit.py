#!/usr/bin/env python
"""Lane wv-native-gfx 11-09: every place that reaches Schaefer's animation block, found in a finished build's work directory (plan V2 section 4, "proven access points").
Reads WORK/opx.bin + opx.json (the PC-relative tables the lifted code reads through OP16/OP32, with their 68000 source addresses) and WORK/gen/c*.c (immediates in the lifted code).
Prints addresses and counts only. A native data block must be reachable through each of these, by a mapped window address:
  - table slots in the opcode store holding a table base (patched once, 4 bytes each, entry for character 1);
  - code immediates holding a table base (resolved at build time through a macro);
  - pointers into the record and assembly range (audited one by one).
usage: access_audit.py WORK"""
import json, pathlib, re, sys

W = pathlib.Path(sys.argv[1])
ox = (W / "opx.bin").read_bytes()
j = json.loads((W / "opx.json").read_text())
inv = sorted((v, int(k, 16)) for k, v in j.items())
BASES = {0x162f90: "T1", 0x163032: "T0", 0x163074: "T2", 0x1630f6: "T3"}
REC_LO, REC_HI = 0x163158, 0x167f20


def src_of(off):
    cand = [(o, a) for o, a in inv if o <= off]
    o, a = cand[-1]
    return a + off - o


slots, ptrs = [], []
for i in range(0, len(ox) - 3, 2):
    v = int.from_bytes(ox[i:i + 4], "big")
    if v in BASES:
        slots.append((src_of(i), BASES[v]))
    elif REC_LO <= v < REC_HI:
        ptrs.append((src_of(i), v))
imm = []
for f in sorted((W / "gen").glob("c*.c"), key=lambda p: int(p.stem[1:])):
    for m in re.finditer(r"P\(0x([0-9a-f]+)u\);\{a\d=\(u32\)\(s32\)\(s32\)\(\(\(u32\)0x(162f90|163032|163074|1630f6)u\)\)", f.read_text()):
        imm.append((int(m[1], 16), BASES[int(m[2], 16)]))
print("opcode-store slots holding a table base:", len(slots))
for a, b in slots: print("  %x -> %s" % (a, b))
print("code immediates holding a table base:", len(imm))
for a, b in imm: print("  at %x -> %s" % (a, b))
print("opcode-store longs pointing into records or assemblies (%x..%x):" % (REC_LO, REC_HI), len(ptrs))
for a, v in ptrs: print("  %x -> %x" % (a, v))
