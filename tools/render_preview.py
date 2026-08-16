#!/usr/bin/env python3
"""Render desktop previews of the packed Saturn assets for visual QA."""

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"

PLAYER_COLORS = [
    (0, 0, 0), (22, 30, 38), (45, 66, 78), (77, 103, 112),
    (132, 157, 161), (219, 224, 211), (53, 84, 142), (75, 132, 187),
    (221, 125, 48), (250, 190, 74), (122, 64, 38), (191, 117, 73),
    (239, 185, 137), (255, 237, 194), (151, 35, 40), (244, 76, 65),
]

CRAWLER_COLORS = [
    (0, 0, 0), (8, 14, 12), (18, 31, 25), (28, 50, 38),
    (41, 72, 51), (64, 103, 69), (93, 137, 88), (134, 174, 110),
    (180, 211, 143), (196, 220, 76), (135, 154, 36), (77, 91, 24),
    (42, 48, 25), (115, 48, 52), (185, 65, 58), (232, 132, 71),
]


def unpack_4bpp(path: Path, width: int, height: int, colors: list[tuple[int, int, int]]) -> Image.Image:
    data = path.read_bytes()
    expected = width * height // 2
    if len(data) != expected:
        raise ValueError(f"{path.name}: expected {expected} bytes, got {len(data)}")
    pixels = bytearray(width * height)
    for index, value in enumerate(data):
        pixels[index * 2] = value >> 4
        pixels[index * 2 + 1] = value & 15
    indexed = Image.frombytes("P", (width, height), bytes(pixels))
    palette = [channel for color in colors for channel in color] + [0] * (256 * 3 - 16 * 3)
    indexed.putpalette(palette)
    indexed.info["transparency"] = 0
    return indexed.convert("RGBA")


def render_actor_sheet() -> None:
    names = [
        "P_IDLE.BIN", "P_WLK1.BIN", "P_WLK2.BIN", "P_ATK1.BIN", "P_ATK2.BIN",
        "P_SPC1.BIN", "P_SPC2.BIN", "P_HIT.BIN", "E_IDLE.BIN", "E_WLK1.BIN",
        "E_WLK2.BIN", "E_ATK1.BIN", "E_ATK2.BIN", "E_HIT.BIN", "E_KO.BIN",
    ]
    columns = 5
    cell_width = 210
    cell_height = 218
    rows = (len(names) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * cell_width, rows * cell_height), (30, 33, 38))
    draw = ImageDraw.Draw(sheet)
    for index, name in enumerate(names):
        colors = PLAYER_COLORS if name.startswith("P_") else CRAWLER_COLORS
        actor = unpack_4bpp(ROOT / "cd" / "SPR4" / name, 192, 192, colors)
        x = (index % columns) * cell_width + 9
        y = (index // columns) * cell_height + 20
        sheet.paste(actor, (x, y), actor)
        draw.text((x, 4 + (index // columns) * cell_height), name, fill=(230, 230, 220))
        draw.rectangle((x, y, x + 191, y + 191), outline=(72, 77, 84))
    sheet.save(BUILD / "actor_contact_sheet.png")


def main() -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    render_actor_sheet()
    Image.open(ROOT / "cd" / "BG" / "CORRIDOR.TGA").convert("RGB").save(
        BUILD / "corridor_preview.png"
    )
    print(f"Wrote previews to {BUILD}")


if __name__ == "__main__":
    main()
