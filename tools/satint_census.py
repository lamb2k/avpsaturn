#!/usr/bin/env python
"""Lane satint: run the retained Round 1 route under MAME and record every tile key the graphics library would look up.
usage: satint_census.py [LUA] [OUTNAME]   default satint_census.lua census; satint_reads.lua reads and satint_oreads.lua oreads record ROM reads.
env for the census: SATINT_STOP_IRQ (15113 ends at the Round 1 clear), SATINT_SNAPS. Output E:/AvP/learning/lane-satint/OUTNAME (ROM-derived, never commit)."""
import os, pathlib, shutil, subprocess, sys
REPO = pathlib.Path("C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-playable-loop-pivot")
out = pathlib.Path(os.environ.get("SATINT_ROOT", "E:/AvP/learning/lane-satint")) / (sys.argv[2] if len(sys.argv) > 2 else "census")
out.mkdir(parents=True, exist_ok=True)
if not (out / "nvram/avspu").exists():
    shutil.copytree(REPO / ".deps/mame/full_route_nvram_baseline", out / "nvram/avspu", copy_function=shutil.copyfile)
(out / "cfg").mkdir(exist_ok=True)
root = str(out).replace("\\", "/")
env = dict(os.environ, SATINT_CENSUS_OUT=root, AVSP_ORACLE11_PLAYER_AUDIO_ROOT=root, AVSP_ORACLE11_PLAYER_AUDIO_VARIANT="baseline",
           AVSP_ORACLE11_PLAYER_AUDIO_COMPACT_QSOUND="1", AVSP_ORACLE11_NAVIGATION_PERTURB="0")
script = pathlib.Path(__file__).with_name(sys.argv[1] if len(sys.argv) > 1 else "satint_census.lua")
r = subprocess.run([str(REPO / ".deps/mame/mame0289/mame.exe"), "avspu", "-rompath", "C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest",
    "-video", "none", "-sound", "none", "-nothrottle", "-skip_gameinfo", "-autoboot_delay", "0", "-nvram_directory", root + "/nvram",
    "-cfg_directory", root + "/cfg", "-snapshot_directory", root + "/snap", "-autoboot_script", str(script)],
    cwd=REPO, env=env, stdout=open(out / "stdout.txt", "w"), stderr=subprocess.STDOUT, timeout=1500)
print("exit", r.returncode)
