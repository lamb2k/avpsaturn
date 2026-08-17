"""Extract white debug hitbox brackets from selected stock-MAME screenshots.

This is screen-space evidence only.  It intentionally does not infer actor-local
origins or replace the 21/55/97 contact offsets until those origins are paired
with the actor/object coordinates.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image


def runs(values: list[bool], minimum: int = 6) -> list[tuple[int, int]]:
    found: list[tuple[int, int]] = []
    start = None
    for index, value in enumerate(values + [False]):
        if value and start is None:
            start = index
        elif not value and start is not None:
            if index - start >= minimum:
                found.append((start, index - 1))
            start = None
    return found


def bracket_boxes(path: Path) -> list[dict[str, int]]:
    image = Image.open(path).convert("RGB")
    width, height = image.size
    white = [[image.getpixel((x, y)) == (255, 255, 255) for x in range(width)]
             for y in range(height)]
    horizontal = [(y, x0, x1) for y, row in enumerate(white)
                  for x0, x1 in runs(row)]
    boxes: set[tuple[int, int, int, int]] = set()
    # Some revisions draw a complete top/bottom edge rather than two corner
    # runs.  Keep these candidates separate only by geometry; the caller still
    # has to reject HUD/text false positives during actor pairing.
    for y0, x0, x1 in horizontal:
        if x1 - x0 < 20:
            continue
        for y1, bx0, bx1 in horizontal:
            if y1 <= y0 + 15 or y1 > y0 + 120:
                continue
            if abs(bx0 - x0) <= 2 and abs(bx1 - x1) <= 2:
                boxes.add((x0, y0, x1, y1))
    for y0 in range(height):
        top = [(x0, x1) for y, x0, x1 in horizontal if y == y0]
        for left, right in ((a, b) for a in top for b in top if a[0] < b[0]):
            if not 20 <= right[0] - left[0] <= 140:
                continue
            for y1, bx0, bx1 in horizontal:
                if y1 <= y0 + 20 or y1 > y0 + 120:
                    continue
                if abs(bx0 - left[0]) > 2:
                    continue
                bottom_right = next(
                    (cx1 for by, cx0, cx1 in horizontal
                     if by == y1 and abs(cx0 - right[0]) <= 2), None)
                if bottom_right is not None and abs(bottom_right - right[1]) <= 2:
                    boxes.add((left[0], y0, right[1], y1))
    return [{"x0": x0, "y0": y0, "x1": x1, "y1": y1,
             "width": x1 - x0 + 1, "height": y1 - y0 + 1}
            for x0, y0, x1, y1 in sorted(boxes, key=lambda b: (b[1], b[0]))]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    result = {
        "schema": 1,
        "classification": "capture-exact screen-space bracket geometry",
        "purpose": "Live white hitbox overlay evidence; actor-local conversion remains open.",
        "frames": [{"image": path.as_posix(), "boxes": bracket_boxes(path)}
                   for path in args.images],
        "remaining_gate": "Pair each bracket with actor/object origin before replacing inferred 21/55/97.",
    }
    payload = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="ascii")
    print(payload, end="")


if __name__ == "__main__":
    main()
