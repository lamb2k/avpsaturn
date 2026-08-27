#!/usr/bin/env python3
"""RP4 fixture/production separation gate.

STRIPS.BIN is a hybrid source-derived stage package.  Its two background
planes, palette/scroll records, and patches are retained presentation data for
the playable slice.  Its captured foreground object schedule remains a
validation fixture and must never become production gameplay authority.  This
gate fails if:

  1. any reference to the fixture in main.c lies outside an
     AVSP_STREET_TEST conditional block;
  2. the tracked manifest loses its fixture_role classification;
  3. a profile which does not own the street presentation package has it
     staged into the ISO content root (build/avsp_cd/ST1);
  4. the playable slice loses the compile-time guard which prevents the
     captured object schedule from being replayed.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> None:
    source = (ROOT / "main.c").read_text(errors="replace").splitlines()
    depth = 0
    street_depth = None
    for number, line in enumerate(source, 1):
        stripped = line.strip()
        if stripped.startswith("#ifdef") or stripped.startswith("#ifndef") \
                or stripped.startswith("#if "):
            depth += 1
            if "AVSP_STREET_TEST" in stripped and \
                    stripped.startswith("#ifdef") and street_depth is None:
                street_depth = depth
        elif stripped.startswith("#endif"):
            if street_depth is not None and depth == street_depth:
                street_depth = None
            depth -= 1
        if "STRIPS.BIN" in line or "rp4_fixture" in line:
            if street_depth is None:
                fail(f"main.c:{number} references the RP4 fixture outside "
                     f"an AVSP_STREET_TEST block")

    manifest = json.loads(
        (ROOT / "data" / "rp4_street_planes.json").read_text())
    role = manifest.get("fixture_role", "")
    if ("HYBRID SOURCE-DERIVED STAGE PACKAGE" not in role or
            "captured foreground object schedule remains validation-only" not
            in role):
        fail("rp4_street_planes.json lost its fixture_role classification")

    joined_source = "\n".join(source)
    if ("#ifndef AVSP_PLAYABLE_SLICE\n"
            "    objects = street_object_frame_offset[rel];" not in
            joined_source):
        fail("playable slice can replay the captured foreground object schedule")

    profile_stamp = ROOT / "build" / "last_compile_profile.txt"
    staged = ROOT / "build" / "avsp_cd" / "ST1" / "STRIPS.BIN"
    if profile_stamp.exists():
        profile = profile_stamp.read_text().strip()
        presentation_profiles = (
            "street-test",
            "camera-stage-salvage-bench",
            "camera-stage-promotion-bench",
            "playable-slice",
            "normal-release",
            "live-encounter",
            "live-encounter-bench",
        )
        owns_stage_package = any(
            profile.endswith(f"-{name}") for name in presentation_profiles)
        if owns_stage_package != staged.exists():
            condition = "missing from" if owns_stage_package else "staged into"
            fail(f"street presentation package {condition} profile '{profile}'")

    print("fixture separation OK: captured actors remain validation-only, "
          "manifest classified, presentation staging matches the build profile")


if __name__ == "__main__":
    main()
