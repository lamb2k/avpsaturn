#!/usr/bin/env python
"""Unit gate: run a ROM routine under Unicorn and its C reconstruction on the same random inputs.

usage: learn_unit.py UNIT|all [CASES] [--no-record]
Compares all changed RAM and palette bytes, and the ordered stubbed calls. Prints PASS/FAIL per unit.
Every run appends one row per unit to E:/AvP/learning/gate_runs.tsv, FAIL included:
time, unit, entry, cases, bad, changed, PASS|FAIL, commit, worktree. The last row of a unit is its state.
--no-record is for runs on deliberately wrong source (mutations); they must never reach that file.

Work files go to E:/AvP/learning/<worktree name>, or AVP_GATE_WORK, so lanes never share an input file.

ROM side: E:/AvP/learning/merged.bin, built by tools/make_merged.py; this tool only reads it. The lifted runtime
uses rt.bin and op.bin instead, because it knows which space each read goes through. Here one image serves all
reads, so a gate whose routine reads pc-relative data merged.bin leaves out lists it in OP_READS.
A gate is source_recon/gates/*.py with SOURCES, UNITS (entry, stubs, input generator) and these optional hooks:
  OP_READS = [(addr, size)]            overlaid from op.bin, for this gate only
  setup(rom)                           maps ranges, sets rom.extra, rom.ignore, rom.stack
  after_run(rom, regs, out, calls)     returns (out, calls), to report results that are not in memory
Hooks apply to their own gate only. Tier label: unicorn-differential. It is not a MAME or console result.
"""
import importlib.util
import os
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
LEARN = pathlib.Path("E:/AvP/learning")
WORK = pathlib.Path(os.environ.get("AVP_GATE_WORK") or LEARN / REPO.name)
SENTINEL = 0x1ffff0
STACK = 0xff0f00
RAM = (0xff0000, 0x10000)
PAL = (0x900000, 0x10000)
OBJ = (0x700000, 0x10000)
IO = (0x800000, 0x10000)


def _image(name):
    p = LEARN / name
    if not p.exists():
        sys.exit(f"{p} is missing: run tools/make_merged.py")
    return p.read_bytes()


IMG = _image("merged.bin")
OP = _image("op.bin")


def overlay(reads):
    """The merged image with these ranges read through opcode space. Private to the caller."""
    img = bytearray(IMG)
    for a, n in reads:
        img[a:a + n] = OP[a:a + n]
    return bytes(img)


class Rom:
    def __init__(self, image=IMG, after_run=None):
        u = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        u.ctl_set_cpu_model(UC_CPU_M68K_M68000)
        u.mem_map(0, 0x200000)
        u.mem_write(0, image)
        for b, n in (RAM, PAL, OBJ, IO):
            u.mem_map(b, n)
        self.u = u
        self.calls = []
        self.stubs = {}
        self.extra = []                # optional ranges from a gate module's setup()
        self.ignore = []
        self.stack = STACK             # a gate whose RAM sits near the default stack moves it
        self.after_run = after_run
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
        if self.after_run:
            return self.after_run(self, regs, out, list(self.calls))
        return out, list(self.calls)


def load_unit(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def wsl(path):
    s = str(path).replace("\\", "/")
    return "/mnt/" + s[0].lower() + s[2:]


def commit():
    r = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"], capture_output=True, text=True)
    d = subprocess.run(["git", "-C", str(REPO), "status", "--porcelain", "--", "source_recon", "tools/learn_unit.py"],
                       capture_output=True, text=True)
    return r.stdout.strip() + ("+dirty" if d.stdout.strip() else "")


def run_group(gatefile, only, cases, record):
    mod = load_unit(gatefile)
    if only and only not in mod.UNITS:
        return {}
    rom = Rom(overlay(getattr(mod, "OP_READS", ())), getattr(mod, "after_run", None))
    if hasattr(mod, "setup"):
        mod.setup(rom)
    WORK.mkdir(parents=True, exist_ok=True)
    exe = WORK / (gatefile.stem + ".bin")
    inp = WORK / (gatefile.stem + ".in.txt")
    srcs = " ".join(f"'{wsl(REPO / 'source_recon' / s)}'" for s in mod.SOURCES)
    cmd = (f"gcc -std=c90 -pedantic -Wall -Wextra -Werror -Wno-unused-result -Wno-unused-function -O1 -I'{wsl(REPO / 'source_recon')}' "
           f"'{wsl(gatefile.with_suffix('.c'))}' {srcs} -o '{wsl(exe)}'")
    subprocess.run(["wsl.exe", "-e", "sh", "-c", cmd], check=True)
    rev = commit()
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
        inp.write_text("\n".join(lines) + "\n")
        r = subprocess.run(["wsl.exe", "-e", "sh", "-c", f"'{wsl(exe)}' < '{wsl(inp)}'"],
                           capture_output=True, text=True)
        got = r.stdout.splitlines()     # a crash in the C is a FAIL of this unit, not a harness error
        bad = 0
        first = None
        for i, (exp, line) in enumerate(zip(expect, got)):
            mem, calls = parse(line)
            if mem != exp[0] or calls != exp[1]:
                bad += 1
                if first is None:
                    first = (i, lines[i][:200], [e for e in exp[0] if e not in mem][:6], [e for e in mem if e not in exp[0]][:6], exp[1][:4], calls[:4])
        changed = sum(1 for e in expect if e[0])
        ok = r.returncode == 0 and bad == 0 and len(got) == cases and changed > 0
        results[name] = ok
        print(f"{'PASS' if ok else 'FAIL'} {name} entry={unit['entry']:x} cases={cases} changed={changed} bad={bad}")
        if first:
            print("  first:", first)
        if r.returncode:
            print(f"  C side exit {r.returncode}, {len(got)} of {cases} lines")
        if record:
            # A crash reports its missing lines as bad, so the ledger's bad == 0 test agrees with the verdict.
            shown = bad if ok or bad else max(1, cases - len(got))
            with open(LEARN / "gate_runs.tsv", "a") as f:
                f.write(f"{time.strftime('%F %T')}\t{name}\t{unit['entry']:x}\t{cases}\t{shown}\t{changed}\t"
                        f"{'PASS' if ok else 'FAIL'}\t{rev}\t{REPO.name}\n")
    return results


def parse(line):
    mem, calls = [], []
    for tok in line.split():
        kind, a, v = tok.split(":")
        (mem if kind == "m" else calls).append((int(a, 16), int(v, 16)))
    return sorted(mem), calls


if __name__ == "__main__":
    argv = [x for x in sys.argv[1:] if x != "--no-record"]
    record = len(argv) == len(sys.argv) - 1
    only = None if argv[0] == "all" else argv[0]
    cases = int(argv[1]) if len(argv) > 1 else 500
    results = {}
    for g in sorted((REPO / "source_recon" / "gates").glob("*.py")):
        results.update(run_group(g, only, cases, record))
    if not results:
        sys.exit(f"no such unit: {only}")
    print(f"{sum(results.values())} passed, {sum(not v for v in results.values())} failed, tier unicorn-differential (HOST)")
    sys.exit(0 if all(results.values()) else 1)
