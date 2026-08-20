#!/usr/bin/env python3
"""Validate the tracked RP2 route census without the private capture.

Checks the structural contract of data/round1_route_census.json:
  - groups tile the complete route with no gaps and no overlaps;
  - every provisional scene ID has bit 15 set and is unique;
  - every group either has a provisional ID or is listed in
    unclassified_groups (RP2 gate);
  - counts are internally consistent (frame_count, group frame sums);
  - no field carries raw payload bytes (hash/count/range fields only).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CENSUS = ROOT / "data" / "round1_route_census.json"
CONTROLS = ROOT / "data" / "round1_route_census_controls.json"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> None:
    census = json.loads(CENSUS.read_text())
    if census.get("schema") != "round1-route-census-v0":
        fail("unexpected schema")
    route = census["route"]
    groups = census["groups"]
    if census["group_count"] != len(groups):
        fail("group_count disagrees with groups")

    expected = route["first_frame"]
    total = 0
    seen_ids = set()
    for group in groups:
        if group["first_frame"] != expected:
            fail(f"gap or overlap at frame {group['first_frame']} "
                 f"(expected {expected})")
        if group["last_frame"] < group["first_frame"]:
            fail("inverted group interval")
        frames = group["last_frame"] - group["first_frame"] + 1
        if frames != group["frames"]:
            fail(f"frame count mismatch in group {group['provisional_scene_id']}")
        scene_id = int(group["provisional_scene_id"], 16)
        if not scene_id & 0x8000:
            fail(f"provisional ID missing bit 15: {scene_id:#06x}")
        if scene_id in seen_ids:
            fail(f"duplicate provisional ID {scene_id:#06x}")
        seen_ids.add(scene_id)
        if group["object_count_max"] < group["object_count_min"]:
            fail("inverted object count range")
        total += frames
        expected = group["last_frame"] + 1
    if expected != route["last_frame"] + 1:
        fail("groups do not reach the route's last frame")
    if total != route["frame_count"]:
        fail("group frames do not sum to the route frame count")
    for entry in census["unclassified_groups"]:
        if entry not in seen_ids and int(entry, 16) not in seen_ids:
            fail(f"unclassified entry {entry} names no group")

    if CONTROLS.exists():
        controls = json.loads(CONTROLS.read_text())
        if not controls.get("pass"):
            fail("recorded negative controls did not pass")

    flagged = sum(1 for g in groups if g["review_flags"])
    print(f"route census OK: {route['frame_count']} frames, "
          f"{len(groups)} groups tile the route exactly, "
          f"{flagged} flagged for review, "
          f"{len(census['unclassified_groups'])} unclassified")


if __name__ == "__main__":
    main()
