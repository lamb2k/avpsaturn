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
OUTPUT_ROOT = ROOT / "build" / "rom_extract"
SATURN_CD_ROOT = ROOT / "build" / "avsp_cd"
GENERATED_ROOT = ROOT / "generated"
VISIBLE_LEFT = 64
VISIBLE_TOP = 16
VISIBLE_WIDTH = 384
VISIBLE_HEIGHT = 224
STAGE1_ACTIVE_OBJECT_RAM = "objram2.tsv"

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


def load_palette() -> list[tuple[int, int, int, int]]:
    palette = []
    lines = (CAPTURE_ROOT / "palette.tsv").read_text(encoding="utf-8").splitlines()[1:]
    for line in lines:
        argb = int(line.split("\t")[1], 16)
        palette.append(((argb >> 16) & 255, (argb >> 8) & 255, argb & 255, 255))
    return palette


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

    entries: list[dict[str, int]] = []
    for offset in range(0, len(words) - 3, 4):
        x, y, code, attribute = words[offset:offset + 4]
        if y >= 0x8000 or attribute >= 0xFF00:
            break
        entries.append({"offset": offset, "x": x, "y": y, "code": code, "attribute": attribute})

    layer = Image.new("RGBA", (VISIBLE_WIDTH, VISIBLE_HEIGHT), (0, 0, 0, 0))
    rendered: list[dict[str, int]] = []
    for entry in reversed(entries):
        raw_x = entry["x"]
        raw_y = entry["y"]
        code = entry["code"] + ((raw_y & 0x6000) << 3)
        attribute = entry["attribute"]
        colour = attribute & 0x1F
        flip_x = bool(attribute & 0x20)
        flip_y = bool(attribute & 0x40)
        nx = ((attribute >> 8) & 0x0F) + 1 if attribute & 0xFF00 else 1
        ny = ((attribute >> 12) & 0x0F) + 1 if attribute & 0xFF00 else 1
        origin_x = raw_x & 0x3FF
        origin_y = raw_y & 0x3FF
        screen_x = origin_x - VISIBLE_LEFT
        screen_y = origin_y - VISIBLE_TOP
        rendered.append({
            **entry,
            "screen_x": screen_x,
            "screen_y": screen_y,
            "width": nx * 16,
            "height": ny * 16,
            "colour": colour,
        })

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
        filename = f"objram{bank}_{frame:04d}.tsv"
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


def exact_object_layers(gfx: bytearray, palette: list[tuple[int, int, int, int]],
                        frame: int, bank: int, offsets: list[int],
                        shift_x: int = 0) -> tuple[dict[int, Image.Image],
                                                   dict[int, list[tuple[int, int, int]]]]:
    """Render selected CPS2 commands without scaling or palette quantisation."""
    filename = f"objram{bank}.tsv" if frame == 4200 else f"objram{bank}_{frame:04d}.tsv"
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
    frame_left = (192 - union_width) // 2
    frame_top = 184 - union_height

    colours = sorted({command["colour"] for command in commands})
    layers = {colour: Image.new("P", (192, 192), 0) for colour in colours}
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
                target_x = frame_left + command["x"] - left + tile_x * 16
                target_y = frame_top + command["y"] - top + tile_y * 16
                for pixel_y in range(16):
                    for pixel_x in range(16):
                        pen = source_pixels[pixel_x, pixel_y]
                        if pen == 15:
                            continue
                        destination_x = target_x + (15 - pixel_x if flip_x else pixel_x)
                        destination_y = target_y + (15 - pixel_y if flip_y else pixel_y)
                        if 0 <= destination_x < 192 and 0 <= destination_y < 192:
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


def write_snapshot_asset(layer: Image.Image, sprite_dir: Path) -> dict[str, object]:
    """Write the complete captured CPS2 object pass as a lossless 8bpp cel."""
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
    return {"path": "SPR8/OBJFRM.BIN", "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "visible_colours": len(colours)}


def write_exact_actor_assets(gfx: bytearray,
                             palette: list[tuple[int, int, int, int]],
                             sprite_dir: Path) -> list[dict[str, object]]:
    groups = {
        "player_idle": exact_object_layers(gfx, palette, 2880, 1, [76, 80, 84, 88]),
        "player_attack": exact_object_layers(
            gfx, palette, 2940, 2, list(range(72, 117, 4)), shift_x=-150),
        "alien_a": exact_object_layers(gfx, palette, 4200, 2, [124, 128]),
        "alien_b": exact_object_layers(gfx, palette, 4200, 2, [144, 148]),
    }
    # Fixed Saturn subpalette slots. Player layers retain CPS2 palettes 0, 7,
    # and 15; the Stage 1 alien retains palette 16.
    cps_colours = (0, 7, 15, 16)
    all_palettes: dict[int, list[tuple[int, int, int]]] = {}
    for _, (_, group_palettes) in groups.items():
        all_palettes.update(group_palettes)
    write_exact_palette_header([all_palettes[colour] for colour in cps_colours])

    file_map = {
        "PXI0.BIN": ("player_idle", 0),
        "PXI1.BIN": ("player_idle", 7),
        "PXA0.BIN": ("player_attack", 0),
        "PXA1.BIN": ("player_attack", 7),
        "PXA2.BIN": ("player_attack", 15),
        "EXA0.BIN": ("alien_a", 16),
        "EXB0.BIN": ("alien_b", 16),
    }
    manifest = []
    preview = Image.new("RGBA", (384, 576), (20, 20, 20, 255))
    preview_groups = (("player_idle", 0), ("player_attack", 192),
                      ("alien_a", 384))
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

    player_idle = fit_actor_frame(selected_object_layer(
        gfx, palette, 2880, 1, [76, 80, 84, 88]))
    player_attack = fit_actor_frame(selected_object_layer(
        gfx, palette, 2940, 2, list(range(72, 125, 4)), shift_x=-150))
    alien_a = fit_actor_frame(selected_object_layer(gfx, palette, 4200, 2, [124, 128]))
    alien_b = fit_actor_frame(selected_object_layer(gfx, palette, 4200, 2, [144, 148]))
    alien_c = fit_actor_frame(selected_object_layer(gfx, palette, 4200, 2, [160, 164]))

    player_sources = [player_idle, player_attack]
    alien_sources = [alien_a, alien_b, alien_c]
    player_palette = common_4bpp_palette(player_sources)
    alien_palette = common_4bpp_palette(alien_sources)
    write_palette_header(player_palette, alien_palette)

    frames = {
        "P_IDLE.BIN": (player_idle, player_palette),
        "P_WLK1.BIN": (player_idle, player_palette),
        "P_WLK2.BIN": (player_idle, player_palette),
        "P_ATK1.BIN": (player_attack, player_palette),
        "P_ATK2.BIN": (player_attack, player_palette),
        "P_SPC1.BIN": (player_attack, player_palette),
        "P_SPC2.BIN": (player_attack, player_palette),
        "P_HIT.BIN": (player_attack, player_palette),
        "E_IDLE.BIN": (alien_a, alien_palette),
        "E_WLK1.BIN": (alien_b, alien_palette),
        "E_WLK2.BIN": (alien_c, alien_palette),
        "E_ATK1.BIN": (alien_a, alien_palette),
        "E_ATK2.BIN": (alien_c, alien_palette),
        "E_HIT.BIN": (alien_b, alien_palette),
        "E_KO.BIN": (alien_c, alien_palette),
    }
    manifest: list[dict[str, object]] = []
    for filename, (source, colours) in frames.items():
        packed = pack_4bpp(map_to_4bpp(source, colours))
        target = sprite_dir / filename
        target.write_bytes(packed)
        manifest.append({"path": f"SPR4/{filename}", "bytes": len(packed),
                         "sha256": hashlib.sha256(packed).hexdigest()})

    # Reuse the small original-engine utility sprites; the visible character
    # and enemy art above comes only from the verified local CPS2 set.
    for filename in ("SHADOW.BIN", "HITFX.BIN"):
        data = (ROOT / "cd" / "SPR4" / filename).read_bytes()
        (sprite_dir / filename).write_bytes(data)
        manifest.append({"path": f"SPR4/{filename}", "bytes": len(data),
                         "sha256": hashlib.sha256(data).hexdigest()})

    manifest.extend(write_exact_actor_assets(gfx, palette, sprite_dir))
    manifest.append(write_snapshot_asset(object_layer, snapshot_dir))

    stage = render_background(gfx, gfxram, cps_a, cps_b, palette,
                              width=512, height=256, include_scroll1=True)
    stage.save(OUTPUT_ROOT / "stage1_saturn_background.png")
    stage = stage.convert("RGB").quantize(colors=256, method=Image.Quantize.MAXCOVERAGE)
    background_target = background_dir / "CORRIDOR.TGA"
    stage.save(background_target, format="TGA", compression=None)
    background_data = background_target.read_bytes()
    manifest.append({"path": "BG/CORRIDOR.TGA", "bytes": len(background_data),
                     "sha256": hashlib.sha256(background_data).hexdigest()})

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
    palette = load_palette()
    gfxram = load_words("gfxram.tsv")
    cps_a = load_words("cps_a_regs.tsv")
    cps_b = load_words("cps_b_regs.tsv")
    background = render_background(gfx, gfxram, cps_a, cps_b, palette)
    words = load_words(STAGE1_ACTIVE_OBJECT_RAM)
    layer, entries = decode_objects(gfx, words, palette)
    verify_stage1_object_capture(entries)
    saturn_layer = final_visible_object_surface(background, layer)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    background.save(OUTPUT_ROOT / "stage1_background.png")
    composite = background.copy()
    composite.alpha_composite(layer)
    composite.save(OUTPUT_ROOT / "stage1_reconstructed.png")
    write_saturn_assets(gfx, palette, gfxram, cps_a, cps_b, saturn_layer)
    saturn_layer.save(OUTPUT_ROOT / "stage1_saturn_visible_objects.png")
    layer.save(OUTPUT_ROOT / "stage1_objects.png")
    (OUTPUT_ROOT / "stage1_objects.json").write_text(
        json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    make_contact_sheet(layer, entries)
    print(f"Decoded {len(entries)} CPS2 object commands to {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
