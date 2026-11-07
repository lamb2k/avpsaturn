#!/usr/bin/env python
"""Lane fit: host check in the Saturn form of OP reads: each OP base rewritten to its side-store offset as saturn/rt/build.py does, the opcode space holding only opx.bin (rest 0xA5), plus per-stage ROM garbage from ROUNDS_SWAP.
A read past a store run sees the wrong bytes here too. usage: rounds_hostfinal.py WORK RUN_DIR OUT   Writes OUT/cN.c, OUT/op.bin, OUT/rt.bin. Then compile with -DHOST -DPREEMPT and run host_kernel.c. ROM-derived: E:/AvP/learning only."""
import json, pathlib, re, shutil, sys
W, R, O = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3])
O.mkdir(parents=True, exist_ok=True)
m = json.loads((W / "opx.json").read_text())
def rw(x):
    paren = "((" if x[0].count("(") == 2 else "("
    return f"OP{x[1]}{paren}0x{m[hex(int(x[2], 16))]:x}u"
for d in R.glob("c[0-9]*"):
    if d.is_dir():
        (O / f"{d.name}.c").write_text(re.sub(r"\bOP(8|16|32)\(\(?0x([0-9a-f]+)u", rw, (d / "lifted_mem.c").read_text()))
s = (W / "opx.bin").read_bytes()
(O / "op.bin").write_bytes(s + b"\xa5" * (0x200000 - len(s)))
shutil.copy(W / "rt.bin", O / "rt.bin"); shutil.copy(R / "dispatch.inc", O / "dispatch.inc")
print(len(s))
