#!/usr/bin/env python3
"""Read-only Round 1 shrink and sprite-load census (no asset writes).

Walks the retained paired source object stream (frames 1972..15193) and reports:
  * tile unions under each shrink step: observed facing only, blank removal,
    identical-payload dedupe, mirror dedupe (VDP1 can flip without extra data);
  * per-segment tile/bank unions, for load-seam planning;
  * per-frame sprite counts and pixel load (source object list), against the
    CPS2 limit and as input for the VDP1 budget.

Numbers only: no ROM bytes or pixels are written.
Tier: SOURCE_CAPTURE (MAME retained evidence). Not a native or Saturn measure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import extract_avspu_stage1 as avsp  # noqa: E402
from census_full_route import RouteState  # noqa: E402
from gen_avsp_gfx_tiles import (  # noqa: E402
    entry_tile_codes,
    entry_tile_codes_exact,
    tile_texture,
)

FIRST, LAST = 1972, 15193
TILE_RECORD = 132  # 128 payload + 4 index
HEADER = 48
BANK = 32


def segments() -> list[dict]:
    rows = [{"first": FIRST, "last": 5566}]
    for path in sorted((ROOT / "data").glob("oracle10_round1_census_extension_*.json")):
        first, last = path.stem.rsplit("_", 2)[1:]
        rows.append({"first": int(first), "last": int(last)})
    rows.sort(key=lambda row: row["first"])
    return rows


def mirrors(payload: bytes) -> list[bytes]:
    """Payload under H, V and HV flip (8 bytes per row, 4bpp)."""
    rows = [payload[i:i + 8] for i in range(0, 128, 8)]
    hflip = [bytes(((b & 15) << 4) | (b >> 4) for b in reversed(row)) for row in rows]
    return [b"".join(hflip), b"".join(reversed(rows)), b"".join(reversed(hflip))]


def shrink(codes: set[int], gfx, cache: dict) -> dict:
    groups, blank, identical = set(), 0, set()
    for code in codes:
        if code not in cache:
            cache[code] = tile_texture(gfx, code)
        data = cache[code]
        if not any(data):
            blank += 1
            continue
        identical.add(data)
        groups.add(min([data] + mirrors(data)))
    return {"codes": len(codes), "blank": blank, "unique_payloads": len(identical),
            "unique_mod_flip": len(groups),
            "payload_bytes_raw": 128 * len(codes),
            "payload_bytes_after_blank": 128 * (len(codes) - blank),
            "payload_bytes_unique": 128 * len(identical),
            "payload_bytes_unique_mod_flip": 128 * len(groups)}


def walk(capture: Path) -> dict:
    gfx = avsp.load_gfx_region()
    cache: dict = {}
    segs = segments()
    for seg in segs:
        seg.update(exact=set(), both=set(), banks=set(), peak_entries=0,
                   peak_tile_cells=0, peak_on_screen_px=0, peak_frame=None)
    state = RouteState(capture)
    exact_all, both_all, banks_all = set(), set(), set()
    frames = entries_total = 0
    histogram = {}
    peak = {"entries": 0, "cells": 0, "px": 0, "commands_gt14": 0}
    digest = hashlib.sha256()
    try:
        for rec in state.frames():
            frame = rec["frame"]
            if frame < FIRST:
                continue
            if frame > LAST:
                break
            seg = next(s for s in segs if s["first"] <= frame <= s["last"])
            active = state.current["objram2" if rec["active_bank"] else "objram1"]
            entries = cells = onscreen = 0
            for offset in range(0, len(active) - 7, 8):
                row = active[offset:offset + 8]
                x, y, code, attr = (int.from_bytes(row[i:i + 2], "big") for i in (0, 2, 4, 6))
                if y >= 0x8000 or attr >= 0xFF00:
                    break
                exact = entry_tile_codes_exact(code, y, attr)
                both = entry_tile_codes(code, y, attr)
                nx, ny = ((attr >> 8) & 15) + 1, ((attr >> 12) & 15) + 1
                exact_all |= exact
                both_all |= both
                seg["exact"] |= exact
                seg["both"] |= both
                banks_all.add(attr & 31)
                seg["banks"].add(attr & 31)
                entries += 1
                cells += nx * ny
                sx, sy = x & 0x3FF, y & 0x3FF
                sx = sx - 1024 if sx >= 512 else sx
                sy = sy - 1024 if sy >= 512 else sy
                # CPS2 raster offset is camera-independent at 64,16 in this game
                # capture frame; clip conservatively to a full 512x512 window, so
                # px is an upper bound on on-screen pixels.
                onscreen += nx * ny * 256
                digest.update(row)
            frames += 1
            entries_total += entries
            bucket = entries // 16 * 16
            histogram[bucket] = histogram.get(bucket, 0) + 1
            if entries > seg["peak_entries"]:
                seg["peak_entries"] = entries
                seg["peak_frame"] = frame
            seg["peak_tile_cells"] = max(seg["peak_tile_cells"], cells)
            seg["peak_on_screen_px"] = max(seg["peak_on_screen_px"], onscreen)
            peak["entries"] = max(peak["entries"], entries)
            peak["cells"] = max(peak["cells"], cells)
            peak["px"] = max(peak["px"], onscreen)
    finally:
        state.close()
    out_segs = []
    for seg in segs:
        out_segs.append({
            "first": seg["first"], "last": seg["last"],
            "banks": len(seg["banks"]), "bank_list": sorted(seg["banks"]),
            "peak_entries": seg["peak_entries"], "peak_frame": seg["peak_frame"],
            "peak_tile_cells": seg["peak_tile_cells"],
            "peak_px_upper_bound": seg["peak_on_screen_px"],
            "exact": shrink(seg["exact"], gfx, cache),
            "both": shrink(seg["both"], gfx, cache)})
    return {"tier": "SOURCE_CAPTURE", "capture": capture.name, "frames": frames,
            "entries": entries_total, "object_stream_sha256": digest.hexdigest(),
            "banks": sorted(banks_all),
            "union_exact": shrink(exact_all, gfx, cache),
            "union_both_facings": shrink(both_all, gfx, cache),
            "peak": peak,
            "entries_histogram_16": dict(sorted(histogram.items())),
            "segments": out_segs}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--capture", default="full_route")
    args = parser.parse_args()
    result = walk(ROOT / ".deps/mame" / args.capture)
    args.output.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in ("frames", "entries", "banks", "union_exact",
                                             "union_both_facings", "peak")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
