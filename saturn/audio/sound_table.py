#!/usr/bin/env python
"""Read the Z80 driver's sound table from avp.01: class, priority and channels of every command number. Numbers only.
Linear address = file offset of avp.01 (see the Z80 read helper at 0x0a71). usage: sound_table.py AVP01 OUT.json"""
import json, sys

def table(rom):
    mod = (rom[0x9000] << 8) | rom[0x9001]
    out = {}
    for n in range(mod):
        e = 0x9006 + 4 * n
        p = (rom[e] << 16) | (rom[e + 1] << 8) | rom[e + 2]
        if p == 0:
            continue
        hdr = rom[p]
        ch = [c for c in range(16) if rom[p + 1 + 2 * c] or rom[p + 2 + 2 * c]]
        out[n] = dict(cls="music" if hdr == 0 else "direct" if hdr >= 0x80 else "sfx", prio=hdr, chans=ch)
    return mod, out

if __name__ == "__main__":
    rom = open(sys.argv[1], "rb").read()
    mod, t = table(rom)
    json.dump({"modulus": mod, "sounds": {f"{k:x}": v for k, v in t.items()}}, open(sys.argv[2], "w"))
    import collections
    print(len(rom), hex(mod), collections.Counter(v["cls"] for v in t.values()), collections.Counter(len(v["chans"]) for v in t.values() if v["cls"] == "sfx"))
