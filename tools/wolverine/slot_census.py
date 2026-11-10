#!/usr/bin/env python
"""Native Wolverine step 1 (2026-11-09): slot census of Schaefer's animation tables (192 slots) from HOST traces.

Input: the program image rt.bin of a build work directory and one or more traces made by the host runner
(tools/lift_runner/host_kernel.c, env WATCH=ff0000,0 TP=16518,16526,165a4: one 'T v<vblank> pc <pc> ... a6 <block> a0 <base> st <state> ch <char> tag <tag> rec <record>' line per call).
The trace is filtered to the player blocks (a6 = ff8380 + 0x100 * n, tag 00). For each slot the census gives:
  chain      the frame records the slot starts (duration, flags, hurt/attack/shadow/event bytes, jump target)
  calls      how often the slot was selected in the traces, by the player's state word (+4..6) at the call and the character number (+0xd2)
  reached    whether a Schaefer call (character 01) selected it
Output: JSON (slot_roles.json, private: ROM-derived, never in git) and a text table.
usage: slot_census.py RT.BIN OUT.json TRACE [TRACE ...]"""
import collections
import json
import sys

rom = open(sys.argv[1], "rb").read()
w = lambda a: int.from_bytes(rom[a:a + 2], "big")
l = lambda a: int.from_bytes(rom[a:a + 4], "big")
s16 = lambda v: v - 65536 if v >= 32768 else v
TABLES = {"T1": (0x162f90, 80), "T0": (0x163032, 33), "T2": (0x163074, 65), "T3": (0x1630f6, 49)}
BASES = {v[0]: k for k, v in TABLES.items()}
BASES.update({v[0] + 0x19d070: k for k, v in TABLES.items()})   # the relocated block (window 0x300000)
FIRST_REC = 0x163158


def chain(a):
    out = []
    for _ in range(80):
        fl = w(a + 2)
        r = dict(at=a, dur=w(a), flags=fl, asm=l(a + 4), hurt=rom[a + 8], atk=rom[a + 9], b10=rom[a + 10], shadow=rom[a + 11], ev=rom[a + 12:a + 16].hex())
        if fl & 0x8000:
            r["jump"] = l(a + 16)
            out.append(r)
            return out
        out.append(r)
        a += 16
    return out


slots = {}
for t, (b, n) in TABLES.items():
    for i in range(n):
        a = b + s16(w(b + 2 * i))
        slots[(t, i)] = dict(table=t, index=i, start=a, chain=chain(a) if a >= FIRST_REC else [], calls=collections.Counter(), by_char=collections.Counter(), direct=collections.Counter())

# trace
players = lambda a6: 0xff8380 <= a6 < 0xff8380 + 0x400 and (a6 - 0xff8380) % 0x100 == 0
nlines = 0
direct = collections.Counter()
rec_slots = collections.defaultdict(list)
for k, s in slots.items():
    for r in s["chain"]:
        rec_slots[r["at"]].append(k)
rec_direct = collections.Counter()   # (record, state) of f_16526 calls that are not the tail of f_16518
for f in sys.argv[3:]:
    prev = None
    for line in open(f, errors="replace"):
        if not line.startswith("T v"):
            continue
        x = line.split()
        try:
            pc = int(x[3], 16)
            d0 = int(x[5], 16)
            a6 = int(x[x.index("a6") + 1], 16)
            a0 = int(x[x.index("a0") + 1], 16)
            st = x[x.index("st") + 1]
            ch = int(x[x.index("ch") + 1], 16)
            tag = int(x[x.index("tag") + 1], 16)
        except (ValueError, IndexError):
            continue
        if not players(a6 & 0xffffff) or tag != 0:
            continue
        nlines += 1
        tail = pc == 0x16526 and prev is not None and prev[0] == 0x16518 and prev[1] == (x[1], a6)   # f_16518 ends in f_16526
        prev = (pc, (x[1], a6))
        if pc in (0x16518, 0x165a4):
            t = BASES.get(a0)
            if t is None:
                direct[("base %x" % a0, pc)] += 1
                continue
            s = slots[(t, d0 & 0xff)] if (d0 & 0xff) < TABLES[t][1] else None
            if s is None:
                direct[("index %d out of range %s" % (d0 & 0xff, t), pc)] += 1
                continue
            s["calls"][st] += 1
            s["by_char"][ch] += 1
            if pc == 0x165a4:
                s["direct"]["165a4"] += 1
        elif not tail:
            rec_direct[(a0, st, ch)] += 1

res = []
for k, s in slots.items():
    res.append(dict(table=s["table"], index=s["index"], start=hex(s["start"]), records=len(s["chain"]), ticks=sum(r["dur"] for r in s["chain"] if r["dur"] != 4095),
                    calls=dict(s["calls"]), by_char=dict(s["by_char"]), via165a4=dict(s["direct"]),
                    chain=[dict(r, at=hex(r["at"]), asm=hex(r["asm"]), jump=hex(r["jump"]) if "jump" in r else None) for r in s["chain"]]))
recs = sorted(rec_direct.items())
json.dump(dict(trace_lines=nlines, slots=res, direct={"%s|%s" % k: v for k, v in direct.items()},
               direct_records=[dict(record=hex(a), state=st, char=ch, n=n, slots=["%s.%d" % k for k in rec_slots.get(a, [])]) for (a, st, ch), n in recs]), open(sys.argv[2], "w"), indent=1)
reach = [r for r in res if r["by_char"].get(1)]
print("trace lines (player blocks):", nlines)
print("slots reached by character 1 (Schaefer):", len(reach), "of", len(res))
print("calls not through a table base:", dict(direct.most_common(12)))
print("direct f_16526 records (not the tail of f_16518):", len(rec_direct), "kinds,", sum(rec_direct.values()), "calls")
