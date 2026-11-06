#!/usr/bin/env python
"""Learning aid: bounded 68000 disassembly from the private decrypted opcode image.

usage: learn_dis68k.py vectors | learn_dis68k.py HEXSTART HEXEND [...pairs]
       learn_dis68k.py xref ADDR [...]   (absolute-long/short references, opcode image)
Prints source-derived text to stdout only. Do not commit its output wholesale.
"""
import pathlib
import struct
import sys

import capstone

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE = ROOT / ".deps" / "mame" / "actorprobe"
OP = (BASE / "decrypted_opcodes_2m.bin").read_bytes()
PR = (BASE / "decrypted_program_2m.bin").read_bytes()
MD = capstone.Cs(capstone.CS_ARCH_M68K, capstone.CS_MODE_M68K_000 | capstone.CS_MODE_BIG_ENDIAN)
MD.skipdata = True


def dis(start, end):
    for i in MD.disasm(OP[start:end], start):
        print(f"{i.address:06x}: {i.bytes.hex():<20} {i.mnemonic} {i.op_str}")


def xref(addr):
    # RAM addresses appear as 00ff xxxx (abs.l); ff.. short forms as xxxx >= 0x8000 only
    pats = [struct.pack(">I", addr)]
    if addr >= 0xff8000:
        pats.append(struct.pack(">H", addr & 0xffff))
    for pat in pats:
        pos = 0
        while (pos := OP.find(pat, pos)) >= 0:
            if pos % 2 == 0:
                for back in (2, 4, 6):
                    insns = list(MD.disasm(OP[pos - back:pos + 8], pos - back, 1))
                    if insns and insns[0].size >= back + len(pat) and f"{addr:x}" in insns[0].op_str:
                        i = insns[0]
                        print(f"{i.address:06x}: {i.mnemonic} {i.op_str}")
                        break
            pos += 2


if sys.argv[1] == "vectors":
    for n in list(range(0, 8)) + list(range(24, 32)) + list(range(32, 40)):
        print(f"vec {n:2d} @{n*4:03x}: {struct.unpack('>I', PR[n*4:n*4+4])[0]:08x}")
elif sys.argv[1] == "xref":
    for a in sys.argv[2:]:
        print("== xref", a)
        xref(int(a, 16))
else:
    args = [int(a, 16) for a in sys.argv[1:]]
    for s, e in zip(args[::2], args[1::2]):
        print(f"--- {s:06x}..{e:06x}")
        dis(s, e)
