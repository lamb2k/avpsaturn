#!/usr/bin/env python3
"""Derive the combat presentation contract from one coherent MAME event stream.

The actor slot supplies the animation record, render inputs, collision selector,
and damage state.  The game's proven Family-1 object emitter then resolves the
exact object/tile identity for that same actor record.  Nearby object-list runs
are never used as actor identity.

Raw screenshots, crops, object RAM, palettes, and generated review media remain
private under .deps/mame/source_bound_combat.  The tracked output contains only
source addresses, semantic fields, geometry, and hashes.
"""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import extract_avspu_stage1 as avsp  # noqa: E402
from gen_avsp_gfx_tiles import entry_tile_codes  # noqa: E402

RAW = ROOT / ".deps/mame/source_bound_combat"
RUN_A = RAW / "run_c"
RUN_B = RAW / "run_d"
ORACLE = ROOT / ".deps/mame/vertical_slice/cold_run_1"
PROGRAM = ROOT / ".deps/mame/actorprobe/decrypted_program_2m.bin"
OUTPUT = ROOT / "data/avsp_source_combat_presentation_contract.json"
COLLISION = ROOT / "data/avsp_collision.json"
QA = RAW / "analysis"
PLAYER_ARCHIVE = ROOT / "build/avsp_cd/SPR4/PCMBT.RLE"
PLAYER_CACHE = RAW / "PCMBT.RLE"
PLAYER_HEADER = ROOT / "src/port_v2/integration/combat/source_player_generated.h"

FIRST = 5173
LAST = 5469
CONTACTS = (5190, 5236, 5283, 5329)
ATTACK_INPUT = (5185, 5230, 5275, 5320)
PLAYER_PRESENTATION = ((5187, 5205), (5232, 5250),
                       (5277, 5300), (5322, 5352))
REACTIONS = ((5191, 5227), (5237, 5277),
             (5284, 5322), (5330, 5469))
EXPECTED_HEALTH = ((87, 63), (63, 39), (39, 8), (8, -1))
EXPECTED_SELECTORS = (1, 2, 3, 4)
VISIBLE_LEFT = 64
VISIBLE_TOP = 16


@lru_cache(maxsize=1)
def gfx_region() -> bytearray:
    return avsp.load_gfx_region()


@lru_cache(maxsize=4096)
def decoded_tile(code: int) -> Image.Image:
    return avsp.decode_tile(gfx_region(), code, 16)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def u16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 2], "big")


def u32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 4], "big")


def s16(value: int) -> int:
    return value - 0x10000 if value & 0x8000 else value


def parse_tsv(path: Path) -> list[dict[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    return [dict(zip(header, line.split("\t"))) for line in lines[1:] if line]


def rows_by_frame(path: Path) -> dict[int, dict[str, str]]:
    return {int(row["frame"]): row for row in parse_tsv(path)}


def render_rows(path: Path) -> dict[tuple[int, str], dict[str, str]]:
    return {(int(row["frame"]), row["role"]): row for row in parse_tsv(path)}


def binary_words(path: Path) -> list[int]:
    data = path.read_bytes()
    return [u16(data, offset) for offset in range(0, len(data), 2)]


def palette(path: Path) -> list[tuple[int, int, int, int]]:
    data = path.read_bytes()
    if len(data) % 4:
        raise ValueError(f"{path}: invalid ARGB palette length")
    return [(data[o + 1], data[o + 2], data[o + 3], 255)
            for o in range(0, len(data), 4)]


@dataclass(frozen=True)
class EmitActor:
    world_x: int
    world_y: int
    world_z: int
    facing: int
    palette: int
    mode: int
    or_value: int
    anchor_x: int
    anchor_y: int


def actor_from_row(row: dict[str, str]) -> EmitActor:
    return EmitActor(
        int(row["world_x"]), int(row["world_y"]), int(row["world_z"]),
        int(row["facing"]), int(row["palette"]), int(row["mode"]),
        int(row["or_value"]), int(row["anchor_x"]), int(row["anchor_y"]))


def attr_final(raw: int, actor: EmitActor) -> int:
    flip = (actor.facing & 1) << 5
    if 1 <= actor.mode <= 0x7F:
        return (raw & 0xFF00) | ((((raw & 0xE0) + actor.palette) ^ flip) & 0xFF)
    return (raw & 0xFF00) | ((raw ^ flip) & 0xFF)


def emit_origin(rom: bytes, d2_address: int,
                actor: EmitActor) -> tuple[int, int]:
    d2 = u32(rom, d2_address)
    high, low = (d2 >> 16) & 0xFFFF, d2 & 0xFFFF
    y = (actor.anchor_y - actor.world_y + 0x100) & 0xFFFF
    y = (y + low if actor.facing & 2 else y - low) & 0xFFFF
    x = (actor.world_x - actor.anchor_x + 0x40) & 0xFFFF
    x = (x + high if actor.facing & 1 else x - high) & 0xFFFF
    return x, y


def emit_group(rom: bytes, header: int, actor: EmitActor,
               has_advance: bool) -> tuple[list[tuple[int, int, int, int]], int]:
    count, selector = u16(rom, header + 2), u16(rom, header + 4)
    if not 1 <= count <= 8:
        raise ValueError(f"bad emitter count {count} at 0x{header:06x}")
    a2 = 0x1FD1C8 + u16(rom, 0x1FD1C8 + selector * 2)
    origin_x, origin_y = emit_origin(rom, header + 6, actor)
    a0 = header + 10
    result = []
    for _ in range(count):
        code, raw = u16(rom, a0), u16(rom, a0 + 2)
        advance = u16(rom, a0 + 4) if has_advance else 0
        dx, dy = u16(rom, a2), u16(rom, a2 + 2)
        attr = attr_final(raw, actor)
        if actor.facing & 1:
            width = (((raw >> 8) & 0xF) + 1) * 16
            x = (origin_x - width - dx) & 0x3FF
        else:
            x = (origin_x + dx) & 0x3FF
        y = (origin_y + dy) & 0x3FF
        result.append((x | actor.or_value, y, code, attr))
        a0 += 6 if has_advance else 4
        a2 += 4 + advance
    return result, header + 10 + count * (6 if has_advance else 4)


def emit_family2(rom: bytes, payload: int,
                 actor: EmitActor) -> tuple[int, int, int, int]:
    raw, selector = u16(rom, payload), u16(rom, payload + 2)
    a2 = 0x1FD1C8 + u16(rom, 0x1FD1C8 + selector * 2)
    dx, dy = u16(rom, a2), u16(rom, a2 + 2)
    origin_x, origin_y = emit_origin(rom, payload + 4, actor)
    attr = attr_final(raw, actor)
    if actor.facing & 1:
        width = (((raw >> 8) & 0xF) + 1) * 16
        x = (origin_x - width - dx) & 0x3FF
    else:
        x = (origin_x + dx) & 0x3FF
    return x | actor.or_value, (origin_y + dy) & 0x3FF, u16(rom, payload + 8), attr


def emit_family_a(rom: bytes, payload: int, actor: EmitActor
                  ) -> tuple[list[tuple[int, int, int, int]], int]:
    count = u16(rom, payload)
    if not 1 <= count <= 16:
        raise ValueError(f"bad family-A count {count} at 0x{payload:06x}")
    origin_x, origin_y = emit_origin(rom, payload + 4, actor)
    pos, result = payload + 8, []
    for _ in range(count):
        code, raw, dx, dy = (u16(rom, pos + n) for n in (0, 2, 4, 6))
        attr = attr_final(raw, actor)
        if actor.facing & 1:
            width = (((raw >> 8) & 0xF) + 1) * 16
            x = (origin_x - width - dx) & 0x3FF
        else:
            x = (origin_x + dx) & 0x3FF
        result.append((x | actor.or_value, (origin_y + dy) & 0x3FF,
                       code, attr))
        pos += 8
    return result, pos


def emit_pose(rom: bytes, assembly: int,
              actor: EmitActor) -> list[tuple[int, int, int, int]]:
    top = u16(rom, assembly)
    if top == 0x000C:
        pos, records = assembly + 2, 2
    elif top in (0x0002, 0x0004, 0x0006, 0x000A):
        pos, records = assembly, 1
    else:
        raise ValueError(f"unsupported emitter tag 0x{top:04x} at 0x{assembly:06x}")
    result = []
    for _ in range(records):
        tag = u16(rom, pos)
        if tag in (0x0004, 0x0006):
            commands, pos = emit_group(rom, pos + 2, actor, tag == 0x0006)
            result.extend(commands)
        elif tag == 0x000A:
            commands, pos = emit_family_a(rom, pos + 4, actor)
            result.extend(commands)
        elif tag == 0x0002:
            result.append(emit_family2(rom, pos + 4, actor))
            pos += 14
        elif tag == 0x0008:
            pos += 4
        else:
            raise ValueError(f"unsupported nested tag 0x{tag:04x} at 0x{pos:06x}")
    return result


def decoded_commands(entries: list[tuple[int, int, int, int]]) -> list[dict[str, int]]:
    words = [word for entry in entries for word in entry] + [0, 0x8000, 0, 0]
    return avsp.decode_object_entries(words, reverse_priority=False)


def normalized_identity(commands: list[dict[str, int]],
                        pivot: tuple[int, int]) -> dict[str, object]:
    normalized = [{
        "tile_code": command["tile_code"],
        "attribute": command["attribute"],
        "palette": command["colour"],
        "x": command["screen_x"] - pivot[0],
        "y": command["screen_y"] - pivot[1],
        "width": command["width"], "height": command["height"],
    } for command in commands]
    object_bytes = json.dumps(normalized, sort_keys=True,
                              separators=(",", ":")).encode("ascii")
    tiles = sorted({tile for command in commands
                    for tile in entry_tile_codes(command["code"],
                                                 command["y"],
                                                 command["attribute"])})
    tile_bytes = ",".join(f"{tile:05x}" for tile in tiles).encode("ascii")
    return {"object_identity_sha256": sha(object_bytes),
            "tile_identity_sha256": sha(tile_bytes),
            "tile_codes": tiles,
            "palettes": sorted({command["colour"] for command in commands}),
            "command_count": len(commands)}


def fnv32(values) -> int:
    value = 2166136261
    for item in values:
        value = ((value ^ (item & 0xFFFF)) * 16777619) & 0xFFFFFFFF
    return value


def signed_10(value: int) -> int:
    value &= 0x3FF
    return value - 0x400 if value & 0x200 else value


def runtime_identity(entries: list[tuple[int, int, int, int]],
                     actor: EmitActor) -> dict[str, int]:
    object_values = []
    tile_values = []
    origin_x = 0x40 + actor.world_x - actor.anchor_x
    origin_y = (0x100 + 0xFF - actor.world_y) & 0x3FF
    for entry in reversed(entries):
        object_values.extend((signed_10((entry[0] & 0x3FF) -
                                        (origin_x & 0x3FF)),
                              signed_10((entry[1] & 0x3FF) - origin_y),
                              entry[2], entry[3]))
        x, y, code, attribute = entry
        code17 = code + ((y & 0x6000) << 3)
        nx = ((attribute >> 8) & 0xF) + 1
        ny = ((attribute >> 12) & 0xF) + 1
        flip_x = bool(attribute & 0x20)
        flip_y = bool(attribute & 0x40)
        for nys in range(ny):
            for nxs in range(nx):
                if flip_x or flip_y:
                    sx = nx - 1 - nxs if flip_x else nxs
                    sy = ny - 1 - nys if flip_y else nys
                    tile_values.append(code17 + sx + 0x10 * sy)
                else:
                    tile_values.append((code17 & ~0xF) +
                                       ((code17 + nxs) & 0xF) +
                                       0x10 * nys)
    return {"runtime_object_identity_fnv32": fnv32(object_values),
            "runtime_tile_identity_fnv32": fnv32(tile_values)}


def actor_pivot(actor: EmitActor) -> tuple[int, int]:
    return ((actor.world_x - actor.anchor_x) - VISIBLE_LEFT,
            186 - (actor.world_y - actor.world_z))


def render_actor(commands: list[dict[str, int]], source_palette,
                 pivot: tuple[int, int], size=(288, 192)) -> Image.Image:
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    origin_x = size[0] // 2 - pivot[0]
    origin_y = size[1] - 8 - pivot[1]
    for command in reversed(commands):
        attribute = command["attribute"]
        nx, ny = command["width"] // 16, command["height"] // 16
        flip_x, flip_y = bool(attribute & 0x20), bool(attribute & 0x40)
        for ty in range(ny):
            for tx in range(nx):
                sx = nx - 1 - tx if flip_x else tx
                sy = ny - 1 - ty if flip_y else ty
                base = command["tile_code"]
                code = ((base & ~0xF) + ((base + sx) & 0xF) + 0x10 * sy
                        if not flip_x and not flip_y else base + sx + 0x10 * sy)
                tile = decoded_tile(code)
                rgba = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
                pixels = rgba.load()
                for py in range(16):
                    for px in range(16):
                        pen = tile.getpixel((px, py))
                        if pen != 15:
                            pixels[15 - px if flip_x else px,
                                   15 - py if flip_y else py] = source_palette[
                                       command["colour"] * 16 + pen]
                canvas.alpha_composite(rgba, (origin_x + command["screen_x"] + tx * 16,
                                              origin_y + command["screen_y"] + ty * 16))
    return canvas


def render_indexed(commands: list[dict[str, int]], pivot: tuple[int, int],
                   colour: int = 0, size=(192, 192)) -> Image.Image:
    """Render one exact actor palette layer to the Saturn packed-cel index."""
    canvas = Image.new("P", size, 0)
    target = canvas.load()
    origin_x = size[0] // 2 - pivot[0]
    origin_y = size[1] - 8 - pivot[1]
    for command in reversed([c for c in commands if c["colour"] == colour]):
        attribute = command["attribute"]
        nx, ny = command["width"] // 16, command["height"] // 16
        flip_x, flip_y = bool(attribute & 0x20), bool(attribute & 0x40)
        for ty in range(ny):
            for tx in range(nx):
                sx = nx - 1 - tx if flip_x else tx
                sy = ny - 1 - ty if flip_y else ty
                base = command["tile_code"]
                code = ((base & ~0xF) + ((base + sx) & 0xF) + 0x10 * sy
                        if not flip_x and not flip_y else base + sx + 0x10 * sy)
                tile = decoded_tile(code)
                for py in range(16):
                    for px in range(16):
                        pen = tile.getpixel((px, py))
                        if pen == 15:
                            continue
                        dx = origin_x + command["screen_x"] + tx * 16 + (
                            15 - px if flip_x else px)
                        dy = origin_y + command["screen_y"] + ty * 16 + (
                            15 - py if flip_y else py)
                        if 0 <= dx < size[0] and 0 <= dy < size[1]:
                            target[dx, dy] = pen + 1
    return canvas


def write_player_archive(rom: bytes,
                         render: dict[tuple[int, str], dict[str, str]],
                         semantic: dict[int, dict[str, str]]) -> dict[str, object]:
    pose_index: dict[str, int] = {}
    encoded_poses: list[bytes] = []
    clip_poses: list[list[int]] = []
    clip_heights: list[list[int]] = []
    clip_records: list[list[int]] = []
    clip_actions: list[list[int]] = []
    clip_substates: list[list[int]] = []
    clip_pivot_x: list[list[int]] = []
    clip_pivot_y: list[list[int]] = []
    clip_object_identity: list[list[int]] = []
    clip_tile_identity: list[list[int]] = []
    for first, last in PLAYER_PRESENTATION:
        poses, heights, records, actions, substates = [], [], [], [], []
        pivot_xs, pivot_ys, object_ids, tile_ids = [], [], [], []
        for frame in range(first, last + 1):
            row = render[(frame, "player")]
            actor = actor_from_row(row)
            record = int(row["anim_record"], 16)
            entries = emit_pose(rom, u32(rom, record + 4), actor)
            commands = decoded_commands(entries)
            pivot = actor_pivot(actor)
            identities = runtime_identity(entries, actor)
            digest = str(normalized_identity(commands, pivot)[
                "object_identity_sha256"])
            if digest not in pose_index:
                image = render_indexed(commands, pivot)
                packed = avsp.pack_4bpp(image)
                pose_index[digest] = len(encoded_poses)
                encoded = avsp.rle_encode_bytes(packed)
                if avsp.rle_decode_bytes(encoded) != packed:
                    raise ValueError("source combat player RLE round trip failed")
                encoded_poses.append(encoded)
            poses.append(pose_index[digest])
            heights.append(actor.world_y - actor.world_z)
            records.append(record)
            sample = semantic[frame]
            actions.append(int(sample["p_action"]))
            substates.append(int(sample["p_sub"]))
            pivot_xs.append(pivot[0])
            pivot_ys.append(pivot[1])
            object_ids.append(identities["runtime_object_identity_fnv32"])
            tile_ids.append(identities["runtime_tile_identity_fnv32"])
        clip_poses.append(poses)
        clip_heights.append(heights)
        clip_records.append(records)
        clip_actions.append(actions)
        clip_substates.append(substates)
        clip_pivot_x.append(pivot_xs)
        clip_pivot_y.append(pivot_ys)
        clip_object_identity.append(object_ids)
        clip_tile_identity.append(tile_ids)
    archive = bytearray()
    offsets, lengths = [], []
    for encoded in encoded_poses:
        offsets.append(len(archive))
        lengths.append(len(encoded))
        archive.extend(encoded)
    PLAYER_ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    PLAYER_ARCHIVE.write_bytes(archive)
    PLAYER_CACHE.write_bytes(archive)
    max_frames = max(map(len, clip_poses))
    enemy_records = []
    enemy_actions = []
    enemy_substates = []
    enemy_world_x = []
    enemy_world_y = []
    enemy_world_z = []
    enemy_facing = []
    enemy_palettes = []
    enemy_object_identity = []
    enemy_tile_identity = []
    for first, last in REACTIONS:
        records, actions, substates = [], [], []
        xs, ys, zs, facings, palettes, object_ids, tile_ids = (
            [], [], [], [], [], [], [])
        for frame in range(first, last + 1):
            row = render[(frame, "street_alien")]
            actor = actor_from_row(row)
            record = int(row["anim_record"], 16)
            entries = emit_pose(rom, u32(rom, record + 4), actor)
            identities = runtime_identity(entries, actor)
            sample = semantic[frame]
            records.append(record)
            actions.append(int(sample["e_action"]))
            substates.append(int(sample["e_sub"]))
            xs.append(actor.world_x)
            ys.append(actor.world_y)
            zs.append(actor.world_z)
            facings.append(actor.facing)
            palettes.append(actor.palette)
            object_ids.append(identities["runtime_object_identity_fnv32"])
            tile_ids.append(identities["runtime_tile_identity_fnv32"])
        enemy_records.append(records)
        enemy_actions.append(actions)
        enemy_substates.append(substates)
        enemy_world_x.append(xs)
        enemy_world_y.append(ys)
        enemy_world_z.append(zs)
        enemy_facing.append(facings)
        enemy_palettes.append(palettes)
        enemy_object_identity.append(object_ids)
        enemy_tile_identity.append(tile_ids)
    max_enemy_frames = max(map(len, enemy_records))
    timeline_records = []
    timeline_actions = []
    timeline_substates = []
    timeline_world_x = []
    timeline_world_y = []
    timeline_world_z = []
    timeline_facing = []
    timeline_palettes = []
    timeline_object_identity = []
    timeline_tile_identity = []
    for frame in range(FIRST, LAST + 1):
        row = render[(frame, "street_alien")]
        actor = actor_from_row(row)
        record = int(row["anim_record"], 16)
        entries = emit_pose(rom, u32(rom, record + 4), actor)
        identities = runtime_identity(entries, actor)
        sample = semantic[frame]
        timeline_records.append(record)
        timeline_actions.append(int(sample["e_action"]))
        timeline_substates.append(int(sample["e_sub"]))
        timeline_world_x.append(actor.world_x)
        timeline_world_y.append(actor.world_y)
        timeline_world_z.append(actor.world_z)
        timeline_facing.append(actor.facing)
        timeline_palettes.append(actor.palette)
        timeline_object_identity.append(
            identities["runtime_object_identity_fnv32"])
        timeline_tile_identity.append(
            identities["runtime_tile_identity_fnv32"])

    def rows(values, suffix=""):
        return ",\n".join(
            "    {" + ", ".join(str(value) + suffix for value in row) +
            ", " + ", ".join("0" + suffix for _ in range(max_frames - len(row))) + "}"
            if len(row) < max_frames else
            "    {" + ", ".join(str(value) + suffix for value in row) + "}"
            for row in values)

    header = f"""/* Generated from the source-bound cadence-1 combat capture. */
#ifndef AVSP_SOURCE_COMBAT_PLAYER_GENERATED_H
#define AVSP_SOURCE_COMBAT_PLAYER_GENERATED_H
#define AVSP_SOURCE_COMBAT_PLAYER_CLIPS 4
#define AVSP_SOURCE_COMBAT_PLAYER_POSES {len(encoded_poses)}
#define AVSP_SOURCE_COMBAT_PLAYER_MAX_FRAMES {max_frames}
#define AVSP_SOURCE_COMBAT_PLAYER_DECODED_BYTES 18432
#define AVSP_SOURCE_COMBAT_PLAYER_ARCHIVE_FILE "PCMBT.RLE"
#define AVSP_SOURCE_COMBAT_PLAYER_ARCHIVE_BYTES {len(archive)}
static const unsigned int avsp_source_combat_player_rle_offsets[AVSP_SOURCE_COMBAT_PLAYER_POSES] = {{
    {", ".join(map(str, offsets))}
}};
static const unsigned short avsp_source_combat_player_rle_bytes[AVSP_SOURCE_COMBAT_PLAYER_POSES] = {{
    {", ".join(map(str, lengths))}
}};
static const unsigned char avsp_source_combat_player_frame_counts[AVSP_SOURCE_COMBAT_PLAYER_CLIPS] = {{
    {", ".join(str(len(row)) for row in clip_poses)}
}};
static const unsigned char avsp_source_combat_player_poses[AVSP_SOURCE_COMBAT_PLAYER_CLIPS][AVSP_SOURCE_COMBAT_PLAYER_MAX_FRAMES] = {{
{rows(clip_poses)}
}};
static const signed char avsp_source_combat_player_heights[AVSP_SOURCE_COMBAT_PLAYER_CLIPS][AVSP_SOURCE_COMBAT_PLAYER_MAX_FRAMES] = {{
{rows(clip_heights)}
}};
static const unsigned long avsp_source_combat_player_records[AVSP_SOURCE_COMBAT_PLAYER_CLIPS][AVSP_SOURCE_COMBAT_PLAYER_MAX_FRAMES] = {{
{rows(clip_records, "UL")}
}};
static const unsigned short avsp_source_combat_player_actions[AVSP_SOURCE_COMBAT_PLAYER_CLIPS][AVSP_SOURCE_COMBAT_PLAYER_MAX_FRAMES] = {{
{rows(clip_actions, "u")}
}};
static const unsigned short avsp_source_combat_player_substates[AVSP_SOURCE_COMBAT_PLAYER_CLIPS][AVSP_SOURCE_COMBAT_PLAYER_MAX_FRAMES] = {{
{rows(clip_substates, "u")}
}};
static const signed short avsp_source_combat_player_pivot_x[AVSP_SOURCE_COMBAT_PLAYER_CLIPS][AVSP_SOURCE_COMBAT_PLAYER_MAX_FRAMES] = {{
{rows(clip_pivot_x)}
}};
static const signed short avsp_source_combat_player_pivot_y[AVSP_SOURCE_COMBAT_PLAYER_CLIPS][AVSP_SOURCE_COMBAT_PLAYER_MAX_FRAMES] = {{
{rows(clip_pivot_y)}
}};
static const unsigned long avsp_source_combat_player_object_identity[AVSP_SOURCE_COMBAT_PLAYER_CLIPS][AVSP_SOURCE_COMBAT_PLAYER_MAX_FRAMES] = {{
{rows(clip_object_identity, "UL")}
}};
static const unsigned long avsp_source_combat_player_tile_identity[AVSP_SOURCE_COMBAT_PLAYER_CLIPS][AVSP_SOURCE_COMBAT_PLAYER_MAX_FRAMES] = {{
{rows(clip_tile_identity, "UL")}
}};
#define AVSP_SOURCE_COMBAT_ENEMY_MAX_FRAMES {max_enemy_frames}
static const unsigned char avsp_source_combat_enemy_frame_counts[AVSP_SOURCE_COMBAT_PLAYER_CLIPS] = {{
    {", ".join(str(len(row)) for row in enemy_records)}
}};
static const unsigned long avsp_source_combat_enemy_records[AVSP_SOURCE_COMBAT_PLAYER_CLIPS][AVSP_SOURCE_COMBAT_ENEMY_MAX_FRAMES] = {{
{rows(enemy_records, "UL")}
}};
static const unsigned short avsp_source_combat_enemy_actions[AVSP_SOURCE_COMBAT_PLAYER_CLIPS][AVSP_SOURCE_COMBAT_ENEMY_MAX_FRAMES] = {{
{rows(enemy_actions, "u")}
}};
static const unsigned short avsp_source_combat_enemy_substates[AVSP_SOURCE_COMBAT_PLAYER_CLIPS][AVSP_SOURCE_COMBAT_ENEMY_MAX_FRAMES] = {{
{rows(enemy_substates, "u")}
}};
static const unsigned short avsp_source_combat_enemy_world_x[AVSP_SOURCE_COMBAT_PLAYER_CLIPS][AVSP_SOURCE_COMBAT_ENEMY_MAX_FRAMES] = {{
{rows(enemy_world_x, "u")}
}};
static const unsigned short avsp_source_combat_enemy_world_y[AVSP_SOURCE_COMBAT_PLAYER_CLIPS][AVSP_SOURCE_COMBAT_ENEMY_MAX_FRAMES] = {{
{rows(enemy_world_y, "u")}
}};
static const unsigned short avsp_source_combat_enemy_world_z[AVSP_SOURCE_COMBAT_PLAYER_CLIPS][AVSP_SOURCE_COMBAT_ENEMY_MAX_FRAMES] = {{
{rows(enemy_world_z, "u")}
}};
static const unsigned char avsp_source_combat_enemy_facing[AVSP_SOURCE_COMBAT_PLAYER_CLIPS][AVSP_SOURCE_COMBAT_ENEMY_MAX_FRAMES] = {{
{rows(enemy_facing, "u")}
}};
static const unsigned char avsp_source_combat_enemy_palettes[AVSP_SOURCE_COMBAT_PLAYER_CLIPS][AVSP_SOURCE_COMBAT_ENEMY_MAX_FRAMES] = {{
{rows(enemy_palettes, "u")}
}};
static const unsigned long avsp_source_combat_enemy_object_identity[AVSP_SOURCE_COMBAT_PLAYER_CLIPS][AVSP_SOURCE_COMBAT_ENEMY_MAX_FRAMES] = {{
{rows(enemy_object_identity, "UL")}
}};
static const unsigned long avsp_source_combat_enemy_tile_identity[AVSP_SOURCE_COMBAT_PLAYER_CLIPS][AVSP_SOURCE_COMBAT_ENEMY_MAX_FRAMES] = {{
{rows(enemy_tile_identity, "UL")}
}};
#define AVSP_SOURCE_COMBAT_ENEMY_TIMELINE_FIRST {FIRST}
#define AVSP_SOURCE_COMBAT_ENEMY_TIMELINE_LAST {LAST}
#define AVSP_SOURCE_COMBAT_ENEMY_TIMELINE_FRAMES {LAST - FIRST + 1}
static const unsigned long avsp_source_combat_enemy_timeline_records[AVSP_SOURCE_COMBAT_ENEMY_TIMELINE_FRAMES] = {{
    {", ".join(str(value) + "UL" for value in timeline_records)}
}};
static const unsigned short avsp_source_combat_enemy_timeline_actions[AVSP_SOURCE_COMBAT_ENEMY_TIMELINE_FRAMES] = {{
    {", ".join(str(value) + "u" for value in timeline_actions)}
}};
static const unsigned short avsp_source_combat_enemy_timeline_substates[AVSP_SOURCE_COMBAT_ENEMY_TIMELINE_FRAMES] = {{
    {", ".join(str(value) + "u" for value in timeline_substates)}
}};
static const unsigned short avsp_source_combat_enemy_timeline_world_x[AVSP_SOURCE_COMBAT_ENEMY_TIMELINE_FRAMES] = {{
    {", ".join(str(value) + "u" for value in timeline_world_x)}
}};
static const unsigned short avsp_source_combat_enemy_timeline_world_y[AVSP_SOURCE_COMBAT_ENEMY_TIMELINE_FRAMES] = {{
    {", ".join(str(value) + "u" for value in timeline_world_y)}
}};
static const unsigned short avsp_source_combat_enemy_timeline_world_z[AVSP_SOURCE_COMBAT_ENEMY_TIMELINE_FRAMES] = {{
    {", ".join(str(value) + "u" for value in timeline_world_z)}
}};
static const unsigned char avsp_source_combat_enemy_timeline_facing[AVSP_SOURCE_COMBAT_ENEMY_TIMELINE_FRAMES] = {{
    {", ".join(str(value) + "u" for value in timeline_facing)}
}};
static const unsigned char avsp_source_combat_enemy_timeline_palettes[AVSP_SOURCE_COMBAT_ENEMY_TIMELINE_FRAMES] = {{
    {", ".join(str(value) + "u" for value in timeline_palettes)}
}};
static const unsigned long avsp_source_combat_enemy_timeline_object_identity[AVSP_SOURCE_COMBAT_ENEMY_TIMELINE_FRAMES] = {{
    {", ".join(str(value) + "UL" for value in timeline_object_identity)}
}};
static const unsigned long avsp_source_combat_enemy_timeline_tile_identity[AVSP_SOURCE_COMBAT_ENEMY_TIMELINE_FRAMES] = {{
    {", ".join(str(value) + "UL" for value in timeline_tile_identity)}
}};
#endif
"""
    PLAYER_HEADER.write_text(header, encoding="ascii", newline="\n")
    return {"path": "SPR4/PCMBT.RLE", "bytes": len(archive),
            "sha256": sha(archive), "unique_poses": len(encoded_poses),
            "clip_frames": [len(row) for row in clip_poses],
            "source_windows": [list(window) for window in PLAYER_PRESENTATION]}


def run_identity(run: Path) -> dict[str, str]:
    result = {}
    for name in ("samples.tsv", "actor_render.tsv"):
        result[name] = sha((run / name).read_bytes())
    digest = hashlib.sha256()
    for frame in range(FIRST, LAST + 1):
        for bucket, suffix in (("objram", "bin"), ("palette", "bin"),
                               ("cps_a", "bin"), ("cps_b", "bin"),
                               ("frames", "png")):
            digest.update((run / bucket / f"{frame:05d}.{suffix}").read_bytes())
    result["raw_frame_set"] = digest.hexdigest()
    return result


def enemy_timeline_contract(
        rom: bytes, render: dict[tuple[int, str], dict[str, str]]) -> dict:
    rows = []
    for frame in range(FIRST, LAST + 1):
        actor = actor_from_row(render[(frame, "street_alien")])
        record = int(render[(frame, "street_alien")]["anim_record"], 16)
        entries = emit_pose(rom, u32(rom, record + 4), actor)
        identities = runtime_identity(entries, actor)
        rows.append([frame, record, actor.palette, actor.world_x,
                     actor.world_y, actor.world_z,
                     identities["runtime_object_identity_fnv32"],
                     identities["runtime_tile_identity_fnv32"]])
    payload = json.dumps(rows, separators=(",", ":")).encode("ascii")
    return {"semantic_first": FIRST, "semantic_last": LAST,
            "visual_screen_first": FIRST + 1,
            "visual_screen_last": LAST + 1,
            "row_fields": ["semantic_frame", "animation_record", "palette",
                           "world_x", "world_y", "world_z",
                           "object_identity_fnv32", "tile_identity_fnv32"],
            "row_count": len(rows), "sequence_sha256": sha(payload)}


def verify_runs() -> dict[str, object]:
    first, second = run_identity(RUN_A), run_identity(RUN_B)
    if first != second:
        raise ValueError("source-bound MAME reruns differ")
    old = rows_by_frame(ORACLE / "samples.tsv")
    new = rows_by_frame(RUN_A / "samples.tsv")
    if any(old[frame] != new[frame] for frame in range(FIRST, LAST + 1)):
        raise ValueError("source-bound semantic rerun diverged from pinned oracle")
    for frame in range(FIRST, LAST + 1):
        for bucket, suffix in (("objram", "bin"), ("palette", "bin"),
                               ("cps_a", "bin"), ("cps_b", "bin"),
                               ("frames", "png")):
            if ((ORACLE / bucket / f"{frame:05d}.{suffix}").read_bytes() !=
                    (RUN_A / bucket / f"{frame:05d}.{suffix}").read_bytes()):
                raise ValueError(f"frame {frame}: {bucket} diverged from pinned oracle")
    return {"byte_identical_reruns": True, "pinned_oracle_subset_match": True,
            "window": [FIRST, LAST], "identities": first}


def command_in_object_list(frame: int, entry: tuple[int, int, int, int]) -> bool:
    words = binary_words(RUN_A / "objram" / f"{frame:05d}.bin")
    return any(tuple(words[offset:offset + 4]) == entry
               for offset in range(0, len(words) - 3, 4))


def observed_count(frame: int,
                   entries: list[tuple[int, int, int, int]]) -> int:
    return sum(command_in_object_list(frame, entry) for entry in entries)


def main() -> None:
    provenance = verify_runs()
    semantic = rows_by_frame(RUN_A / "samples.tsv")
    render = render_rows(RUN_A / "actor_render.tsv")
    rom = PROGRAM.read_bytes()
    collision = json.loads(COLLISION.read_text())
    player_collision = next(
        family for family in collision["families"]
        if family["table_set"] == "0x11ae02")
    enemy_collision = next(
        family for family in collision["families"]
        if family["table_set"] == "0x130ac8")
    enemy_hurt = enemy_collision["hurt_entries"][1]
    player_archive = write_player_archive(rom, render, semantic)
    enemy_timeline = enemy_timeline_contract(rom, render)
    QA.mkdir(parents=True, exist_ok=True)
    events = []
    contact_crops = []
    visual_frames = {}
    for index, contact in enumerate(CONTACTS):
        player_row = render[(contact, "player")]
        enemy_row = render[(contact, "street_alien")]
        p_actor, e_actor = actor_from_row(player_row), actor_from_row(enemy_row)
        p_record = int(player_row["anim_record"], 16)
        e_record = int(enemy_row["anim_record"], 16)
        p_assembly, e_assembly = u32(rom, p_record + 4), u32(rom, e_record + 4)
        p_entries = emit_pose(rom, p_assembly, p_actor)
        e_entries = emit_pose(rom, e_assembly, e_actor)
        # The player record is already active when the contact sample is taken.
        # Enemy contact/reaction state is written after that frame's object-list
        # build and therefore becomes visible one frame later.  Preserve this
        # measured pipeline delay instead of cross-wiring the newer semantic
        # record to the older rendered list.
        player_render_frame = contact
        enemy_contact_render_frame = contact + 1
        player_observed = observed_count(player_render_frame, p_entries)
        enemy_observed = observed_count(enemy_contact_render_frame, e_entries)
        if player_observed == 0 or enemy_observed == 0:
            raise ValueError(f"frame {contact}: source emitter has no object-list witness")
        p_commands, e_commands = decoded_commands(p_entries), decoded_commands(e_entries)
        p_pivot, e_pivot = actor_pivot(p_actor), actor_pivot(e_actor)
        sample = semantic[contact]
        selector = int(sample["p_attack"])
        attack = player_collision["attack_entries"][selector]
        before, after = EXPECTED_HEALTH[index]
        if (selector != EXPECTED_SELECTORS[index] or
                attack["inactive"] or int(sample["e_health"]) != after):
            raise ValueError(f"frame {contact}: selector/damage contract drift")
        player_identity = normalized_identity(p_commands, p_pivot)
        player_identity.update(runtime_identity(p_entries, p_actor))
        enemy_contact_identity = normalized_identity(e_commands, e_pivot)
        enemy_contact_identity.update(runtime_identity(e_entries, e_actor))
        reaction_frame = REACTIONS[index][0]
        rr = render[(reaction_frame, "street_alien")]
        reaction_actor = actor_from_row(rr)
        reaction_record = int(rr["anim_record"], 16)
        reaction_entries = emit_pose(rom, u32(rom, reaction_record + 4), reaction_actor)
        reaction_render_frame = reaction_frame + 1
        reaction_observed = observed_count(reaction_render_frame,
                                           reaction_entries)
        if reaction_observed == 0:
            raise ValueError(f"frame {reaction_frame}: reaction has no object-list witness")
        reaction_commands = decoded_commands(reaction_entries)
        reaction_identity = normalized_identity(reaction_commands,
                                                actor_pivot(reaction_actor))
        reaction_identity.update(runtime_identity(reaction_entries,
                                                  reaction_actor))
        event = {
            "event_index": index, "attack_sequence_step": index + 1,
            "attack_input_frame": ATTACK_INPUT[index],
            "player_presentation_window": list(PLAYER_PRESENTATION[index]),
            "contact_frame": contact,
            "contact_offset": contact - CONTACTS[0],
            "reaction_window": list(REACTIONS[index]),
            "attack_selector": selector,
            "collision": {
                "player_table_set": player_collision["table_set"],
                "attack_selector": selector,
                "attack_record": attack["address"],
                "attack_box": attack["box"],
                "hit_value": attack["hit_value"],
                "enemy_table_set": enemy_collision["table_set"],
                "hurt_selector": 1,
                "hurt_record": enemy_hurt["address"],
                "hurt_box": enemy_hurt["box"],
                "overlap_result": True,
            },
            "hit_value": attack["hit_value"],
            "health_before": before, "health_after": after,
            "player": {
                "slot": player_row["slot"], "role": "player",
                "action": int(sample["p_action"]),
                "substate": int(sample["p_sub"]),
                "animation_record": f"0x{p_record:06x}",
                "assembly": f"0x{p_assembly:06x}",
                "world": [p_actor.world_x, p_actor.world_y, p_actor.world_z],
                "height": p_actor.world_y - p_actor.world_z,
                "facing": p_actor.facing, "pivot": list(p_pivot),
                "source_render_frame": player_render_frame,
                "emitted_commands": len(p_entries),
                "object_list_witnesses": player_observed,
                **player_identity,
            },
            "enemy_contact": {
                "slot": enemy_row["slot"], "role": "street_alien",
                "class_id": int(enemy_row["class_id"]),
                "type": int(enemy_row["type"]),
                "palette": e_actor.palette, "mode": e_actor.mode,
                "action": int(sample["e_action"]),
                "substate": int(sample["e_sub"]),
                "animation_record": f"0x{e_record:06x}",
                "assembly": f"0x{e_assembly:06x}",
                "world": [e_actor.world_x, e_actor.world_y, e_actor.world_z],
                "facing": e_actor.facing, "pivot": list(e_pivot),
                "source_render_frame": enemy_contact_render_frame,
                "emitted_commands": len(e_entries),
                "object_list_witnesses": enemy_observed,
                **enemy_contact_identity,
            },
            "enemy_reaction": {
                "first_visible_frame": reaction_frame,
                "animation_record": f"0x{reaction_record:06x}",
                "assembly": f"0x{u32(rom, reaction_record + 4):06x}",
                "palette": reaction_actor.palette,
                "source_render_frame": reaction_render_frame,
                "emitted_commands": len(reaction_entries),
                "object_list_witnesses": reaction_observed,
                **reaction_identity,
            },
        }
        events.append(event)
        source_palette = palette(
            RUN_A / "palette" / f"{player_render_frame:05d}.bin")
        p_image = render_actor(p_commands, source_palette, p_pivot)
        enemy_palette = palette(
            RUN_A / "palette" / f"{enemy_contact_render_frame:05d}.bin")
        e_image = render_actor(e_commands, enemy_palette, e_pivot)
        r_palette = palette(
            RUN_A / "palette" / f"{reaction_render_frame:05d}.bin")
        r_image = render_actor(reaction_commands, r_palette,
                               actor_pivot(reaction_actor))
        p_image.save(QA / f"event-{index + 1}-player-contact.png")
        e_image.save(QA / f"event-{index + 1}-alien-contact.png")
        r_image.save(QA / f"event-{index + 1}-alien-reaction.png")
        contact_crops.append((index + 1, p_image, e_image, r_image))
        visual_frames[index + 1] = {
            "player_contact_rgba_sha256": sha(p_image.tobytes()),
            "alien_contact_rgba_sha256": sha(e_image.tobytes()),
            "alien_reaction_rgba_sha256": sha(r_image.tobytes()),
        }

    sheet = Image.new("RGB", (288 * 3, 192 * 4), (24, 24, 28))
    draw = ImageDraw.Draw(sheet)
    for row, (event_id, player, enemy, reaction) in enumerate(contact_crops):
        for column, (label, actor_image) in enumerate(
                (("PLAYER CONTACT", player), ("ALIEN CONTACT", enemy),
                 ("ALIEN REACTION", reaction))):
            x, y = column * 288, row * 192
            sheet.paste(actor_image, (x, y), actor_image)
            draw.text((x + 4, y + 4), f"EVENT {event_id} {label}", fill="white")
    sheet.save(QA / "source-event-contact-sheet.png")

    contract = {
        "schema": 1, "task_id": "REPAIR-09-SOURCE-BOUND-COMBAT-PRESENTATION",
        "classification": "MEASURED MAME source contract",
        "target": {"set": "avspu", "revision": "USA 940520"},
        "source": {
            "mame_version": "0.289 (mame0289)",
            "program_sha256": sha(rom), **provenance,
        },
        "event_pipeline": (
            "one event binds selector, player record/assembly/object/tile, "
            "collision state, damage, and enemy reaction record/assembly/object/tile"),
        "contact_offsets": [0, 46, 93, 139],
        "source_player_archive": player_archive,
        "source_enemy_timeline": enemy_timeline,
        "events": events,
        "visual_crops": visual_frames,
        "negative_controls": [
            "selector from a different event", "wrong nonzero player object family",
            "wrong nonzero player tile family", "wrong enemy reaction record",
            "valid neighboring alien object family", "wrong palette",
            "damage without the event active window"],
        "physical_saturn": "UNRUN",
    }
    OUTPUT.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    print(f"Source-bound combat: {len(events)} events, reruns identical, contract {sha(OUTPUT.read_bytes())}")


if __name__ == "__main__":
    main()
