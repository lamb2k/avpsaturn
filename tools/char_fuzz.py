#!/usr/bin/env python
"""Lane stage-sprites: per-character button-fuzz censuses (tools/rounds_fuzz.py) as a pack input.

The route and walk censuses move ahead and press one attack now and then, so a stage file lacks sprite tiles and ROM pages that other play reaches (jump
attacks, hurt poses, specials, enemy frames the route never met). Fuzz runs (random jumps, attacks, guns, every direction, one character each) saw many of
them: 400 to 1300 sprite keys per character and stage that no stage file held, and ROM pages (0x171400, 0xa5800 to 0xa6c00) that no stage file kept, so a
Linn or Hunter move could read tile data instead of a table.

usage: char_fuzz.py WORK BIT=DIR[,DIR...] [BIT=DIR...] [scripts=DIR[,DIR...]] [--add]   (--add: extend the WORK/char_fuzz.json that is there)
  BIT: the game's character bit (ff81cc): 1 Warrior, 2 Schaefer, 4 Hunter, 8 Linn. DIR: a fuzz run directory (fuzz_pal.txt, sNN.txt).
  scripts: runs made with ROUNDS_SCRIPTLOG=1 (scriptlog.txt): the pages the players' sprite scripts were read from. A script is a character's move, the same in every stage, and
  a move the stage's census never saw sits in a page its file does not keep: one such page, 0x171400, holds Linn's script words and is what fatal 0xe2 at 0xa9cc4 (a script
  word outside the 8 entry jump table) looks like when a stage file puts tiles there. Every stage file keeps these pages.
  Writes WORK/char_fuzz.json: per character the sprite keys each stage word looked up and the keys drawn in the character's own palette (his or her body),
  per stage word the ROM pages any run read, and the player script pages. ROM-derived: WORK only.
Build side (saturn/rt/build.py, tools/wolverine/fit.py): augment(rounds, work, ...) below."""
import glob
import json
import pathlib
import re
import sys

PALETTE = {1: 0, 2: 1, 4: 2, 8: 3}   # the player palette of each character (fuzz_pal.txt "pal key"; checked against each character's own tile bank)
SOLO = (1, 2, 4, 8)
PAGE = 0x400
# Rank tiers (key_rank.json scale). Variant files: route 1e6 a section, own walk 1e5, KO 5e4, pair stand-in 1e4. Base file (three or four players): route 1000 a section, KO 500.
RANK_BODY_VARIANT, RANK_FUZZ_VARIANT = 70000, 150000   # a body key the stage's fuzz runs never looked up: below the walks, above KO
RANK_BODY_BASE, RANK_FUZZ_BASE = 550, 600


def read_run(d):
    """One fuzz run directory -> (stage word -> sprite keys, body keys, stage word -> ROM pages read)."""
    d = pathlib.Path(d)
    keys, pages = {}, {}
    for f in d.glob("s[0-9a-f][0-9a-f].txt"):
        st = f.stem[1:]
        ks, ps = set(), set()
        for line in f.read_text().splitlines():
            p = line.split()
            if len(p) == 2 and p[0] == "0":
                ks.add(int(p[1], 16))
            elif p and p[0] == "r":
                ps.add(int(p[1], 16) // PAGE)
        ks.discard(0)
        keys[st], pages[st] = ks, ps
    pal = {}
    for line in (d / "fuzz_pal.txt").read_text().splitlines():
        p, k = line.split()
        pal.setdefault(int(p), set()).add(int(k, 16))
    return keys, pal, pages


# The players' move scripts (sprite script words read for the player blocks at 0xff8380 and up, every fuzz run of every character and stage, rounds_fuzz.lua ROUNDS_SCRIPTLOG)
# lie in one stretch of the ROM, 0x161400 to 0x1717ff: pages 1410 to 1477 of 1 KB, four blocks (one a character) with other data between. Every stage file keeps all of it,
# 68 KB, of which the files already held 67 pages: page 1477 (0x171400, Linn's last script words, old tile spill stretch 0x171000) was kept by none of them.
SCRIPT_REGION = (0x161400, 0x171800)
PLAYER_OBJECTS = (0x8380, 0x8480, 0x8580)   # a4 (low word; RAM 0xff....) of the player blocks, as the script reader sees them


def script_pages(dirs):
    """Pages of the sprite script words read for player objects (rounds_fuzz.lua ROUNDS_SCRIPTLOG: stage, script address, a4 << 8 | table index)."""
    out = set()
    for d in dirs:
        for line in (pathlib.Path(d) / "scriptlog.txt").read_text().splitlines():
            s, a, v = line.split()
            if (int(v, 16) >> 8) & 0xffff in PLAYER_OBJECTS:
                out.add(int(a, 16) // PAGE)
    return out


def build(work, spec, scripts=(), add=False):
    """add: extend WORK/char_fuzz.json (its runs, keys, pages and script pages stay) with the runs in spec and scripts, instead of replacing it."""
    out = dict(version=1, page=PAGE, palette={str(k): v for k, v in PALETTE.items()}, chars={}, pages={}, player_script_pages=sorted(script_pages(scripts)))
    prior = load(work) if add else None
    if prior:
        out["player_script_pages"] = sorted(set(out["player_script_pages"]) | set(prior["player_script_pages"]))
        out["pages"] = {st: set(ps) for st, ps in prior["pages"].items()}
    for bit in sorted(set(spec) | {int(b) for b in (prior["chars"] if prior else ())}):
        old = prior["chars"].get(str(bit)) if prior else None
        keys = {st: set(v) for st, v in old["stage_keys"].items()} if old else {}
        body, runs = set(old["body_keys"]) if old else set(), list(old["runs"]) if old else []
        for d in spec.get(bit, ()):
            k, pal, pages = read_run(d)
            runs.append(str(d))
            for st, ks in k.items():
                keys.setdefault(st, set()).update(ks)
            body |= pal.get(PALETTE[bit], set())
            for st, ps in pages.items():
                out["pages"].setdefault(st, set()).update(ps)
        body.discard(0)
        out["chars"][str(bit)] = dict(runs=runs, stage_keys={st: sorted(v) for st, v in sorted(keys.items())}, body_keys=sorted(body))
    out["pages"] = {st: sorted(v) for st, v in sorted(out["pages"].items())}
    pathlib.Path(work, "char_fuzz.json").write_text(json.dumps(out, separators=(",", ":")))
    return out


def load(work):
    p = pathlib.Path(work) / "char_fuzz.json"
    return json.loads(p.read_text()) if p.exists() else None


def pad(pages, limit):
    return {p + d for p in pages for d in (-1, 0, 1) if 0 <= p + d < limit}


def augment(rounds, data, keys=False, pages=True, remap=(), key_stages=None, window=None):
    """Add the fuzz data to rounds (rounds.json in memory). Returns a report dict.
    pages: every stage file keeps the ROM pages the fuzz runs read in its stage word, in the front end's and in the next stage's, each with a page either side
    (the keep rule of tools/rounds_config.py), and the pages the players' sprite scripts are read from in any stage. A correctness fix: a page a play reads must hold the
    ROM's bytes in the file that plays it.
    keys: a file's sprite candidates gain the sprite keys the fuzz runs of the characters in its mask looked up in its stage, and those characters' body keys
    (their own palette, every stage); both are ranked under the route keys and above the walks (fuzz_keys / body_keys on the file, read by build.py).
    key_stages: stage words (ints) that take keys; None = all. Where every variant of a stage packs to the same bytes (no sprite key dropped) the sector store
    (tools/sector_store.py, 2^18 sectors of 2 KB) keeps the 11 files once; a stage whose variants differ costs about 21 files of room. Only stages whose files already differ
    (0e, 1c, 1e, 24 on the integration build) can take per-character keys without outgrowing the store.
    remap: sprite keys that must not enter (the bonus character's remap keys: a key it uses holds its tile in the guest files).
    window: {stage word: pages} (tools/stage_window.py windows(), STAGE_WINDOW=1): the next stage's term is the pages its first frames read, not every page its fuzz runs read."""
    report = dict(pages_added=0, keys_added=0, files=0)
    page = rounds["page"]
    limit = 0x200000 // page
    if not data:   # no census: the script stretch is still kept
        if not pages:
            return report
        data = dict(page=page, pages={}, chars={})
    if page != data["page"]:
        raise ValueError("fuzz census page size %d is not the rounds page %d" % (data["page"], page))
    remap = set(remap)
    order = sorted({f["stages"][0] for f in rounds["files"] if f["stages"][0]})
    fz = {int(st, 16): set(ps) for st, ps in data["pages"].items()}
    allp = set().union(*fz.values()) if fz else set()
    scripts = set(data.get("player_script_pages", ())) | set(range(SCRIPT_REGION[0] // page, (SCRIPT_REGION[1] + page - 1) // page))
    for f in rounds["files"]:
        s = f["stages"][0]
        if pages:
            if s == 0:
                want = pad(allp | scripts, limit)
            else:
                nxt = next((x for x in order if x > s), None)
                want = pad(fz.get(s, set()) | fz.get(0, set()) | ((window or {}).get(nxt) if nxt in (window or {}) else fz.get(nxt, set())) | scripts, limit)
            new = want - set(f["keep_pages"])
            if new:
                f["keep_pages"] = sorted(set(f["keep_pages"]) | want)
                report["pages_added"] += len(new)
        if keys and s and (key_stages is None or s in key_stages):
            mask = f.get("mask")
            bits = [b for b in SOLO if mask is None or mask & b]
            fk, bk, ak = set(), set(), set()
            for b in SOLO:
                c = data["chars"].get(str(b))
                if c:
                    ak.update(c["stage_keys"].get("%02x" % s, ()))
                    ak.update(c["body_keys"])
                    if b in bits:
                        fk.update(c["stage_keys"].get("%02x" % s, ()))
                        bk.update(c["body_keys"])
            fk -= remap
            bk -= remap
            ak -= remap
            have = set(f["keys"][0])
            # Every variant of a stage asks for the same keys (all four characters' fuzz and body keys, ranked by the characters in the file): in a stage with room
            # the variants then pack to identical files, which the sector store (tools/sector_store.py, 2^18 sectors) keeps once. The ranks decide what drops in a short stage.
            f["keys"][0] = sorted(have | ak)
            f["fuzz_keys"] = sorted(fk)
            f["body_keys"] = sorted(bk)
            # What the characters other than Schaefer (the slot a bonus character takes) looked up: tools/wolverine/guest_rounds.py keeps these in a guest file even where the
            # census calls them Schaefer's own (1c: 28 keys Warrior's fuzz play used that no census route of his saw).
            f["other_keys"] = sorted(set().union(*(set(data["chars"][str(b)]["stage_keys"].get("%02x" % s, ())) | set(data["chars"][str(b)]["body_keys"]) for b in bits if b != 2 and str(b) in data["chars"])) - remap) if len(bits) > (1 if 2 in bits else 0) else []
            report["keys_added"] += len((fk | bk) - have)
            report["files"] += 1
    return report


def rank(f, frank):
    """Raise frank (key -> score) for a file's fuzz and body keys, never lowering a score."""
    variant = "mask" in f
    for ks, tier in ((f.get("fuzz_keys", ()), RANK_FUZZ_VARIANT if variant else RANK_FUZZ_BASE),
                     (f.get("body_keys", ()), RANK_BODY_VARIANT if variant else RANK_BODY_BASE)):
        for k in ks:
            if frank.get(k, 0) < tier:
                frank[k] = tier
    return frank


if __name__ == "__main__":
    spec, scripts, add = {}, [], False
    for a in sys.argv[2:]:
        if a == "--add":
            add = True
            continue
        bit, dirs = a.split("=", 1)
        found = [x for d in dirs.split(",") for x in sorted(glob.glob(d)) or [d]]
        if bit == "scripts":
            scripts += found
        else:
            spec.setdefault(int(bit), []).extend(found)
    o = build(sys.argv[1], spec, scripts, add)
    print({b: (len(c["runs"]), sum(len(v) for v in c["stage_keys"].values()), len(c["body_keys"])) for b, c in o["chars"].items()},
          "page stages", {st: len(ps) for st, ps in o["pages"].items()}, "player script pages", len(o["player_script_pages"]))
