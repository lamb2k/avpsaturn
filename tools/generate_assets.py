#!/usr/bin/env python3
"""Generate deterministic, original assets for the Saturn capability slice."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SPRITE_SIZE = (64, 80)
ACTOR_FRAME_SIZE = (192, 192)


def sprite_canvas(size: tuple[int, int] = SPRITE_SIZE) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("P", size, 0)
    return image, ImageDraw.Draw(image)


def draw_player(pose: str) -> Image.Image:
    image, draw = sprite_canvas()
    stride = -2 if pose == "walk1" else 2 if pose == "walk2" else 0
    lean = 3 if pose in {"attack1", "attack2", "special1", "special2"} else 0
    if pose == "hit":
        lean = -5

    # Boots and legs.
    draw.polygon([(23 + stride, 54), (31, 54), (29 + stride, 72), (20 + stride, 72)], fill=2)
    draw.polygon([(33, 54), (41 - stride, 54), (45 - stride, 72), (35 - stride, 72)], fill=3)
    draw.rectangle((17 + stride, 70, 30 + stride, 75), fill=1)
    draw.rectangle((35 - stride, 70, 50 - stride, 75), fill=1)

    # Armored torso and shoulder silhouette.
    draw.polygon([(20 + lean, 25), (29 + lean, 20), (43 + lean, 24),
                  (47 + lean, 48), (39, 58), (24, 56), (17 + lean, 43)], fill=6)
    draw.polygon([(24 + lean, 27), (39 + lean, 25), (42 + lean, 45),
                  (34, 51), (24, 47)], fill=7)
    draw.rectangle((26 + lean, 32, 38 + lean, 38), fill=4)
    draw.rectangle((29 + lean, 33, 35 + lean, 36), fill=5)

    # Head and visor.
    draw.ellipse((24 + lean, 8, 41 + lean, 26), fill=10)
    draw.polygon([(27 + lean, 11), (39 + lean, 12), (38 + lean, 18),
                  (27 + lean, 17)], fill=9)
    draw.rectangle((29 + lean, 13, 38 + lean, 15), fill=13)

    # Rear arm.
    draw.line((20 + lean, 30, 12 + lean, 47, 16 + stride, 59), fill=3, width=6)
    draw.ellipse((12 + stride, 55, 19 + stride, 63), fill=12)

    # Lead arm changes pose and makes the animation silhouette obvious.
    if pose in {"attack1", "special1"}:
        draw.line((42 + lean, 30, 52, 40, 57, 49), fill=7, width=7)
        draw.ellipse((53, 45, 62, 54), fill=12)
    elif pose in {"attack2", "special2"}:
        draw.line((42 + lean, 30, 53, 31, 61, 29), fill=7, width=7)
        draw.ellipse((57, 25, 63, 33), fill=13)
    elif pose == "hit":
        draw.line((39, 31, 48, 46, 51, 57), fill=6, width=7)
        draw.ellipse((47, 53, 55, 61), fill=12)
    else:
        hand_y = 51 + (2 if pose == "walk1" else -2 if pose == "walk2" else 0)
        draw.line((42, 30, 48, 43, 50, hand_y), fill=7, width=7)
        draw.ellipse((46, hand_y - 2, 54, hand_y + 6), fill=12)

    if pose in {"special1", "special2"}:
        radius = 12 if pose == "special1" else 18
        draw.arc((50 - radius, 29 - radius, 50 + radius, 29 + radius), 220, 80, fill=15, width=3)
        draw.line((51, 29, 63, 20 if pose == "special2" else 25), fill=9, width=2)
        draw.point((62, 18), fill=13)

    return image


def draw_crawler(pose: str) -> Image.Image:
    image, draw = sprite_canvas()
    body_y = 42
    if pose == "attack1":
        body_y = 39
    if pose == "hit":
        body_y = 45

    if pose == "ko":
        draw.ellipse((9, 55, 51, 68), fill=2)
        draw.polygon([(18, 58), (30, 48), (53, 53), (48, 64), (25, 66)], fill=5)
        draw.line((21, 60, 9, 72), fill=3, width=4)
        draw.line((41, 60, 58, 70), fill=3, width=4)
        draw.line((39, 53, 57, 43), fill=6, width=3)
        return image

    tail_shift = -4 if pose == "walk1" else 4 if pose == "walk2" else 0
    draw.arc((0 + tail_shift, body_y - 9, 48, body_y + 32), 150, 332, fill=6, width=5)
    draw.ellipse((16, body_y - 14, 48, body_y + 14), fill=4)
    draw.ellipse((24, body_y - 12, 51, body_y + 11), fill=5)
    draw.polygon([(35, body_y - 13), (51, body_y - 8), (59, body_y + 1),
                  (50, body_y + 9), (35, body_y + 8)], fill=7)
    draw.polygon([(47, body_y - 5), (60, body_y), (49, body_y + 4)], fill=8)
    draw.rectangle((50, body_y - 1, 57, body_y + 1), fill=9)

    # Four jointed legs with two distinct walk contacts.
    offsets = (-4, 2, 4, -2) if pose == "walk1" else (3, -3, -2, 4)
    for index, root_x in enumerate((20, 29, 37, 45)):
        side = -1 if index < 2 else 1
        knee_x = root_x + side * 8 + offsets[index]
        foot_x = root_x + side * 15 + offsets[index]
        draw.line((root_x, body_y + 5, knee_x, body_y + 18, foot_x, body_y + 28), fill=3, width=4)
        draw.line((foot_x, body_y + 28, foot_x + side * 5, body_y + 28), fill=6, width=3)

    if pose in {"attack1", "attack2"}:
        claw_x = 63 if pose == "attack2" else 57
        draw.line((44, body_y + 3, claw_x, body_y + 14), fill=7, width=5)
        draw.line((claw_x - 2, body_y + 13, 63, body_y + 9), fill=15, width=2)
        draw.line((claw_x - 2, body_y + 14, 63, body_y + 18), fill=15, width=2)

    if pose == "hit":
        draw.line((42, body_y - 6, 58, body_y - 17), fill=14, width=3)
        draw.line((45, body_y - 5, 61, body_y - 7), fill=15, width=2)
    return image


def draw_shadow() -> Image.Image:
    image, draw = sprite_canvas((32, 8))
    draw.ellipse((1, 1, 30, 6), fill=2)
    draw.ellipse((7, 2, 24, 5), fill=3)
    return image


def draw_hit_flash() -> Image.Image:
    base, draw = sprite_canvas((32, 32))
    draw.polygon([(15, 0), (19, 11), (30, 5), (23, 15), (31, 20),
                  (20, 21), (22, 31), (15, 24), (7, 31), (10, 21),
                  (0, 20), (8, 15), (1, 6), (12, 11)], fill=8)
    draw.polygon([(15, 7), (18, 13), (24, 11), (21, 17), (25, 20),
                  (18, 20), (15, 26), (13, 20), (7, 20), (11, 16),
                  (8, 12), (13, 14)], fill=13)
    draw.ellipse((13, 13, 18, 18), fill=15)
    return base.resize((64, 64), Image.Resampling.NEAREST)


def actor_frame(base: Image.Image) -> Image.Image:
    frame = Image.new("P", ACTOR_FRAME_SIZE, 0)
    scaled = base.resize((154, 192), Image.Resampling.NEAREST)
    frame.paste(scaled, (19, 0))
    return frame


def make_background() -> Image.Image:
    width, height = 512, 256
    image = Image.new("P", (width, height), 1)
    draw = ImageDraw.Draw(image)

    # Original industrial corridor: distant ceiling, repeating bulkheads,
    # floor grid and a high-contrast playable lane.
    draw.rectangle((0, 0, width, 54), fill=2)
    for y in range(0, 54, 6):
        draw.line((0, y, width, y), fill=3 if (y // 6) & 1 else 4)
    draw.rectangle((0, 54, width, 149), fill=5)
    for x in range(0, width, 64):
        draw.rectangle((x + 3, 58, x + 11, 147), fill=6)
        draw.rectangle((x + 12, 64, x + 59, 137), fill=7)
        draw.line((x + 15, 70, x + 56, 70), fill=10, width=2)
        draw.rectangle((x + 19, 80, x + 53, 118), fill=8)
        draw.rectangle((x + 23, 85, x + 49, 113), fill=9)
        draw.rectangle((x + 25, 88, x + 47, 91), fill=13)
        draw.rectangle((x + 16, 128, x + 56, 134), fill=11)
        draw.rectangle((x + 4, 60, x + 10, 67), fill=14 if (x // 64) & 1 else 15)

    draw.rectangle((0, 149, width, 255), fill=16)
    draw.rectangle((0, 149, width, 156), fill=12)
    for y in (171, 198, 228):
        draw.line((0, y, width, y), fill=18, width=2)
    for x in range(-160, width + 160, 48):
        draw.line((x, 255, x + 85, 151), fill=17, width=2)
    for x in range(0, width, 96):
        draw.rectangle((x + 5, 207, x + 39, 213), fill=19)
        draw.rectangle((x + 42, 207, x + 83, 213), fill=20)
    draw.line((0, 183, width, 183), fill=21, width=2)
    return image


def pack_4bpp(image: Image.Image) -> bytes:
    width, height = image.size
    if width % 8:
        raise ValueError(f"4bpp sprite width must be a multiple of 8, got {width}")
    pixels = list(image.tobytes())
    if max(pixels, default=0) > 15:
        raise ValueError("4bpp source contains a palette index above 15")
    output = bytearray()
    for y in range(height):
        row = y * width
        for x in range(0, width, 2):
            output.append((pixels[row + x] << 4) | pixels[row + x + 1])
    return bytes(output)


def sprite_assets() -> dict[str, Image.Image]:
    return {
        "P_IDLE.BIN": actor_frame(draw_player("idle")),
        "P_WLK1.BIN": actor_frame(draw_player("walk1")),
        "P_WLK2.BIN": actor_frame(draw_player("walk2")),
        "P_ATK1.BIN": actor_frame(draw_player("attack1")),
        "P_ATK2.BIN": actor_frame(draw_player("attack2")),
        "P_SPC1.BIN": actor_frame(draw_player("special1")),
        "P_SPC2.BIN": actor_frame(draw_player("special2")),
        "P_HIT.BIN": actor_frame(draw_player("hit")),
        "E_IDLE.BIN": actor_frame(draw_crawler("idle")),
        "E_WLK1.BIN": actor_frame(draw_crawler("walk1")),
        "E_WLK2.BIN": actor_frame(draw_crawler("walk2")),
        "E_ATK1.BIN": actor_frame(draw_crawler("attack1")),
        "E_ATK2.BIN": actor_frame(draw_crawler("attack2")),
        "E_HIT.BIN": actor_frame(draw_crawler("hit")),
        "E_KO.BIN": actor_frame(draw_crawler("ko")),
        "SHADOW.BIN": draw_shadow().resize((64, 16), Image.Resampling.NEAREST),
        "HITFX.BIN": draw_hit_flash(),
    }


def build_assets(output_root: Path) -> dict[str, object]:
    sprite_dir = output_root / "cd" / "SPR4"
    background_dir = output_root / "cd" / "BG"
    sprite_dir.mkdir(parents=True, exist_ok=True)
    background_dir.mkdir(parents=True, exist_ok=True)

    entries: list[dict[str, object]] = []
    for filename, image in sprite_assets().items():
        data = pack_4bpp(image)
        target = sprite_dir / filename
        target.write_bytes(data)
        entries.append({
            "path": target.relative_to(output_root).as_posix(),
            "width": image.width,
            "height": image.height,
            "format": "packed-4bpp-high-nibble-first",
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })

    background = make_background()
    palette = [0] * (256 * 3)
    colors = {
        0: (0, 0, 0), 1: (9, 12, 16), 2: (14, 19, 25), 3: (20, 27, 34),
        4: (29, 37, 45), 5: (37, 45, 50), 6: (20, 26, 29), 7: (48, 58, 61),
        8: (21, 29, 32), 9: (8, 13, 16), 10: (72, 86, 88), 11: (83, 93, 88),
        12: (121, 128, 113), 13: (82, 151, 164), 14: (239, 174, 46),
        15: (183, 50, 38), 16: (30, 34, 37), 17: (49, 54, 56),
        18: (65, 70, 69), 19: (22, 26, 29), 20: (87, 76, 49),
        21: (117, 88, 48),
    }
    for index, color in colors.items():
        palette[index * 3:index * 3 + 3] = list(color)
    background.putpalette(palette)
    background_target = background_dir / "CORRIDOR.TGA"
    background.save(background_target, format="TGA", compression=None)
    background_data = background_target.read_bytes()
    entries.append({
        "path": background_target.relative_to(output_root).as_posix(),
        "width": background.width,
        "height": background.height,
        "format": "indexed-8bpp-tga",
        "bytes": len(background_data),
        "sha256": hashlib.sha256(background_data).hexdigest(),
    })

    manifest = {
        "generator": "tools/generate_assets.py",
        "license": "Original procedural placeholders generated for this repository",
        "assets": sorted(entries, key=lambda entry: str(entry["path"])),
    }
    manifest_path = output_root / "asset_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def compare_generated() -> int:
    with tempfile.TemporaryDirectory(prefix="saturn-capability-assets-") as temp:
        temporary_root = Path(temp)
        generated = build_assets(temporary_root)
        expected_manifest = ROOT / "asset_manifest.json"
        if not expected_manifest.exists():
            print("asset_manifest.json is missing; run the generator without --check")
            return 1
        committed = json.loads(expected_manifest.read_text(encoding="utf-8"))
        if generated != committed:
            print("asset manifest differs from deterministic generator output")
            return 1
        for entry in generated["assets"]:
            relative = Path(str(entry["path"]))
            actual = ROOT / relative
            expected = temporary_root / relative
            if not actual.exists() or actual.read_bytes() != expected.read_bytes():
                print(f"asset differs: {relative.as_posix()}")
                return 1
    print("Asset check passed: all generated files are deterministic and current.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify committed assets")
    args = parser.parse_args()
    if args.check:
        return compare_generated()
    manifest = build_assets(ROOT)
    print(f"Generated {len(manifest['assets'])} assets in {ROOT / 'cd'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
