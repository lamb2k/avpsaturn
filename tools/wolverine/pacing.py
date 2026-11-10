#!/usr/bin/env python
"""Chain pacing from a host-runner guest trace (tools/lift_runner/host_guests.c wv_host_trace, build with -DWV_HOST_TRACE).

Measures, per chain stage, in game ticks (one player update per vblank, a held tick counts): startup (first tick of the move to the first tick
with a hit box out), active (ticks with a hit box), recovery (last active tick to the next move), total, and the next-input window (ticks from
the start of one chain attack to the start of the next one in the same chain, i.e. how soon the next press was accepted). Stages: LP1, LP2, HP,
HK (the kick). The hit box comes from the generated tables of the move (gen/wolverine_data.inc), so a tick "with a hit box" is the tick whose
published step has one. HOST measurement of the guest's presentation clock plus the native state it follows; not a hardware timing.

usage: pacing.py TRACE.txt [--gen gen/wolverine_data.inc] [--json OUT] [--label TEXT]
Trace line: vblank kind player a b c cur step left exec wall chain cstg hw x z (hex a b c)."""
import argparse
import collections
import json
import statistics
import sys

LP, HP, HK = 3, 4, 5
NAMES = {LP: "LP", HP: "HP", HK: "HK"}


def stage_name(cur, cstg):
    if cur == LP:
        return "LP1" if cstg == 0 else "LP2"
    if cur == HP:
        return "HP"
    return "HK"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trace")
    ap.add_argument("--json")
    ap.add_argument("--label", default="")
    ap.add_argument("--player", type=int, default=0)
    a = ap.parse_args()
    rec = []
    for l in open(a.trace):
        p = l.split()
        if len(p) < 16 or int(p[2]) != a.player:
            continue
        rec.append(dict(v=int(p[0]), kind=int(p[1]), a=int(p[3], 16), b=int(p[4], 16), c=int(p[5], 16), cur=int(p[6]), step=int(p[7]),
                        left=int(p[8]), exec=int(p[9]), wall=int(p[10]), chain=int(p[11]), cstg=int(p[12]), hw=int(p[13])))
    # one record per vblank (the last of the vblank wins: a held tick is kind 0, a run tick kind 1)
    last = {}
    for r in rec:
        last[r["v"]] = r
    ticks = [last[v] for v in sorted(last)]
    # instances of an attack move: a new one starts when the move changes or its wall clock restarts
    inst, cur_i = [], None
    prev = None
    for r in ticks:
        atk = r["cur"] in NAMES
        newi = False
        if atk:
            if prev is None or prev["v"] + 1 != r["v"] or prev["cur"] != r["cur"] or r["wall"] <= prev["wall"] and r["wall"] <= 2:
                newi = True
        if newi:
            cur_i = dict(start=r["v"], cur=r["cur"], cstg=r["cstg"], ticks=[r])
            inst.append(cur_i)
        elif atk and cur_i is not None:
            cur_i["ticks"].append(r)
        else:
            cur_i = None
        prev = r
    out = collections.defaultdict(lambda: collections.defaultdict(list))
    seen_chain = []
    for n, i in enumerate(inst):
        st = stage_name(i["cur"], i["cstg"])
        t = i["ticks"]
        hw = [k for k, r in enumerate(t) if r["hw"]]
        if not hw:
            continue
        first, lastw = hw[0], hw[-1]
        total = len(t)
        # the move continues in recovery (idle pose) until the next instance or the tick the state is no longer the attack's
        end = i["start"] + total
        nxt = inst[n + 1]["start"] if n + 1 < len(inst) else None
        out[st]["startup"].append(first)
        out[st]["active"].append(lastw - first + 1)
        out[st]["recovery"].append(total - lastw - 1)
        out[st]["total"].append(total)
        if nxt is not None and nxt - i["start"] <= 40:
            out[st]["to_next_attack"].append(nxt - i["start"])
    res = {}
    print("pacing %s (player %d): %d attack instances in %d ticks" % (a.label, a.player + 1, len(inst), len(ticks)))
    for st in ("LP1", "LP2", "HP", "HK"):
        d = out.get(st)
        if not d:
            print(" %-3s no instance" % st)
            continue
        row = {}
        for k in ("startup", "active", "recovery", "total", "to_next_attack"):
            v = d.get(k, [])
            if v:
                row[k] = dict(n=len(v), min=min(v), median=statistics.median(v), max=max(v), mode=collections.Counter(v).most_common(1)[0][0])
        res[st] = row
        print(" %-3s n=%-4d " % (st, row["total"]["n"]) + "  ".join("%s %d/%s/%d (mode %d)" % (k, row[k]["min"], ("%g" % row[k]["median"]), row[k]["max"], row[k]["mode"]) for k in row if k != "total") + "  total %d/%g/%d" % (row["total"]["min"], row["total"]["median"], row["total"]["max"]))
    if a.json:
        open(a.json, "w").write(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
