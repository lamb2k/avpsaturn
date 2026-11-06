#!/usr/bin/env python
"""Unit gate: run a ROM routine under Unicorn and its C reconstruction on the same random inputs.

usage: learn_unit.py UNIT [CASES]   |   learn_unit.py all [CASES]
Compares all changed RAM and palette bytes, and the ordered stubbed calls. Prints PASS/FAIL per unit
and appends to E:/AvP/learning/gate_runs.tsv. The ROM side is run from a merged image: instruction
bytes from the decrypted opcode image, data from the decrypted program image, as the board fetches.
A unit is defined in source_recon/gates/*.py with: entry, stubs, a generator of inputs, the C call.
Tier label: unicorn-differential. It is not a MAME or console result.
"""
import importlib.util
import json
import pathlib
import random
import struct
import subprocess
import sys
import time

sys.path.insert(0, "E:/AvP/tools/py")
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE, UC_HOOK_MEM_WRITE  # noqa: E402
from unicorn.m68k_const import UC_CPU_M68K_M68000, UC_M68K_REG_A0, UC_M68K_REG_A7, UC_M68K_REG_D0, UC_M68K_REG_PC, UC_M68K_REG_SR  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parents[1]
DEPS = pathlib.Path("C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-playable-loop-pivot/.deps/mame/actorprobe")
LEARN = pathlib.Path("E:/AvP/learning")
SENTINEL = 0x1ffff0
STACK = 0xff0f00
RAM = (0xff0000, 0x10000)
PAL = (0x900000, 0x10000)
OBJ = (0x700000, 0x10000)
IO = (0x800000, 0x10000)


def merged():
    p = LEARN / "merged.bin"
    if p.exists():
        return p.read_bytes()
    op = (DEPS / "decrypted_opcodes_2m.bin").read_bytes()
    img = bytearray((DEPS / "decrypted_program_2m.bin").read_bytes())
    d = json.load(open(LEARN / "cfg.json"))
    for k, n in d["seen"].items():
        a = int(k, 16)
        img[a:a + n] = op[a:a + n]
    for k, tg in d["tables"].items():
        a = int(k, 16)                 # pc-relative tables are read through the opcode space
        n = len(tg) * 4
        img[a:a + n] = op[a:a + n]
    p.write_bytes(img)
    return bytes(img)


IMG = merged()


class Rom:
    def __init__(self):
        u = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        u.ctl_set_cpu_model(UC_CPU_M68K_M68000)
        u.mem_map(0, 0x200000)
        u.mem_write(0, IMG)
        for b, n in (RAM, PAL, OBJ, IO):
            u.mem_map(b, n)
        self.u = u
        self.calls = []
        self.stubs = {}
        self.extra = []                # optional ranges from a gate module's setup()
        self.ignore = []
        self.stack = STACK             # a gate whose RAM sits near the default stack moves it
        u.hook_add(UC_HOOK_CODE, self._code)

    def _code(self, u, addr, size, _):
        if addr in self.stubs:
            self.calls.append((addr, u.reg_read(UC_M68K_REG_D0) & 0xffffffff))
            sp = u.reg_read(UC_M68K_REG_A7)
            ret = struct.unpack(">I", u.mem_read(sp, 4))[0]
            u.reg_write(UC_M68K_REG_A7, sp + 4)
            u.reg_write(UC_M68K_REG_PC, ret)

    def run(self, entry, stubs, regs, seeds):
        u = self.u
        u.mem_write(RAM[0], bytes(RAM[1]))
        u.mem_write(PAL[0], bytes(PAL[1]))
        for b, n in self.extra:
            u.mem_write(b, bytes(n))
        for a, v in seeds:
            u.mem_write(a, bytes([v]))
        ranges = [RAM, PAL] + list(self.extra)
        self.before = {b: bytes(u.mem_read(b, n)) for b, n in ranges}
        self.stubs = set(stubs)
        self.calls = []
        for i in range(8):
            u.reg_write(UC_M68K_REG_D0 + i, regs.get(f"d{i}", 0))
        for i in range(7):
            u.reg_write(UC_M68K_REG_A0 + i, regs.get(f"a{i}", 0xff8000 if i == 5 else 0))
        u.reg_write(UC_M68K_REG_SR, 0x2700)
        u.mem_write(self.stack, struct.pack(">I", SENTINEL))
        u.reg_write(UC_M68K_REG_A7, self.stack)
        u.emu_start(entry, SENTINEL, count=2000000)
        out = {}
        for b, n in ranges:
            now = bytes(u.mem_read(b, n))
            old = self.before[b]
            if now != old:
                for i in range(n):
                    if now[i] != old[i]:
                        if not (self.stack - 0x100 <= b + i < self.stack + 4) and not any(lo <= b + i < hi for lo, hi in self.ignore):
                            out[b + i] = now[i]
        return out, list(self.calls)


def load_unit(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def wsl(path):
    s = str(path).replace("\\", "/")
    return "/mnt/" + s[0].lower() + s[2:]


def run_group(gatefile, only, cases):
    mod = load_unit(gatefile)
    rom = Rom()
    if hasattr(mod, "setup"):
        mod.setup(rom)
    work = LEARN / "gate_work"
    work.mkdir(exist_ok=True)
    exe = work / (gatefile.stem + ".bin")
    srcs = " ".join(f"'{wsl(REPO / 'source_recon' / s)}'" for s in mod.SOURCES)
    cmd = (f"gcc -std=c90 -pedantic -Wall -Wextra -Werror -Wno-unused-result -Wno-unused-function -O1 -I'{wsl(REPO / 'source_recon')}' "
           f"'{wsl(gatefile.with_suffix('.c'))}' {srcs} -o '{wsl(exe)}'")
    subprocess.run(["wsl.exe", "-e", "sh", "-c", cmd], check=True)
    results = {}
    for name, unit in mod.UNITS.items():
        if only and name != only:
            continue
        rng = random.Random(0xA5F0 ^ unit["entry"])
        lines, expect = [], []
        for _ in range(cases):
            regs, seeds = unit["gen"](rng)
            out, calls = rom.run(unit["entry"], unit.get("stubs", ()), regs, seeds)
            expect.append((sorted(out.items()), calls))
            args = " ".join(f"{regs.get(k, 0):x}" for k in [f"d{i}" for i in range(8)] + [f"a{i}" for i in range(7)])
            lines.append(f"{name} {args} {len(seeds)} " + " ".join(f"{a:x} {v:x}" for a, v in seeds))
        (work / "in.txt").write_text("\n".join(lines) + "\n")
        r = subprocess.run(["wsl.exe", "-e", "sh", "-c", f"'{wsl(exe)}' < '{wsl(work / 'in.txt')}'"],
                           capture_output=True, text=True, check=True)
        got = r.stdout.splitlines()
        bad = 0
        first = None
        for i, (exp, line) in enumerate(zip(expect, got)):
            mem, calls = parse(line)
            if mem != exp[0] or calls != exp[1]:
                bad += 1
                if first is None:
                    first = (i, lines[i][:200], [e for e in exp[0] if e not in mem][:6], [e for e in mem if e not in exp[0]][:6], exp[1][:4], calls[:4])
        changed = sum(1 for e in expect if e[0])
        ok = bad == 0 and len(got) == cases and changed > 0
        results[name] = ok
        print(f"{'PASS' if ok else 'FAIL'} {name} entry={unit['entry']:x} cases={cases} changed={changed} bad={bad}")
        if first:
            print("  first:", first)
        with open(LEARN / "gate_runs.tsv", "a") as f:
            f.write(f"{time.strftime('%F %T')}\t{name}\t{unit['entry']:x}\t{cases}\t{bad}\t{changed}\n")
    return results


def parse(line):
    mem, calls = [], []
    for tok in line.split():
        kind, a, v = tok.split(":")
        (mem if kind == "m" else calls).append((int(a, 16), int(v, 16)))
    return sorted(mem), calls


if __name__ == "__main__":
    only = None if sys.argv[1] == "all" else sys.argv[1]
    cases = int(sys.argv[2]) if len(sys.argv) > 2 else 500
    bad = False
    for g in sorted((REPO / "source_recon" / "gates").glob("*.py")):
        r = run_group(g, only, cases)
        bad |= not all(r.values())
    sys.exit(1 if bad else 0)
