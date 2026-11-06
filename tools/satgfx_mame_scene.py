#!/usr/bin/env python
"""Lane satgfx: run the retained route under MAME and dump scene state and stills.
usage: satgfx_mame_scene.py NAME IRQ[,IRQ...]   Output E:/AvP/learning/lane-satgfx/NAME (ROM-derived, never commit)."""
import os, pathlib, shutil, subprocess, sys
REPO = pathlib.Path("C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-playable-loop-pivot")
name, irqs = sys.argv[1], sys.argv[2]
out = pathlib.Path("E:/AvP/learning/lane-satgfx") / name
out.mkdir(parents=True)
shutil.copytree(REPO / ".deps/mame/full_route_nvram_baseline", out / "nvram/avspu")
(out / "cfg").mkdir()
root = str(out).replace("\\", "/")
last = max(int(x) for x in irqs.split(",")) + 8
env = dict(os.environ, AVSP_ORACLE11_PROGRESSION_ROOT=root, AVSP_ORACLE11_ROUTE_ROOT=root, AVSP_ORACLE11_COFFEE_SHOP_SCENE="1",
           AVSP_ORACLE11_PROGRESSION_LIFECYCLE="1", AVSP_ORACLE11_NAVIGATION_PERTURB="0", AVSP_ORACLE11_PLAYER_AUDIO_ROOT=root,
           AVSP_ORACLE11_PLAYER_AUDIO_VARIANT="baseline", AVSP_ORACLE11_PLAYER_AUDIO_COMPACT_QSOUND="1",
           AVSP_ORACLE11_PLAYER_AUDIO_LAST_FRAME="5566", SATGFX_OUT=root + "/scene.bin", SATGFX_IRQS=irqs)
r = subprocess.run([str(REPO / ".deps/mame/mame0289/mame.exe"), "avspu", "-rompath", "C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest",
    "-video", "none", "-sound", "none", "-nothrottle", "-skip_gameinfo", "-autoboot_delay", "0", "-nvram_directory", root + "/nvram",
    "-cfg_directory", root + "/cfg", "-snapshot_directory", root + "/snap", "-autoboot_script", str(pathlib.Path(__file__).with_name("satgfx_scene_probe.lua"))],
    cwd=REPO, env=env, stdout=open(out / "stdout.txt", "w"), stderr=subprocess.STDOUT, timeout=540)
print("exit", r.returncode)
