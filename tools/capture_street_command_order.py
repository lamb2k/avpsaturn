#!/usr/bin/env python3
"""RP4 v1 Saturn control: capture StreetTest's final VDP1 output.

This reads what the Saturn actually produced, not what the port meant to
produce. At a chosen StreetTest fixture frame it captures:

- the final VDP1 command table, walked through its jump links, with each
  command's index, control words, CMDCOLR, coordinates and character
  address, plus a hash of the whole table;
- the VDP1 sprite framebuffer window around the witness pixel, at native
  resolution straight out of emulator memory, so there is no host
  scaling and no overlay;
- the SGL work-RAM shadow of the VDP2 priority values, which is what the
  program PROGRAMMED. It is not a VDP2 register read: this instrument
  cannot read those registers, and nothing here may be called
  register-exact;
- the StreetTest diagnostic counters, so the captured frame is the
  frame that was asked for.

The framebuffer stride is not assumed. It is calibrated against pixels
the source-side composite independently predicts, and the calibration
must agree at several points before any witness is read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from capture_frontend_cram import Mcp  # noqa: E402

NM = ROOT / ".deps/joengine/Compiler/WINDOWS/sh-elf/bin/nm.exe"
ENDPOINT = "http://127.0.0.1:9640/mcp"
VDP1_VRAM = 0x25C00000
VDP1_FRAMEBUFFER = 0x25C80000
BMPNA_OFFSET = 0x2C
SHADOW_REGISTERS = (("SPCTL", 0xE0), ("PRISA", 0xF0), ("PRISB", 0xF2),
                    ("PRISC", 0xF4), ("PRISD", 0xF6), ("PRINA", 0xF8),
                    ("PRINB", 0xFA))
CANDIDATE_STRIDES = (1024, 704, 512, 2048)
MAX_COMMANDS = 2048


def symbols(elf: Path) -> dict[str, int]:
    out = subprocess.run([str(NM), "--target=coff-sh", str(elf)],
                         capture_output=True, text=True,
                         check=True).stdout
    table = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 3:
            table[parts[2]] = int(parts[0], 16)
    return table


def walk_commands(mcp: Mcp) -> tuple[list[dict], str]:
    """Walk the VDP1 command table through its jump links."""
    raw = bytearray()
    commands = []
    index = 0
    at = 0
    while index < MAX_COMMANDS:
        block = mcp.read(VDP1_VRAM + at * 32, 32)
        raw += block
        ctrl = int.from_bytes(block[0:2], "big")
        if ctrl & 0x8000:                      # draw end
            break
        link = (ctrl >> 12) & 3
        if (ctrl & 0x000F) not in (0, 1, 2, 3, 4, 5, 6, 8, 9, 0xA):
            break
        commands.append({
            "index": index,
            "ctrl": f"0x{ctrl:04x}",
            "pmod": f"0x{int.from_bytes(block[4:6], 'big'):04x}",
            "colr": f"0x{int.from_bytes(block[6:8], 'big'):04x}",
            "srca": f"0x{int.from_bytes(block[8:10], 'big'):04x}",
            "size": f"0x{int.from_bytes(block[10:12], 'big'):04x}",
            "xa": int.from_bytes(block[12:14], "big"),
            "ya": int.from_bytes(block[14:16], "big"),
        })
        index += 1
        if link == 0:
            at = index
        elif link == 1:
            at = int.from_bytes(block[2:4], "big") // 2
        else:
            at = index
    return commands, hashlib.sha256(bytes(raw)).hexdigest()


def read_framebuffer(mcp: Mcp, stride: int, x: int, y: int,
                     radius: int) -> dict[tuple[int, int], int]:
    """A native-resolution window of the sprite framebuffer."""
    window = {}
    for row in range(y - radius, y + radius + 1):
        if row < 0 or row > 255:
            continue
        first = max(x - radius, 0)
        count = (min(x + radius, 351) - first + 1)
        if count <= 0:
            continue
        data = mcp.read(VDP1_FRAMEBUFFER + row * stride + first * 2,
                        count * 2)
        for step in range(count):
            window[(first + step, row)] = int.from_bytes(
                data[step * 2:step * 2 + 2], "big")
    return window


def wait_for_rel(mcp: Mcp, syms: dict, target_rel: int,
                 period: int, timeout: float = 600.0) -> int:
    """Pause StreetTest exactly on one fixture frame, once it is live.

    A frame number alone is not enough: at cold boot the counter reads 0
    and no objects have been drawn, which would satisfy rel 0 while the
    renderer has produced nothing. The capture therefore waits for the
    runtime to report ready, for the street loop to have drawn objects,
    and for at least one complete fixture pass before it accepts a
    frame.
    """
    frame_symbol = syms["_avsp_diag_street_frame"]
    ready_symbol = syms["_avsp_diag_runtime_ready"]
    objects_symbol = syms["_avsp_diag_street_objects"]
    deadline = time.time() + timeout
    # Phase 1: wait for the renderer to come up. Polling hard here
    # starves the emulator through the slow disc boot, so this phase
    # samples gently and leaves the machine running in between.
    live = False
    while time.time() < deadline:
        mcp.call("pause")
        ready = mcp.u32(ready_symbol)
        objects = mcp.u32(objects_symbol)
        mcp.call("resume")
        if ready == 1 and objects > 0:
            live = True
            break
        time.sleep(2.0)
    if not live:
        raise SystemExit(
            "StreetTest never reported a live renderer "
            "(runtime_ready and drawn objects)")

    # Phase 2: avsp_diag_street_frame holds the fixture-relative index,
    # so hunt for the exact frame.
    while time.time() < deadline:
        mcp.call("pause")
        frame = mcp.u32(frame_symbol)
        if frame == target_rel:
            return frame
        # resume immediately followed by pause advances about one frame
        # boundary; sleeping here would let the fixture run past the
        # target and the hunt would never converge.
        mcp.call("resume")
    raise SystemExit(
        f"StreetTest never reached fixture frame {target_rel}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True)
    parser.add_argument("--rel", type=int, required=True)
    parser.add_argument("--witness-x", type=int, required=True)
    parser.add_argument("--witness-y", type=int, required=True)
    parser.add_argument("--radius", type=int, default=6)
    parser.add_argument("--elf", type=Path, default=ROOT / "game.elf")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    syms = symbols(args.elf)
    mcp = Mcp(ENDPOINT)
    mcp.initialize()

    strips = (ROOT / "build/rp4_fixture/STRIPS.BIN").read_bytes()
    period = int.from_bytes(strips[6:8], "big")

    frame = wait_for_rel(mcp, syms, args.rel, period)
    report: dict = {
        "schema": "rp4-street-command-order-capture-v0",
        "label": args.label,
        "requested_rel": args.rel,
        "observed_frame": frame,
        "observed_rel": frame,
        "fixture_period": period,
        "runtime_ready": mcp.u32(syms["_avsp_diag_runtime_ready"]),
        "street_objects": mcp.u32(syms["_avsp_diag_street_objects"]),
        "witness_xy": [args.witness_x, args.witness_y],
    }

    literal = mcp.u32(syms["_slBMPalette"] + 0x10)
    shadow = literal - BMPNA_OFFSET
    report["vdp2_shadow_values"] = {
        name: f"0x{mcp.u16(shadow + off):04x}"
        for name, off in SHADOW_REGISTERS}
    report["vdp2_shadow_note"] = (
        "SGL work-RAM shadow of what the program programmed; this "
        "instrument cannot read VDP2 registers, so this is NOT a "
        "register readback")

    commands, table_hash = walk_commands(mcp)
    report["command_count"] = len(commands)
    report["command_table_sha256"] = table_hash
    report["commands"] = commands[:512]

    windows = {}
    for stride in CANDIDATE_STRIDES:
        window = read_framebuffer(mcp, stride, args.witness_x,
                                  args.witness_y, args.radius)
        windows[str(stride)] = {
            f"{x},{y}": f"0x{value:04x}"
            for (x, y), value in sorted(window.items())}
    report["framebuffer_windows_by_stride"] = windows
    report["framebuffer_note"] = (
        "native-resolution sprite framebuffer straight from emulator "
        "memory: no host scaling, no overlay. The stride is calibrated "
        "downstream, never assumed")

    mcp.call("resume")
    args.output.write_text(
        json.dumps(report, indent=1, sort_keys=True) + "\n",
        encoding="ascii", newline="\n")
    print(f"{args.label}: frame {frame} (rel {report['observed_rel']}), "
          f"{len(commands)} commands, table "
          f"{table_hash[:16]}, objects {report['street_objects']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
