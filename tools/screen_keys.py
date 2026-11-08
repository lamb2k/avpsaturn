#!/usr/bin/env python
"""Tile keys (sprites and the three layers, "section hexkey" lines) of the screens after a KO with no lives left, for every round file (saturn/rt/build.py reads WORK/screen_keys.txt).
Runs tools/screen_keys.lua under the pinned MAME 0.289 on four saved routes (one per character: the continue picture differs, a Queen for
Schaefer and Linn, a Predator arm for the Warrior and Hunter), each to its first such KO, then lets the countdown run out through name entry
and GAME OVER (2650 frames; the score table after it is left out, it costs the full stages about 300 sprite keys each). ROM-derived output stays in WORK.
usage: screen_keys.py WORK [OUTDIR]"""
import concurrent.futures as cf, os, pathlib, shutil, subprocess, sys
HERE = pathlib.Path(__file__).resolve().parent
OLD = pathlib.Path("C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-playable-loop-pivot")
ROMS = "C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest"
WORK = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else WORK / "screen_keys_runs")
ROUTES = dict(pw="r1_pw_ko_boss", c1="full_c1", c2="full_c2", c3="full_c3")


def one(name):
    d = OUT / name
    if d.exists():
        shutil.rmtree(d, onerror=lambda f, p, e: (os.chmod(p, 0o666), f(p)))   # MAME leaves the eeprom read-only
    (d / "cfg").mkdir(parents=True)
    shutil.copytree(OLD / ".deps/mame/full_route_nvram_baseline", d / "nvram/avspu")
    env = dict(os.environ, AVSP_ROUTE=str(HERE / "routes" / f"{ROUTES[name]}.txt").replace("\\", "/"), SCREEN_MODE="wait", SCREEN_SNAP=os.environ.get("SCREEN_SNAP", "0"),
               SCREEN_OUT=str(d / "keys.txt").replace("\\", "/"))
    subprocess.run([str(OLD / ".deps/mame/mame0289/mame.exe"), "avspu", "-rompath", ROMS, "-video", "none", "-sound", "none", "-nothrottle", "-skip_gameinfo",
                    "-autoboot_delay", "0", "-nvram_directory", str(d / "nvram"), "-cfg_directory", str(d / "cfg"), "-snapshot_directory", str(d / "snap"),
                    "-autoboot_script", str(HERE / "screen_keys.lua")], cwd=OLD, env=env, stdout=open(d / "stdout.txt", "w"), stderr=subprocess.STDOUT, timeout=1800)
    return {(int(l.split()[0]), int(l.split()[1], 16)) for l in open(d / "keys.txt") if l.strip()}


with cf.ThreadPoolExecutor(4) as ex:
    sets = dict(zip(ROUTES, ex.map(one, ROUTES)))
keys = set().union(*sets.values()) - {(0, 0)}
(WORK / "screen_keys.txt").write_text("".join(f"{s} {k:x}\n" for s, k in sorted(keys)))
print({k: len(v) for k, v in sets.items()}, "union per section", [sum(1 for s, _ in keys if s == i) for i in range(4)], "->", WORK / "screen_keys.txt")
