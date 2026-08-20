#!/usr/bin/env python3
"""Generate the RP4 two-plane street strips from ROM tiles and capture maps.

Consumes the private full-route capture (map/palette/register truth) and the
locally supplied graphics ROMs (tile pixel truth, via the SHA-verified
extract_avspu_stage1 decode) for the representative interval selected by
tools/select_rp4_interval.py (source frames 3474-3674). Produces:

* build/avsp_cd/ST1/STRIPS.BIN (private, git-ignored; derives from ROMs):
    0x00 u32 magic 'AVSS'
    0x04 u16 schema 0, u16 first_frame-relative frame count
    two plane blocks (NBG0 = scroll2, NBG1 = scroll3), each:
      u16 out_width, u16 height, u16 world_x0, u16 row0,
      u32 pixel_offset (8bpp, row-major, out_width x height)
    2 x 256 u16 Saturn RGB555|0x8000 palettes (index 0 unused/transparent)
    palette-cycle block: u16 bank_index, u16 period_frames, u16 phase,
      2 x 15 u16 alternate colours for the cycling bank
    scroll table: per frame u16 s2x u16 s2y u16 s3x u16 s3y (source regs)
    map-patch schedule: u16 count, then per patch u16 frame_rel, u16 plane,
      u16 out_x, u16 row, u16 cell_count, cells as u32 pixel offsets? -
      patches are emitted as re-rendered 16px-wide column spans:
      u16 span_out_x0, u16 span_out_width, u32 pixel_offset into the
      patch pixel pool (height = plane height)
    object schedule: per frame u16 count, then per entry
      u16 code_rank (index into TILES.BIN codes, 0xFFFF if uncovered),
      s16 x, s16 y, u16 attribute (flips+colour), u16 priority
* data/rp4_street_planes.json - tracked manifest: dimensions, hashes,
  colour budgets, coverage counts, cycle timing. No ROM bytes, no pixels.

The horizontal transform is the repository's endpoint-aligned 384-to-352
mapping, source_x = (out_x * 383 + 175) // 351, applied in unwrapped world
space so every plane and the per-frame scroll conversion share one rule
(the plane-level "common mapping" non-negotiable). Pixels are 8bpp direct
colour-LUT indices: (bank, pen) pairs are packed 1..255 per plane
(transparent 0), which fits because the interval uses 17 banks x 15 pens =
255 for scroll2 and 3 x 15 = 45 for scroll3.
"""
from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import extract_avspu_stage1 as avsp                     # noqa: E402
from census_full_route import RouteState                # noqa: E402
from select_rp4_interval import (tile_index, FIRST_FRAME, LAST_FRAME,
                                 VISIBLE_TOP, VISIBLE_LEFT, VISIBLE_WIDTH,
                                 VISIBLE_HEIGHT)        # noqa: E402

CAPTURE = ROOT / ".deps" / "mame" / "full_route"
OUTPUT_BIN = ROOT / "build" / "avsp_cd" / "ST1" / "STRIPS.BIN"
OUTPUT_MANIFEST = ROOT / "data" / "rp4_street_planes.json"
TILES_BIN = ROOT / "build" / "avsp_cd" / "SPR4" / "TILES.BIN"

PLANES = {
    "scroll2": {"index": 1, "tile": 16, "map_offset": 0x4000, "page": 2,
                "code_base": 0x10000, "code_mask": 0xFFFF},
    "scroll3": {"index": 2, "tile": 32, "map_offset": 0x8000, "page": 3,
                "code_base": 0x4000, "code_mask": 0x3FFF},
}


def out_of(world_x: int) -> int:
    """Endpoint-aligned world->output column (inverse of the source map)."""
    # smallest out with (out*383+175)//351 >= world_x
    out = world_x * 351 // 383
    while (out * 383 + 175) // 351 < world_x:
        out += 1
    return out


def saturn_rgb555(argb: int) -> int:
    r = (argb >> 16) & 0xFF
    g = (argb >> 8) & 0xFF
    b = argb & 0xFF
    return 0x8000 | ((b >> 3) << 10) | ((g >> 3) << 5) | (r >> 3)


def main() -> None:
    gfx = avsp.load_gfx_region()
    state = RouteState(CAPTURE)

    frames = []
    plane_cells: dict[str, dict] = {n: {} for n in PLANES}
    patches: dict[str, list] = {n: [] for n in PLANES}
    palette_states: list[bytes] = []
    palette_frames: list[int] = []
    objects_by_frame = []
    palette_anchor = None

    for rec in state.frames():
        frame = rec["frame"]
        if frame < FIRST_FRAME:
            continue
        if frame > LAST_FRAME:
            break
        cps_a = rec["cps_a"]
        frames.append((frame, cps_a[8], cps_a[9], cps_a[10], cps_a[11]))
        palette = state.gfx_slice(rec["palette_base"], 0xC00 * 2)
        if palette_anchor is None:
            palette_anchor = palette
        page2 = palette[2 * 32 * 32:3 * 32 * 32]
        if not palette_states or palette_states[-1] != page2:
            palette_states.append(page2)
            palette_frames.append(frame)

        active = state.current["objram2" if rec["active_bank"]
                               else "objram1"]
        entries = []
        for offset in range(0, len(active) - 7, 8):
            x = int.from_bytes(active[offset:offset + 2], "big")
            y = int.from_bytes(active[offset + 2:offset + 4], "big")
            code = int.from_bytes(active[offset + 4:offset + 6], "big")
            attribute = int.from_bytes(active[offset + 6:offset + 8], "big")
            if y >= 0x8000 or attribute >= 0xFF00:
                break
            entries.append((x, y, code, attribute))
        objects_by_frame.append(entries)

        for name, plane in PLANES.items():
            size = plane["tile"]
            world = 64 * size
            scroll_x = cps_a[8] if name == "scroll2" else cps_a[10]
            scroll_y = cps_a[9] if name == "scroll2" else cps_a[11]
            plane_map = state.gfx_slice(plane["map_offset"], 0x4000)
            rows = sorted({((raw_y + scroll_y) % world) // size
                           for raw_y in range(VISIBLE_TOP,
                                              VISIBLE_TOP + VISIBLE_HEIGHT)})
            for raw_x in range(VISIBLE_LEFT, VISIBLE_LEFT + VISIBLE_WIDTH +
                               size, size):
                world_x = raw_x + scroll_x
                col = (world_x % world) // size
                unwrapped = world_x // size
                for row in rows:
                    ti = tile_index(plane["index"], col, row)
                    value = (int.from_bytes(plane_map[ti * 4:ti * 4 + 2],
                                            "big"),
                             int.from_bytes(plane_map[ti * 4 + 2:ti * 4 + 4],
                                            "big"))
                    key = (unwrapped, row)
                    known = plane_cells[name].get(key)
                    if known is None:
                        plane_cells[name][key] = value
                    elif known != value:
                        patches[name].append((frame, unwrapped, row, value))
                        plane_cells[name][key] = value
    state.close()

    # --- colour LUTs: lazily assigned from pens actually rendered ---------
    # A bank x 15-pen budget can exceed 256 while the pixels actually used
    # stay well under it, so indices are handed out on first use during the
    # strip render and the budget is enforced on real usage.
    luts: dict[str, dict] = {name: {} for name in PLANES}
    palettes_out = {name: [0x8000] for name in PLANES}

    def lut_index(name: str, bank: int, pen: int) -> int:
        lut = luts[name]
        key = (bank, pen)
        index = lut.get(key)
        if index is None:
            entry = (PLANES[name]["page"] * 32 + bank) * 16 + pen
            argb = int.from_bytes(
                palette_anchor[entry * 2:entry * 2 + 2], "big")
            # CPS2 palette word: 0xFRGB fade/red/green/blue nibbles.
            r = ((argb >> 8) & 0xF) * 17
            g = ((argb >> 4) & 0xF) * 17
            b = (argb & 0xF) * 17
            index = len(palettes_out[name])
            if index > 255:
                raise SystemExit(f"{name}: colour budget exceeded")
            lut[key] = index
            palettes_out[name].append(
                0x8000 | ((b >> 3) << 10) | ((g >> 3) << 5) | (r >> 3))
        return index

    # --- render world strips, then pre-scale ------------------------------
    def render_strip(name: str) -> tuple[bytes, int, int, int, int]:
        plane = PLANES[name]
        size = plane["tile"]
        cells = plane_cells[name]
        cols = sorted({c for c, _ in cells})
        rows = sorted({r for _, r in cells})
        col0, row0 = cols[0], rows[0]
        world_w = (cols[-1] - col0 + 1) * size
        height = (rows[-1] - row0 + 1) * size
        strip = bytearray(world_w * height)
        for (col, row), (code, attr) in cells.items():
            decoded = avsp.decode_tile(
                gfx, plane["code_base"] + (code & plane["code_mask"]),
                size, False)
            pixels = decoded.load()
            flip_x = bool(attr & 0x20)
            flip_y = bool(attr & 0x40)
            bank = attr & 0x1F
            base_x = (col - col0) * size
            base_y = (row - row0) * size
            for py in range(size):
                for px in range(size):
                    pen = pixels[px, py]
                    if pen == 15:
                        continue
                    tx = size - 1 - px if flip_x else px
                    ty = size - 1 - py if flip_y else py
                    strip[(base_y + ty) * world_w + base_x + tx] = \
                        lut_index(name, bank, pen)
        # horizontal pre-scale, world-anchored to col0*size
        world_x0 = col0 * size
        out_x0 = out_of(world_x0)
        out_w = out_of(world_x0 + world_w) - out_x0
        scaled = bytearray(out_w * height)
        for ox in range(out_w):
            sx = ((out_x0 + ox) * 383 + 175) // 351 - world_x0
            if sx >= world_w:
                sx = world_w - 1
            for y in range(height):
                scaled[y * out_w + ox] = strip[y * world_w + sx]
        return bytes(scaled), out_w, height, world_x0, row0

    strips = {name: render_strip(name) for name in PLANES}
    for name in PLANES:
        palettes_out[name] += [0x8000] * (256 - len(palettes_out[name]))

    # --- assemble the binary ----------------------------------------------
    blob = bytearray()
    blob += struct.pack(">IHH", 0x41565353, 0, len(frames))
    header_pos = {}
    for name in ("scroll2", "scroll3"):
        header_pos[name] = len(blob)
        blob += struct.pack(">HHHHI", 0, 0, 0, 0, 0)  # patched below
    for name in ("scroll2", "scroll3"):
        blob += b"".join(struct.pack(">H", c)
                         for c in palettes_out[name])

    # palette cycle: bank 1 of scroll2 alternates between two states.
    cycle_bank = 1
    cycle_states = []
    for state_bytes in palette_states[:2]:
        row = []
        for pen in range(15):
            argb = int.from_bytes(
                state_bytes[cycle_bank * 32 + pen * 2:
                            cycle_bank * 32 + pen * 2 + 2], "big")
            r = ((argb >> 8) & 0xF) * 17
            g = ((argb >> 4) & 0xF) * 17
            b = (argb & 0xF) * 17
            row.append(0x8000 | ((b >> 3) << 10) | ((g >> 3) << 5) |
                       (r >> 3))
        cycle_states.append(row)
    if len(cycle_states) == 1:
        cycle_states.append(cycle_states[0])
    period = (palette_frames[2] - palette_frames[1]) \
        if len(palette_frames) > 2 else 4
    blob += struct.pack(">HHH", cycle_bank, period,
                        (palette_frames[1] - FIRST_FRAME) % (period * 2)
                        if len(palette_frames) > 1 else 0)
    for row in cycle_states:
        blob += b"".join(struct.pack(">H", c) for c in row)

    for frame, s2x, s2y, s3x, s3y in frames:
        blob += struct.pack(">HHHH", s2x, s2y, s3x, s3y)

    # map patches: re-render the touched 16px world column span per event.
    patch_records = []
    patch_pixels = bytearray()
    patch_events = {}
    for name in PLANES:
        for frame, col, row, value in patches[name]:
            patch_events.setdefault((name, frame), []).append(
                (col, row, value))
    for (name, frame), cells in sorted(patch_events.items(),
                                       key=lambda kv: (kv[0][1], kv[0][0])):
        plane = PLANES[name]
        size = plane["tile"]
        strip_bytes, out_w, height, world_x0, row0 = strips[name]
        cols = sorted({c for c, _r, _v in cells})
        span_w0 = out_of(cols[0] * size)
        span_w1 = out_of((cols[-1] + 1) * size)
        span = bytearray((span_w1 - span_w0) * height)
        # start from current strip content, repaint the patched cells
        for ox in range(span_w1 - span_w0):
            for y in range(height):
                span[y * (span_w1 - span_w0) + ox] = strip_bytes[
                    y * out_w + (span_w0 - out_of(world_x0)) + ox]
        for col, row, (code, attr) in cells:
            decoded = avsp.decode_tile(
                gfx, plane["code_base"] + (code & plane["code_mask"]),
                size, False)
            pixels = decoded.load()
            bank = attr & 0x1F
            flip_x = bool(attr & 0x20)
            flip_y = bool(attr & 0x40)
            cell_world_x = col * size
            for py in range(size):
                for px in range(size):
                    pen = pixels[px, py]
                    value_out = 0 if pen == 15 else \
                        lut_index(name, bank, pen)
                    tx = size - 1 - px if flip_x else px
                    ty = size - 1 - py if flip_y else py
                    wx = cell_world_x + tx
                    ox0 = out_of(wx)
                    ox1 = out_of(wx + 1)
                    for ox in range(ox0, ox1):
                        span[((row - row0) * size + ty) *
                             (span_w1 - span_w0) + ox - span_w0] = value_out
        patch_records.append((frame - FIRST_FRAME,
                              0 if name == "scroll2" else 1,
                              span_w0, span_w1 - span_w0, height,
                              len(patch_pixels)))
        patch_pixels += span
        # keep the master strip current so later patches base on it
        strip = bytearray(strip_bytes)
        for ox in range(span_w1 - span_w0):
            for y in range(height):
                strip[y * out_w + (span_w0 - out_of(world_x0)) + ox] = \
                    span[y * (span_w1 - span_w0) + ox]
        strips[name] = (bytes(strip), out_w, height, world_x0, row0)

    blob += struct.pack(">H", len(patch_records))
    for record in patch_records:
        blob += struct.pack(">HHHHHI", *record)

    # object schedule with TILES.BIN coverage.
    tile_codes = []
    if TILES_BIN.exists():
        tiles = TILES_BIN.read_bytes()
        count = int.from_bytes(tiles[4:8], "big")
        codes_offset = int.from_bytes(tiles[12:16], "big")
        tile_codes = [int.from_bytes(
            tiles[codes_offset + i * 4:codes_offset + i * 4 + 4], "big")
            for i in range(count)]
    code_rank = {code: rank for rank, code in enumerate(tile_codes)}
    covered = 0
    uncovered = 0
    for entries in objects_by_frame:
        blob += struct.pack(">H", len(entries))
        for x, y, code, attribute in entries:
            tile_code = code + ((y & 0x6000) << 3)
            rank = code_rank.get(tile_code, 0xFFFF)
            if rank == 0xFFFF:
                uncovered += 1
            else:
                covered += 1
            blob += struct.pack(">HhhHH", rank,
                                (x & 0x3FF) - VISIBLE_LEFT,
                                (y & 0x3FF) - VISIBLE_TOP,
                                attribute, (x >> 13) & 7)

    # patch plane headers, append pixel pools.
    pixel_cursor = len(blob) + len(patch_pixels)
    ordered = []
    for name in ("scroll2", "scroll3"):
        strip_bytes, out_w, height, world_x0, row0 = strips[name]
        struct.pack_into(">HHHHI", blob, header_pos[name],
                         out_w, height, world_x0, row0, pixel_cursor)
        ordered.append(strip_bytes)
        pixel_cursor += len(strip_bytes)
    blob += patch_pixels
    for strip_bytes in ordered:
        blob += strip_bytes

    OUTPUT_BIN.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_BIN.write_bytes(blob)

    manifest = {
        "schema": "rp4-street-planes-v0",
        "classification": "tracked manifest of the private STRIPS.BIN; "
                          "dimensions, counts and hashes only",
        "interval": {"first_frame": FIRST_FRAME, "last_frame": LAST_FRAME},
        "strips_bin_sha256": hashlib.sha256(blob).hexdigest(),
        "strips_bin_bytes": len(blob),
        "planes": {
            name: {
                "out_width": strips[name][1],
                "height": strips[name][2],
                "world_x0": strips[name][3],
                "row0": strips[name][4],
                "pixel_sha256": hashlib.sha256(strips[name][0]).hexdigest(),
                "colours_used": len(luts[name]) + 1,
            } for name in PLANES
        },
        "palette_cycle": {"bank": cycle_bank, "period_frames": period,
                          "states": len(palette_states)},
        "map_patches": len(patch_records),
        "object_schedule": {
            "frames": len(objects_by_frame),
            "entries": covered + uncovered,
            "tiles_bin_covered": covered,
            "tiles_bin_uncovered": uncovered,
        },
        "transform": "source_x = (out_x*383+175)//351, unwrapped world "
                     "space, shared by strips, patches and scroll",
    }
    OUTPUT_MANIFEST.write_text(
        json.dumps(manifest, indent=1, sort_keys=True) + "\n",
        encoding="ascii", newline="\n")
    print(f"strips: {manifest['strips_bin_bytes']} bytes, "
          f"scroll2 {strips['scroll2'][1]}x{strips['scroll2'][2]}, "
          f"scroll3 {strips['scroll3'][1]}x{strips['scroll3'][2]}, "
          f"patches {len(patch_records)}, objects covered {covered} / "
          f"uncovered {uncovered}")


if __name__ == "__main__":
    main()
