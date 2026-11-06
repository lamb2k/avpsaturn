#!/usr/bin/env python
"""List non-1 tick runs and test: ticks != 1 explained by ff81b9 wake guard or overrun catch-up.
usage: learn_tick_runs.py CAPTURE_DIR [FIRST LAST]"""
import collections
import csv
import pathlib
import sys

cap = pathlib.Path(sys.argv[1])
first = int(sys.argv[2]) if len(sys.argv) > 2 else 1972
last = int(sys.argv[3]) if len(sys.argv) > 3 else 5566
csv.field_size_limit(1 << 20)
F = collections.defaultdict(lambda: dict(ticks=0, guard=set(), catch=set(), wr=set(), tail=collections.Counter(), route=None, tasks=set(), countdown=0))
with open(cap / "coffee_shop_scheduler_clock.tsv", newline="") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        fr = int(r["frame"])
        if not first <= fr <= last:
            continue
        d = F[fr]
        d["guard"].add(r.get("wake_guard","0"))
        d["wr"].add(r.get("wake_request","0"))
        d["route"] = r["route"]
        if r["event"] != "opcode_fetch":
            continue
        s = r["site"]
        if s == "00808a":
            d["ticks"] += 1
            d["catch"].add(r["catchup"])
        elif s in ("008156", "00814a", "008162"):
            d["tail"][s] += 1
        elif s == "000e9e":
            d["countdown"] += 1
cross = collections.Counter()
for fr in range(first, last + 1):
    d = F[fr]
    g = "guard" if d["guard"] - {"0", "-1", ""} else "noguard"
    cross[g, d["ticks"]] += 1
print("(wake_guard nonzero during frame, ticks in frame): frames")
for k, v in sorted(cross.items()):
    print(" ", k, v)
ov = collections.Counter()
for fr in range(first, last + 1):
    d = F[fr]
    g = "guard" if d["guard"] - {"0", "-1", ""} else "noguard"
    ov[g, d["tail"]["008156"]] += 1
print("(guard, overrun-branch count in frame): frames", sorted(ov.items()))
tail = collections.Counter()
for d in F.values():
    tail.update(d["tail"])
print("tail branch totals", dict(tail), "(008156 = overrun seen; 00814a = wait; 008162 = continue)")
runs, cur = [], None
for fr in range(first, last + 1):
    t = F[fr]["ticks"]
    if t != 1:
        if cur and cur[1] == fr - 1:
            cur[1] = fr
            cur[2].append(t)
        else:
            cur = [fr, fr, [t]]
            runs.append(cur)
for a, b, ts in runs:
    gs = set().union(*(F[x]["guard"] for x in range(a, b + 1)))
    print(f"{a}..{b} ticks={''.join(map(str, ts))[:60]} guard={sorted(gs)} route={F[a]['route']}")
