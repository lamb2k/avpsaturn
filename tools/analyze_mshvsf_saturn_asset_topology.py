#!/usr/bin/env python3
"""Derive measured Saturn disc-package topology from the tracked manifest."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import defaultdict
from pathlib import Path


def family(path: str) -> str:
    name = Path(path).name.upper()
    if name.endswith(".ST2"):
        return "st2_streams"
    if name.endswith(".ADP"):
        return "adp_audio"
    if re.fullmatch(r"PL[0-9A-F]{2}\.PAC", name):
        return "player_packages"
    if re.fullmatch(r"BG[0-9A-F]{2}\.PAC", name):
        return "background_packages"
    if re.fullmatch(r"SO[0-9A-F]{2}\.PAC", name):
        return "stage_support_packages"
    if name.endswith(".PAC"):
        return "other_pac_packages"
    if name.endswith(".BIN"):
        return "binary_members"
    return "other_members"


def percentile(values: list[int], fraction: float) -> int:
    ordered = sorted(values)
    index = max(0, math.ceil(len(ordered) * fraction) - 1)
    return ordered[index]


def summarize(items: list[dict[str, object]]) -> dict[str, object]:
    sizes = [int(item["bytes"]) for item in items]
    largest = sorted(items, key=lambda item: int(item["bytes"]), reverse=True)[:8]
    return {
        "file_count": len(items),
        "total_file_bytes": sum(sizes),
        "minimum_file_bytes": min(sizes),
        "median_file_bytes": percentile(sizes, 0.5),
        "p95_file_bytes": percentile(sizes, 0.95),
        "maximum_file_bytes": max(sizes),
        "largest_members": [
            {
                "path": item["path"],
                "bytes": item["bytes"],
                "extent": item["extent"],
                "sha256": item["sha256"],
            }
            for item in largest
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/mshvsf_saturn_disc_manifest.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/mshvsf_saturn_asset_topology.json"),
    )
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    files = [
        item for item in manifest["filesystem"] if not bool(item["is_directory"])
    ]
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for item in files:
        grouped[family(str(item["path"]))].append(item)

    required = {
        "st2_streams",
        "adp_audio",
        "player_packages",
        "background_packages",
        "stage_support_packages",
        "other_pac_packages",
        "binary_members",
        "other_members",
    }
    if set(grouped) != required:
        raise RuntimeError(f"Unexpected family set: {sorted(set(grouped) ^ required)}")

    player_sizes = sorted(
        (int(item["bytes"]) for item in grouped["player_packages"]), reverse=True
    )
    background_sizes = sorted(
        (int(item["bytes"]) for item in grouped["background_packages"]),
        reverse=True,
    )
    support_sizes = sorted(
        (int(item["bytes"]) for item in grouped["stage_support_packages"]),
        reverse=True,
    )
    report = {
        "title": "MSHvSF Saturn on-disc asset topology",
        "source_manifest": args.manifest.as_posix(),
        "disc_file_count": len(files),
        "disc_file_bytes": sum(int(item["bytes"]) for item in files),
        "families": {
            name: summarize(grouped[name]) for name in sorted(grouped)
        },
        "storage_envelopes": {
            "two_largest_player_packages_bytes": sum(player_sizes[:2]),
            "two_largest_players_plus_largest_background_and_support_bytes": (
                sum(player_sizes[:2]) + background_sizes[0] + support_sizes[0]
            ),
            "meaning": "Conservative compressed/on-disc package sums for candidate assessment only.",
            "warning": "File size does not reveal decompressed size, simultaneous residency, destination RAM, or runtime lifetime.",
        },
        "proven_observations": [
            "The ISO root is flat and contains distinct player, background, stage-support, ADP-audio, ST2-stream, and binary naming families.",
            "Player, background, and stage-support PAC members are individually addressable ISO files.",
            "ADP assets and eleven CD audio tracks coexist on the same release disc.",
        ],
        "unresolved": [
            "PAC and ST2 internal formats",
            "compression ratios and decompressed sizes",
            "which named package maps to each character or stage",
            "runtime load order, destination, lifetime, and eviction policy",
            "whether adjacent extents imply intentional seek optimization",
        ],
        "confidence": "HIGH for file metadata; LOW for any runtime implication",
        "rights_boundary": "Derived metadata only; no disc payload is committed.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"Summarized {len(files)} files across {len(grouped)} measured families."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
