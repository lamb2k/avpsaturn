#!/usr/bin/env python3
"""Map Coffee Shop unowned audio/load events to source audio commands (read-only).

Joins data/reimplement13_coffee_shop_scene_parity.json (audio and load rows) with
the source command stream in data/oracle11_global_audio_handlers.json. Numbers only.
Tier: SOURCE_CAPTURE. The bucket is a proposal for the Saturn path, not an approved
native rule; semantic sound names stay UNKNOWN in the source records.
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIRST, LAST = 1972, 15193
SCENE_LAST = 5566


def field(row: dict, *names):
    for name in names:
        if name in row:
            return row[name]
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    parity = json.loads((ROOT / "data/reimplement13_coffee_shop_scene_parity.json").read_text())
    handlers = json.loads((ROOT / "data/oracle11_global_audio_handlers.json").read_text())

    def find(node, key):
        if isinstance(node, dict):
            if key in node:
                return node[key]
            for value in node.values():
                hit = find(value, key)
                if hit is not None:
                    return hit
        return None

    audio = find(parity, "audio") or []
    load = find(parity, "load_release") or []
    classes = collections.Counter(r.get("classification") for r in audio + load)
    occurrences = handlers["command_occurrences"]
    per_command = collections.defaultdict(list)
    for row in occurrences:
        per_command[row["command"]].append(row["main_frame"])
    table = []
    for command, frames in sorted(per_command.items()):
        scene = [f for f in frames if FIRST <= f <= SCENE_LAST]
        table.append({"command": command, "route_count": len(frames), "scene_count": len(scene),
                      "first": frames[0], "last": frames[-1],
                      "repeats_in_route": len(frames) > 1})
    result = {
        "tier": "SOURCE_CAPTURE",
        "parity_audio_rows": len(audio), "parity_load_rows": len(load),
        "parity_classifications": dict(classes),
        "audio_row_sample": audio[:2], "load_row_sample": load[:4],
        "route_commands": len(occurrences), "route_identities": len(table),
        "scene_commands": sum(row["scene_count"] for row in table),
        "scene_identities": sum(1 for row in table if row["scene_count"]),
        "max_commands_per_frame": max(collections.Counter(
            row["main_frame"] for row in occurrences).values()),
        "commands": table,
    }
    args.output.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "commands"})[:2500])
    for row in sorted(table, key=lambda r: -r["route_count"])[:14]:
        print(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
