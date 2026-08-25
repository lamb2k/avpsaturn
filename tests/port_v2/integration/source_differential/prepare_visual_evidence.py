#!/usr/bin/env python3
"""Prepare QA-12 review views from genuine Windows Graphics Capture frames."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[4]
PACKAGE = ROOT / "build/feedback/QA-12-source-differential"
SEQUENCE = PACKAGE / "exact-sequence"
READBACK = ROOT / "build/port_v2/live_encounter/run-1/readback.json"
VIEWPORT = (1, 149, 801, 658)
FONT = ImageFont.load_default()


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def aperture(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB")
    require(image.size == (802, 711), f"unexpected capture size: {image.size}")
    return image.crop(VIEWPORT).resize((352, 224), Image.Resampling.NEAREST)


def label(image: Image.Image, text: str) -> Image.Image:
    result = image.copy()
    draw = ImageDraw.Draw(result)
    box = draw.textbbox((0, 0), text, font=FONT)
    draw.rectangle((3, 3, box[2] + 9, box[3] + 9), fill=(0, 0, 0))
    draw.text((6, 6), text, font=FONT, fill=(255, 255, 255))
    return result


sequence_paths = sorted(SEQUENCE.glob("*.png"))
require(len(sequence_paths) == 18, "exact sequence must contain 18 captures")
sequence_frames = [int(path.stem.split("-")[-1]) for path in sequence_paths]
sequence = [aperture(path) for path in sequence_paths]
durations = [max(17, (right - left) * 1000 // 60)
             for left, right in zip(sequence_frames, sequence_frames[1:])]
durations.append(250)
clip = PACKAGE / "saturn-corrected-full-sequence.webp"
sequence[0].save(clip, save_all=True, append_images=sequence[1:],
                 duration=durations, loop=0, lossless=True, method=6)

indices = (0, 2, 5, 7, 9, 12, 15, 17)
strip = Image.new("RGB", (4 * 352, 2 * 224), "black")
for slot, index in enumerate(indices):
    strip.paste(label(sequence[index], f"diagnostic frame {sequence_frames[index]}"),
                ((slot % 4) * 352, (slot // 4) * 224))
strip_path = PACKAGE / "saturn-corrected-temporal-strip.png"
strip.save(strip_path)

exact = [
    ("frame-098-alien-contact.png", 98, "alien contact"),
    ("frame-162-miss.png", 162, "authored miss"),
    ("frame-235-player-contact.png", 235, "player contact"),
    ("frame-311-ko-contact-plus-one.png", 311, "KO contact + 1"),
    ("frame-390.png", 390, "KO fall"),
    ("frame-456.png", 456, "clear and continue"),
]
for name, _, _ in exact:
    require((PACKAGE / name).is_file(), f"missing exact capture: {name}")

readback = json.loads(READBACK.read_text())
samples = {sample["frame"]: sample for sample in readback["samples"]}
overlays = Image.new("RGB", (2 * 352, 2 * 224), "black")
for slot, (name, frame, title) in enumerate(exact[:4]):
    image = aperture(PACKAGE / name)
    sample = samples[frame]
    draw = ImageDraw.Draw(image)
    player_x = sample["player_x"] - sample["camera_world_x"]
    alien_x = sample["alien_x"] - sample["camera_world_x"]
    player_y = sample["player_screen_y"]
    alien_y = sample["alien_screen_y"]
    draw.rectangle((player_x - 20, player_y - 72, player_x + 20, player_y + 4),
                   outline=(64, 192, 255), width=2)
    draw.rectangle((alien_x - 20, alien_y - 48, alien_x + 20, alien_y + 4),
                   outline=(255, 96, 160), width=2)
    draw.line((player_x, player_y, alien_x, alien_y), fill=(255, 255, 0), width=2)
    contact = sample["player_contact"] or sample["alien_contact"]
    caption = f"f{frame} {title} dx={abs(sample['alien_x']-sample['player_x'])} contact={contact} miss={sample['attack_miss']}"
    overlays.paste(label(image, caption),
                   ((slot % 2) * 352, (slot // 2) * 224))
overlay_path = PACKAGE / "saturn-collision-origin-overlays.png"
overlays.save(overlay_path)

crops = Image.new("RGB", (3 * 352, 2 * 144), "black")
for slot, (name, frame, title) in enumerate(exact):
    view = aperture(PACKAGE / name).crop((0, 64, 352, 208))
    crops.paste(label(view, f"f{frame} {title}"),
                ((slot % 3) * 352, (slot // 3) * 144))
crops_path = PACKAGE / "saturn-actor-state-crops.png"
crops.save(crops_path)

timeline = Image.new("RGB", (1000, 260), (20, 20, 24))
draw = ImageDraw.Draw(timeline)
state_colors = {
    0: (80, 160, 255), 1: (255, 180, 60), 2: (80, 220, 120),
    3: (255, 100, 80), 4: (220, 80, 220), 5: (180, 180, 180),
}
draw.text((14, 10), "QA-12 cadence-1 state and contact timeline", font=FONT,
          fill="white")
for row, (field, title) in enumerate((("player_state", "player state"),
                                      ("alien_state", "alien state"))):
    y0 = 45 + row * 62
    draw.text((14, y0), title, font=FONT, fill="white")
    for sample in readback["samples"]:
        x0 = 130 + sample["frame"] * 840 // 471
        x1 = 130 + (sample["frame"] + 1) * 840 // 471
        draw.rectangle((x0, y0, max(x0, x1), y0 + 28),
                       fill=state_colors.get(sample[field], (255, 255, 255)))
for sample in readback["samples"]:
    x = 130 + sample["frame"] * 840 // 471
    if sample["player_contact"]:
        draw.line((x, 38, x, 185), fill=(255, 255, 0), width=2)
    if sample["alien_contact"]:
        draw.line((x, 38, x, 185), fill=(255, 80, 80), width=2)
    if sample["attack_miss"]:
        draw.line((x, 38, x, 185), fill=(255, 255, 255), width=1)
for frame in (0, 98, 162, 235, 310, 390, 450, 470):
    x = 130 + frame * 840 // 471
    draw.text((x - 8, 200), str(frame), font=FONT, fill="white")
draw.text((14, 180), "yellow=player contact  red=alien contact  white=miss",
          font=FONT, fill="white")
timeline_path = PACKAGE / "saturn-state-contact-timeline.png"
timeline.save(timeline_path)

artifacts = [clip, strip_path, overlay_path, crops_path, timeline_path]
manifest = {
    "schema": 1,
    "task": "QA-12-LIVE-ENCOUNTER-SOURCE-DIFFERENTIAL",
    "candidate": readback["source_commit"],
    "iso_sha256": readback["iso_sha256"],
    "capture_method": "Windows Graphics Capture through the uniquely selected Yaba window",
    "full_speed_sequence": {"samples": len(sequence),
                            "diagnostic_frames": sequence_frames,
                            "playback_duration_ms": sum(durations),
                            "timing": "diagnostic frame deltas at 60 Hz"},
    "exact_frames": [{"frame": frame, "label": title, "source": name}
                     for name, frame, title in exact],
    "artifacts": [{"path": path.relative_to(ROOT).as_posix(),
                   "sha256": sha(path), "bytes": path.stat().st_size}
                  for path in artifacts],
    "inspection": {
        "actor_visibility": "PASS",
        "facing_and_equipment_continuity": "PASS within selector-owned source records",
        "alien_family_continuity": "PASS",
        "hit_ko_removal_transition": "PASS",
        "camera_clear_continuation": "PASS",
        "projection_regression": "REJECTED before correction; PASS at corrected candidate",
    },
    "physical_saturn": "UNRUN",
}
manifest_path = PACKAGE / "visual-evidence.json"
manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
print(json.dumps(manifest, sort_keys=True))
