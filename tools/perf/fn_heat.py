#!/usr/bin/env python
"""Per-function heat of the lifted code, from the profiling Ymir's dumps (hwprof_*.txt, tools/perf/README in docs/notes/AVP_PERF_HW_20261112.md).

usage: fn_heat.py OUT.json MAP ELF PROF.txt [PROF2.txt ...]

Keys are "object:symbol" (c3:f_aa016), because the static helpers every chunk carries (pb_at and friends) exist once per object. A function's heat is what the master
did in it over the profiled windows: instructions executed in the game tick and the vblank handler (the idle spin after the pass is left out: it runs only while the
master has nothing to do) and instruction cache line fills on it. The slave's code is not here (it is all in high RAM).
MAP is the link map of a build WITHOUT -ffunction-sections (one .text per object), ELF its image. The names are layout independent, so a heat file made on one build
places the code of another.
"""
import bisect
import collections
import json
import os
import re
import subprocess
import sys

NM = os.environ.get("NM", "E:/AvP/worktrees/saturn-hw/.deps/joengine/Compiler/WINDOWS/sh-elf/bin/nm.exe")


def object_ranges(map_path):
    """(start, end, object stem) of every .text input section in the map."""
    rng = []
    lines = open(map_path, errors="replace").read().splitlines()
    i = 0
    while i < len(lines):
        m = re.match(r"^ (\.text\S*)\s*$", lines[i])
        l = lines[i]
        m2 = re.match(r"^ (\.text\S*)\s+0x([0-9a-f]+)\s+0x([0-9a-f]+)\s+(.*)$", l)
        if not m2 and m and i + 1 < len(lines):   # long section names wrap
            m2 = re.match(r"^\s+0x([0-9a-f]+)\s+0x([0-9a-f]+)\s+(.*)$", lines[i + 1])
            if m2:
                a, n, path = m2.group(1), m2.group(2), m2.group(3)
                i += 1
                m2 = None
                if int(n, 16):
                    rng.append((int(a, 16), int(a, 16) + int(n, 16), re.split(r"[\\/]", path.strip())[-1].rsplit(".", 1)[0]))
                i += 1
                continue
        if m2 and int(m2.group(3), 16):
            rng.append((int(m2.group(2), 16), int(m2.group(2), 16) + int(m2.group(3), 16), re.split(r"[\\/]", m2.group(4).strip())[-1].rsplit(".", 1)[0]))
        i += 1
    rng.sort()
    return rng


def symbols(elf):
    out = subprocess.run([NM, "-S", "-n", elf], capture_output=True, text=True).stdout
    syms = []
    for l in out.splitlines():
        p = l.split()
        if len(p) == 4 and p[2] in "tTwW":
            syms.append((int(p[0], 16), int(p[1], 16), p[3]))
    return syms


def main():
    out, map_path, elf, profs = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
    rng = object_ranges(map_path)
    starts = [r[0] for r in rng]

    def obj_of(a):
        i = bisect.bisect_right(starts, a) - 1
        return rng[i][2] if i >= 0 and a < rng[i][1] else None

    syms = symbols(elf)
    saddr = [s[0] for s in syms]
    key_of = {}   # symbol index -> key

    def func_at(a):
        i = bisect.bisect_right(saddr, a) - 1
        if i < 0:
            return None
        s = syms[i]
        if a >= s[0] + max(s[1], 2) + 64:
            return None
        return i

    heat = collections.defaultdict(lambda: {"exec": 0, "ifill": 0, "size": 0, "scenes": 0})
    for pf in profs:
        seen = set()
        for l in open(pf):
            t = l.split()
            if not t or t[0] not in ("P", "IF"):
                continue
            c = int(t[1])
            if c not in (0, 2):   # master game tick and vblank handler only
                continue
            a = int(t[2], 16)
            if (a & 0x1FFFFFFF) < 0x00200000 or 0x05000000 <= (a & 0x1FFFFFFF) < 0x06000000:
                continue
            i = func_at(a)
            if i is None:
                continue
            o = obj_of(syms[i][0])
            if o is None:
                continue
            k = f"{o}:{syms[i][2][1:] if syms[i][2].startswith(chr(95)) else syms[i][2]}"
            h = heat[k]
            h["size"] = syms[i][1]
            if t[0] == "P":
                h["exec"] += int(t[3])
            else:
                h["ifill"] += int(t[3])
            if k not in seen:
                seen.add(k)
                h["scenes"] += 1
    json.dump(heat, open(out, "w"), indent=0, sort_keys=True)
    ex = [k for k, v in heat.items() if v["exec"] > 0]
    print(f"{len(heat)} functions with heat, {len(ex)} executed, {sum(heat[k]['size'] for k in ex)} bytes")


main()
