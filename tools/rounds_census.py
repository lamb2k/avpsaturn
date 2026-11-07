#!/usr/bin/env python
"""Lane rounds: join walks (tools/rounds_walk.py) and golden2 censuses into per-stage sets and the ROM map.
usage: rounds_census.py OUT.json WALKDIR [WALKDIR...]
Reports each stage's keys, ROM words, sound commands, ROM pages no walk ever read, and instruction words the lift does not know.
ROM-derived: output stays under E:/AvP/learning."""
import glob, json, pathlib, sys
PAGE = 0x400
stages = {}
for w in sys.argv[2:]:
    for f in glob.glob(f"{w}/s[0-9a-f][0-9a-f].txt") + glob.glob(f"{w}/k00.txt"):
        s = 0x100 if pathlib.Path(f).stem[0] == "k" else int(pathlib.Path(f).stem[1:], 16)
        b = stages.setdefault(s, dict(keys=[set(), set(), set(), set()], r=set(), o=set(), m=set(), frames=0))
        for l in open(f):
            a, c = l.split()[:2]
            if a == "frames": b["frames"] += int(c)
            elif a == "r": b["r"].add(int(c, 16))
            elif a == "o": b["o"].add(int(c, 16))
            elif a == "m": b["m"].add(int(c, 16))
            else: b["keys"][int(a)].add(int(c, 16))
read = set()
for b in stages.values():
    read |= b["r"]
cfg = json.load(open("E:/AvP/learning/cfg.json"))
insn = set()
for k, n in cfg["seen"].items():
    insn.update(range(int(k, 16), int(k, 16) + n))
oall = set().union(*(b["o"] for b in stages.values()))
unknown = sorted(a for a in oall if a not in insn)
pages = {a // PAGE for a in read}
runs, start = [], None
for p in range(0x200000 // PAGE + 1):
    free = p not in pages and p < 0x200000 // PAGE
    if free and start is None:
        start = p
    if not free and start is not None:
        runs.append([start * PAGE, (p - start) * PAGE]); start = None
runs.sort(key=lambda r: -r[1])
print("ROM words read", len(read), "free pages total KB", sum(r[1] for r in runs) // 1024, "runs >=32K", [(hex(a), n // 1024) for a, n in runs if n >= 0x8000])
print("opcode-space words read", len(oall), "not instruction words in the code map", len(unknown))
for s in sorted(stages):
    b = stages[s]
    print(f"{'any stage' if s == 0x100 else 'stage'} {s:02x} frames {b['frames']} keys {[len(k) for k in b['keys']]} rom words {len(b['r'])} sound {len(b['m'])}")
json.dump({"holes": runs, "page": PAGE, "stages": {("any" if s == 0x100 else f"{s:02x}"): dict(frames=b["frames"], keys=[sorted(k) for k in b["keys"]], sound=sorted(b["m"]), pages=sorted({a // PAGE for a in b["r"]})) for s, b in stages.items()}, "oreads": sorted(oall)},
          open(sys.argv[1], "w"))
