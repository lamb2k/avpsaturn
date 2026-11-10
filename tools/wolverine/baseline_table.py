#!/usr/bin/env python
"""Native Wolverine: the baseline of what a character on Schaefer's state machine needs (owner 11-10: "enough to compare what he needs to have as a baseline"). OFFLINE, ROM-derived, local only.
usage: baseline_table.py GEN_DIR WORK_DIR EXPLORE_JSON OUT_PREFIX
  GEN_DIR      a build's gen dir (wv_native.bin, wv_native.roles.txt): his chains and the role (MSHvSF source) each uses
  WORK_DIR     a build work dir (rt.bin): Schaefer's stock chains (frame count, ticks, flags, box indexes)
  EXPLORE_JSON WV_EXPLORE output of gen_native.py: every MSHvSF animation entry with its resident frame count
Writes OUT_PREFIX.csv, .md and .png: per index-table chain (the slots that share one chain are listed together): the AvP state word(s) from the census, Schaefer's frames and ticks, Wolverine's current source
and its status (proper / placeholder / alias), and the best MSHvSF candidate with its resident frames."""
import csv, json, pathlib, re, sys
from PIL import Image, ImageDraw

gen, work, explore, outp = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]), sys.argv[4]
rom = (work / "rt.bin").read_bytes()
blk = (gen / "wv_native.bin").read_bytes()
w = lambda b, o: int.from_bytes(b[o:o + 2], "big")
s16 = lambda v: v - 65536 if v >= 32768 else v
TABLES = (("T1", 0x162f90, 80), ("T0", 0x163032, 33), ("T2", 0x163074, 65), ("T3", 0x1630f6, 49))
ex = {(e["sub"], e["ent"]): e for e in json.load(open(explore))}

# ---- Schaefer's chains per slot, grouped by chain address
chains = {}   # donor chain start -> dict(slots=[...], recs=[addr...])
for t, base, n in TABLES:
    for i in range(n):
        a = base + s16(w(rom, base + 2 * i))
        if a < 0x163158: continue
        c = chains.setdefault(a, dict(slots=[], recs=[]))
        c["slots"].append("%s.%d" % (t, i))
        if not c["recs"]:
            x = a
            for _ in range(60):
                c["recs"].append(x)
                if w(rom, x + 2) & 0x8000: break
                x += 16

# ---- roles of his chains (first slot names the chain)
role_of = {}
for line in (gen / "wv_native.roles.txt").read_text().splitlines():
    m = re.match(r"([0-9a-f]+) \('(T\d)', (\d+)\) (\S+)", line)
    if m: role_of[int(m[1], 16)] = m[4]

# ---- state words from the census (static scan of the player routines, Yaba soak): slot -> state word and what it is
STATE = {
    "T1.0": ("020000", "stand"), "T1.29": ("020000", "stand (alias)"), "T1.2": ("020002", "walk"), "T1.1": ("080000", "entrance stand"), "T1.30": ("020000", "stand variant"),
    "T1.3": ("020004", "leap launch (knees bent)"), "T1.37": ("020004", "leap arc (rise, apex, fall)"), "T1.10": ("020004", "leap landing / turn"), "T1.38": ("020004", "jump attack hold"), "T1.40": ("020004", "air attack"),
    "T1.4": ("020004", "crouch / landing hold"), "T1.5": ("020004", "crouch / landing hold"), "T1.6": ("020004", "crouch / landing hold"),
    "T1.32": ("020006", "attack stage 1"), "T1.33": ("020006", "attack stage 2 (alias of 1)"), "T1.34": ("020006", "attack stage 3 (heavy)"), "T1.35": ("020006", "attack stage 4 (finisher, unused with chain B)"), "T1.36": ("020008", "special (stock chain)"),
    "T1.42": ("020008", "special (Berserker slot)"), "T1.41": ("02000a", "lunge / air attack"), "T1.14": ("02000e", "finisher pose"), "T1.16": ("02000e", "finisher swing"),
    "T1.11": ("020010", "short hold"), "T1.12": ("020010", "short hold"), "T1.13": ("020012", "crouch down"), "T1.31": ("020016", "single-pose hold"), "T1.19": ("020018", "single-pose hold"), "T1.23": ("02001a", "wait hold"),
    "T1.48": ("020400", "grab (start)"), "T1.49": ("020400", "grab"), "T1.50": ("020402", "grab hold"), "T1.51": ("020402", "grab hold"), "T1.52": ("020404", "grab hold"), "T1.53": ("020404", "grab hold"), "T1.54": ("020404", "grab hold"),
    "T1.55": ("020406", "lift"), "T1.56": ("020408", "slam / stomp"), "T1.57": ("020004", "after the slam"),
    "T2.0": ("020202", "heavy flinch"), "T2.54": ("0402xx", "KO tumble (loop)"), "T2.23": ("020202/0208xx", "getup (9 frames)"), "T2.24": ("020202/0208xx", "getup 2 (9 frames)"),
    "T2.14": ("0402xx", "knockdown flight"), "T2.16": ("0402xx", "knockdown flight and ground"), "T2.20": ("0402xx", "knockdown flight"), "T2.22": ("0402xx", "ground"), "T2.21": ("0402xx", "ground"),
}
for i in range(1, 13): STATE.setdefault("T2.%d" % i, ("020202", "hit reaction (flinch)"))
for i in (13, 15, 17, 18, 19, 25, 29, 33, 37, 46, 50): STATE.setdefault("T2.%d" % i, ("020202/0402xx", "hit reaction / knockdown alias"))
for i in range(0, 33): STATE.setdefault("T0.%d" % i, ("080000", "stage entrance"))
for i in range(0, 49): STATE.setdefault("T3.%d" % i, ("02000c", "gun aim chain (stock gun; he has no gun)"))

# ---- Wolverine's source and its status, and the candidates (MSHvSF sub.ent from the catalog; resident = frames usable today)
SRC = {"IDLE(ROM)": ("MSHvSF 0.0 idle", "proper"), "WALK(ROM)": ("MSHvSF 0.1 walk", "proper"), "LP1(ROM)": ("MSHvSF 8.0 light punch", "proper (placeholder for the double claw)"), "LP1": ("MSHvSF 8.0 light punch", "proper (placeholder for the double claw)"),
       "LP2": ("MSHvSF 8.3 light punch 2", "proper"), "HP": ("MSHvSF 8.2 heavy punch", "proper"), "LAND": ("MSHvSF 1.3 landing crouch", "proper for landing; placeholder when standing in for a hold"),
       "JUMP(arc)": ("MSHvSF 1.0 jump (lifted arc)", "proper"), "JUMP": ("MSHvSF 1.0 jump", "proper"), "IDLE": ("MSHvSF 0.0 idle pose (alias)", "placeholder (stand pose standing in)"),
       "HIT_M": ("MSHvSF 14.2 hit reaction", "proper"), "HIT_E": ("MSHvSF 14.5 hit reaction", "proper"), "HIT_H": ("MSHvSF 14.4 heavy-hit tumble", "proper for heavy hits; placeholder for knockdown flight"),
       "GRAB_HOLD": ("MSHvSF 8.3 light punch 2", "placeholder (claw poses standing in for a hold)"), "GRAB_SLAM": ("MSHvSF 8.2 heavy punch", "placeholder (slash standing in for a slam)"),
       "BERSERKER(own)": ("MSHvSF 22.10 (Tornado Claw per owner, not the Barrage)", "placeholder (wrong animation)"), "BERSERKER": ("MSHvSF 22.10 (Tornado Claw)", "placeholder (wrong animation)"), "BERS3": ("flurry poses (alias of the Berserker chain)", "alias"), "BERS3(shared)": ("alias of the Berserker chain", "alias"), "BERS": ("MSHvSF 22.10", "placeholder")}
CAND = {"stand": [(0, 0)], "walk": [(0, 1)], "attack stage 1": [(8, 1), (8, 4)], "attack stage 2": [(8, 1), (8, 4)], "attack stage 3": [(8, 2)], "finisher": [(8, 2), (9, 1)], "lunge": [(9, 1), (10, 1)],
        "leap launch": [(1, 3), (1, 0)], "leap arc": [(1, 0), (1, 6)], "landing": [(1, 3)], "crouch": [(1, 3)], "jump attack": [(18, 0), (19, 1)], "air attack": [(18, 0), (19, 1)],
        "special": [(22, 12), (22, 14), (22, 16)], "grab": [(16, 0), (16, 2), (16, 4)], "lift": [(16, 4), (16, 2)], "slam": [(16, 0), (16, 3)], "hold": [(16, 4), (16, 5)],
        "flinch": [(14, 1), (14, 2), (14, 3)], "reaction": [(14, 1), (14, 2)], "knockdown": [(14, 4), (14, 8), (22, 25)], "ground": [(22, 5), (22, 6)], "getup": [(22, 5), (22, 6), (22, 7)], "KO": [(14, 8), (22, 21)],
        "entrance": [(23, 3), (0, 1)], "short hold": [(0, 0)], "wait": [(0, 0)], "gun": []}


def cands(desc):
    for k, v in CAND.items():
        if k in desc: return v
    return []


rows = []
for a, c in sorted(chains.items()):
    first = c["slots"][0]
    sw, desc = STATE.get(first, ("?", "unlisted slot"))
    ticks = sum(w(rom, r) for r in c["recs"] if w(rom, r) < 255)
    atk = any(rom[r + 9] for r in c["recs"])
    role = role_of.get(a, "?")
    src, status = SRC.get(role, ("?", "?"))
    cd = cands(desc)
    cs = "; ".join("%d.%d (%d of %d frames resident)" % (s, e, ex[(s, e)]["resident"], ex[(s, e)]["records"]) for s, e in cd if (s, e) in ex)
    best = max(((ex[(s, e)]["resident"] / max(1, ex[(s, e)]["records"]), s, e) for s, e in cd if (s, e) in ex), default=None)
    rows.append(dict(state=sw, what=desc, slots=",".join(c["slots"][:6]) + ("..." if len(c["slots"]) > 6 else ""), schaefer_frames=len(c["recs"]), schaefer_ticks=ticks, attack_box="yes" if atk else "",
                     wolverine_source=src, status=status, role=role, mshvsf_candidates=cs, best_candidate_resident="yes" if best and best[0] >= 0.99 else ("part" if best and best[0] > 0 else "no") if cd else ""))
with open(outp + ".csv", "w", newline="", encoding="utf-8") as fh:
    wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
order = {"proper": 0}
gaps = [r for r in rows if r["status"].startswith(("placeholder", "alias")) or r["status"] == "?"]
with open(outp + ".md", "w", encoding="utf-8") as fh:
    fh.write("# What a character on Schaefer's state machine needs: Wolverine's baseline (offline, ROM-derived, local)\n\n")
    fh.write("%d chains of Schaefer's index tables (T1 states 02xxxx, T0 entrance, T2 hit/knockdown/getup/KO, T3 gun aim); Wolverine's status counts: %s.\n\n" % (len(rows), ", ".join("%s %d" % (k, sum(1 for r in rows if r["status"].startswith(k))) for k in ("proper", "placeholder", "alias"))))
    fh.write("| State | What | Slots | Schaefer frames / ticks | Wolverine source | Status | Best MSHvSF candidates (resident frames) |\n|---|---|---|---|---|---|---|\n")
    for r in rows:
        fh.write("| %s | %s | %s | %d / %d%s | %s | %s | %s |\n" % (r["state"], r["what"], r["slots"], r["schaefer_frames"], r["schaefer_ticks"], " (attack box)" if r["attack_box"] else "", r["wolverine_source"], r["status"], r["mshvsf_candidates"] or "-"))
    fh.write("\n## Gaps (what he needs)\n\n")
    for r in gaps:
        if r["role"] in ("BERS3", "BERS3(shared)"): continue
        fh.write("- **%s %s** (%s): %s; status: %s. Candidates: %s\n" % (r["state"], r["what"], r["slots"], r["wolverine_source"], r["status"], r["mshvsf_candidates"] or "none listed"))
H = 70 + 20 * len(rows)
img = Image.new("RGB", (1750, H), (40, 40, 48))
d = ImageDraw.Draw(img)
d.text((8, 8), "Wolverine baseline: Schaefer's state-machine chains and Wolverine's current source (green proper, amber placeholder, grey alias). Gaps = what he needs. Candidates from the MSHvSF catalog.", fill=(255, 255, 255))
hdr = [("state", 8), ("what", 90), ("frames/ticks", 400), ("Wolverine source", 480), ("status", 790), ("MSHvSF candidates (resident)", 1130)]
for h, x in hdr: d.text((x, 34), h, fill=(160, 200, 255))
for i, r in enumerate(rows):
    y = 54 + 20 * i
    colr = (120, 255, 120) if r["status"].startswith("proper") and "placeholder" not in r["status"] else (255, 200, 90) if r["status"].startswith("placeholder") or "placeholder" in r["status"] else (170, 170, 180)
    d.text((8, y), r["state"], fill=(255, 255, 255)); d.text((90, y), r["what"][:48], fill=(255, 255, 255)); d.text((400, y), "%d / %d%s" % (r["schaefer_frames"], r["schaefer_ticks"], "*" if r["attack_box"] else ""), fill=(255, 255, 255))
    d.text((480, y), r["wolverine_source"][:52], fill=colr); d.text((790, y), r["status"][:62], fill=colr); d.text((1130, y), (r["mshvsf_candidates"] or "-")[:92], fill=(200, 200, 210))
img.save(outp + ".png")
print("rows", len(rows), "gaps", len(gaps))
