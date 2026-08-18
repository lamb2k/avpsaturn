#!/usr/bin/env python3
"""Analyze synchronized MSHvSF Saturn MCP memory captures."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference_engine import vdp1 as vdp1_model  # noqa: E402


PAGE_SIZE = 4096


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def active_pages(data: bytes) -> list[int]:
    return [
        offset // PAGE_SIZE
        for offset in range(0, len(data), PAGE_SIZE)
        if any(data[offset : offset + PAGE_SIZE])
    ]


def changed_pages(before: bytes, after: bytes) -> list[int]:
    if len(before) != len(after):
        raise ValueError("Cannot compare regions with different lengths")
    return [
        offset // PAGE_SIZE
        for offset in range(0, len(before), PAGE_SIZE)
        if before[offset : offset + PAGE_SIZE] != after[offset : offset + PAGE_SIZE]
    ]


def changed_byte_count(before: bytes, after: bytes) -> int:
    return sum(left != right for left, right in zip(before, after, strict=True))


def nonzero_bounds(data: bytes) -> list[int] | None:
    first = next((index for index, value in enumerate(data) if value), None)
    if first is None:
        return None
    last = len(data) - 1 - next(index for index, value in enumerate(reversed(data)) if value)
    return [first, last + 1]


def parse_vdp1_commands(data: bytes) -> dict[str, object]:
    """Summarise the VDP1 list by real control flow, not by stored order.

    ``sequential_*`` reproduces the earlier stored-order reading so the two can
    be compared; ``reachable_*`` is what the command processor would visit when
    jump, call, return and skip modes are honoured. The residual count is the
    non-zero extent a longer earlier list left behind, and is not this frame's
    command count.
    """
    walk = vdp1_model.traverse(data)
    stored = vdp1_model.sequential_scan(data)
    stored_slots = vdp1_model.stored_nonzero_slots(data)
    return {
        "sequential_command_count": len(stored),
        "terminated": bool(stored and stored[-1].is_end),
        "reachable_command_count": walk.reachable_slot_count,
        "reachable_equals_sequential": (
            {c.offset for c in walk.visited} == {c.offset for c in stored}
        ),
        "drawn_command_count": walk.drawn_command_count,
        "state_command_count": walk.state_command_count,
        "skipped_command_count": walk.skipped_command_count,
        "stored_nonzero_slots": stored_slots,
        "residual_slots_after_terminator": stored_slots - walk.reachable_slot_count,
        "jump_mode_histogram": walk.jump_mode_histogram(),
        "command_type_histogram": walk.command_type_histogram(),
        "sprite_size_histogram": walk.size_histogram(),
        "flip_histogram": walk.flip_histogram(),
        "links_followed": len(walk.links_followed),
        "control_flow_anomalies": walk.anomalies,
        "traversal_stop_reason": walk.stop_reason,
        "texture_bytes_referenced": walk.texture_bytes_referenced(),
        "detail_report": "data/mshvsf_saturn_vdp1_control_flow.json",
    }


def load_anchors(capture_root: Path) -> list[dict[str, object]]:
    session = json.loads((capture_root / "session.json").read_text(encoding="utf-8"))
    anchors = []
    for summary in session["anchors"]:
        anchor_dir = capture_root / f"{summary['captured_frame']:05d}_{summary['label']}"
        manifest = json.loads((anchor_dir / "manifest.json").read_text(encoding="utf-8"))
        regions = {}
        for region in manifest["regions"]:
            data = (anchor_dir / region["file"]).read_bytes()
            if len(data) != region["bytes"] or sha256(data) != region["sha256"]:
                raise ValueError(f"Raw capture failed manifest validation: {anchor_dir / region['file']}")
            regions[region["name"]] = {"metadata": region, "data": data}
        anchors.append({"summary": summary, "manifest": manifest, "regions": regions})
    return anchors


def build_report(anchors: list[dict[str, object]]) -> dict[str, object]:
    anchor_reports = []
    for anchor in anchors:
        region_reports = []
        for name, region in anchor["regions"].items():
            data = region["data"]
            record = {
                **region["metadata"],
                "nonzero_bytes": sum(value != 0 for value in data),
                "nonzero_bounds": nonzero_bounds(data),
                "active_4k_pages": active_pages(data),
            }
            if name == "vdp1_vram":
                record["command_table"] = parse_vdp1_commands(data)
            region_reports.append(record)
        anchor_reports.append(
            {
                "label": anchor["summary"]["label"],
                "requested_frame": anchor["summary"]["requested_frame"],
                "captured_frame": anchor["summary"]["captured_frame"],
                "regions": region_reports,
            }
        )

    transitions = []
    for before, after in zip(anchors, anchors[1:]):
        region_changes = []
        common = sorted(set(before["regions"]) & set(after["regions"]))
        for name in common:
            left = before["regions"][name]["data"]
            right = after["regions"][name]["data"]
            region_changes.append(
                {
                    "name": name,
                    "changed_bytes": changed_byte_count(left, right),
                    "changed_4k_pages": changed_pages(left, right),
                }
            )
        transitions.append(
            {
                "from": before["summary"]["label"],
                "to": after["summary"]["label"],
                "frame_delta": after["summary"]["captured_frame"]
                - before["summary"]["captured_frame"],
                "regions": region_changes,
            }
        )
    return {
        "title": "MSHvSF Saturn synchronized runtime-memory anchors",
        "purpose": "Candidate Saturn architecture evidence for AvP design probes",
        "evidence_class": "MEASURED_ON_MARVEL_NOT_YET_VALIDATED_ON_AVP",
        "anchors": anchor_reports,
        "transitions": transitions,
        "limits": [
            "Changed and nonzero bytes are occupancy leads, not allocator ownership proof.",
            "VDP1 parsing now follows real jump/call/return/skip control flow; reachable and stored-order counts are reported separately.",
            "No Marvel address, timing, or package size transfers directly into AvP.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--capture-root", type=Path, default=Path(".deps/mshvsf_saturn_state")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("data/mshvsf_saturn_runtime_memory.json")
    )
    args = parser.parse_args()
    report = build_report(load_anchors(args.capture_root))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"Analyzed {len(report['anchors'])} anchors and {len(report['transitions'])} transitions."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
