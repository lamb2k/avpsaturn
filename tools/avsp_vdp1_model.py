"""Saturn VDP1 command table: decode and control-flow traversal.

Walks a captured VDP1 VRAM image the way the hardware command processor does -
following the jump/call/return/skip modes in CMDCTRL - instead of assuming the
list is stored sequentially. `sequential_scan` and `stored_nonzero_slots` keep
the stored-order readings so a report can state reachable and stored counts
separately.

That separation is the whole point. A VDP1 command table retains whatever a
longer earlier list wrote past the current terminator, so a naive scan
overcounts: the reference measurement that motivated this port saw 772 stored
non-zero slots against 296 reachable commands at the same anchor. Reporting
"stored" as if it were "drawn" is the trap.

AvP has no other VDP1 tooling. This is not needed by the current runtime; it
exists for S6 hardware-performance work and to settle the per-object versus
per-tile renderer fork with real reachable-command counts rather than
estimates. See data/avsp_stage_scroll.json's sibling measurements for the
CPS2-side halves of that question.

Command-word layout is Sega's published VDP1 command table format - Saturn
hardware, not title-specific. Everything this module reports about a captured
list is MEASURED.

PROVENANCE: retargeted from the isolated reference lane at its immutable
checkpoint (branch `codex/mshvsf-reference-lane`, `dc5d3ea`), analysis half
only. The generation half and every reference-title constant were deliberately
left behind; no measurement, budget, asset or gameplay constant from that lane
crossed into this file. Per that lane's transfer rules, no count measured on
another title is ever a budget here.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import Iterator

#: One VDP1 command occupies 32 bytes (16 big-endian words).
SLOT_BYTES = 0x20
WORDS_PER_COMMAND = 16

#: CMDCTRL bit 15. The command processor stops *before* drawing this command.
END_BIT = 0x8000

# --- CMDCTRL bits 14-12: jump mode -----------------------------------------
JUMP_NEXT = 0
JUMP_ASSIGN = 1
JUMP_CALL = 2
JUMP_RETURN = 3
SKIP_NEXT = 4
SKIP_ASSIGN = 5
SKIP_CALL = 6
SKIP_RETURN = 7

JUMP_MODE_NAMES = {
    JUMP_NEXT: "JUMP_NEXT",
    JUMP_ASSIGN: "JUMP_ASSIGN",
    JUMP_CALL: "JUMP_CALL",
    JUMP_RETURN: "JUMP_RETURN",
    SKIP_NEXT: "SKIP_NEXT",
    SKIP_ASSIGN: "SKIP_ASSIGN",
    SKIP_CALL: "SKIP_CALL",
    SKIP_RETURN: "SKIP_RETURN",
}

#: Modes whose command is *not* drawn but which still route control flow.
SKIP_MODES = frozenset({SKIP_NEXT, SKIP_ASSIGN, SKIP_CALL, SKIP_RETURN})
#: Modes that take their next address from CMDLINK.
LINK_MODES = frozenset({JUMP_ASSIGN, JUMP_CALL, SKIP_ASSIGN, SKIP_CALL})
#: Modes that save a return address before branching.
CALL_MODES = frozenset({JUMP_CALL, SKIP_CALL})
#: Modes that consume the saved return address.
RETURN_MODES = frozenset({JUMP_RETURN, SKIP_RETURN})

# --- CMDCTRL bits 3-0: command type ----------------------------------------
COMMAND_NAMES = {
    0x0: "NORMAL_SPRITE",
    0x1: "SCALED_SPRITE",
    0x2: "DISTORTED_SPRITE",
    0x3: "DISTORTED_SPRITE_ALT",
    0x4: "POLYGON",
    0x5: "POLYLINE",
    0x6: "LINE",
    0x7: "POLYLINE_ALT",
    0x8: "USER_CLIP",
    0x9: "SYSTEM_CLIP",
    0xA: "LOCAL_COORDINATE",
}
#: Command types that put pixels in the framebuffer.
DRAW_COMMANDS = frozenset({0x0, 0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7})
#: Command types that only change renderer state.
STATE_COMMANDS = frozenset({0x8, 0x9, 0xA})

#: CMDCTRL bit 4 / bit 5: character read direction (horizontal / vertical flip).
FLIP_X_BIT = 0x0010
FLIP_Y_BIT = 0x0020

#: CMDPMOD bits 5-3 == 0 selects 16-colour bank mode; CMDCOLR is then the
#: CRAM colour-bank address, and banks are 16 entries apart.
COLOR_MODE_16_BANK = 0
COLOR_BANK_STRIDE = 0x10

#: CMDSRCA stores the texture address divided by eight.
SRCA_SHIFT = 3
#: CMDSIZE bits 13-8 hold width/8; bits 7-0 hold height in lines.
SIZE_WIDTH_SHIFT = 8
SIZE_WIDTH_MASK = 0x3F
SIZE_HEIGHT_MASK = 0xFF


def _s13(value: int) -> int:
    """VDP1 coordinates are 13-bit two's complement inside a 16-bit word."""
    value &= 0x1FFF
    return value - 0x2000 if value & 0x1000 else value


@dataclass(frozen=True)
class Vdp1Command:
    """One decoded or generated VDP1 command table entry."""

    offset: int
    words: tuple[int, ...]

    # -- CMDCTRL views ------------------------------------------------------
    @property
    def control(self) -> int:
        return self.words[0]

    @property
    def is_end(self) -> bool:
        return bool(self.control & END_BIT)

    @property
    def jump_mode(self) -> int:
        return (self.control >> 12) & 0x7

    @property
    def jump_mode_name(self) -> str:
        return JUMP_MODE_NAMES[self.jump_mode]

    @property
    def is_skipped(self) -> bool:
        return self.jump_mode in SKIP_MODES

    @property
    def command_type(self) -> int:
        return self.control & 0xF

    @property
    def command_name(self) -> str:
        return COMMAND_NAMES.get(self.command_type, "UNDEFINED_%X" % self.command_type)

    @property
    def flip_x(self) -> bool:
        return bool(self.control & FLIP_X_BIT)

    @property
    def flip_y(self) -> bool:
        return bool(self.control & FLIP_Y_BIT)

    @property
    def zoom_point(self) -> int:
        return (self.control >> 8) & 0xF

    # -- other words --------------------------------------------------------
    @property
    def link(self) -> int:
        """CMDLINK as a byte address; the register stores address/8."""
        return self.words[1] << SRCA_SHIFT

    @property
    def pmod(self) -> int:
        return self.words[2]

    @property
    def color_mode(self) -> int:
        return (self.pmod >> 3) & 0x7

    @property
    def color_control(self) -> int:
        return self.words[3]

    @property
    def source_address(self) -> int:
        return self.words[4] << SRCA_SHIFT

    @property
    def width(self) -> int:
        return ((self.words[5] >> SIZE_WIDTH_SHIFT) & SIZE_WIDTH_MASK) * 8

    @property
    def height(self) -> int:
        return self.words[5] & SIZE_HEIGHT_MASK

    @property
    def vertices(self) -> tuple[int, ...]:
        return tuple(_s13(word) for word in self.words[6:14])

    @property
    def texture_bytes(self) -> int:
        """Bytes the texture occupies for this command's colour mode."""
        pixels = self.width * self.height
        if self.color_mode in (0, 1):
            return pixels // 2
        if self.color_mode in (2, 3, 4):
            return pixels
        return pixels * 2

    def to_json(self) -> dict[str, object]:
        record: dict[str, object] = {
            "slot": self.offset // SLOT_BYTES,
            "offset": "0x%06X" % self.offset,
            "control": "0x%04X" % self.control,
            "command": self.command_name,
            "jump_mode": self.jump_mode_name,
            "end": self.is_end,
        }
        if self.command_type in DRAW_COMMANDS:
            record.update(
                {
                    "flip_x": self.flip_x,
                    "flip_y": self.flip_y,
                    "color_mode": self.color_mode,
                    "color_control": "0x%04X" % self.color_control,
                    "source_address": "0x%06X" % self.source_address,
                    "size": [self.width, self.height],
                    "texture_bytes": self.texture_bytes,
                }
            )
        if self.jump_mode in LINK_MODES:
            record["link"] = "0x%06X" % self.link
        return record


def decode_command(vram: bytes, offset: int) -> Vdp1Command:
    """Decode the 32-byte command at ``offset``. Raises on a short read."""
    if offset < 0 or offset + SLOT_BYTES > len(vram):
        raise IndexError(
            "VDP1 command at 0x%06X is outside the %d-byte image" % (offset, len(vram))
        )
    words = struct.unpack_from(">%dH" % WORDS_PER_COMMAND, vram, offset)
    return Vdp1Command(offset=offset, words=words)


@dataclass
class TraversalResult:
    """What the command processor would actually reach from a start address."""

    start: int
    visited: list[Vdp1Command] = field(default_factory=list)
    #: (from_offset, to_offset, mode_name) for every non-fallthrough edge.
    links_followed: list[tuple[int, int, str]] = field(default_factory=list)
    #: Human-readable reasons the walk stopped or found broken control flow.
    anomalies: list[str] = field(default_factory=list)
    terminated: bool = False
    stop_reason: str = ""

    # -- derived counts -----------------------------------------------------
    @property
    def reachable_slot_count(self) -> int:
        """Distinct command slots the processor visits, terminator included."""
        return len(self.visited)

    @property
    def drawn_command_count(self) -> int:
        return sum(
            1
            for c in self.visited
            if c.command_type in DRAW_COMMANDS and not c.is_skipped and not c.is_end
        )

    @property
    def skipped_command_count(self) -> int:
        return sum(1 for c in self.visited if c.is_skipped and not c.is_end)

    @property
    def state_command_count(self) -> int:
        return sum(1 for c in self.visited if c.command_type in STATE_COMMANDS and not c.is_end)

    @property
    def command_table_bytes(self) -> int:
        return self.reachable_slot_count * SLOT_BYTES

    def command_type_histogram(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for command in self.visited:
            key = "DRAW_END" if command.is_end else command.command_name
            counts[key] = counts.get(key, 0) + 1
        return dict(sorted(counts.items()))

    def jump_mode_histogram(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for command in self.visited:
            counts[command.jump_mode_name] = counts.get(command.jump_mode_name, 0) + 1
        return dict(sorted(counts.items()))

    def flip_histogram(self) -> dict[str, int]:
        counts = {"NONE": 0, "FLIP_X": 0, "FLIP_Y": 0, "FLIP_XY": 0}
        keys = {
            (False, False): "NONE",
            (True, False): "FLIP_X",
            (False, True): "FLIP_Y",
            (True, True): "FLIP_XY",
        }
        for command in self.visited:
            if command.command_type not in DRAW_COMMANDS or command.is_end:
                continue
            counts[keys[(command.flip_x, command.flip_y)]] += 1
        return counts

    def size_histogram(self) -> dict[str, int]:
        """How many drawn commands use each WxH sprite size."""
        counts: dict[str, int] = {}
        for command in self.visited:
            if command.command_type not in DRAW_COMMANDS or command.is_end:
                continue
            key = "%dx%d" % (command.width, command.height)
            counts[key] = counts.get(key, 0) + 1
        return dict(sorted(counts.items()))

    def color_banks(self) -> list[int]:
        banks = {
            command.color_control
            for command in self.visited
            if command.command_type in DRAW_COMMANDS
            and not command.is_end
            and command.color_mode == COLOR_MODE_16_BANK
        }
        return sorted(banks)

    def texture_spans(self) -> list[tuple[int, int]]:
        """Merged [start, end) byte spans of every referenced texture."""
        raw = sorted(
            (command.source_address, command.source_address + command.texture_bytes)
            for command in self.visited
            if command.command_type in DRAW_COMMANDS
            and not command.is_end
            and command.texture_bytes > 0
        )
        merged: list[list[int]] = []
        for start, end in raw:
            if merged and start <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])
        return [(start, end) for start, end in merged]

    def texture_bytes_referenced(self) -> int:
        return sum(end - start for start, end in self.texture_spans())


def traverse(vram: bytes, start: int = 0, max_steps: int = 65536) -> TraversalResult:
    """Walk the command list from ``start`` following real VDP1 control flow.

    Honours jump-next/assign/call/return and their skip variants, the single
    hardware return-address register, and the draw-end bit. Revisiting a slot
    stops the walk and is reported as a loop anomaly rather than spinning.
    """
    result = TraversalResult(start=start)
    seen: set[int] = set()
    return_address: int | None = None
    address = start

    for _ in range(max_steps):
        if address % SLOT_BYTES:
            result.anomalies.append(
                "unaligned command address 0x%06X (not a 32-byte slot)" % address
            )
            result.stop_reason = "unaligned_address"
            return result
        if address < 0 or address + SLOT_BYTES > len(vram):
            result.anomalies.append("command address 0x%06X outside VRAM image" % address)
            result.stop_reason = "out_of_range"
            return result
        if address in seen:
            result.anomalies.append("control flow revisits slot 0x%06X" % address)
            result.stop_reason = "loop_detected"
            return result

        seen.add(address)
        command = decode_command(vram, address)
        result.visited.append(command)

        if command.is_end:
            result.terminated = True
            result.stop_reason = "draw_end"
            return result

        mode = command.jump_mode
        if mode in CALL_MODES:
            if return_address is not None:
                result.anomalies.append(
                    "nested call at 0x%06X overwrites the pending return address" % address
                )
            return_address = address + SLOT_BYTES

        if mode in RETURN_MODES:
            if return_address is None:
                result.anomalies.append(
                    "return at 0x%06X with no saved return address" % address
                )
                result.stop_reason = "unmatched_return"
                return result
            nxt = return_address
            return_address = None
        elif mode in LINK_MODES:
            nxt = command.link
            if nxt % SLOT_BYTES:
                result.anomalies.append(
                    "CMDLINK at 0x%06X targets non-slot address 0x%06X" % (address, nxt)
                )
        else:
            nxt = address + SLOT_BYTES

        if nxt != address + SLOT_BYTES:
            result.links_followed.append((address, nxt, command.jump_mode_name))
        address = nxt

    result.anomalies.append("traversal exceeded %d steps without a draw-end" % max_steps)
    result.stop_reason = "step_limit"
    return result


def sequential_scan(vram: bytes, start: int = 0, limit: int | None = None) -> list[Vdp1Command]:
    """Read commands in *stored* order until the draw-end bit, ignoring links.

    This reproduces the earlier analysis. It equals ``traverse`` only when every
    reachable command uses jump-next; comparing the two is the point.
    """
    end = len(vram) if limit is None else min(len(vram), start + limit)
    commands: list[Vdp1Command] = []
    for offset in range(start, end - SLOT_BYTES + 1, SLOT_BYTES):
        command = decode_command(vram, offset)
        commands.append(command)
        if command.is_end:
            break
    return commands


def stored_nonzero_slots(vram: bytes, start: int = 0) -> int:
    """Count contiguous non-zero 32-byte slots from ``start``.

    This is a *residue* measurement: a command table keeps whatever a longer
    earlier list wrote past the current terminator. It is an observation of
    written extent, not an allocator high-water mark.
    """
    zero = bytes(SLOT_BYTES)
    count = 0
    for offset in range(start, len(vram) - SLOT_BYTES + 1, SLOT_BYTES):
        if vram[offset : offset + SLOT_BYTES] == zero:
            break
        count += 1
    return count
