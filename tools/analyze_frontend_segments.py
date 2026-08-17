"""Segment the captured CPS2 frontend into Saturn-sized lossless payloads.

`tools/analyze_frontend.py` remains the validated whole-capture gate. This
sibling answers the follow-up question: which representation of the character
confirmation and Round 1 title fits the retired 78,848-byte frontend blocks.

It measures unique-frame transitions rather than raw samples, separates
palette-only (fade) steps from structural steps, and greedily splits each
window into segments that satisfy both the byte budget and the 255-colour
stable-palette limit.

The cost model reuses the byte accounting of `tools/analyze_frontend.py` so the
totals stay comparable:

- base frame: 3 bytes per palette colour plus count/value RLE of the index image
- structural step: 2-byte header, 4 bytes per changed-run command, 1 byte per
  payload pixel, plus 3 bytes per newly introduced colour
- palette-only step: 2-byte header plus 4 bytes per changed CRAM entry

All costs depend only on the equality pattern of the pixels, never on palette
ordering, so the report is deterministic.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
CAPTURE_ROOT = ROOT / ".deps" / "mame" / "frontend"
FIRST_FRAME = 1320
LAST_FRAME = 2160
CADENCE = 2
SOURCE_SIZE = (384, 224)
SATURN_WIDTH = 352
SATURN_HEIGHT = 224
FRONTEND_BLOCK_BYTES = 78848
MAX_STABLE_PALETTE = 255

DEFAULT_WINDOWS = (
    ("start_transition", 1770, 1798),
    ("character_confirm", 1800, 2038),
    ("round_1_title", 2040, 2160),
)


def source_columns() -> np.ndarray:
    """Reproduce the 384-to-352 horizontal fit of the validated analyzer."""
    x = np.arange(SATURN_WIDTH, dtype=np.int64)
    return (x * (SOURCE_SIZE[0] - 1) +
            (SATURN_WIDTH - 1) // 2) // (SATURN_WIDTH - 1)


def load_fitted(frame: int, columns: np.ndarray) -> np.ndarray:
    """Return the horizontally fitted frame as packed 0x00RRGGBB values."""
    path = CAPTURE_ROOT / f"frontend_{frame:04d}.png"
    with Image.open(path) as source:
        image = source.convert("RGB")
    if image.size != SOURCE_SIZE:
        raise ValueError(f"frontend frame {frame} changed size: {image.size}")
    rgb = np.asarray(image, dtype=np.uint32)
    packed = (rgb[:, :, 0] << 16) | (rgb[:, :, 1] << 8) | rgb[:, :, 2]
    return np.ascontiguousarray(packed[:, columns]).reshape(-1)


def rle_size(values: np.ndarray) -> int:
    """Count/value RLE cost in bytes with a 255-length command limit."""
    if values.size == 0:
        return 0
    starts = np.flatnonzero(np.r_[True, values[1:] != values[:-1]])
    lengths = np.diff(np.r_[starts, values.size])
    return int(np.sum((lengths + 254) // 255) * 2)


def coalesced_delta(prior: np.ndarray, current: np.ndarray) -> tuple[int, int]:
    """Return (commands, payload_bytes) for the coalesced row-delta encoder.

    A command absorbs gaps of up to four identical pixels so short stretches of
    unchanged pixels do not fragment one run into several commands.
    """
    differs = prior != current
    rows = differs.reshape(SATURN_HEIGHT, SATURN_WIDTH)
    commands = 0
    payload = 0
    for row_index in np.flatnonzero(rows.any(axis=1)):
        row = rows[row_index]
        changed = np.flatnonzero(row)
        x = 0
        limit = row.size
        while x < limit:
            if not row[x]:
                x += 1
                continue
            end = x + 1
            last_change = x
            while end < limit and end - x < 255:
                if row[end]:
                    last_change = end
                elif end - last_change > 4:
                    break
                end += 1
            count = last_change - x + 1
            commands += 1
            payload += count
            x += count
        del changed
    return commands, payload


def changed_box(prior: np.ndarray,
                current: np.ndarray) -> dict[str, int] | None:
    """Bounding box of the pixels that differ between two fitted frames.

    A small box means the step belongs in a native VDP1 overlay or a scrolling
    VDP2 layer instead of a stored full-screen delta.
    """
    differs = (prior != current).reshape(SATURN_HEIGHT, SATURN_WIDTH)
    rows = np.flatnonzero(differs.any(axis=1))
    if rows.size == 0:
        return None
    columns = np.flatnonzero(differs.any(axis=0))
    return {
        "x": int(columns[0]),
        "y": int(rows[0]),
        "width": int(columns[-1] - columns[0] + 1),
        "height": int(rows[-1] - rows[0] + 1),
        "changed_pixels": int(np.count_nonzero(differs)),
    }


def index_image(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return (palette, index image) for one frame."""
    palette, indices = np.unique(values, return_inverse=True)
    return palette, indices.astype(np.int64)


def palette_only_step(indices: np.ndarray, palette_size: int,
                      values: np.ndarray) -> np.ndarray | None:
    """Return the recoloured palette when the index image still reproduces the
    frame exactly, otherwise None.

    The frame is a pure palette change when every pixel sharing an index also
    shares one colour. The index image is then untouched and only CRAM entries
    are rewritten, which is how source fades should be encoded.
    """
    lowest = np.full(palette_size, np.iinfo(np.uint32).max, dtype=np.uint32)
    highest = np.zeros(palette_size, dtype=np.uint32)
    np.minimum.at(lowest, indices, values)
    np.maximum.at(highest, indices, values)
    present = np.bincount(indices, minlength=palette_size) > 0
    if not np.array_equal(lowest[present], highest[present]):
        return None
    return np.where(present, highest, 0)


def unique_runs(frames: list[int],
                pixels: dict[int, np.ndarray]) -> list[dict[str, int]]:
    """Collapse consecutive identical samples into held unique frames."""
    runs: list[dict[str, int]] = []
    for frame in frames:
        values = pixels[frame]
        if runs and np.array_equal(pixels[runs[-1]["frame"]], values):
            runs[-1]["held_samples"] += 1
            continue
        runs.append({"frame": frame, "held_samples": 1})
    return runs


def measure_window(name: str, first: int, last: int, frames: list[int],
                   pixels: dict[int, np.ndarray],
                   budget: int) -> dict[str, object]:
    selected = [frame for frame in frames if first <= frame <= last]
    runs = unique_runs(selected, pixels)
    union = np.unique(np.concatenate([pixels[frame] for frame in selected]))

    palette, indices = index_image(pixels[runs[0]["frame"]])
    base_bytes = base_frame_bytes(palette, indices)
    base_rle = int(palette.size) * 3 + rle_size(indices.astype(np.uint8))
    base_raw = int(palette.size) * 3 + SATURN_WIDTH * SATURN_HEIGHT
    total = base_bytes
    palette_steps = 0
    structural_steps = 0
    palette_bytes = 0
    structural_bytes = 0
    steps: list[dict[str, object]] = []

    known = set(palette.tolist())
    live_palette = palette.copy()
    prior_values = pixels[runs[0]["frame"]]
    boxes: list[dict[str, int]] = []

    segments: list[dict[str, object]] = []
    segment_start = runs[0]["frame"]
    segment_bytes = base_bytes
    segment_colours = set(palette.tolist())

    for run in runs[1:]:
        frame = run["frame"]
        values = pixels[frame]
        recoloured = palette_only_step(indices, live_palette.size, values)
        if recoloured is not None:
            changed = int(np.count_nonzero(recoloured != live_palette))
            cost = 2 + changed * 4
            kind = "palette"
            palette_steps += 1
            palette_bytes += cost
        else:
            commands, payload = coalesced_delta(prior_values, values)
            new_colours = [int(value) for value in np.unique(values)
                           if int(value) not in known]
            cost = 2 + commands * 4 + payload + len(new_colours) * 3
            kind = "structural"
            structural_steps += 1
            structural_bytes += cost
        total += cost
        box = changed_box(prior_values, values)
        steps.append({
            "frame": frame,
            "kind": kind,
            "bytes": cost,
            "held_samples": run["held_samples"],
            "changed_box": box,
        })
        if box is not None:
            boxes.append(box)

        frame_colours = set(int(value) for value in np.unique(values))
        would_exceed = segment_bytes + cost > budget
        would_overflow = len(segment_colours | frame_colours) > MAX_STABLE_PALETTE
        if would_exceed or would_overflow:
            segments.append({
                "first_frame": segment_start,
                "last_frame": prior_frame_of(runs, frame),
                "bytes": segment_bytes,
                "colours": len(segment_colours),
                "over_budget": bool(segment_bytes > budget),
            })
            new_palette, new_indices = index_image(values)
            segment_start = frame
            segment_bytes = base_frame_bytes(new_palette, new_indices)
            segment_colours = set(new_palette.tolist())
        else:
            segment_bytes += cost
            segment_colours |= frame_colours

        if kind == "palette":
            live_palette = recoloured
        else:
            palette, indices = index_image(values)
            live_palette = palette
            known |= set(palette.tolist())
        prior_values = values

    segments.append({
        "first_frame": segment_start,
        "last_frame": runs[-1]["frame"],
        "bytes": segment_bytes,
        "colours": len(segment_colours),
        "over_budget": bool(segment_bytes > budget),
    })

    reference = reference_model(runs, pixels)

    if boxes:
        left = min(box["x"] for box in boxes)
        top = min(box["y"] for box in boxes)
        right = max(box["x"] + box["width"] for box in boxes)
        bottom = max(box["y"] + box["height"] for box in boxes)
        motion = {
            "x": left,
            "y": top,
            "width": right - left,
            "height": bottom - top,
            "screen_fraction": round((right - left) * (bottom - top) /
                                     (SATURN_WIDTH * SATURN_HEIGHT), 4),
            "max_changed_pixels_in_one_step":
                max(box["changed_pixels"] for box in boxes),
        }
    else:
        motion = None

    return {
        "name": name,
        "first_frame": first,
        "last_frame": last,
        "sample_count": len(selected),
        "unique_frames": len(runs),
        "distinct_images": len({pixels[run["frame"]].tobytes()
                                for run in runs}),
        "fitted_colour_union": int(union.size),
        "single_stable_palette_possible": bool(union.size <=
                                               MAX_STABLE_PALETTE),
        "base_frame_bytes": base_bytes,
        "base_frame_rle_bytes": base_rle,
        "base_frame_raw_bytes": base_raw,
        "base_frame_exceeds_block": bool(base_bytes > FRONTEND_BLOCK_BYTES),
        "motion_box": motion,
        "reference_frame_model": reference,
        "palette_only_steps": palette_steps,
        "structural_steps": structural_steps,
        "palette_only_bytes": palette_bytes,
        "structural_bytes": structural_bytes,
        "unique_transition_total_bytes": total,
        "fits_one_block": bool(total <= budget),
        "fits_two_blocks": bool(total <= budget * 2),
        "segment_budget_bytes": budget,
        "segments_required": len(segments),
        "segmentation_feasible": bool(
            not any(segment["over_budget"] for segment in segments)),
        "segments": segments,
        "steps": steps,
    }


def reference_model(runs: list[dict[str, int]],
                    pixels: dict[int, np.ndarray]) -> dict[str, object]:
    """Cost the window as one fully-lit reference frame plus CRAM updates.

    A fade to or from black is not a function of a dark frame, because many
    distinct source colours collapse onto the same dark value and cannot be
    split again. It *is* a function of the fully-lit frame, so the reference
    must be the most colourful frame in the window. When a fade dominates, the
    window collapses to one stored image plus per-frame palette writes.
    """
    reference = max(runs, key=lambda run: np.unique(pixels[run["frame"]]).size)
    values = pixels[reference["frame"]]
    palette, indices = index_image(values)
    total = base_frame_bytes(palette, indices)
    matched = 0
    live = palette.copy()
    for run in runs:
        if run["frame"] == reference["frame"]:
            continue
        recoloured = palette_only_step(indices, palette.size,
                                       pixels[run["frame"]])
        if recoloured is None:
            continue
        matched += 1
        total += 2 + int(np.count_nonzero(recoloured != live)) * 4
        live = recoloured
    return {
        "reference_frame": reference["frame"],
        "reference_colours": int(palette.size),
        "reference_frame_bytes": base_frame_bytes(palette, indices),
        "palette_only_frames": matched,
        "structural_frames": len(runs) - 1 - matched,
        "covered_fraction": round((matched + 1) / len(runs), 4),
        "bytes_if_fully_covered": total,
    }


def base_frame_bytes(palette: np.ndarray, indices: np.ndarray) -> int:
    """Cheapest lossless encoding of one full frame.

    Count/value RLE expands busy full-screen art past the 78,848-byte raw
    size, so a real encoder stores whichever is smaller.
    """
    overhead = int(palette.size) * 3
    return overhead + min(rle_size(indices.astype(np.uint8)),
                          SATURN_WIDTH * SATURN_HEIGHT)


def prior_frame_of(runs: list[dict[str, int]], frame: int) -> int:
    for index, run in enumerate(runs):
        if run["frame"] == frame:
            return runs[index - 1]["frame"]
    raise ValueError(f"frame {frame} is not a unique-run boundary")


def parse_window(text: str) -> tuple[str, int, int]:
    name, first, last = text.split(":")
    return name, int(first), int(last)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--window", action="append", default=None,
                        metavar="NAME:FIRST:LAST",
                        help="measure an ad-hoc window instead of the defaults")
    parser.add_argument("--budget", type=int, default=FRONTEND_BLOCK_BYTES,
                        help="per-segment byte budget (default: one retired "
                             "78,848-byte frontend block)")
    parser.add_argument("--report", action="store_true",
                        help="write data/frontend_segments.json")
    args = parser.parse_args()

    windows = ([parse_window(text) for text in args.window]
               if args.window else list(DEFAULT_WINDOWS))

    expected_frames = list(range(FIRST_FRAME, LAST_FRAME + 1, CADENCE))
    with (CAPTURE_ROOT / "samples.tsv").open(newline="",
                                             encoding="ascii") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if [int(row["frame"]) for row in rows] != expected_frames:
        raise ValueError("dense frontend frame schedule changed")

    needed = sorted({frame for _, first, last in windows
                     for frame in expected_frames if first <= frame <= last})
    columns = source_columns()
    pixels = {frame: load_fitted(frame, columns) for frame in needed}

    reports = [measure_window(name, first, last, expected_frames, pixels,
                              args.budget)
               for name, first, last in windows]

    report = {
        "source": {
            "romset": "avspu",
            "mame_version": "0.289",
            "cadence": CADENCE,
            "width": SATURN_WIDTH,
            "height": SATURN_HEIGHT,
            "note": "cadence 2 sizes are lower bounds; recapture at cadence 1 "
                    "before fixing the shipped layout",
        },
        "frontend_block_bytes": FRONTEND_BLOCK_BYTES,
        "segment_budget_bytes": args.budget,
        "windows": reports,
    }

    for window in reports:
        print(
            f"{window['name']}: {window['unique_frames']} runs over "
            f"{window['distinct_images']} distinct images, "
            f"union {window['fitted_colour_union']} colours, "
            f"{window['palette_only_steps']} palette steps, "
            f"{window['structural_steps']} structural steps, "
            f"total {window['unique_transition_total_bytes']} bytes"
        )
        box = window["motion_box"]
        if box is not None:
            print(
                f"    motion box {box['width']}x{box['height']} at "
                f"({box['x']},{box['y']}), "
                f"{box['screen_fraction'] * 100:.1f}% of screen, "
                f"peak {box['max_changed_pixels_in_one_step']} changed pixels"
            )
        print(
            f"    base frame: RLE {window['base_frame_rle_bytes']} vs raw "
            f"{window['base_frame_raw_bytes']} bytes; "
            f"exceeds one block: {window['base_frame_exceeds_block']}"
        )
        model = window["reference_frame_model"]
        print(
            f"    reference-frame model: frame {model['reference_frame']} "
            f"({model['reference_colours']} colours, "
            f"{model['reference_frame_bytes']} bytes) covers "
            f"{model['palette_only_frames']}/{window['unique_frames'] - 1} "
            f"later frames as palette-only "
            f"({model['covered_fraction'] * 100:.0f}% of window), "
            f"{model['bytes_if_fully_covered']} bytes for the covered part"
        )
        if not window["segmentation_feasible"]:
            print(
                f"    INFEASIBLE at {window['segment_budget_bytes']} bytes: "
                "one base frame alone exceeds the budget"
            )
        print(f"    {window['segments_required']} segment(s):")
        for segment in window["segments"]:
            flag = " OVER BUDGET" if segment["over_budget"] else ""
            print(
                f"      {segment['first_frame']}..{segment['last_frame']}: "
                f"{segment['bytes']} bytes, {segment['colours']} colours{flag}"
            )

    if args.report:
        output = ROOT / "data" / "frontend_segments.json"
        output.write_text(json.dumps(report, indent=2) + "\n",
                          encoding="ascii")
        print(f"Wrote {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
