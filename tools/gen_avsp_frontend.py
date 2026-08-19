"""Generate deterministic Saturn frontend assets from AvP ROM structures.

The source is the reconstructed graphics ROM plus captured CPS register,
tilemap, object-list and palette state.  Screenshots are comparison oracles
only.  Generated pixels remain ignored; the tracked manifest contains hashes,
geometry, palette maps, object commands and memory totals.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from extract_avspu_stage1 import (  # noqa: E402
    decode_object_entries,
    decode_objects,
    decode_tile,
    load_gfx_region,
    render_background,
    verify_roms,
)

FRONTEND_ROM = ROOT / ".deps" / "mame" / "frontend_rom"
INTERACTION = ROOT / ".deps" / "mame" / "frontend_interaction" / "topology"
OUTPUT_DIR = ROOT / "build" / "avsp_cd" / "FRONT"
MANIFEST = ROOT / "data" / "avsp_frontend_assets.json"
RUNTIME_HEADER = ROOT / "generated" / "avsp_frontend.h"
WIDTH = 352
HEIGHT = 224
BUNDLE_BUDGET = 78848


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    return sha256(path.read_bytes())


def load_words(path: Path) -> list[int]:
    result = []
    for line in path.read_text(encoding="ascii").splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2:
            result.append(int(parts[1], 16))
    return result


def load_palette(path: Path) -> list[tuple[int, int, int, int]]:
    result = []
    for line in path.read_text(encoding="ascii").splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2:
            argb = int(parts[1], 16)
            result.append(((argb >> 16) & 255, (argb >> 8) & 255,
                           argb & 255, 255))
    return result


def fit(image: Image.Image) -> Image.Image:
    if image.size != (384, 224):
        raise ValueError(f"frontend source is {image.size}, expected 384x224")
    source = image.convert("RGBA")
    output = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    src = source.load()
    dst = output.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            source_x = (x * 383 + 175) // 351
            dst[x, y] = src[source_x, y]
    return output


def rgb555(rgb: tuple[int, int, int]) -> int:
    red, green, blue = rgb
    return 0x8000 | ((blue >> 3) << 10) | ((green >> 3) << 5) | (red >> 3)


def rgb555_to_rgb(value: int) -> tuple[int, int, int]:
    red = value & 31
    green = (value >> 5) & 31
    blue = (value >> 10) & 31
    return ((red << 3) | (red >> 2),
            (green << 3) | (green >> 2),
            (blue << 3) | (blue >> 2))


def index_surface(image: Image.Image, transparent: bool) -> tuple[bytes, bytes, int, int]:
    rgba = image.convert("RGBA")
    colours: list[tuple[int, int, int]] = []
    indices: dict[tuple[int, int, int], int] = {}
    pixels = bytearray(WIDTH * HEIGHT)
    first_index = 1 if transparent else 0
    for y in range(HEIGHT):
        for x in range(WIDTH):
            r, g, b, a = rgba.getpixel((x, y))
            if transparent and a == 0:
                index = 0
            else:
                rgb = (r, g, b)
                index = indices.get(rgb, -1)
                if index < 0:
                    index = first_index + len(colours)
                    if index >= 256:
                        raise ValueError("frontend surface exceeds one exact 8bpp palette")
                    indices[rgb] = index
                    colours.append(rgb)
            pixels[y * WIDTH + x] = index
    palette = [0] * 256
    changed_colours = 0
    for rgb, index in indices.items():
        palette[index] = rgb555(rgb)
        if rgb555_to_rgb(palette[index]) != rgb:
            changed_colours += 1
    palette_bytes = b"".join(struct.pack(">H", value) for value in palette)
    return bytes(pixels), palette_bytes, len(colours), changed_colours


def rle_encode(data: bytes) -> bytes:
    if not data:
        return b""
    output = bytearray()
    value = data[0]
    count = 1
    for next_value in data[1:]:
        if next_value == value and count < 255:
            count += 1
        else:
            output.extend((count, value))
            value = next_value
            count = 1
    output.extend((count, value))
    return bytes(output)


def rle_decode(data: bytes) -> bytes:
    if len(data) & 1:
        raise ValueError("odd frontend RLE length")
    output = bytearray()
    for offset in range(0, len(data), 2):
        output.extend([data[offset + 1]] * data[offset])
    return bytes(output)


def frame_state(root: Path, frame: int, object_name: str) -> dict[str, object]:
    return {
        "gfxram": load_words(root / f"gfxram_{frame:04d}.tsv"),
        "cps_a": load_words(root / f"cps_a_regs_{frame:04d}.tsv"),
        "cps_b": load_words(root / f"cps_b_regs_{frame:04d}.tsv"),
        "palette": load_palette(root / f"palette_{frame:04d}.tsv"),
        "objects": load_words(root / object_name),
        "reference": Image.open(root / f"reference_{frame:04d}.png").convert("RGBA"),
    }


def render_layers(gfx: bytearray, state: dict[str, object], layers: tuple[int, ...],
                  transparent: bool) -> Image.Image:
    return render_background(
        gfx, state["gfxram"], state["cps_a"], state["cps_b"], state["palette"],
        layer_filter=layers, transparent_background=transparent)


def compare(name: str, actual: Image.Image, reference: Image.Image) -> int:
    a = actual.convert("RGB")
    b = reference.convert("RGB")
    if a.size != b.size:
        raise ValueError(f"{name}: comparison dimensions differ")
    differing = [
        (index % a.width, index // a.width, left, right)
        for index, (left, right) in enumerate(
            zip(a.get_flattened_data(), b.get_flattened_data()))
        if left != right
    ]
    differences = len(differing)
    if differences:
        xs = [item[0] for item in differing]
        ys = [item[1] for item in differing]
        samples = differing[:8]
        raise ValueError(
            f"{name}: {differences} pixels differ from ROM-state oracle; "
            f"bounds=({min(xs)},{min(ys)})-({max(xs)},{max(ys)}); "
            f"samples={samples}"
        )
    return differences


def pack_object_cel(gfx: bytearray, entry: dict[str, int]) -> bytes:
    nx = entry["width"] // 16
    ny = entry["height"] // 16
    code = entry["tile_code"]
    flip_x = bool(entry["attribute"] & 0x20)
    flip_y = bool(entry["attribute"] & 0x40)
    pixels = bytearray(entry["width"] * entry["height"])
    for tile_y in range(ny):
        for tile_x in range(nx):
            source_y = ny - 1 - tile_y if flip_y else tile_y
            source_x = nx - 1 - tile_x if flip_x else tile_x
            if not flip_x and not flip_y:
                tile_code = ((code & ~0xF) + ((code + source_x) & 0xF)
                             + 0x10 * source_y)
            else:
                tile_code = code + source_x + 0x10 * source_y
            tile = decode_tile(gfx, tile_code, 16)
            for y in range(16):
                for x in range(16):
                    sx = 15 - x if flip_x else x
                    sy = 15 - y if flip_y else y
                    pen = tile.getpixel((sx, sy))
                    pixels[(tile_y * 16 + y) * entry["width"] + tile_x * 16 + x] = (
                        0 if pen == 15 else pen + 1)
    packed = bytearray((len(pixels) + 1) // 2)
    for index, pen in enumerate(pixels):
        if index & 1:
            packed[index // 2] |= pen
        else:
            packed[index // 2] = pen << 4
    return bytes(packed)


def object_palette(palette: list[tuple[int, int, int, int]],
                   bank: int) -> tuple[bytes, int]:
    # CPS pen 15 is transparent. Saturn 4bpp transparency is index zero, so
    # visible source pens 0..14 are shifted to indices 1..15 by pack_object_cel.
    source_colours = [palette[bank * 16 + pen][:3] for pen in range(15)]
    values = [0] + [rgb555(colour) for colour in source_colours]
    changed = sum(rgb555_to_rgb(value) != colour
                  for value, colour in zip(values[1:], source_colours))
    return b"".join(struct.pack(">H", value) for value in values), changed


def object_command(entry: dict[str, int], asset: str) -> dict[str, object]:
    centre_x = entry["screen_x"] + entry["width"] // 2
    return {
        "asset": asset,
        "source_slot_word": entry["offset"],
        "source_x": entry["screen_x"],
        "source_y": entry["screen_y"],
        "source_width": entry["width"],
        "source_height": entry["height"],
        "saturn_centre_x": (centre_x * WIDTH) // 384 - WIDTH // 2,
        "saturn_centre_y": entry["screen_y"] + entry["height"] // 2 - HEIGHT // 2,
        "saturn_scale_x_numerator": WIDTH,
        "saturn_scale_x_denominator": 384,
        "palette_bank": entry["colour"],
    }


def asset_record(path: str, data: bytes, kind: str, **extra: object) -> dict[str, object]:
    return {"path": path, "kind": kind, "bytes": len(data),
            "sha256": sha256(data), **extra}


def runtime_header(manifest: dict[str, object]) -> bytes:
    assets = {str(asset["path"]): asset for asset in manifest["assets"]}
    title_commands = manifest["object_schedules"]["title_draw_order"]
    cursor_assets = sorted(
        (asset for asset in manifest["assets"]
         if str(asset["path"]).startswith("FRONT/CUR") and
         str(asset["path"]).endswith(".BIN")),
        key=lambda asset: str(asset["path"]))
    cursor_index = {str(asset["path"]): index
                    for index, asset in enumerate(cursor_assets)}
    source_to_subbank = {26: 14, 27: 15}
    title_lines = []
    for command in title_commands:
        asset = assets[str(command["asset"])]
        title_lines.append(
            '    {"%s", %d, %d, %d, %d, %d, %d},' % (
                Path(str(command["asset"])).name,
                asset["bytes"], command["source_width"],
                command["source_height"], command["saturn_centre_x"],
                command["saturn_centre_y"],
                source_to_subbank[int(command["palette_bank"])]))
    cursor_lines = []
    for asset in cursor_assets:
        cursor_lines.append(
            '    {"%s", %d, %d, %d},' % (
                Path(str(asset["path"])).name, asset["bytes"],
                asset["width"], asset["height"]))
    cycle = manifest["cursor_animation"]["border_assets_in_display_order"]
    cycle_indices = ", ".join(str(cursor_index[str(path)]) for path in cycle)
    label_index = cursor_index[str(manifest["cursor_animation"]["label_asset"])]
    title_vdp1_bytes = sum(int(assets[str(command["asset"])]["bytes"])
                           for command in title_commands)
    cursor_vdp1_bytes = sum(int(asset["bytes"]) for asset in cursor_assets)
    text = f"""/* Generated by tools/gen_avsp_frontend.py; metadata only. */
#ifndef GENERATED_AVSP_FRONTEND_H
#define GENERATED_AVSP_FRONTEND_H

#define AVSP_FRONTEND_WIDTH 352
#define AVSP_FRONTEND_HEIGHT 224
#define AVSP_FRONTEND_DECODED_BYTES 78848
#define AVSP_FRONTEND_TITLE_RLE_FILE "TITLE.RLE"
#define AVSP_FRONTEND_TITLE_RLE_BYTES {assets['FRONT/TITLE.RLE']['bytes']}
#define AVSP_FRONTEND_TITLE_PALETTE_FILE "TITLE.PAL"
#define AVSP_FRONTEND_SELECT_RLE_FILE "SELBACK.RLE"
#define AVSP_FRONTEND_SELECT_RLE_BYTES {assets['FRONT/SELBACK.RLE']['bytes']}
#define AVSP_FRONTEND_SELECT_PALETTE_FILE "SELBACK.PAL"
#define AVSP_FRONTEND_PALETTE_BYTES 512
#define AVSP_FRONTEND_TITLE_OBJECT_COUNT {len(title_commands)}
#define AVSP_FRONTEND_CURSOR_CEL_COUNT {len(cursor_assets)}
#define AVSP_FRONTEND_CURSOR_PERIOD {len(cycle)}
#define AVSP_FRONTEND_CURSOR_LABEL_CEL {label_index}
#define AVSP_FRONTEND_CURSOR_PALETTE_SUBBANK 15
#define AVSP_FRONTEND_TITLE_PALETTE_A_FILE "TP1A.PAL"
#define AVSP_FRONTEND_TITLE_PALETTE_B_FILE "TP1B.PAL"
#define AVSP_FRONTEND_TITLE_PALETTE_A_SUBBANK 14
#define AVSP_FRONTEND_TITLE_PALETTE_B_SUBBANK 15
#define AVSP_FRONTEND_SUBPALETTE_BYTES 32
#define AVSP_FRONTEND_TITLE_VDP1_BYTES {title_vdp1_bytes}
#define AVSP_FRONTEND_CURSOR_VDP1_BYTES {cursor_vdp1_bytes}
#define AVSP_FRONTEND_VDP1_MAX_BYTES {max(title_vdp1_bytes, cursor_vdp1_bytes)}

typedef struct {{
    const char *filename;
    unsigned int bytes;
    unsigned short width;
    unsigned short height;
    short centre_x;
    short centre_y;
    unsigned char palette_subbank;
}} AvspFrontendTitleObject;

typedef struct {{
    const char *filename;
    unsigned int bytes;
    unsigned short width;
    unsigned short height;
}} AvspFrontendCursorCel;

#ifdef AVSP_FRONTEND_IMPLEMENTATION
static const AvspFrontendTitleObject avsp_frontend_title_objects[
    AVSP_FRONTEND_TITLE_OBJECT_COUNT] = {{
{chr(10).join(title_lines)}
}};

static const AvspFrontendCursorCel avsp_frontend_cursor_cels[
    AVSP_FRONTEND_CURSOR_CEL_COUNT] = {{
{chr(10).join(cursor_lines)}
}};

static const unsigned char avsp_frontend_cursor_cycle[
    AVSP_FRONTEND_CURSOR_PERIOD] = {{{cycle_indices}}};

/* Source indices 0 Warrior, 1 Schaefer, 2 Hunter, 3 Linn. */
static const short avsp_frontend_cursor_centres[4][2] = {{
    {{-118, -37}}, {{117, -37}}, {{117, 67}}, {{-118, 67}}
}};
#endif

#endif
"""
    return text.encode("ascii")


def bank_maps() -> dict[str, object]:
    composition = json.loads(
        (ROOT / "data" / "frontend_rom_composition.json").read_text(encoding="ascii"))
    result = {}
    for frame in composition["key_frames"]:
        banks = set(frame["object_palette_banks"])
        for values in frame["live_tilemap_palette_banks"].values():
            banks.update(values)
        ordered = sorted(banks)
        if len(ordered) != frame["live_palette_banks_total"]:
            raise ValueError(f"frame {frame['frame']}: bank accounting mismatch")
        if len(ordered) > 32:
            raise ValueError(f"frame {frame['frame']}: {len(ordered)} banks exceed 32")
        mapping = {f"0x{source:02X}": target for target, source in enumerate(ordered)}
        if len(set(mapping.values())) != len(mapping):
            raise ValueError(f"frame {frame['frame']}: palette alias")
        result[str(frame["frame"])] = {
            "live_banks": len(ordered), "source_to_frontend_bank": mapping,
        }
    return result


def generate() -> tuple[dict[str, object], dict[str, bytes]]:
    verify_roms()
    gfx = load_gfx_region()
    title = frame_state(FRONTEND_ROM, 1620, "objram1_1620.tsv")
    select = frame_state(INTERACTION, 2695, "objram_active_2694.tsv")

    title_back = render_layers(gfx, title, (3, 2), False)
    title_front = render_layers(gfx, title, (1,), True)
    title_objects, title_entries = decode_objects(gfx, title["objects"], title["palette"])
    title_full = title_back.copy()
    title_full.alpha_composite(title_objects)
    title_full.alpha_composite(title_front)
    compare("title", fit(title_full), fit(title["reference"]))
    # On this held title state the front tilemap has no visible overlap with
    # any title object. Prove that equivalence before flattening the two
    # tilemaps into one NBG1 surface; this leaves NBG0 available to Jo's debug
    # console and must not be generalized to transition frames.
    title_flat = title_back.copy()
    title_flat.alpha_composite(title_front)
    title_flat_composite = title_flat.copy()
    title_flat_composite.alpha_composite(title_objects)
    compare("title flattened tilemaps", fit(title_flat_composite),
            fit(title["reference"]))

    select_back = render_layers(gfx, select, (2, 3, 1), False)
    # MAME's screenshot callback sees the preceding frame's active cursor
    # list.  The two overlapping marker commands display in forward slot
    # order; this is independently required for the 2695 pixel oracle.
    select_objects, select_entries = decode_objects(
        gfx, select["objects"], select["palette"], reverse_priority=False)
    select_full = select_back.copy()
    select_full.alpha_composite(select_objects)
    compare("select", fit(select_full), fit(select["reference"]))

    files: dict[str, bytes] = {}
    assets: list[dict[str, object]] = []
    changed_live_colours = 0
    for filename, image, transparent, bundle in (
        ("TITLE.RLE", fit(title_flat), False, "title"),
        ("SELBACK.RLE", fit(select_back), False, "select"),
    ):
        pixels, palette, colours, changed_colours = index_surface(image, transparent)
        changed_live_colours += changed_colours
        encoded = rle_encode(pixels)
        if rle_decode(encoded) != pixels:
            raise ValueError(f"{filename}: RLE round trip failed")
        palette_name = filename.replace(".RLE", ".PAL")
        files[filename] = encoded
        files[palette_name] = palette
        assets.append(asset_record(f"FRONT/{filename}", encoded, "vdp2-rle-8bpp",
                                   decoded_bytes=len(pixels), colours=colours,
                                   rgb555_changed_colours=changed_colours,
                                   width=WIDTH, height=HEIGHT, bundle=bundle,
                                   transparent=transparent))
        assets.append(asset_record(f"FRONT/{palette_name}", palette,
                                   "cram-rgb555", entries=256, bundle=bundle))

    cursor_entries: dict[tuple[int, int, int, int], dict[str, int]] = {}
    for frame in range(2677, 3351):
        path = INTERACTION / f"objram_active_{frame:04d}.tsv"
        if not path.is_file():
            continue
        entries = [entry for entry in decode_object_entries(load_words(path))
                   if entry["tile_code"] and entry["colour"] == 15]
        if len(entries) == 2:
            for entry in entries:
                key = (entry["tile_code"], entry["width"], entry["height"],
                       entry["attribute"])
                cursor_entries[key] = entry
    sorted_cursor_entries = sorted(cursor_entries.values(),
                                   key=lambda value: value["tile_code"])
    cursor_asset_by_code: dict[int, str] = {}
    for index, entry in enumerate(sorted_cursor_entries):
        data = pack_object_cel(gfx, entry)
        filename = f"CUR{index:02d}.BIN"
        cursor_asset_by_code[entry["tile_code"]] = f"FRONT/{filename}"
        files[filename] = data
        assets.append(asset_record(
            f"FRONT/{filename}", data, "vdp1-4bpp-cel",
            tile_code=f"0x{entry['tile_code']:04X}", width=entry["width"],
            height=entry["height"], palette_bank=entry["colour"], bundle="select"))
    cursor_source_colours = [select["palette"][15 * 16 + pen][:3]
                             for pen in range(15)]
    cursor_palette = [0] + [rgb555(colour) for colour in cursor_source_colours]
    cursor_changed_colours = sum(
        rgb555_to_rgb(value) != colour
        for value, colour in zip(cursor_palette[1:], cursor_source_colours))
    changed_live_colours += cursor_changed_colours
    cursor_palette_data = b"".join(struct.pack(">H", value)
                                   for value in cursor_palette)
    files["CURSOR.PAL"] = cursor_palette_data
    assets.append(asset_record("FRONT/CURSOR.PAL", cursor_palette_data,
                               "vdp1-cram-rgb555", entries=16,
                               rgb555_changed_colours=cursor_changed_colours,
                               bundle="select"))

    title_commands = []
    title_palette_banks = sorted({entry["colour"] for entry in title_entries
                                  if entry["tile_code"]})
    for bank in title_palette_banks:
        data, changed_colours = object_palette(title["palette"], bank)
        changed_live_colours += changed_colours
        filename = f"TP{bank:02X}.PAL"
        files[filename] = data
        assets.append(asset_record(
            f"FRONT/{filename}", data, "vdp1-cram-rgb555", entries=16,
            source_palette_bank=bank, rgb555_changed_colours=changed_colours,
            bundle="title"))
    for index, entry in enumerate(entry for entry in title_entries
                                  if entry["tile_code"]):
        data = pack_object_cel(gfx, entry)
        filename = f"TIT{index:02d}.BIN"
        files[filename] = data
        assets.append(asset_record(
            f"FRONT/{filename}", data, "vdp1-4bpp-cel",
            tile_code=f"0x{entry['tile_code']:04X}", width=entry["width"],
            height=entry["height"], source_palette_bank=entry["colour"],
            bundle="title"))
        title_commands.append(object_command(entry, f"FRONT/{filename}"))

    cursor_commands = [
        object_command(entry, cursor_asset_by_code[entry["tile_code"]])
        for entry in select_entries if entry["tile_code"]
    ]
    cursor_cycle_codes = [0x887D, 0x889D, 0x88BD, 0x88DD, 0x883D, 0x885D]
    if any(code not in cursor_asset_by_code for code in cursor_cycle_codes + [0x8D04]):
        raise ValueError("cadence-1 capture is missing a cursor animation cel")

    title_drawn = [entry for entry in title_entries if entry["tile_code"]]
    select_drawn = [entry for entry in select_entries if entry["tile_code"]]
    bundle_bytes = {
        name: sum(int(asset["bytes"]) for asset in assets
                  if asset.get("bundle") == name)
        for name in ("title", "select")
    }
    for name, total in bundle_bytes.items():
        if total > BUNDLE_BUDGET:
            raise ValueError(f"{name} bundle {total} exceeds {BUNDLE_BUDGET}")

    manifest = {
        "schema": 1,
        "classification": "Saturn frontend assets derived from ROM graphics + "
                          "CPS tilemap/object/palette state; no captured pixels",
        "geometry": {"source_width": 384, "output_width": WIDTH,
                     "height": HEIGHT, "mapping": "endpoint-aligned-nearest"},
        "representation": {
            "title": "NBG1 fitted scroll3+scroll2+scroll1 surface plus VDP1 "
                     "objects; flattening is valid only because the measured "
                     "title hold has zero front-layer/object overlap",
            "select": "NBG1 fitted scroll2+scroll3+scroll1 without cursor; live "
                      "two-object VDP1 cursor",
        },
        "source_frames": {
            "title": 1620,
            "settled_select_state": 2695,
            "settled_select_displayed_object_list": 2694,
        },
        "pixel_checks": {
            "title_differences": 0,
            "title_flattened_layer_order_differences": 0,
            "select_differences": 0,
        },
        "colour_conversion": {
            "source_format": "MAME-expanded CPS palette RGB",
            "saturn_format": "RGB555",
            "changed_live_palette_entries": changed_live_colours,
        },
        "source_evidence": {
            "reconstructed_gfx_region_sha256": sha256(bytes(gfx)),
            "title": {
                name: file_sha256(FRONTEND_ROM / name)
                for name in (
                    "gfxram_1620.tsv", "cps_a_regs_1620.tsv",
                    "cps_b_regs_1620.tsv", "palette_1620.tsv",
                    "objram1_1620.tsv", "reference_1620.png")
            },
            "select": {
                name: file_sha256(INTERACTION / name)
                for name in (
                    "gfxram_2695.tsv", "cps_a_regs_2695.tsv",
                    "cps_b_regs_2695.tsv", "palette_2695.tsv",
                    "objram_active_2694.tsv", "reference_2695.png")
            },
        },
        "source_objects": {"title": len(title_drawn), "select": len(select_drawn)},
        "object_schedules": {
            "title_draw_order": title_commands,
            "settled_select_cursor_draw_order": cursor_commands,
        },
        "cursor_unique_cels": len(cursor_entries),
        "cursor_animation": {
            "source_frame_period": len(cursor_cycle_codes),
            "border_assets_in_display_order": [cursor_asset_by_code[code]
                                                 for code in cursor_cycle_codes],
            "label_asset": cursor_asset_by_code[0x8D04],
        },
        "cram_source_bank_maps": bank_maps(),
        "bundle_budget_bytes": BUNDLE_BUDGET,
        "bundle_bytes": bundle_bytes,
        "assets": sorted(assets, key=lambda item: str(item["path"])),
    }
    return manifest, files


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-deterministic", action="store_true")
    args = parser.parse_args()
    required = (FRONTEND_ROM / "gfxram_1620.tsv",
                INTERACTION / "gfxram_2695.tsv")
    if not all(path.is_file() for path in required):
        print("frontend assets: SKIPPED - private ROM-truth capture absent")
        return 0
    first_manifest, first_files = generate()
    first_header = runtime_header(first_manifest)
    if args.verify_deterministic:
        second_manifest, second_files = generate()
        second_header = runtime_header(second_manifest)
        if (first_manifest != second_manifest or first_files != second_files or
                first_header != second_header):
            raise ValueError("frontend generation is not deterministic")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for old_path in OUTPUT_DIR.iterdir():
        if old_path.is_file() and old_path.name not in first_files:
            old_path.unlink()
    for name, data in first_files.items():
        (OUTPUT_DIR / name).write_bytes(data)
    MANIFEST.write_text(json.dumps(first_manifest, indent=1, sort_keys=True) + "\n",
                        encoding="ascii")
    RUNTIME_HEADER.parent.mkdir(parents=True, exist_ok=True)
    RUNTIME_HEADER.write_bytes(first_header)
    print("frontend assets: PASS - title/select pixel checks exact, bundles %s"
          % first_manifest["bundle_bytes"])
    print("wrote", MANIFEST)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
