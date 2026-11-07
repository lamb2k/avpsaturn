#!/usr/bin/env python
"""Lane fit: per-stage use rank of sprite keys. score = 1000 * sections of the real, unassisted full route (golden census) that drew the key + walks that drew it in that stage + 500 if a KO or continue drew it.
usage: rounds_rank.py WORK CENSUS WALKDIR...   Writes WORK/key_rank.json: file name -> {key: score}. Prints what each stage's lowest ranks are. ROM-derived: E:/AvP/learning only."""
import collections, glob, json, pathlib, sys
W, C = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
R = collections.defaultdict(collections.Counter)
for f in glob.glob(str(C / "sections/*.tiles.txt")):
    s = int(pathlib.Path(f).name[:4], 16) & 0xff
    for l in open(f):
        a, k = l.split()
        if a == "0":
            R[s][int(k, 16)] += 1000
for w in sys.argv[3:]:
    for f in glob.glob(f"{w}/s[0-9a-f][0-9a-f].txt"):
        s = int(pathlib.Path(f).stem[1:], 16)
        for l in open(f):
            a, k = l.split()[:2]
            if a == "0":
                R[s][int(k, 16)] += 1
# KO, continue and game over can happen in any stage: above any tile only a walk saw, below the real route.
ko = set()
for w in sys.argv[3:]:
    for f in glob.glob(f"{w}/k00.txt"):
        ko |= {int(l.split()[1], 16) for l in open(f) if l[0] == "0"}
for c in R.values():
    for k in ko:
        c[k] += 500
out = {("front" if s == 0 else f"stage{s:02x}"): {str(k): v for k, v in c.items()} for s, c in R.items()}
(W / "key_rank.json").write_text(json.dumps(out))
print({n: len(v) for n, v in out.items()})
