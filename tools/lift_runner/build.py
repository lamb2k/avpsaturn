#!/usr/bin/env python
"""Lift all functions and build the host runner under E:/AvP/learning/lift/run. Output is ROM-derived and stays on this PC."""
import json, pathlib, re, subprocess, sys
T = pathlib.Path(__file__).resolve().parents[1]
H = pathlib.Path("E:/AvP/learning/lift/run"); H.mkdir(parents=True, exist_ok=True)
d = json.load(open("E:/AvP/learning/cfg.json"))
funcs = sorted(a for a in d["funcs"] if a != 0xd86)
groups = {}
for a in funcs:
    groups.setdefault(a >> 15, []).append(a)
chunks = [groups[k] for k in sorted(groups)]
refs = set()
for n, c in enumerate(chunks):
    l = H / f"list{n}.txt"; l.write_text(" ".join(f"{a:x}" for a in c))
    src = H/f"c{n}"/"lifted_mem.c"
    old = src.read_bytes() if src.exists() else b""
    subprocess.run([sys.executable, str(T/"lift68k.py"), str(H/f"c{n}"), "mem", f"@{l}"], check=True, stdout=subprocess.DEVNULL)
    if src.read_bytes() != old:
        (H/f"c{n}.o").unlink(missing_ok=True)
    refs |= {int(x,16) for x in re.findall(r"extern void f_([0-9a-f]+)\(void\)", (H/f"c{n}"/"lifted_mem.c").read_text())}
miss = sorted(refs - set(funcs) - {0xd86})
inc = ["typedef void (*VF)(void);"] + [f"extern void f_{a:x}(void);" for a in funcs] + ["extern void f_d86(void);","static const struct {u32 a; VF f;} TBL[]={"] + [f"{{0x{a:x}u,f_{a:x}}}," for a in sorted(funcs+[0xd86])] + ["};",
 "static VF lookup(u32 a){int l=0,h=sizeof TBL/sizeof TBL[0]-1;a&=0xffffff;while(l<=h){int m=(l+h)/2;if(TBL[m].a==a)return TBL[m].f;if(TBL[m].a<a)l=m+1;else h=m-1;}return 0;}"]
inc += [f'void f_{a:x}(void){{puts("MISSING {a:x}");fflush(stdout);exit(3);}}' for a in miss]
(H/"dispatch.inc").write_text("\n".join(inc)+"\n")
print("missing", len(miss))
w = "/mnt/e/AvP/learning/lift/run"
_h = (T / "lift_runner/host_kernel.c").as_posix()
main = "/mnt/" + _h[0].lower() + _h[2:]
cmd = f"cd {w} && for n in {' '.join(map(str,range(len(chunks))))}; do echo c$n; done | xargs -P3 -I@ sh -c 'test -f @.o || gcc -DHOST -DPREEMPT -w -O1 -g -fno-strict-aliasing -c @/lifted_mem.c -o @.o' && gcc -w -O1 -g -rdynamic -I. '{main}' {' '.join(f'c{n}.o' for n in range(len(chunks)))} -o lift_runner && echo built"
r = subprocess.run(["wsl.exe","-e","sh","-c",cmd],capture_output=True,text=True); print(r.stdout[-200:], r.stderr[-1200:])
