#!/usr/bin/env python3
"""Focused controls for the minimal actor-image comparator."""

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "actor_image_compare", HERE / "actor_image_compare.py")
comparator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparator)


def main() -> None:
    report = comparator.generate()
    allowed_flags = {"record_change_without_visible_change"}
    if any(set(item["flags"]) - allowed_flags
           for item in report["baseline_flags"]):
        raise AssertionError(
            f"actor-image comparison found an objective mismatch: "
            f"{report['baseline_flags'][:10]}")
    inspection_path = comparator.OUTPUT / "actor-image-direct-inspection.json"
    if not inspection_path.is_file():
        raise AssertionError("flagged actor pairs await direct inspection")
    import json
    inspection = json.loads(inspection_path.read_text(encoding="utf-8"))
    expected_pairs = {(item["actor"], item["frame"])
                      for item in report["baseline_flags"]}
    actual_pairs = {(item["actor"], item["frame"])
                    for item in inspection["findings"]}
    if inspection["result"] != "PASS" or actual_pairs != expected_pairs:
        raise AssertionError("direct inspection does not cover every flag")
    expected = {
        "valid_wrong_alien_crop", "one_frame_y_offset",
        "stale_repeated_pose", "skipped_reaction_pose", "pivot_jump",
    }
    controls = report["negative_controls"]
    if {item["name"] for item in controls} != expected or \
            any(item["result"] != "REJECTED" for item in controls):
        raise AssertionError("an actor-image negative control escaped")
    print("INTEGRATE-03 actor-image comparator: PASS")


if __name__ == "__main__":
    main()
