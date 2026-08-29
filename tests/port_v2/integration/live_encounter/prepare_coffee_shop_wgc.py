#!/usr/bin/env python3
"""Package the exact Coffee Shop frame-2280..2310 WGC cadence."""

import hashlib
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = (ROOT / "build/feedback/REIMPLEMENT-13-COFFEE-SHOP-SCENE-PARITY"
           / "wgc-2280-2310")
FRAMES = tuple(range(2280, 2311))
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


paths = [PACKAGE / f"source-frame-{frame}.png" for frame in FRAMES]
missing = [path.name for path in paths if not path.is_file()]
if missing:
    raise RuntimeError(f"missing Coffee Shop WGC frames: {missing}")
images = [aperture(path) for path in paths]

clip = PACKAGE / "source-frames-2280-2310.webp"
images[0].save(clip, save_all=True, append_images=images[1:],
               duration=17, loop=0, lossless=True, method=6)

sheet = Image.new("RGB", (8 * 352, 4 * 224), "black")
for index, (frame, image) in enumerate(zip(FRAMES, images)):
    sheet.paste(labelled(image, frame),
                ((index % 8) * 352, (index // 8) * 224))
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
    "scheduler_collision_frame": 2306,
    "impact_visible_frame": 2307,
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
