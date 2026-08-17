"""Pair selected debug hitbox rectangles with their white pivot markers.

The result is capture-exact overlay geometry and actor-state context.  It is
not yet the native collision table: the runtime replacement remains a gate.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".deps" / "mame" / "round1_debug_hitboxes" / "actor_state.bin"
FIRST_FRAME = 4201
SAMPLE_SIZE = 0x2D00
ACTOR_BLOCK_OFFSET = 0x0D00
ACTOR_STRIDE = 0xC0

OBSERVATIONS = (
    (13700, "stalker", 0xFFB500, (216, 103, 273, 180), (232, 184)),
    (13700, "player", 0xFFA240, (335, 112, 380, 191), (352, 192)),
    (14400, "chrysalis", 0xFFA3C0, (176, 184, 271, 199), (224, 192)),
    (14400, "player", 0xFFA240, (331, 101, 370, 192), (352, 192)),
)


def actor_words(frame: int, address: int) -> dict[str, object]:
    sample = (STATE.read_bytes()[(frame - FIRST_FRAME) * SAMPLE_SIZE:
                                 (frame - FIRST_FRAME + 1) * SAMPLE_SIZE])
    offset = ACTOR_BLOCK_OFFSET + (address - 0xFFA000)
    words = [int.from_bytes(sample[offset + i:offset + i + 2], "big")
             for i in range(0, ACTOR_STRIDE, 2)]
    return {
        "w10": words[0x10 // 2],
        "w14": words[0x14 // 2],
        "w18": words[0x18 // 2],
        "script_pointer": f"0x{(words[0x1c // 2] << 16 | words[0x1e // 2]):06x}",
        "health_word": words[0x44 // 2],
    }


def white(image: Image.Image, x: int, y: int) -> bool:
    return image.getpixel((x, y)) == (255, 255, 255)


def verify_pivot(image: Image.Image, pivot: tuple[int, int]) -> None:
    x, y = pivot
    if sum(white(image, px, py) for px in range(x - 4, x + 5)
           for py in (y, y + 1)) < 8:
        raise ValueError(f"pivot {pivot}: missing horizontal white marker")
    if sum(white(image, px, py) for px in (x, x + 1)
           for py in range(y - 4, y + 5)) < 8:
        raise ValueError(f"pivot {pivot}: missing vertical white marker")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", type=Path,
                        default=ROOT / "data" / "round1_hitbox_geometry.json")
    args = parser.parse_args()
    rows = []
    for frame, actor, address, box, pivot in OBSERVATIONS:
        image_path = ROOT / ".deps" / "mame" / "round1_debug_hitboxes" / f"overlay_{frame:05d}.png"
        image = Image.open(image_path).convert("RGB")
        verify_pivot(image, pivot)
        x0, y0, x1, y1 = box
        rows.append({
            "frame": frame,
            "actor": actor,
            "actor_address": f"0x{address:06x}",
            "image": image_path.relative_to(ROOT).as_posix(),
            "screen_box": {"x0": x0, "y0": y0, "x1": x1, "y1": y1,
                           "width": x1 - x0 + 1, "height": y1 - y0 + 1},
            "screen_pivot_marker": {"x": pivot[0], "y": pivot[1]},
            "pivot_relative_candidate": {
                "left": x0 - pivot[0], "top": y0 - pivot[1],
                "right": x1 - pivot[0], "bottom": y1 - pivot[1],
            },
            "actor_state_context": actor_words(frame, address),
        })
    result = {
        "schema": 1,
        "classification": "capture-exact overlay geometry; native collision replacement missing",
        "purpose": "White debug boxes paired with their white pivot markers and actor-state context.",
        "observations": rows,
        "remaining_gate": (
            "Validate pivot-relative candidates across all Round 1 poses and actor types, "
            "then replace inferred 21/55/97 and Stalker contact data in native collision code."
        ),
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    print(f"Validated {len(rows)} actor-labeled hitbox geometries: {args.output}")


if __name__ == "__main__":
    main()
