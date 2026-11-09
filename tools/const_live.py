#!/usr/bin/env python
"""Per-stage pages of the tables the lifted code addresses by constant, for the functions that run in that stage.
usage: const_live.py LIFT_FINAL_DIR FETCH_CENSUS_DIRS OUT.json [GENERIC default 8]
FETCH_CENSUS_DIRS: comma list of golden_census directories (sections/NNNN_NN.fetch.txt, the executed instruction ranges, NNNN the stage word).
A function is live in a stage when any of its instructions (P(pc) markers) was fetched in that stage's census. A stage keeps the constant-address table pages
(lea or move #imm into a0-a6, OP or RD of a literal, each with the page after: tables run forward) of the functions live in it, and of every function live in
GENERIC or more stages (generic code: an enemy that did not spawn on a census route can still spawn). Stage 0c's alien grab function f_5526a runs in the 0c census,
so its table at 0x56632 (page 0x159) is kept there, although the grab branch itself never ran on a census route.
Output: {"stages": {"<stage word>": [page...]}, "generic": GENERIC, "all": [page...]}. Used by tools/rounds_config.py (env ROUNDS_CONST_LIVE)."""
import bisect, collections, glob, json, os, re, sys
G, FETCH, OUT = sys.argv[1], sys.argv[2].split(","), sys.argv[3]
GENERIC = int(sys.argv[4]) if len(sys.argv) > 4 else 8
PAT = [re.compile(r"\ba[0-6]=0x([0-9a-f]+)u;"), re.compile(r"(?:OP|RD)(?:8|16|32)\(\(?0x([0-9a-f]+)u")]
PC = re.compile(r"\bP\(0x([0-9a-f]+)u\)")
FN = re.compile(r"^void (f_[0-9a-f]+)\(void\)\{", re.M)
ranges = collections.defaultdict(list)
for d in FETCH:
    for f in glob.glob(d + "/sections/*.fetch.txt"):
        st = int(os.path.basename(f)[:4], 16)
        for l in open(f):
            p = l.split()
            if len(p) == 2:
                ranges[st].append((int(p[0], 16), int(p[1], 16)))
merged = {}
for st, rs in ranges.items():
    out = []
    for a, b in sorted(rs):
        if out and a <= out[-1][1] + 1:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    merged[st] = (out, [x[0] for x in out])
def fetched(st, pc):
    r, starts = merged[st]
    i = bisect.bisect_right(starts, pc) - 1
    return i >= 0 and r[i][0] <= pc <= r[i][1]
funcs = {}
for f in glob.glob(G + "/c*.c"):
    s = open(f).read()
    ms = list(FN.finditer(s))
    for i, m in enumerate(ms):
        body = s[m.end():ms[i + 1].start() if i + 1 < len(ms) else len(s)]
        cs = set()
        for p in PAT:
            for c in p.finditer(body):
                a = int(c[1], 16)
                if 0x400 <= a < 0x200000:
                    cs.add(a)
        if cs:
            funcs[m[1]] = ([int(x, 16) for x in PC.findall(body)], cs)
stages = sorted(s for s in merged if s)
live = {s: {fn for fn, (pcs, cs) in funcs.items() if any(fetched(s, pc) for pc in pcs)} for s in stages}
count = {fn: sum(1 for s in stages if fn in live[s]) for fn in funcs}
def pages(fs):
    p = set()
    for fn in fs:
        for a in funcs[fn][1]:
            p |= {a >> 10, min((a >> 10) + 1, 0x7ff)}
    return p
generic = {fn for fn in funcs if count[fn] >= GENERIC}
res = {"stages": {str(s): sorted(pages(live[s] | generic)) for s in stages}, "generic": GENERIC, "all": sorted(pages(funcs))}
json.dump(res, open(OUT, "w"))
print("functions with constants", len(funcs), "generic", len(generic), "pages all", len(res["all"]), "per stage", {hex(s): len(v) for s, v in zip(stages, map(lambda s: res["stages"][str(s)], stages))})
