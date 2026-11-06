#!/usr/bin/env python
"""Boundary loop: run the host check, add a root for each dispatch to an unlifted ROM address, rebuild, repeat."""
import re, subprocess, sys, time
T = "E:/AvP/worktrees/decomp-main/tools"
ROOTS = "E:/AvP/learning/roots.txt"
end = time.time() + float(sys.argv[1]) if len(sys.argv) > 1 else time.time() + 500
while time.time() < end:
    r = subprocess.run(["wsl.exe", "-e", "sh", "/mnt/e/AvP/worktrees/decomp-main/tools/lift_runner/run.sh", "6000", "100000"], capture_output=True, text=True, errors="replace")
    m = re.search(r"NOFN ([0-9a-f]+) vblank (\d+)", r.stdout)
    print(r.stdout.strip().splitlines()[-1][:160], flush=True)
    if not m:
        break
    a = int(m[1], 16)
    if a & 1 or a >= 0x200000 or a < 0x400:
        print("not a ROM code address, stopping")
        break
    open(ROOTS, "a").write(f"{a:x}\n")
    for c in (["learn_cfg68k.py", "build"], ["make_merged.py"], ["lift_runner/build.py"]):
        subprocess.run([sys.executable, f"{T}/{c[0]}"] + c[1:], capture_output=True)
