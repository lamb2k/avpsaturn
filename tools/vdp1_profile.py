#!/usr/bin/env python3
"""Decode SAT_VDP1_PROFILE ring dumps. Raw SH-2 words are big endian.

Read sat_vdp1_plots and sat_vdp1_frames while paused (sizes from the ELF),
then: python tools/vdp1_profile.py --plots plots.bin --frames frames.bin
All times remain FRT ticks; no emulator observation is called hardware timing.
"""
from __future__ import annotations

import argparse
import json
import math
import struct
from pathlib import Path

PLOT_FIELDS = (
    "attempt", "serial", "source_vblank", "stage_characters",
    "snapshot_ticks", "handoff_tick", "start_vblank", "submit_tick",
    "wait_end_ticks", "sprite_ticks", "upload_ticks", "upload_bytes",
    "wait_change_ticks", "wait_latch_ticks", "layer_ticks", "cpu_ticks",
    "objects", "commands", "source_texels", "sprite_pixels", "clear_pixels",
    "half_transparent", "colour_modes", "flags", "raster_upper_ticks",
)
FRAME_FIELDS = (
    "vblank", "started", "shown_before", "shown_after", "edsr", "cpu_busy",
)
TIMES = (
    "snapshot_ticks", "wait_end_ticks", "sprite_ticks", "upload_ticks",
    "wait_change_ticks", "wait_latch_ticks", "layer_ticks", "cpu_ticks",
)
SUBMITTED, END_TIMEOUT, CHANGE_TIMEOUT, LATCH_TIMEOUT, CEF_AT_DONE = 1, 2, 4, 8, 16
MASK = 0xFFFFFFFF


def decode_ring(raw: bytes, fields: tuple[str, ...], endian: str = "big") -> list[dict]:
    size = len(fields) * 4
    if not raw or len(raw) % size:
        raise ValueError(f"ring needs a nonzero multiple of {size} bytes, got {len(raw)}")
    rows = [dict(zip(fields, values)) for values in struct.iter_unpack(
        (">" if endian == "big" else "<") + "I" * len(fields), raw)]
    rows = [row for row in rows if row[fields[0]]]
    if not rows:
        return []
    newest = rows[0][fields[0]]
    for row in rows[1:]:
        candidate = row[fields[0]]
        if 0 < ((candidate - newest) & MASK) < 0x80000000:
            newest = candidate
    return sorted(rows, key=lambda row: (newest - row[fields[0]]) & MASK, reverse=True)


def distribution(values: list[int]) -> dict:
    if not values:
        return {"count": 0}
    values = sorted(values)
    return {"count": len(values), "mean": round(sum(values) / len(values), 2),
            "p95": values[math.ceil(len(values) * 0.95) - 1], "max": values[-1]}


def summarize(plots: list[dict], frames: list[dict]) -> dict:
    submitted = [p for p in plots if p["flags"] & SUBMITTED]
    changes = [f for f in frames if f["shown_after"] != f["shown_before"]]
    waits = [f for f in frames if f["started"] != f["shown_before"] and
             f["shown_after"] == f["shown_before"] and not (f["edsr"] & 2)]
    idle = [f for f in frames if f["started"] == f["shown_before"]]
    stages: dict[str, list[dict]] = {}
    for p in submitted:
        value = p["stage_characters"]
        key = f"stage_{value & 0xffff:02x}_slots_{(value >> 16) & 255}_{value >> 24}"
        stages.setdefault(key, []).append(p)
    return {
        "tier": "capture tier must be supplied by the operator; HOST tests are synthetic",
        "units": "FRT ticks, texels, and clipped destination bounding-box pixels",
        "notes": [
            "Retained ring rows only, not whole-run totals; dump frequently or raise depth.",
            "Frame-change requests are not proof of pictures actually displayed. Use SAT_VLOG serials for that.",
            "CPU-busy samples overlap presentation classes; do not add their percentages.",
            "Raster observations after layer work are upper bounds, not measured chip drawing duration.",
            "Snapshot/handoff use the master timer; draw fields use the slave timer. Never subtract across CPUs.",
            "Character bytes identify arcade slots; record guest build flags separately.",
        ],
        "presentation": {
            "sampled_vblanks": len(frames),
            "frame_change_requests": len(changes),
            "waiting_for_end_flag": len(waits),
            "no_unshown_plot": len(idle),
            "slave_busy_at_vblank": sum(bool(f["cpu_busy"]) for f in frames),
            "vblank_gaps": sum(((b["vblank"] - a["vblank"]) & MASK) != 1
                               for a, b in zip(frames, frames[1:])),
        },
        "attempts": {
            "retained": len(plots), "submitted": len(submitted),
            "end_timeout": sum(bool(p["flags"] & END_TIMEOUT) for p in plots),
            "change_timeout": sum(bool(p["flags"] & CHANGE_TIMEOUT) for p in plots),
            "latch_timeout": sum(bool(p["flags"] & LATCH_TIMEOUT) for p in plots),
        },
        "timing_ticks": {name: distribution([p[name] for p in submitted]) for name in TIMES},
        "work": {name: distribution([p[name] for p in submitted]) for name in (
            "objects", "commands", "upload_bytes", "source_texels", "sprite_pixels",
            "clear_pixels", "half_transparent")},
        "raster_completion_upper_bound_ticks": distribution([
            p["raster_upper_ticks"] for p in submitted if p["flags"] & CEF_AT_DONE]),
        "by_stage_and_arcade_slots": {
            key: {"plots": len(rows), "commands": distribution([p["commands"] for p in rows]),
                  "sprite_ticks": distribution([p["sprite_ticks"] for p in rows]),
                  "upload_bytes": distribution([p["upload_bytes"] for p in rows])}
            for key, rows in stages.items()
        },
        "plot_rows": plots, "frame_rows": frames,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plots", required=True, type=Path)
    parser.add_argument("--frames", required=True, type=Path)
    parser.add_argument("--endian", choices=("big", "little"), default="big")
    args = parser.parse_args()
    try:
        plots = decode_ring(args.plots.read_bytes(), PLOT_FIELDS, args.endian)
        frames = decode_ring(args.frames.read_bytes(), FRAME_FIELDS, args.endian)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(summarize(plots, frames), indent=2))


if __name__ == "__main__":
    main()
