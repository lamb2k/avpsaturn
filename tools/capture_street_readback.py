#!/usr/bin/env python3
"""RP4 live readback: read the full VDP2 register set the street test
programs (via the SGL work-RAM shadow), the CRAM offsets, the VDP1 command
classes, the diagnostic counters, and several PNT/char VRAM canaries against
the staged STRIPS.BIN. Writes data/rp4_street_live_readback.json."""
from __future__ import annotations

import json
import struct
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from capture_frontend_cram import Mcp  # noqa: E402

NM = ROOT / ".deps/joengine/Compiler/WINDOWS/sh-elf/bin/nm.exe"
BMPNA_OFFSET = 0x2C
SHADOW_REGISTERS = (
    ("TVMD", 0x00), ("BGON", 0x20), ("CHCTLA", 0x28), ("CHCTLB", 0x2A),
    ("PNCN0", 0x30), ("PNCN1", 0x32), ("PLSZ", 0x3A), ("MPOFN", 0x3C),
    ("MPABN0", 0x40), ("MPCDN0", 0x42), ("MPABN1", 0x44), ("MPCDN1", 0x46),
    ("SCXIN0", 0x70), ("SCYIN0", 0x74), ("SCXIN1", 0x80), ("SCYIN1", 0x84),
    ("CRAOFA", 0xE4), ("CRAOFB", 0xE6), ("SPCTL", 0xE0),
    ("PRISA", 0xF0), ("PRISB", 0xF2), ("PRISC", 0xF4), ("PRISD", 0xF6),
    ("PRINA", 0xF8), ("PRINB", 0xFA),
)
VDP2_VRAM = 0x25E00000
VDP1_VRAM = 0x25C00000


def symbols() -> dict[str, int]:
    out = subprocess.run(
        [str(NM), "--target=coff-sh", str(ROOT / "game.elf")],
        capture_output=True, text=True, check=True).stdout
    table = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 3:
            table[parts[2]] = int(parts[0], 16)
    return table


def main() -> None:
    syms = symbols()
    m = Mcp("http://127.0.0.1:9640/mcp")
    literal = m.u32(syms["_slBMPalette"] + 0x10)
    assert 0x06000000 <= literal < 0x06100000, hex(literal)
    shadow = literal - BMPNA_OFFSET

    report: dict = {"schema": "rp4-street-live-readback-v0"}
    report["symbols"] = {k: f"0x{v:08x}" for k, v in syms.items()
                         if k in ("__bend", "_avsp_diag_street_frame",
                                  "_avsp_diag_street_scx",
                                  "_avsp_diag_street_objects",
                                  "_avsp_diag_runtime_ready",
                                  "_avsp_diag_print_buffer")}
    report["runtime_ready"] = m.u32(syms["_avsp_diag_runtime_ready"])

    m.call("pause")
    try:
        regs = {name: m.u16(shadow + off) for name, off in SHADOW_REGISTERS}
        report["vdp2_shadow_registers"] = {k: f"0x{v:04x}"
                                           for k, v in regs.items()}
        frame = m.u32(syms["_avsp_diag_street_frame"])
        scx = m.read(syms["_avsp_diag_street_scx"], 8)
        report["street_frame"] = frame
        report["street_scx"] = [int.from_bytes(scx[:4], "big"),
                                int.from_bytes(scx[4:], "big")]
        report["street_objects"] = m.u32(syms["_avsp_diag_street_objects"])
        buf = m.read(syms["_avsp_diag_print_buffer"], 64)
        report["print_buffer"] = buf.split(b"\0")[0].decode(
            "ascii", "replace")

        strips = (ROOT / "build/rp4_fixture/STRIPS.BIN").read_bytes()

        def u16(at): return int.from_bytes(strips[at:at + 2], "big")

        def u32b(at): return int.from_bytes(strips[at:at + 4], "big")

        rel = frame % u16(6)

        # VRAM canaries: NBG0/NBG1 char pools and base PNT words must match
        # the fixture (issue A: nothing else may write these areas).
        # Runtime placement mirrors main.c street_load_planes: NBG0 chars at
        # VDP2 VRAM 0x00000, NBG1 chars at 0x28000, PNT pages A0 0x10000 /
        # A1 0x12000 (NBG0), 0x30000/0x32000 (NBG1) per MPABN0/1 decode.
        canaries = []
        # main.c: NBG0 chars at VRAM A0 (0x00000), NBG1 chars at A1
        # (0x20000), NBG0 PNT at B0 (0x40000), NBG1 PNT at B0+0x4000.
        for plane, char_vram, pnt_vram in ((0, 0x00000, 0x40000),
                                           (1, 0x20000, 0x44000)):
            at = 8 + plane * 20
            char_count = u16(at + 8)
            char_off = u32b(at + 12)
            cell_cols = u16(at)
            for label, offset, expected in (
                    ("char_first64", 0, strips[char_off:char_off + 64]),
                    ("char_mid64", (char_count // 2) * 64,
                     strips[char_off + (char_count // 2) * 64:
                            char_off + (char_count // 2) * 64 + 64]),
                    ("char_last64", (char_count - 1) * 64,
                     strips[char_off + (char_count - 1) * 64:
                            char_off + char_count * 64])):
                live = m.read(VDP2_VRAM + char_vram + offset, 64)
                canaries.append({
                    "plane": plane, "kind": label,
                    "vram": f"0x{char_vram + offset:05x}",
                    "match": live == expected})
            # PNT canary: compare the first 32 base pattern words that
            # no patch has touched yet only when the loop has not passed a
            # patch frame; otherwise compare the last row (never patched).
            pnt_off = u32b(at + 16)
            expected_words = strips[pnt_off + (cell_cols * 2 * 0):
                                    pnt_off + 64]
            live_words = m.read(VDP2_VRAM + pnt_vram, 64)
            expect = b"".join(
                struct.pack(">H", u16(pnt_off + i * 2) * 2)
                for i in range(32))
            canaries.append({"plane": plane, "kind": "pnt_first32",
                             "vram": f"0x{pnt_vram:05x}",
                             "match": live_words == expect})
        report["vram_canaries"] = canaries
        report["vram_canaries_all_match"] = all(c["match"]
                                                for c in canaries)

        # CRAM: first entries of the two street palettes.
        cram = {}
        for bank, base in (("nbg0_palette", regs["CRAOFA"] & 7),
                           ("nbg1_palette", (regs["CRAOFA"] >> 4) & 7)):
            cram[bank] = f"colour-ram offset {base}"
        report["cram_offsets"] = cram

        # VDP1 command walk: count commands per priority class bits 14-13
        # of CMDCOLR (sprite type 3).
        classes: dict[int, int] = {}
        at = VDP1_VRAM
        for _ in range(2048):
            cmd = m.read(at, 32)
            ctrl = int.from_bytes(cmd[0:2], "big")
            if ctrl & 0x8000:
                break
            if (ctrl & 0xF) <= 4 and not (ctrl & 0x4000):
                colr = int.from_bytes(cmd[6:8], "big")
                cls = (colr >> 13) & 3
                classes[cls] = classes.get(cls, 0) + 1
            jump = (ctrl >> 12) & 3
            if jump == 0:
                at += 32
            elif jump == 1:
                at = VDP1_VRAM + int.from_bytes(cmd[2:4], "big") * 8
            else:
                at += 32
        report["vdp1_command_classes"] = {str(k): v
                                          for k, v in classes.items()}
        report["street_rel_frame"] = rel
    finally:
        m.call("resume")

    out = ROOT / "data/rp4_street_live_readback.json"
    out.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n",
                   encoding="ascii", newline="\n")
    print(json.dumps(report["vdp2_shadow_registers"], sort_keys=True))
    print("canaries all match:", report["vram_canaries_all_match"],
          "| classes:", report["vdp1_command_classes"],
          "| frame", report["street_frame"], "scx", report["street_scx"],
          "objects", report["street_objects"])


if __name__ == "__main__":
    main()
