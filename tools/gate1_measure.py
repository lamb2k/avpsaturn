#!/usr/bin/env python
"""First gate: SH-2 size and modelled tick cost of the lifted program. Results to stdout and E:/AvP/learning/lift/gate1.json.

usage: gate1_measure.py MODE     (mem or local; lifts all functions, compiles in chunks with SH-2 GCC -O2)
Cycle model, MODELLED, not a Saturn timing: alu/store 1, load 2, branch 2, call/return 3 per executed SH-2 instruction,
static mix of each function, weighted by the 68000 instruction counts MAME executed (exec_a probe). Cache low/high: x1.0 / x1.6.
"""
import collections
import concurrent.futures as cf
import json
import os
import pathlib
import random
import re
import subprocess
import sys

B = r"C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest-playable-loop-pivot\.deps\joengine\Compiler\WINDOWS"
L = pathlib.Path("E:/AvP/learning/lift")
ENV = dict(os.environ, PATH=rf"{B}\bin;{B}\sh-elf\bin;" + os.environ["PATH"])
mode = sys.argv[1]
TOOLS = pathlib.Path(__file__).parent
cfgd = json.load(open("E:/AvP/learning/cfg.json"))
FUNCS = sorted(cfgd["funcs"])
SEEN = {int(k, 16): v for k, v in cfgd["seen"].items()}
CHUNK = 400


def compile_chunk(n):
    s = L / f"c{mode}{n}.s"
    r = subprocess.run([rf"{B}\bin\sh-elf-gcc.exe", "-m2", "-O2", "-ffixed-r14", "-w", "-S", f"chunk{mode}{n}/lifted_{mode}.c", "-o", str(s)],
                       cwd=L, env=ENV, capture_output=True, text=True)
    return n, r.returncode, r.stderr[:300]


def parse(path):
    """Per function: instruction counts by class, and bytes (2 per instruction, 4 per .long, 2 per .short)."""
    out = {}
    cur = None
    for line in open(path):
        m = re.match(r"_f_([0-9a-f]+):", line)
        if m:
            cur = out.setdefault(int(m[1], 16), collections.Counter())
            continue
        if cur is None or not line.startswith("\t"):
            continue
        t = line.split()
        if not t:
            continue
        op = t[0]
        if op == ".long":
            cur["bytes"] += 4
        elif op == ".short":
            cur["bytes"] += 2
        elif op.startswith("."):
            continue
        else:
            cur["bytes"] += 2
            cur["insns"] += 1
            args = " ".join(t[1:])
            if op in ("rts", "jsr", "jmp", "bsr", "bsrf", "braf"):
                cur["cyc"] += 3
            elif op in ("bt", "bf", "bt.s", "bf.s", "bra", "bt/s", "bf/s"):
                cur["cyc"] += 2
            elif op.startswith("mov") and re.match(r"@", args):
                cur["cyc"] += 2
            elif op.startswith("mul") or op.startswith("dmul"):
                cur["cyc"] += 2
            else:
                cur["cyc"] += 1
    return out


def body68k(addrs):
    """Reachable 68000 bytes and instructions per function, each instruction owned by the nearest function at or below."""
    return None


chunks = [FUNCS[i:i + CHUNK] for i in range(0, len(FUNCS), CHUNK)]
for n, c in enumerate(chunks):
    (L / f"list{n}.txt").write_text(" ".join(f"{a:x}" for a in c))
    if not (L / f"chunk{mode}{n}" / f"lifted_{mode}.c").exists():
        subprocess.run([sys.executable, str(TOOLS / "lift68k.py"), str(L / f"chunk{mode}{n}"), mode, f"@{L / f'list{n}.txt'}"],
                       check=True, stdout=subprocess.DEVNULL)
with cf.ThreadPoolExecutor(3) as ex:
    res = list(ex.map(compile_chunk, range(len(chunks))))
fail = [r for r in res if r[1]]
print("chunks", len(chunks), "failed", len(fail), fail[:2])
stats = collections.Counter()
unh = collections.Counter()
per = {}
for n in range(len(chunks)):
    if res[n][1] == 0:
        per.update(parse(L / f"c{mode}{n}.s"))
    st = json.load(open(L / f"chunk{mode}{n}" / f"stats_{mode}.json"))
    stats.update(st["stats"])
    unh.update(dict(st["unhandled"]))

# Each instruction belongs to the nearest function entry at or below it (bodies shared by branches count once).
import bisect
entries = sorted(per)
own = collections.defaultdict(lambda: [0, 0])
owner = {}
for a, n in SEEN.items():
    i = bisect.bisect_right(entries, a) - 1
    if i >= 0:
        e = entries[i]
        own[e][0] += n
        own[e][1] += 1
        owner[a] = e
tot68 = sum(v[0] for v in own.values())
totsh = sum(c["bytes"] for c in per.values())
print(f"68000 reachable bytes {sum(SEEN.values())}, functions compiled {len(per)}, 68000 bytes in them {tot68}")
print(f"ALL: SH-2 bytes {totsh}, ratio {totsh / tot68:.2f} SH-2 bytes per 68000 byte")
rng = random.Random(1994)
sample = rng.sample([e for e in entries if own[e][0]], 300)
s68 = sum(own[e][0] for e in sample)
ssh = sum(per[e]["bytes"] for e in sample)
print(f"SAMPLE 300: 68000 {s68} SH-2 {ssh} ratio {ssh / s68:.2f}")
print("stats", dict(stats), "unhandled", unh.most_common(12))

# Execution weighting
counts, frames = {}, {}
for line in open("E:/AvP/learning/mame/exec_a/probe.tsv"):
    p = line.split()
    if p[0] == "F":
        frames[int(p[1])] = int(p[2])
    else:
        counts[int(p[0], 16)] = int(p[1])
exec_words = sum(counts.values())
fr = sorted(n for f, n in frames.items() if f >= 2000)
cov_bytes = sum(SEEN[a] for a in counts if a in SEEN)
cov_sh = 0
f_cov = {}
for a in counts:
    if a in owner:
        f_cov[owner[a]] = 1
cov_sh = sum(per[e]["bytes"] for e in f_cov if e in per)
print(f"route code functions touched {len(f_cov)}, their SH-2 bytes {cov_sh}, executed 68000 bytes {cov_bytes}")
perfn = collections.Counter()
ins68 = 0
for a, c in counts.items():
    if a in owner:
        e = owner[a]
        k = own[e][1] or 1
        pc = per.get(e)
        if pc and pc["insns"]:
            perfn[e] += c * (pc["cyc"] / k)
        ins68 += c
base = sum(perfn.values())
print(f"route 68000 instructions {ins68}, words {exec_words}; base model cycles per 68000 instruction {base / ins68:.2f}")
words_per_ins = exec_words / ins68
for name, w in (("mean", sum(fr) / len(fr)), ("p95", fr[int(len(fr) * .95)]), ("max", fr[-1])):
    ins = w / words_per_ins
    cyc = ins * base / ins68
    print(f"tick {name}: {w:.0f} words, {ins:.0f} 68000 ins; SH-2 MODELLED {cyc:.0f} cycles low, {cyc * 1.6:.0f} high; "
          f"{cyc / 28.636e6 * 1000:.1f} to {cyc * 1.6 / 28.636e6 * 1000:.1f} ms at 28.636 MHz")
top = perfn.most_common()
acc = 0
for k in (10, 50, 100, 200, 500):
    print(f"hottest {k}: {100 * sum(v for _, v in top[:k]) / base:.1f}% of modelled cycles")
print("hottest", [(hex(e), round(100 * v / base, 1)) for e, v in top[:12]])
print(f"frames>=2000: {len(fr)}")
json.dump(dict(totsh=totsh, tot68=tot68, base=base, ins68=ins68), open(L / f"gate1_{mode}.json", "w"))
