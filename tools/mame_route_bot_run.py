#!/usr/bin/env python
"""Run tools/mame_route_bot.lua from an empty or given prefix. usage: mame_route_bot_run.py OUTDIR CHAR MAXFRAMES [PREFIX]   CHAR as BOT_CHAR. Writes OUTDIR/route.txt, log.txt, snap/ (ROM-derived stills: not for commit). env BOT_SNAPEV, BOT_SHOT."""
import os, pathlib, shutil, subprocess, sys
OLD = pathlib.Path("C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-playable-loop-pivot")
L, want, maxf = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3]
L.mkdir(parents=True)
prefix = sys.argv[4] if len(sys.argv) > 4 else None
if not prefix:
    prefix = str(L / "prefix0.txt")
    pathlib.Path(prefix).write_text("last 0\n")
shutil.copytree(OLD / ".deps/mame/full_route_nvram_baseline", L / "nvram/avspu", copy_function=shutil.copyfile)
(L / "cfg").mkdir()
u = lambda p: str(p).replace("\\", "/")
env = dict(os.environ, BOT_PREFIX=u(prefix), BOT_OUT=u(L / "route.txt"), BOT_LOG=u(L / "log.txt"), BOT_MAX=maxf, BOT_CHAR=want)
r = subprocess.run([str(OLD / ".deps/mame/mame0289/mame.exe"), "avspu", "-rompath", "C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest", "-video", "none", "-sound", "none", "-nothrottle",
                    "-snapshot_directory", u(L / "snap"), "-skip_gameinfo", "-autoboot_delay", "0", "-nvram_directory", u(L / "nvram"), "-cfg_directory", u(L / "cfg"),
                    "-autoboot_script", u(pathlib.Path(__file__).with_name("mame_route_bot.lua"))], cwd=OLD, env=env, stdout=open(L / "stdout.txt", "w"), stderr=subprocess.STDOUT)
print("exit", r.returncode)
