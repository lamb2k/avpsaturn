"""Decode the observed AvP animation-script programs from a private ROM dump.

The current evidence supports two record forms:

* normal: duration word, flags word, assembly pointer, eight-byte tail;
* jump: one long pointer back into the script region.

The flags word at offset +2 splits into flip_x (bit 15), a 7-bit sequence
index (bits 14-8), and an 8-bit parameter byte (bits 7-0).

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


def _walker_to_first_pose(start: int, data: bytes, base: int) -> int:
    """Walk each pointer forward to its loop target.

    The script has an explicit loop. A pointer from the actor struct may land
    on any record inside that loop.  We advance 16 bytes per pose, check for
    a negative-flags jump record, follow it, and repeat until the address we
    reach is also a pose entry (non-negative flags or end-of-data).  That
    pose is the canonical loop target.
    """
    address = start
    visited: set[int] = set()
    for _ in range(128):
        if address in visited:
            # We have circled back to an address we already know; use it.
            return address
        visited.add(address)
        offset = address - base
        if offset < 0 or offset + 4 > len(data):
            return address
        # Try to decode as a 16-byte pose record.
        if offset + 16 > len(data):
            return address
        duration = u16(data, offset)
        flags_word = u16(data, offset + 2)
        assembly = u32(data, offset + 4)
        # Zero record? Treat it as end of chain -- unlikely for live data.
        if duration == 0 and flags_word == 0 and assembly == 0:
            return address
        # Negative flags means the next 4 bytes are a long-pointer jump.
        if flags_word & 0x8000:
            if offset + 20 > len(data):
                return address
            jump_target = u32(data, offset + 16)
            if SCRIPT_FIRST <= jump_target < SCRIPT_LAST:
                # The loop target is the NEXT pose after the jump.
                next_pos = jump_target
                # Walk forward ONE pose to get the canonical first entry.
                n_offset = next_pos - base
                if n_offset >= 0 and n_offset + 16 <= len(data):
                    n_flags = u16(data, n_offset + 2)
                    if not (n_flags & 0x8000):
                        return next_pos
                    else:
                        # The "next" is also negative -- continue walking.
                        address = next_pos
                        continue
                return next_pos
            return address
        # Not a jump; this is a normal pose. Advance 16 bytes and keep walking
        # until we hit the negative-flags loop redirect.
        address += 16
    return address


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
        flags_word = u16(data, offset + 2)
        flip_x = bool(flags_word & 0x8000)
        sequence_index = (flags_word >> 8) & 0x7F
        param_byte = flags_word & 0xFF
        assembly = u32(data, offset + 4)
        tail = data[offset + 8:offset + 16]
        if duration == 0 and flags_word == 0 and assembly == 0:
            status = "terminator"
            break
        records.append({
            "address": f"0x{address:06x}",
            "kind": "pose",
            "duration": duration,
            "word_plus2_raw": f"0x{flags_word:04x}",
            "word_plus2_high_byte": f"0x{flags_word >> 8:02x}",
            "word_plus2_low_byte": f"0x{flags_word & 0xFF:02x}",
            "flip_x": flip_x,
            "sequence_index": sequence_index,
            "param_byte": param_byte,
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
    then one packed long plus one offset word per tile.  Budget is the real
    entry count (48-65 entries across assemblies); tile_count (3-4) is not.
    The packed long and offset-table semantics remain renderer-level data
    until the pixel gate proves their meaning.
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
    for index in range(budget):
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
            layout_address += 4  # Each layout entry is 4 bytes (x_word + y_word)
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
    
    # Deduplicate entry points that are mid-animation snapshots jumping to the same loop.
    canonical_map: dict[int, dict[str, object]] = {}
    snapshot_aliases: list[dict[str, str | int]] = []
    for start in starts:
        canonical = _walker_to_first_pose(start, data, args.base)
        if canonical not in canonical_map:
            canonical_map[canonical] = decode_program(data, args.base, canonical)
        else:
            snapshot_aliases.append({
                "alias_start": f"0x{start:06x}",
                "points_to": f"0x{canonical:06x}",
            })
    programs = list(canonical_map.values())
    
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
            "word_plus2_offset": 2,
            "word_plus2_high_byte": (
                "bit 15 = flip_x; bits 14-8 = 7-bit sequence index"
            ),
            "word_plus2_low_byte": "independent parameter byte",
            "assembly_pointer_offset": 4,
            "tail_bytes": 8,
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
                "flags word at offset +2 splits into flip_x (bit 15), a 7-bit sequence "
                "index, and an 8-bit parameter byte. The tail is not an X/Y word pair: "
                "bytes +8 and +9 index interaction tables."
            ),
        },
        "script_pointer_count": len(starts),
        "unique_program_count": len(programs),
        "snapshot_aliases": snapshot_aliases,
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
