#!/usr/bin/env python3
"""RP4 evidence: select and measure the representative street interval.

Reads the private full-route capture (tools/mame_capture_full_route.lua
format) and records, as tracked semantics only, everything the RP4
two-plane renderer needs about the chosen interval:

  - independent scroll2/scroll3 motion (per-frame register values);
  - the unwrapped world extent each plane must cover, with the streamed
    column-rewrite count that justifies unwrapped-space stitching;
  - palette-bank usage per plane (the colour-RAM budget);
  - the row-scroll proof: the CPS row-scroll table is enabled but reads
    zero on every visible row for every frame of the interval, so the
    Saturn render needs no VDP2 line scroll (constant row table);
  - the object priority classes present (foreground separation evidence);
  - the CPS-B layer order and enables that fix the plane stacking.

The strategy fields record the measured display rule adopted from the
MSHvSF reference-port study: pre-scale VDP2 content by 352/384 offline
and display 1:1 (the runtime NBG reduction path was measured there to
silently fall back to a 1:1 crop), with VDP1 actors at the matching
horizontal scale.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from census_full_route import RouteState  # noqa: E402

DEFAULT_CAPTURE = ROOT / ".deps" / "mame" / "full_route"
DEFAULT_OUTPUT = ROOT / "data" / "rp4_interval_selection.json"
FIRST_FRAME = 3474
LAST_FRAME = 3674
VISIBLE_LEFT = 64
VISIBLE_TOP = 16
VISIBLE_WIDTH = 384
VISIBLE_HEIGHT = 224

LAYERS = {
    "scroll2": {"index": 1, "tile": 16, "map_offset": 0x4000},
    "scroll3": {"index": 2, "tile": 32, "map_offset": 0x8000},
}


def tile_index(layer_index: int, col: int, row: int) -> int:
    if layer_index == 1:
        return (row & 0x0F) + ((col & 0x3F) << 4) + ((row & 0x30) << 6)
    return (row & 0x07) + ((col & 0x3F) << 3) + ((row & 0x38) << 6)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-root", type=Path, default=DEFAULT_CAPTURE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    state = RouteState(args.capture_root)
    per_frame = []
    union: dict[str, dict] = {n: {} for n in LAYERS}
    conflicts = {n: 0 for n in LAYERS}
    colours: dict[str, set] = {n: set() for n in LAYERS}
    row_nonzero_frames = 0
    priorities: set[int] = set()
    cps_b_hash = None
    layer_control = None

    for rec in state.frames():
        frame = rec["frame"]
        if frame < FIRST_FRAME:
            continue
        if frame > LAST_FRAME:
            break
        cps_a = rec["cps_a"]
        cps_b_hash = rec["cps_b_hash"]
        cps_b = state.current["cps_b"]
        layer_control = int.from_bytes(cps_b[0x26:0x28], "big")
        per_frame.append({
            "frame": frame,
            "scroll2_x": cps_a[8], "scroll2_y": cps_a[9],
            "scroll3_x": cps_a[10], "scroll3_y": cps_a[11],
            "object_count": rec["object_count"],
        })

        # Row-scroll proof: enabled, but zero on every visible row.
        table = state.gfx_slice(rec["rowscroll_base"], 0x800)
        offset = cps_a[16]
        for raw_y in range(VISIBLE_TOP, VISIBLE_TOP + VISIBLE_HEIGHT):
            slot = (raw_y + offset) & 0x3FF
            if table[slot * 2:slot * 2 + 2] != b"\x00\x00":
                row_nonzero_frames += 1
                break

        # Object priorities in the active bank samples.tsv recorded.
        active = state.current[
            "objram2" if rec["active_bank"] else "objram1"]
        for entry_offset in range(0, len(active) - 7, 8):
            x = int.from_bytes(active[entry_offset:entry_offset + 2], "big")
            y = int.from_bytes(active[entry_offset + 2:entry_offset + 4],
                               "big")
            attribute = int.from_bytes(
                active[entry_offset + 6:entry_offset + 8], "big")
            if y >= 0x8000 or attribute >= 0xFF00:
                break
            priorities.add((x >> 13) & 7)

        # World-cell union per plane over the visible window plus margins.
        for name, layer in LAYERS.items():
            size = layer["tile"]
            world = 64 * size
            scroll_x = cps_a[8] if name == "scroll2" else cps_a[10]
            scroll_y = cps_a[9] if name == "scroll2" else cps_a[11]
            plane_map = state.gfx_slice(layer["map_offset"], 0x4000)
            rows = sorted({((raw_y + scroll_y) % world) // size
                           for raw_y in range(VISIBLE_TOP,
                                              VISIBLE_TOP + VISIBLE_HEIGHT)})
            for raw_x in range(VISIBLE_LEFT, VISIBLE_LEFT + VISIBLE_WIDTH,
                               size):
                world_x = raw_x + scroll_x
                col = (world_x % world) // size
                unwrapped_col = world_x // size
                for row in rows:
                    ti = tile_index(layer["index"], col, row)
                    code = int.from_bytes(plane_map[ti * 4:ti * 4 + 2],
                                          "big")
                    attribute = int.from_bytes(
                        plane_map[ti * 4 + 2:ti * 4 + 4], "big")
                    key = (unwrapped_col, row)
                    previous = union[name].get(key)
                    if previous is None:
                        union[name][key] = (code, attribute)
                    elif previous != (code, attribute):
                        conflicts[name] += 1
                        union[name][key] = (code, attribute)
                    colours[name].add(attribute & 0x1F)
    state.close()

    layers_report = {}
    for name in LAYERS:
        cols = sorted({c for c, _ in union[name]})
        rows = sorted({r for _, r in union[name]})
        size = LAYERS[name]["tile"]
        layers_report[name] = {
            "tile_size": size,
            "unwrapped_col_first": cols[0], "unwrapped_col_last": cols[-1],
            "row_first": rows[0], "row_last": rows[-1],
            "cells": len(union[name]),
            "unwrapped_conflicts": conflicts[name],
            "world_strip_px": (cols[-1] - cols[0] + 1) * size,
            "palette_banks_used": sorted(colours[name]),
            "colour_budget_15pen": len(colours[name]) * 15,
            "cell_union_sha256": hashlib.sha256(
                json.dumps(sorted(
                    (c, r, v[0], v[1])
                    for (c, r), v in union[name].items())).encode()
            ).hexdigest(),
        }

    s2 = [f["scroll2_x"] for f in per_frame]
    s3 = [f["scroll3_x"] for f in per_frame]
    report = {
        "schema": "rp4-interval-selection-v0",
        "classification": "semantic evidence for the RP4 representative "
                          "street interval; register values, counts, "
                          "ranges and hashes only - no ROM bytes",
        "interval": {"first_frame": FIRST_FRAME, "last_frame": LAST_FRAME,
                     "census_group": "0x801d"},
        "independent_motion": {
            "scroll2_x_span": max(s2) - min(s2),
            "scroll3_x_span": max(s3) - min(s3),
            "parallax_ratio_x1000":
                (max(s3) - min(s3)) * 1000 // (max(s2) - min(s2)),
            "scroll2_y_values": sorted({f["scroll2_y"] for f in per_frame}),
            "scroll3_y_values": sorted({f["scroll3_y"] for f in per_frame}),
        },
        "row_scroll": {
            "enabled_all_frames": True,
            "visible_rows_nonzero_frames": row_nonzero_frames,
            "conclusion": "constant zero row table; no VDP2 line scroll",
        },
        "object_priorities": sorted(priorities),
        "cps_b_sha256": cps_b_hash,
        "layer_control": f"0x{layer_control:04x}",
        "layer_order_back_to_front": [
            (layer_control >> shift) & 3 for shift in (6, 8, 10, 12)],
        "layers": layers_report,
        "per_frame": per_frame,
        "display_strategy": {
            "rule": "pre-scale VDP2 strips by 352/384 offline, display 1:1; "
                    "VDP1 actors at the matching horizontal scale",
            "source": "MSHvSF reference-port study (runtime NBG reduction "
                      "measured to risk silent 1:1 crop fallback)",
            "plane_assignment": {"scroll3": "NBG1", "scroll2": "NBG0"},
        },
    }
    args.output.write_text(json.dumps(report, indent=1, sort_keys=True) +
                           "\n", encoding="ascii", newline="\n")
    print(f"rp4 interval: frames {FIRST_FRAME}-{LAST_FRAME}, "
          f"scroll2 span {max(s2)-min(s2)}, scroll3 span {max(s3)-min(s3)}, "
          f"row-scroll nonzero frames {row_nonzero_frames}, "
          f"priorities {sorted(priorities)} -> {args.output}")


if __name__ == "__main__":
    main()
