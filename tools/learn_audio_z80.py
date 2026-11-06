#!/usr/bin/env python
"""Bounded Z80 disassembly of the private sound ROM to stdout. usage: learn_audio_z80.py HEXSTART HEXEND ... | dump
'dump' writes a linear pass of the fixed 0..7fff and bank-0 8000..bfff to E:/AvP/learning/audio/z80.dis. Never commit output."""
import pathlib, sys
sys.path.insert(0, "C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-playable-loop-pivot/.deps/python-z80dis")
from z80dis import z80
ROM = pathlib.Path("C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest/avspu/avp.01").read_bytes()
def dis(s, e, out=sys.stdout):
    a = s
    while a < e:
        d = z80.decode(ROM[a:a + 6], a)
        n = d.len or 1
        out.write(f"{a:04x}: {ROM[a:a+n].hex():<10} {z80.disasm(d)}\n")
        a += n
if __name__ == "__main__":
    if sys.argv[1] == "dump":
        dis(0, 0x8000, open("E:/AvP/learning/audio/z80.dis", "w"))
    else:
        v = [int(x, 16) for x in sys.argv[1:]]
        for s, e in zip(v[::2], v[1::2]):
            dis(s, e)
