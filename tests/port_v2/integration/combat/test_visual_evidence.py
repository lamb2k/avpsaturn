#!/usr/bin/env python3
"""Validate the reusable cadence-1 REPAIR-09 visual-QA package."""

import json
import hashlib
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
PACKAGE = ROOT / "build/feedback/REPAIR-09-SOURCE-BOUND-COMBAT-PRESENTATION"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    trace = json.loads((PACKAGE / "saturn-cadence-1-trace.json").read_text())
    repeat = json.loads((PACKAGE / "saturn-cadence-1-trace-run-2.json").read_text())
    findings = json.loads((PACKAGE / "visual-findings.json").read_text())
    timing = json.loads((PACKAGE / "attack-timing-comparison.json").read_text())
    grounding = json.loads((PACKAGE / "player-grounding-trace.json").read_text())
    require(len(trace["frames"]) == 297 and
            trace["source_frame_range"] == [5173, 5469],
            "cadence-1 trace is incomplete")
    require([item["state"] for item in trace["frames"]] ==
            [item["state"] for item in repeat["frames"]],
            "paired cadence-1 semantic traces differ")
    for first, second in zip(trace["frames"], repeat["frames"]):
        left = PACKAGE / "saturn-frames" / f"{first['source_frame']:05d}.png"
        right = PACKAGE / "saturn-frames-run-2" / f"{second['source_frame']:05d}.png"
        require(hashlib.sha256(left.read_bytes()).digest() ==
                hashlib.sha256(right.read_bytes()).digest(),
                f"paired cadence-1 pixels differ at {first['source_frame']}")
    require(findings["result"] == "PASS" and
            not findings["identity_mismatch_frames"] and
            not findings["missing_actor_frames"] and
            not findings["player_grounding_mismatch_frames"],
            "visual findings contain an unresolved objective defect")
    require(len(timing) == 4 and
            [row["selector"] for row in timing] == [1, 2, 3, 4] and
            all(row["difference_frames"] == 0 for row in timing),
            "source event timing drifted")
    require(len(grounding) == 297, "grounding trace is incomplete")
    for name in ("alien-visual-family-comparison.png",
                 "source-vs-saturn-temporal-strips.png",
                 "collision-overlay-1.png", "collision-overlay-2.png",
                 "collision-overlay-3.png", "collision-overlay-4.png"):
        path = PACKAGE / name
        require(path.is_file(), f"missing visual artifact {name}")
        with Image.open(path) as image:
            require(image.width >= 704 and image.height >= 224,
                    f"visual artifact {name} is truncated")
    require((PACKAGE / "source-full-speed.webp").is_file() and
            (PACKAGE / "saturn-full-speed.webp").is_file() and
            (PACKAGE / "source-vs-saturn-slow-motion.webp").is_file(),
            "review clips are missing")
    print("REPAIR-09 cadence-1 image evidence: PASS")


if __name__ == "__main__":
    main()
