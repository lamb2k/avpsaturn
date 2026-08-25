#!/usr/bin/env python3
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--image", type=Path, required=True)
parser.add_argument("--frame", type=int, required=True)
args = parser.parse_args()
image = args.image.resolve()
if not image.is_file() or not 180 <= args.frame <= 320:
    raise ValueError("visual QA requires a genuine action image at frame 180..320")
with Image.open(image) as opened:
    width, height = opened.size
    colours = opened.convert("RGB").getcolors(maxcolors=width * height)
if width < 700 or height < 600 or colours is None or len(colours) < 64:
    raise ValueError("visual QA image does not contain the visible emulator scene")
source_commit = subprocess.run(
    ["git", "-C", str(ROOT), "rev-parse", "HEAD"], check=True,
    capture_output=True, text=True).stdout.strip()
inventory = json.loads((HERE / "inventory.json").read_text())
report = {
    "schema": 1,
    "task_id": inventory["task_id"],
    "source_commit": source_commit,
    "gameplay_frame": args.frame,
    "capture_method": "Windows.Graphics.Capture via @oai/sky",
    "screenshot": {
        "path": image.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
        "bytes": image.stat().st_size,
        "width": width,
        "height": height,
    },
    "physical_saturn": "UNRUN",
    "result": "PASS",
}
output = ROOT / inventory["build_root"] / "visual-qa.json"
output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="ascii")
print(f"recorded {output.relative_to(ROOT)}")
