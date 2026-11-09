#!/usr/bin/env python3
"""Decode a paused SAT_CPU_SLACK_PROFILE ring; every timestamp is on the master.

Optionally join a tools/vdp1_profile.py JSON report from the same paused capture
by source_vblank. Slave durations remain separate: clocks are never subtracted.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import struct

FIELDS = (
    "vblank", "flags", "period_ticks", "handoff_tick", "layers_done_tick",
    "irq_done_tick", "game_done_tick", "handoff_serial", "gfx_handed_end",
    "gfx_done_end", "stage_characters",
)
FINISHED, OVERRUN, HOME = 1, 2, 4
BUSY_BEGIN, BUSY_DONE, BUSY_END = 8, 16, 32
TIMER_WRAP, UNPAIRED_DONE, BAD_ORDER = 64, 128, 256
HANDED, PREVIOUS_OVERRUN = 512, 1024
MASK = UNKNOWN = 0xFFFFFFFF


def decode_ring(raw: bytes, endian: str = "big") -> list[dict]:
    size = len(FIELDS) * 4
    if not raw or len(raw) % size:
        raise ValueError(f"ring needs a nonzero multiple of {size} bytes")
    rows = [dict(zip(FIELDS, values)) for values in struct.iter_unpack(
        (">" if endian == "big" else "<") + "I" * len(FIELDS), raw)]
    rows = [r for r in rows if r["vblank"]]
    if len({r["vblank"] for r in rows}) != len(rows):
        raise ValueError("duplicate vblank tags: dump one ring from one paused capture")
    for row in rows:
        if row["flags"] & ~2047:
            raise ValueError("unknown CPU-slack flags: check build and decoder ABI")
        for name in FIELDS[2:7]:
            if row[name] != UNKNOWN and row[name] > 0xFFFF:
                raise ValueError(f"{name} is not a 16-bit master timer value")
    if not rows:
        return []
    newest = rows[0]["vblank"]
    for row in rows[1:]:
        if 0 < ((row["vblank"] - newest) & MASK) < 0x80000000:
            newest = row["vblank"]
    return sorted(rows, key=lambda r: (newest - r["vblank"]) & MASK, reverse=True)


def distribution(values: list[int]) -> dict:
    if not values:
        return {"count": 0}
    values = sorted(values)
    def percentile(fraction: float) -> int:
        return values[max(0, math.ceil(len(values) * fraction) - 1)]
    return {"count": len(values), "min": values[0], "p05": percentile(.05),
            "p50": percentile(.5), "p95": percentile(.95), "max": values[-1],
            "mean": round(sum(values) / len(values), 2)}


def summarize(rows: list[dict], *, candidate_ticks: int | None = None,
              reserve_ticks: int = 0, vdp1: dict | None = None) -> dict:
    if reserve_ticks < 0 or (candidate_ticks is not None and candidate_ticks < 0):
        raise ValueError("candidate and reserve ticks must be nonnegative")
    plots: dict[int, list[dict]] = {}
    frames: dict[int, dict] = {}
    if vdp1:
        for plot in vdp1.get("plot_rows", []):
            plots.setdefault(plot["source_vblank"], []).append(plot)
        frames = {f["vblank"]: f for f in vdp1.get("frame_rows", [])}
    samples = []
    for original in rows:
        row = dict(original)
        flags, period = row["flags"], row["period_ticks"]
        reasons = [label for bit, label in (
            (HOME, "home_hold"), (OVERRUN, "master_overrun"),
            (TIMER_WRAP, "timer_overflow"), (UNPAIRED_DONE, "unpaired_completion"),
            (BAD_ORDER, "inconsistent_phase_order")) if flags & bit]
        if not flags & FINISHED:
            reasons.append("no_paired_completion")
        phases = [row["irq_done_tick"], row["game_done_tick"], period]
        if flags & HANDED:
            phases[:0] = [row["handoff_tick"], row["layers_done_tick"]]
        if (not period or any(t == UNKNOWN for t in phases) or
                phases != sorted(phases)):
            if "inconsistent_phase_order" not in reasons:
                reasons.append("inconsistent_phase_order")
        row["excluded_from_window"] = reasons
        row["completion_window_ticks"] = None if reasons else period - row["game_done_tick"]
        if candidate_ticks is not None:
            row["candidate_fits_window_upper_bound"] = (
                not reasons and row["completion_window_ticks"] >= candidate_ticks + reserve_ticks)
        if vdp1 is not None:
            row["vdp1_source_plots"] = plots.get(row["vblank"], [])
            row["next_vblank_presentation"] = frames.get((row["vblank"] + 1) & MASK)
        samples.append(row)
    gameplay = [r for r in samples if not r["flags"] & HOME]
    valid = [r for r in gameplay if r["completion_window_ticks"] is not None]
    busy = [r for r in valid if r["flags"] & BUSY_DONE]
    busy_end = [r for r in valid if r["flags"] & BUSY_END]
    result = {
        "format_version": 1,
        "units": "master FRT ticks; no conversion or cross-CPU subtraction",
        "notes": [
            "Retained completed vblank windows only, not whole-run totals.",
            "Period is master timer reset to next IRQ entry; it omits that IRQ's prologue.",
            "Completion window is scheduler completion to next IRQ: an upper bound on usable slack, not measured idle cycles.",
            "The lifted f_11ec wait and later main-loop work must be traced before any of this window is treated as free time.",
            "Slave busy means the handoff is unfinished; it does not identify the command-build phase.",
            "Overrun, home, wrapped, unordered and unpaired samples never supply a completion window.",
            "Observed candidate fit is a necessary budget check, not proof that moving work is safe or faster.",
            "A joined VDP1 report must come from the same build and paused capture.",
        ],
        "counts": {
            "retained": len(samples), "gameplay": len(gameplay), "valid_completion_windows": len(valid),
            "master_overruns": sum(bool(r["flags"] & OVERRUN) for r in gameplay),
            "previous_master_overruns": sum(bool(r["flags"] & PREVIOUS_OVERRUN) for r in gameplay),
            "slave_busy_at_begin": sum(bool(r["flags"] & BUSY_BEGIN) for r in gameplay),
            "slave_busy_at_done_valid": len(busy), "slave_busy_at_end_valid": len(busy_end),
            "timer_overflow": sum(bool(r["flags"] & TIMER_WRAP) for r in samples),
            "unpaired_completion": sum(bool(r["flags"] & UNPAIRED_DONE) for r in samples),
            "vblank_gaps": sum(((b["vblank"] - a["vblank"]) & MASK) != 1
                               for a, b in zip(samples, samples[1:])),
        },
        "master_ticks": {name: distribution([r[name] for r in valid]) for name in (
            "period_ticks", "irq_done_tick", "game_done_tick")},
        "snapshot_handoff_ticks": distribution([r["handoff_tick"] for r in valid if r["flags"] & HANDED]),
        "snapshot_layers_done_ticks": distribution([r["layers_done_tick"] for r in valid if r["flags"] & HANDED]),
        "completion_window_ticks": distribution([r["completion_window_ticks"] for r in valid]),
        "completion_window_with_slave_busy_at_done": distribution([r["completion_window_ticks"] for r in busy]),
        "completion_window_with_slave_busy_at_next_irq": distribution([r["completion_window_ticks"] for r in busy_end]),
        "rows": samples,
    }
    if candidate_ticks is not None:
        result["candidate"] = {
            "work_ticks": candidate_ticks, "reserve_ticks": reserve_ticks,
            "fits_gameplay_window_upper_bound": sum(r["candidate_fits_window_upper_bound"] for r in gameplay),
            "total_gameplay_windows": len(gameplay),
            "fits_busy_end_window_upper_bound": sum(r["candidate_fits_window_upper_bound"] for r in busy_end),
            "valid_busy_end_windows": len(busy_end),
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ring", type=Path)
    parser.add_argument("--tier", required=True, choices=("HOST", "EMULATOR", "HARDWARE"))
    parser.add_argument("--build-ref", required=True)
    parser.add_argument("--scene", default="unspecified")
    parser.add_argument("--endian", choices=("big", "little"), default="big")
    parser.add_argument("--candidate-ticks", type=int)
    parser.add_argument("--reserve-ticks", type=int, default=0)
    parser.add_argument("--vdp1-report", type=Path)
    args = parser.parse_args()
    try:
        rows = decode_ring(args.ring.read_bytes(), args.endian)
        paired = json.loads(args.vdp1_report.read_text()) if args.vdp1_report else None
        result = summarize(rows, candidate_ticks=args.candidate_ticks,
                           reserve_ticks=args.reserve_ticks, vdp1=paired)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    result.update(tier=args.tier, build_ref=args.build_ref, scene=args.scene)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
