#!/usr/bin/env python
"""Join native-report audio events, owner ledgers and the sound ROM's command classes.
Writes E:/AvP/learning/audio/command_map.tsv and events.tsv (private); prints a summary only."""
import collections, json, pathlib
R = pathlib.Path(__file__).resolve().parents[1]
ROM = pathlib.Path("C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest/avspu/avp.01").read_bytes()
OUT = pathlib.Path("E:/AvP/learning/audio")
def lg(a):                       # logical 24-bit sound address to ROM offset (0xa71 reader, file offset 0x8000 is bank 0)
    return 0x8000 + max((a >> 14) - 2, 0) * 0x4000 + (a & 0x3fff)
MOD = (ROM[lg(0x9000)] << 8) | ROM[lg(0x9001)]
def cmd_class(c):
    if c >> 8 == 0xff:
        return "ctrl", c & 0xff, None
    e = lg(0x9006) + 4 * (c % MOD)
    p = (ROM[e] << 16) | (ROM[e + 1] << 8) | ROM[e + 2]
    if p == 0:
        return "null", 0, None
    h = ROM[lg(p)]
    if h == 0:
        v = sum(1 for i in range(16) if ROM[lg(p + 1 + 2 * i)] or ROM[lg(p + 2 + 2 * i)])
        return "music", 0, v
    if h >= 0x80:
        b = ROM[lg(p + 1)]
        return "adpcm", h & 0x7f, b & 3
    v = sum(1 for i in range(16) if ROM[lg(p + 1 + 2 * i)] or ROM[lg(p + 2 + 2 * i)])
    return "sfx", h, v
def family_index():
    fam = {}
    for f in "boss encounter enemy presentation projectile route".split():
        x = json.load(open(R / f"data/spec02_{f}_audio_owner_program.json"))
        for c in x["commands"]:
            fam.setdefault(int(c, 16), set()).add(f)
    p = json.load(open(R / "data/oracle11_predator_player_audio.json"))
    return fam, p
if __name__ == "__main__":
    fam, player = family_index()
    print("table modulus", hex(MOD), "player keys", list(player.keys())[:12])
    c = collections.Counter(cmd_class(i)[0] for i in range(MOD))
    print("all table entries by class:", dict(c))
    ev = json.load(open(R / "data/reimplement13_coffee_shop_scene_parity.json"))["scene_events"]["audio"]
    h = json.load(open(R / "data/oracle11_global_audio_handlers.json"))
    seen = collections.Counter(int(o["command"], 16) for o in h["command_occurrences"])
    rows = []
    for k in sorted(seen):
        cl = cmd_class(k)
        rows.append((k, cl, seen[k], sorted(fam.get(k, []))))
    with open(OUT / "command_map.tsv", "w") as f:
        for k, cl, n, fm in rows:
            f.write(f"{k:04x}\t{cl[0]}\t{cl[1]}\t{cl[2]}\t{n}\t{','.join(fm)}\n")
            print(f"{k:04x} {cl[0]:6} prio={cl[1]} n={cl[2]} seen={n} {','.join(fm)}")
    by = collections.defaultdict(list)
    for e in ev:
        by[(e["origin_a6"][:8], tuple(e["caller_chain"][1:2]), e["command_u16"])].append(e["frame"])
    with open(OUT / "events.tsv", "w") as f:
        for (o, ch, c), fr in sorted(by.items(), key=lambda kv: kv[1][0]):
            f.write(f"{o}\t{ch[0] if ch else ''}\t{c}\t{len(fr)}\t{fr[0]}\t{fr[-1]}\n")
    print("events", len(ev), "groups", len(by))
    print("by class", collections.Counter(cmd_class(int(e["command_u16"], 16))[0] for e in ev))
    print("by origin", collections.Counter(e["origin_a6"] for e in ev).most_common(30))
    print("by cmd", collections.Counter(e["command_u16"] for e in ev).most_common(60))
    print("by caller", collections.Counter(e["caller_chain"][0] + ">" + e["caller_chain"][1] for e in ev).most_common(40))
    print("fam-covered", sum(1 for e in ev if int(e["command_u16"], 16) in fam), "src classes", collections.Counter(e["source_classification"] for e in ev))
    print("max frame", max(e["frame"] for e in ev), "ff window 5449..5559:", [(e["frame"], e["command_u16"]) for e in ev if 5449 <= e["frame"] <= 5559])
    fr = collections.Counter(e["frame"] for e in ev); print("max enq in a frame", fr.most_common(5))
