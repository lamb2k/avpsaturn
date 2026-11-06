#!/usr/bin/env python
"""Build the single ROM image used by tests and the lifted program: E:/AvP/learning/merged.bin.

The board fetches instructions and pc-relative reads through the opcode space, other data through the program space.
So the image is program bytes, with opcode bytes over all reachable instructions and over the data they read pc-relative.
Word tables take 2 bytes per recovered entry and long tables 4. A pc-relative operand without a recovered table takes the
bytes up to the next instruction, at most 64.
"""
import json
import pathlib
import re
import sys

keep = sys.argv
sys.argv = ["x", "style"]
import importlib.util as iu
sp = iu.spec_from_file_location("cfg", pathlib.Path(__file__).parent / "learn_cfg68k.py")
c = iu.module_from_spec(sp)
sp.loader.exec_module(c)
sys.argv = keep

d = json.load(open(c.OUT / "cfg.json"))
img = bytearray(c.PR)
seen = {int(k, 16): v for k, v in d["seen"].items()}
for a, n in seen.items():
    img[a:a + n] = c.OP[a:a + n]
tables = {int(k, 16): v for k, v in d["tables"].items()}
widths = {}
pcuse = set()
for a in seen:
    i = c.insn(a)
    for m in re.finditer(r"\$([0-9a-f]+)\(pc(,[^)]*)?\)", i.op_str):
        t = int(m[1], 16)
        if t not in seen:
            pcuse.add(t)
        if t in tables:
            widths[t] = 4 if i.mnemonic.startswith("movea.l") or i.mnemonic.startswith("move.l") else 2
for t, tg in tables.items():
    if t in seen:
        continue                       # bra tables are code
    n = len(tg) * widths.get(t, 2)
    img[t:t + n] = c.OP[t:t + n]
for t in pcuse - set(tables):
    e = t
    while e < t + 64 and e not in seen:
        e += 2
    img[t:e] = c.OP[t:e]
(c.OUT / "merged.bin").write_bytes(img)
print("merged", len(pcuse), "pc-relative data sites;", len(tables), "tables")
