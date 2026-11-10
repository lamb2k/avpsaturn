#!/usr/bin/env python
"""Host check: every round file's tile pack holds the whole caption font (scroll 1 codes 0x1260-0x131f and the signs 0x1246-9, 0x1256-9, both column halves) in its scroll 1 key table, as saturn/rt/build.py
CAPTION_KEYS adds for home builds. A glyph missing from a stage's file draws blank in that stage's story captions.
usage: check_caption_keys.py WORK   (reads WORK/rounds/R*.BIN, the files build.py writes)   exit 1 on any file missing a key."""
import glob, pathlib, struct, sys

work = pathlib.Path(sys.argv[1])
want = {(c << 1) | h for c in list(range(0x1260, 0x1320)) + [0x1246, 0x1247, 0x1248, 0x1249, 0x1256, 0x1257, 0x1258, 0x1259] for h in (0, 1)}
bad = 0
files = sorted(glob.glob(str(work / "rounds" / "R*.BIN")))
if not files:
    raise SystemExit("no round files under %s/rounds" % work)
for fn in files:
    b = open(fn, "rb").read()
    i = b.find(b"SGP1")
    if i < 0:
        i = b.find(b"SGP2")
    if i < 0:
        i = b.find(b"SGP3")
    h = struct.unpack_from(">13I", b, i)
    n, ko = h[4], h[5]
    have = {struct.unpack_from(">I", b, i + ko + j * 4)[0] >> 14 for j in range(n)}
    miss = want - have
    if miss:
        bad += 1
        print(pathlib.Path(fn).name, "missing", len(miss), "keys, first", hex(min(miss)))
print("files", len(files), "short", bad)
sys.exit(1 if bad else 0)
