#!/usr/bin/env python3
"""Guards for the RP4 direct-order result and its residency contradiction.

These lock in the two measured facts that ended this body, so neither can
be lost or quietly reinterpreted:

* the sorted submission path DOES carry the emission order into the final
  VDP1 command sequence, which falsifies the premise the body started
  from;
* no submission seam can preserve the texture-content invariant, because
  every fixture frame needs more distinct resident textures than Jo
  Engine's entire sprite-definition table.

The residency numbers are recomputed from the fixture here rather than
read back from the manifest, so the manifest cannot drift away from the
fixture it claims to describe. If the tile residency is ever fixed, this
test is expected to fail and must be updated deliberately - that is the
point of asserting the contradiction rather than tolerating it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from rp4_source_groups import frame_tile_demand, objects_offset  # noqa: E402

MANIFEST = ROOT / "data" / "rp4_direct_order.json"
STRIPS = ROOT / "build" / "rp4_fixture" / "STRIPS.BIN"
JO_MAX_SPRITE = 255
TILE_SPRITE_POOL = 96


def check_manifest_shape(report: dict) -> None:
    assert report["schema"] == "rp4-direct-order-v0", report["schema"]
    assert report["decision_table_result"] == "D", report
    assert report["rp4_v1_status"] == "FALSIFIED", report
    assert report["capability_gate_1"] == "0/7", report
    for blocked in ("cmdcolr_priority_selector",
                    "sprite_priority_register_effect"):
        assert blocked in report["controls_not_promoted"], report
    # No raw evidence may leak into the tracked manifest.
    text = json.dumps(report)
    assert "commands" not in report, "raw command list must stay ignored"
    assert len(text) < 200_000, "tracked manifest is carrying bulk data"


def check_sorted_path_controls_order(report: dict) -> None:
    """The falsified premise, stated as an assertion."""
    builds = report["builds"]
    assert builds["sorted_reverse"]["witness_direction"] == \
        "earlier_cps_entry_later_in_vdp1", builds["sorted_reverse"]
    assert builds["sorted_forward"]["witness_direction"] == \
        "earlier_cps_entry_earlier_in_vdp1", builds["sorted_forward"]
    # Reversing the loop must actually change the final sequence.
    pair = report["comparisons"]["sorted_reverse_vs_forward"]
    assert not pair["same_draw_order"], pair
    assert report["falsified_premise"]["status"] == \
        "FALSIFIED_BY_FRAME_PINNED_MEASUREMENT", report["falsified_premise"]


def check_immediate_path_is_not_a_substitute(report: dict) -> None:
    builds = report["builds"]
    sorted_count = builds["sorted_reverse"]["command_count"]
    immediate_count = builds["immediate_reverse"]["command_count"]
    assert immediate_count != sorted_count, (sorted_count, immediate_count)
    cross = report["comparisons"]["sorted_vs_immediate_same_loop"]
    assert not cross["same_command_count"], cross
    assert not cross["same_identity_multiset"], cross
    for name in ("immediate_reverse", "immediate_forward"):
        assert builds[name]["witness_direction"] == "not_uniquely_joinable", \
            builds[name]


def check_production_behaviour_unchanged(report: dict) -> None:
    unchanged = report["unchanged_production_behavior"]
    assert unchanged["default_build_command_table_matches_pristine"], unchanged


def check_residency_contradiction(report: dict) -> None:
    """Recompute the residency demand straight from the fixture."""
    strips = STRIPS.read_bytes()
    _, frames = objects_offset(strips)
    demands = [frame_tile_demand(strips, rel)["distinct_tiles"]
               for rel in range(frames)]

    recorded = report["texture_residency"]
    assert recorded["fixture_frames"] == frames, recorded
    assert recorded["distinct_tiles_min"] == min(demands), recorded
    assert recorded["distinct_tiles_max"] == max(demands), recorded
    assert recorded["tile_sprite_pool_slots"] == TILE_SPRITE_POOL, recorded
    assert recorded["jo_max_sprite_table"] == JO_MAX_SPRITE, recorded

    over_pool = sum(1 for d in demands if d > TILE_SPRITE_POOL)
    over_table = sum(1 for d in demands if d > JO_MAX_SPRITE)
    assert recorded["frames_over_pool"] == over_pool, recorded
    assert recorded["frames_over_jo_sprite_table"] == over_table, recorded

    # The contradiction itself: it is not a marginal overrun.
    assert over_pool == frames, (over_pool, frames)
    assert over_table == frames, (over_table, frames)
    assert min(demands) > JO_MAX_SPRITE, min(demands)


def main() -> None:
    report = json.loads(MANIFEST.read_text())
    check_manifest_shape(report)
    check_sorted_path_controls_order(report)
    check_immediate_path_is_not_a_substitute(report)
    check_production_behaviour_unchanged(report)
    check_residency_contradiction(report)
    print("rp4 direct order: sorted path carries order; texture residency "
          "exceeds the Jo sprite table on every fixture frame")


if __name__ == "__main__":
    main()
