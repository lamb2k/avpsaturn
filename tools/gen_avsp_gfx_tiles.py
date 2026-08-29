"""Generate the ROM tile archive the per-object VDP1 renderer consumes.

S2 Body E's texture source. Enumerates every CPS2 object entry the proven
corpus decoder produces across the four paired capture routes, expands each
entry into its 16x16 ROM tile codes exactly as the CPS2 object hardware does
(MAME 0.289 cps2_render_sprites: non-flipped reads wrap within the tile row,
flipped reads run linearly; the union over both facings is stored so one
archive serves either), decodes those tiles from the locally supplied
graphics ROMs (`extract_avspu_stage1.load_gfx_region`, the SHA-verified
interleave + unshuffle already trusted by the cel pipeline), and packs them
as VDP1 16-colour-bank textures (pen 15 transparent -> pixel 0; visible pen
p -> pixel p+1, matching Jo's CRAM base+1 convention used by every cel).

Outputs:

* build/avsp_cd/SPR4/TILES.BIN - the archive, written straight into the
  staged ISO content root (build/ is git-ignored; the bytes derive from the
  private graphics ROMs and are never committed). Big-endian throughout:
    0x00 u32 magic 'AVTL'
    0x04 u32 tile_count
    0x08 u32 palette_slot_count  (16-colour banks stored)
    0x0C u32 codes_offset        (byte offset of the code table)
    0x10 u8  bank_map[32]        (CPS2 colour 0..31 -> palette slot, 0xFF unused)
    0x30 u16 cram[slot_count*16] (Saturn RGB555|0x8000, entry 0 written but
                                  unused: pen p renders colour cram[slot*16+p-1]
                                  after Jo's base+1 shift; kept 16-aligned)
    codes_offset: u32 codes[tile_count] ascending
    then tile_count * 128 bytes of 4bpp texture (high nibble = left pixel)
* data/avsp_gfx_tiles.json - tracked manifest: counts, hashes, palette source
  frame, per-route entry statistics. No ROM bytes.

The palette block is transcribed from a route-matched captured palette frame
(ADAPTED until palette RAM emulation lands: CPS2 palettes fade dynamically;
one mid-combat frame is used and its choice is recorded in the manifest).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import extract_avspu_stage1 as avsp        # noqa: E402
from decode_avsp_object_stream import Rom  # noqa: E402
import verify_avsp_object_corpus as V      # noqa: E402
from census_full_route import RouteState   # noqa: E402
from gen_avsp_emit_windows import (       # noqa: E402
    decode_spec02_presentations,
    load_spec02_round1_presentations,
)

ROM_PATH = ROOT / ".deps/mame/actorprobe/decrypted_program_2m.bin"
MAIN_C = ROOT / "main.c"
# Two named scopes only - no scope may be inferred from whether TILES.BIN
# happens to exist (that inference is what let extract_avspu_stage1.py's
# generic SPR4 sweep silently force a full-scope regen on every build; see
# docs/AGENT_HANDOFF.md "Item 1 continued"). --scope is REQUIRED, not
# defaulted, so a caller must say which budget it is asking for.
ROUTES_BY_SCOPE = {
    "street": ("enemy_actions", "full_route:3474:3674"),
    "round1": ("enemy_actions", "stalker_actions", "boss_actions", "boss_ko"),
}
# "street" (1,533 tiles, 202,564 bytes) is the archive MEASURED to fit the
# current cartridge budget alongside the rest of the boot working set.
# "round1" (4,640 tiles, 612,720 bytes) is the complete four-route cast;
# it does NOT fit today - widening AVSP_TILE_REGION_BYTES to hold it left
# EACT.RLE (131,552 bytes) with no single cart zone able to allocate it
# (bank0 ~13 KB free, bank1 ~103 KB free, MEASURED live over MCP). Do not
# build --scope round1 into a normal-release ISO until more PCM moves to
# phase-boundary loads - see docs/AGENT_HANDOFF.md.
PALETTE_ROUTE = "enemy_actions"
OUT_BIN = ROOT / "build" / "avsp_cd" / "SPR4" / "TILES.BIN"
OUT_JSON = ROOT / "data" / "avsp_gfx_tiles.json"
TILE_BYTES = 128
# Stride 1: sampling every 3rd frame proved lossy - the two-frame pose at
# record 0x12DE78 (tiles 0x4A20-0x4A28/0x4A30-0x4A38) fell entirely between
# samples and the renderer silently dropped it. Every captured frame is
# decoded. Residual completeness risk (labelled UNRESOLVED): poses reachable
# by the free-running interpreter that the captured routes never visited;
# closing it needs an actor-state-free assembly part walker.
SAMPLE_STRIDE = 1
FIRST_SEGMENT_SOURCE = ROOT / ".deps" / "mame" / "full_route"
FIRST_SEGMENT_FIRST_FRAME = 2074
FIRST_SEGMENT_LAST_EXCLUSIVE = 3474
STARTUP_RESIDENCY_LAST_EXCLUSIVE = 2254
SOURCE_POOL_LAYOUTS = (
    (0x9580, 0xC0, 20),
    (0xA480, 0x80, 20),
    (0xAE80, 0x80, 16),
    (0xB680, 0x80, 32),
)
NATIVE_INITIAL_FAMILIES = {(12, 0x1F), (20, 0x09),
                           (24, 0x4E), (24, 0x44)}


def entry_tile_codes(code: int, y: int, attr: int) -> set[int]:
    """All tile codes either facing of this entry can fetch (MAME 0.289)."""
    code17 = code + ((y & 0x6000) << 3)
    nx = ((attr >> 8) & 0xF) + 1
    ny = ((attr >> 12) & 0xF) + 1
    codes = set()
    for sy in range(ny):
        for sx in range(nx):
            # non-flipped: wrap within the 16-tile row (pgear fix)
            codes.add((code17 & ~0xF) + ((code17 + sx) & 0xF) + 0x10 * sy)
            # flipped (x, y, or both): linear
            codes.add(code17 + sx + 0x10 * sy)
    return codes


def entry_tile_codes_exact(code: int, y: int, attr: int) -> set[int]:
    """Tile codes fetched by the entry's recorded facing only."""
    code17 = code + ((y & 0x6000) << 3)
    nx = ((attr >> 8) & 0xF) + 1
    ny = ((attr >> 12) & 0xF) + 1
    flip_x = (attr >> 5) & 1
    flip_y = (attr >> 6) & 1
    codes = set()
    for out_y in range(ny):
        for out_x in range(nx):
            if flip_x or flip_y:
                source_x = nx - 1 - out_x if flip_x else out_x
                source_y = ny - 1 - out_y if flip_y else out_y
                tile = code17 + source_x + 0x10 * source_y
            else:
                tile = ((code17 & ~0xF) + ((code17 + out_x) & 0xF)
                        + 0x10 * out_y)
            codes.add(tile)
    return codes


def read_tile_sprite_pool() -> int:
    text = MAIN_C.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"#define\s+AVSP_TILE_SPRITE_POOL\s+(\d+)", text)
    if not match:
        raise SystemExit("AVSP_TILE_SPRITE_POOL not found in main.c")
    return int(match.group(1))


def read_main_define(name: str) -> int:
    text = MAIN_C.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"#define\s+%s\s+(\d+)(?:UL)?" % re.escape(name),
                      text)
    if not match:
        raise SystemExit("%s not found in main.c" % name)
    return int(match.group(1))


def measure_spec02_composites(results, threshold: int) -> dict[str, int]:
    """Measure SPEC entries too large for the bounded per-tile walker."""
    entries = set()
    max_bytes = 0
    for _kind, _assembly, _facing, flat in results:
        for index in range(0, len(flat), 4):
            _x, y, code, attr = flat[index:index + 4]
            nx = ((attr >> 8) & 0xF) + 1
            ny = ((attr >> 12) & 0xF) + 1
            if nx * ny <= threshold:
                continue
            entries.add((y & 0x6000, code, attr & 0xFFE0))
            max_bytes = max(max_bytes, nx * ny * TILE_BYTES)
    texture_bytes = sum(
        ((((attr >> 8) & 0xF) + 1) *
         (((attr >> 12) & 0xF) + 1) * TILE_BYTES)
        for _y_bits, _code, attr in entries)
    return {"spec02_composite_unique_entries": len(entries),
            "spec02_composite_texture_bytes": texture_bytes,
            "spec02_composite_max_texture_bytes": max_bytes}


def measure_first_segment_composites(rom: Rom, results,
                                     threshold: int) -> dict[str, int]:
    """Measure the persistent composite union used by native Round 1."""
    entries = set()

    def retain(flat) -> None:
        for index in range(0, len(flat), 4):
            _x, y, code, attr = flat[index:index + 4]
            nx = ((attr >> 8) & 0xF) + 1
            ny = ((attr >> 12) & 0xF) + 1
            if nx * ny > threshold:
                entries.add((y & 0x6000, code, attr & 0xFFE0))

    for _kind, _assembly, _facing, flat in results:
        retain(flat)
    route = RouteState(FIRST_SEGMENT_SOURCE)
    try:
        for frame in route.frames():
            number = frame["frame"]
            if number < FIRST_SEGMENT_FIRST_FRAME:
                continue
            if number >= FIRST_SEGMENT_LAST_EXCLUSIVE:
                break
            work = route.current["workram"]
            presentations = []
            for base, stride, capacity in SOURCE_POOL_LAYOUTS:
                for index in range(capacity):
                    offset = base + index * stride
                    if (work[offset] != 1 or
                        (work[offset + 8], work[offset + 2]) not in
                            NATIVE_INITIAL_FAMILIES):
                        continue
                    animation = int.from_bytes(
                        work[offset + 0x1C:offset + 0x20], "big")
                    assembly = rom.u32(animation + 4) if animation else 0
                    if assembly == 0 or rom.u16(assembly) == 0x0008:
                        continue
                    presentations.append({
                        "kind": "first-segment-source",
                        "animation_record": animation,
                        "assembly": assembly,
                        "facing": work[offset + 0x0F],
                        "coordinate_mode": work[offset + 0x0D],
                        "palette": work[offset + 0x0E],
                        "object_or": int.from_bytes(
                            work[offset + 0x2E:offset + 0x30], "big"),
                    })
            if presentations:
                decoded = decode_spec02_presentations(rom, presentations)
                for _kind, _assembly, _facing, flat in decoded:
                    retain(flat)
    finally:
        route.close()
    sizes = [
        ((((attr >> 8) & 0xF) + 1) *
         (((attr >> 12) & 0xF) + 1) * TILE_BYTES)
        for _y_bits, _code, attr in entries
    ]
    return {
        "first_segment_composite_unique_entries": len(entries),
        "first_segment_composite_texture_bytes": sum(sizes),
        "first_segment_composite_max_texture_bytes": max(sizes or [0]),
    }


def measure_first_segment_composite_frame_peak(rom: Rom,
                                                threshold: int) -> dict:
    """Measure recyclable composite slots for the source Coffee Shop cast."""
    route = RouteState(FIRST_SEGMENT_SOURCE)
    peak_entries = 0
    peak_bytes = 0
    peak_frame = 0
    dimensions = set()
    dimension_slot_peaks = {}
    ranked_slot_capacities = []
    try:
        for frame in route.frames():
            number = frame["frame"]
            if number < FIRST_SEGMENT_FIRST_FRAME:
                continue
            if number >= FIRST_SEGMENT_LAST_EXCLUSIVE:
                break
            work = route.current["workram"]
            presentations = []
            for base, stride, capacity in SOURCE_POOL_LAYOUTS:
                for index in range(capacity):
                    offset = base + index * stride
                    if (work[offset] != 1 or
                        (work[offset + 8], work[offset + 2]) not in
                            NATIVE_INITIAL_FAMILIES):
                        continue
                    animation = int.from_bytes(
                        work[offset + 0x1C:offset + 0x20], "big")
                    assembly = rom.u32(animation + 4) if animation else 0
                    if assembly == 0 or rom.u16(assembly) == 0x0008:
                        continue
                    presentations.append({
                        "kind": "first-segment-source",
                        "animation_record": animation,
                        "assembly": assembly,
                        "facing": work[offset + 0x0F],
                        "coordinate_mode": work[offset + 0x0D],
                        "palette": work[offset + 0x0E],
                        "object_or": int.from_bytes(
                            work[offset + 0x2E:offset + 0x30], "big"),
                    })
            frame_entries = set()
            if presentations:
                decoded = decode_spec02_presentations(rom, presentations)
                for _kind, _assembly, _facing, flat in decoded:
                    for word in range(0, len(flat), 4):
                        _x, y, code, attr = flat[word:word + 4]
                        nx = ((attr >> 8) & 0xF) + 1
                        ny = ((attr >> 12) & 0xF) + 1
                        if nx * ny > threshold:
                            frame_entries.add((y & 0x6000, code,
                                               attr & 0xFFE0))
                            dimensions.add((nx * 16, ny * 16))
            frame_bytes = sum(
                ((((attr >> 8) & 0xF) + 1) *
                  (((attr >> 12) & 0xF) + 1) * TILE_BYTES)
                for _y_bits, _code, attr in frame_entries)
            frame_sizes = sorted((
                ((((attr >> 8) & 0xF) + 1) *
                  (((attr >> 12) & 0xF) + 1) * TILE_BYTES)
                for _y_bits, _code, attr in frame_entries), reverse=True)
            while len(ranked_slot_capacities) < len(frame_sizes):
                ranked_slot_capacities.append(0)
            for slot, size in enumerate(frame_sizes):
                ranked_slot_capacities[slot] = max(
                    ranked_slot_capacities[slot], size)
            frame_dimension_counts = {}
            for _y_bits, _code, attr in frame_entries:
                dimension = (((attr >> 8) & 0xF) + 1,
                             ((attr >> 12) & 0xF) + 1)
                frame_dimension_counts[dimension] = (
                    frame_dimension_counts.get(dimension, 0) + 1)
            for dimension, count in frame_dimension_counts.items():
                dimension_slot_peaks[dimension] = max(
                    count, dimension_slot_peaks.get(dimension, 0))
            if (len(frame_entries), frame_bytes) > (peak_entries, peak_bytes):
                peak_entries = len(frame_entries)
                peak_bytes = frame_bytes
                peak_frame = number
    finally:
        route.close()
    return {
        "first_segment_composite_frame_peak_entries": peak_entries,
        "first_segment_composite_frame_peak_bytes": peak_bytes,
        "first_segment_composite_frame_peak_frame": peak_frame,
        "first_segment_composite_dimensions": [
            [width, height] for width, height in sorted(dimensions)
        ],
        "first_segment_composite_dimension_slot_peaks": [
            {"width": nx * 16, "height": ny * 16, "slots": count}
            for (nx, ny), count in sorted(dimension_slot_peaks.items())
        ],
        "first_segment_composite_dimension_slots":
            sum(dimension_slot_peaks.values()),
        "first_segment_composite_ranked_slot_capacities":
            ranked_slot_capacities,
        "first_segment_composite_ranked_slot_bytes":
            sum(ranked_slot_capacities),
    }


def measure_first_segment_presentation_peak(rom: Rom) -> dict[str, int]:
    """Measure the exact live-tile union for the native initial families."""
    route = RouteState(FIRST_SEGMENT_SOURCE)
    peak_tiles = 0
    peak_frame = 0
    peak_actors = 0
    peak_entries = 0
    try:
        for frame in route.frames():
            number = frame["frame"]
            if number < FIRST_SEGMENT_FIRST_FRAME:
                continue
            if number >= FIRST_SEGMENT_LAST_EXCLUSIVE:
                break
            work = route.current["workram"]
            presentations = []
            for base, stride, capacity in SOURCE_POOL_LAYOUTS:
                for index in range(capacity):
                    offset = base + index * stride
                    if (work[offset] != 1 or
                        (work[offset + 8], work[offset + 2]) not in
                            NATIVE_INITIAL_FAMILIES):
                        continue
                    animation = int.from_bytes(
                        work[offset + 0x1C:offset + 0x20], "big")
                    assembly = rom.u32(animation + 4) if animation else 0
                    if assembly == 0 or rom.u16(assembly) == 0x0008:
                        continue
                    presentations.append({
                        "kind": "first-segment-source",
                        "animation_record": animation,
                        "assembly": assembly,
                        "facing": work[offset + 0x0F],
                        "coordinate_mode": work[offset + 0x0D],
                        "palette": work[offset + 0x0E],
                        "object_or": int.from_bytes(
                            work[offset + 0x2E:offset + 0x30], "big"),
                    })
            if not presentations:
                continue
            decoded = decode_spec02_presentations(rom, presentations)
            codes: set[int] = set()
            entries = 0
            for _kind, _assembly, _facing, flat in decoded:
                entries += len(flat) // 4
                for word in range(0, len(flat), 4):
                    _x, y, code, attr = flat[word:word + 4]
                    codes |= entry_tile_codes_exact(code, y, attr)
            if len(codes) > peak_tiles:
                peak_tiles = len(codes)
                peak_frame = number
                peak_actors = len(presentations)
                peak_entries = entries
    finally:
        route.close()
    if peak_tiles == 0:
        raise SystemExit("first-segment presentation peak was not measured")
    return {"source_peak_unique_tiles": peak_tiles,
            "source_peak_frame": peak_frame,
            "source_peak_actors": peak_actors,
            "source_peak_object_entries": peak_entries}


def measure_startup_noncomposite_peak(rom: Rom, threshold: int) -> dict:
    """Measure ordinary tiles in the accepted boot-to-handoff window."""
    route = RouteState(FIRST_SEGMENT_SOURCE)
    peak_tiles = 0
    peak_frame = 0
    try:
        for frame in route.frames():
            number = frame["frame"]
            if number < FIRST_SEGMENT_FIRST_FRAME:
                continue
            if number >= STARTUP_RESIDENCY_LAST_EXCLUSIVE:
                break
            work = route.current["workram"]
            presentations = []
            for base, stride, capacity in SOURCE_POOL_LAYOUTS:
                for index in range(capacity):
                    offset = base + index * stride
                    if (work[offset] != 1 or
                        (work[offset + 8], work[offset + 2]) not in
                            NATIVE_INITIAL_FAMILIES):
                        continue
                    animation = int.from_bytes(
                        work[offset + 0x1C:offset + 0x20], "big")
                    assembly = rom.u32(animation + 4) if animation else 0
                    if assembly == 0 or rom.u16(assembly) == 0x0008:
                        continue
                    presentations.append({
                        "kind": "startup-source",
                        "animation_record": animation,
                        "assembly": assembly,
                        "facing": work[offset + 0x0F],
                        "coordinate_mode": work[offset + 0x0D],
                        "palette": work[offset + 0x0E],
                        "object_or": int.from_bytes(
                            work[offset + 0x2E:offset + 0x30], "big"),
                    })
            tiles: set[int] = set()
            if presentations:
                decoded = decode_spec02_presentations(rom, presentations)
                for _kind, _assembly, _facing, flat in decoded:
                    for word in range(0, len(flat), 4):
                        _x, y, code, attr = flat[word:word + 4]
                        nx = ((attr >> 8) & 0xF) + 1
                        ny = ((attr >> 12) & 0xF) + 1
                        if nx * ny <= threshold:
                            tiles |= entry_tile_codes_exact(code, y, attr)
            if len(tiles) > peak_tiles:
                peak_tiles = len(tiles)
                peak_frame = number
    finally:
        route.close()
    if peak_tiles == 0:
        raise SystemExit("startup non-composite peak was not measured")
    return {
        "startup_source_frame_range": [FIRST_SEGMENT_FIRST_FRAME,
                                         STARTUP_RESIDENCY_LAST_EXCLUSIVE - 1],
        "startup_peak_noncomposite_tiles": peak_tiles,
        "startup_peak_noncomposite_frame": peak_frame,
    }


def measure_first_segment_noncomposite_peak(rom: Rom,
                                             threshold: int) -> dict:
    """Measure the complete Coffee Shop per-frame tile-cache requirement."""
    route = RouteState(FIRST_SEGMENT_SOURCE)
    peak_tiles = 0
    peak_frame = 0
    try:
        for frame in route.frames():
            number = frame["frame"]
            if number < FIRST_SEGMENT_FIRST_FRAME:
                continue
            if number >= FIRST_SEGMENT_LAST_EXCLUSIVE:
                break
            work = route.current["workram"]
            presentations = []
            for base, stride, capacity in SOURCE_POOL_LAYOUTS:
                for index in range(capacity):
                    offset = base + index * stride
                    if (work[offset] != 1 or
                        (work[offset + 8], work[offset + 2]) not in
                            NATIVE_INITIAL_FAMILIES):
                        continue
                    animation = int.from_bytes(
                        work[offset + 0x1C:offset + 0x20], "big")
                    assembly = rom.u32(animation + 4) if animation else 0
                    if assembly == 0 or rom.u16(assembly) == 0x0008:
                        continue
                    presentations.append({
                        "kind": "first-segment-source",
                        "animation_record": animation,
                        "assembly": assembly,
                        "facing": work[offset + 0x0F],
                        "coordinate_mode": work[offset + 0x0D],
                        "palette": work[offset + 0x0E],
                        "object_or": int.from_bytes(
                            work[offset + 0x2E:offset + 0x30], "big"),
                    })
            tiles: set[int] = set()
            if presentations:
                decoded = decode_spec02_presentations(rom, presentations)
                for _kind, _assembly, _facing, flat in decoded:
                    for word in range(0, len(flat), 4):
                        _x, y, code, attr = flat[word:word + 4]
                        nx = ((attr >> 8) & 0xF) + 1
                        ny = ((attr >> 12) & 0xF) + 1
                        if nx * ny <= threshold:
                            tiles |= entry_tile_codes_exact(code, y, attr)
            if len(tiles) > peak_tiles:
                peak_tiles = len(tiles)
                peak_frame = number
    finally:
        route.close()
    if peak_tiles == 0:
        raise SystemExit("first-segment non-composite peak was not measured")
    return {
        "first_segment_peak_noncomposite_tiles": peak_tiles,
        "first_segment_peak_noncomposite_frame": peak_frame,
    }


def collect_full_route_entries(spec, tiles, banks):
    """Object-list truth from the RP2 delta capture for a frame interval.

    Spec is "full_route:first:last". Unlike the workram actor decode, this
    reads the recorded active object banks directly, so it covers every
    transient the interval actually drew (projectiles, shadows, effects)."""
    from census_full_route import RouteState
    name, first, last = spec.split(":")
    first, last = int(first), int(last)
    state = RouteState(ROOT / ".deps" / "mame" / name)
    n_entries = 0
    n_frames = 0
    for rec in state.frames():
        if rec["frame"] < first:
            continue
        if rec["frame"] > last:
            break
        n_frames += 1
        active = state.current["objram2" if rec["active_bank"]
                               else "objram1"]
        for offset in range(0, len(active) - 7, 8):
            y = int.from_bytes(active[offset + 2:offset + 4], "big")
            code = int.from_bytes(active[offset + 4:offset + 6], "big")
            attr = int.from_bytes(active[offset + 6:offset + 8], "big")
            if y >= 0x8000 or attr >= 0xFF00:
                break
            tiles |= entry_tile_codes(code, y, attr)
            banks.add(attr & 0x1F)
            n_entries += 1
    state.close()
    print("%s: %d frames, %d entries -> %d tiles"
          % (spec, n_frames, n_entries, len(tiles)))
    return {"frames_sampled": n_frames, "entries": n_entries}


def collect_entries(rom: Rom, routes):
    """Decode every eligible actor instance across the corpus routes."""
    per_route = {}
    tiles = set()
    banks = set()
    for route in routes:
        if route.startswith("full_route:"):
            per_route[route] = collect_full_route_entries(route, tiles,
                                                          banks)
            continue
        root = ROOT / ".deps" / "mame" / route
        frames = sorted(root.glob("workram_*.bin"))[::SAMPLE_STRIDE]
        n_entries = 0
        for wpath in frames:
            work = wpath.read_bytes()
            if len(work) != 0x8000:
                continue
            ax, ay = V.read_anchors(work)
            for n in range((0x10000 - 0x8380) // V.ACTOR_STRIDE):
                so = (V.ACTOR_ANCHOR - V.WORKRAM_BASE) + n * V.ACTOR_STRIDE
                if so + V.ACTOR_STRIDE > len(work):
                    break
                try:
                    flat, _meta = V.decode_actor_entries(rom, work, so, ax, ay)
                except IndexError:
                    flat = None
                if not flat:
                    continue
                for i in range(0, len(flat), 4):
                    _x, y, code, attr = flat[i:i + 4]
                    tiles |= entry_tile_codes(code, y, attr)
                    banks.add(attr & 0x1F)
                    n_entries += 1
        per_route[route] = {"frames_sampled": len(frames),
                            "entries": n_entries}
        print("%s: %d frames, %d entries so far -> %d tiles"
              % (route, len(frames), n_entries, len(tiles)))
    return tiles, banks, per_route


def pick_palette_frame() -> Path:
    """A mid-combat street-route palette frame, stable vs its neighbours."""
    root = ROOT / ".deps" / "mame" / PALETTE_ROUTE
    frames = sorted(root.glob("palette_*.tsv"))
    if not frames:
        raise SystemExit("no palette captures in " + str(root))
    mid = frames[len(frames) // 2]
    return mid


def build_palette_block(banks: set[int], palette_path: Path):
    palette = avsp.load_palette_path(palette_path)
    bank_map = [0xFF] * 32
    slots = []
    for bank in sorted(banks):
        bank_map[bank] = len(slots)
        slots.append(bank)
    cram = []
    for bank in slots:
        for pen in range(16):
            # Saturn colour for VDP1 pixel value pen+1 lands at CRAM index
            # slot*16+pen after Jo's base+1 shift; pen 15's slot (index 15)
            # is written from CPS2 pen 15 but never rendered (transparent).
            r, g, b, _a = palette[bank * 16 + pen]
            cram.append(0x8000 | ((b >> 3) << 10) | ((g >> 3) << 5) | (r >> 3))
    return bank_map, slots, cram


def tile_texture(gfx: bytearray, code: int) -> bytes:
    """One 16x16 tile as VDP1 4bpp bytes (pen15 -> 0, pen p -> p+1)."""
    image = avsp.decode_tile(gfx, code, 16)
    pixels = image.load()
    out = bytearray(TILE_BYTES)
    for y in range(16):
        for x in range(0, 16, 2):
            left = pixels[x, y]
            right = pixels[x + 1, y]
            left = 0 if left == 15 else left + 1
            right = 0 if right == 15 else right + 1
            out[y * 8 + x // 2] = (left << 4) | right
    return bytes(out)


def read_tile_region_bytes() -> int:
    """The runtime's carved cart budget, parsed straight from main.c so
    this generator and the compiled runtime can never silently disagree."""
    text = MAIN_C.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"#define\s+AVSP_TILE_REGION_BYTES\s+(0x[0-9A-Fa-f]+)",
                 text)
    if not m:
        raise SystemExit("AVSP_TILE_REGION_BYTES not found in main.c")
    return int(m.group(1), 16)


def build_archive_blob(codes, banks, palette_path, gfx):
    """Serialize one deterministic AVTL archive from an exact tile set."""
    bank_map, slots, cram = build_palette_block(banks, palette_path)
    header_bytes = 0x10 + 32 + len(cram) * 2
    blob = bytearray()
    blob += b"AVTL"
    blob += len(codes).to_bytes(4, "big")
    blob += len(slots).to_bytes(4, "big")
    blob += header_bytes.to_bytes(4, "big")
    blob += bytes(bank_map)
    for value in cram:
        blob += value.to_bytes(2, "big")
    assert len(blob) == header_bytes
    for code in codes:
        blob += code.to_bytes(4, "big")
    for code in codes:
        blob += tile_texture(gfx, code)
    return blob, slots


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--scope", choices=("street", "round1"),
                        help="street: the archive proven to fit the current "
                             "cartridge budget. round1: the complete "
                             "four-route cast archive, does not fit today.")
    source.add_argument("--probe3-schedule", type=Path,
                        help="tracked Probe 3 schedule whose exact recorded "
                             "tile union is staged through the AVTL path")
    parser.add_argument("--output-bin", type=Path, default=OUT_BIN)
    parser.add_argument("--output-json", type=Path, default=OUT_JSON)
    parser.add_argument("--allow-over-budget", action="store_true",
                        help="write the archive even if it exceeds the "
                             "runtime's AVSP_TILE_REGION_BYTES carve "
                             "(measurement only - never for a build).")
    args = parser.parse_args()
    avsp.verify_roms()
    gfx = avsp.load_gfx_region()
    avsp.verify_loaded_gfx_region(gfx)
    schedule_sha256 = None
    presentation_residency = None
    if args.probe3_schedule:
        schedule_path = args.probe3_schedule.resolve()
        schedule_bytes = schedule_path.read_bytes()
        schedule_sha256 = hashlib.sha256(schedule_bytes).hexdigest()
        schedule = json.loads(schedule_bytes)
        tiles: set[int] = set()
        banks: set[int] = set()
        per_route = {}
        for workload in schedule["schedules"]:
            entries = workload["object_entries"]
            for entry in entries:
                tiles |= entry_tile_codes_exact(
                    entry["code"], entry["y"], entry["attr"])
                banks.add(entry["attr"] & 0x1F)
            per_route[workload["id"]] = {
                "source_frame": workload["source_frame"],
                "object_entries": len(entries),
                "reachable_commands": workload["actual_reachable_command_count"],
                "workload_checksum_sha256": workload["workload_checksum_sha256"],
            }
        palette_path = (ROOT / schedule["schedules"][1]["palette_artifact"])
        scope = "probe3-exact-schedule-union"
        facing_union = False
    else:
        routes = ROUTES_BY_SCOPE[args.scope]
        rom = Rom(ROM_PATH.read_bytes())
        tiles, banks, per_route = collect_entries(rom, routes)
        spec_presentations, spec_fixture_sha256 = (
            load_spec02_round1_presentations())
        spec_presentations = [
            item for item in spec_presentations
            if item["kind"] != "class1f-source-hit-window"]
        spec_results = decode_spec02_presentations(rom, spec_presentations)
        spec_tile_count_before = len(tiles)
        spec_palette_banks: set[int] = set()
        for _kind, _assembly, _facing, flat in spec_results:
            for index in range(0, len(flat), 4):
                _x, y, code, attr = flat[index:index + 4]
                tiles |= entry_tile_codes_exact(code, y, attr)
                spec_palette_banks.add(attr & 0x1F)
                banks.add(attr & 0x1F)
        per_route["spec02_round1_native_presentations"] = {
            "fixture_sha256": spec_fixture_sha256,
            "decoded_variants": len(spec_results),
            "unique_assemblies": len({item["assembly"]
                                      for item in spec_presentations}),
            "tiles_added": len(tiles) - spec_tile_count_before,
            "palette_banks": ["0x%02X" % bank for bank in
                              sorted(spec_palette_banks)],
        }
        presentation_residency = measure_first_segment_presentation_peak(rom)
        fixture = json.loads((ROOT / "data" /
                              "spec02_round1_generated_fixtures.json")
                             .read_text(encoding="ascii"))
        weapon_contract = fixture["authority_data"]["player"][
            "weapon_projectile_resource"]["implementation_contract"]
        child_count = weapon_contract["record4_parent_class0"][
            "child_emitter_state"]["initial_child_count_u8"]
        parent_max = max(
            len({tile for index in range(0, len(flat), 4)
                 for tile in entry_tile_codes_exact(
                     flat[index + 2], flat[index + 1], flat[index + 3])})
            for kind, _assembly, _facing, flat in spec_results
            if kind == "projectile-parent")
        child_max = max(
            len({tile for index in range(0, len(flat), 4)
                 for tile in entry_tile_codes_exact(
                     flat[index + 2], flat[index + 1], flat[index + 3])})
            for kind, _assembly, _facing, flat in spec_results
            if kind == "projectile-child")
        projectile_max = max(parent_max, child_max)
        impact_max = 0
        per_tile_required = (
            presentation_residency["source_peak_unique_tiles"] +
            parent_max + child_count * child_max)
        composite_threshold = read_main_define(
            "AVSP_COMPOSITE_TILE_THRESHOLD")
        composite = measure_spec02_composites(spec_results,
                                               composite_threshold)
        first_segment_composite = measure_first_segment_composites(
            rom, spec_results, composite_threshold)
        first_segment_composite_peak = (
            measure_first_segment_composite_frame_peak(
                rom, composite_threshold))
        startup_residency = measure_startup_noncomposite_peak(
            rom, composite_threshold)
        first_segment_noncomposite = measure_first_segment_noncomposite_peak(
            rom, composite_threshold)
        configured_tiles = read_tile_sprite_pool()
        configured_composites = read_main_define(
            "AVSP_COMPOSITE_SPRITE_POOL")
        composite_budget = read_main_define(
            "AVSP_COMPOSITE_TEXTURE_BUDGET")
        composite_max = read_main_define(
            "AVSP_COMPOSITE_MAX_TEXTURE_BYTES")
        child_composite_entries = 0
        child_composite_bytes = 0
        player_composite_entries = 0
        player_composite_bytes = 0
        for kind, _assembly, _facing, flat in spec_results:
            sizes = []
            for index in range(0, len(flat), 4):
                attr = flat[index + 3]
                nx = ((attr >> 8) & 0xF) + 1
                ny = ((attr >> 12) & 0xF) + 1
                if nx * ny > composite_threshold:
                    sizes.append(nx * ny * TILE_BYTES)
            if kind == "projectile-child":
                child_composite_entries = max(child_composite_entries,
                                              len(sizes))
                child_composite_bytes = max(child_composite_bytes,
                                            sum(sizes))
            elif kind.startswith("player-"):
                player_composite_entries = max(player_composite_entries,
                                               len(sizes))
                player_composite_bytes = max(player_composite_bytes,
                                             sum(sizes))
        composite_required_slots = (
            first_segment_composite_peak[
                "first_segment_composite_frame_peak_entries"] +
            child_count * child_composite_entries +
            player_composite_entries)
        composite_required_bytes = (
            first_segment_composite_peak[
                "first_segment_composite_ranked_slot_bytes"] +
            child_count * child_composite_bytes +
            player_composite_bytes)
        presentation_residency.update({
            "source_capture": str(FIRST_SEGMENT_SOURCE.relative_to(ROOT))
                .replace("\\", "/"),
            "source_frame_range": [FIRST_SEGMENT_FIRST_FRAME,
                                   FIRST_SEGMENT_LAST_EXCLUSIVE - 1],
            "projectile_simultaneous_bound": child_count + 1,
            "parent_tiles_at_peak": parent_max,
            "child_tiles_at_peak": child_max,
            "max_tiles_per_projectile": projectile_max,
            "max_tiles_per_impact": impact_max,
            "per_tile_scanout_requirement": per_tile_required,
            "retained_tile_sprite_pool": configured_tiles,
            "configured_composite_slots": configured_composites,
            "configured_composite_texture_budget": composite_budget,
            "configured_composite_max_texture_bytes": composite_max,
            "composite_tile_threshold": composite_threshold,
            **composite,
            **first_segment_composite,
            **first_segment_composite_peak,
            **startup_residency,
            **first_segment_noncomposite,
            "scene_composite_required_slots": composite_required_slots,
            "scene_composite_required_bytes": composite_required_bytes,
            "scene_composite_player_peak_entries": player_composite_entries,
            "scene_composite_player_peak_bytes": player_composite_bytes,
            "scene_composite_child_peak_entries": child_composite_entries,
            "scene_composite_child_peak_bytes": child_composite_bytes,
            "mid_frame_lru_replacement_allowed": False,
            "between_frame_composite_replacement_allowed": True,
        })
        if configured_tiles < startup_residency[
                "startup_peak_noncomposite_tiles"]:
            raise SystemExit(
                "REFUSING to build: retained tile pool cannot hold the "
                "accepted startup non-composite peak")
        if configured_tiles < first_segment_noncomposite[
                "first_segment_peak_noncomposite_tiles"]:
            raise SystemExit(
                "REFUSING to build: retained tile pool cannot hold the "
                "complete Coffee Shop non-composite peak")
        if (configured_composites < composite_required_slots or
            composite_budget < composite_required_bytes or
            composite_max < first_segment_composite[
                "first_segment_composite_max_texture_bytes"]):
            raise SystemExit(
                "REFUSING to build: recyclable native object-entry composite "
                "budget cannot hold the Coffee Shop frame peak")
        palette_path = pick_palette_frame()
        scope = args.scope
        facing_union = True
    max_code = len(gfx) * 8 // (TILE_BYTES * 8)
    bad = [c for c in tiles if c < 0 or c >= max_code]
    if bad:
        raise SystemExit("tile codes outside gfx region: %s"
                         % ", ".join("0x%X" % c for c in sorted(bad)[:8]))
    codes = sorted(tiles)

    blob, slots = build_archive_blob(codes, banks, palette_path, gfx)
    print("tiles: %d (%d bytes), palette banks: %s -> %d slots"
          % (len(codes), len(codes) * TILE_BYTES,
             ",".join("0x%02X" % b for b in sorted(banks)), len(slots)))

    region_bytes = read_tile_region_bytes()
    if len(blob) > region_bytes and not args.allow_over_budget:
        raise SystemExit(
            "REFUSING to write: archive is %d bytes but the runtime's "
            "AVSP_TILE_REGION_BYTES carve (main.c) is only %d bytes. "
            "A build must never ship an ISO member the runtime cannot "
            "hold. Either regenerate with --scope street, or widen the "
            "carve in main.c AND re-measure the cartridge allocator "
            "budget for every other cart-resident asset before doing so "
            "(see docs/AGENT_HANDOFF.md). Pass --allow-over-budget only "
            "to measure an oversized archive offline, never to build."
            % (len(blob), region_bytes))
    print("tile region budget: %d / %d bytes used (%.1f%%)"
         % (len(blob), region_bytes, 100 * len(blob) / region_bytes))

    args.output_bin.parent.mkdir(parents=True, exist_ok=True)
    args.output_bin.write_bytes(blob)

    manifest = {
        "schema": 1,
        "classification": "tile archive manifest - no ROM bytes",
        "archive": {"file": str(args.output_bin.relative_to(ROOT)).replace("\\", "/"),
                     "bytes": len(blob),
                     "sha256": hashlib.sha256(bytes(blob)).hexdigest()},
        "tile_count": len(codes),
        "tile_bytes": TILE_BYTES,
        "palette": {"source": str(palette_path.relative_to(ROOT)).replace(
                        "\\", "/"),
                    "banks": ["0x%02X" % b for b in slots],
                    "label": "ADAPTED single-frame palette"},
        "facing_union": facing_union,
        "scope": scope,
        "tile_region_budget_bytes": region_bytes,
        "tile_region_budget_used_pct": round(100 * len(blob) / region_bytes, 2),
        "sample_stride": SAMPLE_STRIDE,
        "routes": per_route,
        "gfx_region_sha256": hashlib.sha256(bytes(gfx)).hexdigest(),
    }
    if presentation_residency is not None:
        manifest["presentation_residency"] = presentation_residency
    if schedule_sha256 is not None:
        manifest["probe3_schedule"] = {
            "file": str(schedule_path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": schedule_sha256,
        }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    print("wrote %s (%d bytes) and %s" %
          (args.output_bin, len(blob), args.output_json))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
