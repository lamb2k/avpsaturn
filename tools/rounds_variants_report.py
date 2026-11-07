#!/usr/bin/env python
"""Lane packs: blank sprite keys and lost sound plays per real route, with the one-for-all file and with the file the kernel picks; every variant's drops; what the kernel's selector picks on each golden.
usage: rounds_variants_report.py WORK ROUTE=MASK=CENSUS[=GOLDEN] ...   CENSUS: tools/golden_census.py directory; GOLDEN: LEARN_DELTA probe.tsv, replays saturn/rt/kernel.c round_check. Output holds counts only."""
import collections, glob, json, pathlib, struct, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from rounds_variants import _route
W = pathlib.Path(sys.argv[1])
R = json.loads((W / "rounds.json").read_text())
ST = json.loads((W / "round_stats.json").read_text())
SD = json.loads((W / "sound_rank.json").read_text())["dropped"]
names = [f["name"] for f in R["files"]]
vf, masks = R["variant_file"], R["variant_masks"]
col = lambda m: masks.index(m) + 1 if m in masks else 0


def selector(path):
    """round_check over a golden, one call per dump. Returns [(stage, chars at load)]."""
    ram, out = bytearray(0x10000), []
    loaded, settled, chars, t = 0, None, 0, 0
    with open(path, "rb") as f:
        while True:
            h = f.read(76)
            if len(h) < 76:
                return out
            t += 1
            for _ in range(struct.unpack_from(">I", h, 72)[0]):
                b, w = struct.unpack(">HH", f.read(4))
                d = f.read(w * 4)
                if b < 0x4000:
                    ram[b * 4:b * 4 + w * 4] = d
            s = 0 if ram[0x81b0] or ram[0x8001] != 2 else ram[0x81e9]
            row = s if str(s) in R["stage_file"] else 0
            if row:
                chars |= ram[0x81cc] & 15
            if row == loaded:
                settled = None
                continue
            if settled is None:
                settled = t
            if t - settled < 12:
                continue
            settled = None
            if not row:
                chars = 0
            loaded = row
            out.append((row, chars))


tot = collections.Counter()
for a in sys.argv[2:]:
    p = a.split("=")
    name, mask, c = p[0], int(p[1]), _route(p[2])
    if len(p) > 3:
        sel = selector(p[3])
        wrong = [(hex(s), m) for s, m in sel if s and m != mask]
        print(name, "selector loads", len(sel), "wrong", wrong)
    row = {"before": collections.Counter(), "after": collections.Counter()}
    by = {}
    for s, v in sorted(c.items()):
        if str(s) not in vf:
            continue
        for tag, fi in (("before", vf[str(s)][0]), ("after", vf[str(s)][col(mask)])):
            n = names[fi]
            d = set(ST[n]["dropped"])
            lost = {int(x, 16) for x in SD[n]}
            bk = len(d & set(v[0]))
            bp = sum(u for x, u in v[1].items() if x in lost)
            row[tag]["keys"] += bk; row[tag]["plays"] += bp
            by.setdefault(hex(s), []).extend([bk, bp])
    print(name, "before keys", row["before"]["keys"], "plays", row["before"]["plays"], "| after keys", row["after"]["keys"], "plays", row["after"]["plays"])
    print("  stage [before keys, plays, after keys, plays] where not all 0:", {k: x for k, x in by.items() if any(x)})
print("file drops by variant (sum over stages: keys, sound cmds; worst stage keys)")
agg = collections.defaultdict(lambda: [0, 0, 0, ""])
for n in names[1:]:
    t = n.split("_m")[1] if "_m" in n else "all"
    a = agg[t]; a[0] += ST[n]["dropped_keys"]; a[1] += len(SD[n])
    if ST[n]["dropped_keys"] > a[2]:
        a[2], a[3] = ST[n]["dropped_keys"], n
for t, a in agg.items():
    print(" ", t, a)
sz = [v["file"] for v in ST.values()]
print("files", len(sz), "MB", sum(sz) >> 20, "largest", max(sz), "largest restore", max(v["restore"] for v in ST.values()), "most regions", max(v["spill_runs"] + v["restore_runs"] for v in ST.values()))
print("iso", (W / "sat.iso").stat().st_size)
