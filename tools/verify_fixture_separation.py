#!/usr/bin/env python3
"""RP4 fixture/production separation gate.

The captured street object schedule and strips (STRIPS.BIN) are a
validation fixture: they exist to prove the two-plane renderer against
source truth and must never become production runtime payload. This gate
fails if:

  1. any reference to the fixture in main.c lies outside an
     AVSP_STREET_TEST conditional block;
  2. the tracked manifest loses its fixture_role classification;
  3. a non-StreetTest build profile has the fixture staged into the ISO
     content root (build/avsp_cd/ST1).
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
    if "VALIDATION FIXTURE ONLY" not in manifest.get("fixture_role", ""):
        fail("rp4_street_planes.json lost its fixture_role classification")

    profile_stamp = ROOT / "build" / "last_compile_profile.txt"
    staged = ROOT / "build" / "avsp_cd" / "ST1" / "STRIPS.BIN"
    if profile_stamp.exists():
        profile = profile_stamp.read_text().strip()
        if "street-test" not in profile and staged.exists():
            fail(f"fixture staged into the ISO root under profile "
                 f"'{profile}'")

    print("fixture separation OK: fixture references are StreetTest-only, "
          "manifest classified, staging matches the build profile")


if __name__ == "__main__":
    main()
