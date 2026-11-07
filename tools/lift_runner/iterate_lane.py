#!/usr/bin/env python
"""Boundary loop for a private work tree (env LEARN_OUT). Run the host check; on NOFN at an even ROM address add a root, rebuild, repeat, until SECONDS is spent.
usage: iterate_lane.py SECONDS GOLDEN     env GOLD_DELTA=1 for a delta golden. Prints the last line of each run."""
import os, pathlib, re, subprocess, sys, time
T = pathlib.Path(__file__).resolve().parents[1]
W = os.environ["LEARN_OUT"]
wsl = lambda p: "/mnt/" + p[0].lower() + p[2:]
RUN = wsl(T.as_posix()) + "/lift_runner/run.sh"
end = time.time() + float(sys.argv[1])
while time.time() < end:
    tmo = int(max(20, min(end - time.time(), 150)))
    cmd = f"GOLD_DELTA=1 GOLDEN={sys.argv[2]} LIFT_RUN={wsl(W)}/lift/run LIFT_ROM={wsl(W)}/rt.bin TMO={tmo} TAIL=8 sh '{RUN}' 400000 {os.environ.get('STOP', '3')}"
    r = subprocess.run(["wsl.exe", "-e", "sh", "-c", cmd], capture_output=True, text=True, errors="replace")
    last = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-200:]
    print(last[:200], flush=True)
    m = re.search(r"NOFN ([0-9a-f]+) vblank (\d+)", r.stdout)
    if not m:
        print(r.stdout[-1500:])
        break
    a = int(m[1], 16)
    if a & 1 or a >= 0x200000 or a < 0x400:
        print("not a ROM code address, stopping")
        break
    with open(T / "roots.txt", "a") as f:
        f.write(f"{a:x}\n")
    for c in (["learn_cfg68k.py", "build"], ["make_merged.py"], ["lift_runner/build.py"]):
        subprocess.run([sys.executable, str(T / c[0])] + c[1:], capture_output=True)
