"""Per-layer CPS scroll rates: does the stage background need parallax?

The Saturn runtime flattens the CPS tilemap layers into ONE VDP2 bitmap and
scrolls it with a single linear rescale (`cap_background_fit_scroll_x` in
capability_model.c). That is only faithful if every visible layer moves at the
SAME rate as the camera. This measures whether it does, straight from the
CPS-A scroll registers already captured for each route - no emulator, no ROM
bytes, register words and counts only.

METHOD. Each captured frame carries the full cps_a share. Layer scroll X lives
at word 6 (scroll1), 8 (scroll2) and 10 (scroll3); row-scroll enable is bit 0
of word 17 (see tools/extract_avspu_stage1.py's render_background, which is the
authoritative reading of these registers in this project). For consecutive
captured frames the per-layer delta is compared. Frames whose delta exceeds
DISCONTINUITY_LIMIT in magnitude are wrap-around or room changes, not camera
motion, and are excluded and counted separately rather than silently dropped.

RESULT (2026-08-19, the reason this tool exists): the street and the interior
disagree, and generalising from the interior is the trap.

  street  (enemy_actions)   48 moving frames, sum d2=70 sum d3=53 -> 0.757
  interior(stalker_actions) 230 moving frames, sum d2=160 sum d3=160 -> 1.000

The street ramp is unambiguous - one deceleration runs 11/9, 10/9, 9/8, 8/7,
7/6, 6/5, 5/4 before converging - so scroll3 genuinely trails scroll2. A single
flattened surface at a single rate cannot express two rates, which makes the
current background a MEASURED fidelity gap on the Round 1 street. It is
recorded here, NOT fixed: the fix is a CPS2-to-Saturn architectural fork
(per-layer VDP2 planes versus one surface) and belongs to a separate, gated
body.

STILL UNRESOLVED, and independent of the above: row-scroll is enabled on every
street and interior frame. It applies to scroll2 only and indexes a per-row
table in gfxram, and NO gameplay capture dumps gfxram - so the table has never
been observed. A non-constant table is a second way the flattened bitmap could
be wrong. This tool reports the enable bit and names that probe; it cannot
answer it.

Output: data/avsp_stage_scroll.json (tracked). Skips cleanly when the private
captures are absent, the same contract as the other analyzers here.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "data" / "avsp_stage_scroll.json"

ROUTES = ("enemy_actions", "stalker_actions", "boss_actions", "boss_ko")

# cps_a word indices, per tools/extract_avspu_stage1.py render_background().
SCROLL_X_WORDS = {"scroll1": 6, "scroll2": 8, "scroll3": 10}
SCROLL_Y_WORDS = {"scroll1": 7, "scroll2": 9, "scroll3": 11}
ROW_SCROLL_OFFSET_WORD = 16
ROW_SCROLL_CONTROL_WORD = 17

# A single-frame delta larger than this is a wrap or a room change, not camera
# motion. The observed street ramp peaks at 11 px/frame, so 100 is far above
# real motion and far below the ~1000 seen at a discontinuity.
DISCONTINUITY_LIMIT = 100


def read_words(path: Path) -> list[int]:
    words: list[int] = []
    with path.open() as handle:
        next(handle)
        for line in handle:
            parts = line.split()
            if len(parts) >= 2:
                words.append(int(parts[1], 16))
    return words


def s16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def scan_route(route: str) -> dict | None:
    root = ROOT / ".deps" / "mame" / route
    frames = sorted(root.glob("cps_a_regs_*.tsv")) if root.is_dir() else []
    if not frames:
        return None

    previous = None
    moving = 0
    identical = 0
    discontinuities = 0
    sums = {name: 0 for name in SCROLL_X_WORDS}
    bias_values: set[int] = set()
    row_scroll_enable: set[int] = set()
    scroll1_values: set[int] = set()
    ramp: list[dict] = []

    for path in frames:
        words = read_words(path)
        if len(words) <= ROW_SCROLL_CONTROL_WORD:
            continue
        current = {name: words[index]
                   for name, index in SCROLL_X_WORDS.items()}
        row_scroll_enable.add(words[ROW_SCROLL_CONTROL_WORD] & 1)
        scroll1_values.add(current["scroll1"])
        bias_values.add((current["scroll2"] - current["scroll3"]) & 0xFFFF)

        if previous is not None:
            deltas = {name: s16(current[name] - previous[name])
                      for name in SCROLL_X_WORDS}
            if any(deltas.values()):
                if any(abs(d) > DISCONTINUITY_LIMIT for d in deltas.values()):
                    discontinuities += 1
                else:
                    moving += 1
                    for name in SCROLL_X_WORDS:
                        sums[name] += deltas[name]
                    if deltas["scroll2"] == deltas["scroll3"]:
                        identical += 1
                    if len(ramp) < 24:
                        ramp.append({
                            "frame": path.stem.split("_")[-1],
                            "d_scroll2": deltas["scroll2"],
                            "d_scroll3": deltas["scroll3"],
                        })
        previous = current

    rate = (sums["scroll3"] / sums["scroll2"]) if sums["scroll2"] else None
    single_rate = moving > 0 and identical == moving

    return {
        "route": route,
        "frames_scanned": len(frames),
        "moving_frames": moving,
        "excluded_discontinuities": discontinuities,
        "delta_sums": sums,
        "scroll3_over_scroll2_rate": (round(rate, 6)
                                      if rate is not None else None),
        "identical_delta_frames": identical,
        "single_rate": single_rate,
        "scroll1_distinct_values": len(scroll1_values),
        "scroll2_minus_scroll3_bias_values": sorted(
            "0x%04X" % b for b in bias_values)[:8],
        "row_scroll_enable_values": sorted(row_scroll_enable),
        "first_moving_frames": ramp,
    }


def main() -> int:
    routes = [r for r in (scan_route(name) for name in ROUTES) if r]
    if not routes:
        print("stage scroll: SKIPPED - no cps_a register captures present")
        return 0

    parallax = [r for r in routes if r["moving_frames"] > 0
                and not r["single_rate"]]
    single = [r for r in routes if r["moving_frames"] > 0 and r["single_rate"]]

    manifest = {
        "schema": 1,
        "classification": "CPS layer scroll rates - register words and counts "
                          "only; no ROM bytes, no tile or colour data",
        "question": "does any captured route scroll its tilemap layers at "
                    "DIFFERENT rates, i.e. does the stage need parallax that "
                    "one flattened VDP2 bitmap cannot express?",
        "method": "per-frame CPS-A scroll-X deltas (words 6/8/10) between "
                  "consecutive captured frames; single-frame deltas above "
                  "%d are wrap/room discontinuities and are excluded and "
                  "counted, not dropped" % DISCONTINUITY_LIMIT,
        "finding": (
            "layer scroll rates DIFFER by route: %s show differing per-layer "
            "deltas (parallax), %s move every layer identically. The runtime "
            "flattens all layers into one VDP2 bitmap scrolled by a single "
            "linear rescale (cap_background_fit_scroll_x), which cannot "
            "express more than one rate - a MEASURED fidelity gap wherever "
            "parallax is present."
            % ([r["route"] for r in parallax] or "no route",
               [r["route"] for r in single] or "no route")),
        "methodological_note": "the interior route does NOT generalise to the "
                               "street. An earlier pass correlated work-RAM "
                               "values over the interior pan, found every "
                               "tracker at slope 1.0 and recorded a null "
                               "result; the street was camera-locked in the "
                               "frames it sampled. Measure the street route "
                               "before claiming anything about the street.",
        "unresolved_row_scroll": "row-scroll is enabled on every scanned "
                                 "frame (control word %d bit 0). It applies "
                                 "to scroll2 only and indexes a per-row table "
                                 "in gfxram; no gameplay capture dumps "
                                 "gfxram, so the table has never been "
                                 "observed. A non-constant table is a second, "
                                 "independent way one flattened surface could "
                                 "be wrong. Probe: dump the 1024-word "
                                 "row-scroll window during a street pan."
                                 % ROW_SCROLL_CONTROL_WORD,
        "not_fixed_here": "the remedy is a CPS2-to-Saturn architectural fork "
                          "(per-layer VDP2 planes versus one surface) and "
                          "touches capability_model.c; it belongs to a "
                          "separate gated body, not to this measurement.",
        "discontinuity_limit": DISCONTINUITY_LIMIT,
        "routes": routes,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")

    for entry in routes:
        rate = entry["scroll3_over_scroll2_rate"]
        print("%-16s moving=%4d excluded=%3d  d2=%5d d3=%5d  rate=%s  "
              "identical=%d/%d  %s"
              % (entry["route"], entry["moving_frames"],
                 entry["excluded_discontinuities"],
                 entry["delta_sums"]["scroll2"], entry["delta_sums"]["scroll3"],
                 ("%.3f" % rate) if rate is not None else "n/a",
                 entry["identical_delta_frames"], entry["moving_frames"],
                 "SINGLE-RATE" if entry["single_rate"]
                 else ("PARALLAX" if entry["moving_frames"] else "no motion")))
    print("wrote", OUT_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
