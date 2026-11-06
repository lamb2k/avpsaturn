#!/usr/bin/env python
"""Write the whole reachable 68000 disassembly to E:/AvP/learning/audio/all.dis (private, never committed)."""
import json, pathlib, capstone
B = pathlib.Path("C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-playable-loop-pivot/.deps/mame/actorprobe")
OP = (B / "decrypted_opcodes_2m.bin").read_bytes()
MD = capstone.Cs(capstone.CS_ARCH_M68K, capstone.CS_MODE_M68K_000 | capstone.CS_MODE_BIG_ENDIAN)
d = json.load(open("E:/AvP/learning/cfg.json"))
with open("E:/AvP/learning/audio/all.dis", "w") as f:
    for a in sorted(int(k, 16) for k in d["seen"]):
        for i in MD.disasm(OP[a:a + 10], a, 1):
            f.write(f"{i.address:06x}: {i.mnemonic} {i.op_str}\n")
