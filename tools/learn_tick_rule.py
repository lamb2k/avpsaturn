#!/usr/bin/env python
"""Measure the top-level tick rule from retained MAME scheduler-clock ledgers.

Reads last-seen irq_counter (ff8018) / loop_counter (ff8019) / catchup (task+0x10)
per emulated video frame. Output is aggregate statistics only.
usage: learn_tick_rule.py CAPTURE_DIR [FIRST LAST]
"""
import collections
import csv
import pathlib
import sys

cap = pathlib.Path(sys.argv[1])
first = int(sys.argv[2]) if len(sys.argv) > 2 else 1972
last = int(sys.argv[3]) if len(sys.argv) > 3 else 5566
csv.field_size_limit(1 << 20)
frames = {}
events = collections.Counter()
sites = collections.Counter()
catchups = collections.Counter()
with open(cap / "coffee_shop_scheduler_clock.tsv", newline="") as f:
    rd = csv.DictReader(f, delimiter="\t")
    if "--header" in sys.argv:
        print(rd.fieldnames)
    for r in rd:
        fr = int(r["frame"])
        if not first <= fr <= last + 1:
            continue
        events[r["event"]] += 1
        sites[r["event"], r["site"]] += 1
        frames[fr] = (int(r["irq_counter"]), int(r["loop_counter"]))
        if r["catchup"] not in ("-1", ""):
            catchups[int(r["catchup"])] += 1
hist = collections.Counter()
irq = collections.Counter()
per = []
for fr in range(first, last + 1):
    if fr in frames and fr + 1 in frames:
        di = (frames[fr + 1][0] - frames[fr][0]) & 255
        dl = (frames[fr + 1][1] - frames[fr][1]) & 255
        irq[di] += 1
        hist[dl] += 1
        per.append((fr, di, dl))
print("capture", cap.name, "frames compared", len(per), "missing", last - first + 1 - len(per))
print("irq delta per frame", sorted(irq.items()))
print("loop-tick delta per frame", sorted(hist.items()))
print("total ticks", sum(p[2] for p in per), "total irqs", sum(p[1] for p in per))
print("catchup values seen in events", sorted(catchups.items()))
print("events", events.most_common(8))
print("sites", sites.most_common(30))
# longest runs of non-1 deltas and where they happen, by 500-frame bucket
b = collections.defaultdict(collections.Counter)
for fr, _, dl in per:
    b[fr // 500 * 500][dl] += 1
for k in sorted(b):
    print(k, sorted(b[k].items()))
