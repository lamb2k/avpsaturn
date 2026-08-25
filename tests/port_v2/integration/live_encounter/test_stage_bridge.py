#!/usr/bin/env python3
"""Focused REPAIR-11 live camera to captured VDP2-plane contract."""

from pathlib import Path
import json
import re


ROOT = Path(__file__).resolve().parents[4]
MAIN = (ROOT / "main.c").read_text(encoding="utf-8")
MANIFEST = json.loads((ROOT / "data/rp4_street_planes.json").read_text(
    encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def out_of(source_x: int) -> int:
    return (source_x * 351 - 175 + 382) // 383


def scroll3_for_scroll2(scroll2_x: int) -> int:
    # Captured register knots covering the bounded live camera range and the
    # final endpoint. The production helper reads these values from STRIPS.BIN.
    knots = ((768, 104), (779, 113), (789, 122), (799, 131), (944, 258))
    previous_x, previous_y = knots[0]
    if scroll2_x <= previous_x:
        return previous_y
    for current_x, current_y in knots[1:]:
        if scroll2_x <= current_x:
            span = current_x - previous_x
            offset = scroll2_x - previous_x
            delta = current_y - previous_y
            return previous_y + (offset * delta + span // 2) // span
        previous_x, previous_y = current_x, current_y
    return previous_y


def plane_scrolls(camera_world_x: int) -> tuple[int, int]:
    scroll2_origin = MANIFEST["planes"]["scroll2"]["world_x0"]
    scroll3_origin = MANIFEST["planes"]["scroll3"]["world_x0"]
    scroll3_x = scroll3_for_scroll2(camera_world_x)
    return (
        out_of(camera_world_x + 64) - out_of(scroll2_origin),
        out_of(scroll3_x + 64) - out_of(scroll3_origin),
    )


def main() -> None:
    require(MANIFEST["planes"]["scroll2"]["world_x0"] == 832 and
            MANIFEST["planes"]["scroll3"]["world_x0"] == 160,
            "captured plane origins drifted")
    require(plane_scrolls(768) == (0, 7),
            f"opening plane bridge drifted: {plane_scrolls(768)}")
    require(plane_scrolls(790) == (20, 24),
            f"post-unlock plane bridge drifted: {plane_scrolls(790)}")
    require(plane_scrolls(768) != (768, 384),
            "raw-camera corruption control did not reject")

    patterns = (
        r"static int street_scroll3_for_scroll2\(const int scroll2_x\)",
        r"street_scroll3_for_scroll2\(live_scroll2_x\)",
        r"street_out_of\(live_scroll2_x \+ 64\)\s*-\s*"
        r"street_out_of\(street_plane\[0\]\.world_x0\)",
        r"street_out_of\(live_scroll3_x \+ 64\)\s*-\s*"
        r"street_out_of\(street_plane\[1\]\.world_x0\)",
    )
    for pattern in patterns:
        require(re.search(pattern, MAIN) is not None,
                f"live stage bridge missing: {pattern}")
    require("scx0 = live_encounter_runtime.camera_world_x;" not in MAIN and
            "scx1 = live_encounter_runtime.camera_world_x / 2;" not in MAIN,
            "raw-camera corruption bridge returned")
    print("REPAIR-11 live stage bridge: PASS")


if __name__ == "__main__":
    main()
