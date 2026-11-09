#!/usr/bin/env python
"""Lane wv-native-gfx 11-09: the relocated donor block for the HOST identity run (plan V2 section 5).
Schaefer's animation data is one span of the ROM image: index tables (0x162f90..0x163158, four overlapping tables of 16-bit offsets), frame records (two clusters, 0x163158..0x165490
and 0x166ce2..0x167570) with pose assemblies between them. The span is copied verbatim to window offset 0 (68000 address 0x300000, delta 0x19d070). The only changed bytes are the
32-bit jump targets of the jump records (+16 of a record whose flags word has bit 15), each plus the delta. Assembly pointers (record +4) stay as they are: the assemblies stay in the ROM image.
Output: BLOCK.bin (64 KB window image), and a report of the named pointer changes.
usage: reloc_block.py ROM_IMAGE BLOCK.bin"""
import sys

rom = open(sys.argv[1], "rb").read()
LO, END, WIN = 0x162f90, 0x167580, 0x300000
D = WIN - LO
blk = bytearray(0x10000)
blk[:END - LO] = rom[LO:END]
w = lambda a: int.from_bytes(rom[a:a + 2], "big")
l = lambda a: int.from_bytes(rom[a:a + 4], "big")
s16 = lambda v: v - 65536 if v >= 32768 else v
TABLES = ((0x162f90, 80), (0x163032, 33), (0x163074, 65), (0x1630f6, 49))   # up to the start of the next table or of the first record
FIRST_REC = 0x163158


def chain_ok(a):
    for _ in range(200):
        if not (LO <= a < END): return False
        if w(a + 2) & 0x8000:
            return LO <= l(a + 16) < END
        a += 16
    return False


recs, todo = {}, []
for b, n in TABLES:
    for i in range(n):
        a = b + s16(w(b + 2 * i))
        if a >= FIRST_REC and chain_ok(a): todo.append(a)
while todo:
    a = todo.pop()
    while a not in recs:
        fl = w(a + 2); recs[a] = fl
        if fl & 0x8000:
            t = l(a + 16)
            if t not in recs: todo.append(t)
            break
        a += 16
jumps = [a for a, fl in recs.items() if fl & 0x8000]
for a in jumps:
    blk[a + 16 - LO:a + 20 - LO] = (l(a + 16) + D).to_bytes(4, "big")
diff = sum(1 for i in range(END - LO) if blk[i] != rom[LO + i])
print("block %x..%x -> %x, %d bytes; %d records (%x..%x); %d jump targets rebased; bytes differing from the donor %d (limit %d)" % (
    LO, END, WIN, END - LO, len(recs), min(recs), max(recs), len(jumps), diff, 4 * len(jumps)))
assert diff <= 4 * len(jumps) and max(recs) + 20 <= END
open(sys.argv[2], "wb").write(blk)
