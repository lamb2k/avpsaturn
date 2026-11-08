"""Bonus characters: guest stage file variants, added to the build's ROUNDS in memory (saturn/rt/build.py, env GUEST_ASSETS).
Wolverine (guest 0) takes Schaefer's slot, ff81cc bit 2: for every stage word and every variant whose mask holds bit 2, a new file is the
Schaefer variant's candidates minus Schaefer's whole-game own keys plus Wolverine's keys (tools/wolverine/assets.py remap.json "stage_keys"),
with the same sound and kept pages. ROUNDS["guest_files"] then maps guest -> stage word -> file per variant (0 = the arcade's file).
The graphics region the packer reads becomes ASSETS/gfx_wolverine.bin: the AvP region with his tiles at sprite keys no AvP file uses,
so every AvP file packs the same bytes as before."""
import os, pathlib, sys

SPEC = "E:/AvP/learning/lane-packs/spec.json"
SLOT = 2


def extend(R, assets):
    import json
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
    import rounds_variants
    assets = pathlib.Path(assets)
    A = json.loads((assets / "remap.json").read_text())
    own = rounds_variants.Data(os.environ.get("GUEST_SPEC", SPEC)).own[SLOT]
    masks = R["variant_masks"]
    files = R["files"]
    table, made = {}, {}
    for word, row in R["variant_file"].items():
        out = [0] * (len(masks) + 1)
        for vi, m in enumerate(masks, start=1):
            if not m & SLOT:
                continue
            if row[vi] in made:
                out[vi] = made[row[vi]]
                continue
            base = files[row[vi]]
            st = base["stages"][0]
            wk = set(A["stage_keys"].get(f"{st:02x}", A["keys"]))
            f = dict(base)
            f["name"] = base["name"] + "_wv"
            f["keys"] = [sorted(set(base["keys"][0]) - own | wk)] + [list(k) for k in base["keys"][1:]]
            f["audio_from"] = row[vi]
            f["rank_from"] = base["name"]
            f["guest_keys"] = sorted(wk)
            f["guest"] = 0
            out[vi] = made[row[vi]] = len(files)
            files.append(f)
        table[word] = out
    R["guest_files"] = {"0": table}
    os.environ["GFX_BIN"] = str(assets / "gfx_wolverine.bin")
    return R
