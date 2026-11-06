#!/usr/bin/env python
"""Semantics audit of the lifter (backlog item 8). Tier: HOST.

Every distinct instruction form in the reachable program, at up to SITES real sites, is lifted alone with all flags live, then run
on random registers and flags against the same instruction in Unicorn. Compares d0-d7, a0-a7, X N Z V C and changed RAM.
usage: lift_audit.py [good|bad]    bad sets LIFT_BAD=1 in the generator: deliberate defects, which the audit must catch.
"""
import collections
import json
import os
import pathlib
import random
import re
import struct
import subprocess
import sys

sys.path.insert(0, "E:/AvP/tools/py")
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UcError  # noqa: E402
from unicorn.m68k_const import UC_CPU_M68K_M68000, UC_M68K_REG_A0, UC_M68K_REG_A7, UC_M68K_REG_D0, UC_M68K_REG_SR  # noqa: E402

TOOLS = pathlib.Path(__file__).parent
W = pathlib.Path("E:/AvP/learning/lift/audit")
W.mkdir(parents=True, exist_ok=True)
SITES, CASES = 4, 12
variant = sys.argv[1] if len(sys.argv) > 1 else "good"
if variant == "bad":
    os.environ["LIFT_BAD"] = "1"
keep = sys.argv
sys.argv = ["lift68k", str(W), "mem", "0"]
import importlib.util as iu
sp = iu.spec_from_file_location("lift68k", TOOLS / "lift68k.py")
lf = iu.module_from_spec(sp)
sp.loader.exec_module(lf)
sys.argv = keep
cfg = lf.cfg
SKIP = {"bra", "bsr", "jsr", "jmp", "rts", "rte", "rtr", "trap", "stop", "nop", "illegal", "reset", "dc"}
ALLF = set("zncvx")


def shape(op):
    if op.startswith("#"):
        return "imm"
    if re.fullmatch(r"d[0-7]", op):
        return "d"
    if re.fullmatch(r"a[0-7]", op):
        return "a"
    if op in ("sr", "ccr", "usp"):
        return op
    if op.endswith(")+"):
        return "(a)+"
    if op.startswith("-("):
        return "-(a)"
    if "(pc" in op:
        return "pcx" if "," in op else "pc"
    if "," in op:
        return "ix"
    if "(a" in op:
        return "(a5)" if "(a5)" in op else ("d(a)" if op[0] != "(" else "(a)")
    if op.endswith(".w"):
        return "abs.w"
    if op.endswith(".l"):
        return "abs.l"
    return "reg-list" if "/" in op or "-" in op else "?"


def forms():
    out = collections.defaultdict(list)
    for a in sorted(lf.SEEN):
        i = cfg.insn(a)
        m = i.mnemonic.split(".")[0]
        if m in SKIP or (m[0] == "b" and m[1:] in lf.FLAGS_OF) or m.startswith("db"):
            continue
        key = i.mnemonic + " " + ",".join(shape(o) for o in lf.split_ops(i.op_str))
        out[key].append(a)
    return out


def lift_one(a):
    i = cfg.insn(a)
    m0 = i.mnemonic
    m = m0.split(".")[0]
    sz = {"b": 1, "w": 2, "l": 4}.get(m0.split(".")[1] if "." in m0 else "")
    fn = lf.Fn(a)
    st = lf.emit(fn, a, i, m, sz, ALLF, set(), a)
    defs = "".join(f"#define {r} (R->{r[0]}[{r[1]}])\n" for r in sorted(fn.regs))
    und = "".join(f"#undef {r}\n" for r in sorted(fn.regs))
    return defs + f"void i_{a:x}(void){{int fz=R->ccz,fn=R->ccn,fc=R->ccc,fv=R->ccv,fx=R->ccx;{{{st}}}CCOUT();}}\n" + und


def main():
    F = forms()
    rng = random.Random(68000)
    chosen = []
    src = [lf.HEADER]
    dropped = []
    for key, sites in sorted(F.items()):
        got = 0
        for a in rng.sample(sites, min(len(sites), SITES)):
            try:
                t = lift_one(a)
            except ValueError:
                dropped.append((key, f"{a:x}"))
                continue
            src.append(t)
            chosen.append((key, a))
            got += 1
    (W / f"audit_{variant}.c").write_text("".join(src) + "typedef void(*VF)(void);\nconst struct{u32 a;VF f;}ITAB[]={" + "".join(f"{{0x{a:x}u,i_{a:x}}}," for _, a in chosen) + "{0,0}};\n")
    ram = bytes(rng.randrange(256) if k % 3 else 0 for k in range(0x10000))
    (W / "ram.bin").write_bytes(ram)
    vals = [0, 1, 2, 7, 8, 16, 31, 32, 33, 0xff, 0x80, 0x7f, 0xffff, 0x8000, 0x7fff, 0xffffffff, 0x80000000, 0x7fffffff, 0x10000]
    cases = []
    for key, a in chosen:
        for _ in range(CASES):
            d = [rng.choice(vals) if rng.random() < .6 else rng.getrandbits(32) for _ in range(8)]
            ar = [0xff1000 + 2 * rng.randrange(0x3000) for _ in range(7)] + [0xff0f00]
            ar[5] = 0xff8000
            cases.append((key, a, d, ar, rng.randrange(32)))
    (W / "cases.txt").write_text("".join(f"{a:x} " + " ".join(f"{x:x}" for x in d + ar) + f" {f}\n" for _, a, d, ar, f in cases))
    wsl = "/mnt/e/AvP/learning/lift/audit"
    cmd = (f"cd {wsl} && cp '/mnt/e/AvP/worktrees/decomp-main/tools/lift_audit_main.c' m.c && gcc -DHOST -DLIFT_TEST -w -O1 -fno-strict-aliasing -c audit_{variant}.c -o a_{variant}.o && "
           f"gcc -w -O1 m.c a_{variant}.o -o a_{variant} && ./a_{variant} ram.bin /mnt/e/AvP/learning/merged.bin cases.txt > out_{variant}.txt")
    r = subprocess.run(["wsl.exe", "-e", "sh", "-c", cmd], capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-1500:])
        sys.exit(2)
    u = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
    u.ctl_set_cpu_model(UC_CPU_M68K_M68000)
    u.mem_map(0, 0x1000000)
    u.mem_write(0, pathlib.Path("E:/AvP/learning/merged.bin").read_bytes())
    bad = collections.Counter()
    tot = collections.Counter()
    ex = {}
    for (key, a, d, ar, fl), line in zip(cases, open(W / f"out_{variant}.txt")):
        head, _, memtxt = line.partition("|")
        p = head.split()
        hreg = [int(x, 16) for x in p[1:17]]
        hf = int(p[17])
        u.mem_write(0xff0000, ram)
        for i in range(8):
            u.reg_write(UC_M68K_REG_D0 + i, d[i])
        for i in range(7):
            u.reg_write(UC_M68K_REG_A0 + i, ar[i])
        u.reg_write(UC_M68K_REG_A7, ar[7])
        # Unicorn's SR register view is stale for lazily computed flags, so set and read them with real instructions.
        u.mem_write(0x1f0000, struct.pack(">HH", 0x46fc, 0x2700 | fl))
        u.reg_write(UC_M68K_REG_SR, 0x2700)
        u.emu_start(0x1f0000, 0x1f0004, count=1)
        ins = cfg.insn(a)
        tot[key] += 1
        if p[0] != "ok":
            bad[key] += 0
            tot["_stopped"] += 1
            continue
        try:
            u.emu_start(a, a + ins.size, count=1)
        except UcError:
            tot["_uc_fault"] += 1
            continue
        ureg = [u.reg_read(UC_M68K_REG_D0 + i) & 0xffffffff for i in range(8)] + [u.reg_read(UC_M68K_REG_A0 + i) & 0xffffffff for i in range(8)]
        hold = u.reg_read(UC_M68K_REG_D0)
        u.mem_write(0x1f0010, struct.pack(">H", 0x40c0))
        u.emu_start(0x1f0010, 0x1f0012, count=1)
        uf = u.reg_read(UC_M68K_REG_D0) & 31
        u.reg_write(UC_M68K_REG_D0, hold)
        now = bytes(u.mem_read(0xff0000, 0x10000))
        um = {0xff0000 + k: now[k] for k in range(0x10000) if now[k] != ram[k]}
        hm = {}
        for t in memtxt.split():
            x, v = t.split(":")
            hm[int(x, 16)] = int(v, 16)
        m = ins.mnemonic.split(".")[0]
        mask = 31
        if m in ("abcd", "sbcd"):
            mask = 0b10101
        if m in ("divu", "divs"):
            mask = 0b00011
        if ureg != hreg or (uf & mask) != (hf & mask) or um != hm:
            bad[key] += 1
            ex.setdefault(key, (f"{a:x}", ins.op_str, [hex(x) for x in d[:3]], f"flags in {fl:05b} out u {uf:05b} h {hf:05b}",
                                [(i, hex(hreg[i]), hex(ureg[i])) for i in range(16) if hreg[i] != ureg[i]][:2], sorted(set(um.items()) ^ set(hm.items()))[:2]))
    forms_n = len({k for k, _ in chosen})
    fbad = sum(1 for k in bad if bad[k])
    ncases = sum(v for k, v in tot.items() if not k.startswith("_"))
    print(f"variant {variant}: forms {forms_n}, sites {len(chosen)}, cases {ncases}, stopped {tot['_stopped']}, uc faults {tot['_uc_fault']}, failing cases {sum(bad.values())}, failing forms {fbad}; not liftable {len(dropped)} {dropped[:30]}")
    for k, v in bad.most_common(40):
        if v:
            print(f"  {k}: {v}/{tot[k]}", ex.get(k))


main()
