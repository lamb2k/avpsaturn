#!/usr/bin/env python
"""Lane sprite-store: offline replay of build.py's packer for the arcade stage files: tiles held, keys dropped and the cart room left (KB) per file.

usage: stage_headroom.py WORK [STAGES]   STAGES: comma separated hex stage words (default 02,04,06,0c,0e,1c,1e,20,24,26)
Environment as for the build: KERNEL_CFLAGS (SAT_TILE_ROWTRIM), PACK_TAIL_FILL, CHAR_FUZZ_KEYS, CHAR_FUZZ_KEY_STAGES, STAGE_WINDOW, STAGE_WINDOW_PAD, CHAR_FUZZ, GFX_BIN.
Replays the file with the keys the build asks for (tools/wolverine/fit.py's key assembly: route and fuzz keys, screen keys, text fonts; the home caption and edge keys of build.py are
left out, a few hundred bytes), then reports, for the base file of each stage, the plan: tiles in main and spill, dropped keys, and the headroom, the bytes the file's main part
and every free ROM stretch could still take (the average record is about 80 bytes). Replay only: the build's own log is the measurement. ROM-derived input: WORK and GFX_BIN."""
import json
import os
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools" / "wolverine"))
sys.path.insert(0, str(REPO / "tools"))
import fit
import rounds_pack


def main(argv):
    work = pathlib.Path(argv[1])
    stages = [int(x, 16) for x in (argv[2] if len(argv) > 2 else "02,04,06,0c,0e,1c,1e,20,24,26").split(",")]
    environ = os.environ
    import re
    m = re.search(r"-DSAT_TILE_ROWTRIM(?:=(\d))?(?!\w)", environ.get("KERNEL_CFLAGS", ""))
    fit.ROWTRIM = int(m.group(1) or 1) if m else 0
    config = fit.settings(environ)
    rounds, ends, screens, rank = fit.load(work, environ)
    window = None
    if environ.get("STAGE_WINDOW", "0") == "1":
        import stage_window
        sw = stage_window.load(work)
        pad = int(environ.get("STAGE_WINDOW_PAD", "2"))
        print("stage window:", stage_window.apply(rounds, sw, extra=pad), flush=True)
        window = stage_window.windows(sw, pad)
    if environ.get("CHAR_FUZZ", "1") != "0":
        import char_fuzz
        data = char_fuzz.load(work)
        if data:
            print("char fuzz:", char_fuzz.augment(rounds, data, keys=environ.get("CHAR_FUZZ_KEYS", "0") == "1", pages=environ.get("CHAR_FUZZ_PAGES", "1") == "1",
                                                  key_stages={int(x, 16) for x in environ.get("CHAR_FUZZ_KEY_STAGES", "0e,1c,1e,24").split(",") if x} or None, window=window), flush=True)
    room = ends[-1][0] - fit.CART_PACK
    free = fit.free_runs(rounds, ends, **config)
    raw = pathlib.Path(environ.get("GFX_BIN", "E:/AvP/learning/lane-satgfx/gfx.bin")).read_bytes()
    rows = []
    for s in stages:
        f = next(x for x in rounds["files"] if x["stages"][0] == s and "mask" not in x)
        runs = free(f)
        p, dropped = fit.run(raw, f, f["keys"], room, free, rank.get(f["name"], {}), screens)
        row = dict(file=f["name"], keep_pages=len(f["keep_pages"]), free_runs=len(runs), free_kb=sum(r[1] for r in runs) // 1024, dropped=len(dropped))
        if p is not None and p.get("rowtrim"):
            fixed = rounds_pack.HEAD + 8 + sum(len(k) for k in p["key"]) + sum((len(p["tile"][i]) + 3) & ~3 for i in (1, 2, 3)) + (((p["n_tiles"] + 1023) >> 10) << 2) + ((p["n_tiles"] * 2 + 3) & ~3) + 16
            cap = room - fixed - 4 - 8 * len(runs) + sum(r[1] if len(r) > 2 and r[2] else r[1] & -rounds_pack.SEC for r in runs)
            row.update(tiles=p["n_tiles"], in_main=p["inmain"], spill_tiles=p["n_tiles"] - p["inmain"], bytes=p["pos"][-1], headroom_kb=round((cap - p["pos"][-1]) / 1024, 1))
        rows.append(row)
        print(json.dumps(row), flush=True)
    return rows


if __name__ == "__main__":
    main(sys.argv)
