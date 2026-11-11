#!/usr/bin/env python
"""Lane sprite-store: keep only the next stage's load-window pages in a stage file (STAGE_WINDOW=1, default off).

A stage file keeps the ROM pages its own stage reads, the front end's and the next stage's (tools/rounds_config.py), each with a page either side. The next
stage's pages are there because the Saturn kernel loads a stage file only after the stage word has held 12 vblanks (saturn/rt/kernel.c round_check), so the
game runs its first frames of the next stage on the old file. Those frames read a small part of the next stage's pages (the stage's setup tables); the rest of the
next stage's reads come after its own file has loaded and restored them. Keeping all of the next stage's pages costs 100 to 400 pages of tile spill room per file.

This keeps the pages read in the first N frames after the stage word changes (tools/rounds_fuzz.lua ROUNDS_WINDOW=N, N=45, 3.75 times the 12 vblank hold; wNN.txt,
"p page" lines, one file per entered stage per run) instead of all of them. A page the old file then spills tiles over is restored by the next stage's own file
(rounds_pack restores, build.py round_files), as every spilled page already is.

usage: stage_window.py WORK CENSUS.json RUNDIR [RUNDIR...]   RUNDIR: a fuzz or route census run made with ROUNDS_WINDOW (wNN.txt files); a directory of such runs
  is also taken (every subdirectory with w files). Writes WORK/stage_window.json: the census pages per stage (with the KO/continue pages, as rounds_config.py unions
  them), the window pages per stage word with the number of runs they came from, and the frames.
Build side (saturn/rt/build.py, tools/wolverine/fit.py): apply(rounds, data) before char_fuzz.augment(..., window=windows(data)). ROM-derived input: WORK only."""
import glob
import json
import pathlib
import sys

PAGE = 0x400
ROM_BYTES = 0x200000


def pad(pages, limit, by=1):
    return {p + d for p in pages for d in range(-by, by + 1) if 0 <= p + d < limit}


def read_window(d):
    """One run directory -> {stage word hex: set of ROM pages read in the first frames after the word changed to it}."""
    out = {}
    for f in pathlib.Path(d).glob("w[0-9a-f][0-9a-f].txt"):
        ps = set()
        for line in f.read_text().splitlines():
            p = line.split()
            if len(p) == 2 and p[0] == "p":
                ps.add(int(p[1]))
        out[f.stem[1:]] = ps
    return out


def run_dirs(paths):
    found = []
    for a in paths:
        for d in sorted(glob.glob(str(a))) or [str(a)]:
            d = pathlib.Path(d)
            if any(d.glob("w[0-9a-f][0-9a-f].txt")):
                found.append(d)
            else:
                found += sorted(x for x in d.iterdir() if x.is_dir() and any(x.glob("w[0-9a-f][0-9a-f].txt")))
    return found


def build(work, census, dirs, frames=45):
    C = json.loads(pathlib.Path(census).read_text())
    if C["page"] != PAGE:
        raise ValueError("census page size %d is not %d" % (C["page"], PAGE))
    stages = dict(C["stages"])
    ANY = stages.pop("any", dict(pages=[]))
    census_pages = {st: sorted(set(v["pages"]) | set(ANY["pages"])) for st, v in sorted(stages.items())}
    window, runs, seen = {}, {}, []
    for d in run_dirs(dirs):
        w = read_window(d)
        if not w:
            continue
        seen.append(str(d))
        for st, ps in w.items():
            if not ps:   # a run that never entered the stage
                continue
            window.setdefault(st, set()).update(ps)
            runs[st] = runs.get(st, 0) + 1
    out = dict(version=1, page=PAGE, frames=frames, census=census_pages, window={st: sorted(v) for st, v in sorted(window.items())}, runs=dict(sorted(runs.items())), sources=seen)
    pathlib.Path(work, "stage_window.json").write_text(json.dumps(out, separators=(",", ":")))
    return out


def load(work):
    p = pathlib.Path(work) / "stage_window.json"
    return json.loads(p.read_text()) if p.exists() else None


def windows(data):
    """{stage word (int): pages} the window rule keeps of a stage entered next; absent where a stage has no window run (the whole stage stays kept)."""
    return {int(st, 16): set(ps) for st, ps in data["window"].items() if data["runs"].get(st, 0) >= 1} if data else {}


def apply(rounds, data, min_runs=1):
    """Replace the next-stage term of every stage file's keep_pages (rounds.json as tools/rounds_config.py wrote it, before char_fuzz.augment) by the window pages.
    The old rule is recomputed from the census pages and must reproduce keep_pages exactly (else the census is not the one rounds.json was made from)."""
    if not data:
        raise ValueError("STAGE_WINDOW=1 needs WORK/stage_window.json (tools/stage_window.py)")
    if data["page"] != rounds["page"]:
        raise ValueError("window census page size %d is not the rounds page %d" % (data["page"], rounds["page"]))
    limit = ROM_BYTES // rounds["page"]
    pg = {int(st, 16): set(ps) for st, ps in data["census"].items()}
    order = sorted(pg)
    win = {st: ps for st, ps in windows(data).items() if data["runs"].get("%02x" % st, 0) >= min_runs}
    report = dict(files=0, windowed=0, pages_freed=0, whole=[])
    for f in rounds["files"]:
        s = f["stages"][0]
        if s == 0:
            continue
        nxt = next((x for x in order if x > s), None)
        old = pad(pg[s] | pg[0] | pg.get(nxt, set()), limit)
        if old != set(f["keep_pages"]):
            raise ValueError("stage_window.json census does not reproduce the keep pages of %s (%d against %d pages)" % (f["name"], len(old), len(f["keep_pages"])))
        report["files"] += 1
        if nxt is None or nxt not in win:
            if nxt is not None:
                report["whole"].append("%02x" % nxt)
            continue
        new = pad(pg[s] | pg[0] | win[nxt], limit)
        f["keep_pages"] = sorted(new)
        report["windowed"] += 1
        report["pages_freed"] += len(old) - len(new)
    report["whole"] = sorted(set(report["whole"]))
    return report


if __name__ == "__main__":
    o = build(sys.argv[1], sys.argv[2], sys.argv[3:])
    print({"frames": o["frames"], "window pages": {st: len(v) for st, v in o["window"].items()}, "runs": o["runs"], "run dirs": len(o["sources"])})
