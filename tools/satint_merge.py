#!/usr/bin/env python
"""Lane satint: replaces the 1.06 MB opcode view on the cart with a side store of only what the lifted code reads through OP*: each pc-relative
base up to the next function (CAP bytes at most, more for a longer resolved table), plus every opcode-space read on the route that is not an
instruction. Each OP read is rewritten at build time to a constant offset in the store, so reads cost nothing extra and the data view stays exact.
usage: satint_merge.py WORK   Reads rt.bin, op.bin, src/, oreads/oreads.txt, cfg.json. Writes WORK/opx.bin, opx.json and, for the host check, WORK/hostop.bin
(data view with the store overlaid: what an OP read outside the store would see). ROM-derived: never commit."""
import bisect, json, os, pathlib, re, sys
W = pathlib.Path(sys.argv[1])
CAP = 0x100
rt, op = (W / "rt.bin").read_bytes(), (W / "op.bin").read_bytes()
LEARN = pathlib.Path(os.environ.get("LEARN_OUT", "E:/AvP/learning"))
D = json.load(open(LEARN / "cfg.json"))
funcs = sorted(D["funcs"])
tables = {int(k, 16): v for k, v in D["tables"].items()}
insn = set()
for k, n in D["seen"].items():
    insn.update(range(int(k, 16), int(k, 16) + n))
oread = {int(x, 16) for x in open(W / "oreads/oreads.txt")}
ran = set()   # instruction words the host ran over the whole route (PROF output of host_kernel.c): a table stops only at real code
if (W / "pf.txt").exists():
    for x in open(W / "pf.txt"):
        a = int(x.split()[0], 16)
        ran.update(range(a, a + D["seen"].get(hex(a)[2:], 2)))
want = set()
bases = set()
for f in (W / "src").glob("c*.c"):
    for m in re.finditer(r"\bOP(8|16|32)\(\(?0x([0-9a-f]+)u?(\+)?", f.read_text()):
        a, w = int(m[2], 16), int(m[1]) // 8
        bases.add(a)
        if m[3]:
            j = bisect.bisect_right(funcs, a)
            end = min(funcs[j] if j < len(funcs) else a + 0x100, a + CAP)
            if tables.get(a):
                end = max(end, a + w * len(tables[a]))
            # A false code root inside a table (0x4ccc0 in the table at 0x4ccb0) must not end it: go on through words the route read, up to code the host really ran.
            while end < a + CAP and end in oread and end not in ran:
                end += 2
        else:
            end = a + w
        want.update(range(a, end))
for x in open(W / "oreads/oreads.txt"):
    a = int(x, 16)
    if a not in insn:
        want.update((a, a + 1))
if (W / "opdata.txt").exists():   # tools/lift_runner/oplog.sh: what the lifted code really read
    want.update(int(x, 16) for x in open(W / "opdata.txt"))
    for x in open(W / "opdata.txt.ranges"):   # base, lowest, end: one base must stay in one run of the store, or its offset reads other bytes
        b, lo, hi = (int(y, 16) for y in x.split())
        want.update(range(min(b, lo), max(b, hi)))
want = sorted(a for a in want if a < 0x200000)
runs, a = [], 0
for x in want:
    if runs and x <= runs[-1][1] + 8:
        runs[-1][1] = x + 1
    else:
        runs.append([x & ~1, x + 1])
store, off = bytearray(), {}
for s, e in runs:
    e = (e + 1) & ~1
    off[s] = len(store)
    store += op[s:e]
keys = sorted(off)
bm = {}
for b in sorted(bases):
    r = keys[bisect.bisect_right(keys, b) - 1]
    if b < 0x200000:
        bm[hex(b)] = off[r] + b - r
(W / "opx.bin").write_bytes(store)
(W / "opx.json").write_text(json.dumps(bm))
h = bytearray(rt)
for s, e in runs:
    e = (e + 1) & ~1
    h[s:e] = op[s:e]
(W / "hostop.bin").write_bytes(h)
# Heat per lifted chunk: fetched words on the route, for placement.
heat, keyed = {}, {}
for f in (LEARN / "lift/run").glob("list*.txt"):
    n = "c" + f.stem[4:]
    for a in f.read_text().split():
        keyed[int(a, 16) >> 15] = n
for x in open(W / "oreads/oreads.txt"):
    n = keyed.get(int(x, 16) >> 15)
    if n:
        heat[n] = heat.get(n, 0) + 1
for n in set(keyed.values()):
    heat.setdefault(n, 0)
(W / "heat.json").write_text(json.dumps(heat))
print(json.dumps({"store_bytes": len(store), "runs": len(runs), "bases": len(bases)}))
