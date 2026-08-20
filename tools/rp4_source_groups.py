#!/usr/bin/env python3
"""Decode the emitted street object/tile groups from the RP4 fixture (pure).

This is the source half of the RP4 join. `STRIPS.BIN` carries the object
schedule the street renderer actually walks, and `TILES.BIN` carries the
tile pixels it uploads, so between them they say which tiles each CPS2
object-RAM entry turns into and what those tiles contain.

The tile expansion is a transcription of `avsp_entry_tiles` in
`avsp_tiles.c`, which is itself MAME 0.289's `cps2_render_sprites` block
expansion. Keeping a second copy here is deliberate: the join must be
computed from the fixture without running the Saturn build, so a
disagreement between this and the runtime is detectable rather than
shared.

Nothing here reads the emulator. It produces, per source object slot, the
tiles that slot emits and the SHA-256 of each tile's 4bpp bytes, which is
the key the captured VDP1 commands are joined on.
"""
from __future__ import annotations

import hashlib
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STREET_HEADER_BYTES = 8
PLANE_HEADER_BYTES = 20
CYCLE_HEADER_END = 48 + 1024 + 6
#: One 16x16 4bpp tile.
TILE_BYTES = 128


def u16(data: bytes, at: int) -> int:
    return struct.unpack_from(">H", data, at)[0]


def u32(data: bytes, at: int) -> int:
    return struct.unpack_from(">I", data, at)[0]


def objects_offset(data: bytes) -> tuple:
    """Walk the bundle headers exactly as avsp_street_bundle.c does."""
    frames = u16(data, 6)
    cycle_entries = u16(data, 48 + 1028)
    cycle_offset = CYCLE_HEADER_END
    scroll_offset = cycle_offset + cycle_entries * 6
    patch_offset = scroll_offset + frames * 8
    patch_count = u16(data, patch_offset)
    cursor = patch_offset + 2
    for _ in range(patch_count):
        updates = u16(data, cursor + 4)
        cursor += 6 + updates * 6
    return cursor, frames


def frame_entries(strips: bytes, target_rel: int) -> list:
    """The (x, y, code, attr) object entries for one fixture frame."""
    cursor, frames = objects_offset(strips)
    if not 0 <= target_rel < frames:
        raise ValueError("fixture frame %d outside 0..%d"
                         % (target_rel, frames - 1))
    for rel in range(frames):
        count = u16(strips, cursor)
        cursor += 2
        if rel == target_rel:
            return [tuple(struct.unpack_from(">HHHH", strips, cursor + i * 8))
                    for i in range(count)]
        cursor += count * 8
    raise AssertionError("unreachable")


def entry_tiles(y: int, code: int, attr: int) -> list:
    """Transcription of avsp_entry_tiles (MAME cps2_render_sprites)."""
    code17 = code + ((y & 0x6000) << 3)
    nx = ((attr >> 8) & 0xF) + 1
    ny = ((attr >> 12) & 0xF) + 1
    flip_x = (attr >> 5) & 1
    flip_y = (attr >> 6) & 1
    out = []
    for nys in range(ny):
        for nxs in range(nx):
            if flip_x or flip_y:
                sx = (nx - 1 - nxs) if flip_x else nxs
                sy = (ny - 1 - nys) if flip_y else nys
                tile = code17 + sx + 0x10 * sy
            else:
                tile = (code17 & ~0xF) + ((code17 + nxs) & 0xF) + 0x10 * nys
            out.append({"code": tile, "dx": nxs * 16, "dy": nys * 16,
                        "flip_x": bool(flip_x), "flip_y": bool(flip_y)})
    return out


def tile_archive(tiles: bytes) -> dict:
    """Map tile code -> SHA-256 of its 128 texture bytes, by archive rank."""
    count = u32(tiles, 8)
    codes_offset = u32(tiles, 12)
    data_offset = u32(tiles, 16) if len(tiles) >= 20 else None
    ranks = {}
    for index in range(count):
        code = u32(tiles, codes_offset + index * 4)
        ranks[code] = index
    return {"ranks": ranks, "count": count, "data_offset": data_offset}


def tile_texture_sha256(tiles: bytes, data_offset: int, rank: int) -> str:
    start = data_offset + rank * TILE_BYTES
    return hashlib.sha256(tiles[start:start + TILE_BYTES]).hexdigest()


def frame_tile_demand(strips: bytes, rel: int) -> dict:
    """How many tiles, and how many DISTINCT tiles, one frame draws.

    The distinct count is the number that must fit in the runtime's tile
    sprite pool. If it exceeds the pool, the pool evicts and overwrites
    texture VRAM inside a single frame, and commands emitted earlier in
    that frame end up pointing at another tile's pixels.
    """
    entries = frame_entries(strips, rel)
    codes = []
    for x, y, code, attr in entries:
        for tile in entry_tiles(y, code, attr):
            codes.append(tile["code"])
    return {
        "entries": len(entries),
        "tiles": len(codes),
        "distinct_tiles": len(set(codes)),
    }


def source_groups(strips: bytes, tiles: bytes, rel: int) -> list:
    """Per source object slot, the tile texture hashes it emits, in order."""
    archive = tile_archive(tiles)
    groups = []
    for slot, (x, y, code, attr) in enumerate(frame_entries(strips, rel)):
        textures = []
        for tile in entry_tiles(y, code, attr):
            rank = archive["ranks"].get(tile["code"])
            if rank is None:
                textures = None
                break
            textures.append(tile_texture_sha256(
                tiles, archive["data_offset"], rank))
        groups.append({
            "slot": slot,
            "x": x, "y": y, "code": code, "attr": attr,
            "textures": textures,
            "covered": textures is not None,
        })
    return groups


def main() -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rel", type=int, default=0)
    parser.add_argument("--strips", type=Path,
                        default=ROOT / "build/rp4_fixture/STRIPS.BIN")
    parser.add_argument("--tiles", type=Path,
                        default=ROOT / "build/avsp_cd/SPR4/TILES.BIN")
    args = parser.parse_args()

    strips = args.strips.read_bytes()
    demand = frame_tile_demand(strips, args.rel)
    print(json.dumps({"rel": args.rel, "demand": demand}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
