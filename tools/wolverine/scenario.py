#!/usr/bin/env python
"""Scenario metrics from host-runner dumps (PDUMP = player blocks, EDUMP = object-block health): damage in HP, hits, health cost, walk speed, state transitions.

usage: scenario.py fight|walk|special|transitions FILE.pd [FILE.ed] [--from FRAME] [--to FRAME]
  fight        enemy HP lost (sum of drops of the health word of active tag-0c blocks), hit events, player HP lost, attack runs (state 02 00 06/0e)
  walk         player 1 x/depth, px per tick over ticks where the state is walk (02 00 02) and x moved (average over the walking ticks)
  special      player 1 health before/after each special run (state 02 00 08) = the health cost
  transitions  the set of (state -> state) pairs of player 1 (+4,+5,+6), for a validity comparison
Records: PDUMP 532 bytes (fielddiff.py), EDUMP 184 bytes (46 blocks x active, tag, hp hi, hp lo)."""
import argparse
import collections
import struct
import sys

REC, EREC = 532, 184


def player(d, f):
    return d[f * REC:f * REC + 256]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode"); ap.add_argument("pd"); ap.add_argument("ed", nargs="?")
    ap.add_argument("--from", dest="lo", type=int, default=0); ap.add_argument("--to", dest="hi", type=int, default=10**9)
    a = ap.parse_args()
    d = open(a.pd, "rb").read(); n = len(d) // REC
    lo, hi = a.lo, min(a.hi, n)
    if a.mode == "fight":
        e = open(a.ed, "rb").read()
        lost, events, per = 0, [], collections.Counter()
        for f in range(max(lo, 1), min(hi, len(e) // EREC)):
            p, c = e[(f - 1) * EREC:f * EREC], e[f * EREC:(f + 1) * EREC]
            for k in range(46):
                if c[k * 4 + 1] == 0x0c and c[k * 4] and p[k * 4] and p[k * 4 + 1] == 0x0c:
                    h0, h1 = p[k * 4 + 2] << 8 | p[k * 4 + 3], c[k * 4 + 2] << 8 | c[k * 4 + 3]
                    if h1 < h0 and h0 - h1 < 300:
                        lost += h0 - h1; events.append((f, h0 - h1)); per[h0 - h1] += 1
        runs, prev = 0, None
        php, plost = None, 0
        for f in range(lo, hi):
            b = player(d, f); st = (b[4], b[5], b[6])
            if b[0] and st[0] == 2 and st[1] == 0 and st[2] in (6, 0xe) and prev != st: runs += 1
            prev = st
            hp = b[0x40] << 8 | b[0x41]
            if php is not None and hp < php and php - hp < 100: plost += php - hp
            php = hp
        print("enemy HP lost %d in %d hit events (sizes %s); player HP lost %d; attack-state entries %d" % (lost, len(events), dict(per.most_common(8)), plost, runs))
        print("first hits at frames", [f for f, _ in events[:8]])
    elif a.mode == "walk":
        xs, zs, ticks, dist = None, None, 0, 0
        prev = None
        for f in range(lo, hi):
            b = player(d, f)
            x, z = b[0x10] << 8 | b[0x11], b[0x18] << 8 | b[0x19]
            st = (b[4], b[5], b[6])
            if prev and st == (2, 0, 2) and prev[0] == (2, 0, 2):
                dx, dz = x - prev[1], z - prev[2]
                if abs(dx) < 24 and abs(dz) < 24 and (dx or dz):
                    ticks += 1; dist += abs(dx)
            prev = (st, x, z)
        wt = sum(1 for f in range(lo, hi) if (player(d, f)[4], player(d, f)[5], player(d, f)[6]) == (2, 0, 2))
        print("walk ticks %d (moving %d), x distance %d px: %.3f px per moving tick, %.3f px per walk tick" % (wt, ticks, dist, dist / max(ticks, 1), dist / max(wt, 1)))
    elif a.mode == "special":
        prev, start = None, None
        for f in range(lo, hi):
            b = player(d, f); st = (b[4], b[5], b[6]); hp = b[0x40] << 8 | b[0x41]
            if st == (2, 0, 8) and prev != (2, 0, 8): start = (f, prev_hp)
            if prev == (2, 0, 8) and st != (2, 0, 8) and start: print("special frames %d..%d (%d ticks): health %d -> %d (cost %d)" % (start[0], f, f - start[0], start[1], hp, start[1] - hp)); start = None
            prev, prev_hp = st, hp
    elif a.mode == "transitions":
        T = collections.Counter(); prev = None
        for f in range(lo, hi):
            b = player(d, f); st = (b[4], b[5], b[6]) if b[0] else None
            if prev and st and st != prev: T[(prev, st)] += 1
            prev = st
        for (s, t), c in sorted(T.items()):
            print("%02x%02x%02x -> %02x%02x%02x %d" % (s + t + (c,)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
