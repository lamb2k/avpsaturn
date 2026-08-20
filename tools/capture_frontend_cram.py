"""Capture live VDP2 bitmap/palette state at every -FrontendShotTest hold.

The frontend provenance chain is converter output -> ISO member -> decoded
work RAM -> NBG1 VRAM -> palette payload -> CRAM -> active VDP2 registers.
Payloads follow Jo Engine's one-based palette contract, so pixel value p is
expected at hardware colour entry 256 * palette_id + p.
The last two links can only be measured on the running machine, so this tool
drives the pinned Yaba Sanshiro MCP debug server while a `-FrontendShotTest`
build walks its nineteen exact (state, frame) holds, and records for each hold:

* the SGL VDP2 register shadow (TVMD/CHCTLA/BMPNA/CRAOFA/... in work RAM,
  because the CPU-side VDP2 register reads return zero);
* the 258-entry CRAM window centred on the NBG1 bitmap's colour base, so the
  block base and Jo's one-entry-higher allocation can both be tested;
* the active VDP1 command table, decoded to clip/local-coordinate setup and
  per-object command type, order, texture, size, colour bank and vertices;
* the runtime frontend diagnostics.

The raw capture holds ROM-derived colour values, so it is written to the
ignored build tree.  `tools/verify_frontend_cram.py` validates it and emits
the tracked evidence summary.

Symbol addresses move on every link.  Pass them from
`nm --target=coff-sh game.elf`, or let `--elf` derive them.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_OUTPUT = ROOT / "build" / "frontend_cram_readback.json"
DEFAULT_NM = (ROOT / ".deps" / "joengine" / "Compiler" / "WINDOWS" / "sh-elf"
              / "bin" / "nm.exe")
DEFAULT_URL = "http://127.0.0.1:9640/mcp"

# SGL keeps a VDP2 register shadow in work RAM and transfers it at slSynch.
# slBMPalette's literal pool holds the shadow address of BMPNA (VDP2 0x2C),
# which anchors the whole shadow block.
BMPNA_OFFSET = 0x2C
SHADOW_REGISTERS = (
    ("TVMD", 0x00), ("RAMCTL", 0x0E), ("BGON", 0x20), ("CHCTLA", 0x28),
    ("CHCTLB", 0x2A), ("BMPNA", 0x2C), ("MPOFN", 0x3C), ("SCXIN1", 0x80),
    ("SCYIN1", 0x84), ("ZMXIN1", 0x88), ("ZMYIN1", 0x8C), ("CRAOFA", 0xE4),
    ("PRINA", 0xF8), ("PRINB", 0xFA),
)
CRAM = 0x25F00000
CRAM_WINDOW_ENTRIES = 258      # one entry below the base through base + 256
HOLD_COUNT = 19

# VDP1 draws from a command table at the base of its VRAM.  Each command is
# sixteen words; CMDCTRL bit 15 ends the list and its JP field says how to
# reach the next command.  Capturing the table at a held frame is the only way
# to prove object geometry, colour bank, and draw order rather than infer them
# from a screenshot.
VDP1_VRAM = 0x25C00000
VDP1_COMMAND_WORDS = 16
VDP1_COMMAND_BYTES = VDP1_COMMAND_WORDS * 2
VDP1_MAX_COMMANDS = 128

DIAGNOSTIC_SYMBOLS = (
    "avsp_diag_runtime_ready", "avsp_diag_encounter_state",
    "avsp_diag_world_frame", "avsp_diag_hold_index", "avsp_diag_hold_timer",
    "avsp_diag_hold_active", "avsp_diag_frontend_palette_errors",
    "avsp_diag_frontend_rle_errors", "avsp_diag_frontend_missing_assets",
    "avsp_diag_frontend_late_reads", "avsp_diag_frontend_commands",
    "avsp_diag_frontend_palette_boundary_writes",
    "avsp_diag_selection_cursor", "avsp_diag_encounter_timer",
)
REQUIRED_SYMBOLS = DIAGNOSTIC_SYMBOLS + ("frontend_palettes", "slBMPalette")


class Mcp:
    """Minimal JSON-RPC client for the emulator's MCP debug server."""

    def __init__(self, url: str) -> None:
        self.url = url
        self.next_id = 0
        self.session: str | None = None

    def _post(self, method: str, params: dict) -> dict:
        self.next_id += 1
        body = json.dumps({"jsonrpc": "2.0", "id": self.next_id,
                           "method": method, "params": params}).encode()
        headers = {"Content-Type": "application/json",
                   "Accept": "application/json, text/event-stream"}
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        request = urllib.request.Request(self.url, data=body, headers=headers)
        with urllib.request.urlopen(request, timeout=30) as response:
            session = response.headers.get("Mcp-Session-Id")
            if session:
                self.session = session
            text = response.read().decode()
        for line in text.splitlines():
            if line.startswith("data:"):
                text = line[5:].strip()
                break
        return json.loads(text) if text.strip() else {}

    def initialize(self) -> None:
        self._post("initialize", {"protocolVersion": "2024-11-05",
                                  "capabilities": {},
                                  "clientInfo": {"name": "avsp-cram",
                                                 "version": "1"}})
        self._post("notifications/initialized", {})

    def call(self, name: str, **arguments) -> str:
        result = self._post("tools/call", {"name": name,
                                           "arguments": arguments})
        if "error" in result:
            raise RuntimeError(f"{name}: {result['error']}")
        return "\n".join(item.get("text", "")
                         for item in result["result"].get("content", []))

    def read(self, address: int, length: int) -> bytes:
        """memory_read honours `length` only when it is a real integer."""
        text = self.call("memory_read", address=hex(address), length=length)
        data = bytearray()
        for line in text.splitlines():
            match = re.match(r"^[0-9A-Fa-f]+:\s+((?:[0-9A-Fa-f]{2} ?)+)", line)
            if match:
                data += bytes(int(pair, 16) for pair in match.group(1).split())
        if len(data) < length:
            raise RuntimeError(
                f"memory_read at {address:#x} returned {len(data)} of {length}")
        return bytes(data[:length])

    def u16(self, address: int) -> int:
        return int.from_bytes(self.read(address, 2), "big")

    def u32(self, address: int) -> int:
        return int.from_bytes(self.read(address, 4), "big")


def load_symbols(elf: Path, nm: Path) -> dict[str, int]:
    output = subprocess.run([str(nm), "--target=coff-sh", str(elf)],
                            capture_output=True, text=True, check=True).stdout
    symbols: dict[str, int] = {}
    for line in output.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[2].startswith("_"):
            symbols.setdefault(parts[2][1:], int(parts[0], 16))
    missing = [name for name in REQUIRED_SYMBOLS if name not in symbols]
    if missing:
        raise SystemExit(f"missing symbols in {elf}: {', '.join(missing)}")
    return symbols


def diagnostics(mcp: Mcp, symbols: dict[str, int]) -> dict[str, int]:
    values = {name.replace("avsp_diag_", ""): mcp.u32(symbols[name])
              for name in DIAGNOSTIC_SYMBOLS}
    for index in range(2):
        entry = symbols["frontend_palettes"] + index * 8
        values[f"frontend_palette_{index}_data"] = mcp.u32(entry)
        values[f"frontend_palette_{index}_id"] = mcp.u32(entry + 4)
    for key in ("hold_index", "hold_timer"):
        if values[key] >= 0x80000000:
            values[key] -= 0x100000000
    return values


def capture_vdp1(mcp: Mcp) -> list[dict]:
    """Walk the live VDP1 command table and decode every command it draws.

    The whole table is read once and walked in memory, because the frontend's
    commands are laid out consecutively and a per-command read would multiply
    the debugger round trips.  The walk follows CMDCTRL's JP field so a jump
    table would still be traversed correctly, and stops at the end bit.
    """
    raw = mcp.read(VDP1_VRAM, VDP1_MAX_COMMANDS * VDP1_COMMAND_BYTES)
    commands: list[dict] = []
    offset = 0
    seen: set[int] = set()
    while len(commands) < VDP1_MAX_COMMANDS:
        if offset in seen or offset + VDP1_COMMAND_BYTES > len(raw):
            break
        seen.add(offset)
        words = [int.from_bytes(raw[offset + i * 2:offset + i * 2 + 2], "big")
                 for i in range(VDP1_COMMAND_WORDS)]
        control = words[0]
        vertices = [words[6 + i] - 0x10000 if words[6 + i] > 0x7FFF
                    else words[6 + i] for i in range(8)]
        commands.append({
            "offset": offset,
            "control": control,
            "command": control & 0xF,
            "jump": (control >> 12) & 7,
            "end": bool(control & 0x8000),
            "link": words[1],
            "mode": words[2],
            "colour": words[3],
            "character_address": words[4],
            "size": words[5],
            "vertices": vertices,
        })
        if control & 0x8000:
            break
        jump = (control >> 12) & 7
        if jump == 1:
            offset = words[1] * 8
        elif jump == 0:
            offset += VDP1_COMMAND_BYTES
        else:
            break
    return commands


def capture_hold(mcp: Mcp, shadow: int, symbols: dict[str, int]) -> dict:
    registers = {name: mcp.u16(shadow + offset)
                 for name, offset in SHADOW_REGISTERS}
    base_entry = ((registers["BMPNA"] & 0x700) >> 8) * 256
    start_entry = base_entry - 1
    # The window spans base - 1 through base + 256 so both hardware block
    # boundaries, 256 * id and 256 * (id + 1), are captured alongside the
    # 255 entries the palette owns.
    raw = mcp.read(CRAM + start_entry * 2, CRAM_WINDOW_ENTRIES * 2)
    cram = [int.from_bytes(raw[i * 2:i * 2 + 2], "big")
            for i in range(CRAM_WINDOW_ENTRIES)]
    return {
        "registers": registers,
        "nbg1_bitmap_palette_number": (registers["BMPNA"] >> 8) & 0x7F,
        "nbg1_colour_base_entry": base_entry,
        "cram_start_entry": start_entry,
        "cram": cram,
        "vdp1": capture_vdp1(mcp),
        "diagnostics": diagnostics(mcp, symbols),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--elf", type=Path, default=ROOT / "game.elf")
    parser.add_argument("--nm", type=Path, default=DEFAULT_NM)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--timeout", type=float, default=600.0)
    parser.add_argument("--output", type=Path, default=RAW_OUTPUT)
    args = parser.parse_args()

    symbols = load_symbols(args.elf, args.nm)
    mcp = Mcp(args.url)
    mcp.initialize()
    shadow = mcp.u32(symbols["slBMPalette"] + 0x10) - BMPNA_OFFSET

    records: dict[int, dict] = {}
    deadline = time.time() + args.timeout
    while time.time() < deadline and len(records) < HOLD_COUNT:
        state = diagnostics(mcp, symbols)
        index = state["hold_index"]
        if state["hold_active"] and 0 <= index < HOLD_COUNT \
                and index not in records:
            mcp.call("pause")
            time.sleep(0.2)
            records[index] = capture_hold(mcp, shadow, symbols)
            mcp.call("resume")
            print(f"hold {index:2d}: state="
                  f"{records[index]['diagnostics']['encounter_state']} "
                  f"BMPNA=0x{records[index]['registers']['BMPNA']:04X} "
                  f"base entry {records[index]['nbg1_colour_base_entry']} "
                  f"vdp1 commands {len(records[index]['vdp1'])}")
        time.sleep(0.35)

    if len(records) < HOLD_COUNT:
        print(f"captured only {sorted(records)} of {HOLD_COUNT} holds",
              file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({
        "schema": 1,
        "shadow_base": shadow,
        "holds": {str(key): value for key, value in sorted(records.items())},
    }, indent=1) + "\n", encoding="ascii")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
