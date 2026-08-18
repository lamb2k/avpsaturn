"""Measure AvP's own per-frame CPS2 sprite demand, from captured object lists.

Phase A asks whether AvP can be rendered as one VDP1 16x16 command per source
tile instead of precomposed per-palette cels. The demand side of that question
is answerable today, with no Saturn code and no renderer prototype, because the
CPS2 active object list *is* the tile list: AvP and the official Capcom Saturn
reference title run on the same arcade hardware, so the source primitive is
identical and only the volume differs.

Field layout is taken from MAME 0.289 `cps2_render_sprites` / `find_last_sprite`
(`.deps/mame-src/src/mame/capcom/cps2.cpp`), not inferred:

    word 0  x        priority = (x >> 13) & 7
    word 1  y        code high bits = (y & 0x6000) << 3
    word 2  code
    word 3  attr     palette = attr & 0x1F      (32 banks of 16 colours)
                     flipx   = bit 5, flipy = bit 6
                     blocked sprite when attr & 0xFF00:
                       nx = ((attr & 0x0F00) >> 8) + 1
                       ny = ((attr & 0xF000) >> 12) + 1

    list ends at the first entry with y >= 0x8000 or attr >= 0xFF00

Every emitted field is `MEASURED` (read from a capture) or `DECODED` (computed
losslessly from one). No Saturn budget is asserted here; this reports demand,
and the phase-A decision compares it against Saturn limits separately.

Input is the tracked-format `objram_active_NNNNN.tsv` captures under `.deps`
(private, ignored). Output is a copyright-safe report: counts only, no tile
data, no pixels, no palette colours.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBJ_WORDS = 4


def read_objram(path: Path) -> list[int]:
    words = []
    for line in path.read_text().splitlines()[1:]:
        parts = line.split("\t")
        if len(parts) == 2:
            words.append(int(parts[1], 16))
    return words


def scan_frame(words: list[int]) -> dict:
    """One frame's live object list, decoded exactly as MAME draws it."""
    objects = 0
    tiles = 0
    palettes: set[int] = set()
    codes: set[int] = set()
    blocked = 0
    widest = 0
    off = 0
    while off + OBJ_WORDS <= len(words):
        y = words[off + 1]
        attr = words[off + 3]
        if y >= 0x8000 or attr >= 0xFF00:
            break
        code = words[off + 2] + ((y & 0x6000) << 3)
        nx = ((attr & 0x0F00) >> 8) + 1
        ny = ((attr & 0xF000) >> 12) + 1
        if attr & 0xFF00:
            blocked += 1
        objects += 1
        tiles += nx * ny
        widest = max(widest, nx * ny)
        palettes.add(attr & 0x1F)
        for iy in range(ny):
            for ix in range(nx):
                codes.add((code + iy * 16 + ix) & 0xFFFF)
        off += OBJ_WORDS
    return {
        "objects": objects,
        "tiles_16x16": tiles,
        "distinct_palettes": len(palettes),
        "distinct_tile_codes": len(codes),
        "blocked_objects": blocked,
        "largest_object_tiles": widest,
    }


def summarize(rows: list[tuple[int, dict]]) -> dict:
    def peak(key):
        f, v = max(rows, key=lambda r: r[1][key])
        return {"value": v[key], "at_source_frame": f}

    def mean(key):
        return round(sum(r[1][key] for r in rows) / len(rows), 2)

    return {
        "frames": len(rows),
        "source_frame_first": rows[0][0],
        "source_frame_last": rows[-1][0],
        "peak_objects": peak("objects"),
        "peak_tiles_16x16": peak("tiles_16x16"),
        "peak_distinct_palettes": peak("distinct_palettes"),
        "peak_distinct_tile_codes": peak("distinct_tile_codes"),
        "peak_largest_object_tiles": peak("largest_object_tiles"),
        "mean_objects": mean("objects"),
        "mean_tiles_16x16": mean("tiles_16x16"),
        "mean_distinct_palettes": mean("distinct_palettes"),
        "mean_distinct_tile_codes": mean("distinct_tile_codes"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--capture-root", required=True, action="append",
                    help="directory holding objram_active_NNNNN.tsv; repeatable")
    ap.add_argument("--label", required=True, action="append",
                    help="route label for the matching --capture-root")
    ap.add_argument("--output", default=str(ROOT / "data" / "avsp_sprite_demand.json"))
    args = ap.parse_args()

    routes = []
    overall: list[tuple[int, dict]] = []
    for root, label in zip(args.capture_root, args.label):
        d = Path(root)
        files = sorted(d.glob("objram_active_*.tsv"))
        if not files:
            print("no captures under %s" % d)
            return 2
        rows = []
        for f in files:
            frame = int(f.stem.rsplit("_", 1)[1])
            rows.append((frame, scan_frame(read_objram(f))))
        rows.sort(key=lambda r: r[0])
        overall.extend(rows)
        routes.append({
            "label": label,
            "capture_root": str(d).replace("\\", "/"),
            "evidence": "MEASURED",
            "summary": summarize(rows),
        })

    overall.sort(key=lambda r: r[0])
    report = {
        "schema": 1,
        "classification": "AvP per-frame CPS2 sprite demand - counts only, no graphics data",
        "field_layout_source": "MAME 0.289 cps2_render_sprites / find_last_sprite",
        "field_layout_evidence": "DECODED",
        "what_this_does_not_claim": [
            "no Saturn VDP1 or colour-RAM budget is asserted here; this is the demand side only",
            "tile codes are counted, never emitted; no graphics data is in this report",
            "a per-tile pipeline still needs its own Saturn-side command-build and fill-rate measurement",
        ],
        "routes": routes,
        "combined": summarize(overall),
    }
    text = json.dumps(report, indent=1, sort_keys=True) + "\n"
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    print("wrote %s (sha256=%s)" % (out, hashlib.sha256(text.encode()).hexdigest()))
    c = report["combined"]
    print("frames=%d" % c["frames"])
    for k in ("peak_objects", "peak_tiles_16x16", "peak_distinct_palettes",
              "peak_distinct_tile_codes", "peak_largest_object_tiles"):
        print("  %-28s %5d  (frame %d)" % (k, c[k]["value"], c[k]["at_source_frame"]))
    for k in ("mean_objects", "mean_tiles_16x16", "mean_distinct_palettes",
              "mean_distinct_tile_codes"):
        print("  %-28s %8.2f" % (k, c[k]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
