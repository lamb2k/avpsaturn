#!/usr/bin/env python
"""Native Wolverine: which chain, table slots and role a frame-record address (68000 window 0x300000...) belongs to, from a build's gen dir (wv_native.bin + wv_native.roles.txt).
usage: recmap.py GEN_DIR [soak.jsonl ...]   with a soak trace (native_soak.py, SOAK_RECS=1) prints the states and the roles their records show
library: load(gen) -> classify(rec) -> (role, [slot names])"""
import json, re, sys, pathlib, collections
TABLES = (("T1", 0, 80), ("T0", 0x163032 - 0x162f90, 33), ("T2", 0x163074 - 0x162f90, 65), ("T3", 0x1630f6 - 0x162f90, 49))


def load(gen):
    gen = pathlib.Path(gen)
    blk = (gen / "wv_native.bin").read_bytes()
    w = lambda a: int.from_bytes(blk[a:a + 2], "big")
    s16 = lambda v: v - 65536 if v >= 32768 else v
    slots = collections.defaultdict(list)   # window chain start -> slot names
    for name, base, n in TABLES:
        for i in range(n): slots[0x300000 + base + s16(w(base + 2 * i))].append("%s.%d" % (name, i))
    role_of_slot = {}
    for line in (gen / "wv_native.roles.txt").read_text().splitlines():
        m = re.match(r"[0-9a-f]+ \('(T\d)', (\d+)\) (\S+)", line)
        if m: role_of_slot["%s.%s" % (m[1], m[2])] = m[3]
    rec_of = {}
    for start, names in slots.items():
        a = start - 0x300000
        for _ in range(60):
            rec_of.setdefault(0x300000 + a, (start, names))
            if w(a + 2) & 0x8000: break
            a += 16
    def classify(rec):
        if rec not in rec_of: return ("?", [])
        start, names = rec_of[rec]
        role = next((role_of_slot[n] for n in names if n in role_of_slot), "?")
        return role, names
    return classify


if __name__ == "__main__":
    cl = load(sys.argv[1])
    for p in sys.argv[2:]:
        seen = collections.Counter(); first = {}
        for l in open(p):
            r = json.loads(l); role, names = cl(int(r["rec"], 16))
            k = (r["state"], role, ",".join(names[:4])); seen[k] += 1; first.setdefault(k, r["v"])
        for k, c in sorted(seen.items(), key=lambda kv: kv[0]): print("%s %-14s %-28s x%d (first v%d)" % (k[0], k[1], k[2], c, first[k]))
