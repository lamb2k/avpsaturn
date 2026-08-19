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
                 own inputs (`D2`); not a sprite part. `decode_group_origin`
                 reproduces the routine exactly (live-disassembled via MAME's
                 own trace facility, not the static ROM dump, which reads as
                 garbage at this code address): origin is actor world
                 position (`+0x10`/`+0x14`) adjusted by this D2 long (split by
                 a `swap`, one half per axis, added or subtracted per a
                 facing-conditional branch) and two now-resolved camera-anchor
                 constants (`ANCHOR_Y=0x00FF`, `ANCHOR_X=0x03F0`, solved by
                 equating the formula against 4 independent oracle group
                 instances and cross-verified identical in every case). Origin
                 is therefore ROM + actor-record derived, not a caller-supplied
                 live-trace value.
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
  maps to the list of group header addresses for that pose (n=2, both from
  this one street-alien actor - `group1_header = pose.assembly + 4`, then a
  fixed per-group stride; not yet proven to generalize past this actor/pose).
- whether `ANCHOR_Y`/`ANCHOR_X` and the "exactly 2 groups per actor-frame"
  dispatch count are ROM-wide constants or specific to this route/actor.
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

# Every group is announced by this 2-byte tag immediately before its 3-word
# header - not just the first group in a pose's list, but every subsequent
# one too (the tag reappears at the position the previous group's own stride
# lands on). This matches avsp_anim_script.h's own naming for the pose
# `assembly` field ("selector-6 assembly"): what looked at first like a
# fixed "assembly+4" offset was really "scan forward from assembly for this
# tag", and the earlier "+12+count*6 stride to the next group" finding is
# the SAME mechanism applied again, not a second rule.
GROUP_TAG = 0x0006


def find_group_header(rom: Rom, scan_from: int, max_scan: int = 8) -> int:
    """Find the first group header starting at-or-after `scan_from` (usually
    a pose's `assembly` field) by locating the GROUP_TAG word. Returns the
    header address (tag address + 2), or None if not found within
    `max_scan` bytes. Verified exact against 5 independent (actor, pose)
    pairs across 2 actors - see docs/AGENT_HANDOFF.md."""
    for off in range(0, max_scan, 2):
        if rom.u16(scan_from + off) == GROUP_TAG:
            return scan_from + off + 2
    return None


def next_group_header(rom: Rom, header_addr: int, count: int) -> int:
    """Address the NEXT group's header would occupy if this pose dispatches
    another group after this one - i.e. `find_group_header` starting right
    after this group's own data. A GROUP_TAG existing there is NECESSARY but
    NOT SUFFICIENT proof the game actually dispatches it: a plausible-looking
    "group 3" tag follows both already-verified 2-group poses in the oracle,
    but a live trace independently proved the dispatcher never calls it for
    those poses. How many groups a given pose actually uses is a separate,
    still-unresolved fact (apparently fixed per actor TYPE, not per pose) -
    callers must supply the group count externally (live-trace-confirmed),
    not infer it from tag presence alone."""
    return header_addr + 12 + count * 6


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


# The two camera-anchor values inside the origin routine (bsr $0AA59A),
# read from RAM at (A5+0x27C) and (A5+0x278) - positive displacements per
# MAME's own live disassembler (tools/mame_trace_origin_disasm.lua), not the
# negative ones an earlier hand-transcription assumed. They are NOT ROM
# constants: they are live camera state, derived from the CPS-A scroll1
# registers (corpus-verified across two routes with different camera
# positions - street window scroll1=(944,513) -> anchors (1008,255);
# stalker window scroll1=(747,544) -> anchors (811,224)):
#
#   anchor_x = scroll1_x + 0x40
#   anchor_y = 0x300 - scroll1_y
#
# The module-level defaults below are the street-window values, kept so the
# tracked oracle set (captured in that window) stays self-contained.
ANCHOR_Y = 0x00FF
ANCHOR_X = 0x03F0


def anchors_from_scroll(scroll1_x: int, scroll1_y: int) -> tuple:
    """Camera anchors from the CPS-A scroll1 registers (see comment above)."""
    return (scroll1_x + 0x40) & 0xFFFF, (0x300 - scroll1_y) & 0xFFFF


def decode_group_origin(rom: Rom, header_addr: int, world_x: int, world_y: int,
                        facing_raw: int, anchor_x: int = ANCHOR_X,
                        anchor_y: int = ANCHOR_Y) -> tuple:
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
    y = (anchor_y - world_y + 0x100) & 0xFFFF
    y = (y + d2_lo if (facing_raw & 2) else y - d2_lo) & 0xFFFF
    x = (world_x - anchor_x + 0x40) & 0xFFFF
    x = (x + d2_hi if (facing_raw & 1) else x - d2_hi) & 0xFFFF
    return x, y


def decode_family2_entry(rom: Rom, record_addr: int, world_x: int, world_y: int,
                         facing_raw: int, palette_byte: int, or_value: int,
                         anchor_x: int = ANCHOR_X,
                         anchor_y: int = ANCHOR_Y,
                         coord_mode_positive: bool = True) -> dict:
    """Family-0x0002: a single-entry record with inline code/attr.

    Live-disassembled (tools/mame_trace_family2b.lua) at its jump-table
    handler 0x0A9D52 (fresh-budget entry 0x0A9D4A):

        move.w (A0)+,D0            ; attr raw
        tst.b (0xD,A4) ; beq/bmi   ; positive coordinate mode only:
        andi.b #0xE0,D0            ;   attr low = (raw & 0xE0) + palette
        add.b (0xE,A4),D0
        move.w (A0)+,D2 ; ...      ; selector -> A2 via the 0x1FD1C8 table
        bsr $0AA59A                ; SAME origin routine (consumes D2 long)
        eor.b D1,D0                ; attr ^= flip mask
        bsr $0A9D8C                ; X/Y: plain path identical to family-6's
                                   ;   plain loop (X = origin_x + dx,
                                   ;   Y = origin_y + dy); flip paths branch
                                   ;   on D1 bits 5 (X) and 6 (Y)
        move.l D3,(A1)+            ; store X,Y
        move.w (A0)+,(A1)+         ; store code (read straight from record)
        move.w D0,(A1)+            ; store attr

    `record_addr` points at the record's payload (after [tag][budget]):
    [attr u16][selector u16][D2 u32][code u16] = 10 bytes.

    The flipped (facing bit set) X path at 0x0A9D9E is not yet traced; the
    flipped formula used here (origin - width - dx, mirroring family-6) is
    corpus-verified, not disassembly-verified - falsified against every
    flipped family-2 instance in the captured corpus."""
    attr_raw = rom.u16(record_addr)
    selector = rom.u16(record_addr + 2)
    code = rom.u16(record_addr + 8)
    a2 = A2_TABLE_BASE + rom.u16(A2_TABLE_BASE + selector * 2)
    dx = s16(rom.u16(a2))
    dy = s16(rom.u16(a2 + 2))

    # origin: header_addr semantics in decode_group_origin expect the D2
    # long at header+6; here it sits at record+4.
    d2 = rom.u32(record_addr + 4)
    d2_hi, d2_lo = (d2 >> 16) & 0xFFFF, d2 & 0xFFFF
    oy = (anchor_y - world_y + 0x100) & 0xFFFF
    oy = (oy + d2_lo if (facing_raw & 2) else oy - d2_lo) & 0xFFFF
    ox = (world_x - anchor_x + 0x40) & 0xFFFF
    ox = (ox + d2_hi if (facing_raw & 1) else ox - d2_hi) & 0xFFFF

    flip = (facing_raw << 5) & 0xFF
    if coord_mode_positive:
        attr = (attr_raw & 0xFF00) | ((((attr_raw & 0xE0) + palette_byte) ^ flip) & 0xFF)
    else:
        # family-2's +0x0D <= 0 path skips only the palette add (beq/bmi
        # $a9d68); its eor.b D1,D0 at 0x0A9D7E is unconditional.
        attr = (attr_raw & 0xFF00) | (((attr_raw & 0xFF) ^ flip) & 0xFF)
    if facing_raw & 1:
        width = ((((attr_raw >> 8) & 0xF) + 1) * 16)
        x = ((ox - width - dx) & 0x3FF) | or_value
    else:
        x = ((ox + dx) & 0x3FF) | or_value
    y = (oy + dy) & 0x3FF
    return {"code": "0x%04x" % code, "attr": "0x%04x" % attr,
            "x": "0x%04x" % x, "y": "0x%04x" % y}


def decode_group_entries(rom: Rom, header_addr: int, origin_x: int, origin_y: int,
                         palette_byte: int, facing_raw: int,
                         or_value: int = 0x8000,
                         mode_positive: bool = True,
                         has_advance: bool = True) -> list:
    """Returns `count` four-word entries: [{code, attr, x, y}, ...].

    `palette_byte` (actor `+0x0E`) is a plain actor-record field, read the
    same way as `world_x`/`world_y`. `facing_raw` (actor `+0x0F`) is the same
    value `decode_group_origin` takes; the emitter's flip mask is not an
    independent input - the origin routine's own `lsl.b #5,D1` (see
    `decode_group_origin`'s docstring) proves it is exactly
    `(facing_raw << 5) & 0xFF`, derived here rather than supplied separately.
    The raw ROM attr's low byte is only the game's TEMPLATE, transformed
    per-actor before use:

      attr_final_low  = ((attr_raw_low & 0xE0) + palette_byte) ^ flip_byte
      attr_final_high = attr_raw_high   (unchanged; carries the nx/ny block
                                          size bits `decode_group_header`'s
                                          width computation already reads)
    """
    flip_byte = (facing_raw << 5) & 0xFF
    header = decode_group_header(rom, header_addr)
    count = header["count"]
    a0 = header_addr + 0x0A
    a2 = int(header["a2_base"], 16)
    entries = []
    for _ in range(count):
        code = rom.u16(a0)
        attr_raw = rom.u16(a0 + 2)
        # Family 0x0004 (handler 0x0A9DEE; layout decoded offline from the
        # retained tag-4 write-tap + ROM bytes): identical to family 6 but
        # parts are 4 bytes (code, attr) with NO advance word - fixed A2
        # stride of one dx/dy pair per part.
        advance = rom.u16(a0 + 4) if has_advance else 0
        if mode_positive:
            attr = (attr_raw & 0xFF00) | ((((attr_raw & 0xE0) + palette_byte)
                                           ^ flip_byte) & 0xFF)
        else:
            # +0x0D <= 0 mode (live-disassembled at 0x0AA09A via
            # tools/mame_trace_coordmode.lua, flip contribution
            # corpus-derived): no palette injection, but the flip XOR still
            # applies - the facing=0 trace stores the record long raw, and
            # every flipped instance in the corpus differs from raw by
            # exactly bit 5. Same origin routine, same X/Y formulas;
            # "coordinate mode" is really an attr-transform mode.
            attr = (attr_raw & 0xFF00) | ((attr_raw ^ flip_byte) & 0xFF)
        dx = s16(rom.u16(a2))
        dy = s16(rom.u16(a2 + 2))
        nx = ((attr_raw >> 8) & 0xF) + 1
        width = nx * 16
        # The dispatcher (0x0AA00E; live-disassembled in full via
        # tools/mame_trace_facing0.lua) selects one of two loop bodies on the
        # origin routine's Z flag (set by its final `lsl.b #5,D1`, i.e. by
        # facing == 0):
        #   facing != 0 -> flipped loop  (0x0AA1DC..): X = origin - width - dx,
        #                  attr low byte ^= flip mask (0x20)
        #   facing == 0 -> plain loop (0x0AA1A8..0x0AA1DA): X = origin + dx,
        #                  no width term, no XOR (flip_byte is 0 here anyway)
        # Both walk A2 identically: dx, dy reads then A2 += advance.
        if facing_raw:
            x = ((origin_x - width - dx) & 0x3FF) | or_value
        else:
            x = ((origin_x + dx) & 0x3FF) | or_value
        y = (origin_y + dy) & 0x3FF
        entries.append({
            "code": "0x%04x" % code, "attr": "0x%04x" % attr,
            "x": "0x%04x" % x, "y": "0x%04x" % y,
            "dx": dx, "dy": dy, "width": width,
        })
        a0 += 6 if has_advance else 4
        a2 = a2 + 4 + advance
    return entries


def build_report(rom_path: Path, groups: list) -> dict:
    """`groups` is a list of dicts: {header, world_x, world_y, facing_raw,
    palette_byte, label, expected: [{code,attr,x,y}, ...] or None}.
    `origin_x`/`origin_y` are no longer caller-supplied: they are derived from
    `world_x`/`world_y`/`facing_raw` via `decode_group_origin`, and the attr
    flip byte is derived from that same `facing_raw` (see
    `decode_group_entries`), so the whole report is ROM + actor-record only,
    with no live-trace-captured value anywhere in the calculation."""
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
                                       g["palette_byte"], g["facing_raw"],
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
                "attr": "(attr_raw & 0xFF00) | (((attr_raw & 0xE0) + palette_byte) ^ ((facing_raw<<5)&0xFF))",
                "origin": "see decode_group_origin - world position adjusted by the header's own "
                          "trailing D2 long and the two now-resolved camera-anchor constants "
                          "(ANCHOR_Y=0x00FF, ANCHOR_X=0x03F0)",
            },
        },
        "unresolved": [
            "pose-record-to-group-header-list mapping (group addresses here are from live trace, not derived structurally; n=2, both this one street-alien actor)",
            "whether ANCHOR_Y/ANCHOR_X (0x00FF/0x03F0) and the exactly-2-groups-per-actor-frame dispatch count are ROM-wide constants or specific to this route/actor - solved/observed on 4 oracle group instances, all from one actor",
            "whether a2_advance is ever non-zero in practice",
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
     "palette_byte": 0x11,
     "expected": [
         {"code": "0x4efe", "attr": "0x0131", "x": "0x8113", "y": "0x0099"},
         {"code": "0x4ef6", "attr": "0x0431", "x": "0x80e3", "y": "0x00a9"},
         {"code": "0x4fc8", "attr": "0x0131", "x": "0x80f3", "y": "0x00b9"},
     ]},
    {"label": "4214 group2 (2 parts)", "header": "0x12F74C",
     "world_x": 1257, "world_y": 310, "facing_raw": 1,
     "palette_byte": 0x11,
     "expected": [
         {"code": "0x473a", "attr": "0x2431", "x": "0x8121", "y": "0x007b"},
         {"code": "0x479c", "attr": "0x1331", "x": "0x8111", "y": "0x00ab"},
     ]},
    {"label": "4253 group1 (2 parts)", "header": "0x12FEC0",
     "world_x": 1313, "world_y": 310, "facing_raw": 1,
     "palette_byte": 0x11,
     "expected": [
         {"code": "0x4df8", "attr": "0x0131", "x": "0x814f", "y": "0x009e"},
         {"code": "0x4ef0", "attr": "0x0531", "x": "0x810f", "y": "0x00ae"},
     ]},
    {"label": "4253 group2 (3 parts)", "header": "0x12FED8",
     "world_x": 1313, "world_y": 310, "facing_raw": 1,
     "palette_byte": 0x11,
     "expected": [
         {"code": "0x4b04", "attr": "0x2531", "x": "0x815b", "y": "0x007b"},
         {"code": "0x4a88", "attr": "0x1431", "x": "0x814b", "y": "0x00ab"},
         {"code": "0x4958", "attr": "0x0131", "x": "0x816b", "y": "0x006b"},
     ]},
    # A SECOND, independent actor (0xFFFFA000, not the tracked street alien),
    # same frame window, different palette byte and poses - added specifically
    # to test generalization beyond the one actor/pose pair above. Header
    # addresses and expected entries are ground truth from a live entry-point
    # breakpoint (0x0AA00E, a0 == the header address before any part read) and
    # the object-buffer write tap, both a6-conditioned to this actor
    # (tools/mame_trace_actor2.lua, untracked one-off). world_x/world_y/
    # facing_raw/palette_byte are this actor's own record fields, read the
    # same way as the first actor's. This independently confirms the origin
    # formula (same ANCHOR_Y/ANCHOR_X, no per-actor tuning) and the attr
    # transform (different palette_byte=0x10) generalize; it does NOT test
    # the pose.assembly+4 header-derivation rule, which is known NOT to
    # generalize to this actor (predicted 0x12F7D0, real header is 0x12F7CE) -
    # these header addresses are supplied directly, not derived from a pose.
    {"label": "actor2 4214-ish header 0x12F7CE (2 parts)", "header": "0x12F7CE",
     "world_x": 1181, "world_y": 297, "facing_raw": 1,
     "palette_byte": 0x10,
     "expected": [
         {"code": "0x46f0", "attr": "0x0930", "x": "0x8085", "y": "0x00c8"},
         {"code": "0x5060", "attr": "0x2630", "x": "0x8095", "y": "0x0098"},
     ]},
    {"label": "actor2 4214-ish header 0x12F7E6 (2 parts)", "header": "0x12F7E6",
     "world_x": 1181, "world_y": 297, "facing_raw": 1,
     "palette_byte": 0x10,
     "expected": [
         {"code": "0x4800", "attr": "0x0930", "x": "0x8075", "y": "0x00c8"},
         {"code": "0x5090", "attr": "0x2530", "x": "0x80a5", "y": "0x0098"},
     ]},
    {"label": "actor2 4214-ish header 0x12F7FE (2 parts)", "header": "0x12F7FE",
     "world_x": 1181, "world_y": 297, "facing_raw": 1,
     "palette_byte": 0x10,
     "expected": [
         {"code": "0x4830", "attr": "0x1830", "x": "0x8085", "y": "0x00b8"},
         {"code": "0x50c0", "attr": "0x1530", "x": "0x8095", "y": "0x0098"},
     ]},
]

# (pose record address, expected group1 header address) - ground truth for
# `find_group_header`, all from live traces: actor1's two poses (each a
# 2-group dispatch) and actor2's three poses (each a 1-group dispatch),
# confirmed via a live entry-point breakpoint (a0 at 0x0AA00E) reading the
# actor's own pose pointer at the exact moment of dispatch, not a
# separately-sampled snapshot. See docs/AGENT_HANDOFF.md for the derivation.
_POSE_HEADER_ORACLE = [
    (0x0012EB4C, 0x0012F72E),
    (0x0012D8A0, 0x0012FEC0),
    (0x0012EC04, 0x0012F7CE),
    (0x0012EC14, 0x0012F7E6),
    (0x0012EC24, 0x0012F7FE),
]


def verify_pose_header_chain(rom: Rom) -> bool:
    ok = True
    for pose_addr, expected_header in _POSE_HEADER_ORACLE:
        assembly = rom.u32(pose_addr + 4)
        found = find_group_header(rom, assembly)
        passed = found == expected_header
        ok = ok and passed
        print("  pose=0x%06x assembly=0x%06x -> header=0x%06x expected=0x%06x %s" %
              (pose_addr, assembly, found or 0, expected_header, "OK" if passed else "MISMATCH"))
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--report", default=str(Path(__file__).resolve().parents[1] / "data" / "avsp_object_stream.json"))
    ap.add_argument("--verify-deterministic", action="store_true")
    args = ap.parse_args()

    rom_for_chain = Rom(Path(args.rom).read_bytes())
    print("pose-to-group-header chain (find_group_header):")
    chain_ok = verify_pose_header_chain(rom_for_chain)
    print("pose-header chain: %s" % ("ALL EXACT" if chain_ok else "MISMATCH"))

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
    return 0 if (report["all_groups_exact"] and chain_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
