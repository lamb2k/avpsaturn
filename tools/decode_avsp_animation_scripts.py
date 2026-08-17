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


def decode_assembly(data: bytes, base: int, address: int,
                    offset_data: bytes | None = None,
                    layout_data: bytes | None = None,
                    offset_base: int = 0x1FD1C8,
                    offset_window_base: int = 0x1F6000) -> dict[str, object]:
    """Decode the selector-6 assembly command consumed by the renderer.

    The renderer reads selector, budget word, tile count, offset-table index,
    then one packed long plus one offset word per tile.  The packed long and
    offset-table semantics remain renderer-level data until the pixel gate.
    """
    offset = address - base
    if offset < 0 or offset + 8 > len(data):
        return {"address": f"0x{address:06x}", "status": "out_of_window"}
    selector = u16(data, offset)
    result: dict[str, object] = {
        "address": f"0x{address:06x}",
        "selector": selector,
        "format": "selector,budget,count,offset-index,(packed-long,offset-word)*",
    }
    if selector != 6:
        result["status"] = "unmapped_selector"
        return result
    budget = u16(data, offset + 2)
    count = u16(data, offset + 4)
    offset_index = u16(data, offset + 6)
    result.update({"status": "decoded_structure", "budget": budget,
                   "tile_count": count, "offset_table_index": offset_index})
    entries = []
    layout_address: int | None = None
    if offset_data is not None and offset_index * 2 + 2 <= len(offset_data):
        table_offset = u16(offset_data, offset_index * 2)
        layout_address = offset_base + table_offset
        result["layout_table_pointer"] = f"0x{layout_address:06x}"
    cursor = offset + 8
    for index in range(min(count, 64)):
        if cursor + 6 > len(data):
            result["status"] = "truncated"
            break
        entry: dict[str, object] = {
            "index": index,
            "packed_source": f"0x{u32(data, cursor):08x}",
            "offset_adjust": f"0x{u16(data, cursor + 4):04x}",
        }
        if layout_address is not None:
            layout_offset = layout_address - offset_window_base
            source = layout_data
            source_offset = layout_offset
            if (source is None or source_offset < 0 or
                    source_offset + 4 > len(source)) and offset_data is not None:
                source = offset_data
                source_offset = layout_address - offset_base
            if source is not None and 0 <= source_offset + 4 <= len(source):
                x_word = u16(source, source_offset)
                y_word = u16(source, source_offset + 2)
                entry.update({
                    "layout_address": f"0x{layout_address:06x}",
                    "layout_x_word": f"0x{x_word:04x}",
                    "layout_y_word": f"0x{y_word:04x}",
                    "layout_x_signed": x_word - 0x10000 if x_word & 0x8000 else x_word,
                    "layout_y_signed": y_word - 0x10000 if y_word & 0x8000 else y_word,
                })
            adjust = u16(data, cursor + 4)
            signed_adjust = adjust - 0x10000 if adjust & 0x8000 else adjust
            layout_address += 4 + signed_adjust
        entries.append(entry)
        cursor += 6
    result["entries"] = entries
    result["trailing_word"] = (f"0x{u16(data, cursor):04x}"
                                if cursor + 2 <= len(data) else None)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rom-window", type=Path,
                        default=Path(".deps/mame/actorprobe/rom_window_13c_13f.bin"))
    parser.add_argument("--actor-tsv", type=Path,
                        default=Path(".deps/mame/actorprobe/actor_ffa3c0.tsv"))
    parser.add_argument("--offset-table", type=Path,
                        default=Path(".deps/mame/actorprobe/offset_program.bin"))
    parser.add_argument("--layout-window", type=Path,
                        default=Path(".deps/mame/actorprobe/offset_full_program.bin"))
    parser.add_argument("--offset-window-base", type=lambda value: int(value, 0),
                        default=0x1E0000)
    parser.add_argument("-o", "--output", type=Path,
                        default=Path("data/avsp_animation_scripts.json"))
    parser.add_argument("--base", type=lambda value: int(value, 0),
                        default=SCRIPT_FIRST)
    args = parser.parse_args()
    data = args.rom_window.read_bytes()
    starts = script_pointers(args.actor_tsv)
    programs = [decode_program(data, args.base, start) for start in starts]
    assembly_addresses = sorted({int(address, 16)
                                 for program in programs
                                 for address in program["assembly_pointers"]})
    offset_data = args.offset_table.read_bytes() if args.offset_table.exists() else None
    layout_data = args.layout_window.read_bytes() if args.layout_window.exists() else None
    assemblies = [decode_assembly(data, args.base, address, offset_data, layout_data,
                                   offset_window_base=args.offset_window_base)
                  for address in assembly_addresses]
    result = {
        "schema": 1,
        "classification": "missing pixel gate (ROM-derived script structure)",
        "source": {
            "rom_window": args.rom_window.as_posix(),
            "window_base": f"0x{args.base:06x}",
            "actor_trace": args.actor_tsv.as_posix(),
            "offset_table": args.offset_table.as_posix(),
            "layout_window": args.layout_window.as_posix(),
            "offset_table_base": "0x1fd1c8",
            "offset_window_base": f"0x{args.offset_window_base:06x}",
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
        "assemblies": assemblies,
        "remaining_gate": (
            "Map packed assembly source words and offset-table entries to CPS object "
            "commands, then prove one rendered pose pixel for pixel against a captured "
            "pose; label tail fields and actor-local hitboxes."
        ),
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    print(f"Decoded {len(programs)} animation programs: {args.output}")


if __name__ == "__main__":
    main()
