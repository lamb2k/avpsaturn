#!/usr/bin/env python
"""Census of the sound helper library: run every 0x1a36 caller in 0x1a62..0x3a88 under Unicorn twice and record what it queues.
Writes E:/AvP/learning/audio/helpers.tsv (private); prints shape counts. Tier: unicorn, source census, not a gate."""
import collections
import importlib.util
import pathlib
import re
import sys
sys.argv = ["x"]
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import learn_unit as lu  # noqa: E402

OP = (lu.DEPS / "decrypted_opcodes_2m.bin").read_bytes()
rom = lu.Rom()
rom.stack = 0xff7f00
rom.u.mem_write(0, OP[:0x10000])  # helpers and their small pc-relative tables live here
rom.u.mem_map(0x618000, 0x2000)
rom.extra = [(0x618000, 0x2000)]
rom.ignore = [(0xff0e88, 0xff0e9c)]
entries = []
last = None
for line in open("E:/AvP/learning/audio/all.dis"):
    a, t = line.rstrip().split(": ", 1)
    a = int(a, 16)
    if 0x1a62 <= a < 0x3a88 and t.startswith("jsr $1a36"):
        entries.append(a)
A6 = 0xff9000
def run(entry, x, toggles):
    seeds = [(A6 + 0x10, x >> 8), (A6 + 0x11, x & 255), (0xff81ad, 1)]
    seeds += [(0xff0ea0 + i, toggles) for i in range(0x60)]
    try:
        mem, _ = rom.run(entry, (), dict(a6=A6), seeds)
    except Exception as e:
        return None, str(e)[:40]
    ring = sorted((a, v) for a, v in mem.items() if 0xff0a88 <= a < 0xff0e88)
    b = bytearray(16)
    for a, v in ring:
        if a - 0xff0a88 < 16:
            b[a - 0xff0a88] = v
    n = ((mem.get(0xff8021, 0)) >> 4) if 0xff8021 in mem else 0
    return (n, b.hex()), sorted(a for a in mem if not (0xff0a88 <= a < 0xff0e88) and a not in (0xff8020, 0xff8021))
rows = []
shapes = collections.Counter()
cmds = set()
for e in entries:
    r0, o0 = run(e, 0x60, 0)
    r2, _ = run(e, 0x60, 2)
    r3, _ = run(e, 0xc0, 0)
    if not r0:
        shapes["fault"] += 1
        rows.append((e, "fault", o0))
        continue
    c0, c2 = r0[1][4:8], r2[1][4:8]
    alt = c0 != c2
    pan = r0[1][8:16] != r3[1][8:16]
    v = r0[1][10:12] + "." + r0[1][14:16]
    s = ("alt" if alt else "fixed") + ("+pan" if pan else "")
    shapes[s] += 1
    cmds.update((c0, c2))
    rows.append((e, s, c0, c2, r0[1][8:16], r0[1][16:24], r0[0], ",".join(f"{a:x}" for a in o0)))
with open("E:/AvP/learning/audio/helpers.tsv", "w") as f:
    for r in rows:
        f.write("\t".join(f"{x:x}" if isinstance(x, int) else str(x) for x in r) + "\n")
print("helpers", len(entries), dict(shapes), "distinct commands", len(cmds))
