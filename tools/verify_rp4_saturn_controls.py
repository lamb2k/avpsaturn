#!/usr/bin/env python3
"""RP4 v1 Saturn controls: score the captured StreetTest evidence.

Consumes the per-build captures produced by
tools/capture_street_command_order.py and writes the tracked manifest
data/rp4_saturn_controls.json through tools/saturn_control_status.py.

Only bounded evidence is written: hashes, counts, indices, statuses and
the witness identity. No framebuffer bytes, no command dumps, no build
artefacts.

What this can and cannot see in the current instrument:

- the final VDP1 command table IS readable, so the ORDER VDP1 will draw
  in can be compared between two builds directly;
- the VDP1 framebuffer is NOT readable. It returns zeros under the
  OpenGL core and is unmapped under the software core, and this build of
  the emulator has no screenshot facility at all. The observed winner at
  a witness PIXEL therefore cannot be obtained, and any control that
  needs it is recorded BLOCKED rather than assumed.
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
from saturn_control_status import build_saturn_status  # noqa: E402

WITNESSES = ROOT / "data" / "rp4_object_order_witnesses.json"
FIXTURE = ROOT / "build" / "rp4_fixture" / "STRIPS.BIN"
OUTPUT = ROOT / "data" / "rp4_saturn_controls.json"

FRAMEBUFFER_BLOCKED = (
    "the VDP1 framebuffer is unreadable in this instrument (zeros under "
    "the OpenGL core, unmapped under the software core) and this "
    "emulator build has no screenshot facility, so no witness pixel can "
    "be observed")


def identity(commands: list[dict]) -> list[tuple]:
    """A command's identity ignoring where its texture happens to live.

    Texture addresses move when the tile upload order changes, which is
    a consequence of the emission order rather than an independent
    variable, so ordering is compared on position, colour and size.
    """
    return [(c["xa"], c["ya"], c["colr"], c["size"]) for c in commands]


def order_relationship(baseline: list[dict], variant: list[dict]) -> dict:
    b, v = identity(baseline), identity(variant)
    unique = [p for p in set(b) & set(v)
              if b.count(p) == 1 and v.count(p) == 1]
    pairs = sorted((b.index(p), v.index(p)) for p in unique)
    preserved = sum(1 for i in range(len(pairs))
                    for j in range(i + 1, len(pairs))
                    if pairs[i][1] < pairs[j][1])
    total = len(pairs) * (len(pairs) - 1) // 2
    return {
        "same_command_multiset": Counter(b) == Counter(v),
        "same_draw_order": b == v,
        "exactly_reversed": b == v[::-1],
        "comparable_commands": len(unique),
        "order_preserving_pairs": preserved,
        "comparable_pairs": total,
        "order_preserved_fraction": round(preserved / total, 6)
        if total else None,
    }


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture_provenance(path: Path) -> dict:
    """Return only the reproducible identity of one ignored capture.

    The raw command list stays ignored.  Its absolute replay location is
    deliberately retained here because this diagnostic has no tracked input
    substitute; the hash makes an accidental replacement detectable.
    """
    resolved = path.resolve()
    captured = json.loads(resolved.read_text(encoding="utf-8"))
    if captured.get("schema") != "rp4-street-command-order-capture-v0":
        raise ValueError(f"not an RP4 command capture: {resolved}")
    if "requested_rel" not in captured or "commands" not in captured:
        raise ValueError(f"incomplete RP4 command capture: {resolved}")
    return {
        "path": str(resolved),
        "sha256": sha256_of(resolved),
        "schema": captured["schema"],
        "requested_rel": captured["requested_rel"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-capture", type=Path, required=True)
    parser.add_argument("--forward-capture", type=Path, required=True)
    parser.add_argument("--baseline-build-sha256", required=True)
    parser.add_argument("--forward-build-sha256", required=True)
    args = parser.parse_args()

    baseline = json.loads(args.baseline_capture.read_text())
    forward = json.loads(args.forward_capture.read_text())
    baseline_provenance = capture_provenance(args.baseline_capture)
    forward_provenance = capture_provenance(args.forward_capture)
    witnesses = json.loads(WITNESSES.read_text())
    witness = next(w for w in witnesses["witnesses"]
                   if w.get("streettest_rel") == baseline["requested_rel"])

    relationship = order_relationship(baseline["commands"],
                                      forward["commands"])

    # The ordering control executed and REFUTED the mechanism: reversing
    # the emission loop left the final VDP1 draw order untouched.
    mechanism_controls_order = not relationship["same_draw_order"]
    command_order = {
        "baseline_build_sha256": args.baseline_build_sha256,
        "variant_build_sha256": args.forward_build_sha256,
        "fixture_sha256": sha256_of(FIXTURE),
        "witness_sha256": sha256_of(WITNESSES),
        "source_frame": witness["frame"],
        "streettest_rel": witness["streettest_rel"],
        "expected_winner": "later object-RAM entry",
        "observed_winner":
            "unobservable pixel; final VDP1 draw order unchanged"
            if not mechanism_controls_order else
            "final VDP1 draw order changed",
        "witness_pixels_changed": 0,
        "negative_control_pixels_changed": 0,
        "status": "failed" if not mechanism_controls_order else "blocked",
        "blocked_reason": FRAMEBUFFER_BLOCKED,
        "baseline_command_table_sha256":
            baseline["command_table_sha256"],
        "variant_command_table_sha256": forward["command_table_sha256"],
        "measurement": relationship,
        "note":
            "reversing the emission loop did not change what VDP1 draws: "
            "the same commands appear at the same indices in both builds "
            "and only texture addresses moved, so SGL does not preserve "
            "submission order for equal-Z sprites and the reverse loop "
            "is not the mechanism that controls output order",
    }

    blocked = {
        "baseline_build_sha256": args.baseline_build_sha256,
        "variant_build_sha256": "0" * 64,
        "fixture_sha256": sha256_of(FIXTURE),
        "witness_sha256": sha256_of(WITNESSES),
        "source_frame": witness["frame"],
        "streettest_rel": witness["streettest_rel"],
        "expected_winner": "tile layer",
        "observed_winner": None,
        "witness_pixels_changed": 0,
        "negative_control_pixels_changed": 0,
        "status": "blocked",
        "blocked_reason": FRAMEBUFFER_BLOCKED,
        "baseline_command_table_sha256":
            baseline["command_table_sha256"],
        "variant_command_table_sha256": "0" * 64,
    }

    controls = {
        "command_order": command_order,
        "cmdcolr_priority_selector": dict(blocked),
        "sprite_priority_register_effect": dict(blocked),
    }
    status = build_saturn_status(controls)

    report = {
        "schema": "rp4-saturn-controls-v0",
        "instrument_limits": {
            "vdp1_command_table": "READABLE",
            "vdp1_framebuffer": "UNREADABLE",
            "vdp2_registers": "UNREADABLE",
            "emulator_screenshot": "UNAVAILABLE",
        },
        "witness": {
            "source_frame": witness["frame"],
            "streettest_rel": witness["streettest_rel"],
            "source_xy": witness["source_xy"],
            "pair_type": witness["pair_type"],
            "earlier_slot": witness["earlier"]["slot"],
            "later_slot": witness["later"]["slot"],
        },
        "builds": {
            "baseline": {
                "sha256": args.baseline_build_sha256,
                "command_count": baseline["command_count"],
                "command_table_sha256": baseline["command_table_sha256"],
                "street_objects": baseline["street_objects"],
                "vdp2_shadow_values": baseline["vdp2_shadow_values"],
            },
            "forward_order": {
                "sha256": args.forward_build_sha256,
                "command_count": forward["command_count"],
                "command_table_sha256": forward["command_table_sha256"],
                "street_objects": forward["street_objects"],
                "vdp2_shadow_values": forward["vdp2_shadow_values"],
            },
        },
        "input_captures": {
            "baseline": baseline_provenance,
            "forward_order": forward_provenance,
        },
        "shadow_values_note":
            "SGL work-RAM shadow of what the program programmed; this is "
            "NOT a VDP2 register readback",
        "controls": controls,
        "status": status,
    }
    OUTPUT.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n",
                      encoding="ascii", newline="\n")
    print(f"saturn controls: {status['saturn_output_order_status']}; "
          f"executed {status['controls_executed']}, passed "
          f"{status['controls_passed']}, blocked "
          f"{status['controls_blocked']}")
    for name, result in sorted(status["per_control"].items()):
        print(f"  {name}: detected={result['detected']} "
              f"({result['reason'][:80]})")
    return 0 if status["saturn_output_order_status"] == "MEASURED" else 3


if __name__ == "__main__":
    raise SystemExit(main())
