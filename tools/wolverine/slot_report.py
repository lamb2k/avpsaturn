#!/usr/bin/env python
"""Text table of the slot census (tools/wolverine/slot_census.py JSON files): one row per distinct chain start, slots that name it, states and counts seen, record shape.
Private output (ROM-derived), not for git.   usage: slot_report.py OUT.md CENSUS.json [CENSUS.json ...]"""
import collections, json, sys

slots = {}
for f in sys.argv[2:]:
    for s in json.load(open(f))["slots"]:
        k = (s["table"], s["index"])
        if k not in slots:
            slots[k] = dict(s, calls=collections.Counter(), by_char=collections.Counter())
        slots[k]["calls"].update(s["calls"]); slots[k]["by_char"].update(s["by_char"])
chains = collections.OrderedDict()
for (t, i), s in slots.items():
    if not s["chain"]:
        continue
    c = chains.setdefault(s["start"], dict(slots=[], calls=collections.Counter(), chain=s["chain"]))
    c["slots"].append("%s.%d" % (t, i)); c["calls"].update(s["calls"])
out = ["| chain | slots | states (calls by Schaefer) | recs | ticks | flag bytes | hurt / attack idx | shadow | event bytes |", "|---|---|---|---:|---:|---|---|---|---|"]
for st, c in chains.items():
    ch = c["chain"]
    out.append("| %s | %s | %s | %d | %s | %s | %s / %s | %s | %s |" % (
        st, " ".join(c["slots"]), " ".join("%s:%d" % kv for kv in c["calls"].most_common()) or "not reached",
        len(ch), "+".join(str(r["dur"]) for r in ch), " ".join("%02x" % (r["flags"] & 0xff) + ("J" if r["flags"] & 0x8000 else "") for r in ch),
        ",".join(str(r["hurt"]) for r in ch), ",".join(str(r["atk"]) for r in ch), ",".join(str(r["shadow"]) for r in ch), ",".join(r["ev"] for r in ch if r["ev"] != "00000000") or "-"))
open(sys.argv[1], "w").write("\n".join(out) + "\n")
print(len(chains), "distinct chains")
