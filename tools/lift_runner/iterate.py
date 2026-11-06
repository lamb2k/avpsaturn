#!/usr/bin/env python
"""Boundary loop: run the host runner; a jump to an unknown function adds a root; rebuild; repeat. usage: iterate.py VBLANKS [ROUNDS]"""
import pathlib, re, subprocess, sys
T = pathlib.Path(__file__).resolve().parents[1]
L = pathlib.Path("E:/AvP/learning")
G = "/mnt/e/AvP/learning/mame/golden_a/probe.tsv"
rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 12
for k in range(rounds):
    r = subprocess.run(["wsl.exe","-e","sh","-c",f"cd /mnt/e/AvP/learning/lift/run && STOP_DIV=${{STOP_DIV:-6}} timeout 120 ./lift_runner /mnt/e/AvP/learning/merged.bin {G} {G}.io.txt {sys.argv[1]} /mnt/e/AvP/learning/mask.txt 2>&1 | tail -24"],capture_output=True,text=True)
    out = r.stdout
    m = re.search(r"(NOFN|MISSING) ([0-9a-f]+)", out)
    if not m:
        print(out[-2500:]); break
    print("new root", m[2], out.strip().splitlines()[-1][:80], flush=True)
    with open(L/"roots.txt","a") as f: f.write(m[2]+"\n")
    (L/"roots_auto.txt").unlink(missing_ok=True)
    subprocess.run([sys.executable,str(T/"learn_cfg68k.py"),"build"],check=True,stdout=subprocess.DEVNULL)
    subprocess.run([sys.executable,str(T/"make_merged.py")],check=True,stdout=subprocess.DEVNULL)
    subprocess.run([sys.executable,str(T/"lift_runner"/"build.py")],check=True,stdout=subprocess.DEVNULL)
