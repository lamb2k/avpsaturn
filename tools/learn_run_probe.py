#!/usr/bin/env python
"""Run a learning probe through the retained Coffee Shop route (frames to 5566).
usage: learn_run_probe.py NAME PROBE.lua [PERTURB]
Output: E:/AvP/learning/mame/NAME/probe.tsv. Refuses to overwrite. Checks free commit first."""
import os
import pathlib
import shutil
import subprocess
import sys

REPO = pathlib.Path("C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-playable-loop-pivot")
name, probe = sys.argv[1], pathlib.Path(sys.argv[2]).resolve()
perturb = len(sys.argv) > 3
free = int(subprocess.check_output(["powershell", "-NoProfile", "-c",
           "(Get-CimInstance Win32_OperatingSystem).FreeVirtualMemory"]).strip()) / (1 << 20)
if free < 10:
    sys.exit(f"free commit {free:.1f} GB under 10 GB: not starting")
out = pathlib.Path("E:/AvP/learning/mame") / name
out.mkdir(parents=True)
shutil.copytree(REPO / ".deps/mame/full_route_nvram_baseline", out / "nvram/avspu")
(out / "cfg").mkdir()
env = dict(os.environ)
env.update(AVSP_ORACLE11_PROGRESSION_ROOT=str(out).replace("\\", "/"),
           AVSP_ORACLE11_COFFEE_SHOP_SCENE="1", AVSP_ORACLE11_PROGRESSION_LIFECYCLE="1",
           AVSP_ORACLE11_NAVIGATION_PERTURB="1" if perturb else "0",
           AVSP_ORACLE11_PLAYER_AUDIO_ROOT=str(out).replace("\\", "/"), AVSP_ORACLE11_PLAYER_AUDIO_VARIANT="baseline",
           AVSP_ORACLE11_PLAYER_AUDIO_COMPACT_QSOUND="1", AVSP_ORACLE11_PLAYER_AUDIO_LAST_FRAME="5566",
           AVSP_LEARN_PROBE_OUT=str(out / "probe.tsv").replace("\\", "/"))
r = subprocess.run([str(REPO / ".deps/mame/mame0289/mame.exe"), "avspu", "-rompath",
                    "C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest", "-video", "none", "-sound", "none",
                    "-nothrottle", "-skip_gameinfo", "-autoboot_delay", "0", "-nvram_directory", str(out / "nvram"),
                    "-cfg_directory", str(out / "cfg"), "-autoboot_script", str(probe)],
                   cwd=REPO, env=env, stdout=open(out / "stdout.txt", "w"), stderr=subprocess.STDOUT, timeout=int(os.environ.get("LEARN_PROBE_TIMEOUT", "540")))
print("exit", r.returncode, "rows", sum(1 for _ in open(out / "probe.tsv")))
