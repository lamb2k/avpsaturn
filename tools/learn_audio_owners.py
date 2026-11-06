#!/usr/bin/env python
"""Group the native report's 279 audio events by owner family using the retained trigger ledgers, and check alternate pairs' channels.
Prints counts only."""
import collections
import json
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from learn_audio_map import ROM, lg, MOD, cmd_class
R = pathlib.Path(__file__).resolve().parents[1]
ev = json.load(open(R / "data/reimplement13_coffee_shop_scene_parity.json"))["scene_events"]["audio"]
own = {}
d = json.load(open(R / "data/oracle11_global_audio_trigger_owners.json"))
for g in d["trigger_groups"]:
    for c in g["transition_guard"]["contexts"]:
        own[(c["origin_record"], c["source_owner_return"], g["command"])] = c["owner_family"]
fam = collections.Counter()
det = collections.defaultdict(collections.Counter)
for e in ev:
    k = (e["origin_a6"], e["caller_chain"][1], e["command_u16"])
    f = "player" if e["origin_a6"] == "0xff8380" else own.get(k)
    if f is None:
        f = next((v for (o, r, c), v in own.items() if c == e["command_u16"] and r == e["caller_chain"][1]), None)
    f = f or "other"
    fam[f] += 1
    det[f][e["command_u16"]] += 1
print("279 by owner family:", fam.most_common())
for f, c in det.items():
    print(" ", f, sorted(c.items()))
print("other:", [(e["frame"], e["origin_a6"], e["caller_chain"][1], e["command_u16"]) for e in ev
                 if e["origin_a6"] != "0xff8380" and not any(r == e["caller_chain"][1] and c == e["command_u16"] for (_, r, c) in own)][:12])
def channels(c):
    e = lg(0x9006) + 4 * (c % MOD)
    p = (ROM[e] << 16) | (ROM[e + 1] << 8) | ROM[e + 2]
    return [i for i in range(16) if ROM[lg(p + 1 + 2 * i)] or ROM[lg(p + 2 + 2 * i)]]
print("alternate-pair channels:", [(hex(a), channels(a), hex(b), channels(b)) for a, b in
      ((0x3d, 0x108), (0x3e, 0x109), (0x3f, 0x10a), (0x4d, 0x118), (0x4e, 0x119), (0x4f, 0x11a), (0x5d, 0x12d), (0x60, 0x130))])
print("music channels:", [(hex(c), channels(c)) for c in (1, 4, 6, 7, 0xf, 0x16, 0x1f)])
print("player sfx channels:", [(hex(c), channels(c)) for c in (0x24e, 0x51, 0x91, 0x96, 0x203)])
all_ch = collections.Counter()
pr = collections.Counter()
for c in range(MOD):
    k = cmd_class(c)
    if k[0] == "sfx":
        pr[k[1]] += 1
        for ch in channels(c):
            all_ch[ch] += 1
print("sfx priority histogram", sorted(pr.items()))
print("sfx use per channel", sorted(all_ch.items()))
