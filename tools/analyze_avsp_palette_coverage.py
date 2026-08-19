"""Does the shipped tile archive's palette cover what the routes actually draw?

The ROM tile renderer resolves each object's CPS colour bank through the tile
archive's own bank map (avsp_tiles_bank_slot). A bank the archive does not
carry cannot be resolved, so any object referencing it is a miss. This measures
the distance between what the archive ships and what the captured routes
reference - bank indices and counts only, no colour values, no ROM bytes.

WHY IT IS NOT A LIVE DEFECT TODAY. The tile path currently renders street
aliens only, and their banks (0x10-0x13) are shipped. The gap opens when S3
widens the tile path to the rest of the cast.

WHAT THE CONSTRAINT ACTUALLY IS. Not colour RAM: avsp_tiles.c accepts up to 32
palette slots and the measured peak CONCURRENT demand is far below that. The
binding constraint is archive CONTENT, and it resolves together with the tile
region budget under S3 phase loading - tools/gen_avsp_gfx_tiles.py already
refuses a --scope round1 archive against the real carve.

The paired test (tests/test_avsp_palette_coverage.py) pins this gap open so the
archive scope cannot be widened without widening the palette.

Output: data/avsp_palette_coverage.json (tracked). Skips cleanly without the
private captures.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

OUT_JSON = ROOT / "data" / "avsp_palette_coverage.json"
TILES_MANIFEST = ROOT / "data" / "avsp_gfx_tiles.json"

ROUTES = ("enemy_actions", "stalker_actions")
SAMPLE_STRIDE = 10          # declared below; the denominator is reported


def read_words(path: Path) -> list[int]:
    words: list[int] = []
    with path.open() as handle:
        next(handle)
        for line in handle:
            parts = line.split()
            if len(parts) >= 2:
                words.append(int(parts[1], 16))
    return words


def shipped_banks() -> list[int]:
    if not TILES_MANIFEST.is_file():
        return []
    manifest = json.loads(TILES_MANIFEST.read_text())
    banks = manifest.get("palette", {}).get("banks", [])
    return sorted(int(b, 16) if isinstance(b, str) else int(b) for b in banks)


def scan_route(route: str, shipped: set[int], decode) -> dict | None:
    root = ROOT / ".deps" / "mame" / route
    frames = sorted(root.glob("objram_active_*.tsv")) if root.is_dir() else []
    if not frames:
        return None
    sampled = frames[::SAMPLE_STRIDE]

    banks = Counter()
    inside = 0
    outside = 0
    frames_with_outside = 0
    peak_concurrent = 0

    for path in sampled:
        drawn = [e for e in decode(read_words(path)) if e["tile_code"] != 0]
        live = {e["colour"] for e in drawn}
        peak_concurrent = max(peak_concurrent, len(live))
        has_outside = False
        for entry in drawn:
            banks[entry["colour"]] += 1
            if entry["colour"] in shipped:
                inside += 1
            else:
                outside += 1
                has_outside = True
        if has_outside:
            frames_with_outside += 1

    total = inside + outside
    return {
        "route": route,
        "frames_available": len(frames),
        "frames_sampled": len(sampled),
        "sample_stride": SAMPLE_STRIDE,
        "distinct_banks_referenced": len(banks),
        "banks_referenced": sorted("0x%02X" % b for b in banks),
        "peak_concurrent_banks_per_frame": peak_concurrent,
        "drawn_objects_total": total,
        "drawn_objects_in_shipped_banks": inside,
        "drawn_objects_outside_shipped_banks": outside,
        "frames_containing_outside_bank_object": frames_with_outside,
        "uncovered_banks": sorted("0x%02X" % b for b in banks
                                  if b not in shipped),
    }


def main() -> int:
    shipped = shipped_banks()
    if not shipped:
        print("palette coverage: SKIPPED - tile manifest absent (%s)"
              % TILES_MANIFEST.relative_to(ROOT).as_posix())
        return 0
    try:
        from extract_avspu_stage1 import decode_object_entries
    except Exception as exc:                       # pragma: no cover
        print("palette coverage: SKIPPED - decoder unavailable (%s)" % exc)
        return 0

    shipped_set = set(shipped)
    routes = [r for r in (scan_route(name, shipped_set, decode_object_entries)
                          for name in ROUTES) if r]
    if not routes:
        print("palette coverage: SKIPPED - no object captures present")
        return 0

    manifest = {
        "schema": 1,
        "classification": "tile-archive palette coverage - bank indices and "
                          "counts only; no colour values, no ROM bytes",
        "question": "do the captured routes reference CPS colour banks that "
                    "the shipped tile archive does not carry?",
        "shipped_banks": ["0x%02X" % b for b in shipped],
        "shipped_bank_count": len(shipped),
        "shipped_palette_label": json.loads(
            TILES_MANIFEST.read_text()).get("palette", {}).get("label"),
        "archive_format_slot_limit": 32,
        "finding": "the archive ships a single-frame ADAPTED palette; the "
                   "routes reference more banks than it carries. This is not "
                   "a live defect while the ROM tile path renders street "
                   "aliens only (their banks are shipped), and it is NOT a "
                   "colour-RAM limit - avsp_tiles.c accepts 32 slots. The "
                   "binding constraint is archive content, which resolves "
                   "with the tile-region budget under S3 phase loading.",
        "recommendation": "defer regeneration to S3, when the full-cast tile "
                          "path is the consumer; the paired test pins this "
                          "gap open so scope cannot widen silently.",
        "routes": routes,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")

    print("palette coverage: shipped %d banks %s"
          % (len(shipped), ["0x%02X" % b for b in shipped]))
    for entry in routes:
        total = entry["drawn_objects_total"] or 1
        print("  %-16s refs %2d banks, peak %2d concurrent, %5.1f%% of drawn "
              "objects outside shipped, %d/%d frames affected"
              % (entry["route"], entry["distinct_banks_referenced"],
                 entry["peak_concurrent_banks_per_frame"],
                 100.0 * entry["drawn_objects_outside_shipped_banks"] / total,
                 entry["frames_containing_outside_bank_object"],
                 entry["frames_sampled"]))
    print("wrote", OUT_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
