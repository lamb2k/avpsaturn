#!/usr/bin/env python
"""Lane sprite-store: how many sprite keys do new fuzz runs look up that the stage files do not hold?

usage: fuzz_unseen.py WORK GFX_BIN BIT=DIR[,DIR...] [BIT=DIR...] [--stages 0e,1c,1e,24] [--out report.json]
  WORK: a build work directory (rounds.json, char_fuzz.json, screen_keys.txt). GFX_BIN: the arcade tile ROM as tools/satgfx_pack.py reads it.
  BIT: the game's character bit (1 Warrior, 2 Schaefer, 4 Hunter, 8 Linn); DIR: a fuzz run (tools/rounds_fuzz.py: sNN.txt, fuzz_pal.txt), in the order they are added.
A key is held when the stage's route census (rounds.json), any character's fuzz keys of that stage or body keys in char_fuzz.json, or the screen keys have it (what
a CHAR_FUZZ_KEYS=1 stage file asks for before the packer drops anything). Per character and stage the runs are replayed in order: the keys of run k that the data
and runs 0..k-1 lack (new), and of those the ones whose tile has a visible pen (blank tiles draw nothing). The last runs of a list are the held-out check
of what the earlier ones cover. ROM-derived input: WORK and GFX_BIN only."""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import char_fuzz
import satgfx_pack


def held(work, stage):
    work = pathlib.Path(work)
    rounds = json.loads((work / "rounds.json").read_text())
    f = next(x for x in rounds["files"] if x["stages"][0] == int(stage, 16) and "mask" not in x)
    keys = set(f["keys"][0])
    cf = json.loads((work / "char_fuzz.json").read_text())
    for c in cf["chars"].values():
        keys |= set(c["stage_keys"].get(stage, ())) | set(c["body_keys"])
    sk = work / "screen_keys.txt"
    for line in sk.read_text().splitlines() if sk.exists() else []:
        if line.strip() and line.split()[0] == "0":
            keys.add(int(line.split()[1], 16))
    keys.discard(0)
    return keys


def main(argv):
    out_path, stages, spec = None, ["0e", "1c", "1e", "24"], {}
    args = list(argv[3:])
    while args:
        a = args.pop(0)
        if a == "--out":
            out_path = args.pop(0)
        elif a == "--stages":
            stages = args.pop(0).split(",")
        else:
            bit, dirs = a.split("=", 1)
            spec.setdefault(int(bit), []).extend(dirs.split(","))
    work, raw = argv[1], pathlib.Path(argv[2]).read_bytes()
    vis = {}
    visible = lambda k: vis.setdefault(k, satgfx_pack.payload(raw, 0, k)[1])
    base = {st: held(work, st) for st in stages}
    report = {}
    for bit, dirs in spec.items():
        for st in stages:
            have, rows = set(base[st]), []
            for d in dirs:
                keys, pal, pages = char_fuzz.read_run(d)
                got = keys.get(st, set())
                new = got - have
                rows.append(dict(run=pathlib.Path(d).name, asked=len(got), new=len(new), new_visible=sum(1 for k in new if visible(k)), keys=sorted(new)))
                have |= got
            report["%d/%s" % (bit, st)] = rows
            print("char %d stage %s: %s" % (bit, st, "  ".join("%s %d new, %d visible" % (r["run"], r["new"], r["new_visible"]) for r in rows)), flush=True)
    if out_path:
        pathlib.Path(out_path).write_text(json.dumps(report))
    return report


if __name__ == "__main__":
    main(sys.argv)
