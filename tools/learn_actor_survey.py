#!/usr/bin/env python
"""Per-class survey over the eight pool dispatch tables. Output goes under E:/AvP/learning/actor only.
usage: learn_actor_survey.py   Sites are assigned to the class entry at or below them (body ranges are
contiguous above 0x2b000, so this is an approximation for shared low code). Tier: source."""
import bisect
import collections
import json
import pathlib
import re
import struct

import capstone

P = pathlib.Path("C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-playable-loop-pivot/.deps/mame/actorprobe")
OP = (P / "decrypted_opcodes_2m.bin").read_bytes()
MD = capstone.Cs(capstone.CS_ARCH_M68K, capstone.CS_MODE_M68K_000 | capstone.CS_MODE_BIG_ENDIAN)
OUT = pathlib.Path("E:/AvP/learning/actor")
POOLS = [(4, 0x1b846), (8, 0x1b916), (12, 0x1b974), (16, 0x1b8bc), (20, 0x1bc38), (24, 0x1ba62), (28, 0x1bcda), (36, 0x1bd48)]
seen = {int(k, 16): n for k, n in json.load(open(OUT.parent / "cfg.json"))["seen"].items()}


def table(entry):
    a = entry
    while OP[a:a + 2] != b"\x20\x7b":
        a += 2
    base = a + 2 + OP[a + 3]
    out, t = [], base
    while True:
        v = struct.unpack(">I", OP[t:t + 4])[0]
        if v >= 0x100000 or v < 0x400:
            break
        out.append(v)
        t += 4
    return base, out


entries = []
tabs = {}
for tag, e in POOLS:
    base, ent = table(e)
    tabs[tag] = (base, ent)
    for c, v in enumerate(ent):
        entries.append((v, tag, c))
entries.sort()
keys = [e[0] for e in entries]
res = collections.defaultdict(lambda: collections.Counter())
for a, n in sorted(seen.items()):
    if a < keys[0]:
        continue
    for i in MD.disasm(OP[a:a + n], a, 1):
        s = i.op_str
        m = i.mnemonic
        if not re.search(r"\$2c\(a[46]\)", s):
            continue
        kind = None
        if m == "tst.b":
            kind = "test"
        elif m.startswith("subq.b"):
            kind = "dec"
        elif m in ("clr.b",) or (m == "move.b" and s.endswith("$2c(a6)")):
            kind = "set"
        elif m == "move.b":
            kind = "read"
        else:
            kind = "other"
        k = entries[bisect.bisect_right(keys, a) - 1]
        res[(k[1], k[2])][kind] += 1
lines = []
for (tag, c), v in sorted(res.items()):
    lines.append(f"tag{tag} class{c:02x} {tabs[tag][1][c]:06x} " + " ".join(f"{a}={b}" for a, b in sorted(v.items())))
(OUT / "field2c_by_class.txt").write_text("\n".join(lines) + "\n")
(OUT / "class_tables.json").write_text(json.dumps({str(t): {"base": b, "entries": e} for t, (b, e) in tabs.items()}))
print("classes", len(entries), "with +0x2c sites", len(res))
pat = collections.Counter()
for k, v in res.items():
    pat["test+dec" if v["test"] and v["dec"] else "test only" if v["test"] else "dec only" if v["dec"] else "other"] += 1
print(pat)
for t, (b, e) in tabs.items():
    print(t, hex(b), len(e))
