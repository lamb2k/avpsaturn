"""Bonus characters: guest stage file variants, added to the build's ROUNDS in memory (saturn/rt/build.py, env GUEST_ASSETS).
Wolverine (guest 0) takes Schaefer's slot, ff81cc bit 2: for every stage word and every variant whose mask holds bit 2, a new file is the
Schaefer variant's candidates minus Schaefer's whole-game own keys plus Wolverine's keys (tools/wolverine/assets.py remap.json "stage_keys"),
with the same sound and kept pages. ROUNDS["guest_files"] then maps guest -> stage word -> file per variant (0 = the arcade's file).
The graphics region the packer reads becomes ASSETS/gfx_wolverine.bin: the AvP region with his tiles at sprite keys no AvP file uses,
so every AvP file packs the same bytes as before.
Select screen and HUD art (tools/wolverine/hud_art.py, optional `hud`): the guest's stage files read the region with his HUD portrait and
name written at Schaefer's tile codes, and a front end file of his own (the arcade's front file, the select picture, plate and ranking
icon written the same way) is guest_files["0"]["0"], row 0, variant 0. Without `hud` nothing here changes.
Optional `s1_keys` (SAT_WV_DIALOG): scroll 1 keys added to every guest stage file, for the guest's story box wording."""
import os, pathlib, sys

SPEC = "E:/AvP/learning/lane-packs/spec.json"
SLOT = 2


def extend(R, assets, hud=None, s1_keys=(), work=None):
    import json
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
    import rounds_variants
    assets = pathlib.Path(assets)
    A = json.loads((assets / "remap.json").read_text())
    own = rounds_variants.Data(os.environ.get("GUEST_SPEC", SPEC)).own[SLOT]
    remap = set(A["keys"])
    masks = R["variant_masks"]
    files = R["files"]
    table, made = {}, {}
    wv_snd, wv_rank = None, {}
    if work is not None:   # Wolverine's own sounds (tools/wolverine/wv_sound.py, wv_audio.py): GUEST_ASSETS/wv_sound or env WV_SOUND; without them the packs stay the arcade's
        import wv_audio
        sdir = pathlib.Path(os.environ.get("WV_SOUND") or assets / "wv_sound")
        if (sdir / "wv_sound.json").exists():
            wv_snd = wv_audio.load_assets(sdir)
            rk = pathlib.Path(work) / "sound_rank.json"
            wv_rank = json.loads(rk.read_text())["uses"] if rk.exists() else {}
            wv_stats = {}
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
            f["keys"] = [sorted(set(base["keys"][0]) - (own - set(base.get("other_keys", ()))) - remap | wk)] + [list(k) for k in base["keys"][1:]]   # remap: a key of his art holds his tile in the guest files, whatever the arcade file asks for there (fuzz keys, tools/char_fuzz.py)
            if s1_keys:   # scroll 1 keys the guest's own story box wording draws (tools/wolverine/dialog.py, SAT_WV_DIALOG)
                f["keys"][1] = sorted(set(f["keys"][1]) | set(s1_keys))
            f["audio_from"] = row[vi]
            f["rank_from"] = base["name"]
            f["guest_keys"] = sorted(wk)
            f["guest"] = 0
            if hud:
                f["gfx"] = str(hud["stage_gfx"])
            out[vi] = made[row[vi]] = len(files)
            if wv_snd is not None:
                uses = {int(k, 16): n for k, n in wv_rank.get(f"{st:02x}", {}).items()}
                pack, rep = wv_audio.build((pathlib.Path(work) / "audio" / f"r{row[vi]:03d}.bin").read_bytes(), wv_snd, uses, "stage")
                (pathlib.Path(work) / "audio" / f"r{len(files):03d}.bin").write_bytes(pack)
                f["audio_from"] = len(files)
                wv_stats[f["name"]] = rep
            files.append(f)
        table[word] = out
    if hud:
        assert files[0]["name"] == "front" and "0" not in table
        front = dict(files[0], name=files[0]["name"] + "_wv", audio_from=0, rank_from=files[0]["name"], gfx=str(hud["front_gfx"]), guest=0)
        table["0"] = [len(files)] + [0] * len(masks)   # row 0 is the front end: its file, variant 0 (no characters)
        if wv_snd is not None:
            pack, rep = wv_audio.build((pathlib.Path(work) / "audio" / "r000.bin").read_bytes(), wv_snd, {}, "front")
            (pathlib.Path(work) / "audio" / f"r{len(files):03d}.bin").write_bytes(pack)
            front["audio_from"] = len(files)
            wv_stats[front["name"]] = rep
        files.append(front)
    R["guest_files"] = {"0": table}
    if wv_snd is not None:
        (pathlib.Path(work) / "wv_sound_report.json").write_text(json.dumps(wv_stats, indent=0, default=str))
    os.environ["GFX_BIN"] = str(assets / "gfx_wolverine.bin")
    return R
