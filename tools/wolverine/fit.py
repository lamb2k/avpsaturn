#!/usr/bin/env python
"""Lane avp-wolverine: real packer fit of Wolverine stage files against the Schaefer files they replace.
Same planning as saturn/rt/build.py round_files (free ROM stretches, shared pages, screen keys, key rank, rounds_pack.fit),
run on a finished build's WORK directory, without writing files.
Wolverine file = Schaefer file's keys - Schaefer's own keys for that stage + Wolverine's remapped keys (tools/wolverine/assets.py).
usage: fit.py WORK ASSETS_DIR [STAGE_FILTER]   prints a table and writes ASSETS_DIR/fit.json. ROM-derived inputs stay under E:/AvP/learning."""
import json, pathlib, re, sys
REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
import rounds_pack

SCH = 2                       # ff81cc mask bit of the slot Wolverine takes (owner 11-08: Schaefer)
OTHERS = (1, 4, 8)
PAIRS = {3: "m3", 6: "m6", 10: "ma"}
SPEC = "E:/AvP/learning/lane-packs/spec.json"
CART_PACK, SHARED_MIN, MIN_RUN = 0x02654000, 10, 1


def load(work):
    R = json.loads((work / "rounds.json").read_text())
    ends = json.loads((work / "round_code_ends.json").read_text())
    rom = (work / "rom_final.bin").read_bytes()
    sk = [set(), set(), set(), set()]
    for l in open(work / "screen_keys.txt"):
        if l.strip():
            sk[int(l.split()[0])].add(int(l.split()[1], 16))
    sk[0].discard(0)
    rank = json.loads((work / "key_rank.json").read_text())
    return R, ends, rom, sk, rank


def free_runs(R, ends):
    page = R["page"]
    code = bytearray(0x200000 // page)
    for at, end in ends[:-1]:
        for q in range((at - 0x02400000) // page, (end - 0x02400000 + page - 1) // page):
            code[q] = 1
    base = [f for f in R["files"] if re.fullmatch(r"stage[0-9a-f]{2}", f["name"])]
    seen = {}
    for f in base:
        for q in set(f["keep_pages"]):
            seen[q] = seen.get(q, 0) + 1
    shared = {q for q, c in seen.items() if c >= SHARED_MIN}

    def free(f):
        keep = set(f["keep_pages"]) | shared
        out, st = [], None
        for q in range(0x200000 // page + 1):
            ok = q < 0x200000 // page and q not in keep and not code[q]
            if ok and st is None:
                st = q
            if not ok and st is not None:
                if q - st >= MIN_RUN:
                    out.append([st * page, (q - st) * page])
                st = None
        out.sort(key=lambda r: -r[1])
        return out
    return free


def run(raw, f, keys, room, free, rank, sk):
    keys = [set(k) | e for k, e in zip(keys, sk)]
    frank = {int(x): v for x, v in rank.items()}
    frank.update({k: 1 << 40 for k in sk[0]})
    p, dropped = rounds_pack.fit(raw, keys, room, free(f), frank)
    return p, dropped


def main():
    work, adir = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    filt = sys.argv[3] if len(sys.argv) > 3 else ""
    R, ends, rom, sk, rank = load(work)
    room = ends[-1][0] - CART_PACK
    free = free_runs(R, ends)
    A = json.loads((adir / "remap.json").read_text())
    raw = (adir / "gfx_wolverine.bin").read_bytes()    # AvP graphics with Wolverine's tiles written at his remapped keys
    stage_keys = {int(s, 16): set(v) for s, v in A["stage_keys"].items()} if "stage_keys" in A else None
    wkeys_all = set(A["keys"])
    files = {f["name"]: f for f in R["files"]}
    import rounds_variants
    sch_own = rounds_variants.Data(SPEC).own[SCH]
    rows, out = [], {}
    for name, f in files.items():
        m = re.fullmatch(r"stage([0-9a-f]{2})_m([0-9a-f])", name)
        if not m or int(m.group(2), 16) & SCH == 0 or not name.startswith("stage" + filt):
            continue
        st, mask = m.group(1), int(m.group(2), 16)
        own = set(f["keys"][0]) & sch_own   # keys only Schaefer uses in the whole game (rounds_variants own set)
        wk = stage_keys.get(int(st, 16), wkeys_all) if stage_keys else wkeys_all
        p0, d0 = run(raw, f, f["keys"], room, free, rank.get(name, {}), sk)
        k1 = [set(f["keys"][0]) - own | wk] + [set(k) for k in f["keys"][1:]]
        r1 = dict(rank.get(name, {}))
        r1.update({str(k): 1 << 39 for k in wk})   # his frames rank as the playing character's own route
        p1, d1 = run(raw, f, k1, room, free, r1, sk)
        wd = len(set(d1) & wk)
        row = dict(file=name, schaefer_own=len(own), wolverine=len(wk), sch_drop=len(d0), wolv_drop=len(d1), wolv_own_dropped=wd,
                   sch_tiles=p0["inmain"] + sum(x[2] for x in p0["segs"]), wolv_tiles=p1["inmain"] + sum(x[2] for x in p1["segs"]),
                   gate=len(d1) <= len(d0) and wd == 0)
        rows.append(row)
        print(json.dumps(row), flush=True)
    (adir / f"fit{filt}.json").write_text(json.dumps(rows, indent=0))
    print("gate", all(r["gate"] for r in rows), "fail", [r["file"] for r in rows if not r["gate"]])


if __name__ == "__main__":
    main()
