#!/usr/bin/env python
"""Lane fit: write the ROUNDS_SWAP list for the host check from WORK/rounds.json: per stage word, every ROM page its file does not keep. usage: rounds_hostcheck.py WORK OUT"""
import json, pathlib, sys
R = json.loads((pathlib.Path(sys.argv[1]) / "rounds.json").read_text())
P = R["page"]
assert P == 0x400   # host_kernel.c SW_PAGE
with open(sys.argv[2], "w", newline="\n") as f:
    for fl in R["files"]:
        keep = set(fl["keep_pages"])
        junk = [p for p in range(0x200000 // P) if p not in keep]
        f.write(f"{fl['stages'][0]} {len(junk)} " + " ".join(map(str, junk)) + "\n")
