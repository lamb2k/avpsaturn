#!/usr/bin/env python3
"""Analyze synchronized MSHvSF Saturn MCP memory captures."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


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
    commands: list[dict[str, object]] = []
    for offset in range(0, min(len(data), 0x10000), 0x20):
        words = [int.from_bytes(data[offset + i : offset + i + 2], "big") for i in range(0, 0x20, 2)]
        control = words[0]
        command = {
            "index": offset // 0x20,
            "offset": offset,
            "control": f"0x{control:04X}",
            "link": f"0x{words[1]:04X}",
            "pmod": f"0x{words[2]:04X}",
            "color": f"0x{words[3]:04X}",
            "source": f"0x{words[4] * 8:05X}",
            "width": ((words[5] >> 8) & 0x3F) * 8,
            "height": words[5] & 0xFF,
            "coordinates": [
                value - 0x10000 if value & 0x8000 else value
                for value in words[6:14]
            ],
        }
        commands.append(command)
        if control & 0x8000:
            break
    return {
        "sequential_command_count": len(commands),
        "terminated": bool(commands and int(commands[-1]["control"], 16) & 0x8000),
        "commands": commands,
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
            "VDP1 parsing follows the sequential table only; jump/call traversal remains to be added.",
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
