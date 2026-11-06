#!/usr/bin/env python
"""Per-task resume PCs and zero-tick holder evidence from a retained scheduler-clock ledger.
usage: learn_task_resume.py CAPTURE_DIR [FIRST LAST]"""
import collections
import csv
import pathlib
import sys

cap = pathlib.Path(sys.argv[1])
first = int(sys.argv[2]) if len(sys.argv) > 2 else 1972
last = int(sys.argv[3]) if len(sys.argv) > 3 else 5566
csv.field_size_limit(1 << 20)
res = collections.defaultdict(collections.Counter)
span = {}
held = collections.defaultdict(collections.Counter)
with open(cap / "coffee_shop_scheduler_clock.tsv", newline="") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        fr = int(r["frame"])
        if not first <= fr <= last or r["event"] != "opcode_fetch":
            continue
        if r["site"] in ("00107e", "00108e"):
            res[r["task"]][r["task_resume"], r["usp"]] += 1
            a, b = span.get(r["task"], (fr, fr))
            span[r["task"]] = (min(a, fr), max(b, fr))
        if r["site"] == "00107e" and r["task"] == "ff00d8":
            held[fr][r["stack_return"], r["usp"]] += 1
for t in sorted(res):
    print(t, "frames", span[t], "top (resume, usp):", res[t].most_common(5))
print("sample loop-task holds")
for fr in (2260, 2265, 5524, 5549, 5551, 5559, 5562, 5564, 3000):
    print(fr, dict(held.get(fr, {})))
