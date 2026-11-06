#!/usr/bin/env python
"""Census cooperative tasks and suspend sites from a retained scheduler-clock ledger.
usage: learn_task_census.py CAPTURE_DIR [FIRST LAST]"""
import collections
import csv
import pathlib
import sys

cap = pathlib.Path(sys.argv[1])
first = int(sys.argv[2]) if len(sys.argv) > 2 else 1972
last = int(sys.argv[3]) if len(sys.argv) > 3 else 5566
csv.field_size_limit(1 << 20)
sus = collections.Counter()
zero_ctx = []
prev_loop_task = None
ticks = collections.Counter()
last_sus = {}
with open(cap / "coffee_shop_scheduler_clock.tsv", newline="") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        fr = int(r["frame"])
        if not first <= fr <= last or r["event"] != "opcode_fetch":
            continue
        s = r["site"]
        if s == "00808a":
            ticks[fr] += 1
            prev_loop_task = r["task"]
        if s == "001060":
            key = (r["task"], r["stack_return"])
            sus[key] += 1
            last_sus.setdefault(fr, []).append(key)
print("loop task", prev_loop_task)
print("(task, return address): suspend count")
for k, v in sus.most_common(40):
    print(" ", k, v)
print("zero-tick frames: suspends by the loop task")
for fr in range(first, last):
    if ticks[fr] == 0:
        print(" ", fr, [k[1] for k in last_sus.get(fr, []) if k[0] == prev_loop_task], "other tasks:",
              len([k for k in last_sus.get(fr, []) if k[0] != prev_loop_task]))
