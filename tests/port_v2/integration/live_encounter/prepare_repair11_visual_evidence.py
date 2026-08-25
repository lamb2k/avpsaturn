#!/usr/bin/env python3
"""Package the directly inspected REPAIR-11 opening/post-unlock views."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = ROOT / "build/feedback/REPAIR-11-LIVE-BACKGROUND-PRESENTATION"
OPENING = PACKAGE / "opening-frame-paused.png"
POST_UNLOCK = PACKAGE / "post-unlock-paused.png"
FONT = ImageFont.load_default()


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def aperture(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB")
    require(image.size == (816, 718), f"unexpected capture size: {image.size}")
    return image.crop((8, 150, 808, 658)).resize(
        (352, 224), Image.Resampling.NEAREST
    )


def label(image: Image.Image, text: str) -> Image.Image:
    result = image.copy()
    draw = ImageDraw.Draw(result)
    bounds = draw.textbbox((0, 0), text, font=FONT)
    draw.rectangle((3, 3, bounds[2] + 9, bounds[3] + 9), fill=(0, 0, 0))
    draw.text((6, 6), text, font=FONT, fill=(255, 255, 255))
    return result


require(OPENING.is_file(), f"missing {OPENING}")
require(POST_UNLOCK.is_file(), f"missing {POST_UNLOCK}")
opening = aperture(OPENING)
post_unlock = aperture(POST_UNLOCK)
strip = Image.new("RGB", (704, 224), "black")
strip.paste(label(opening, "opening f53 camera=768 planes=[0,7]"), (0, 0))
strip.paste(
    label(post_unlock, "post-unlock camera=881 planes=[103,97]"), (352, 0)
)
strip_path = PACKAGE / "opening-post-unlock-strip.png"
strip.save(strip_path)

head = subprocess.run(
    ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()
manifest = {
    "schema": 1,
    "task": "REPAIR-11-LIVE-BACKGROUND-PRESENTATION",
    "candidate": head,
    "normalized_diagnostic_iso_sha256":
        "9b900cffdd0da0d44069f704059c258787e2a0066300be6f2534cf0635df51ba",
    "capture_method": (
        "Computer Use direct inspection plus process-bound Windows window capture"
    ),
    "captures": [
        {
            "label": "opening-and-current-paused-boundary",
            "gameplay_frame": 53,
            "camera_world_x": 768,
            "plane_scroll_x": [0, 7],
            "path": OPENING.relative_to(ROOT).as_posix(),
            "sha256": sha256(OPENING),
            "bytes": OPENING.stat().st_size,
        },
        {
            "label": "stable-post-unlock",
            "observed_gameplay_frame": 5713,
            "camera_world_x": 881,
            "plane_scroll_x": [103, 97],
            "path": POST_UNLOCK.relative_to(ROOT).as_posix(),
            "sha256": sha256(POST_UNLOCK),
            "bytes": POST_UNLOCK.stat().st_size,
        },
    ],
    "derived_artifact": {
        "path": strip_path.relative_to(ROOT).as_posix(),
        "sha256": sha256(strip_path),
        "bytes": strip_path.stat().st_size,
    },
    "inspection": {
        "opening_camera_position": "PASS",
        "paused_frame_around_52": "PASS at fully paused diagnostic frame 53",
        "player_movement_across_viewport": "PASS",
        "post_unlock_camera_movement": "PASS",
        "left_and_right_visible_edges": "PASS for both VDP2 planes",
        "plane_corruption": "ABSENT",
        "measured_relative_scroll": (
            "PASS; scroll2 delta 103 and scroll3 delta 90"
        ),
        "raw_pnt_offset_displacement": "ABSENT",
        "player_alien_camera_coherence": "PASS",
        "reviewed_attack_sequence_regression": "PASS; unchanged 471-frame ledger",
        "class_0x1f_tracking_regression": "PASS; unchanged 471-frame ledger",
        "hud_audio_palette_priority_residency_gameplay_regression": "ABSENT",
    },
    "neutral_facing_release": "UNRESOLVED_FOR_ROUND1_PLAYER_AUTHORITY",
    "user09": "CHANGES_REQUESTED",
    "frontend_active": False,
    "physical_saturn": "UNRUN",
    "result": "PASS",
}
manifest_path = PACKAGE / "visual-evidence.json"
manifest_path.write_text(
    json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="ascii"
)
print(json.dumps(manifest, sort_keys=True))
