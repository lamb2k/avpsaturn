#!/usr/bin/env python
"""Tile keys of the story pages and cut-ins of every stage (saturn/rt/build.py reads WORK/story_keys.txt, "STAGEHEX section hexkey" lines).
The route censuses warp into a stage and press Attack, which skips the stage's intro story and the stage-clear story, so a stage file lacked the pictures' sprite tiles and the
story drew with holes (stage 0a, Boss Rush fight 3 and the stage select entry: 40+ sprite keys). tools/story_keys.lua warps to each stage word (02..24) and presses nothing: one
start run (the stage's own intro story and opening) and one clear run (boss-down flags after 900 frames of play: the clear card, the stage-clear story, the next stage's intro).
A key seen in a clear run is listed under the stage word the game held when it was seen AND under the stage that was cleared (the file switch happens early in a Boss Rush).
ROM-derived output stays in WORK.  usage: story_keys.py WORK [OUTDIR]"""
import concurrent.futures as cf, os, pathlib, shutil, subprocess, sys
HERE = pathlib.Path(__file__).resolve().parent
OLD = pathlib.Path("C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-playable-loop-pivot")
ROMS = "C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest"
WORK = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else WORK / "story_keys_runs")
STAGES = [f"{w:02x}" for w in range(2, 0x26, 2)]
JOBS = [(w, kind) for w in STAGES for kind in ("s", "c")]
WINDOW_START = 1000   # frames after the warp: keys first seen before it belong to the stage's intro story and round card
WINDOW_CLEAR = 900    # frames after the warp: the clear runs set the flags at 900 frames of play (the warp to the first play frame takes a few), so what is first seen after it is the clear sequence


def one(job):
    w, kind = job
    d = OUT / f"{w}_{kind}"
    if not (os.environ.get("STORY_REUSE") and (d / "keys.txt").exists()):   # STORY_REUSE=1 re-reads finished runs
        if d.exists():
            shutil.rmtree(d, onerror=lambda f, p, e: (os.chmod(p, 0o666), f(p)))   # MAME leaves the eeprom read-only
        (d / "cfg").mkdir(parents=True)
        shutil.copytree(OLD / ".deps/mame/full_route_nvram_baseline", d / "nvram/avspu")
        run(d, w, kind)
    out = set()
    for l in open(d / "keys.txt"):
        t = l.split()
        if len(t) < 4:
            continue
        tag, sec, key, seen = t[0], int(t[1]), int(t[2], 16), int(t[3])
        if kind == "s" and seen >= WINDOW_START:   # a start run keeps the story and the round card (the first frames)
            continue
        if kind == "c" and seen < WINDOW_CLEAR:    # a clear run keeps what is first seen after the clear flags (the clear sequence, the clear story, the next stage's intro)
            continue
        out.add((tag, sec, key))
        if kind == "c":
            out.add((w, sec, key))
    return out


def run(d, w, kind):
    env = dict(os.environ, S_OUT=str(d).replace("\\", "/"), S_STAGE=w, S_SPAN="1800" if kind == "s" else "3300", S_CLEAR_AT="-1" if kind == "s" else "900", S_FRAMES="12000")
    subprocess.run([str(OLD / ".deps/mame/mame0289/mame.exe"), "avspu", "-rompath", ROMS, "-video", "none", "-sound", "none", "-nothrottle", "-skip_gameinfo",
                    "-autoboot_delay", "0", "-seconds_to_run", "100000", "-nvram_directory", str(d / "nvram"), "-cfg_directory", str(d / "cfg"), "-snapshot_directory", str(d / "snap"),
                    "-autoboot_script", str(HERE / "story_keys.lua")], cwd=OLD, env=env, stdout=open(d / "stdout.txt", "w"), stderr=subprocess.STDOUT, timeout=1800)


with cf.ThreadPoolExecutor(4) as ex:
    sets = list(ex.map(one, JOBS))
keys = set().union(*sets) - {(w, 0, 0) for w in STAGES}
(WORK / "story_keys.txt").write_text("".join(f"{w} {s} {k:x}\n" for w, s, k in sorted(keys)))
print({w: sum(1 for t in keys if t[0] == w) for w in STAGES}, "->", WORK / "story_keys.txt")
