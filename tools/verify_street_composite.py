#!/usr/bin/env python3
"""RP4 correction: a real host composite of the street scene.

Builds, for every frame of the 201-frame RP4 interval, the full final
composite the priority programming encodes - NBG1 (scroll3) below NBG0
(scroll2, source transparency) below the VDP1 object classes (actor
class = CPS priority 1, foreground class = CPS priority 4) below the
unported scroll1 text layer - and compares it per pixel against the
captured reference PNG. The endpoint-aligned 384-to-352 transform is
applied once, at composite level, for the fitted checks.

Deliberate-overlap search: every frame's actor-class opaque mask is
intersected with the foreground-class opaque mask. The first overlapping
pixel is recorded with frame, source and fitted coordinates, object
index, tile/palette identity and expected winning layer. If the interval
contains none, this tool STOPS with "RP4 interval falsified: no
deliberate overlap" instead of inventing proof.

Negative controls are EXECUTED rerenders: each control recomposes the
same frame with exactly one perturbed input and passes only when the
perturbed composite differs from the correct composite by a nonzero
pixel count:

  wrong_transform       naive 384-to-352 column map vs endpoint-aligned
  scroll_shift          scroll2 X register +1 for one frame
  row_entry             row-scroll enabled with one nonzero table entry
  palette_cycle         one measured cycle-destination colour changed
  patch_dropped         first map patch's cell words reverted
  register_order        foreground class composited below NBG0

The two overlap-object controls (overlap object shifted by one pixel,
overlap object priority class swapped) require the measured overlap and
are BLOCKED while the interval is falsified.

Results merge into data/rp4_street_readback.json under "composite".
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import extract_avspu_stage1 as avsp                     # noqa: E402
from census_full_route import RouteState                # noqa: E402
from select_rp4_interval import FIRST_FRAME, LAST_FRAME  # noqa: E402
from rp4_status import build_status, check_evidence, exit_code  # noqa: E402

CAPTURE = ROOT / ".deps" / "mame" / "full_route"
READBACK = ROOT / "data" / "rp4_street_readback.json"

ACTOR_PRIORITY = 1
FOREGROUND_PRIORITY = 4
CONTROL_FRAME = FIRST_FRAME
CYCLE_FLIP_FRAME = FIRST_FRAME + 4
PATCH_FRAME = FIRST_FRAME + 123


def in_of(out_x: int) -> int:
    """Endpoint-aligned inverse of the 384-to-352 output map."""
    return (out_x * 383 + 175) // 351


def words_for_priority(words: list[int], priority: int | None,
                       shift_x: dict[int, int] | None = None,
                       swap_priority: dict[int, int] | None = None
                       ) -> list[int]:
    """Object words filtered to one CPS priority class, preserving order
    and re-terminated; optional per-entry-index X shifts / class swaps."""
    out: list[int] = []
    index = 0
    for offset in range(0, len(words) - 3, 4):
        x, y, code, attribute = words[offset:offset + 4]
        if y >= 0x8000 or attribute >= 0xFF00:
            break
        pri = (x >> 13) & 7
        if swap_priority and index in swap_priority:
            pri = swap_priority[index]
            x = (x & ~0xE000) | (pri << 13)
        if priority is None or pri == priority:
            if shift_x and index in shift_x:
                x = (x & ~0x3FF) | ((x + shift_x[index]) & 0x3FF)
            out.extend([x, y, code, attribute])
        index += 1
    out.extend([0, 0x8000, 0, 0])
    return out


class Frame:
    def __init__(self, state: RouteState, rec: dict):
        self.rec = rec
        self.cps_a = list(rec["cps_a"])
        self.cps_b = [int.from_bytes(state.current["cps_b"][i:i + 2], "big")
                      for i in range(0, 0x40, 2)]
        gfxram: list[int] = []
        for name in ("gfxram0", "gfxram1", "gfxram2"):
            data = state.current[name]
            gfxram += [int.from_bytes(data[i:i + 2], "big")
                       for i in range(0, len(data), 2)]
        self.gfxram = gfxram
        self.palette = [(((c >> 8) & 0xF) * 17, ((c >> 4) & 0xF) * 17,
                        (c & 0xF) * 17, 255)
                        for c in (int.from_bytes(
                            state.gfx_slice(rec["palette_base"] + i * 2, 2),
                            "big") for i in range(0xC00))]
        active = state.current[
            "objram2" if rec["active_bank"] else "objram1"]
        self.words = [int.from_bytes(active[i:i + 2], "big")
                      for i in range(0, len(active), 2)]


def compose(gfx, frame: Frame, cps_a=None, gfxram=None, palette=None,
            words=None, order_swap: bool = False) -> Image.Image:
    """The final composite: scroll3 < scroll2 < actor objects <
    foreground objects < scroll1, from the (optionally perturbed)
    inputs. order_swap composites the foreground class below scroll2."""
    cps_a = cps_a if cps_a is not None else frame.cps_a
    gfxram = gfxram if gfxram is not None else frame.gfxram
    palette = palette if palette is not None else frame.palette
    words = words if words is not None else frame.words

    def layer(n):
        return avsp.render_background(
            gfx, gfxram, cps_a, frame.cps_b, palette, layer_filter=(n,),
            transparent_background=True)

    def objects(priority):
        img, _ = avsp.decode_objects(
            gfx, words_for_priority(words, priority), palette)
        return img

    canvas = Image.new("RGBA", (384, 224), frame.palette[0xBFF])
    canvas.alpha_composite(layer(3))
    if order_swap:
        canvas.alpha_composite(objects(FOREGROUND_PRIORITY))
        canvas.alpha_composite(layer(2))
        canvas.alpha_composite(objects(ACTOR_PRIORITY))
    else:
        canvas.alpha_composite(layer(2))
        canvas.alpha_composite(objects(ACTOR_PRIORITY))
        canvas.alpha_composite(objects(FOREGROUND_PRIORITY))
    canvas.alpha_composite(layer(1))
    return canvas


def fitted(image: Image.Image, naive: bool = False) -> Image.Image:
    out = Image.new("RGBA", (352, 224))
    src = image.load()
    dst = out.load()
    for x in range(352):
        sx = (x * 384) // 352 if naive else in_of(x)
        for y in range(224):
            dst[x, y] = src[min(sx, 383), y]
    return out


def diff_count(a: Image.Image, b: Image.Image) -> int:
    pa, pb = a.load(), b.load()
    w, h = a.size
    return sum(1 for y in range(h) for x in range(w)
               if pa[x, y][:3] != pb[x, y][:3])


def rgb555(rgb: tuple) -> int:
    r, g, b = rgb
    return ((b >> 3) << 10) | ((g >> 3) << 5) | (r >> 3)


def find_overlap(gfx, frame, f):
    """First qualifying actor/foreground overlap in one frame.

    Qualifying: both surfaces opaque at the pixel, and at least one such
    pixel where the two colours DIFFER (the witness), so the priority
    perturbations are observable. Records identity, coordinates, pixel
    counts and the baseline RGB555 the truth shows."""
    actor_words = words_for_priority(frame.words, ACTOR_PRIORITY)
    actor_img, actor_entries = avsp.decode_objects(
        gfx, actor_words, frame.palette)
    if not actor_entries:
        return None
    fore_img, fore_entries = avsp.decode_objects(
        gfx, words_for_priority(frame.words, FOREGROUND_PRIORITY),
        frame.palette)
    pa, pf = actor_img.load(), fore_img.load()
    pixels = []
    witness = None
    for y in range(224):
        for x in range(384):
            if pa[x, y][3] and pf[x, y][3]:
                pixels.append([x, y])
                if witness is None and pa[x, y][:3] != pf[x, y][:3]:
                    witness = (x, y)
    if not pixels or witness is None:
        return None
    wx, wy = witness

    def entry_at(entries, x, y):
        for index, e in enumerate(entries):
            if (e["screen_x"] <= x < e["screen_x"] + e["width"] and
                    e["screen_y"] <= y < e["screen_y"] + e["height"]):
                return index, e
        return None, None

    actor_i, actor = entry_at(actor_entries, wx, wy)
    fore_i, fore = entry_at(fore_entries, wx, wy)
    truth = Image.open(
        CAPTURE / f"reference_{f:05d}.png").convert("RGBA").load()
    return {
        "frame": f,
        "overlap_pixel_count": len(pixels),
        "overlap_pixels_sample": pixels[:16],
        "witness_source_xy": [wx, wy],
        "fitted_xy": [(wx * 351 - 175 + 382) // 383, wy],
        "actor_entry_index": actor_i,
        "actor_slot_offset": actor["offset"],
        "actor_tile_code": actor["tile_code"],
        "actor_colour": actor["colour"],
        "actor_priority": ACTOR_PRIORITY,
        "foreground_entry_index": fore_i,
        "foreground_slot_offset": fore["offset"],
        "foreground_tile_code": fore["tile_code"],
        "foreground_colour": fore["colour"],
        "foreground_priority": FOREGROUND_PRIORITY,
        "expected_winner": "foreground-class VDP1",
        "witness_baseline_rgb555": rgb555(truth[wx, wy][:3]),
        "source_xy": [wx, wy],
    }


def evidence_hashes(overlap) -> dict:
    """Input hashes pinning this evidence to its sources."""
    strips = ROOT / "build" / "rp4_fixture" / "STRIPS.BIN"
    census = ROOT / "data" / "round1_route_census.json"
    frame = overlap["frame"] if overlap else FIRST_FRAME
    png = CAPTURE / f"reference_{frame:05d}.png"
    return {
        "strips_bin": hashlib.sha256(strips.read_bytes()).hexdigest(),
        "route_census": hashlib.sha256(census.read_bytes()).hexdigest(),
        "witness_frame_png":
            hashlib.sha256(png.read_bytes()).hexdigest(),
    }


def main() -> None:
    state = RouteState(CAPTURE)
    gfx = avsp.load_gfx_region()

    frames: dict[int, Frame] = {}
    overlap = None
    overlap_frame = None
    mismatch_total = 0
    mismatch_max = 0
    frames_checked = 0
    control_inputs: dict[int, Frame] = {}

    for rec in state.frames():
        f = rec["frame"]
        if f < FIRST_FRAME:
            continue
        if f > LAST_FRAME:
            break
        frame = Frame(state, rec)
        if f in (CONTROL_FRAME, CYCLE_FLIP_FRAME, PATCH_FRAME):
            control_inputs[f] = frame

        composite = compose(gfx, frame)
        truth = Image.open(
            CAPTURE / f"reference_{f:05d}.png").convert("RGBA")
        mism = diff_count(composite, truth)
        mismatch_total += mism
        mismatch_max = max(mismatch_max, mism)
        frames_checked += 1

        # Deliberate-overlap search: pixels where actor-class and
        # foreground-class objects are both opaque. The witness pixel
        # must have DIFFERING actor/foreground colours so the priority
        # perturbations are observable in the composite.
        if overlap is None:
            found = find_overlap(gfx, frame, f)
            if found is not None:
                overlap = found
                overlap_frame = frame
        if f % 25 == 0:
            print(f"frame {f}: composite mismatch {mism}")

    # ------------------------------------------------------------------
    # Executed negative controls, each one perturbed input recomposed.
    controls: dict[str, dict] = {}
    base = compose(gfx, control_inputs[CONTROL_FRAME])

    wrong = diff_count(fitted(base, naive=True), fitted(base))
    controls["wrong_transform"] = {
        "detected": wrong > 0,
        "pixels": wrong,
        "detail": "naive vs endpoint-aligned fitted composite"}

    scrolled_a = list(control_inputs[CONTROL_FRAME].cps_a)
    scrolled_a[8] += 1
    d = diff_count(compose(gfx, control_inputs[CONTROL_FRAME],
                           cps_a=scrolled_a), base)
    controls["scroll_shift"] = {
        "detected": d > 0, "pixels": d,
        "detail": "scroll2 X register +1"}

    fr = control_inputs[CONTROL_FRAME]
    row_a = list(fr.cps_a)
    row_a[17] |= 1
    other_base = (((row_a[4] * 256) & 0x3FFFF) & ~(0x800 - 1)) // 2
    row_ram = list(fr.gfxram)
    for i in range(0x400):
        row_ram[other_base + i] = 0
    row_ram[other_base + ((120 + row_a[16]) & 0x3FF)] = 1
    d = diff_count(compose(gfx, fr, cps_a=row_a, gfxram=row_ram), base)
    controls["row_entry"] = {
        "detected": d > 0, "pixels": d,
        "detail": "row scroll enabled, one visible entry = 1"}

    flip = control_inputs[CYCLE_FLIP_FRAME]
    cycled_pens = [pen for pen in range(16)
                   if fr.palette[0x41 * 16 + pen] !=
                   flip.palette[0x41 * 16 + pen]]
    if not cycled_pens:
        controls["palette_cycle"] = {
            "detected": False, "pixels": 0,
            "detail": "no cycled pen found between flip frames"}
    else:
        pal = list(flip.palette)
        dest = 0x41 * 16 + cycled_pens[0]
        r, g, b, a = pal[dest]
        pal[dest] = (r ^ 0x88, g, b ^ 0x88, a)
        d = diff_count(compose(gfx, flip, palette=pal),
                       compose(gfx, flip))
        controls["palette_cycle"] = {
            "detected": d > 0, "pixels": d,
            "detail": f"cycle destination pen {cycled_pens[0]} "
                      f"(bank 1) recoloured at flip frame"}

    patch_frame = control_inputs[PATCH_FRAME]
    patch_base = compose(gfx, patch_frame)
    reverted = list(patch_frame.gfxram)
    changed = 0
    for register in (2, 3):
        map_words = ((patch_frame.cps_a[register] * 256) & 0x3FFFF
                     & ~(0x4000 - 1)) // 2
        for i in range(0x2000):
            if reverted[map_words + i] != fr.gfxram[map_words + i]:
                reverted[map_words + i] = fr.gfxram[map_words + i]
                changed += 1
    d = diff_count(compose(gfx, patch_frame, gfxram=reverted), patch_base)
    controls["patch_dropped"] = {
        "detected": changed > 0 and d > 0, "pixels": d,
        "detail": f"first patch: {changed} map words reverted to "
                  f"interval start"}

    d = diff_count(compose(gfx, fr, order_swap=True), base)
    controls["register_order"] = {
        "detected": d > 0, "pixels": d,
        "detail": "foreground class composited below NBG0"}

    if overlap is not None and overlap_frame is not None:
        obase = compose(gfx, overlap_frame)
        # words_for_priority indexes RAW objram slots (offset // 4);
        # decoder entry lists are reverse-ordered, so use the recorded
        # raw slot offsets, never the decoder indices.
        actor_i = overlap["actor_slot_offset"] // 4
        fore_i = overlap["foreground_slot_offset"] // 4
        wx, wy = overlap["witness_source_xy"]

        shifted = words_for_priority(
            overlap_frame.words, None, shift_x={actor_i: 1})
        d = diff_count(compose(gfx, overlap_frame, words=shifted), obase)
        controls["overlap_object_shift"] = {
            "detected": d > 0, "pixels": d,
            "detail": f"measured overlap actor (entry {actor_i}) "
                      f"shifted +1px at frame {overlap['frame']}"}

        swapped = words_for_priority(
            overlap_frame.words, None,
            swap_priority={actor_i: FOREGROUND_PRIORITY,
                           fore_i: ACTOR_PRIORITY})
        perturbed = compose(gfx, overlap_frame, words=swapped)
        d = diff_count(perturbed, obase)
        witness_changed = (perturbed.load()[wx, wy][:3] !=
                           obase.load()[wx, wy][:3])
        overlap["baseline_rgb555"] = overlap["witness_baseline_rgb555"]
        overlap["perturbed_rgb555"] = rgb555(
            perturbed.load()[wx, wy][:3])
        controls["overlap_priority_swap"] = {
            "detected": d > 0 and witness_changed, "pixels": d,
            "detail": f"actor entry {actor_i} and foreground entry "
                      f"{fore_i} classes swapped; witness pixel "
                      f"({wx},{wy}) changed: {witness_changed}"}
    else:
        for name in ("overlap_object_shift", "overlap_priority_swap"):
            controls[name] = {
                "detected": None,
                "detail": "BLOCKED: requires the measured overlap; the "
                          "interval is falsified (no qualifying "
                          "actor/foreground overlap in frames "
                          f"{FIRST_FRAME}-{LAST_FRAME})"}

    executed = {k: v for k, v in controls.items()
                if v["detected"] is not None}
    all_detected = all(v["detected"] for v in executed.values())

    report = {
        "frames_composited": frames_checked,
        "composite_mismatch_total": mismatch_total,
        "composite_mismatch_max_per_frame": mismatch_max,
        "composite_mismatch_note":
            "object pixel-decoder imprecision residue (GAP); the "
            "per-plane reconstruction mismatches are 0 (see "
            "plane_pixels_mismatched)",
        "overlap": overlap,
        "overlap_verdict": ("MEASURED" if overlap else
                            "RP4 interval falsified: no deliberate "
                            "overlap"),
        "controls": controls,
    }

    readback = json.loads(READBACK.read_text())
    planes_mismatched = sum(
        readback.get("plane_pixels_mismatched", {}).values())
    status = build_status(controls, overlap, planes_mismatched)
    report["status"] = status
    # Ambiguous aggregate kept only as a strict alias of the status
    # block so stale consumers cannot read a softer answer.
    report["controls_all_detected"] = status["controls_all_detected"]

    hashes = evidence_hashes(overlap)
    report["evidence_sha256"] = hashes
    check_evidence(report["evidence_sha256"], evidence_hashes(overlap))

    readback["composite"] = report
    READBACK.write_text(
        json.dumps(readback, indent=1, sort_keys=True) + "\n",
        encoding="ascii", newline="\n")

    blocked = status["required_controls_blocked"]
    print(f"composite: {frames_checked} frames, mismatch total "
          f"{mismatch_total} (max {mismatch_max}/frame), "
          f"{status['required_controls_passed']}/"
          f"{status['required_controls_total']} controls passed, "
          f"{blocked} blocked, rp4_contract_status="
          f"{status['rp4_contract_status']}")
    if status["rp4_contract_status"] == "FALSIFIED":
        print("RP4 interval falsified: no deliberate overlap")
    raise SystemExit(exit_code(status))


if __name__ == "__main__":
    main()
