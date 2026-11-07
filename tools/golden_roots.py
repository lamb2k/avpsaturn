#!/usr/bin/env python
"""Candidate code roots from the census: opcode-space words MAME read that the code map has not seen. A run counts as code when capstone decodes it from its first word
through its whole length. Others are pc-relative data. usage: golden_roots.py RAW CFG_JSON [--add]    env LEARN_OUT as learn_cfg68k. Adds to tools/roots.txt with --add."""
import json, pathlib, sys
sys_argv = sys.argv
sys.argv = ["x", "style"]
import importlib.util as iu
sp = iu.spec_from_file_location("cfg", pathlib.Path(__file__).parent / "learn_cfg68k.py")
c = iu.module_from_spec(sp)
sp.loader.exec_module(c)
sys.argv = sys_argv
seen = set()
for k, n in json.load(open(sys.argv[2]))["seen"].items():
    a = int(k, 16)
    seen.update(a + i for i in range(0, n, 2))
op = set()
for l in open(sys.argv[1]):
    if l[0] == "O":
        op.add(int(l.split()[1], 16))
un = sorted(op - seen)
runs, s, p = [], None, None
for a in un:
    if s is None:
        s = p = a
    elif a == p + 2:
        p = a
    else:
        runs.append((s, p + 2))
        s = p = a
if s is not None:
    runs.append((s, p + 2))
code, data = [], []
for b, e in runs:
    a, ok, term = b, True, False
    while a < e - 2:
        i = c.insn(a)
        if i is None:
            ok = False
            break
        a += i.size
        if i.mnemonic in ("rts", "rte", "jmp", "bra", "bra.b", "bra.w", "bra.s", "trap"):
            term = True
    ok = ok and term
    (code if ok and e - b >= 16 else data).append((b, e))
print("opcode words", len(op), "unseen", len(un), "runs", len(runs), "code-like", len(code), "data-like", len(data))
print("code", " ".join(f"{b:x}-{e:x}" for b, e in code[:60]))
print("data", " ".join(f"{b:x}-{e:x}" for b, e in data[:40]))
if "--add" in sys.argv:
    p = pathlib.Path(__file__).parent / "roots.txt"
    have = set(p.read_text().split())
    new = [f"{b:x}" for b, e in code if f"{b:x}" not in have]
    with open(p, "a") as f:
        f.write("".join(x + "\n" for x in new))
    print("added", len(new))
