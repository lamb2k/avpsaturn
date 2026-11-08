# Lane all: pages the lifted code read (readmap.json from tools/diag_readmap.py, -DSAT_READMAP build) that the loaded stage file does not keep.
# usage: readmiss.py WORK RUN [RUN...]   Prints per file: pages read, read but not kept. Counts and page numbers only.
import json, sys, pathlib
R = json.load(open(pathlib.Path(sys.argv[1]) / "rounds.json"))
miss = {}
OUT = None
args = sys.argv[2:]
if "--out" in args:
    i = args.index("--out"); OUT = args[i + 1]; del args[i:i + 2]
for run in args:
    p = pathlib.Path(run) / "readmap.json"
    if not p.exists():
        continue
    for k, pages in json.load(open(p)).items():
        i = int(k)
        if i >= len(R["files"]):
            continue
        f = R["files"][i]
        m = sorted(set(pages) - set(f["keep_pages"]))
        print(run[-8:], f["name"], "read", len(pages), "not kept", len(m), m[:40])
        miss.setdefault(f["stages"][0], set()).update(m)
print({hex(s): sorted(v) for s, v in miss.items() if v})
if OUT:
    old = json.load(open(OUT)) if pathlib.Path(OUT).exists() else {}
    for s, v in miss.items():
        old[hex(s)] = sorted(set(old.get(hex(s), [])) | v)
    json.dump(old, open(OUT, "w"))
