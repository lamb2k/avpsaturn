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
    if i.mnemonic.split(".")[0] in ("lea", "pea", "jmp", "jsr"):
        continue                       # takes an address, reads nothing through the opcode space
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

# Runtime image for lifted code. Lifted code fetches no instructions, so code bytes are never read as code: every read is data.
# Program bytes everywhere; opcode bytes only where an instruction reads pc-relative. False code decodes can't shadow data here.
rt = bytearray(c.PR)
SZ = {"b": 1, "w": 2, "l": 4}
for a in seen:
    i = c.insn(a)
    if i.mnemonic.split(".")[0] in ("lea", "pea", "jmp", "jsr"):
        continue
    for m in re.finditer(r"\$([0-9a-f]+)\(pc(,[^)]*)?\)", i.op_str):
        t = int(m[1], 16)
        if t in tables:
            continue
        if m[2]:                       # indexed: extent unknown, up to the next instruction
            e = t + 2
            while e < t + 64 and e not in seen:
                e += 2
        else:
            e = t + SZ.get(i.mnemonic.rsplit(".", 1)[-1], 2)
        rt[t:e] = c.OP[t:e]
for t, tg in tables.items():
    if t in seen:
        continue
    n = len(tg) * widths.get(t, 2)
    rt[t:t + n] = c.OP[t:t + n]
(c.OUT / "rt.bin").write_bytes(rt)
