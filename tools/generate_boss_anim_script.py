"""Generate generated/avsp_boss_anim_script.h for the SH-2 script interpreter.

The header carries two things:

* the raw boss animation script window, ROM 0x13C000..0x13F000, as bytes. This
  is the input the interpreter walks: 16-byte pose records plus the four-byte
  jump records a negative (bit-15) flags word points at. The window bytes come
  from the ignored private MAME dump, so they are regenerated, never committed.

* the per-program *expected* record sequences, taken from the tracked, already
  validated data/avsp_animation_scripts.json. Before emitting, the generator
  re-walks the raw window with the exact interpreter rules (big-endian fields,
  bit-15 jump to the u32 at record+16, otherwise advance 16) and REQUIRES the
  raw walk to agree with the JSON record-for-record (assembly pointer, duration,
  seven-bit sequence index, low parameter byte) and to close the loop. If the
  ROM and the JSON disagree, generation fails: we never build the interpreter
  against a table we have not proven consistent.

The eight-byte record tail is deliberately left out of the expected data; its
consumers (interaction-table selectors) are proven separately.
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM_WINDOW = ROOT / ".deps" / "mame" / "actorprobe" / "rom_window_13c_13f.bin"
SCRIPTS = ROOT / "data" / "avsp_animation_scripts.json"
OUT = ROOT / "generated" / "avsp_boss_anim_script.h"

BASE = 0x13C000
SIZE = 0x3000  # 0x13C000 .. 0x13F000 inclusive


def u16(data: bytes, off: int) -> int:
    return struct.unpack_from(">H", data, off)[0]


def u32(data: bytes, off: int) -> int:
    return struct.unpack_from(">I", data, off)[0]


def read_pose(data: bytes, addr: int) -> dict | None:
    off = addr - BASE
    if off < 0 or off + 16 > len(data):
        return None
    duration = u16(data, off)
    flags = u16(data, off + 2)
    assembly = u32(data, off + 4)
    return {
        "address": addr,
        "duration": duration,
        "flags": flags,
        "seq": (flags >> 8) & 0x7F,
        "param": flags & 0xFF,
        "assembly": assembly,
    }


def next_address(data: bytes, pose: dict) -> int:
    if pose["flags"] & 0x8000:
        off = pose["address"] - BASE + 16
        if off + 4 <= len(data):
            target = u32(data, off)
            if BASE <= target < BASE + len(data):
                return target
    return pose["address"] + 16


def cycle(data: bytes, start: int, cap: int = 1024) -> list:
    """Ordered pose records of the loop from ``start`` (closed when we return)."""
    records = []
    addr = start
    for _ in range(cap):
        pose = read_pose(data, addr)
        if pose is None:
            break
        records.append(pose)
        nxt = next_address(data, pose)
        if nxt == start:
            return records
        addr = nxt
    return records


def emit_byte_array(text, name: str, data: bytes, per_line: int = 16) -> None:
    text.write(f"static const unsigned char {name}[{len(data)}] = {{\n")
    for i in range(0, len(data), per_line):
        chunk = data[i:i + per_line]
        text.write("    " + ", ".join(f"0x{b:02x}" for b in chunk) + ",\n")
    text.write("};\n")


def main() -> int:
    if not ROM_WINDOW.is_file():
        print(f"missing {ROM_WINDOW}", file=sys.stderr)
        return 2
    data = ROM_WINDOW.read_bytes()
    if len(data) != SIZE:
        print(f"rom window is {len(data)} bytes, expected {SIZE}", file=sys.stderr)
        return 2
    if not SCRIPTS.is_file():
        print(f"missing {SCRIPTS}", file=sys.stderr)
        return 2
    scripts = json.loads(SCRIPTS.read_text(encoding="ascii"))
    programs = scripts.get("programs", [])
    if not programs:
        print("no programs in avsp_animation_scripts.json", file=sys.stderr)
        return 2

    # Cross-validate raw walk vs JSON for every program.
    expected = []  # flat list of pose dicts, programs concatenated in order
    starts = []
    for prog in programs:
        start = int(prog["start"], 16)
        starts.append(start)
        json_records = [r for r in prog["records"] if r["kind"] == "pose"]
        raw = cycle(data, start)
        if len(raw) != len(json_records):
            print(f"{prog['start']}: raw walk has {len(raw)} records, "
                  f"json has {len(json_records)}", file=sys.stderr)
            return 1
        for a, b in zip(raw, json_records):
            ja = int(b["assembly"], 16)
            if (a["assembly"] != ja or a["duration"] != b["duration"]
                    or a["seq"] != b["sequence_index"]
                    or a["param"] != b["param_byte"]):
                print(f"{prog['start']}: mismatch at {a['address']:06x} "
                      f"raw asm=0x{a['assembly']:06x} d={a['duration']} "
                      f"seq={a['seq']} p={a['param']} "
                      f"vs json asm={b['assembly']} d={b['duration']} "
                      f"seq={b['sequence_index']} p={b['param_byte']}",
                      file=sys.stderr)
                return 1
        if raw and next_address(data, raw[-1]) != start:
            print(f"{prog['start']}: loop does not close "
                  f"(next={next_address(data, raw[-1]):06x})", file=sys.stderr)
            return 1
        expected.extend(raw)

    n_programs = len(starts)
    offsets = []
    index = 0
    for prog in programs:
        offsets.append(index)
        index += sum(1 for r in prog["records"] if r["kind"] == "pose")
    offsets.append(index)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="ascii", newline="\n") as text:
        text.write("/* Generated by tools/generate_boss_anim_script.py.\n"
                   " * Do not edit: the window bytes come from the private MAME\n"
                   " * dump and the expected record table is cross-checked against\n"
                   " * data/avsp_animation_scripts.json at generation time.\n"
                   " */\n"
                   "#ifndef AVSP_BOSS_ANIM_SCRIPT_H\n"
                   "#define AVSP_BOSS_ANIM_SCRIPT_H\n\n")
        text.write(f"#define AVSP_BOSS_ANIM_SCRIPT_BASE 0x{BASE:06x}u\n")
        text.write(f"#define AVSP_BOSS_ANIM_SCRIPT_SIZE 0x{SIZE:04x}u\n\n")
        emit_byte_array(text, "avsp_boss_anim_script", data)
        text.write("\n")
        text.write(f"#define AVSP_BOSS_ANIM_PROGRAM_COUNT {n_programs}\n")
        text.write("static const unsigned int avsp_boss_anim_program_start"
                   f"[{n_programs}] = {{\n    "
                   + ", ".join(f"0x{a:06x}u" for a in starts) + "\n};\n\n")
        text.write(f"static const int avsp_boss_anim_record_offset"
                   f"[{n_programs + 1}] = {{\n    "
                   + ", ".join(str(o) for o in offsets) + "\n};\n\n")

        def arr(name: str, key: str, fmt: str) -> None:
            text.write(f"static const unsigned int {name}"
                       f"[{len(expected)}] = {{\n    "
                       + ", ".join(fmt.format(r[key]) for r in expected)
                       + "\n};\n\n")

        arr("avsp_boss_anim_exp_address", "address", "0x{:06x}u")
        arr("avsp_boss_anim_exp_duration", "duration", "{}")
        arr("avsp_boss_anim_exp_flags", "flags", "0x{:04x}u")
        arr("avsp_boss_anim_exp_seq", "seq", "{}")
        arr("avsp_boss_anim_exp_param", "param", "{}")
        arr("avsp_boss_anim_exp_assembly", "assembly", "0x{:06x}u")
        text.write("#endif /* AVSP_BOSS_ANIM_SCRIPT_H */\n")

    print(f"[OK] {OUT}: {n_programs} programs, {len(expected)} records, "
          f"{SIZE} window bytes (raw walk == json for all).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
