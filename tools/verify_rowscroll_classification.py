#!/usr/bin/env python3
"""SP10 gate: structural consistency of the row-scroll classification.

Capture-free checks against the tracked census:

1. every census group has a verdict and the ranges match;
2. verdict booleans recompute from the recorded counts
   (requires_line_scroll == distinct_visible_frames > 0);
3. a scene with zero enabled frames cannot require line scroll;
4. the street group cross-check fields are consistent;
5. negative controls: a flipped verdict and a range drift must be
   detected.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check(report: dict, census: dict) -> list[str]:
    errors: list[str] = []
    scenes = report["scenes"]
    groups = census["groups"]
    if len(scenes) != len(groups):
        errors.append("scene count diverges from census")
        return errors
    for group in groups:
        sid = group["provisional_scene_id"]
        entry = scenes.get(sid)
        if entry is None:
            errors.append(f"{sid}: missing verdict")
            continue
        if entry["first_frame"] != group["first_frame"] or \
                entry["last_frame"] != group["last_frame"]:
            errors.append(f"{sid}: range diverges from census")
        expected = entry["distinct_visible_frames"] > 0
        if entry["requires_line_scroll"] != expected:
            errors.append(f"{sid}: verdict does not recompute")
        if entry["enabled_frames"] == 0 and entry["requires_line_scroll"]:
            errors.append(f"{sid}: requires line scroll without any "
                          f"enabled frame")
    street = report["rp4_street_group"]
    if scenes[street]["requires_line_scroll"] != \
            report["rp4_street_requires_line_scroll"]:
        errors.append("street cross-check fields inconsistent")
    listed = set(report["line_scroll_scenes"])
    actual = {sid for sid, entry in scenes.items()
              if entry["requires_line_scroll"]}
    if listed != actual:
        errors.append("line_scroll_scenes list diverges from verdicts")
    return errors


def main() -> None:
    report = json.loads(
        (ROOT / "data" / "round1_rowscroll_classification.json").read_text())
    census = json.loads(
        (ROOT / "data" / "round1_route_census.json").read_text())
    errors = check(report, census)
    if errors:
        for error in errors[:20]:
            print("FAIL:", error)
        raise SystemExit(1)

    controls = {}
    mutated = copy.deepcopy(report)
    sid = mutated["line_scroll_scenes"][0]
    mutated["scenes"][sid]["requires_line_scroll"] = False
    controls["flipped_verdict"] = bool(check(mutated, census))
    mutated = copy.deepcopy(report)
    first = next(iter(mutated["scenes"].values()))
    first["first_frame"] += 1
    controls["range_drift"] = bool(check(mutated, census))

    failed = [name for name, detected in controls.items() if not detected]
    print(f"rowscroll classification: {len(report['scenes'])} scenes, "
          f"{len(report['line_scroll_scenes'])} require line scroll, "
          f"controls {'PASS' if not failed else 'FAIL ' + ','.join(failed)}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
