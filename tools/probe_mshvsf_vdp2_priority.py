#!/usr/bin/env python3
"""Re-read the official port's VDP2 priority registers.

The tracked MSHvSF capture reports the VDP2 register block as 288 zero
bytes at every anchor, and the handoff records that as an INSTRUMENT
LIMIT rather than a measurement: layer enables, priorities and the
sprite-priority mapping "cannot be decoded from this capture at all".

This probe attacks the instrument, not the parser. It reads the register
block through every plausible SH-2 view of it at a paused anchor:

  0x05F80000  cached A-bus view (what the tracked capture used)
  0x25F80000  uncached mirror
  0x05F00000  colour RAM, as a positive control that the reader works

A view is USABLE when it returns a nonzero block; the colour-RAM control
must be nonzero in every run, so an all-zero control means the reader
itself is broken and no conclusion about VDP2 may be drawn.

When a usable view exists the priority registers are decoded:

  SPCTL  0x0E0  sprite type, colour-mode and priority-bit split
  PRISA..PRISD 0x0F0..0x0F6  per sprite-priority-number priority
  PRINA/PRINB  0x0F8/0x0FA   per-NBG priority
  PRIR         0x0FC         RBG0 priority

Nothing here is written back into the reference documents by this tool;
it emits evidence only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from capture_mshvsf_saturn_mcp import (  # noqa: E402
    McpClient, dump_region, parse_status, wait_and_pause)

DEFAULT_ENDPOINT = "http://127.0.0.1:9640/mcp"
REGISTER_LENGTH = 0x120

VIEWS = {
    "cached_a_bus": 0x05F80000,
    "uncached_mirror": 0x25F80000,
}
CONTROL_VIEW = ("colour_ram_positive_control", 0x05F00000, 0x200)

SPRITE_TYPES = {
    # Sprite type -> (priority bits in the sprite data, colour bits).
    0x0: ("bits 14-15", "bits 11-13"),
    0x1: ("bits 13-15", "bits 11-12"),
    0x2: ("bit 15", "bits 11-13"),
    0x3: ("bits 14-15", "bits 11-12"),
    0x4: ("bits 14-15", "bits 10-12"),
    0x5: ("bit 15", "bits 12-14"),
    0x6: ("bit 15", "bits 11-13"),
    0x7: ("bit 15", "bits 12-13"),
    0x8: ("bit 7", "none"),
    0x9: ("bit 7", "bit 6"),
    0xA: ("bits 6-7", "none"),
    0xB: ("none", "bits 6-7"),
    0xC: ("bit 7", "none"),
    0xD: ("bit 7", "bit 6"),
    0xE: ("bits 6-7", "none"),
    0xF: ("none", "bits 6-7"),
}


def word(block: bytes, offset: int) -> int:
    return int.from_bytes(block[offset:offset + 2], "big")


def decode_priority_registers(block: bytes) -> dict:
    """Decode the VDP2 priority programming from a register block."""
    if len(block) < REGISTER_LENGTH:
        raise ValueError(
            f"register block is {len(block)} bytes, expected "
            f"{REGISTER_LENGTH}")
    spctl = word(block, 0x0E0)
    sprite_type = (spctl >> 8) & 0xF
    pris = [word(block, off) for off in (0x0F0, 0x0F2, 0x0F4, 0x0F6)]
    sprite_priorities = []
    for register in pris:
        sprite_priorities.append(register & 0x7)
        sprite_priorities.append((register >> 8) & 0x7)
    prina, prinb = word(block, 0x0F8), word(block, 0x0FA)
    return {
        "spctl": f"0x{spctl:04x}",
        "sprite_type": sprite_type,
        "sprite_data_split": {
            "priority_bits": SPRITE_TYPES[sprite_type][0],
            "colour_bits": SPRITE_TYPES[sprite_type][1],
        },
        "sprite_colour_calculation_condition": (spctl >> 12) & 0x7,
        "sprite_window_enabled": bool(spctl & 0x10),
        "sprite_priority_by_number":
            {str(n): p for n, p in enumerate(sprite_priorities)},
        "nbg_priority": {
            "NBG0": prina & 0x7,
            "NBG1": (prina >> 8) & 0x7,
            "NBG2": prinb & 0x7,
            "NBG3": (prinb >> 8) & 0x7,
        },
        "rbg0_priority": word(block, 0x0FC) & 0x7,
    }


def read_views(client: McpClient, chunk: int) -> dict:
    views = {}
    for name, address in VIEWS.items():
        try:
            block = dump_region(client, address, REGISTER_LENGTH, chunk)
        except Exception as error:                      # instrument fault
            views[name] = {"address": f"0x{address:08x}",
                           "error": str(error)}
            continue
        nonzero = sum(1 for b in block if b)
        views[name] = {
            "address": f"0x{address:08x}",
            "nonzero_bytes": nonzero,
            "total_bytes": len(block),
            "sha256": hashlib.sha256(block).hexdigest(),
            "usable": nonzero > 0,
            "priority_decode":
                decode_priority_registers(block) if nonzero else None,
        }
    name, address, length = CONTROL_VIEW
    control = dump_region(client, address, length, chunk)
    control_nonzero = sum(1 for b in control if b)
    views[name] = {
        "address": f"0x{address:08x}",
        "nonzero_bytes": control_nonzero,
        "total_bytes": len(control),
        "reader_proven_working": control_nonzero > 0,
    }
    return views


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--frame", type=int, required=True,
                        help="anchor frame to pause on")
    parser.add_argument("--label", required=True)
    parser.add_argument("--chunk", type=int, default=0x100)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    client = McpClient(args.endpoint)
    status = wait_and_pause(client, args.frame)
    state, frame = parse_status(status)
    if state != "stopped" or frame != args.frame:
        raise SystemExit(
            f"could not pause at frame {args.frame} (state {state}, "
            f"frame {frame})")
    views = read_views(client, args.chunk)

    control = views[CONTROL_VIEW[0]]
    usable = [n for n, v in views.items()
              if isinstance(v, dict) and v.get("usable")]
    report = {
        "schema": "mshvsf-vdp2-priority-probe-v0",
        "anchor": {"label": args.label, "frame": frame},
        "views": views,
        "reader_proven_working": control["reader_proven_working"],
        "usable_views": usable,
        "conclusion":
            "VDP2 registers unreadable through every view; the tracked "
            "all-zero block is an instrument limit, not a measurement"
            if not usable else
            f"VDP2 registers readable through {usable[0]}",
    }
    if not control["reader_proven_working"]:
        report["conclusion"] = (
            "memory reader returned zeros for colour RAM as well; no "
            "conclusion about VDP2 may be drawn from this run")
    args.output.write_text(
        json.dumps(report, indent=1, sort_keys=True) + "\n",
        encoding="ascii", newline="\n")
    print(f"{args.label} frame {frame}: usable views {usable or 'none'}, "
          f"reader control "
          f"{'ok' if control['reader_proven_working'] else 'BROKEN'}")
    return 0 if control["reader_proven_working"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
