#!/usr/bin/env python
"""Swap saturn/game's readable routines into a private copy of the host runner's objects, keeping each lifted body as lifted_NNN for the IRQ fallback.
usage: apply_overrides.py HOSTDIR    (holds c*/lifted_mem.c, c*.o, dispatch.inc; output is ROM-derived and stays on this PC)"""
import pathlib, re, subprocess, sys
T = pathlib.Path(__file__).resolve().parents[2]
H = pathlib.Path(sys.argv[1])
wsl = lambda p: "/mnt/" + p.as_posix()[0].lower() + p.as_posix()[2:]
names = (T / "saturn/game/overrides.txt").read_text().split()
cmds = []
for src in H.glob("c[0-9]*/lifted_mem.c"):
    t = o = src.read_text()
    for n in names:
        t = t.replace(f"void f_{n}(void){{", f"void lifted_{n}(void){{")
    if t != o:
        src.write_text(t)
        cmds.append(f"gcc -DHOST -DPREEMPT -w -O1 -g -fno-strict-aliasing -c {src.parent.name}/lifted_mem.c -o {src.parent.name}.o")
g = wsl(T / "saturn/game")
cmds.append(f"gcc -DHOST_CHECK -w -O1 -g -c '{g}/game_hot.c' -o cg_hot.o && gcc -DHOST_CHECK -w -O1 -g -c '{g}/game_bind.c' -o cg_bind.o")
r = subprocess.run(["wsl.exe", "-e", "sh", "-c", f"cd '{wsl(H)}' && " + " && ".join(cmds)], capture_output=True, text=True)
print(r.stdout[-400:], r.stderr[-1200:], "rebuilt", len(cmds) - 1, "chunks")
sys.exit(r.returncode)
