#!/usr/bin/env python
"""Check Wolverine's GUEST_ASSETS pack plan against the Schaefer files it replaces.

Uses a finished build's layout and the real rounds_pack.fit implementation. No
round files are written. All variants containing Schaefer must be checked for
every requested stage; an empty or incomplete selection is an error.

usage: fit.py WORK ASSETS_DIR [STAGES]   (FIT_DIALOG_KEYS=gen/guest_dialog_keys.json adds the SAT_WV_DIALOG scroll 1 keys to his files)   STAGES is comma-separated hex, e.g. 06,1c,1e.
With no STAGES, check every non-front-end stage in variant_file. Writes
ASSETS_DIR/fit[STAGES].json. Exit 0: all pass; 1: fit fails; 2: missing/bad inputs.
Honours GUEST_SPEC, SCREEN_KEYS_REQUIRED, ROUND_SHARED_MIN, ROUND_MIN_RUN and
ARENA_KEEP as build.py does. FIT_GFX_GUEST and FIT_GFX_FRONT (tools/wolverine/hud_art.py's gfx_hud_stage.bin and
gfx_hud_front.bin) pack the guest's files from the regions with his select screen and HUD art, and check his front file too. This checks full pack generation, not the old
KEEP_ROUND_FILES partial-build shortcut. Private inputs stay outside Git.
"""
import json
import os
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
SCH = 2
SPEC = "E:/AvP/learning/lane-packs/spec.json"
ROM_BASE, ROM_BYTES, CART_PACK, CART_END = 0x02400000, 0x200000, 0x02654000, 0x02800000


def parse_stages(text):
    if not text:
        return None
    stages = set()
    for part in text.split(","):
        if not re.fullmatch(r"(?:0[xX])?[0-9a-fA-F]{1,2}", part.strip()):
            raise ValueError("STAGES must be comma-separated hexadecimal stage words")
        word = int(part, 16)
        if not word:
            raise ValueError("stage 00 is the front end, not a Wolverine stage file")
        stages.add(word)
    return sorted(stages)


def settings(environ):
    shared = int(environ.get("ROUND_SHARED_MIN", "10"))
    minimum = int(environ.get("ROUND_MIN_RUN", "1"))
    if shared < 0 or minimum < 0:
        raise ValueError("ROUND_SHARED_MIN and ROUND_MIN_RUN must be nonnegative")
    return dict(shared_min=shared, min_run=minimum,
                arena_keep=environ.get("ARENA_KEEP") or None,
                tail_fill=environ.get("PACK_TAIL_FILL", "0") == "1")


ROWTRIM = False   # main() sets it from KERNEL_CFLAGS: SAT_TILE_ROWTRIM packs SGP2 (build.py)
STORY_PAGES = set()   # load() fills it: the story caption ROM pages every file keeps (tools/story_text_pages.py)
FONT_KEYS = set()   # load() fills it: every text font glyph (tools/font_glyph_keys.py), kept in every file as build.py does


def load(work, environ):
    global FONT_KEYS, STORY_PAGES
    rounds = json.loads((work / "rounds.json").read_text())
    ends = json.loads((work / "round_code_ends.json").read_text())
    if not ends or not CART_PACK <= ends[-1][0] <= CART_END or ends[-1][1] != 0:
        raise ValueError("round_code_ends.json has no valid cart-pack boundary")
    screens = [set() for _ in range(4)]
    screen_file = work / "screen_keys.txt"
    for line in screen_file.read_text().splitlines() if screen_file.exists() else []:
        if line.strip():
            section, key = line.split()
            section = int(section)
            if not 0 <= section < 4:
                raise ValueError("screen key section outside 0..3")
            screens[section].add(int(key, 16))
    screens[0].discard(0)
    sys.path.insert(0, str(REPO / "tools"))
    import system_banner_keys   # the "HURRY UP!" banner and countdown tiles: kept in every stage file, as build.py does
    if (work / "rt.bin").exists() and (work / "op.bin").exists():   # every real work dir has both; a synthetic one (tests) does not
        screens[1] |= system_banner_keys.from_work(work)
        import font_glyph_keys   # the text fonts' glyph tables (both banks, both column parities), every file including the front end
        FONT_KEYS = font_glyph_keys.from_work(work) if environ.get("FONT_KEYS", "1") == "1" else set()
        import story_text_pages   # the story captions' ROM pages stay out of every file's tile spill, as build.py does
        STORY_PAGES = story_text_pages.from_work(work, rounds["page"]) if environ.get("STORY_PAGES", "1") == "1" else set()
    if environ.get("SCREEN_KEYS_REQUIRED", "1") == "1" and not screens[0]:
        raise ValueError("WORK/screen_keys.txt missing or empty (SCREEN_KEYS_REQUIRED=0 to omit)")
    rank_file = work / "key_rank.json"
    rank = json.loads(rank_file.read_text()) if rank_file.exists() else {}
    return rounds, ends, screens, rank


def selected_files(rounds, stages=None):
    """Return every required (stage, variant, mask, base file); fail closed on gaps."""
    masks = rounds.get("variant_masks", [])
    variants = [(i, mask) for i, mask in enumerate(masks, 1) if mask & SCH]
    if not variants or len(set(masks)) != len(masks):
        raise ValueError("no valid Schaefer variants in variant_masks")
    table, files = rounds.get("variant_file", {}), rounds.get("files", [])
    declared = {int(st) for st in table if int(st)}
    declared.update(int(st) for st in rounds.get("stage_file", {}) if int(st))
    declared.update(st for f in files for st in f.get("stages", []) if st)
    wanted = stages if stages is not None else sorted(declared)
    if not wanted:
        raise ValueError("no stages selected")
    selected = []
    for word in wanted:
        row = table.get(str(word))
        if not isinstance(row, list) or len(row) != len(masks) + 1:
            raise ValueError("stage %02x has no complete variant row" % word)
        for variant, mask in variants:
            number = row[variant]
            if not isinstance(number, int) or not 0 <= number < len(files):
                raise ValueError("stage %02x mask %x has no file" % (word, mask))
            base = files[number]
            if base.get("name") == "front" or word not in base.get("stages", []):
                raise ValueError("stage %02x mask %x maps to the wrong stage file" % (word, mask))
            selected.append((word, variant, mask, base))
    return selected


def free_runs(rounds, ends, shared_min=10, min_run=1, arena_keep=None, tail_fill=False):
    """Same code-page, shared-page, and ARENA_KEEP exclusions as round_files()."""
    page = rounds["page"]
    if page <= 0 or ROM_BYTES % page:
        raise ValueError("invalid ROM census page size")
    code = set()
    for at, end in ends[:-1]:
        if not ROM_BASE <= at <= end <= ROM_BASE + ROM_BYTES:
            raise ValueError("cold code range outside the ROM image")
        code.update(range((at - ROM_BASE) // page, (end - ROM_BASE + page - 1) // page))
    base = [f for f in rounds["files"] if re.fullmatch(r"stage[0-9a-f]{2}", f["name"])]
    seen = {}
    for f in base:
        for q in set(f["keep_pages"]):
            seen[q] = seen.get(q, 0) + 1
    shared = {q for q, count in seen.items() if count >= shared_min}
    k02 = set()
    if arena_keep:
        stage02 = next((f for f in base if f["name"] == "stage02"), None)
        if stage02 is None:
            raise ValueError("ARENA_KEEP requires stage02's keep_pages")
        k02 = set(stage02["keep_pages"])
        if arena_keep not in ("1", "all"):
            wanted = set()
            for span in arena_keep.split(","):
                lo, hi = (int(value, 16) for value in span.split("-"))
                if not 0 <= lo < hi <= ROM_BYTES:
                    raise ValueError("ARENA_KEEP range outside the ROM image")
                wanted.update(range(lo // page, (hi + page - 1) // page))
            k02 &= wanted

    def free(f):
        keep = set(f["keep_pages"]) | shared | STORY_PAGES
        if k02 and set(f.get("stages", [])) & {0x0e, 0x1c, 0x1e, 0x24}:
            keep |= k02
        out, start = [], None
        for q in range(ROM_BYTES // page + 1):
            available = q < ROM_BYTES // page and q not in keep and q not in code
            if available and start is None:
                start = q
            if not available and start is not None:
                if q - start >= min_run:
                    # PACK_TAIL_FILL as build.py: a run ending in a kept plain ROM page may use its odd page
                    out.append([start * page, (q - start) * page] + ([True] if tail_fill and q < ROM_BYTES // page and q in keep and q not in code else []))
                start = None
        out.sort(key=lambda item: -item[1])
        return out
    return free


def run(raw, f, keys, room, free, rank, screens, guest_keys=(), fit_fn=None):
    """Apply build priorities before calling the packer; imports stay out of helpers."""
    if fit_fn is None:
        sys.path.insert(0, str(REPO / "tools"))
        import rounds_pack
        fit_fn = rounds_pack.fit
    keys = [set(k) for k in keys]
    keys[1] |= FONT_KEYS
    frank = {int(key): value for key, value in rank.items()}
    if f.get("fuzz_keys") or f.get("body_keys"):   # CHAR_FUZZ_KEYS, as build.py
        import char_fuzz
        char_fuzz.rank(f, frank)
    frank.update({key: 1 << 39 for key in guest_keys})
    if not f["name"].startswith("front"):   # front_wv too
        keys = [k | extra for k, extra in zip(keys, screens)]
        frank.update({key: 1 << 40 for key in screens[0]})
    return fit_fn(raw, keys, room, free(f), frank, **({"rowtrim": ROWTRIM} if ROWTRIM else {}))


def main(argv=None, environ=None, fit_fn=None, own_keys=None):
    argv = sys.argv[1:] if argv is None else argv
    environ = os.environ if environ is None else environ
    if not 2 <= len(argv) <= 3:
        print("usage: fit.py WORK ASSETS_DIR [06,1c,1e]", file=sys.stderr)
        return 2
    adir = pathlib.Path(argv[1])
    report = adir / "fit.json"
    rows = []
    try:
        stages = parse_stages(argv[2] if len(argv) == 3 else "")
        suffix = "_".join("%02x" % word for word in stages) if stages else ""
        report = adir / ("fit" + suffix + ".json")
        global ROWTRIM
        m = re.search(r"-DSAT_TILE_ROWTRIM(?:=(\d))?(?!\w)", environ.get("KERNEL_CFLAGS", ""))
        ROWTRIM = int(m.group(1) or 1) if m else 0
        config = settings(environ)
        rounds, ends, screens, rank = load(pathlib.Path(argv[0]), environ)
        window = None
        if environ.get("STAGE_WINDOW", "0") == "1":   # tools/stage_window.py as build.py applies it (WORK/stage_window.json)
            sys.path.insert(0, str(REPO / "tools"))
            import stage_window
            sw = stage_window.load(pathlib.Path(argv[0]))
            print("stage window:", stage_window.apply(rounds, sw), flush=True)
            window = stage_window.windows(sw)
        if environ.get("CHAR_FUZZ", "1") != "0":   # tools/char_fuzz.py as build.py applies it (WORK/char_fuzz.json; absent = nothing changes)
            sys.path.insert(0, str(REPO / "tools"))
            import char_fuzz
            data = char_fuzz.load(pathlib.Path(argv[0]))
            if data:
                print("char fuzz:", char_fuzz.augment(rounds, data, keys=environ.get("CHAR_FUZZ_KEYS", "0") == "1",
                                                      pages=environ.get("CHAR_FUZZ_PAGES", "1") == "1",
                                                      key_stages={int(x, 16) for x in environ.get("CHAR_FUZZ_KEY_STAGES", "0e,1c,1e,24").split(",") if x} or None, window=window), flush=True)
        selected = selected_files(rounds, stages)
        room = ends[-1][0] - CART_PACK
        free = free_runs(rounds, ends, **config)
        assets = json.loads((adir / "remap.json").read_text())
        raw = (adir / "gfx_wolverine.bin").read_bytes()
        stage_keys = assets.get("stage_keys", {})
        if own_keys is None:
            sys.path.insert(0, str(REPO / "tools"))
            import rounds_variants
            own_keys = rounds_variants.Data(environ.get("GUEST_SPEC", SPEC)).own[SCH]
        sources = {}
        dialog_keys = set(json.loads(pathlib.Path(environ["FIT_DIALOG_KEYS"]).read_text())) if environ.get("FIT_DIALOG_KEYS") else set()   # gen/guest_dialog_keys.json
        hud_stage = pathlib.Path(environ["FIT_GFX_GUEST"]).read_bytes() if environ.get("FIT_GFX_GUEST") else None
        for word, variant, mask, base in selected:
            own = set(base["keys"][0]) & set(own_keys)
            # guest_rounds.extend keys a shared base file by its first stage.
            asset_stage = base["stages"][0]
            wk = set(stage_keys.get("%02x" % asset_stage, assets["keys"]))
            name = base["name"]
            r = rank.get(base.get("rank_from", name), {})
            if base.get("gfx") and base["gfx"] not in sources:
                sources[base["gfx"]] = pathlib.Path(base["gfx"]).read_bytes()
            source = sources.get(base.get("gfx"), raw)
            p0, d0 = run(source, base, base["keys"], room, free, r, screens, fit_fn=fit_fn)
            guest = dict(base, name=name + "_wv", rank_from=name)
            keys = [set(base["keys"][0]) - own - set(assets["keys"]) | wk] + [set(k) for k in base["keys"][1:]]   # as guest_rounds.extend
            if dialog_keys:   # SAT_WV_DIALOG: the scroll 1 keys of his story box wording, as guest_rounds.extend adds them
                keys[1] = keys[1] | dialog_keys
            p1, d1 = run(source if hud_stage is None else hud_stage, guest, keys, room, free, rank.get(name, {}), screens, wk, fit_fn)
            missing = sorted(set(d1) & wk)
            tiles = lambda p: p["inmain"] + sum(x[2] for x in p["segs"]) if p is not None else None
            row = dict(file=name, stage="%02x" % word, variant=variant, mask=mask,
                       schaefer_own=len(own), wolverine=len(wk), sch_drop=len(d0), wolv_drop=len(d1),
                       wolv_own_dropped=len(missing), missing_guest_keys=missing,
                       sch_tiles=tiles(p0), wolv_tiles=tiles(p1), cart_pack_room=room, controls=config,
                       gate=p0 is not None and p1 is not None and len(d1) <= len(d0) and not missing)
            rows.append(row)
            print(json.dumps(row), flush=True)
        if environ.get("FIT_GFX_FRONT"):   # his front file: the arcade's keys and ranking, the select picture, plate and icon written in
            front = next(f for f in rounds["files"] if f["name"] == "front")
            fr = rank.get("front", {})
            p0, d0 = run(raw, front, front["keys"], room, free, fr, screens, fit_fn=fit_fn)
            p1, d1 = run(pathlib.Path(environ["FIT_GFX_FRONT"]).read_bytes(), dict(front, name="front_wv", rank_from="front"), front["keys"], room, free, fr, screens, fit_fn=fit_fn)
            tiles = lambda p: p["inmain"] + sum(x[2] for x in p["segs"]) if p is not None else None
            row = dict(file="front_wv", stage="00", variant=0, mask=0, sch_drop=len(d0), wolv_drop=len(d1), sch_tiles=tiles(p0), wolv_tiles=tiles(p1),
                       sch_bytes=sum(len(t) for t in p0["tile"]) if p0 else None, wolv_bytes=sum(len(t) for t in p1["tile"]) if p1 else None,
                       cart_pack_room=room, controls=config, gate=p0 is not None and p1 is not None and len(d1) <= len(d0))
            rows.append(row)
            print(json.dumps(row), flush=True)
        report.write_text(json.dumps(rows, indent=0))
        passed = bool(rows) and all(row["gate"] for row in rows)
        print("gate", passed, "fail", [row["file"] for row in rows if not row["gate"]])
        return 0 if passed else 1
    except (OSError, ValueError, KeyError, IndexError, TypeError, ImportError) as exc:
        # Do not leave a previous successful report looking like this attempt.
        if adir.is_dir():
            try:
                report.write_text("[]\n")
            except OSError:
                pass
        print("NO-GO:", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
