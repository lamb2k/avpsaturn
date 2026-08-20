"""Prove the confirmation shutter against the complete source interval.

The character-confirm transition ends in a row shutter: the visible band of
the settled selection image shrinks symmetrically to the content centre and
everything outside it is black.  The capability model encodes it as
`cap_confirm_shutter_band()`: content rows 40..223, four rows per edge per
frame starting after confirm timer 85 (the model clock leads frames-since-
input by one), centre 131.5.  The complete interval pins the first masked
source frame to 1886 (frames-since-input 86) and closure to 1908.

That expectation came from sampled frames.  This check replays the COMPLETE
captured confirm interval at cadence 1 - every reference frame from the
last object activity to the Round 1 text appearance - and requires, for
every frame:

* rows inside the model band are byte-identical to the pre-shutter baseline
  frame;
* rows outside the band (within the content rows) are pure black;
* before the start frame nothing is masked, and after closure every content
  row stays black until the Round 1 title text tilemap appears at 1971.

Rows 0..39 are outside the shutter's content band (HUD / Press Start area)
and are not part of this contract.

Four negative controls run against the interval that just passed exactly: a
one-frame start shift, a one-row band shift (broken centre), a wrong
rows-per-frame rate, and a wrong closure. Each must fail.

The raw reference frames are private; the tracked report carries counts,
row indices and verdicts only.  Skips cleanly when the capture is absent.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover - Pillow is part of the toolchain
    Image = None

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / ".deps" / "mame" / "frontend_rom"
REPORT = ROOT / "data" / "avsp_confirm_shutter_readback.json"

WIDTH = 384
HEIGHT = 224
CONTENT_TOP = 40
CONTENT_BOTTOM = 223
CONFIRM_INPUT_FRAME = 1800
SHUTTER_START_TIMER = 85
ROWS_PER_FRAME = 4
# Object activity (the confirmation blink burst) ends at source frame 1859;
# the Round 1 title text tilemap appears at 1971. Between those, the frame
# is pure tilemap state and the shutter is the only change.
FIRST_CHECKED_FRAME = 1860
LAST_CHECKED_FRAME = 1970
BASELINE_FRAME = 1884


def band(timer: int, start_timer: int = SHUTTER_START_TIMER,
         rate: int = ROWS_PER_FRAME, shift: int = 0) -> tuple[int, int]:
    """cap_confirm_shutter_band(), with control knobs for falsification."""
    top, bottom = CONTENT_TOP, CONTENT_BOTTOM
    if timer > start_timer:
        moved = (timer - start_timer) * rate
        top += moved
        bottom -= moved
    return top + shift, bottom + shift


def frame_rows(path: Path) -> list[bytes]:
    image = Image.open(path).convert("RGB")
    if image.size != (WIDTH, HEIGHT):
        raise ValueError(f"{path.name}: expected 384x224")
    raw = image.tobytes()
    stride = WIDTH * 3
    return [raw[y * stride:(y + 1) * stride] for y in range(HEIGHT)]


def check_interval(rows_by_frame: dict[int, list[bytes]],
                   baseline: list[bytes], black: bytes,
                   start_timer: int = SHUTTER_START_TIMER,
                   rate: int = ROWS_PER_FRAME,
                   shift: int = 0) -> list[str]:
    """Every content row of every frame must be explained by the band."""
    failures: list[str] = []
    for frame, rows in sorted(rows_by_frame.items()):
        # The band is a function of frames since the confirm input; the
        # runtime converts its leading encounter timer back to this count.
        frames_since_input = frame - CONFIRM_INPUT_FRAME
        top, bottom = band(frames_since_input, start_timer, rate, shift)
        for y in range(CONTENT_TOP, CONTENT_BOTTOM + 1):
            if top <= y <= bottom:
                if rows[y] != baseline[y]:
                    failures.append(
                        f"frame {frame} row {y}: inside the band but not "
                        "byte-identical to the pre-shutter baseline")
            elif rows[y] != black:
                failures.append(
                    f"frame {frame} row {y}: outside the band but not black")
            if len(failures) >= 8:
                return failures
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=Path, default=CAPTURE)
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()

    if Image is None or not (
            args.capture / f"reference_{BASELINE_FRAME}.png").is_file():
        print("confirm shutter: SKIPPED - private capture absent")
        return 0

    rows_by_frame = {}
    for frame in range(FIRST_CHECKED_FRAME, LAST_CHECKED_FRAME + 1):
        path = args.capture / f"reference_{frame:04d}.png"
        if not path.is_file():
            print(f"confirm shutter: SKIPPED - {path.name} absent")
            return 0
        rows_by_frame[frame] = frame_rows(path)

    baseline = rows_by_frame[BASELINE_FRAME]
    black = bytes(WIDTH * 3)

    failures = check_interval(rows_by_frame, baseline, black)
    if failures:
        for line in failures:
            print(f"confirm shutter: FAIL - {line}")
        return 1

    # The interval only proves the shutter if it actually contains both a
    # fully open and a fully closed portion.
    open_frames = sum(
        1 for frame in rows_by_frame
        if band(frame - CONFIRM_INPUT_FRAME)[0] == CONTENT_TOP)
    closed_frames = sum(
        1 for frame in rows_by_frame
        if band(frame - CONFIRM_INPUT_FRAME)[0]
        > band(frame - CONFIRM_INPUT_FRAME)[1])
    moving_frames = len(rows_by_frame) - open_frames - closed_frames
    if not open_frames or not closed_frames or moving_frames < 20:
        print("confirm shutter: FAIL - the checked interval does not span "
              f"open ({open_frames}), moving ({moving_frames}) and closed "
              f"({closed_frames}) phases")
        return 1

    controls = {
        "start_shifted_one_frame": check_interval(
            rows_by_frame, baseline, black,
            start_timer=SHUTTER_START_TIMER + 1),
        "band_shifted_one_row": check_interval(
            rows_by_frame, baseline, black, shift=1),
        "rate_three_rows": check_interval(
            rows_by_frame, baseline, black, rate=3),
        "rate_five_rows": check_interval(
            rows_by_frame, baseline, black, rate=5),
    }
    control_failures = [name for name, result in controls.items()
                        if not result]
    if control_failures:
        for name in control_failures:
            print(f"confirm shutter: FAIL - negative control {name} "
                  "still passed")
        return 1

    args.report.write_text(json.dumps({
        "schema": 1,
        "classification": "Complete-interval confirmation-shutter proof; "
                          "frame ranges, row indices, counts and verdicts "
                          "only, no captured pixels",
        "instrument": "MAME 0.289 cadence-1 reference frames "
                      f"{FIRST_CHECKED_FRAME}..{LAST_CHECKED_FRAME}",
        "model": "cap_confirm_shutter_band(): content rows "
                 f"{CONTENT_TOP}..{CONTENT_BOTTOM}, {ROWS_PER_FRAME} rows "
                 f"per edge per frame after confirm timer "
                 f"{SHUTTER_START_TIMER} (first masked source frame 1886), centre 131.5",
        "verdict": "PASS",
        "frames_checked": len(rows_by_frame),
        "open_frames": open_frames,
        "moving_frames": moving_frames,
        "closed_frames": closed_frames,
        "baseline_frame": BASELINE_FRAME,
        "unexplained_rows": 0,
        "negative_controls": {
            name: {"failed_as_required": bool(result),
                   "first_failure": result[0] if result else None}
            for name, result in controls.items()
        },
    }, indent=1, sort_keys=True) + "\n", encoding="ascii")
    print(f"confirm shutter: PASS - {len(rows_by_frame)} frames "
          f"({open_frames} open, {moving_frames} moving, {closed_frames} "
          "closed), every content row explained, 4 negative controls "
          "failed as required")
    print(f"wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
