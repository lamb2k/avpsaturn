#!/usr/bin/env python
"""Source campaign ledger and numbers.

usage: learn_ledger.py report   prints the two campaign numbers; both are byte-weighted over ROM code
       learn_ledger.py check    fails on a row whose status its evidence does not support
Ledger: docs/research/avp_source_ledger.tsv (addr size status name unit gate note). Short addresses only.
Statuses: UNDERSTOOD (named, purpose written, reader test) and GATE-PASS (also has a passing gate).
Every function is ORIGINAL-ASM by the method decision, so there is no byte-match count.
Denominators: all reachable code (cfg.json), and Round 1 route executed code (cover_a probe, if present).
"""
import bisect
import csv
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
LEARN = pathlib.Path("E:/AvP/learning")
LEDGER = REPO / "docs/research/avp_source_ledger.tsv"


def load():
    with open(LEDGER, newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def main(cmd):
    d = json.load(open(LEARN / "cfg.json"))
    seen = {int(k, 16): v for k, v in d["seen"].items()}
    total = sum(seen.values())
    cover_path = LEARN / "mame/cover_a/probe.tsv"
    cover = None
    if cover_path.exists():
        words = {int(x, 16) for x in cover_path.read_text().split()}
        cover = {a for a in seen if a in words}
    rows = load()
    gate_ok = {}
    runs = LEARN / "gate_runs.tsv"
    if runs.exists():
        for r in csv.reader(open(runs), delimiter="\t"):
            gate_ok[r[1]] = int(r[4]) == 0 and int(r[5]) > 0
    addrs = sorted(seen)
    bad = 0

    def in_row(r):
        a = int(r["addr"], 16)
        i = bisect.bisect_left(addrs, a)
        out = []
        end = a + int(r["size"], 16)
        while i < len(addrs) and addrs[i] < end:
            out.append(addrs[i])
            i += 1
        return out

    und, gate = set(), set()
    for r in rows:
        if r["status"] not in ("UNDERSTOOD", "GATE-PASS"):
            print("bad status", r["addr"], r["status"])
            bad += 1
        if r["status"] == "GATE-PASS" and not all(gate_ok.get(g) for g in r["gate"].split(",")):
            print("no passing gate run on this PC:", r["addr"], r["gate"])
            bad += 1
        if not re.fullmatch(r"[a-z][a-z0-9_]*", r["name"]) or not r["note"]:
            print("needs a name and a note:", r["addr"])
            bad += 1
        s = in_row(r)
        und.update(s)
        if r["status"] == "GATE-PASS":
            gate.update(s)

    def bytes_of(x):
        return sum(seen[a] for a in x)

    print(f"reachable code {total} bytes, {len(seen)} instructions, {len(d['funcs'])} call targets (lower bound)")
    print(f"understood under rules: {bytes_of(und)} bytes = {100 * bytes_of(und) / total:.2f}% ; rows {len(rows)}")
    print(f"gate-passed (behaviour differential, not a byte match): {bytes_of(gate)} bytes = {100 * bytes_of(gate) / total:.2f}%")
    if cover is not None:
        c = bytes_of(cover)
        print(f"Coffee Shop route executed: {c} bytes = {100 * c / total:.2f}% of reachable")
        print(f"  of that, understood {100 * bytes_of(und & cover) / c:.2f}% ; gate-passed {100 * bytes_of(gate & cover) / c:.2f}%")
    if cmd == "check" and bad:
        sys.exit(1)


main(sys.argv[1] if len(sys.argv) > 1 else "report")
