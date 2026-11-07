#!/usr/bin/env python
"""Lane rounds: run tools/rounds_walk.lua under MAME. usage: rounds_walk.py OUTDIR [MAXFRAMES]. ROM-derived output: keep under E:/AvP/learning."""
import os, pathlib, shutil, subprocess, sys
REPO = pathlib.Path("C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-playable-loop-pivot")
out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
if not (out / "nvram/avspu").exists():
    shutil.copytree(REPO / ".deps/mame/full_route_nvram_baseline", out / "nvram/avspu", copy_function=shutil.copyfile)
(out / "cfg").mkdir(exist_ok=True)
root = str(out).replace("\\", "/")
env = dict(os.environ, ROUNDS_OUT=root, ROUNDS_MAXF=sys.argv[2] if len(sys.argv) > 2 else "400000")
r = subprocess.run([str(REPO / ".deps/mame/mame0289/mame.exe"), "avspu", "-rompath", "C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest", "-video", "none", "-sound", "none", "-nothrottle",
    "-skip_gameinfo", "-autoboot_delay", "0", "-nvram_directory", root + "/nvram", "-cfg_directory", root + "/cfg", "-snapshot_directory", root + "/snap",
    "-autoboot_script", str(pathlib.Path(__file__).with_name("rounds_walk.lua"))], cwd=REPO, env=env, stdout=open(out / "stdout.txt", "w"), stderr=subprocess.STDOUT, timeout=int(os.environ.get("ROUNDS_TIMEOUT", "550")))
print("exit", r.returncode)
