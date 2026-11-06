#!/usr/bin/env python
"""Boundary loop: run the host check, add a root for each dispatch to an unlifted ROM address, rebuild, repeat."""
import re, subprocess, sys, time
import pathlib
T = pathlib.Path(__file__).resolve().parents[1].as_posix()
WT = "/mnt/" + T[0].lower() + T[2:]
GOLDEN = sys.argv[2] if len(sys.argv) > 2 else "golden_r1s"
ROOTS = T + "/roots.txt"
end = time.time() + float(sys.argv[1]) if len(sys.argv) > 1 else time.time() + 500
while time.time() < end:
    r = subprocess.run(["wsl.exe", "-e", "sh", "-c", f"GOLDEN={GOLDEN} TMO=280 sh {WT}/lift_runner/run.sh 30000 100000"], capture_output=True, text=True, errors="replace")
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
