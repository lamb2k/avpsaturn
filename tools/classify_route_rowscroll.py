#!/usr/bin/env python3
"""SP10/RP7: classify row-scroll usage across the complete captured route.

For every census group, scan the private cadence-1 capture and measure the
scroll2 row-scroll table where the hardware would actually apply it:

- enabled: CPS-A register 0x22 bit 0 (row-scroll enable) per frame;
- visible values: the per-scanline words indexed by
  (raw_y + row_scroll_offset) & 0x3FF for the 224 visible lines;
- spread: max - min of the visible values on enabled frames.

A group requires Saturn line scroll only when some enabled frame shows a
non-constant visible table (spread > 0). A constant non-zero table is a
whole-layer offset (normal scroll); a disabled or zero table needs
nothing.

Output: data/round1_rowscroll_classification.json (per-group verdicts and
measured spreads only). The RP4 interval's constant-zero result is
re-derived here as a cross-check.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from census_full_route import RouteState  # noqa: E402

CAPTURE = ROOT / ".deps" / "mame" / "full_route"
CENSUS = ROOT / "data" / "round1_route_census.json"
MANIFEST = ROOT / "data" / "avsp_scene_manifest.json"
OUTPUT = ROOT / "data" / "round1_rowscroll_classification.json"

VIS_TOP = 16
VIS_H = 224


def main() -> None:
    census = json.loads(CENSUS.read_text())
    groups = census["groups"]
    manifest = json.loads(MANIFEST.read_text())
    runtime_by_provisional = {
        scene["provisional_scene_id"]: scene["runtime_scene_id"]
        for scene in manifest["scenes"]}
    missing = [g["provisional_scene_id"] for g in groups
               if g["provisional_scene_id"] not in runtime_by_provisional]
    if missing:
        raise SystemExit(f"census groups absent from the scene manifest: "
                         f"{missing[:5]}")
    state = RouteState(CAPTURE)

    results = {g["provisional_scene_id"]: {
        "first_frame": g["first_frame"],
        "last_frame": g["last_frame"],
        "enabled_frames": 0,
        "distinct_visible_frames": 0,
        "max_spread": 0,
        "max_abs_value": 0,
    } for g in groups}
    order = [g["provisional_scene_id"] for g in groups]
    bounds = {g["provisional_scene_id"]: (g["first_frame"], g["last_frame"])
              for g in groups}

    cursor = 0
    for rec in state.frames():
        frame = rec["frame"]
        while cursor < len(order) and frame > bounds[order[cursor]][1]:
            cursor += 1
        if cursor >= len(order):
            break
        sid = order[cursor]
        cps_a = rec["cps_a"]
        if not (cps_a[17] & 1):
            continue
        entry = results[sid]
        entry["enabled_frames"] += 1
        base = (((cps_a[4] * 256) & 0x3FFFF) & ~(0x800 - 1))
        offset = cps_a[16]
        table = state.gfx_slice(base, 0x800)
        values = []
        for y in range(VIS_TOP, VIS_TOP + VIS_H):
            at = (((y + offset) & 0x3FF) * 2) % 0x800
            values.append(int.from_bytes(table[at:at + 2], "big"))
        spread = max(values) - min(values)
        if spread:
            entry["distinct_visible_frames"] += 1
            entry["max_spread"] = max(entry["max_spread"], spread)
        entry["max_abs_value"] = max(entry["max_abs_value"],
                                     max(values, key=abs), key=abs)

    scenes = {}
    line_scroll_scenes = []
    for sid in order:
        entry = results[sid]
        requires = entry["distinct_visible_frames"] > 0
        entry["requires_line_scroll"] = requires
        entry["provisional_scene_id"] = sid
        rid = runtime_by_provisional[sid]
        if requires:
            line_scroll_scenes.append(rid)
        # Keyed by the 16-bit runtime_scene_id (the one identity the
        # runtime interface accepts); the provisional 0x80xx value stays
        # inside the entry as census provenance.
        scenes[str(rid)] = entry

    # Cross-check: the RP4 street interval (3474..3674) sits inside the
    # street group and was measured constant-zero at selection time.
    street = runtime_by_provisional[next(
        sid for sid in order if bounds[sid][0] <= 3474 <= bounds[sid][1])]
    report = {
        "schema": "round1-rowscroll-classification-v1",
        "scene_id_namespace": "runtime_scene_id (see "
                              "data/avsp_scene_manifest.json); "
                              "provisional IDs kept as provenance",
        "source_census_sha256": manifest["source_census_sha256"],
        "classification": "per-scene row-scroll verdicts; counts and "
                          "spreads only",
        "route": census["route"],
        "scenes": scenes,
        "line_scroll_scenes": line_scroll_scenes,
        "rp4_street_group": street,
        "rp4_street_requires_line_scroll":
            scenes[str(street)]["requires_line_scroll"],
    }
    OUTPUT.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n",
                      encoding="ascii", newline="\n")
    print(f"rowscroll classification: {len(order)} scenes, "
          f"{len(line_scroll_scenes)} require line scroll: "
          f"{line_scroll_scenes}; street group {street} requires: "
          f"{scenes[str(street)]['requires_line_scroll']}")


if __name__ == "__main__":
    main()
