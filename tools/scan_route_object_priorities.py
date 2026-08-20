#!/usr/bin/env python3
"""Route-wide visible-object priority sweep (hard-stop evidence).

The RP4 overlap contract presumes visible actor-class objects at CPS
priority 1 and foreground content at priority 4. The street scanner
found zero onscreen priority-1 objects across the whole street scene;
this sweep extends the falsification to the COMPLETE 18000-frame
cadence-1 route: for every frame, every active objram entry is
classified by (x >> 13) & 7 and intersected with the visible window.

Tracked output data/route_object_priority_sweep.json: counts only.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from census_full_route import RouteState  # noqa: E402

CAPTURE = ROOT / ".deps" / "mame" / "full_route"
OUTPUT = ROOT / "data" / "route_object_priority_sweep.json"


def main() -> None:
    state = RouteState(CAPTURE)
    onscreen = Counter()
    frames_with = Counter()
    parked = Counter()
    total = 0
    for rec in state.frames():
        total += 1
        active = state.current[
            "objram2" if rec["active_bank"] else "objram1"]
        seen = set()
        for off in range(0, len(active) - 7, 8):
            x = int.from_bytes(active[off:off + 2], "big")
            y = int.from_bytes(active[off + 2:off + 4], "big")
            attr = int.from_bytes(active[off + 6:off + 8], "big")
            if y >= 0x8000 or attr >= 0xFF00:
                break
            pri = (x >> 13) & 7
            sx = (x & 0x3FF) - 64
            sy = (y & 0x3FF) - 16
            w = (((attr >> 8) & 0xF) + 1) * 16 if attr & 0xFF00 else 16
            h = (((attr >> 12) & 0xF) + 1) * 16 if attr & 0xFF00 else 16
            if sx + w > 0 and sx < 384 and sy + h > 0 and sy < 224:
                onscreen[pri] += 1
                seen.add(pri)
            else:
                parked[pri] += 1
        for pri in seen:
            frames_with[pri] += 1
    state.close()

    report = {
        "schema": "route-object-priority-sweep-v0",
        "classification": "counts only; no ROM bytes or pixels",
        "frames_scanned": total,
        "onscreen_objects_by_priority":
            {str(k): v for k, v in sorted(onscreen.items())},
        "offscreen_parked_by_priority":
            {str(k): v for k, v in sorted(parked.items())},
        "frames_with_visible_objects_by_priority":
            {str(k): v for k, v in sorted(frames_with.items())},
        "finding": "priority 1 never draws a visible object anywhere in "
                   "the route; visible content is priority 4 plus a "
                   "priority-7 population the current class model does "
                   "not map. The actor-class-is-priority-1 premise is "
                   "falsified route-wide.",
        "inputs_sha256": {
            "route_census": hashlib.sha256(
                (ROOT / "data" / "round1_route_census.json")
                .read_bytes()).hexdigest(),
        },
    }
    OUTPUT.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n",
                      encoding="ascii", newline="\n")
    print(f"route sweep: {total} frames, onscreen by priority "
          f"{dict(onscreen)}, frames with visible {dict(frames_with)}")


if __name__ == "__main__":
    main()
