"""Extract the native geometry of the CPS2 character-confirm transition.

`tools/analyze_frontend_segments.py` established that the confirm window is not
video: it is a transform of a surface the runtime already holds. This analyzer
recovers that transform and proves it reproduces the capture exactly, so the
Saturn can render the sequence from the resident character-select surface with
no stored frames.

Two claims are validated against the raw capture and the run raises if either
fails:

1. The wipe is a row shutter, not a vertical squeeze. Every row of every wipe
   frame is either byte-identical to the static pre-wipe frame or entirely
   black. A squeeze would resample rows and fail this test.
2. The visible band closes linearly and symmetrically about a fixed centre at
   a constant number of rows per source frame.

The result is a handful of integers instead of a stored animation. Because the
capture cadence is 2, the start frame and per-frame rate are only determined to
within one source frame; the recorded model must be re-fitted against a
cadence-1 capture before any timeline is called capture-exact.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

import analyze_frontend_segments as segments
from analyze_frontend_segments import (ROOT, SATURN_HEIGHT, SATURN_WIDTH,
                                       load_fitted, source_columns)


STATIC_FRAME = 1852
WIPE_FIRST = 1884
WIPE_LAST = 1908


def visible_band(frame: np.ndarray) -> tuple[int, int] | None:
    rows = np.flatnonzero((frame != 0).any(axis=1))
    if rows.size == 0:
        return None
    return int(rows[0]), int(rows[-1])


def validate_shutter(static: np.ndarray,
                     frames: dict[int, np.ndarray]) -> list[dict[str, object]]:
    """Prove every wipe frame is the static frame clipped to a row band."""
    observations: list[dict[str, object]] = []
    for frame in sorted(frames):
        current = frames[frame]
        band = visible_band(current)
        if band is None:
            observations.append({
                "frame": frame, "top": None, "bottom": None, "height": 0,
            })
            continue
        top, bottom = band
        inside = current[top:bottom + 1]
        if not np.array_equal(inside, static[top:bottom + 1]):
            raise ValueError(
                f"frame {frame} is not the static frame inside rows "
                f"{top}..{bottom}; the wipe is not a pure row shutter")
        outside = np.ones(SATURN_HEIGHT, dtype=bool)
        outside[top:bottom + 1] = False
        if current[outside].any():
            raise ValueError(
                f"frame {frame} has non-black pixels outside rows "
                f"{top}..{bottom}")
        observations.append({
            "frame": frame,
            "top": top,
            "bottom": bottom,
            "height": bottom - top + 1,
        })
    return observations


def fit_linear_shutter(observations: list[dict[str, object]],
                       static: np.ndarray,
                       cadence: int) -> dict[str, object]:
    """Fit top(f) and bottom(f) as lines and require exact integer residuals.

    The caller's window may include held frames before the shutter starts, so
    the static prefix is located and excluded here rather than assumed away.
    Its last frame bounds the start from below; the fitted line extrapolated
    back to the content extent bounds it from above.
    """
    points = [entry for entry in observations if entry["top"] is not None]
    if len(points) < 3:
        raise ValueError("not enough visible wipe frames to fit a shutter")

    content_rows = np.flatnonzero((static != 0).any(axis=1))
    content_top = int(content_rows[0])
    content_bottom = int(content_rows[-1])

    moving = [entry for entry in points if int(entry["top"]) > content_top]
    if len(moving) < 3:
        raise ValueError("not enough moving samples to fit a shutter")
    held = [entry for entry in points if int(entry["top"]) == content_top]
    if any(int(entry["top"]) < content_top for entry in points):
        raise ValueError("a sample opens above the static content extent")
    last_static = max((int(entry["frame"]) for entry in held), default=None)
    if last_static is not None and last_static > int(moving[0]["frame"]):
        raise ValueError("static and moving samples interleave")

    fit = moving
    frames = np.array([entry["frame"] for entry in fit], dtype=np.int64)
    tops = np.array([entry["top"] for entry in fit], dtype=np.int64)
    bottoms = np.array([entry["bottom"] for entry in fit], dtype=np.int64)

    top_steps = np.diff(tops) // (np.diff(frames) // cadence)
    bottom_steps = np.diff(bottoms) // (np.diff(frames) // cadence)
    if len(set(top_steps.tolist())) != 1:
        raise ValueError(f"top edge is not linear: steps {top_steps.tolist()}")
    if len(set(bottom_steps.tolist())) != 1:
        raise ValueError(
            f"bottom edge is not linear: steps {bottom_steps.tolist()}")

    per_sample = int(top_steps[0])
    if int(bottom_steps[0]) != -per_sample:
        raise ValueError("shutter is not symmetric about its centre")
    if per_sample % cadence:
        raise ValueError(
            f"{per_sample} rows per {cadence}-frame sample is not an integer "
            "rows-per-frame rate")
    per_frame = per_sample // cadence

    centres = {(top + bottom) / 2 for top, bottom in zip(tops, bottoms)}
    if len(centres) != 1:
        raise ValueError(f"shutter centre moves: {sorted(centres)}")
    centre = centres.pop()

    # Extrapolate the opening frame from the fitted line back to the static
    # content extent.
    reference = fit[0]
    offset = (int(reference["top"]) - content_top) // per_frame
    start_frame = int(reference["frame"]) - offset
    # The true start lies in [last_static, last_static + cadence): the shutter
    # had not moved at the last held sample, and the extrapolated line places
    # it before the first moving sample. A gap of a full cadence or more means
    # the model disagrees with the capture rather than merely under-sampling.
    if last_static is not None and not (
            0 <= start_frame - last_static < cadence):
        raise ValueError(
            f"extrapolated start {start_frame} is inconsistent with the last "
            f"held sample {last_static} at cadence {cadence}")

    residuals = []
    for entry in fit:
        expected_top = content_top + per_frame * (entry["frame"] - start_frame)
        residuals.append(int(entry["top"]) - expected_top)
    if any(residuals):
        raise ValueError(f"linear model does not reproduce tops: {residuals}")

    closes_at = start_frame + (int(reference["bottom"]) + offset * per_frame -
                               content_top) / (2 * per_frame)
    return {
        "rows_per_source_frame_per_edge": per_frame,
        "rows_per_sample_per_edge": per_sample,
        "centre_row": centre,
        "content_top_row": content_top,
        "content_bottom_row": content_bottom,
        "fitted_start_source_frame": start_frame,
        "start_frame_ambiguity_source_frames": (
            0 if last_static == start_frame else cadence - 1),
        "last_held_sample": last_static,
        "held_samples_before_wipe": len(held),
        "moving_samples": len(moving),
        "fully_closed_by_source_frame": WIPE_LAST,
        "closes_at_fractional_frame": round(closes_at, 3),
        "top_residuals": residuals,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", action="store_true",
                        help="write the geometry report")
    parser.add_argument("--capture-root", default=None,
                        help="capture directory relative to the repository "
                             "root (default: the cadence-2 frontend capture)")
    parser.add_argument("--cadence", type=int, default=segments.CADENCE,
                        help="source frames between samples in that capture")
    parser.add_argument("--first", type=int, default=WIPE_FIRST,
                        help="first wipe sample to validate")
    parser.add_argument("--last", type=int, default=WIPE_LAST,
                        help="last wipe sample to validate")
    parser.add_argument("--static-frame", type=int, default=STATIC_FRAME,
                        help="the held frame the shutter clips; it must exist "
                             "inside the chosen capture")
    parser.add_argument("--output", default="data/frontend_geometry.json",
                        help="report path relative to the repository root")
    args = parser.parse_args()

    if args.capture_root:
        segments.CAPTURE_ROOT = ROOT / Path(args.capture_root)
    capture_root = segments.CAPTURE_ROOT
    if not capture_root.is_dir():
        raise SystemExit(f"capture directory not found: {capture_root}")

    columns = source_columns()
    static = load_fitted(args.static_frame, columns).reshape(SATURN_HEIGHT,
                                                             SATURN_WIDTH)
    frames = {
        frame: load_fitted(frame, columns).reshape(SATURN_HEIGHT,
                                                   SATURN_WIDTH)
        for frame in range(args.first, args.last + 1, args.cadence)
    }

    observations = validate_shutter(static, frames)
    model = fit_linear_shutter(observations, static, args.cadence)

    report = {
        "source": {
            "romset": "avspu",
            "mame_version": "0.289",
            "cadence": args.cadence,
            "capture_root": str(capture_root.relative_to(ROOT)).replace(
                "\\", "/"),
            "static_frame": args.static_frame,
            "wipe_first_frame": args.first,
            "wipe_last_frame": args.last,
        },
        "verified": {
            "row_shutter_not_squeeze": True,
            "band_rows_identical_to_static_frame": True,
            "outside_band_fully_black": True,
            "stored_frame_bytes_required": 0,
        },
        "shutter_model": model,
        "observations": observations,
    }

    print(f"Character-confirm wipe validated over {len(observations)} "
          f"cadence-{args.cadence} samples from {capture_root.name}.")
    print(f"  every visible row is byte-identical to static frame "
          f"{args.static_frame}; everything else is black")
    print(f"  shutter closes {model['rows_per_source_frame_per_edge']} rows "
          f"per source frame per edge about row {model['centre_row']}")
    print(f"  content rows {model['content_top_row']}.."
          f"{model['content_bottom_row']}, fitted start source frame "
          f"{model['fitted_start_source_frame']} "
          f"(+/-{model['start_frame_ambiguity_source_frames']} at cadence "
          f"{args.cadence})")
    print(f"  top residuals {model['top_residuals']}")
    print("  stored animation payload: 0 bytes")

    if args.report:
        output = ROOT / Path(args.output)
        output.write_text(json.dumps(report, indent=2) + "\n",
                          encoding="ascii")
        print(f"Wrote {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
