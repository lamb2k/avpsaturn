#!/usr/bin/env python
"""Sprite tile keys of the player characters' poses, for every round file (saturn/rt/build.py reads WORK/pose_keys.txt).
usage: pose_keys.py WORK FUZZDIR [FUZZDIR...]   each FUZZDIR is an output of tools/rounds_fuzz.py (fuzz_pal.txt lines "palette key", sNN.txt per stage word).
Takes palettes 0 and 1 (player 1 and 2) of every run, unions them and writes the keys as hex, one a line.
Also writes WORK/fuzz_stage_keys/stageXX.txt: every sprite key (all palettes) the fuzz runs looked up in that stage word, which build.py adds to that
stage's files unranked (dropped first when a stage is short of room). ROM-derived: WORK only."""
import pathlib, sys

work = pathlib.Path(sys.argv[1])
keys = set()
stage = {}
for d in sys.argv[2:]:
    for l in open(pathlib.Path(d) / "fuzz_pal.txt"):
        p, k = l.split()
        if int(p) in (0, 1):
            keys.add(int(k, 16))
    for f in pathlib.Path(d).glob("s[0-9a-f][0-9a-f].txt"):
        if f.stem == "s00":
            continue
        for l in open(f):
            p = l.split()
            if len(p) == 2 and p[0] == "0":
                stage.setdefault(f.stem[1:], set()).add(int(p[1], 16))
keys.discard(0)
(work / "pose_keys.txt").write_text("".join(f"{k:x}\n" for k in sorted(keys)))
(work / "fuzz_stage_keys").mkdir(exist_ok=True)
for n, ks in stage.items():
    ks.discard(0)
    (work / "fuzz_stage_keys" / f"stage{n}.txt").write_text("".join(f"{k:x}\n" for k in sorted(ks)))
print(len(keys), "pose keys ->", work / "pose_keys.txt", "; stage sets", {n: len(k) for n, k in sorted(stage.items())})
