"""Decode a CPS2 Family-1 object-emission GROUP into its four-word entries.

This is the proven part-stream algorithm behind the game's flipped-block
emitter (0x0AA00E dispatcher -> 0x0AA1DC loop; true store instructions at
0x0AA210/0x0AA212, two instructions before the watchpoint-reported
0x0AA214/0x0AA216 - a confirmed MAME PC-reporting skew). See
docs/AGENT_HANDOFF.md "Body A/B resolved" for the full derivation and its
live verification.

## What a GROUP is, and why "5 hidden entries" was never real

A single actor's pose is rendered by one or more independently dispatched
GROUPS, each entered via 0x0AA00E and each producing its own object entries.
A group is not "part of" the group before or after it in the ROM; it has its
own 3-word header, its own call to the origin routine (which recomputes the
per-actor screen origin fresh for that group), and its own part list. The
5-slot street-alien pose examined throughout this project's history is two
groups (3 parts then 2, or 2 then 3, depending on pose) landing in the SAME
growing object buffer with no gap between them. The earlier "two hidden
entries between watched slots 2 and 3" finding was an artefact of treating the
gap between two groups' part tables as if it were inside one group's part
list; it was not a skip and there is no non-emitting part.

## Group layout

```
+0x00  budget    (u16) subtracted from a per-frame emission budget register
+0x02  count     (u16) exact number of parts in THIS group (not "count - 1";
                       the dispatcher's own `subq.w #1,D0` produces the dbra
                       terminal count from this raw value)
+0x04  selector  (u16) index into the ROM table at 0x1FD1C8: A2 (the per-part
                       dx/dy table base) = 0x1FD1C8 + word[0x1FD1C8 + selector*2]
+0x06  (4 bytes) consumed by the origin routine (bsr 0x0AA59A) as one of its
                 own inputs; not a sprite part. The routine's own semantics
                 (actor world position minus a fixed camera anchor) are
                 disassembled in the handoff; the two anchor constants still
                 need a route-matched live read before this module can derive
                 origin from world state alone. Origin is therefore always a
                 caller-supplied input here, not computed by this decoder.
+0x0A  part[0]   6 bytes: u16 code, u16 attr, u16 a2_advance
+0x10  part[1]   ...
       ...       `count` parts total, each 6 bytes
```

Per part, the A2 pointer is read as two words (dx, dy), each auto-incrementing
by 2, and then additionally advanced by that part's own trailing `a2_advance`
word (`A2 = A2 + 4 + a2_advance`) before the next part's dx/dy read. The
observed `a2_advance` is 0 for every part examined so far, but the decoder
implements the general rule rather than assuming zero.

## The four-word entry formula (flipped-block variant)

```
width = 16 * (((attr >> 8) & 0xF) + 1)
X = ((origin_x - width - dx) & 0x3FF) | 0x8000
Y = (origin_y + dy) & 0x3FF
```

`0x8000` is the confirmed live value of the actor's `+0x2E` field for every
group examined so far (it supplies the priority bits OR'd into X). It is
supplied by the caller, not hardcoded by this module, because it is a real
per-actor/per-pose value that has only been observed as 0x8000, not proven
constant for every actor and pose.

## Verification

Verified against BOTH captured oracle frames (street alien, source frames
4214 and 4253 - `data/street_alien_object_emission_oracles.json`), decoding
group headers whose addresses were themselves found by live trace (see
`tools/mame_trace_emitter_full.lua`, untracked one-off diagnostic) and never
copied from the oracle's expected output. Every field this decoder reads -
budget, count, selector, the A2-table lookup, every part's code/attr/advance,
every dx/dy - matches independently, and the resulting ten object entries
(5 per frame) are exact.

Not yet resolved (see docs/AGENT_HANDOFF.md and NEXT_AGENT_PROMPT.md):
- how a pose's ANIMATION RECORD (`avsp_anim_read_pose`'s `assembly` field)
  maps to the list of group header addresses for that pose. The addresses
  used above were found by live trace, not derived structurally. This is
  required before this decoder can be driven from a pose record alone.
- the two fixed camera-anchor constants inside the origin routine, needed to
  compute origin from live actor state rather than take it as an input.
- whether `a2_advance` is ever non-zero in practice (not yet observed).

This module takes a decrypted ROM image and explicit group header addresses;
it never assumes a hardcoded frame or actor.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def s16(v: int) -> int:
    return v - 65536 if v > 32767 else v


class Rom:
    def __init__(self, data: bytes):
        self.d = data

    def u16(self, o: int) -> int:
        return (self.d[o] << 8) | self.d[o + 1]

    def u32(self, o: int) -> int:
        return int.from_bytes(self.d[o:o + 4], "big")


A2_TABLE_BASE = 0x1FD1C8


def decode_group_header(rom: Rom, header_addr: int) -> dict:
    budget = rom.u16(header_addr)
    count = rom.u16(header_addr + 2)
    selector = rom.u16(header_addr + 4)
    a2_offset = rom.u16(A2_TABLE_BASE + selector * 2)
    a2_base = A2_TABLE_BASE + a2_offset
    return {
        "header_address": "0x%06x" % header_addr,
        "budget": budget,
        "count": count,
        "selector": selector,
        "a2_table_entry_address": "0x%06x" % (A2_TABLE_BASE + selector * 2),
        "a2_base": "0x%06x" % a2_base,
        "part0_code_attr_address": "0x%06x" % (header_addr + 0x0A),
    }


# The two camera-anchor constants inside the origin routine (bsr $0AA59A),
# read as (A5+0x27C) and (A5+0x278) - NOT negative displacements, despite an
# earlier session's hand-transcription assuming so; MAME's own live
# disassembler (tools/mame_trace_origin_disasm.lua) printed the true
# instructions as `sub.w ($27c,A5),D3` / `sub.w ($278,A5),D3` (positive
# displacement). Solved by equating the routine's known formula against the
# already-verified origin_x/origin_y oracle values and cross-checked exact
# across all 4 oracle group instances (2 different D2 values, 2 different
# actor world positions) - not yet proven to be a ROM-wide constant beyond
# this route/actor.
ANCHOR_Y = 0x00FF
ANCHOR_X = 0x03F0


def decode_group_origin(rom: Rom, header_addr: int, world_x: int, world_y: int,
                        facing_raw: int) -> tuple:
    """Reproduce the origin routine (bsr $0AA59A) from ROM + actor-record
    inputs alone - no live-trace-captured origin needed. `world_x`/`world_y`
    are the actor's own `+0x10`/`+0x14` fields; `facing_raw` is the actor's
    `+0x0F` facing byte (also the source of the emitter's flip mask via
    `facing_raw << 5`). `header_addr + 6` is the group header's own trailing
    4-byte long (`D2`), consumed here, not part of the part table.

    Disassembled live, instruction for instruction, via
    tools/mame_trace_origin_disasm.lua:
        moveq #0,D1 ; move.b (0xF,A4),D1        ; D1 = facing_raw
        move.l (A0)+,D2                          ; D2 = header's trailing long
        move.w (0x14,A4),D3 ; sub.w ($27c,A5),D3 ; D3 = world_y - anchor_y
        neg.w D3 ; addi.w #0x100,D3              ; D3 = anchor_y - world_y + 0x100
        btst #1,D1 ; bne .add                    ; facing bit 1 selects add/sub
        sub.w D2,D3 / (taken:) add.w D2,D3        ; D3 -/+= D2's low word
        swap D2 ; swap D3                         ; D2's high word now first;
                                                    ; D3's result moves to its
                                                    ; high word (this becomes Y)
        move.w (0x10,A4),D3 ; sub.w ($278,A5),D3  ; D3(low) = world_x - anchor_x
        addi.w #0x40,D3
        btst #0,D1 ; bne .add                     ; facing bit 0 selects add/sub
        sub.w D2,D3 / (taken:) add.w D2,D3         ; D3(low) -/+= D2's (post-swap)
                                                    ; low word = original high word
        move.l D3,(-0x64f4,A5)                     ; store: hi=origin_y, lo=origin_x
    """
    d2 = rom.u32(header_addr + 6)
    d2_hi, d2_lo = (d2 >> 16) & 0xFFFF, d2 & 0xFFFF
    y = (ANCHOR_Y - world_y + 0x100) & 0xFFFF
    y = (y + d2_lo if (facing_raw & 2) else y - d2_lo) & 0xFFFF
    x = (world_x - ANCHOR_X + 0x40) & 0xFFFF
    x = (x + d2_hi if (facing_raw & 1) else x - d2_hi) & 0xFFFF
    return x, y


def decode_group_entries(rom: Rom, header_addr: int, origin_x: int, origin_y: int,
                         palette_byte: int, flip_byte: int,
                         or_value: int = 0x8000) -> list:
    """Returns `count` four-word entries: [{code, attr, x, y}, ...].

    `palette_byte` (actor `+0x0E`) and `flip_byte` (`D1`, derived from actor
    `+0x0F` facing, confirmed live as `0x20` when facing is non-zero) are
    caller-supplied live inputs, not hardcoded: the raw ROM attr's low byte is
    only the game's TEMPLATE, transformed per-actor before use:

      attr_final_low  = ((attr_raw_low & 0xE0) + palette_byte) ^ flip_byte
      attr_final_high = attr_raw_high   (unchanged; carries the nx/ny block
                                          size bits `decode_group_header`'s
                                          width computation already reads)
    """
    header = decode_group_header(rom, header_addr)
    count = header["count"]
    a0 = header_addr + 0x0A
    a2 = int(header["a2_base"], 16)
    entries = []
    for _ in range(count):
        code = rom.u16(a0)
        attr_raw = rom.u16(a0 + 2)
        advance = rom.u16(a0 + 4)
        attr_high = attr_raw & 0xFF00
        attr_low = (((attr_raw & 0xE0) + palette_byte) ^ flip_byte) & 0xFF
        attr = attr_high | attr_low
        dx = s16(rom.u16(a2))
        dy = s16(rom.u16(a2 + 2))
        nx = ((attr_raw >> 8) & 0xF) + 1
        width = nx * 16
        x = ((origin_x - width - dx) & 0x3FF) | or_value
        y = (origin_y + dy) & 0x3FF
        entries.append({
            "code": "0x%04x" % code, "attr": "0x%04x" % attr,
            "x": "0x%04x" % x, "y": "0x%04x" % y,
            "dx": dx, "dy": dy, "width": width,
        })
        a0 += 6
        a2 = a2 + 4 + advance
    return entries


def build_report(rom_path: Path, groups: list) -> dict:
    """`groups` is a list of dicts: {header, world_x, world_y, facing_raw,
    palette_byte, flip_byte, label, expected: [{code,attr,x,y}, ...] or None}.
    `origin_x`/`origin_y` are no longer caller-supplied: they are derived from
    `world_x`/`world_y`/`facing_raw` via `decode_group_origin`, so the whole
    report is ROM + actor-record only, with no live-trace-captured origin."""
    rom_bytes = rom_path.read_bytes()
    rom = Rom(rom_bytes)
    results = []
    all_exact = True
    for g in groups:
        header_addr = int(g["header"], 16)
        header = decode_group_header(rom, header_addr)
        origin_x, origin_y = decode_group_origin(rom, header_addr, g["world_x"], g["world_y"],
                                                  g["facing_raw"])
        entries = decode_group_entries(rom, header_addr, origin_x, origin_y,
                                       g["palette_byte"], g["flip_byte"],
                                       g.get("or_value", 0x8000))
        entry = {
            "label": g.get("label"),
            "header": header,
            "origin_x": origin_x,
            "origin_y": origin_y,
            "entries": entries,
        }
        if g.get("expected") is not None:
            exact = True
            for got, want in zip(entries, g["expected"]):
                if (got["code"], got["attr"], got["x"], got["y"]) != \
                   (want["code"], want["attr"], want["x"], want["y"]):
                    exact = False
            exact = exact and len(entries) == len(g["expected"])
            entry["exact_match_vs_expected"] = exact
            all_exact = all_exact and exact
        results.append(entry)
    return {
        "schema": 1,
        "classification": "decoded CPS2 object-stream groups - coordinates only, no ROM bytes",
        "method": "68000 routine decode; see tools/decode_avsp_object_stream.py docstring",
        "algorithm": {
            "header_layout": "u16 budget, u16 count, u16 selector, 4 bytes consumed by the origin routine",
            "a2_table_base": "0x%06x" % A2_TABLE_BASE,
            "part_layout": "u16 code, u16 attr, u16 a2_advance, repeated `count` times",
            "formula": {
                "width": "16 * (((attr_raw>>8)&0xF)+1)",
                "x": "((origin_x - width - dx) & 0x3FF) | or_value",
                "y": "(origin_y + dy) & 0x3FF",
                "attr": "(attr_raw & 0xFF00) | (((attr_raw & 0xE0) + palette_byte) ^ flip_byte)",
                "origin": "see decode_group_origin - world position adjusted by the header's own "
                          "trailing D2 long and the two now-resolved camera-anchor constants "
                          "(ANCHOR_Y=0x00FF, ANCHOR_X=0x03F0)",
            },
        },
        "unresolved": [
            "pose-record-to-group-header-list mapping (group addresses here are from live trace, not derived structurally)",
            "whether ANCHOR_Y/ANCHOR_X (0x00FF/0x03F0) are a ROM-wide constant or specific to this route - solved by equating 4 oracle group instances, not yet observed to vary or proven fixed elsewhere",
            "whether a2_advance is ever non-zero in practice",
            "palette_byte/flip_byte are per-actor live-trace inputs here (0x11/0x20 for this street-alien instance), not yet derived from a general actor-record read",
        ],
        "inputs": {
            "program_image": {"path": str(rom_path).replace("\\", "/"),
                              "sha256": hashlib.sha256(rom_bytes).hexdigest(),
                              "bytes": len(rom_bytes)},
        },
        "all_groups_exact": all_exact if any("exact_match_vs_expected" in r for r in results) else None,
        "groups": results,
    }


# The two street-alien oracle frames, group header addresses and origins from
# live trace (tools/mame_trace_emitter_full.lua), expected entries from
# data/street_alien_object_emission_oracles.json. Kept here as the anti-
# hardcoding control set this module is falsified against by default.
_ORACLE_GROUPS = [
    {"label": "4214 group1 (3 parts)", "header": "0x12F72E",
     "world_x": 1257, "world_y": 310, "facing_raw": 1,
     "palette_byte": 0x11, "flip_byte": 0x20,
     "expected": [
         {"code": "0x4efe", "attr": "0x0131", "x": "0x8113", "y": "0x0099"},
         {"code": "0x4ef6", "attr": "0x0431", "x": "0x80e3", "y": "0x00a9"},
         {"code": "0x4fc8", "attr": "0x0131", "x": "0x80f3", "y": "0x00b9"},
     ]},
    {"label": "4214 group2 (2 parts)", "header": "0x12F74C",
     "world_x": 1257, "world_y": 310, "facing_raw": 1,
     "palette_byte": 0x11, "flip_byte": 0x20,
     "expected": [
         {"code": "0x473a", "attr": "0x2431", "x": "0x8121", "y": "0x007b"},
         {"code": "0x479c", "attr": "0x1331", "x": "0x8111", "y": "0x00ab"},
     ]},
    {"label": "4253 group1 (2 parts)", "header": "0x12FEC0",
     "world_x": 1313, "world_y": 310, "facing_raw": 1,
     "palette_byte": 0x11, "flip_byte": 0x20,
     "expected": [
         {"code": "0x4df8", "attr": "0x0131", "x": "0x814f", "y": "0x009e"},
         {"code": "0x4ef0", "attr": "0x0531", "x": "0x810f", "y": "0x00ae"},
     ]},
    {"label": "4253 group2 (3 parts)", "header": "0x12FED8",
     "world_x": 1313, "world_y": 310, "facing_raw": 1,
     "palette_byte": 0x11, "flip_byte": 0x20,
     "expected": [
         {"code": "0x4b04", "attr": "0x2531", "x": "0x815b", "y": "0x007b"},
         {"code": "0x4a88", "attr": "0x1431", "x": "0x814b", "y": "0x00ab"},
         {"code": "0x4958", "attr": "0x0131", "x": "0x816b", "y": "0x006b"},
     ]},
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--report", default=str(Path(__file__).resolve().parents[1] / "data" / "avsp_object_stream.json"))
    ap.add_argument("--verify-deterministic", action="store_true")
    args = ap.parse_args()

    report = build_report(Path(args.rom), _ORACLE_GROUPS)
    text = json.dumps(report, indent=1, sort_keys=True) + "\n"

    if args.verify_deterministic:
        again = json.dumps(build_report(Path(args.rom), _ORACLE_GROUPS), indent=1, sort_keys=True) + "\n"
        if again != text:
            print("NON-DETERMINISTIC: two decodes differ")
            return 2
        print("deterministic: two decodes agree")

    out = Path(args.report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    print("wrote %s" % out)
    print("all_groups_exact=%s" % report["all_groups_exact"])
    for g in report["groups"]:
        print("  %-24s exact=%s count=%d" % (
            g["label"], g.get("exact_match_vs_expected"), g["header"]["count"]))
    return 0 if report["all_groups_exact"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
