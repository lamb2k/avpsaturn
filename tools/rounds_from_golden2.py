#!/usr/bin/env python
"""Lane rounds: turn lane golden2's per-section census into one walk directory for tools/rounds_census.py. usage: rounds_from_golden2.py CENSUS OUTDIR. ROM-derived: E:/AvP/learning only."""
import glob, pathlib, sys
C, O = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]); O.mkdir(parents=True, exist_ok=True)
rows = {}
for f in glob.glob(str(C / "sections/*.tiles.txt")):
    rows.setdefault(int(pathlib.Path(f).name[:4], 16), []).append(pathlib.Path(f).name.split(".")[0])
for s, names in rows.items():
    out = []
    for n in names:
        p = C / "sections" / n
        out += [l.strip() for l in open(f"{p}.tiles.txt")]
        for l in open(f"{p}.sounds.txt"):
            out.append("m %x" % (int(l.split()[0], 16) & 0xffff))
        for tag, ext in (("r", "reg"), ("o", "pcrel"), ("o", "fetch")):
            for l in open(f"{p}.{ext}.txt"):
                a, b = (int(x, 16) for x in l.split())
                out += [f"{tag} {x:x}" for x in range(a & ~1, b, 2)]
    (O / f"s{s & 0xff:02x}.txt").write_text("\n".join(out) + "\n")
print(sorted(hex(s) for s in rows))
