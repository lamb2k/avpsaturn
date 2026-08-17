#!/usr/bin/env python3
"""Decode the locally supplied avspu CPS2 object layer for Saturn conversion."""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
ROM_ROOT = ROOT / "avspu"
CAPTURE_ROOT = ROOT / ".deps" / "mame" / "captures"
PLAYER_ACTION_ROOT = ROOT / ".deps" / "mame" / "player_actions"
OUTPUT_ROOT = ROOT / "build" / "rom_extract"
SATURN_CD_ROOT = ROOT / "build" / "avsp_cd"
GENERATED_ROOT = ROOT / "generated"
VISIBLE_LEFT = 64
VISIBLE_TOP = 16
VISIBLE_WIDTH = 384
VISIBLE_HEIGHT = 224
SATURN_VIEW_WIDTH = 352
SATURN_FITTED_BACKGROUND_WIDTH = 469
STAGE1_ACTIVE_OBJECT_RAM = "objram2.tsv"
ANIMATION_SAMPLE_ACTIVE_BANK = {2880: 2, 2940: 2}
STAGE1_ENCOUNTER_ANCHORS = (2760, 3000, 3240, 3480, 3600, 3720,
                            3840, 3960, 4080, 4200)
STAGE1_SATURN_SPAWNS = (
    (36, 174, 1, 2760),
    (92, 190, 2, 2760),
    (154, 158, 1, 2760),
    (224, 196, 0, 2760),
    (348, 180, 1, 3000),
    (18, 164, 3, 3480),
    (286, 154, 0, 3480),
    (366, 198, 2, 3480),
)
STAGE1_OBJECT_GROUPS = (
    ("capture_padding", "nonvisual", "verified", (0, 4, 8)),
    ("ground_shadows", "shadow_sprites", "verified",
     (12, 16, 20, 24, 28, 32, 36, 40, 44, 48)),
    ("alien_left_edge", "actor", "verified", (52, 56, 60)),
    ("predator_player", "actor", "verified", (64, 68, 72, 76, 80, 84, 88)),
    ("purple_alien", "actor", "verified",
     (92, 96, 100, 104, 108, 132, 136, 140)),
    ("right_edge_actor_fragment", "actor_candidate", "candidate", (112, 116, 120)),
    ("blue_alien_middle", "actor", "verified", (124, 128)),
    ("blue_alien_left", "actor", "verified", (144, 148)),
    ("floor_fragment", "actor_candidate", "candidate", (152, 156)),
    ("green_alien_middle", "actor", "verified", (160, 164)),
    ("barrel", "prop", "verified", (168, 172)),
    ("blue_alien_right", "actor", "verified", (176, 180)),
    ("left_edge_prop_fragment", "prop_candidate", "candidate", (184, 188, 192, 196)),
    ("street_signs", "prop", "verified", (200, 204, 208, 212)),
)

EXPECTED_SHA1 = {
    "avp.13m": "457ce959aa5db3a003de7dda2b3799b2f1ae279b",
    "avp.14m": "911754d8930e0df71a3d929e4bc80f9efb9ad1ff",
    "avp.15m": "bc1291a4a222d410bc99b6f1ed392067d9c3999e",
    "avp.16m": "25595161500eae9c9b329ca37a4b306ab8b96430",
    "avp.17m": "efaad001527a5eba8f626aea9037ac6ef9a2c295",
    "avp.18m": "0de6bdca37a4ac05568b23cb071c66f51f737c08",
    "avp.19m": "809ccb7f10262e227d5e9d9f710e06f0e751f550",
    "avp.20m": "7c90a9b98eba9b26992d3d02875b64431b941c24",
}


def verify_roms() -> None:
    for name, expected in EXPECTED_SHA1.items():
        path = ROM_ROOT / name
        actual = hashlib.sha1(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"{name}: expected SHA-1 {expected}, found {actual}")


def load_gfx_region() -> bytearray:
    region = bytearray(0x1000000)
    groups = [
        (0x0000000, ["avp.13m", "avp.15m", "avp.17m", "avp.19m"]),
        (0x0800000, ["avp.14m", "avp.16m", "avp.18m", "avp.20m"]),
    ]
    for base, names in groups:
        for lane, name in enumerate(names):
            source = (ROM_ROOT / name).read_bytes()
            destination = base + lane * 2
            for offset in range(0, len(source), 2):
                target = destination + (offset // 2) * 8
                region[target:target + 2] = source[offset:offset + 2]

    # CPS2 boards store each 2 MiB graphics bank in a recursively shuffled
    # order.  MAME performs this same 64-bit-block permutation during video
    # initialisation before the standard CPS tile layouts see the data.
    def unshuffle(start: int, block_count: int) -> None:
        if block_count == 2:
            return
        half = block_count // 2
        unshuffle(start, half)
        unshuffle(start + half * 8, half)
        for index in range(half // 2):
            left = start + (half // 2 + index) * 8
            right = start + (half + index) * 8
            temporary = region[left:left + 8]
            region[left:left + 8] = region[right:right + 8]
            region[right:right + 8] = temporary

    bank_size = 0x200000
    for bank_start in range(0, len(region), bank_size):
        unshuffle(bank_start, bank_size // 8)
    return region


def verify_loaded_gfx_region(region: bytearray) -> None:
    """Compare against MAME's optional diagnostic dump when it is present."""
    diagnostic = CAPTURE_ROOT / "gfx_region.bin"
    if diagnostic.exists():
        reference = diagnostic.read_bytes()
        if region != reference:
            raise ValueError("decoded graphics region differs from MAME's loaded :gfx region")


def load_words(name: str) -> list[int]:
    lines = (CAPTURE_ROOT / name).read_text(encoding="utf-8").splitlines()[1:]
    return [int(line.split("\t")[1], 16) for line in lines if line]


def load_palette(name: str = "palette.tsv") -> list[tuple[int, int, int, int]]:
    palette = []
    lines = (CAPTURE_ROOT / name).read_text(encoding="utf-8").splitlines()[1:]
    for line in lines:
        argb = int(line.split("\t")[1], 16)
        palette.append(((argb >> 16) & 255, (argb >> 8) & 255, argb & 255, 255))
    return palette


def load_palette_path(path: Path) -> list[tuple[int, int, int, int]]:
    palette = []
    lines = path.read_text(encoding="utf-8").splitlines()[1:]
    for line in lines:
        argb = int(line.split("\t")[1], 16)
        palette.append(((argb >> 16) & 255, (argb >> 8) & 255,
                        argb & 255, 255))
    return palette


@lru_cache(maxsize=1)
def load_animation_sample_banks() -> dict[int, int]:
    lines = (CAPTURE_ROOT / "animation_samples.tsv").read_text(
        encoding="utf-8").splitlines()[1:]
    samples = {}
    for line in lines:
        if not line:
            continue
        frame, bank, _ = line.split("\t")
        samples[int(frame)] = int(bank)
    return samples


def animation_object_filename(frame: int, expected_bank: int) -> str:
    samples = load_animation_sample_banks()
    captured_bank = samples.get(frame)
    if captured_bank is None:
        raise ValueError(f"frame {frame} is absent from animation_samples.tsv")
    if captured_bank != expected_bank:
        raise ValueError(
            f"frame {frame}: expected active bank {expected_bank}, captured {captured_bank}")
    return f"objram_active_{frame:04d}.tsv"


def animation_palette(frame: int) -> list[tuple[int, int, int, int]]:
    return load_palette(f"palette_{frame:04d}.tsv")


def decode_tile(gfx: bytearray, code: int, size: int, right_half: bool = False) -> Image.Image:
    """Decode one tile using the four standard CPS graphics layouts."""
    if size not in (8, 16, 32):
        raise ValueError(f"unsupported CPS tile size {size}")
    image = Image.new("P", (size, size), 15)
    pixels = image.load()
    plane_offsets = (24, 16, 8, 0)
    if size == 8:
        x_offsets = tuple(range(32, 40)) if right_half else tuple(range(8))
        stride_bits = 512
        y_stride = 64
    else:
        x_offsets = tuple(offset + bit for offset in range(0, size * 4, 32) for bit in range(8))
        stride_bits = 4 * size * size
        y_stride = 4 * size
    base = code * stride_bits
    for y in range(size):
        for x in range(size):
            pen = 0
            for plane, plane_offset in enumerate(plane_offsets):
                bit_index = base + y * y_stride + x_offsets[x] + plane_offset
                bit = (gfx[bit_index >> 3] >> (7 - (bit_index & 7))) & 1
                pen |= bit << (3 - plane)
            pixels[x, y] = pen
    return image


def render_background(gfx: bytearray, gfxram: list[int], cps_a: list[int],
                      cps_b: list[int], palette: list[tuple[int, int, int, int]],
                      width: int = VISIBLE_WIDTH, height: int = VISIBLE_HEIGHT,
                      include_scroll1: bool = True) -> Image.Image:
    """Flatten the three live CPS tilemaps from the captured Stage 1 frame."""
    canvas = Image.new("RGBA", (width, height), palette[0xBFF])
    layer_control = cps_b[0x26 // 2]
    order = [
        (layer_control >> 6) & 3,
        (layer_control >> 8) & 3,
        (layer_control >> 10) & 3,
        (layer_control >> 12) & 3,
    ]
    # CPS2 removes the sprite layer from the tilemap ordering and draws the
    # remaining three tilemaps from back to front before the object pass.
    order = [layer for layer in order if layer != 0]
    if not include_scroll1:
        order = [layer for layer in order if layer != 1]

    base_words = []
    for register in (1, 2, 3):
        byte_address = (cps_a[register] * 256) & 0x3FFFF
        byte_address &= ~(0x4000 - 1)
        base_words.append(byte_address // 2)
    scroll_x = (cps_a[6], cps_a[8], cps_a[10])
    scroll_y = (cps_a[7], cps_a[9], cps_a[11])
    other_base = (((cps_a[4] * 256) & 0x3FFFF) & ~(0x800 - 1)) // 2
    row_scroll_offset = cps_a[16]
    row_scroll_enabled = bool(cps_a[17] & 1)

    @lru_cache(maxsize=8192)
    def indexed_tile(code: int, size: int, right_half: bool, flip_x: bool,
                     flip_y: bool, colour: int) -> Image.Image:
        indexed = decode_tile(gfx, code, size, right_half)
        rgba = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        source = indexed.load()
        target = rgba.load()
        for y in range(size):
            for x in range(size):
                pen = source[x, y]
                if pen != 15:
                    tx = size - 1 - x if flip_x else x
                    ty = size - 1 - y if flip_y else y
                    target[tx, ty] = palette[colour * 16 + pen]
        return rgba

    for layer_number in order:
        layer_index = layer_number - 1
        size = (8, 16, 32)[layer_index]
        enable_mask = (0x02, 0x04, 0x08)[layer_index]
        if not (layer_control & enable_mask):
            continue
        if layer_index > 0 and not (cps_a[17] & (1 << (layer_index + 1))):
            continue
        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        tile_cache: dict[tuple[int, int], Image.Image] = {}
        for screen_y in range(height):
            raw_y = screen_y + VISIBLE_TOP
            world_y = (raw_y + scroll_y[layer_index]) % (64 * size)
            row = world_y // size
            pixel_y = world_y % size
            extra_x = 0
            if layer_index == 1 and row_scroll_enabled:
                extra_x = gfxram[other_base + ((raw_y + row_scroll_offset) & 0x3FF)]
            for screen_x in range(width):
                raw_x = screen_x + VISIBLE_LEFT
                world_x = (raw_x + scroll_x[layer_index] + extra_x) % (64 * size)
                column = world_x // size
                pixel_x = world_x % size
                if layer_index == 0:
                    tile_index = (row & 0x1F) + ((column & 0x3F) << 5) + ((row & 0x20) << 6)
                elif layer_index == 1:
                    tile_index = (row & 0x0F) + ((column & 0x3F) << 4) + ((row & 0x30) << 6)
                else:
                    tile_index = (row & 0x07) + ((column & 0x3F) << 3) + ((row & 0x38) << 6)
                key = (tile_index, layer_index)
                tile_image = tile_cache.get(key)
                if tile_image is None:
                    code = gfxram[base_words[layer_index] + tile_index * 2]
                    attribute = gfxram[base_words[layer_index] + tile_index * 2 + 1]
                    if layer_index == 0:
                        code = 0x20000 + code
                        right_half = bool(tile_index & 0x20)
                        colour = (attribute & 0x1F) + 0x20
                    elif layer_index == 1:
                        code = 0x10000 + (code & 0xFFFF)
                        right_half = False
                        colour = (attribute & 0x1F) + 0x40
                    else:
                        code = 0x4000 + (code & 0x3FFF)
                        right_half = False
                        colour = (attribute & 0x1F) + 0x60
                    tile_image = indexed_tile(code, size, right_half,
                                              bool(attribute & 0x20),
                                              bool(attribute & 0x40), colour)
                    tile_cache[key] = tile_image
                pixel = tile_image.getpixel((pixel_x, pixel_y))
                if pixel[3]:
                    layer.putpixel((screen_x, screen_y), pixel)
        canvas.alpha_composite(layer)
    return canvas


def decode_object_entries(words: list[int]) -> list[dict[str, int]]:
    raw_entries = []
    for offset in range(0, len(words) - 3, 4):
        x, y, code, attribute = words[offset:offset + 4]
        if y >= 0x8000 or attribute >= 0xFF00:
            break
        raw_entries.append(
            {"offset": offset, "x": x, "y": y, "code": code,
             "attribute": attribute})

    rendered = []
    for entry in reversed(raw_entries):
        raw_x = entry["x"]
        raw_y = entry["y"]
        attribute = entry["attribute"]
        nx = ((attribute >> 8) & 0x0F) + 1 if attribute & 0xFF00 else 1
        ny = ((attribute >> 12) & 0x0F) + 1 if attribute & 0xFF00 else 1
        rendered.append({
            **entry,
            "tile_code": entry["code"] + ((raw_y & 0x6000) << 3),
            "screen_x": (raw_x & 0x3FF) - VISIBLE_LEFT,
            "screen_y": (raw_y & 0x3FF) - VISIBLE_TOP,
            "width": nx * 16,
            "height": ny * 16,
            "colour": attribute & 0x1F,
            "priority": (raw_x >> 13) & 0x07,
        })
    return rendered


def decode_objects(gfx: bytearray, words: list[int], palette: list[tuple[int, int, int, int]]) -> tuple[Image.Image, list[dict[str, int]]]:
    plane_offsets = (24, 16, 8, 0)
    x_offsets = tuple(range(8)) + tuple(range(32, 40))

    @lru_cache(maxsize=4096)
    def tile(code: int, colour: int, flip_x: bool, flip_y: bool) -> Image.Image:
        image = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        pixels = image.load()
        base = code * 1024
        for y in range(16):
            for x in range(16):
                pen = 0
                for plane, plane_offset in enumerate(plane_offsets):
                    bit_index = base + y * 64 + x_offsets[x] + plane_offset
                    bit = (gfx[bit_index >> 3] >> (7 - (bit_index & 7))) & 1
                    pen |= bit << (3 - plane)
                if pen != 15:
                    target_x = 15 - x if flip_x else x
                    target_y = 15 - y if flip_y else y
                    pixels[target_x, target_y] = palette[colour * 16 + pen]
        return image

    layer = Image.new("RGBA", (VISIBLE_WIDTH, VISIBLE_HEIGHT), (0, 0, 0, 0))
    rendered = decode_object_entries(words)
    for entry in rendered:
        code = entry["tile_code"]
        attribute = entry["attribute"]
        colour = entry["colour"]
        flip_x = bool(attribute & 0x20)
        flip_y = bool(attribute & 0x40)
        nx = entry["width"] // 16
        ny = entry["height"] // 16
        screen_x = entry["screen_x"]
        screen_y = entry["screen_y"]

        for tile_y in range(ny):
            for tile_x in range(nx):
                if flip_y:
                    source_y = ny - 1 - tile_y
                else:
                    source_y = tile_y
                if flip_x:
                    source_x = nx - 1 - tile_x
                else:
                    source_x = tile_x
                if not flip_x and not flip_y:
                    tile_code = (code & ~0xF) + ((code + source_x) & 0xF) + 0x10 * source_y
                else:
                    tile_code = code + source_x + 0x10 * source_y
                target_x = screen_x + tile_x * 16
                target_y = screen_y + tile_y * 16
                layer.alpha_composite(tile(tile_code, colour, flip_x, flip_y), (target_x, target_y))
    return layer, rendered


def final_visible_object_surface(background: Image.Image,
                                 object_layer: Image.Image) -> Image.Image:
    """Recover the final CPS2 object/priority result from the MAME reference."""
    reference = Image.open(CAPTURE_ROOT / "stage1_4200.png").convert("RGBA")
    if reference.size != background.size or reference.size != object_layer.size:
        raise ValueError("MAME reference, background, and object dimensions differ")
    result = Image.new("RGBA", reference.size, (0, 0, 0, 0))
    reference_pixels = reference.load()
    background_pixels = background.load()
    object_pixels = object_layer.load()
    result_pixels = result.load()
    for y in range(reference.height):
        for x in range(reference.width):
            if (object_pixels[x, y][3] and
                    reference_pixels[x, y][:3] != background_pixels[x, y][:3]):
                result_pixels[x, y] = reference_pixels[x, y]
    return result


def verify_stage1_object_capture(entries: list[dict[str, int]]) -> None:
    """Reject a stale capture or the inactive CPS2 object-RAM bank."""
    expected = {
        (68, 320, 82, 773, 0),       # Predator body, partly outside the crop
        (124, 87, 142, 20288, 16),   # left blue alien upper assembly
        (128, 105, 152, 17973, 16),  # left blue alien lower assembly
        (140, 136, 104, 18016, 17),  # purple alien main assembly
    }
    actual = {
        (entry["offset"], entry["screen_x"], entry["screen_y"],
         entry["code"], entry["colour"])
        for entry in entries
    }
    if len(entries) != 54 or not expected.issubset(actual):
        raise ValueError(
            f"{STAGE1_ACTIVE_OBJECT_RAM}: expected the verified 54-command "
            "Stage 1 active-bank signature")


def verify_animation_bank_alignment(gfx: bytearray) -> None:
    """Prove the tapped active bank matches pixels in representative screenshots."""
    report = []
    samples = load_animation_sample_banks()
    for frame in (2880, 4200):
        reference = Image.open(
            CAPTURE_ROOT / f"stage1_sample_{frame:04d}.png").convert("RGBA")
        reference_pixels = reference.load()
        palette = animation_palette(frame)
        scores = {}
        for bank in (1, 2):
            filename = (f"objram{bank}.tsv" if frame == 4200 else
                        f"objram{bank}_{frame:04d}.tsv")
            layer, _ = decode_objects(gfx, load_words(filename), palette)
            layer_pixels = layer.load()
            opaque = 0
            matches = 0
            for y in range(layer.height):
                for x in range(layer.width):
                    pixel = layer_pixels[x, y]
                    if pixel[3]:
                        opaque += 1
                        if pixel[:3] == reference_pixels[x, y][:3]:
                            matches += 1
            scores[bank] = {"matching_pixels": matches, "opaque_pixels": opaque}
        active_bank = samples.get(frame)
        if active_bank not in (1, 2):
            raise ValueError(f"frame {frame}: invalid captured active bank {active_bank}")
        alternate_bank = 1 if active_bank == 2 else 2
        if (scores[active_bank]["matching_pixels"] <=
                scores[alternate_bank]["matching_pixels"]):
            raise ValueError(
                f"frame {frame}: tapped bank {active_bank} does not best match the screenshot")
        report.append({
            "frame": frame,
            "active_bank": active_bank,
            "active_score": scores[active_bank],
            "alternate_bank": alternate_bank,
            "alternate_score": scores[alternate_bank],
        })
    (OUTPUT_ROOT / "animation_bank_verification.json").write_text(
        json.dumps({"checks": report}, indent=2) + "\n", encoding="utf-8")


def contiguous_palette_runs(entries: list[dict[str, int]],
                            colour: int) -> list[list[dict[str, int]]]:
    """Split one CPS2 palette into object-list runs without guessing tile art."""
    runs: list[list[dict[str, int]]] = []
    for entry in sorted((item for item in entries if item["colour"] == colour),
                        key=lambda item: item["offset"]):
        if not runs or entry["offset"] != runs[-1][-1]["offset"] + 4:
            runs.append([])
        runs[-1].append(entry)
    return runs


def command_bounds(commands: list[dict[str, int]]) -> tuple[int, int, int, int]:
    return (
        min(entry["screen_x"] for entry in commands),
        min(entry["screen_y"] for entry in commands),
        max(entry["screen_x"] + entry["width"] for entry in commands),
        max(entry["screen_y"] + entry["height"] for entry in commands),
    )


def bounds_overlap(first: tuple[int, int, int, int],
                   second: tuple[int, int, int, int], margin: int = 0) -> bool:
    return not (
        first[2] + margin <= second[0] or
        second[2] + margin <= first[0] or
        first[3] + margin <= second[1] or
        second[3] + margin <= first[1])


def player_animation_commands(entries: list[dict[str, int]]) -> list[dict[str, int]]:
    """Select the established Predator assembly used by the dense route ledger."""
    return [
        entry for entry in entries
        if ((entry["colour"] == 0 and entry["tile_code"] < 7000 and
             entry["screen_y"] < 160) or
            (entry["colour"] == 7 and entry["tile_code"] >= 40000) or
            entry["colour"] == 15)
    ]


def isolated_player_animation_commands(
        entries: list[dict[str, int]]) -> list[dict[str, int]]:
    """Select one contiguous Predator assembly without absorbing nearby actors."""
    primary_candidates = []
    for run in contiguous_palette_runs(entries, 0):
        left, top, right, bottom = command_bounds(run)
        if (any(0 < entry["tile_code"] < 7000 for entry in run) and
                right - left <= 192 and bottom - top <= 192 and
                left < VISIBLE_WIDTH + 64 and right > -64 and
                top < VISIBLE_HEIGHT + 32 and bottom > 24):
            primary_candidates.append(run)
    if not primary_candidates:
        return []
    primary = max(
        primary_candidates,
        key=lambda run: (sum(entry["width"] * entry["height"] for entry in run),
                         -abs((command_bounds(run)[0] +
                               command_bounds(run)[2]) // 2 - VISIBLE_WIDTH // 2)))
    primary_bounds = command_bounds(primary)
    primary_last_offset = max(entry["offset"] for entry in primary)
    commands = list(primary)
    for run in contiguous_palette_runs(entries, 7):
        first_offset = min(entry["offset"] for entry in run)
        if ((primary_last_offset < first_offset <= primary_last_offset + 20) or
                bounds_overlap(primary_bounds, command_bounds(run), margin=24)):
            commands.extend(run)
    for run in contiguous_palette_runs(entries, 15):
        if bounds_overlap(primary_bounds, command_bounds(run), margin=96):
            commands.extend(run)
    return sorted(commands, key=lambda entry: entry["offset"])


def write_player_animation_timeline() -> None:
    """Deduplicate the dense active-bank samples into pivoted player poses."""
    samples = load_animation_sample_banks()
    expected_frames = list(range(2760, 4201, 4))
    if sorted(samples) != expected_frames:
        raise ValueError("animation capture must contain every four-frame sample from 2760 to 4200")

    poses: dict[str, dict[str, object]] = {}
    timeline = []
    for frame in expected_frames:
        entries = decode_object_entries(load_words(f"objram_active_{frame:04d}.tsv"))
        commands = player_animation_commands(entries)
        primary_commands = [entry for entry in commands if entry["colour"] == 0]
        if not primary_commands:
            raise ValueError(f"frame {frame}: incomplete Predator command assembly")
        primary = max(primary_commands,
                      key=lambda entry: entry["width"] * entry["height"])
        pivot_x = primary["screen_x"] + primary["width"] // 2
        pivot_y = primary["screen_y"] + primary["height"]
        normalized = [
            {
                "tile_code": entry["tile_code"],
                "attribute": entry["attribute"],
                "palette": entry["colour"],
                "priority": entry["priority"],
                "x": entry["screen_x"] - pivot_x,
                "y": entry["screen_y"] - pivot_y,
                "width": entry["width"],
                "height": entry["height"],
            }
            for entry in sorted(commands, key=lambda item: item["offset"], reverse=True)
        ]
        signature = json.dumps(normalized, separators=(",", ":"), sort_keys=True)
        pose_id = hashlib.sha256(signature.encode("ascii")).hexdigest()[:12]
        if pose_id not in poses:
            poses[pose_id] = {
                "id": pose_id,
                "first_frame": frame,
                "frames": [],
                "palettes": sorted({entry["colour"] for entry in commands}),
                "commands": normalized,
            }
        poses[pose_id]["frames"].append(frame)
        timeline.append({
            "frame": frame,
            "pose": pose_id,
            "pivot": [pivot_x, pivot_y],
            "command_offsets": sorted(entry["offset"] for entry in commands),
        })

    if not 50 <= len(poses) <= 120:
        raise ValueError(f"unexpected Predator pose count: {len(poses)}")
    runs = []
    for sample in timeline:
        if runs and runs[-1]["pose"] == sample["pose"]:
            runs[-1]["end_frame"] = sample["frame"]
            runs[-1]["samples"] += 1
        else:
            runs.append({
                "start_frame": sample["frame"],
                "end_frame": sample["frame"],
                "samples": 1,
                "pose": sample["pose"],
            })
    (OUTPUT_ROOT / "player_animation_timeline.json").write_text(
        json.dumps({
            "sample_stride_frames": 4,
            "sample_count": len(timeline),
            "unique_pose_count": len(poses),
            "poses": sorted(poses.values(), key=lambda pose: int(pose["first_frame"])),
            "timeline": timeline,
            "runs": runs,
        }, indent=2) + "\n", encoding="utf-8")


def write_stage1_encounter_observations() -> None:
    """Record reproducible evidence behind the native first-room wave script."""
    anchors = []
    for frame in STAGE1_ENCOUNTER_ANCHORS:
        object_path = CAPTURE_ROOT / f"objram_active_{frame:04d}.tsv"
        screenshot_path = CAPTURE_ROOT / f"stage1_sample_{frame:04d}.png"
        entries = decode_object_entries(load_words(object_path.name))
        palette_runs = []
        for colour in (16, 17, 18, 19):
            for run in contiguous_palette_runs(entries, colour):
                visible = [
                    entry for entry in run
                    if (entry["screen_x"] < VISIBLE_WIDTH and
                        entry["screen_x"] + entry["width"] > 0 and
                        entry["screen_y"] < VISIBLE_HEIGHT and
                        entry["screen_y"] + entry["height"] > 96)
                ]
                if not visible:
                    continue
                palette_runs.append({
                    "cps2_palette": colour,
                    "command_offsets": [entry["offset"] for entry in visible],
                    "visible_bounds": [
                        max(0, min(entry["screen_x"] for entry in visible)),
                        max(0, min(entry["screen_y"] for entry in visible)),
                        min(VISIBLE_WIDTH, max(
                            entry["screen_x"] + entry["width"] for entry in visible)),
                        min(VISIBLE_HEIGHT, max(
                            entry["screen_y"] + entry["height"] for entry in visible)),
                    ],
                })
        anchors.append({
            "frame": frame,
            "active_object_bank": load_animation_sample_banks()[frame],
            "object_ram_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
            "screenshot_sha256": hashlib.sha256(screenshot_path.read_bytes()).hexdigest(),
            "visible_enemy_palette_runs": palette_runs,
        })

    spawns = [
        {"slot": slot, "x": x, "lane": lane, "variant": variant,
         "cps2_palette": 16 + variant, "source_anchor": source_frame,
         "wave": 1 if slot < 5 else 2}
        for slot, (x, lane, variant, source_frame)
        in enumerate(STAGE1_SATURN_SPAWNS)
    ]
    (OUTPUT_ROOT / "stage1_encounter_observations.json").write_text(
        json.dumps({
            "capture_window": [2760, 4200],
            "sample_stride_frames": 4,
            "method": "active-bank object-list palette runs at hashed screenshot anchors",
            "saturn_wave_script": {
                "room_width": 384,
                "wave_one_slots": 5,
                "wave_two_slots": 3,
                "reinforcement_after_defeats": 3,
                "total_enemies": len(spawns),
                "spawns": spawns,
            },
            "anchors": anchors,
            "scope_note": (
                "Spawn composition and palette variants are capture-derived; "
                "arcade AI and exact spawn timing remain to be mapped."),
        }, indent=2) + "\n", encoding="utf-8")


def write_stage1_object_groups(entries: list[dict[str, int]]) -> None:
    """Emit exhaustive frame-local grouping metadata for animation extraction."""
    by_offset = {entry["offset"]: entry for entry in entries}
    grouped_offsets: set[int] = set()
    groups = []
    for name, role, confidence, offsets in STAGE1_OBJECT_GROUPS:
        overlap = grouped_offsets.intersection(offsets)
        if overlap:
            raise ValueError(f"duplicate Stage 1 group offsets: {sorted(overlap)}")
        missing = set(offsets).difference(by_offset)
        if missing:
            raise ValueError(f"{name}: missing object offsets {sorted(missing)}")
        grouped_offsets.update(offsets)
        commands = [by_offset[offset] for offset in offsets]
        left = min(command["screen_x"] for command in commands)
        top = min(command["screen_y"] for command in commands)
        right = max(command["screen_x"] + command["width"] for command in commands)
        bottom = max(command["screen_y"] + command["height"] for command in commands)
        visible_commands = [
            command for command in commands
            if (command["screen_x"] < VISIBLE_WIDTH and
                command["screen_x"] + command["width"] > 0 and
                command["screen_y"] < VISIBLE_HEIGHT and
                command["screen_y"] + command["height"] > 0)]
        if visible_commands:
            visible_bounds = [
                max(0, min(command["screen_x"] for command in visible_commands)),
                max(0, min(command["screen_y"] for command in visible_commands)),
                min(VISIBLE_WIDTH, max(command["screen_x"] + command["width"]
                                       for command in visible_commands)),
                min(VISIBLE_HEIGHT, max(command["screen_y"] + command["height"]
                                        for command in visible_commands)),
            ]
        else:
            visible_bounds = None
        groups.append({
            "name": name,
            "role": role,
            "confidence": confidence,
            "command_offsets": list(offsets),
            "cps2_palettes": sorted({command["colour"] for command in commands}),
            "cps2_priorities": sorted({(command["x"] >> 13) & 0x07
                                        for command in commands}),
            "source_bounds": [left, top, right, bottom],
            "visible_bounds": visible_bounds,
        })
    ungrouped = set(by_offset).difference(grouped_offsets)
    if ungrouped:
        raise ValueError(f"ungrouped Stage 1 object offsets: {sorted(ungrouped)}")
    (OUTPUT_ROOT / "stage1_object_groups.json").write_text(
        json.dumps({
            "capture_frame": 4200,
            "object_ram": STAGE1_ACTIVE_OBJECT_RAM,
            "grouping_scope": "frame-local; candidate groups require temporal confirmation",
            "groups": groups,
        }, indent=2) + "\n", encoding="utf-8")


def make_contact_sheet(layer: Image.Image, entries: list[dict[str, int]]) -> None:
    visible = [entry for entry in entries if entry["screen_x"] < VISIBLE_WIDTH and
               entry["screen_x"] + entry["width"] > 0 and entry["screen_y"] < VISIBLE_HEIGHT and
               entry["screen_y"] + entry["height"] > 0]
    sheet = Image.new("RGB", (768, 448), (25, 27, 31))
    sheet.paste(layer, (0, 0), layer)
    draw = ImageDraw.Draw(sheet)
    for entry in visible:
        x = entry["screen_x"]
        y = entry["screen_y"]
        draw.rectangle((x, y, x + entry["width"] - 1, y + entry["height"] - 1), outline=(255, 215, 0))
        draw.text((x + 1, y + 1), f"{entry['offset']//4:02x}", fill=(255, 255, 255))
    reference = Image.open(CAPTURE_ROOT / "stage1_4200.png").convert("RGB")
    sheet.paste(reference, (384, 0))
    sheet.save(OUTPUT_ROOT / "object_reference.png")


def selected_object_layer(gfx: bytearray, palette: list[tuple[int, int, int, int]],
                          frame: int, bank: int, offsets: list[int],
                          shift_x: int = 0) -> Image.Image:
    if frame == 4200:
        filename = f"objram{bank}.tsv"
    else:
        filename = animation_object_filename(frame, bank)
        palette = animation_palette(frame)
    source = load_words(filename)
    selected: list[int] = []
    for offset in sorted(offsets):
        command = source[offset:offset + 4]
        if len(command) != 4:
            raise ValueError(f"object command {offset} is missing from {filename}")
        if shift_x:
            command = command.copy()
            command[0] = (command[0] & ~0x3FF) | (((command[0] & 0x3FF) + shift_x) & 0x3FF)
        selected.extend(command)
    selected.extend((0, 0x8000, 0, 0xFF00))
    layer, _ = decode_objects(gfx, selected, palette)
    bounds = layer.getbbox()
    if not bounds:
        raise ValueError(f"selected object group from {filename} rendered empty")
    return layer.crop(bounds)


def fit_actor_frame(source: Image.Image, max_width: int = 176,
                    max_height: int = 176) -> Image.Image:
    scale = min(max_width / source.width, max_height / source.height)
    width = max(1, round(source.width * scale))
    height = max(1, round(source.height * scale))
    scaled = source.resize((width, height), Image.Resampling.NEAREST)
    frame = Image.new("RGBA", (192, 192), (0, 0, 0, 0))
    frame.alpha_composite(scaled, ((192 - width) // 2, 184 - height))
    return frame


def common_4bpp_palette(images: list[Image.Image]) -> list[tuple[int, int, int]]:
    opaque = []
    for image in images:
        pixels = image.load()
        opaque.extend(
            pixels[x, y][:3]
            for y in range(image.height)
            for x in range(image.width)
            if pixels[x, y][3] >= 128)
    if not opaque:
        raise ValueError("cannot build a palette from empty actor frames")
    sample = Image.new("RGB", (len(opaque), 1))
    sample.putdata(opaque)
    quantized = sample.quantize(colors=15, method=Image.Quantize.MEDIANCUT)
    raw_palette = quantized.getpalette()
    histogram = quantized.histogram()
    colour_count = max(index for index, count in enumerate(histogram) if count) + 1
    return [tuple(raw_palette[index * 3:index * 3 + 3]) for index in range(colour_count)]


def map_to_4bpp(image: Image.Image, palette: list[tuple[int, int, int]]) -> Image.Image:
    indexed = Image.new("P", image.size, 0)
    source = image.load()
    target = indexed.load()
    for y in range(image.height):
        for x in range(image.width):
            pixel = source[x, y]
            if pixel[3] < 128:
                continue
            rgb = pixel[:3]
            nearest = min(range(len(palette)),
                          key=lambda index: sum((rgb[channel] - palette[index][channel]) ** 2
                                                for channel in range(3)))
            target[x, y] = nearest + 1
    return indexed


def pack_4bpp(image: Image.Image) -> bytes:
    pixels = image.tobytes()
    output = bytearray()
    for index in range(0, len(pixels), 2):
        output.append((pixels[index] << 4) | pixels[index + 1])
    return bytes(output)


def player_pose_capture(frame: int) -> tuple[int, list[int], tuple[int, int]]:
    bank = load_animation_sample_banks()[frame]
    entries = decode_object_entries(load_words(animation_object_filename(frame, bank)))
    commands = player_animation_commands(entries)
    primary = max((entry for entry in commands if entry["colour"] == 0),
                  key=lambda entry: entry["width"] * entry["height"])
    pivot = (primary["screen_x"] + primary["width"] // 2,
             primary["screen_y"] + primary["height"])
    return bank, sorted(entry["offset"] for entry in commands), pivot


@lru_cache(maxsize=None)
def load_player_action_sample_banks(action: str) -> dict[int, int]:
    metadata = PLAYER_ACTION_ROOT / action / "samples.tsv"
    samples = {}
    for line in metadata.read_text(encoding="utf-8").splitlines()[1:]:
        if not line:
            continue
        frame, recorded_action, bank, _ = line.split("\t")
        if recorded_action != action:
            raise ValueError(
                f"{action}: action metadata contains {recorded_action!r}")
        samples[int(frame)] = int(bank)
    return samples


def isolated_player_pose_capture(
        action: str, frame: int) -> tuple[int, list[int], tuple[int, int], Path]:
    bank = load_player_action_sample_banks(action).get(frame)
    if bank not in (1, 2):
        raise ValueError(f"{action} frame {frame}: missing active object bank")
    object_path = PLAYER_ACTION_ROOT / action / f"objram_active_{frame:05d}.tsv"
    lines = object_path.read_text(encoding="utf-8").splitlines()[1:]
    words = [int(line.split("\t")[1], 16) for line in lines if line]
    entries = decode_object_entries(words)
    commands = isolated_player_animation_commands(entries)
    primary = max((entry for entry in commands if entry["colour"] == 0),
                  key=lambda entry: entry["width"] * entry["height"])
    pivot = (primary["screen_x"] + primary["width"] // 2,
             primary["screen_y"] + primary["height"])
    return bank, sorted(entry["offset"] for entry in commands), pivot, object_path


def rightmost_blue_alien_capture(
        frame: int) -> tuple[int, list[int], tuple[int, int]]:
    """Select the independently visible right-side blue alien temporal track."""
    bank = load_animation_sample_banks()[frame]
    entries = decode_object_entries(load_words(animation_object_filename(frame, bank)))
    candidates = []
    for run in contiguous_palette_runs(entries, 16):
        left = min(entry["screen_x"] for entry in run)
        top = min(entry["screen_y"] for entry in run)
        right = max(entry["screen_x"] + entry["width"] for entry in run)
        bottom = max(entry["screen_y"] + entry["height"] for entry in run)
        if (left < VISIBLE_WIDTH and right > 0 and top < VISIBLE_HEIGHT + 32 and
                bottom > 128 and right <= VISIBLE_WIDTH + 64):
            candidates.append((left, top, right, bottom, run))
    if not candidates:
        raise ValueError(f"frame {frame}: no independently visible blue alien run")
    left, top, right, bottom, commands = max(
        candidates, key=lambda item: (item[2], item[0]))
    primary = max(commands, key=lambda entry: entry["width"] * entry["height"])
    pivot = (primary["screen_x"] + primary["width"] // 2,
             primary["screen_y"] + primary["height"])
    return bank, [entry["offset"] for entry in commands], pivot


def exact_object_layers(gfx: bytearray, palette: list[tuple[int, int, int, int]],
                        frame: int, bank: int, offsets: list[int],
                        shift_x: int = 0,
                        pivot: tuple[int, int] | None = None,
                        source_filename: str | None = None,
                        canvas_size: tuple[int, int] = (192, 192)) -> tuple[dict[int, Image.Image],
                                                   dict[int, list[tuple[int, int, int]]]]:
    """Render selected CPS2 commands without scaling or palette quantisation."""
    if source_filename is not None:
        filename = source_filename
    elif frame == 4200:
        filename = f"objram{bank}.tsv"
    else:
        filename = animation_object_filename(frame, bank)
        palette = animation_palette(frame)
    words = load_words(filename)
    commands: list[dict[str, int]] = []
    for offset in offsets:
        x, y, code, attribute = words[offset:offset + 4]
        x = (x & ~0x3FF) | (((x & 0x3FF) + shift_x) & 0x3FF)
        nx = ((attribute >> 8) & 0x0F) + 1 if attribute & 0xFF00 else 1
        ny = ((attribute >> 12) & 0x0F) + 1 if attribute & 0xFF00 else 1
        commands.append({"offset": offset, "x": (x & 0x3FF) - VISIBLE_LEFT,
                         "y": (y & 0x3FF) - VISIBLE_TOP,
                         "raw_y": y, "code": code + ((y & 0x6000) << 3),
                         "attribute": attribute, "nx": nx, "ny": ny,
                         "colour": attribute & 0x1F})

    left = min(command["x"] for command in commands)
    top = min(command["y"] for command in commands)
    right = max(command["x"] + command["nx"] * 16 for command in commands)
    bottom = max(command["y"] + command["ny"] * 16 for command in commands)
    union_width = right - left
    union_height = bottom - top
    canvas_width, canvas_height = canvas_size
    if pivot is None:
        canvas_x = (canvas_width - union_width) // 2 - left
        canvas_y = canvas_height - 8 - bottom
    else:
        canvas_x = canvas_width // 2 - pivot[0]
        canvas_y = canvas_height - 8 - pivot[1]

    colours = sorted({command["colour"] for command in commands})
    layers = {colour: Image.new("P", canvas_size, 0) for colour in colours}
    palettes = {
        colour: [palette[colour * 16 + pen][:3] for pen in range(15)]
        for colour in colours
    }

    for command in sorted(commands, key=lambda entry: entry["offset"], reverse=True):
        attribute = command["attribute"]
        flip_x = bool(attribute & 0x20)
        flip_y = bool(attribute & 0x40)
        for tile_y in range(command["ny"]):
            for tile_x in range(command["nx"]):
                source_y = command["ny"] - 1 - tile_y if flip_y else tile_y
                source_x = command["nx"] - 1 - tile_x if flip_x else tile_x
                if not flip_x and not flip_y:
                    tile_code = ((command["code"] & ~0xF) +
                                 ((command["code"] + source_x) & 0xF) +
                                 0x10 * source_y)
                else:
                    tile_code = command["code"] + source_x + 0x10 * source_y
                source_tile = decode_tile(gfx, tile_code, 16)
                source_pixels = source_tile.load()
                target_pixels = layers[command["colour"]].load()
                target_x = canvas_x + command["x"] + tile_x * 16
                target_y = canvas_y + command["y"] + tile_y * 16
                for pixel_y in range(16):
                    for pixel_x in range(16):
                        pen = source_pixels[pixel_x, pixel_y]
                        if pen == 15:
                            continue
                        destination_x = target_x + (15 - pixel_x if flip_x else pixel_x)
                        destination_y = target_y + (15 - pixel_y if flip_y else pixel_y)
                        if (0 <= destination_x < canvas_width and
                                0 <= destination_y < canvas_height):
                            target_pixels[destination_x, destination_y] = pen + 1
    return layers, palettes


def write_exact_palette_header(palette_banks: list[list[tuple[int, int, int]]]) -> None:
    GENERATED_ROOT.mkdir(parents=True, exist_ok=True)
    padded_banks = []
    for bank in palette_banks:
        padded_banks.append(bank + [(0, 0, 0)] * (15 - len(bank)))
    bank_rows = []
    for bank in padded_banks:
        colours = ",\n".join(
            f"        {{{red}, {green}, {blue}}}" for red, green, blue in bank)
        bank_rows.append("    {\n" + colours + "\n    }")
    header = """/* Generated locally from exact CPS2 palette pens. */
#ifndef AVSP_PALETTE_H
#define AVSP_PALETTE_H
#define AVSP_EXACT_PALETTE_BANKS %d
static const unsigned char avsp_exact_palettes[AVSP_EXACT_PALETTE_BANKS][15][3] = {
%s
};
#endif
""" % (len(padded_banks), ",\n".join(bank_rows))
    (GENERATED_ROOT / "avsp_palette.h").write_text(header, encoding="ascii")


def write_snapshot_asset(layer: Image.Image, sprite_dir: Path) -> list[dict[str, object]]:
    """Write exact-crop and Saturn full-fit versions of the CPS2 object pass."""
    # Jo stores palette array entry 0 at CRAM bank + 1. Pixel index 0 remains
    # transparent, so visible pixel index N uses colours[N - 1].
    colour_to_index: dict[tuple[int, int, int], int] = {}
    colours: list[tuple[int, int, int]] = []
    data = bytearray(layer.width * layer.height)
    source = layer.load()

    for y in range(layer.height):
        for x in range(layer.width):
            red, green, blue, alpha = source[x, y]
            if not alpha:
                continue
            rgb = (red, green, blue)
            index = colour_to_index.get(rgb)
            if index is None:
                index = len(colours) + 1
                if index >= 256:
                    raise ValueError("captured CPS2 object pass exceeds one Saturn 8bpp palette")
                colour_to_index[rgb] = index
                colours.append(rgb)
            data[y * layer.width + x] = index

    padded = colours + [(0, 0, 0)] * (256 - len(colours))
    rows = ",\n".join(
        f"    {{{red}, {green}, {blue}}}" for red, green, blue in padded)
    header = f"""/* Generated locally from the captured CPS2 object pass. */
#ifndef AVSP_SNAPSHOT_PALETTE_H
#define AVSP_SNAPSHOT_PALETTE_H
#define AVSP_SNAPSHOT_PALETTE_COLOURS {len(colours)}
static const unsigned char avsp_snapshot_palette[256][3] = {{
{rows}
}};
#endif
"""
    (GENERATED_ROOT / "avsp_snapshot_palette.h").write_text(header, encoding="ascii")

    target = sprite_dir / "OBJFRM.BIN"
    target.write_bytes(data)
    fit_width = SATURN_VIEW_WIDTH
    if layer.width != VISIBLE_WIDTH or layer.height != VISIBLE_HEIGHT:
        raise ValueError("captured CPS2 object pass must be 384x224")
    fit_data = bytearray(fit_width * layer.height)
    for y in range(layer.height):
        for x in range(fit_width):
            # Align both endpoints so a full-fit sprite cannot discard the
            # CPS2 field's final source column through integer truncation.
            source_x = (
                x * (layer.width - 1) + (fit_width - 1) // 2
            ) // (fit_width - 1)
            fit_data[y * fit_width + x] = data[y * layer.width + source_x]
    fit_target = sprite_dir / "OBJFIT.BIN"
    fit_target.write_bytes(fit_data)
    return [
        {"path": "SPR8/OBJFRM.BIN", "bytes": len(data),
         "sha256": hashlib.sha256(data).hexdigest(),
         "visible_colours": len(colours), "display": "source-oracle"},
        {"path": "SPR8/OBJFIT.BIN", "bytes": len(fit_data),
         "sha256": hashlib.sha256(fit_data).hexdigest(),
         "visible_colours": len(colours), "display": "full-width-fit"},
    ]


def write_frontend_assets(sprite_dir: Path) -> list[dict[str, object]]:
    """Emit lossless full-fit menu and character-select capture surfaces."""
    scenes = (("MENUFIT.BIN", 1440), ("CHARFIT.BIN", 1800))
    palettes: list[list[tuple[int, int, int]]] = []
    manifest: list[dict[str, object]] = []

    for filename, frame in scenes:
        source_path = CAPTURE_ROOT / f"stage1_{frame:04d}.png"
        image = Image.open(source_path).convert("RGB")
        if image.size != (VISIBLE_WIDTH, VISIBLE_HEIGHT):
            raise ValueError(f"frontend frame {frame} must be 384x224")

        colours: list[tuple[int, int, int]] = []
        colour_to_index: dict[tuple[int, int, int], int] = {}
        source_data = bytearray(VISIBLE_WIDTH * VISIBLE_HEIGHT)
        for y in range(VISIBLE_HEIGHT):
            for x in range(VISIBLE_WIDTH):
                rgb = image.getpixel((x, y))
                index = colour_to_index.get(rgb)
                if index is None:
                    index = len(colours) + 1
                    if index >= 256:
                        raise ValueError(
                            f"frontend frame {frame} exceeds one Saturn 8bpp palette")
                    colour_to_index[rgb] = index
                    colours.append(rgb)
                source_data[y * VISIBLE_WIDTH + x] = index

        fit_data = bytearray(SATURN_VIEW_WIDTH * VISIBLE_HEIGHT)
        for y in range(VISIBLE_HEIGHT):
            for x in range(SATURN_VIEW_WIDTH):
                source_x = (
                    x * (VISIBLE_WIDTH - 1) + (SATURN_VIEW_WIDTH - 1) // 2
                ) // (SATURN_VIEW_WIDTH - 1)
                fit_data[y * SATURN_VIEW_WIDTH + x] = (
                    source_data[y * VISIBLE_WIDTH + source_x])

        target = sprite_dir / filename
        target.write_bytes(fit_data)
        palettes.append(colours + [(0, 0, 0)] * (256 - len(colours)))
        manifest.append({
            "path": f"SPR8/{filename}",
            "bytes": len(fit_data),
            "sha256": hashlib.sha256(fit_data).hexdigest(),
            "source_frame": frame,
            "visible_colours": len(colours),
            "display": "lossless-full-width-fit",
        })

    palette_scenes = []
    for palette in palettes:
        rows = ",\n".join(
            f"        {{{red}, {green}, {blue}}}" for red, green, blue in palette)
        palette_scenes.append("    {\n" + rows + "\n    }")
    filenames = ", ".join(f'"{filename}"' for filename, _ in scenes)
    header = f"""/* Generated from the cold-boot CPS2 frontend capture. */
#ifndef AVSP_FRONTEND_PALETTE_H
#define AVSP_FRONTEND_PALETTE_H
#define AVSP_FRONTEND_SCENES {len(scenes)}
static const char avsp_frontend_files[AVSP_FRONTEND_SCENES][12] = {{
    {filenames}
}};
static const unsigned char avsp_frontend_palettes[AVSP_FRONTEND_SCENES][256][3] = {{
{",\n".join(palette_scenes)}
}};
#endif
"""
    (GENERATED_ROOT / "avsp_frontend_palette.h").write_text(
        header, encoding="ascii")
    return manifest


def write_route_sequence_assets(sprite_dir: Path) -> list[dict[str, object]]:
    """Emit capture-exact key states for one replaceable VDP1 sequence slot."""
    scene_events = (
        ("R1TITLE.RLE", "round_1_title"),
        ("BARRIN.RLE", "barricade_intro"),
        ("WITHDRAW.RLE", "withdraw_dialogue"),
        ("BREACH.RLE", "barricade_breach"),
        ("DOORDLG.RLE", "door_dialogue"),
        ("INTERIOR.RLE", "interior_transition"),
        ("BOSSEND.RLE", "boss_death_explosion"),
        ("STCLEAR.RLE", "stage_clear"),
        ("RESULT1.RLE", "results_begin"),
        ("RESULT2.RLE", "results_complete"),
        ("RESEXIT.RLE", "results_exit"),
        ("INTERMS.RLE", "intermission"),
        ("R2TITLE.RLE", "round_2_boundary"),
    )
    ledger = json.loads((ROOT / "data" / "stage1_route.json").read_text(
        encoding="utf-8"))
    events = {event["id"]: event for event in ledger["events"]}
    capture_roots = {
        "opening": ROOT / ledger["capture"]["opening_root"],
        "continuation": ROOT / ledger["capture"]["continuation_root"],
    }
    palettes: list[list[tuple[int, int, int]]] = []
    byte_lengths: list[int] = []
    source_frames: list[int] = []
    manifest: list[dict[str, object]] = []

    for filename, event_id in scene_events:
        event = events[event_id]
        namespace, source_name = event["capture"].split(":", 1)
        source_path = capture_roots[namespace] / source_name
        image = Image.open(source_path).convert("RGB")
        if image.size != (VISIBLE_WIDTH, VISIBLE_HEIGHT):
            raise ValueError(f"route scene {event_id} must be 384x224")

        colours: list[tuple[int, int, int]] = []
        colour_to_index: dict[tuple[int, int, int], int] = {}
        fit_data = bytearray(SATURN_VIEW_WIDTH * VISIBLE_HEIGHT)
        for y in range(VISIBLE_HEIGHT):
            for x in range(SATURN_VIEW_WIDTH):
                source_x = (
                    x * (VISIBLE_WIDTH - 1) + (SATURN_VIEW_WIDTH - 1) // 2
                ) // (SATURN_VIEW_WIDTH - 1)
                rgb = image.getpixel((source_x, y))
                index = colour_to_index.get(rgb)
                if index is None:
                    index = len(colours) + 1
                    if index >= 256:
                        raise ValueError(
                            f"route scene {event_id} exceeds one Saturn 8bpp palette")
                    colour_to_index[rgb] = index
                    colours.append(rgb)
                fit_data[y * SATURN_VIEW_WIDTH + x] = index

        encoded = bytearray()
        run_value = fit_data[0]
        run_length = 0
        for value in fit_data:
            if value == run_value and run_length < 255:
                run_length += 1
            else:
                encoded.extend((run_length, run_value))
                run_value = value
                run_length = 1
        encoded.extend((run_length, run_value))

        target = sprite_dir / filename
        target.write_bytes(encoded)
        palettes.append(colours + [(0, 0, 0)] * (256 - len(colours)))
        byte_lengths.append(len(encoded))
        source_frames.append(event["frame"])
        manifest.append({
            "path": f"SPR8/{filename}",
            "bytes": len(encoded),
            "decoded_bytes": len(fit_data),
            "sha256": hashlib.sha256(encoded).hexdigest(),
            "source_frame": event["frame"],
            "route_event": event_id,
            "visible_colours": len(colours),
            "encoding": "rle8-count-value",
            "display": "lossless-full-width-fit",
        })

    palette_scenes = []
    for palette in palettes:
        rows = ",\n".join(
            f"        {{{red}, {green}, {blue}}}" for red, green, blue in palette)
        palette_scenes.append("    {\n" + rows + "\n    }")
    filenames = ", ".join(f'"{filename}"' for filename, _ in scene_events)
    lengths = ", ".join(str(length) for length in byte_lengths)
    frames = ", ".join(str(frame) for frame in source_frames)
    scene_constants = "\n".join(
        f"#define AVSP_SEQUENCE_{event_id.upper()} {index}"
        for index, (_, event_id) in enumerate(scene_events))
    header = f"""/* Generated from verified CPS2 Stage 1 route anchors. */
#ifndef AVSP_SEQUENCE_PALETTE_H
#define AVSP_SEQUENCE_PALETTE_H
#define AVSP_SEQUENCE_SCENES {len(scene_events)}
{scene_constants}
static const char avsp_sequence_files[AVSP_SEQUENCE_SCENES][13] = {{
    {filenames}
}};
static const unsigned int avsp_sequence_rle_bytes[AVSP_SEQUENCE_SCENES] = {{
    {lengths}
}};
static const unsigned int avsp_sequence_source_frames[AVSP_SEQUENCE_SCENES] = {{
    {frames}
}};
static const unsigned char avsp_sequence_palettes[AVSP_SEQUENCE_SCENES][256][3] = {{
{",\n".join(palette_scenes)}
}};
#endif
"""
    (GENERATED_ROOT / "avsp_sequence_palette.h").write_text(
        header, encoding="ascii")
    return manifest


def fit_background_for_saturn(stage: Image.Image) -> Image.Image:
    """Pre-scale a CPS2 background so VDP2 can display it at reliable 1:1."""
    expected_width = round(stage.width * SATURN_VIEW_WIDTH / VISIBLE_WIDTH)
    if expected_width != SATURN_FITTED_BACKGROUND_WIDTH:
        raise ValueError(
            f"unexpected fitted background width {expected_width}")
    fitted = stage.convert("RGB").resize(
        (expected_width, stage.height), Image.Resampling.NEAREST)
    canvas = Image.new("RGB", stage.size, (0, 0, 0))
    canvas.paste(fitted, (0, 0))
    return canvas


def rle_encode_bytes(data: bytes) -> bytes:
    encoded = bytearray()
    run_value = data[0]
    run_length = 0
    for value in data:
        if value == run_value and run_length < 255:
            run_length += 1
        else:
            encoded.extend((run_length, run_value))
            run_value = value
            run_length = 1
    encoded.extend((run_length, run_value))
    return bytes(encoded)


def rle_decode_bytes(data: bytes) -> bytes:
    if len(data) % 2:
        raise ValueError("count/value RLE payload has an odd byte count")
    decoded = bytearray()
    for offset in range(0, len(data), 2):
        count = data[offset]
        if count == 0:
            raise ValueError("count/value RLE payload contains a zero-length run")
        decoded.extend(bytes((data[offset + 1],)) * count)
    return bytes(decoded)


def write_player_action_sequence_assets(
        gfx: bytearray, sprite_dir: Path) -> list[dict[str, object]]:
    report_path = OUTPUT_ROOT / "player_action_probe.json"
    if not report_path.is_file():
        raise ValueError(
            "isolated player-action report is missing; run capture_player_actions.ps1")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    damage_report_path = OUTPUT_ROOT / "player_damage_probe.json"
    if not damage_report_path.is_file():
        raise ValueError(
            "natural player-damage report is missing; run capture_player_damage.ps1")
    damage_report = json.loads(damage_report_path.read_text(encoding="utf-8"))
    action_names = ("gun", "melee", "jump", "dash", "special", "walk")
    action_reports = {entry["action"]: entry for entry in report["actions"]}
    cps_colours = (0, 7, 15)
    base_palette = load_palette_path(
        PLAYER_ACTION_ROOT / "idle" / "palette_02525.tsv")
    base_palettes = {
        colour: [base_palette[colour * 16 + pen][:3] for pen in range(15)]
        for colour in cps_colours
    }

    pose_sources: dict[str, tuple[str, int]] = {}
    clip_specs: list[dict[str, object]] = []
    for action in action_names:
        action_report = action_reports[action]
        if not action_report["accepted"] or action_report["clip_frame_count"] <= 0:
            raise ValueError(f"{action}: isolated input was not accepted")
        runs = action_report["clip_runs"]
        if sum(int(run["samples"]) for run in runs) != int(
                action_report["clip_frame_count"]):
            raise ValueError(f"{action}: clip run durations do not cover the clip")
        total_frames = int(action_report["clip_frame_count"])
        clip_specs.append({
            "name": action,
            "source_action": action,
            "runs": runs,
            "total_frames": total_frames,
            "frame_offsets": [[0, 0] for _ in range(total_frames)],
        })
        for run in runs:
            pose_sources.setdefault(str(run["pose"]),
                                    (action, int(run["start_frame"])))

    damage_clips = {entry["name"]: entry for entry in damage_report["clips"]}
    for clip_name in ("hit", "ko"):
        damage_clip = damage_clips[clip_name]
        runs = damage_clip["runs"]
        total_frames = int(damage_clip["frame_count"])
        frame_offsets = damage_clip["frame_offsets"]
        if sum(int(run["samples"]) for run in runs) != total_frames:
            raise ValueError(f"{clip_name}: damage runs do not cover the clip")
        if len(frame_offsets) != total_frames:
            raise ValueError(f"{clip_name}: damage offsets do not cover the clip")
        clip_specs.append({
            "name": clip_name,
            "source_action": "damage",
            "runs": runs,
            "total_frames": total_frames,
            "frame_offsets": frame_offsets,
        })
        for run in runs:
            pose_sources.setdefault(str(run["pose"]),
                                    ("damage", int(run["start_frame"])))

    pose_ids = list(pose_sources)
    if len(pose_ids) >= 256:
        raise ValueError("isolated player actions exceed 8-bit pose indices")
    pose_indices = {pose_id: index for index, pose_id in enumerate(pose_ids)}
    archive = bytearray()
    archive_offsets: list[list[int]] = []
    compressed_lengths: list[list[int]] = []
    source_frames: list[int] = []
    manifest: list[dict[str, object]] = []
    for pose_index, pose_id in enumerate(pose_ids):
        action, frame = pose_sources[pose_id]
        bank, offsets, pivot, object_path = isolated_player_pose_capture(
            action, frame)
        palette = load_palette_path(
            PLAYER_ACTION_ROOT / action / f"palette_{frame:05d}.tsv")
        layers, palettes = exact_object_layers(
            gfx, palette, frame, bank, offsets, pivot=pivot,
            source_filename=str(object_path))
        pose_offsets = []
        pose_lengths = []
        for layer_index, colour in enumerate(cps_colours):
            if colour in palettes and palettes[colour] != base_palettes[colour]:
                raise ValueError(
                    f"{action} frame {frame}: CPS2 player palette {colour} changed")
            layer = layers.get(colour, Image.new("P", (192, 192), 0))
            decoded = pack_4bpp(layer)
            encoded = rle_encode_bytes(decoded)
            if rle_decode_bytes(encoded) != decoded:
                raise ValueError(
                    f"{action} frame {frame}: player action RLE round trip failed")
            pose_offsets.append(len(archive))
            archive.extend(encoded)
            pose_lengths.append(len(encoded))
        archive_offsets.append(pose_offsets)
        compressed_lengths.append(pose_lengths)
        source_frames.append(frame)

    archive_filename = "PACT.RLE"
    (sprite_dir / archive_filename).write_bytes(archive)
    manifest.append({
        "path": f"SPR4/{archive_filename}",
        "bytes": len(archive),
        "decoded_bytes": len(pose_ids) * len(cps_colours) * (192 * 192) // 2,
        "sha256": hashlib.sha256(archive).hexdigest(),
        "components": len(pose_ids) * len(cps_colours),
        "encoding": "indexed-rle8-count-value",
    })

    max_steps = max(len(clip["runs"]) for clip in clip_specs)
    max_frames = max(int(clip["total_frames"]) for clip in clip_specs)
    offset_rows = ",\n".join(
        "    {" + ", ".join(str(offset) for offset in pose_offsets) + "}"
        for pose_offsets in archive_offsets)
    length_rows = ",\n".join(
        "    {" + ", ".join(str(length) for length in lengths) + "}"
        for lengths in compressed_lengths)
    count_rows = ", ".join(str(len(clip["runs"])) for clip in clip_specs)
    total_rows = ", ".join(str(clip["total_frames"]) for clip in clip_specs)
    pose_rows = []
    duration_rows = []
    frame_x_rows = []
    frame_y_rows = []
    for clip in clip_specs:
        runs = clip["runs"]
        pose_values = [pose_indices[str(run["pose"])] for run in runs]
        duration_values = [int(run["samples"]) for run in runs]
        pose_values.extend([0] * (max_steps - len(pose_values)))
        duration_values.extend([0] * (max_steps - len(duration_values)))
        pose_rows.append("    {" + ", ".join(map(str, pose_values)) + "}")
        duration_rows.append("    {" + ", ".join(map(str, duration_values)) + "}")
        frame_offsets = clip["frame_offsets"]
        x_values = [int(offset[0]) for offset in frame_offsets]
        y_values = [int(offset[1]) for offset in frame_offsets]
        x_values.extend([0] * (max_frames - len(x_values)))
        y_values.extend([0] * (max_frames - len(y_values)))
        frame_x_rows.append("    {" + ", ".join(map(str, x_values)) + "}")
        frame_y_rows.append("    {" + ", ".join(map(str, y_values)) + "}")
    frame_rows = ", ".join(str(frame) for frame in source_frames)
    action_constants = "\n".join(
        f"#define AVSP_PLAYER_CLIP_{str(clip['name']).upper()} {index}"
        for index, clip in enumerate(clip_specs))
    header = f"""/* Generated from deterministic isolated CPS2 player actions. */
#ifndef AVSP_PLAYER_ACTION_ANIMATION_H
#define AVSP_PLAYER_ACTION_ANIMATION_H
#define AVSP_PLAYER_ACTION_CLIPS {len(clip_specs)}
#define AVSP_PLAYER_ACTION_LAYERS {len(cps_colours)}
#define AVSP_PLAYER_ACTION_POSES {len(pose_ids)}
#define AVSP_PLAYER_ACTION_MAX_STEPS {max_steps}
#define AVSP_PLAYER_ACTION_MAX_FRAMES {max_frames}
#define AVSP_PLAYER_ACTION_DECODED_BYTES {(192 * 192) // 2}
#define AVSP_PLAYER_ACTION_ARCHIVE_FILE "{archive_filename}"
#define AVSP_PLAYER_ACTION_ARCHIVE_BYTES {len(archive)}
{action_constants}
static const unsigned int avsp_player_action_rle_offsets[AVSP_PLAYER_ACTION_POSES][AVSP_PLAYER_ACTION_LAYERS] = {{
{offset_rows}
}};
static const unsigned short avsp_player_action_rle_bytes[AVSP_PLAYER_ACTION_POSES][AVSP_PLAYER_ACTION_LAYERS] = {{
{length_rows}
}};
static const unsigned char avsp_player_action_step_counts[AVSP_PLAYER_ACTION_CLIPS] = {{
    {count_rows}
}};
static const unsigned char avsp_player_action_total_frames[AVSP_PLAYER_ACTION_CLIPS] = {{
    {total_rows}
}};
static const unsigned char avsp_player_action_step_poses[AVSP_PLAYER_ACTION_CLIPS][AVSP_PLAYER_ACTION_MAX_STEPS] = {{
{",\n".join(pose_rows)}
}};
static const unsigned char avsp_player_action_step_durations[AVSP_PLAYER_ACTION_CLIPS][AVSP_PLAYER_ACTION_MAX_STEPS] = {{
{",\n".join(duration_rows)}
}};
static const signed short avsp_player_action_frame_x[AVSP_PLAYER_ACTION_CLIPS][AVSP_PLAYER_ACTION_MAX_FRAMES] = {{
{",\n".join(frame_x_rows)}
}};
static const signed short avsp_player_action_frame_y[AVSP_PLAYER_ACTION_CLIPS][AVSP_PLAYER_ACTION_MAX_FRAMES] = {{
{",\n".join(frame_y_rows)}
}};
static const unsigned short avsp_player_action_source_frames[AVSP_PLAYER_ACTION_POSES] = {{
    {frame_rows}
}};
#endif
"""
    (GENERATED_ROOT / "avsp_player_action_animation.h").write_text(
        header, encoding="ascii")
    return manifest


def write_enemy_walk_sequence_assets(
        gfx: bytearray, sprite_dir: Path) -> list[dict[str, object]]:
    source_frames = list(range(4164, 4201, 4))
    base_palette = [
        animation_palette(source_frames[0])[16 * 16 + pen][:3]
        for pen in range(15)
    ]
    files = []
    manifest = []
    for pose_index, frame in enumerate(source_frames):
        bank, offsets, pivot = rightmost_blue_alien_capture(frame)
        layers, palettes = exact_object_layers(
            gfx, animation_palette(frame), frame, bank, offsets, pivot=pivot)
        if 16 not in layers or palettes[16] != base_palette:
            raise ValueError(f"frame {frame}: blue alien palette 16 changed")
        filename = f"EA{pose_index:02d}.BIN"
        data = pack_4bpp(layers[16])
        (sprite_dir / filename).write_bytes(data)
        files.append(filename)
        manifest.append({
            "path": f"SPR4/{filename}",
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "source_frame": frame,
            "cps2_palette": 16,
        })

    file_rows = ",\n".join(f'    "{filename}"' for filename in files)
    frame_rows = ", ".join(str(frame) for frame in source_frames)
    header = f"""/* Generated from a temporally tracked CPS2 blue alien. */
#ifndef AVSP_ENEMY_ANIMATION_H
#define AVSP_ENEMY_ANIMATION_H
#define AVSP_ENEMY_WALK_POSES {len(source_frames)}
static const char avsp_enemy_walk_files[AVSP_ENEMY_WALK_POSES][12] = {{
{file_rows}
}};
static const unsigned short avsp_enemy_walk_source_frames[AVSP_ENEMY_WALK_POSES] = {{
    {frame_rows}
}};
#endif
"""
    (GENERATED_ROOT / "avsp_enemy_animation.h").write_text(
        header, encoding="ascii")
    return manifest


def write_boss_idle_assets(gfx: bytearray,
                           sprite_dir: Path) -> list[dict[str, object]]:
    """Emit the complete multi-palette Chrysalis-room boss assembly."""
    bank = int((CAPTURE_ROOT / "boss_active_object_bank.txt").read_text(
        encoding="ascii").strip())
    offsets = [36, 40, 44]
    palette = load_palette("boss_palette.tsv")
    layers, palettes = exact_object_layers(
        gfx, palette, 12660, bank, offsets, pivot=(74, 211),
        source_filename=f"boss_objram{bank}.tsv", canvas_size=(256, 192))
    cps_colours = (27,)
    files = []
    manifest = []
    for layer_index, colour in enumerate(cps_colours):
        layer = layers.get(colour)
        if layer is None:
            raise ValueError(f"boss capture is missing CPS2 palette {colour}")
        filename = f"BI{layer_index}.BIN"
        data = pack_4bpp(layer)
        (sprite_dir / filename).write_bytes(data)
        files.append(filename)
        manifest.append({
            "path": f"SPR4/{filename}",
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "source_frame": 12660,
            "cps2_palette": colour,
        })
    header = f"""/* Generated from the Stage 1 Chrysalis-room CPS2 capture. */
#ifndef AVSP_BOSS_ANIMATION_H
#define AVSP_BOSS_ANIMATION_H
#define AVSP_BOSS_IDLE_LAYERS {len(files)}
#define AVSP_BOSS_CEL_WIDTH 256
#define AVSP_BOSS_CEL_HEIGHT 192
static const char avsp_boss_idle_files[AVSP_BOSS_IDLE_LAYERS][12] = {{
    {", ".join(f'\"{filename}\"' for filename in files)}
}};
static const unsigned char avsp_boss_idle_palette_banks[AVSP_BOSS_IDLE_LAYERS] = {{
    7
}};
#endif
"""
    (GENERATED_ROOT / "avsp_boss_animation.h").write_text(
        header, encoding="ascii")
    return manifest


def write_exact_actor_assets(gfx: bytearray,
                             palette: list[tuple[int, int, int, int]],
                             sprite_dir: Path) -> list[dict[str, object]]:
    idle_bank, idle_offsets, idle_pivot, idle_object_path = (
        isolated_player_pose_capture("idle", 2525))
    isolated_idle_palette = load_palette_path(
        PLAYER_ACTION_ROOT / "idle" / "palette_02525.tsv")
    groups = {
        "player_idle": exact_object_layers(
            gfx, isolated_idle_palette, 2525, idle_bank, idle_offsets,
            pivot=idle_pivot, source_filename=str(idle_object_path)),
    }
    # Fixed Saturn subpalette slots. Player layers retain CPS2 palettes 0, 7,
    # and 15; the four Stage 1 alien variants retain palettes 16-19, and the
    # Chrysalis-room boss adds CPS2 palette 27.
    cps_colours = (0, 7, 15, 16, 17, 18, 19, 27)
    player_palette = isolated_idle_palette
    enemy_palette = animation_palette(2760)
    enemy_palette_anchors = (3000, 3240, 3480, 3720, 3960, 4200)
    for frame in enemy_palette_anchors:
        candidate = animation_palette(frame)
        for colour in (16, 17, 18, 19):
            if ([candidate[colour * 16 + pen][:3] for pen in range(15)] !=
                    [enemy_palette[colour * 16 + pen][:3] for pen in range(15)]):
                raise ValueError(
                    f"frame {frame}: Stage 1 enemy palette {colour} changed")
    palette_banks = {
        0: [player_palette[pen][:3] for pen in range(15)],
        7: [player_palette[7 * 16 + pen][:3] for pen in range(15)],
        15: [player_palette[15 * 16 + pen][:3] for pen in range(15)],
    }
    for colour in (16, 17, 18, 19):
        palette_banks[colour] = [
            enemy_palette[colour * 16 + pen][:3] for pen in range(15)]
    boss_palette = load_palette("boss_palette.tsv")
    palette_banks[27] = [
        boss_palette[27 * 16 + pen][:3] for pen in range(15)]
    write_exact_palette_header([palette_banks[colour] for colour in cps_colours])

    file_map = {
        "PXI0.BIN": ("player_idle", 0),
        "PXI1.BIN": ("player_idle", 7),
    }
    manifest = []
    preview = Image.new("RGBA", (384, 384), (20, 20, 20, 255))
    preview_groups = (("player_idle", 0),)
    for group_name, preview_y in preview_groups:
        layers, group_palettes = groups[group_name]
        for colour, layer in layers.items():
            rgb_palette = [(0, 0, 0)] + group_palettes[colour]
            rgba = Image.new("RGBA", layer.size, (0, 0, 0, 0))
            for y in range(layer.height):
                for x in range(layer.width):
                    index = layer.getpixel((x, y))
                    if index:
                        rgba.putpixel((x, y), (*rgb_palette[index], 255))
            preview.alpha_composite(rgba, (96, preview_y))
    preview.save(OUTPUT_ROOT / "exact_actor_preview.png")

    for filename, (group_name, colour) in file_map.items():
        layer = groups[group_name][0].get(colour)
        if layer is None:
            raise ValueError(f"{group_name} has no CPS2 palette {colour}")
        data = pack_4bpp(layer)
        target = sprite_dir / filename
        target.write_bytes(data)
        manifest.append({"path": f"SPR4/{filename}", "bytes": len(data),
                         "sha256": hashlib.sha256(data).hexdigest(),
                         "cps2_palette": colour})
    manifest.extend(write_player_action_sequence_assets(gfx, sprite_dir))
    manifest.extend(write_enemy_walk_sequence_assets(gfx, sprite_dir))
    manifest.extend(write_boss_idle_assets(gfx, sprite_dir))
    return manifest


def write_palette_header(player: list[tuple[int, int, int]],
                         alien: list[tuple[int, int, int]]) -> None:
    GENERATED_ROOT.mkdir(parents=True, exist_ok=True)

    def rows(colours: list[tuple[int, int, int]]) -> str:
        padded = colours + [(0, 0, 0)] * (15 - len(colours))
        return ",\n".join(f"    {{{red}, {green}, {blue}}}" for red, green, blue in padded)

    header = f"""/* Generated locally from the verified avspu graphics ROMs. */
#ifndef AVSP_PALETTE_H
#define AVSP_PALETTE_H
static const unsigned char avsp_player_palette[15][3] = {{
{rows(player)}
}};
static const unsigned char avsp_alien_palette[15][3] = {{
{rows(alien)}
}};
#endif
"""
    (GENERATED_ROOT / "avsp_palette.h").write_text(header, encoding="ascii")


def write_saturn_assets(gfx: bytearray, palette: list[tuple[int, int, int, int]],
                        gfxram: list[int], cps_a: list[int], cps_b: list[int],
                        object_layer: Image.Image) -> None:
    sprite_dir = SATURN_CD_ROOT / "SPR4"
    snapshot_dir = SATURN_CD_ROOT / "SPR8"
    background_dir = SATURN_CD_ROOT / "BG"
    sprite_dir.mkdir(parents=True, exist_ok=True)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    background_dir.mkdir(parents=True, exist_ok=True)

    # These directories are generated and ignored. Remove only their direct
    # files so stale approximate assets cannot leak into a clean image pack.
    for output_dir in (sprite_dir, snapshot_dir, background_dir):
        for stale_file in output_dir.iterdir():
            if stale_file.is_file():
                stale_file.unlink()

    manifest: list[dict[str, object]] = []

    manifest.extend(write_exact_actor_assets(gfx, palette, sprite_dir))
    manifest.extend(write_frontend_assets(snapshot_dir))
    manifest.extend(write_route_sequence_assets(snapshot_dir))
    manifest.extend(write_snapshot_asset(object_layer, snapshot_dir))

    stage = render_background(gfx, gfxram, cps_a, cps_b, palette,
                              width=512, height=256, include_scroll1=True)
    stage.save(OUTPUT_ROOT / "stage1_saturn_source_background.png")
    stage = fit_background_for_saturn(stage)
    stage.save(OUTPUT_ROOT / "stage1_saturn_background.png")
    stage = stage.quantize(colors=256, method=Image.Quantize.MAXCOVERAGE)
    background_target = background_dir / "CORRIDOR.TGA"
    stage.save(background_target, format="TGA", compression=None)
    background_data = background_target.read_bytes()
    manifest.append({"path": "BG/CORRIDOR.TGA", "bytes": len(background_data),
                     "sha256": hashlib.sha256(background_data).hexdigest(),
                     "content_width": SATURN_FITTED_BACKGROUND_WIDTH,
                     "display": "full-width-fit-at-1:1"})

    boss_stage = render_background(
        gfx, load_words("boss_gfxram.tsv"), load_words("boss_cps_a_regs.tsv"),
        load_words("boss_cps_b_regs.tsv"), load_palette("boss_palette.tsv"),
        width=512, height=256, include_scroll1=True)
    boss_stage.save(OUTPUT_ROOT / "stage1_boss_source_background.png")
    boss_stage = fit_background_for_saturn(boss_stage)
    boss_stage.save(OUTPUT_ROOT / "stage1_boss_background.png")
    boss_stage = boss_stage.quantize(
        colors=256, method=Image.Quantize.MAXCOVERAGE)
    boss_background_target = background_dir / "BOSSROOM.TGA"
    boss_stage.save(boss_background_target, format="TGA", compression=None)
    boss_background_data = boss_background_target.read_bytes()
    manifest.append({
        "path": "BG/BOSSROOM.TGA", "bytes": len(boss_background_data),
        "sha256": hashlib.sha256(boss_background_data).hexdigest(),
        "source_frame": 12660,
        "content_width": SATURN_FITTED_BACKGROUND_WIDTH,
        "display": "full-width-fit-at-1:1",
    })

    manifest_path = OUTPUT_ROOT / "saturn_asset_manifest.json"
    manifest_path.write_text(json.dumps({
        "source_set": "avspu",
        "source_capture_frame": 4200,
        "distribution": "private local capability test only",
        "assets": sorted(manifest, key=lambda entry: str(entry["path"])),
    }, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    verify_roms()
    gfx = load_gfx_region()
    verify_loaded_gfx_region(gfx)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    for legacy_player_header in (
            GENERATED_ROOT / "avsp_player_animation.h",
            GENERATED_ROOT / "avsp_player_shoot_animation.h"):
        if legacy_player_header.is_file():
            legacy_player_header.unlink()
    verify_animation_bank_alignment(gfx)
    write_player_animation_timeline()
    write_stage1_encounter_observations()
    palette = load_palette()
    gfxram = load_words("gfxram.tsv")
    cps_a = load_words("cps_a_regs.tsv")
    cps_b = load_words("cps_b_regs.tsv")
    background = render_background(gfx, gfxram, cps_a, cps_b, palette)
    words = load_words(STAGE1_ACTIVE_OBJECT_RAM)
    layer, entries = decode_objects(gfx, words, palette)
    verify_stage1_object_capture(entries)
    saturn_layer = final_visible_object_surface(background, layer)
    background.save(OUTPUT_ROOT / "stage1_background.png")
    composite = background.copy()
    composite.alpha_composite(layer)
    composite.save(OUTPUT_ROOT / "stage1_reconstructed.png")
    write_saturn_assets(gfx, palette, gfxram, cps_a, cps_b, saturn_layer)
    saturn_layer.save(OUTPUT_ROOT / "stage1_saturn_visible_objects.png")
    layer.save(OUTPUT_ROOT / "stage1_objects.png")
    (OUTPUT_ROOT / "stage1_objects.json").write_text(
        json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    write_stage1_object_groups(entries)
    make_contact_sheet(layer, entries)
    print(f"Decoded {len(entries)} CPS2 object commands to {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
