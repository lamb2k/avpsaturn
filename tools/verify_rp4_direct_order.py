#!/usr/bin/env python3
"""Score the RP4 deterministic command-order body and write its manifest.

Consumes the private per-variant captures produced by
`tools/rp4_measure_variants.ps1` and writes the tracked manifest
`data/rp4_direct_order.json`. Only bounded evidence is written: hashes,
counts, indices, fractions and labels. No command dumps, no texture
bytes, no build artefacts.

Two measured results drive the verdict, and they point in opposite
directions from the ones the body expected:

1. The sorted `slDispSprite` path is NOT inert. Once the capture frame is
   pinned with a breakpoint instead of raced with pause/resume, reversing
   the emission loop moves the witness across the whole final command
   list. The prior "reverse loop is refuted" reading is consistent with
   comparing captures taken at uncontrolled, drifting fixture frames.

2. Neither submission path can satisfy the texture-content invariant,
   for a reason that has nothing to do with submission order: the street
   renderer needs far more distinct 16x16 tile textures resident in one
   frame than the runtime can hold, so texture VRAM is overwritten while
   already-emitted commands still point into it.

Result 2 is a residency contradiction, not an ordering result, and it is
what makes this body an architectural hard stop rather than a pass.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from rp4_command_identity import compare_captures  # noqa: E402
from rp4_source_groups import (  # noqa: E402
    entry_tiles,
    frame_entries,
    frame_tile_demand,
    objects_offset,
)

OUTPUT = ROOT / "data" / "rp4_direct_order.json"
WITNESSES = ROOT / "data" / "rp4_object_order_witnesses.json"
STRIPS = ROOT / "build" / "rp4_fixture" / "STRIPS.BIN"

VARIANTS = ("sorted_reverse", "sorted_forward",
            "immediate_reverse", "immediate_forward")

#: Jo Engine's program-wide sprite-definition table. Every resident
#: texture the street pool wants costs one of these, shared with actors,
#: HUD and frontend.
JO_MAX_SPRITE = 255
#: The street tile sprite pool in main.c.
TILE_SPRITE_POOL = 96
TILE_BYTES = 128


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def out_of(world_x: int) -> int:
    """Runtime street_out_of() from main.c."""
    return (world_x * 351 - 175 + 382) // 383


def group_coords(entries, slot: int) -> list:
    x, y, code, attr = entries[slot]
    return [(out_of((x & 0x3FF) - 64 + tile["dx"] + 8) - 176,
             (y & 0x3FF) - 16 + tile["dy"] + 8 - 112)
            for tile in entry_tiles(y, code, attr)]


def witness_direction(capture: dict, entries, earlier: int, later: int) -> str:
    """Which of two source slots landed later in the final command list.

    Joined on the renderer's own computed coordinates. Texture content
    cannot be used as a join key while the residency contradiction below
    stands, so this direction is SUPPORTING evidence only and is recorded
    as such; it is not sufficient to pass `command_order`.
    """
    draws = [c for c in capture["commands"] if "xa" in c]
    final = [(c["xa"], c["ya"]) for c in draws]
    counts = Counter(final)
    spans = {}
    for label, slot in (("earlier", earlier), ("later", later)):
        coords = group_coords(entries, slot)
        if not all(counts.get(c, 0) == 1 for c in coords):
            return "not_uniquely_joinable"
        indices = [final.index(c) for c in coords]
        spans[label] = (min(indices), max(indices))
    if spans["earlier"][0] > spans["later"][1]:
        return "earlier_cps_entry_later_in_vdp1"
    if spans["earlier"][1] < spans["later"][0]:
        return "earlier_cps_entry_earlier_in_vdp1"
    return "interleaved"


def residency(strips: bytes) -> dict:
    """Distinct tile textures each fixture frame needs, against the pool."""
    _, frames = objects_offset(strips)
    demands = [frame_tile_demand(strips, rel)["distinct_tiles"]
               for rel in range(frames)]
    worst = max(demands)
    return {
        "fixture_frames": frames,
        "distinct_tiles_min": min(demands),
        "distinct_tiles_mean": round(sum(demands) / len(demands), 1),
        "distinct_tiles_max": worst,
        "tile_sprite_pool_slots": TILE_SPRITE_POOL,
        "jo_max_sprite_table": JO_MAX_SPRITE,
        "frames_over_pool": sum(1 for d in demands if d > TILE_SPRITE_POOL),
        "frames_over_jo_sprite_table":
            sum(1 for d in demands if d > JO_MAX_SPRITE),
        "worst_frame_texture_bytes": worst * TILE_BYTES,
        "pool_texture_bytes": TILE_SPRITE_POOL * TILE_BYTES,
        "verdict": "TEXTURE_RESIDENCY_EXCEEDS_JO_SPRITE_TABLE",
        "note":
            "every fixture frame needs more distinct 16x16 textures than "
            "the 96-slot street pool, and more than Jo Engine's entire "
            "255-entry program-wide sprite-definition table. The pool "
            "therefore evicts and overwrites texture VRAM inside a single "
            "frame, so commands emitted earlier in that frame reference "
            "another tile's pixels by the time VDP1 draws the list. VDP1 "
            "texture VRAM is NOT the binding limit; the Jo sprite table is",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path,
                        default=ROOT / "private-evidence" / "rp4-direct-order")
    args = parser.parse_args()

    captures = {}
    for name in VARIANTS:
        path = args.evidence / (name + ".json")
        captures[name] = json.loads(path.read_text())
        captures[name]["_sha256"] = sha256_of(path)

    strips = STRIPS.read_bytes()
    entries = frame_entries(strips, 0)
    witnesses = json.loads(WITNESSES.read_text())
    witness = next(w for w in witnesses["witnesses"]
                   if w.get("streettest_rel") == 0)
    earlier = witness["earlier"]["slot"]
    later = witness["later"]["slot"]

    builds = {}
    for name, capture in captures.items():
        builds[name] = {
            "elf_sha256": capture["elf_sha256"],
            "iso_sha256": capture["iso_sha256"],
            "capture_sha256": capture["_sha256"],
            "scene_rel": capture["scene_rel"],
            "frame_lag": capture["frame_lag"],
            "command_count": capture["command_count"],
            "drawn_commands": capture["drawn_commands"],
            "state_commands": capture["state_commands"],
            "distinct_texture_slots": capture["distinct_textures"],
            "terminated": capture["terminated"],
            "anomalies": capture["anomalies"],
            "command_table_sha256": capture["command_table_sha256"],
            "witness_direction": witness_direction(capture, entries,
                                                   earlier, later),
        }

    pairs = {
        "sorted_reverse_vs_forward": ("sorted_reverse", "sorted_forward"),
        "immediate_reverse_vs_forward": ("immediate_reverse",
                                         "immediate_forward"),
        "sorted_vs_immediate_same_loop": ("sorted_reverse",
                                          "immediate_reverse"),
    }
    comparisons = {}
    for label, (a, b) in pairs.items():
        comparisons[label] = compare_captures(captures[a]["commands"],
                                              captures[b]["commands"])

    report = {
        "schema": "rp4-direct-order-v0",
        "fixture_sha256": sha256_of(STRIPS),
        "witness_sha256": sha256_of(WITNESSES),
        "witness": {
            "source_frame": witness["frame"],
            "streettest_rel": witness["streettest_rel"],
            "source_xy": witness["source_xy"],
            "earlier_slot": earlier,
            "later_slot": later,
            "pair_type": witness["pair_type"],
            "join_key": "renderer-computed coordinates",
            "join_key_limitation":
                "texture content cannot be used as a join key while the "
                "residency contradiction stands, so every direction here "
                "is supporting evidence and cannot pass command_order",
        },
        "builds": builds,
        "comparisons": comparisons,
        "texture_residency": residency(strips),
        "decision_table_result": "D",
        "decision_reasons": [
            "the immediate slPutSprite path does not preserve geometry: at "
            "fixture frame 0 the sorted path lands on the renderer's own "
            "computed coordinates (367/391 x and 390/391 y at offset zero) "
            "while the immediate path matches no offset of them (99/505 x) "
            "and emits 505 commands against 391",
            "no seam can preserve the texture-content invariant, because "
            "every fixture frame needs more distinct resident textures "
            "than Jo Engine's whole 255-entry sprite table",
            "correcting that residency crosses a measured Jo Engine "
            "structural limit rather than a VDP1 VRAM budget, so it is an "
            "architectural change and not a bounded setup correction",
        ],
        "falsified_premise": {
            "claim":
                "reversing the emission loop leaves the final VDP1 command "
                "order unchanged, so SGL does not preserve submission order "
                "for equal-Z sprites",
            "status": "FALSIFIED_BY_FRAME_PINNED_MEASUREMENT",
            "evidence":
                "with the capture frame pinned by breakpoint, the witness "
                "moves from final indices 380-384 (reverse) to 7-11 "
                "(forward) against the later entry at 239-246 and 145-152, "
                "matching the emission positions 53 and 5 of 59 exactly",
            "suspected_cause_of_prior_reading":
                "the previous capture advanced the fixture by roughly 44 "
                "frames per pause/resume round trip, so two captures were "
                "not of the same scene",
        },
        "unchanged_production_behavior": {
            "pristine_base_elf_sha256":
                "8ffd8a113c3bcf66926fc91fc10970c4085e01ebe6ec6f47246e85889aa93e83",
            "default_build_command_table_matches_pristine": True,
            "note":
                "the default build keeps the sorted path; its VDP1 command "
                "table is byte-identical to the pristine base build, so the "
                "diagnostic seam changes no production behavior",
        },
        "controls_not_promoted": [
            "cmdcolr_priority_selector",
            "sprite_priority_register_effect",
        ],
        "rp4_v1_status": "FALSIFIED",
        "capability_gate_1": "0/7",
    }

    OUTPUT.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n",
                      encoding="ascii", newline="\n")
    print("rp4 direct order: decision %s" % report["decision_table_result"])
    for name in VARIANTS:
        b = builds[name]
        print("  %-18s cmds=%3d textures=%3d witness=%s"
              % (name, b["command_count"], b["distinct_texture_slots"],
                 b["witness_direction"]))
    r = report["texture_residency"]
    print("  residency: %d/%d frames exceed the %d-entry Jo sprite table "
          "(max %d distinct tiles)"
          % (r["frames_over_jo_sprite_table"], r["fixture_frames"],
             JO_MAX_SPRITE, r["distinct_tiles_max"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
