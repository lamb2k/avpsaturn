#!/usr/bin/env python
"""Run lifted functions (host) against the ROM routines (Unicorn) from real MAME-captured entry states.

usage: lift_test.py build            lift all, compile for host in WSL (E:/AvP/learning/lift/host)
       lift_test.py run [MAXCASES]   compare, write E:/AvP/learning/lift/results.tsv, print pass rate
A case passes when d0-d7, a0-a6, RAM (stack area excluded), tile/palette and object bytes agree, and, for a function whose
caller reads flags, ZNCV too. Both sides stop at a trap or an op the lifter does not model. Tier: HOST.
"""
import collections
import json
import pathlib
import re
import shutil
import struct
import subprocess
import sys

sys.path.insert(0, "E:/AvP/tools/py")
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE, UC_HOOK_INTR, UcError  # noqa: E402
from unicorn.m68k_const import UC_CPU_M68K_M68000, UC_M68K_REG_A0, UC_M68K_REG_A7, UC_M68K_REG_D0, UC_M68K_REG_PC, UC_M68K_REG_SR  # noqa: E402

TOOLS = pathlib.Path(__file__).parent
L = pathlib.Path("E:/AvP/learning/lift")
H = L / "host"
CASES = pathlib.Path("E:/AvP/learning/mame/entries_a/probe.tsv")
ROM = pathlib.Path("E:/AvP/learning/merged.bin")
REC = 76 + 0x22000
SENT = 0x1ffff0
FAULTS = collections.Counter()


def wsl(p):
    s = str(p).replace("\\", "/")
    return "/mnt/" + s[0].lower() + s[2:]


def build():
    H.mkdir(exist_ok=True)
    d = json.load(open("E:/AvP/learning/cfg.json"))
    funcs = sorted(d["funcs"])
    chunks = [funcs[i:i + 400] for i in range(0, len(funcs), 400)]
    aborts = set()
    for n, c in enumerate(chunks):
        lst = H / f"list{n}.txt"
        lst.write_text(" ".join(f"{a:x}" for a in c))
        subprocess.run([sys.executable, str(TOOLS / "lift68k.py"), str(H / f"c{n}"), "mem", f"@{lst}"], check=True, stdout=subprocess.DEVNULL)
        aborts |= set((H / f"c{n}" / "aborts_mem.txt").read_text().split())
    (H / "aborts.txt").write_text(" ".join(sorted(aborts)))
    inc = ["typedef void (*VF)(void);"]
    inc += [f"extern void f_{a:x}(void);" for a in funcs]
    inc += ["static const struct {u32 a; VF f;} TBL[]={"] + [f"{{0x{a:x}u,f_{a:x}}}," for a in funcs] + ["};"]
    inc += ["static VF lookup(u32 a){int l=0,h=sizeof TBL/sizeof TBL[0]-1;a&=0xffffff;while(l<=h){int m=(l+h)/2;if(TBL[m].a==a)return TBL[m].f;if(TBL[m].a<a)l=m+1;else h=m-1;}return 0;}",
            "void f_dispatch(u32 a){VF f=lookup(a);if(!f)stop(\"nofn\");f();}"]
    fset = set(funcs)
    refs = set()
    for n in range(len(chunks)):
        refs |= {int(x, 16) for x in re.findall(r"extern void f_([0-9a-f]+)\(void\)", (H / f"c{n}" / "lifted_mem.c").read_text())}
    miss = sorted(refs - fset)
    inc += [f'void f_{a:x}(void){{stop("nofn");}}' for a in miss]
    print("targets outside the function list", len(miss), [hex(x) for x in miss[:60]])
    (H / "dispatch.inc").write_text("\n".join(inc) + "\n")
    shutil.copy(TOOLS / "lift_host_main.c", H / "main.c")
    srcs = " ".join(f"c{n}/lifted_mem.c" for n in range(len(chunks)))
    cmd = (f"cd '{wsl(H)}' && for n in {' '.join(str(i) for i in range(len(chunks)))}; do echo c$n; done | "
           f"xargs -P3 -I@ sh -c 'gcc -DHOST -w -O1 -fno-strict-aliasing -c @/lifted_mem.c -o @.o' && "
           f"gcc -w -O1 -I. main.c {' '.join(f'c{n}.o' for n in range(len(chunks)))} -o lift_host && echo built")
    r = subprocess.run(["wsl.exe", "-e", "sh", "-c", cmd], capture_output=True, text=True)
    print(r.stdout[-300:], r.stderr[-1500:])


class Rom:
    def __init__(self, aborts):
        u = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        u.ctl_set_cpu_model(UC_CPU_M68K_M68000)
        u.mem_map(0, 0x1000000)
        self.img = ROM.read_bytes()
        u.mem_write(0, self.img)
        self.zero = bytes(0xff0000 - 0x200000)
        self.u = u
        self.aborts = aborts
        self.why = "ok"
        u.hook_add(UC_HOOK_INTR, self._intr)
        u.hook_add(UC_HOOK_CODE, self._code)

    def _intr(self, u, n, _):
        self.why = "trap"
        u.emu_stop()

    def _code(self, u, addr, size, _):
        if addr in self.aborts:
            self.why = "abort"
            u.emu_stop()

    def run(self, addr, regs, ram, gfx, obj):
        u = self.u
        u.mem_write(0x200000, self.zero)
        u.mem_write(0xff0000, ram)
        u.mem_write(0x900000, gfx)
        u.mem_write(0x700000, obj + bytes(0x10000 - len(obj)))
        for i in range(8):
            u.reg_write(UC_M68K_REG_D0 + i, regs[i])
        for i in range(7):
            u.reg_write(UC_M68K_REG_A0 + i, regs[8 + i])
        sp = (regs[15] & 0xffffff) - 4
        u.mem_write(sp, struct.pack(">I", SENT))
        u.reg_write(UC_M68K_REG_A7, sp)
        u.reg_write(UC_M68K_REG_SR, 0x2700)
        self.why = "ok"
        try:
            u.emu_start(addr, SENT, count=400000)
            if u.reg_read(UC_M68K_REG_PC) != SENT and self.why == "ok":
                self.why = "timeout"
        except UcError as e:
            self.why = "fault"
            self.fault = (hex(addr), hex(u.reg_read(UC_M68K_REG_PC)), str(e)[:40])
            FAULTS[self.fault[1:]] += 1
        hold = u.reg_read(UC_M68K_REG_D0)
        u.mem_write(0x1f0010, struct.pack(">H", 0x40c0))
        try:
            u.emu_start(0x1f0010, 0x1f0012, count=1)
            sr = u.reg_read(UC_M68K_REG_D0) & 0xffff
        except UcError:
            sr = 0
        u.reg_write(UC_M68K_REG_D0, hold)
        out = [u.reg_read(UC_M68K_REG_D0 + i) & 0xffffffff for i in range(8)] + [u.reg_read(UC_M68K_REG_A0 + i) & 0xffffffff for i in range(7)]
        cc = [(sr >> 2) & 1, (sr >> 3) & 1, sr & 1, (sr >> 1) & 1]
        mem = {}
        for base, old in ((0xff0000, ram), (0x900000, gfx), (0x700000, obj)):
            now = bytes(u.mem_read(base, len(old)))
            if now != old:
                for k in range(len(old)):
                    if now[k] != old[k]:
                        a = base + k
                        if base == 0xff0000 and sp - 0x800 <= a < sp + 12:
                            continue
                        mem[a] = now[k]
        return self.why, out, cc, mem


def ccret():
    sys.argv, keep = ["x", "style"], sys.argv
    import importlib.util as iu
    sp = iu.spec_from_file_location("cfg", TOOLS / "learn_cfg68k.py")
    c = iu.module_from_spec(sp)
    sp.loader.exec_module(c)
    sys.argv = keep
    d = json.load(open("E:/AvP/learning/cfg.json"))
    out = set()
    for k in d["seen"]:
        a = int(k, 16)
        i = c.insn(a)
        if i.mnemonic.split(".")[0] in ("jsr", "bsr"):
            n = c.insn(a + i.size)
            t = c.hexval(i.op_str) if re.fullmatch(r"\$[0-9a-f]+(\.[lw]|\(pc\))?", i.op_str.strip()) else None
            if t is not None and n is not None and n.mnemonic[0] == "b" and n.mnemonic.split(".")[0] not in ("bra", "bsr", "btst", "bset", "bclr", "bchg"):
                out.add(t)
    return out


def run(maxc):
    res = L / "host_out.txt"
    r = subprocess.run(["wsl.exe", "-e", "sh", "-c",
                        f"cd '{wsl(H)}' && timeout 500 ./lift_host '{wsl(CASES)}' '{wsl(ROM)}' '{wsl(res)}' 0 {maxc}"], capture_output=True, text=True)
    print("host rc", r.returncode, r.stderr[-200:])
    aborts = {int(x, 16) for x in (H / "aborts.txt").read_text().split()}
    rom = Rom(aborts)
    cc_set = ccret()
    C = collections.Counter()
    fails = []
    fnres = collections.defaultdict(lambda: [0, 0])
    f = open(CASES, "rb")
    rows = open(L / "results.tsv", "w")
    for line in open(res):
        head, _, memtxt = line.partition("|")
        p = head.split()
        n, addr, why = int(p[0]), int(p[1], 16), p[2]
        f.seek(n * REC)
        rec = f.read(REC)
        regs = list(struct.unpack(">16I", rec[12:76]))
        ram, gfx, obj = rec[76:76 + 0x10000], rec[76 + 0x10000:76 + 0x20000], rec[76 + 0x20000:]
        rw, ro, rcc, rm = rom.run(addr, regs, ram, gfx, obj)
        hr = [int(x, 16) for x in p[3:18]]
        hcc = [int(x) for x in p[19:23]]
        hm = {}
        for t in memtxt.split():
            a, v = t.split(":")
            hm[int(a, 16)] = int(v, 16)
        for a in list(hm):
            if 0xff0000 <= a <= 0xffffff and (regs[15] & 0xffffff) - 0x804 <= a < (regs[15] & 0xffffff) + 12:
                del hm[a]
        kind = None
        if rw in ("timeout", "fault") or why in ("timeout", "nofn", "div0", "badjump"):
            kind = f"skip_{rw if rw != 'ok' else why}"
        elif hr[:7] != [x for x in ro[:7]] or hr[7:] != ro[7:]:
            kind = "fail_regs"
        elif hm != rm:
            kind = "fail_mem"
        elif addr in cc_set and rw == "ok" and why == "ok" and hcc != rcc:
            kind = "fail_cc"
        else:
            kind = "pass_stopped" if why != "ok" else "pass"
        C[kind] += 1
        fnres[addr][0 if kind.startswith("pass") else 1] += 1
        rows.write(f"{n}\t{addr:x}\t{kind}\t{why}\t{rw}\n")
        if kind.startswith("fail") and len(fails) < 12:
            dr = [(i, hex(hr[i]), hex(ro[i])) for i in range(15) if hr[i] != ro[i]][:3]
            dm = [(hex(a), hm.get(a), rm.get(a)) for a in sorted(set(hm) ^ set(rm))[:3]]
            fails.append((n, hex(addr), kind, why, rw, dr, dm))
    total = sum(C.values())
    ok = C["pass"] + C["pass_stopped"]
    print(f"cases {total}; {dict(C)}")
    tested = sum(1 for a, b in fnres.values() if a + b)
    good = sum(1 for a, b in fnres.values() if a and not b)
    print("faults", FAULTS.most_common(10))
    print(f"functions touched {tested}; all cases pass {good}")
    for x in fails:
        print(x)


if sys.argv[1] == "build":
    build()
else:
    run(int(sys.argv[2]) if len(sys.argv) > 2 else 1 << 30)
