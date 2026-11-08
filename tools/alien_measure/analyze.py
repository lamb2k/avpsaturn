#!/usr/bin/env python
"""Lane alien-measure: join alien_walk.lua runs into an inventory and a slot fit table.
usage: analyze.py OUT.json RUNDIR [RUNDIR...]
Fit: for each kind and stage, keys not already in that stage's file candidates (lane-packs rounds.json) = extra tiles the swap needs;
keys only that character uses in the stage (rounds_variants own set) = tiles the swap frees. ROM-derived output: E:/AvP/learning only."""
import collections, json, sys
sys.path.insert(0, "E:/AvP/worktrees/lane-packs/tools")
import rounds_variants as rv
K = collections.defaultdict(lambda: dict(keys=set(), frames=0, poses=0, stages=set(), pals=set(), states={}, runs=0, a6=set()))
for run in sys.argv[2:]:
    for l in open(run + "/kinds.tsv"):
        p = l.rstrip("\n").split("\t")
        k = K[p[1]]
        if p[0] == "KIND":
            k["frames"] += int(p[2].split()[1]); k["poses"] = max(k["poses"], int(p[4].split()[1])); k["runs"] += 1
        elif p[0] == "STAGES":
            k["stages"] |= {int(x, 16) for x in p[2].split()}
        elif p[0] == "A6":
            k["a6"] |= set(p[2].split())
        elif p[0] == "PAL":
            k["pals"].add(int(p[2]))
        elif p[0] == "STATE":
            k["states"][p[2]] = max(k["states"].get(p[2], 0), int(p[3]))
        elif p[0] == "KEYS":
            k["keys"] |= {int(x, 16) for x in p[2].split()}
R = json.load(open("E:/AvP/learning/lane-packs/work/rounds.json"))
stage_keys = {f["stages"][0]: set(f["keys"][0]) for f in R["files"] if "mask" not in f}
D = rv.Data("E:/AvP/learning/lane-packs/spec.json")
own_stage = {}
for c in rv.SOLO:
    per = collections.defaultdict(set)
    for r in D.route[c]:
        for s, v in r.items():
            per[s] |= {x for x in v[0] if x in D.own[c]}
    for w in D.walk[c]:
        for s, v in w.items():
            per[s] |= {x for x in v[0] if x in D.own[c]}
    own_stage[c] = per
out = {}
for id, k in K.items():
    extra = {f"{s:02x}": len(k["keys"] - sk) for s, sk in stage_keys.items() if s}
    out[id] = dict(frames=k["frames"], keys=len(k["keys"]), poses=k["poses"], stages=sorted(f"{s:02x}" for s in k["stages"]), pals=sorted(k["pals"]),
                   states=dict(sorted(k["states"].items())), a6=sorted(k["a6"]), extra_per_stage=extra)
json.dump(dict(kinds=out, own={str(c): {f"{s:02x}": len(v) for s, v in sorted(own_stage[c].items())} for c in rv.SOLO}, own_total={str(c): len(D.own[c]) for c in rv.SOLO}),
          open(sys.argv[1], "w"), indent=1)
for id in sorted(out, key=lambda i: -out[i]["keys"]):
    o = out[id]
    print(id, "keys", o["keys"], "frames", o["frames"], "states", len(o["states"]), "stages", " ".join(o["stages"]), "a6", " ".join(o["a6"][:3]), "extra02", o["extra_per_stage"].get("02"))
