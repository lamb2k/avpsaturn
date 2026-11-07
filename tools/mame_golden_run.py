#!/usr/bin/env python
"""Golden from a saved input route, without the retained route harness.
usage: mame_golden_run.py NAME ROUTE [LAST]    env LEARN_SAVE=frame,frame LEARN_DELTA=1 (changed words only)   Output: E:/AvP/learning/mame/NAME. Refuses to overwrite; checks free commit and E: space."""
import os, pathlib, shutil, subprocess, sys
OLD = pathlib.Path("C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-playable-loop-pivot")
HERE = pathlib.Path(__file__).resolve().parent
name, route = sys.argv[1], pathlib.Path(sys.argv[2]).resolve()
last = sys.argv[3] if len(sys.argv) > 3 else None
free = int(subprocess.check_output(["powershell", "-NoProfile", "-c", "(Get-CimInstance Win32_OperatingSystem).FreeVirtualMemory"]).strip()) / (1 << 20)
if free < 12:
    sys.exit(f"free commit {free:.1f} GB under 12 GB: not starting")
if shutil.disk_usage("E:/").free < 4 << 30:
    sys.exit("E: under 4 GB")
out = pathlib.Path("E:/AvP/learning/mame") / name
out.mkdir(parents=True)
shutil.copytree(OLD / ".deps/mame/full_route_nvram_baseline", out / "nvram/avspu")
(out / "cfg").mkdir()
env = dict(os.environ, AVSP_ROUTE=str(route).replace("\\", "/"), AVSP_LEARN_PROBE_OUT=str(out / "probe.tsv").replace("\\", "/"), LEARN_MAXIRQ=os.environ.get("LEARN_MAXIRQ", "30000"))
if last:
    env["LEARN_LAST"] = last
r = subprocess.run([str(OLD / ".deps/mame/mame0289/mame.exe"), "avspu", "-rompath", "C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest", "-video", "none", "-sound", "none",
                    "-nothrottle", "-skip_gameinfo", "-autoboot_delay", "0", "-nvram_directory", str(out / "nvram"), "-cfg_directory", str(out / "cfg"),
                    "-state_directory", str(out / "sta"), "-autoboot_script", str(HERE / "mame_golden.lua")],
                   cwd=OLD, env=env, stdout=open(out / "stdout.txt", "w"), stderr=subprocess.STDOUT, timeout=int(os.environ.get("LEARN_PROBE_TIMEOUT", "3000")))
print("exit", r.returncode, "bytes", (out / "probe.tsv").stat().st_size, "IRQ", (out / "probe.tsv.io.txt").read_bytes().count(bytes([86,13,10])))
