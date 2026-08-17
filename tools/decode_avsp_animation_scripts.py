"""Decode the observed AvP animation-script programs from a private ROM dump.

The current evidence supports two record forms:

* normal: duration word, flags word, assembly pointer, eight-byte tail;
* jump: one long pointer back into the script region.

The tail is retained verbatim.  Its byte fields are not labelled until the
pixel-exact assembly test and actor-origin pairing prove their meaning.
"""

from __future__ import annotations

import argparse
import csv
import json
import struct
from pathlib import Path


SCRIPT_FIRST = 0x13C000
SCRIPT_LAST = 0x13D800
ASSEMBLY_FIRST = 0x13DE00
ASSEMBLY_LAST = 0x13F000


def u16(data: bytes, offset: int) -> int:
    return struct.unpack_from(">H", data, offset)[0]


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from(">I", data, offset)[0]


def script_pointers(actor_path: Path) -> list[int]:
    pointers: set[int] = set()
    with actor_path.open(encoding="ascii", newline="") as source:
        for row in csv.DictReader(source, delimiter="\t"):
            pointer = (int(row["w1c"], 16) << 16) | int(row["w1e"], 16)
            if SCRIPT_FIRST <= pointer < SCRIPT_LAST:
                pointers.add(pointer)
    return sorted(pointers)


def decode_program(data: bytes, base: int, start: int) -> dict[str, object]:
    records: list[dict[str, object]] = []
    address = start
    visited: set[int] = set()
    status = "limit"
    for _ in range(128):
        if address in visited:
            status = "loop"
            break
        visited.add(address)
        offset = address - base
        if offset < 0 or offset + 4 > len(data):
            status = "out_of_window"
            break
        possible_jump = u32(data, offset)
        if SCRIPT_FIRST <= possible_jump < SCRIPT_LAST:
            records.append({"address": f"0x{address:06x}",
                            "kind": "jump",
                            "target": f"0x{possible_jump:06x}"})
            address = possible_jump
            continue
        if offset + 16 > len(data):
            status = "truncated"
            break
        duration = u16(data, offset)
        flags = u16(data, offset + 2)
        assembly = u32(data, offset + 4)
        tail = data[offset + 8:offset + 16]
        if duration == 0 and flags == 0 and assembly == 0:
            status = "terminator"
            break
        records.append({
            "address": f"0x{address:06x}",
            "kind": "pose",
            "duration": duration,
            "flags": f"0x{flags:04x}",
            "flip_x": bool(flags & 0x8000),
            "assembly": f"0x{assembly:06x}",
            "tail_hex": tail.hex(),
            "tail_bytes": list(tail),
        })
        address += 16
    else:
        status = "record_limit"
    return {"start": f"0x{start:06x}", "status": status,
            "records": records,
            "pose_count": sum(r["kind"] == "pose" for r in records),
            "jump_count": sum(r["kind"] == "jump" for r in records),
            "assembly_pointers": sorted({r["assembly"] for r in records
                                          if r["kind"] == "pose"})}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rom-window", type=Path,
                        default=Path(".deps/mame/actorprobe/rom_window_13c_13f.bin"))
    parser.add_argument("--actor-tsv", type=Path,
                        default=Path(".deps/mame/actorprobe/actor_ffa3c0.tsv"))
    parser.add_argument("-o", "--output", type=Path,
                        default=Path("data/avsp_animation_scripts.json"))
    parser.add_argument("--base", type=lambda value: int(value, 0),
                        default=SCRIPT_FIRST)
    args = parser.parse_args()
    data = args.rom_window.read_bytes()
    starts = script_pointers(args.actor_tsv)
    programs = [decode_program(data, args.base, start) for start in starts]
    result = {
        "schema": 1,
        "classification": "missing pixel gate (ROM-derived script structure)",
        "source": {
            "rom_window": args.rom_window.as_posix(),
            "window_base": f"0x{args.base:06x}",
            "actor_trace": args.actor_tsv.as_posix(),
        },
        "format": {
            "normal_record_bytes": 16,
            "jump_record_bytes": 4,
            "duration_offset": 0,
            "flags_offset": 2,
            "assembly_pointer_offset": 4,
            "tail_bytes": 8,
            "flip_flag": "0x8000",
            "tail_field_labels": "unresolved; bytes +8/+9 are consumed by interaction dispatch",
        },
        "routine_evidence": {
            "script_advance": ["0x16536", "0x165c4", "0x16644"],
            "script_advance_bytes": 16,
            "backward_jump_when_flags_negative": True,
            "tail_byte_8_reader": "0x1cf94",
            "tail_byte_9_reader": "0x1cf88",
            "full_record_copy_reader": "0x88e16",
            "note": (
                "The animation updater reads duration and flags, advances by 16 bytes, "
                "and follows a long backward pointer when flags are negative. The "
                "tail is not an X/Y word pair: bytes +8 and +9 index interaction tables."
            ),
        },
        "script_pointer_count": len(starts),
        "assembly_range_hint": [f"0x{ASSEMBLY_FIRST:06x}",
                                f"0x{ASSEMBLY_LAST:06x}"],
        "programs": programs,
        "remaining_gate": (
            "Decode the assembly records and prove one rendered pose pixel for "
            "pixel against a captured pose; then label tail fields and actor-local hitboxes."
        ),
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    print(f"Decoded {len(programs)} animation programs: {args.output}")


if __name__ == "__main__":
    main()
