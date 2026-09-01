#!/usr/bin/env python3
"""Create cadence-1 visual QA from a debug-rig framebuffer_burst manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


EXPECTED_SIZE = (800, 612)
PRESENTED_APERTURE = (0, 53, 800, 559)
OUTPUT_SIZE = (352, 224)
FONT = ImageFont.load_default()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_manifest(path: Path) -> list[dict[str, object]]:
    lines = path.read_text(encoding="ascii").splitlines()
    if not lines or lines[0] != "frame\tfile\tsha256":
        raise ValueError("invalid framebuffer_burst manifest header")
    rows: list[dict[str, object]] = []
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) != 3:
            raise ValueError("invalid framebuffer_burst manifest row")
        frame = int(parts[0])
        image_path = path.parent / parts[1]
        if not image_path.is_file() or sha(image_path) != parts[2]:
            raise ValueError(f"framebuffer_burst image identity drift at {frame}")
        rows.append({"frame": frame, "path": image_path, "sha256": parts[2]})
    if not rows or any(right["frame"] != left["frame"] + 1
                       for left, right in zip(rows, rows[1:])):
        raise ValueError("framebuffer_burst frames are not cadence-1")
    return rows


def aperture(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB")
    if image.size != EXPECTED_SIZE:
        raise ValueError(f"unexpected MCP framebuffer size {image.size}")
    return image.crop(PRESENTED_APERTURE).resize(
        OUTPUT_SIZE, Image.Resampling.NEAREST)


def labelled(image: Image.Image, frame: int) -> Image.Image:
    result = image.copy()
    draw = ImageDraw.Draw(result)
    text = f"emulator frame {frame}"
    box = draw.textbbox((0, 0), text, font=FONT)
    draw.rectangle((2, 2, box[2] + 8, box[3] + 8), fill="black")
    draw.text((5, 5), text, font=FONT, fill="white")
    return result


def build(manifest: Path, output: Path) -> dict[str, object]:
    rows = read_manifest(manifest)
    images = [aperture(row["path"]) for row in rows]
    output.mkdir(parents=True, exist_ok=True)
    first = int(rows[0]["frame"])
    last = int(rows[-1]["frame"])
    clip = output / f"mcp-frames-{first}-{last}.webp"
    images[0].save(clip, save_all=True, append_images=images[1:],
                   duration=17, loop=0, lossless=True, method=6)
    columns = min(8, len(images))
    rows_count = (len(images) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * OUTPUT_SIZE[0],
                              rows_count * OUTPUT_SIZE[1]), "black")
    for index, (row, image) in enumerate(zip(rows, images)):
        sheet.paste(labelled(image, int(row["frame"])),
                    ((index % columns) * OUTPUT_SIZE[0],
                     (index // columns) * OUTPUT_SIZE[1]))
    sheet_path = output / "cadence-1-contact-sheet.png"
    sheet.save(sheet_path)
    sequence = "\n".join(f"{row['frame']}\t{row['sha256']}" for row in rows)
    report = {
        "schema": 1,
        "capture_mode": "MCP_FRAMEBUFFER_BURST",
        "evidence_tier": "ONE_EMULATOR",
        "frame_range": [first, last],
        "frame_count": len(rows),
        "unique_frame_hashes": len({row["sha256"] for row in rows}),
        "manifest_sha256": sha(manifest),
        "canonical_frame_hash_sequence_sha256": hashlib.sha256(
            sequence.encode("ascii")).hexdigest(),
        "artifacts": [
            {"path": clip.name, "sha256": sha(clip), "bytes": clip.stat().st_size},
            {"path": sheet_path.name, "sha256": sha(sheet_path),
             "bytes": sheet_path.stat().st_size},
        ],
        "physical_saturn": "UNRUN",
        "result": "PASS",
    }
    (output / "mcp-visual-qa.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="ascii")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.manifest.resolve(), args.output.resolve()),
                     sort_keys=True))


if __name__ == "__main__":
    main()
