#!/usr/bin/env python
"""Join missing Coffee Shop lifetimes to the allocation that created them.
usage: learn_actor_lineage.py PROBE_DIR   Prints counts only, no ROM data. Tier: MAME."""
import collections
import csv
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
d = json.load(open(REPO / "data/reimplement13_coffee_shop_scene_parity.json"))
miss = set(d["missing_source_lifetime_ids"])
src = d["actor_lifetime_timeline"]["source"]
rows = list(csv.DictReader(open(pathlib.Path(sys.argv[1]) / "probe.tsv"), delimiter="\t"))
alloc = collections.defaultdict(list)
for r in rows:
    if r["event"].startswith("alloc") and int(r["count"]):
        alloc[int(r["slot"], 16)].append(r)
    if r["event"] == "table":
        alloc[int(r["slot"], 16)].append(r)
counts = collections.Counter(r["event"] for r in rows)
print({k: v for k, v in counts.items() if not k.startswith("w")})
by = collections.Counter()
allby = collections.Counter()
unknown = 0
for l in src:
    if l["first_frame"] == 5566 or l["type"] == 0:
        continue
    s = int(l["source_slot"], 16)
    cands = [r for r in alloc.get(s, []) if int(r["frame"]) <= l["first_frame"]]
    if not cands:
        unknown += 1
        continue
    # the last allocation of this slot at or before the first visible frame
    r = cands[-1]
    key = (l["type"], l["class"], r["event"] if r["event"] == "table" else r["caller"],
           r["a6_type"] + "/" + r["a6_class"] if r["event"] != "table" else "-")
    allby[key] += 1
    if l["id"] in miss:
        by[key] += 1
print("no alloc row", unknown)
print("--- missing lifetimes by spawner: type class caller owner(type/class) count")
for k, v in sorted(by.items(), key=lambda x: -x[1]):
    print(*k, v, "of", allby[k])
print("--- all spawners")
for k, v in sorted(allby.items(), key=lambda x: (x[0][0], x[0][1], -x[1])):
    print(*k, v)
