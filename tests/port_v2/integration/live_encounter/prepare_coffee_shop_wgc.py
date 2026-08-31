#!/usr/bin/env python3
"""Package the exact Coffee Shop frame-2280..2310 WGC cadence."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[4]
VIEWPORT = (1, 149, 801, 658)
FONT = ImageFont.load_default()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def aperture(path):
    image = Image.open(path).convert("RGB")
    if image.size != (802, 711):
        raise RuntimeError(f"unexpected WGC size for {path.name}: {image.size}")
    return image.crop(VIEWPORT).resize((352, 224), Image.Resampling.NEAREST)


def labelled(image, frame):
    result = image.copy()
    draw = ImageDraw.Draw(result)
    text = f"source visible frame {frame}"
    box = draw.textbbox((0, 0), text, font=FONT)
    draw.rectangle((2, 2, box[2] + 8, box[3] + 8), fill="black")
    draw.text((5, 5), text, font=FONT, fill="white")
    return result


parser = argparse.ArgumentParser()
parser.add_argument("--first", type=int, default=2280)
parser.add_argument("--last", type=int, default=2310)
parser.add_argument("--frames", type=int, nargs="+")
parser.add_argument("--focus-frame", type=int)
parser.add_argument(
    "--package",
    default=("build/feedback/REIMPLEMENT-13-COFFEE-SHOP-SCENE-PARITY/"
             "wgc-2280-2310"),
)
args = parser.parse_args()
if args.frames:
    if args.first != 2280 or args.last != 2310:
        raise ValueError("choose an explicit frame list or a frame range")
    FRAMES = tuple(args.frames)
    if (not FRAMES or any(frame < 0 for frame in FRAMES) or
            any(right <= left for left, right in zip(FRAMES, FRAMES[1:]))):
        raise ValueError("Coffee Shop WGC frames must be increasing")
else:
    if args.first < 0 or args.last < args.first:
        raise ValueError("invalid Coffee Shop WGC frame range")
    FRAMES = tuple(range(args.first, args.last + 1))
if args.focus_frame is not None and args.focus_frame not in FRAMES:
    raise ValueError("focus frame must be inside the WGC frame range")
PACKAGE = ROOT / args.package

paths = [PACKAGE / f"source-frame-{frame}.png" for frame in FRAMES]
missing = [path.name for path in paths if not path.is_file()]
if missing:
    raise RuntimeError(f"missing Coffee Shop WGC frames: {missing}")
images = [aperture(path) for path in paths]

clip = PACKAGE / f"source-frames-{FRAMES[0]}-{FRAMES[-1]}.webp"
images[0].save(clip, save_all=True, append_images=images[1:],
               duration=17, loop=0, lossless=True, method=6)

columns = min(8, len(images))
rows = (len(images) + columns - 1) // columns
sheet = Image.new("RGB", (columns * 352, rows * 224), "black")
for index, (frame, image) in enumerate(zip(FRAMES, images)):
    sheet.paste(labelled(image, frame),
                ((index % columns) * 352, (index // columns) * 224))
sheet_path = PACKAGE / "cadence-1-contact-sheet.png"
sheet.save(sheet_path)

source_commit = subprocess.run(
    ["git", "-C", str(ROOT), "rev-parse", "HEAD"], check=True,
    capture_output=True, text=True).stdout.strip()
report = {
    "schema": 1,
    "task": "REIMPLEMENT-13-SOURCE-CLOSED-ROUND1",
    "source_commit": source_commit,
    "capture_method": "Windows.Graphics.Capture via @oai/sky",
    "source_visible_frame_range": [FRAMES[0], FRAMES[-1]],
    "focus_frame": args.focus_frame,
    "capture_count": len(paths),
    "captures": [
        {"source_visible_frame": frame,
         "path": path.relative_to(ROOT).as_posix(),
         "sha256": sha(path), "bytes": path.stat().st_size}
        for frame, path in zip(FRAMES, paths)
    ],
    "artifacts": [
        {"path": path.relative_to(ROOT).as_posix(),
         "sha256": sha(path), "bytes": path.stat().st_size}
        for path in (clip, sheet_path)
    ],
    "physical_saturn": "UNRUN",
    "result": "PASS",
}
(PACKAGE / "wgc-evidence.json").write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="ascii")
print(json.dumps(report, sort_keys=True))
