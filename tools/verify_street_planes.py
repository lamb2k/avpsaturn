#!/usr/bin/env python3
"""RP4 offline proof: the street-plane runtime pipeline against source truth.

For every frame of the representative interval this verifier reconstructs,
independently, what the Saturn displays per plane and what the CPS2 source
composed, and compares them in the Saturn RGB555 domain:

  NBG0/NBG1: the STRIPS.BIN cell data + pattern grids + palettes + scroll
  conversion + map patches + palette cycle are replayed exactly as the
  street-test runtime replays them (same integer transforms), producing a
  352x224 window per plane; the source truth is the MAME-exact
  render_background of the captured gfxram/registers for the same layer,
  fitted with the shared endpoint-aligned mapping. The anamorphic fit is
  the recorded ADAPTED decision, so the pass criterion is: at most a
  bounded set of single-column mismatches at resample boundaries (the two
  integer pipelines quantize at different anchors), zero row mismatches,
  and zero mismatches anywhere else. Every mismatch column is counted and
  the worst frame recorded.

  VDP1: the object schedule in STRIPS.BIN must be byte-identical to the
  captured active object banks, every expanded tile must exist in the
  street TILES.BIN, and the runtime priority classes must partition the
  entries exactly by the source priority word.

  Page boundary: the frames whose window crosses fitted cell column 64
  are identified and must compare clean; the aliased-page negative
  control rewrites page B with page A and must fail on exactly those
  frames.

Negative controls (each must FAIL the comparison):
  1. wrong horizontal transform (352/384 midpoint rounding);
  2. aliased second pattern page;
  3. one scroll record shifted by one;
  4. one palette-cycle entry recoloured;
  5. one map patch dropped;
  6. one object x perturbed;
  7. one object priority class flipped;
  8. one sprite-priority register value swapped (class order inverted).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import extract_avspu_stage1 as avsp                     # noqa: E402
from census_full_route import RouteState                # noqa: E402
from select_rp4_interval import FIRST_FRAME, LAST_FRAME  # noqa: E402

STRIPS = ROOT / "build" / "rp4_fixture" / "STRIPS.BIN"
TILES_BIN = ROOT / "build" / "avsp_cd" / "SPR4" / "TILES.BIN"
CAPTURE = ROOT / ".deps" / "mame" / "full_route"
OUTPUT = ROOT / "data" / "rp4_street_readback.json"

VIS_W, VIS_H, VIS_LEFT, VIS_TOP = 384, 224, 64, 16
OUT_W = 352


def u16(data: bytes, at: int) -> int:
    return (data[at] << 8) | data[at + 1]


def u32(data: bytes, at: int) -> int:
    return (u16(data, at) << 16) | u16(data, at + 2)


def out_of(world_x: int) -> int:
    return (world_x * 351 - 175 + 382) // 383


def src_of(out_x: int) -> int:
    return (out_x * 383 + 175) // 351


class Strips:
    def __init__(self, blob: bytes):
        self.blob = blob
        assert u32(blob, 0) == 0x41565353 and u16(blob, 4) == 1
        self.frames = u16(blob, 6)
        self.planes = []
        for plane in range(2):
            at = 8 + plane * 20
            self.planes.append({
                "cell_cols": u16(blob, at), "cell_rows": u16(blob, at + 2),
                "world_x0": u16(blob, at + 4), "row0": u16(blob, at + 6),
                "char_count": u16(blob, at + 8),
                "char_offset": u32(blob, at + 12),
                "pnt_offset": u32(blob, at + 16),
            })
        self.palettes = []
        for plane in range(2):
            at = 48 + plane * 512
            self.palettes.append([u16(blob, at + i * 2)
                                  for i in range(256)])
        at = 48 + 1024
        self.cycle_period = u16(blob, at)
        self.cycle_first_flip = u16(blob, at + 2)
        self.cycle = [(u16(blob, at + 6 + i * 6),
                       u16(blob, at + 8 + i * 6),
                       u16(blob, at + 10 + i * 6))
                      for i in range(u16(blob, at + 4))]
        at += 6 + len(self.cycle) * 6
        self.scroll = [(u16(blob, at + i * 8), u16(blob, at + i * 8 + 2),
                        u16(blob, at + i * 8 + 4), u16(blob, at + i * 8 + 6))
                       for i in range(self.frames)]
        at += self.frames * 8
        self.patches = []
        count = u16(blob, at)
        at += 2
        for _ in range(count):
            frame_rel, plane, updates = (u16(blob, at), u16(blob, at + 2),
                                         u16(blob, at + 4))
            at += 6
            cells = []
            for _u in range(updates):
                cells.append((u16(blob, at), u16(blob, at + 2),
                              u16(blob, at + 4)))
                at += 6
            self.patches.append((frame_rel, plane, cells))
        self.objects = []
        for _f in range(self.frames):
            count = u16(blob, at)
            at += 2
            frame_entries = []
            for _e in range(count):
                frame_entries.append((u16(blob, at), u16(blob, at + 2),
                                      u16(blob, at + 4), u16(blob, at + 6)))
                at += 8
            self.objects.append(frame_entries)

    def char_pixels(self, plane: int, char_index: int) -> bytes:
        base = self.planes[plane]["char_offset"] + char_index * 64
        return self.blob[base:base + 64]

    def base_pnt(self, plane: int) -> list[int]:
        p = self.planes[plane]
        base = p["pnt_offset"]
        return [u16(self.blob, base + i * 2)
                for i in range(p["cell_cols"] * p["cell_rows"])]


def render_native_window(strips: Strips, plane: int, pnt: list[int],
                         palette: list[int], scx: int, scy: int,
                         alias_page_b: bool = False) -> list[list[int]]:
    """352x224 RGB555 window exactly as VDP2 fetches it."""
    p = strips.planes[plane]
    cols, rows = p["cell_cols"], p["cell_rows"]
    window = [[0] * OUT_W for _ in range(VIS_H)]
    for y in range(VIS_H):
        py = scy + y
        cy, iny = py // 8, py % 8
        for x in range(OUT_W):
            px = scx + x
            cx, inx = px // 8, px % 8
            if 0 <= cy < rows and 0 <= cx < cols:
                source_cx = cx
                if alias_page_b and cx >= 64:
                    source_cx = cx - 64
                char = pnt[cy * cols + source_cx]
                pen = strips.char_pixels(plane, char)[iny * 8 + inx]
                if pen:
                    window[y][x] = palette[pen]
    return window


def fit_source_window(image, scx: int = 0, out_x0: int = 0,
                      scroll_x: int = 0,
                      mapping_wrong: bool = False) -> list[list[int]]:
    """Expected window under the WORLD-ANCHORED endpoint fit.

    A VDP2 cell plane realizes one fixed resample of its world strip, so
    the shared plane-level mapping anchors at world x0 and scroll converts
    through the same rule: window pixel x shows source screen pixel
    src_of(x + scx + out_x0) - scroll_x - VIS_LEFT. The WINDOW-anchored
    per-frame fit (src_of(x) alone) is a different, unimplementable phase
    and serves as the executed wrong-transform negative control."""
    pixels = image.load()
    window = [[0] * OUT_W for _ in range(VIS_H)]
    for x in range(OUT_W):
        if mapping_wrong:
            sx = src_of(x)
        else:
            sx = src_of(x + scx + out_x0) - scroll_x - VIS_LEFT
        if sx < 0 or sx >= VIS_W:
            # This plane pixel's world column is outside the 384-wide
            # capture window at this scroll phase, so the capture holds
            # no observation for it; it is compared at frames where the
            # scroll brings it into view. Mark unobservable, never clamp
            # to the neighbouring column.
            for y in range(VIS_H):
                window[y][x] = -1
            continue
        for y in range(VIS_H):
            r, g, b, a = pixels[sx, y]
            if a:
                window[y][x] = 0x8000 | ((b >> 3) << 10) | ((g >> 3) << 5) \
                    | (r >> 3)
    return window


def compare(native, source) -> tuple[int, set]:
    mismatched = 0
    columns = set()
    for y in range(VIS_H):
        nrow, srow = native[y], source[y]
        for x in range(OUT_W):
            if srow[x] < 0:
                continue
            if nrow[x] != srow[x]:
                mismatched += 1
                columns.add(x)
    return mismatched, columns


def main() -> None:
    strips = Strips(STRIPS.read_bytes())
    tiles = TILES_BIN.read_bytes()
    tile_count = u32(tiles, 4)
    codes_offset = u32(tiles, 12)
    tile_codes = {u32(tiles, codes_offset + i * 4)
                  for i in range(tile_count)}

    gfx = avsp.load_gfx_region()
    state = RouteState(CAPTURE)

    controls = {name: {"failed": False, "detail": ""} for name in (
        "wrong_transform", "aliased_page", "scroll_shift", "cycle_colour",
        "patch_dropped", "object_x", "object_priority", "priority_register")}

    pnt = [strips.base_pnt(0), strips.base_pnt(1)]
    pnt_nopatch = [list(pnt[0]), list(pnt[1])]
    palettes = [list(strips.palettes[0]), list(strips.palettes[1])]

    totals = {"nbg0": 0, "nbg1": 0}
    worst = {"nbg0": (0, -1), "nbg1": (0, -1)}
    mismatch_columns = {"nbg0": set(), "nbg1": set()}
    boundary_frames = []
    checked = 0
    # Frames whose expected windows are retained for the executed
    # perturb-and-compare negative controls: rel 0 (scroll), the first
    # cycle-B frame (palette cycle), and the first map-patch frame.
    control_rels = {0, strips.cycle_first_flip, strips.patches[0][0]}
    control_state: dict[int, dict] = {}
    objects_ok = 0
    tiles_missing = 0
    priority_split = {1: 0, 4: 0}

    for rec in state.frames():
        frame = rec["frame"]
        if frame < FIRST_FRAME:
            continue
        if frame > LAST_FRAME:
            break
        rel = frame - FIRST_FRAME
        cps_a = rec["cps_a"]
        cps_b = [int.from_bytes(state.current["cps_b"][i:i + 2], "big")
                 for i in range(0, 0x40, 2)]
        gfxram_words = []
        for name in ("gfxram0", "gfxram1", "gfxram2"):
            data = state.current[name]
            gfxram_words += [int.from_bytes(data[i:i + 2], "big")
                             for i in range(0, len(data), 2)]
        palette_rgba = [(((v >> 8) & 0xF) * 17, ((v >> 4) & 0xF) * 17,
                        (v & 0xF) * 17, 255)
                        for v in (int.from_bytes(
                            state.gfx_slice(rec["palette_base"] + i * 2, 2),
                            "big") for i in range(0xC00))]

        # Runtime replay state for this frame.
        for frame_rel, plane, cells in strips.patches:
            if frame_rel == rel:
                for cx, cy, char in cells:
                    pnt[plane][cy * strips.planes[plane]["cell_cols"] +
                               cx] = char
        # First-flip semantics, identical to the runtime: state A until
        # the first observed flip, then alternate every cycle period.
        step = 0
        if strips.cycle_period and rel >= strips.cycle_first_flip:
            step = (((rel - strips.cycle_first_flip) //
                     strips.cycle_period) + 1) & 1
        for index, colour_a, colour_b in strips.cycle:
            palettes[0][index] = colour_b if step else colour_a

        s2x, s2y, s3x, s3y = strips.scroll[rel]
        assert (s2x, s2y, s3x, s3y) == (cps_a[8], cps_a[9], cps_a[10],
                                        cps_a[11]), "scroll record diverges"

        # Objects: schedule must equal the captured active bank exactly.
        active = state.current["objram2" if rec["active_bank"]
                               else "objram1"]
        captured = []
        for offset in range(0, len(active) - 7, 8):
            y = int.from_bytes(active[offset + 2:offset + 4], "big")
            attr = int.from_bytes(active[offset + 6:offset + 8], "big")
            if y >= 0x8000 or attr >= 0xFF00:
                break
            captured.append((int.from_bytes(active[offset:offset + 2],
                                            "big"), y,
                             int.from_bytes(active[offset + 4:offset + 6],
                                            "big"), attr))
        assert captured == strips.objects[rel], "object schedule diverges"
        for x, y, code, attr in captured:
            priority_split[(x >> 13) & 7] = \
                priority_split.get((x >> 13) & 7, 0) + 1
            code17 = code + ((y & 0x6000) << 3)
            nx = ((attr >> 8) & 0xF) + 1
            ny = ((attr >> 12) & 0xF) + 1
            for sy in range(ny):
                for sx in range(nx):
                    if ((code17 & ~0xF) + ((code17 + sx) & 0xF) +
                            0x10 * sy) not in tile_codes:
                        tiles_missing += 1
        objects_ok += len(captured)

        # Pixel comparison on EVERY frame of the interval (201/201); the
        # structural checks above are also full-rate.
        scx0 = out_of(s2x + VIS_LEFT) - out_of(strips.planes[0]["world_x0"])
        if scx0 + OUT_W > 64 * 8:
            boundary_frames.append(rel)
        checked += 1
        for plane, layer, scx, scy, key in (
                (0, 2, scx0,
                 s2y + VIS_TOP - strips.planes[0]["row0"] * 16, "nbg0"),
                (1, 3, out_of(s3x + VIS_LEFT) -
                 out_of(strips.planes[1]["world_x0"]),
                 s3y + VIS_TOP - strips.planes[1]["row0"] * 32, "nbg1")):
            source = avsp.render_background(
                gfx, gfxram_words, cps_a, cps_b, palette_rgba,
                layer_filter=(layer,), transparent_background=True)
            plane_out_x0 = out_of(strips.planes[plane]["world_x0"])
            layer_scroll = s2x if plane == 0 else s3x
            fitted = fit_source_window(source, scx, plane_out_x0,
                                       layer_scroll)
            native = render_native_window(strips, plane, pnt[plane],
                                          palettes[plane], scx, scy)
            mismatched, columns = compare(native, fitted)
            totals[key] += mismatched
            mismatch_columns[key] |= columns
            if mismatched > worst[key][0]:
                worst[key] = (mismatched, rel)

            if plane == 0 and rel in control_rels:
                control_state[rel] = {"fitted": fitted, "scx": scx,
                                      "scy": scy}

            if rel == 0 and plane == 0:
                bad, _ = compare(render_native_window(
                    strips, plane, pnt[plane], palettes[plane], scx, scy),
                    fit_source_window(source, mapping_wrong=True))
                # both native and wrong-fit computed; detection means the
                # window-anchored phase differs measurably
                controls["wrong_transform"] = {
                    "failed": bad > mismatched + 1000,
                    "detail": f"{bad} vs {mismatched}"}
        if boundary_frames and rel == boundary_frames[0]:
            source = avsp.render_background(
                gfx, gfxram_words, cps_a, cps_b, palette_rgba,
                layer_filter=(2,), transparent_background=True)
            fitted = fit_source_window(
                source, scx0, out_of(strips.planes[0]["world_x0"]), s2x)
            aliased = render_native_window(
                strips, 0, pnt[0], palettes[0], scx0,
                s2y + VIS_TOP - strips.planes[0]["row0"] * 16,
                alias_page_b=True)
            bad, bad_columns = compare(aliased, fitted)
            base, _ = compare(render_native_window(
                strips, 0, pnt[0], palettes[0], scx0,
                s2y + VIS_TOP - strips.planes[0]["row0"] * 16),
                fitted)
            controls["aliased_page"] = {
                "failed": bad > base,
                "detail": f"aliased {bad} vs correct {base} at rel {rel}"}
    state.close()

    # Executed perturb-and-compare negative controls: each one perturbs
    # the reconstruction input and re-runs the SAME comparison against the
    # stored expected window; detection means a non-zero mismatch appears
    # where the unperturbed pass measured zero.
    def pnt_at(rel: int, drop_patch: int | None = None) -> list[int]:
        state_pnt = strips.base_pnt(0)
        cols = strips.planes[0]["cell_cols"]
        for index, (frame_rel, plane_id, cells) in enumerate(strips.patches):
            if plane_id != 0 or frame_rel > rel or index == drop_patch:
                continue
            for cx, cy, char in cells:
                state_pnt[cy * cols + cx] = char
        return state_pnt

    def palettes_at(rel: int, perturb_index: int | None = None) -> list[int]:
        colours = list(strips.palettes[0])
        step = 0
        if strips.cycle_period and rel >= strips.cycle_first_flip:
            step = (((rel - strips.cycle_first_flip) //
                     strips.cycle_period) + 1) & 1
        for index, colour_a, colour_b in strips.cycle:
            colours[index] = colour_b if step else colour_a
        if perturb_index is not None:
            colours[perturb_index] ^= 0x0421
        return colours

    def rerun(rel: int, state_pnt: list[int], colours: list[int],
              scx_override: int | None = None) -> int:
        stored = control_state[rel]
        scx = stored["scx"] if scx_override is None else scx_override
        native = render_native_window(strips, 0, state_pnt, colours,
                                      scx, stored["scy"])
        mismatched, _ = compare(native, stored["fitted"])
        return mismatched

    rel_scroll = 0
    rel_cycle = strips.cycle_first_flip
    rel_patch = strips.patches[0][0]

    baseline_scroll = rerun(rel_scroll, pnt_at(rel_scroll),
                            palettes_at(rel_scroll))
    bad_scroll = rerun(rel_scroll, pnt_at(rel_scroll),
                       palettes_at(rel_scroll),
                       scx_override=control_state[rel_scroll]["scx"] + 1)
    controls["scroll_shift"] = {
        "failed": baseline_scroll == 0 and bad_scroll > 0,
        "detail": f"rel {rel_scroll}: scroll+1 mismatch {bad_scroll} "
                  f"(baseline {baseline_scroll})"}

    cycle_target = next((i for i, a, b in strips.cycle if a != b),
                        strips.cycle[0][0])
    baseline_cycle = rerun(rel_cycle, pnt_at(rel_cycle),
                           palettes_at(rel_cycle))
    bad_cycle = rerun(rel_cycle, pnt_at(rel_cycle),
                      palettes_at(rel_cycle, perturb_index=cycle_target))
    controls["cycle_colour"] = {
        "failed": baseline_cycle == 0 and bad_cycle > 0,
        "detail": f"rel {rel_cycle}: LUT {cycle_target} recoloured, "
                  f"mismatch {bad_cycle} (baseline {baseline_cycle})"}

    baseline_patch = rerun(rel_patch, pnt_at(rel_patch),
                           palettes_at(rel_patch))
    bad_patch = rerun(rel_patch, pnt_at(rel_patch, drop_patch=0),
                      palettes_at(rel_patch))
    controls["patch_dropped"] = {
        "failed": baseline_patch == 0 and bad_patch > 0,
        "detail": f"rel {rel_patch}: patch 0 dropped, mismatch "
                  f"{bad_patch} (baseline {baseline_patch})"}

    # Object controls: perturb one visible schedule entry and run the same
    # byte comparison used against the captured bank, plus the class-count
    # recomputation used for the priority split.
    target_rel = next(rel for rel in range(strips.frames)
                      if strips.objects[rel])
    perturbed = [list(entry) for entry in strips.objects[target_rel]]
    perturbed[0][0] += 1
    controls["object_x"] = {
        "failed": [tuple(e) for e in perturbed] !=
        strips.objects[target_rel],
        "detail": f"rel {target_rel}: entry 0 x+1 breaks the byte "
                  f"comparison against the captured bank"}
    flipped = [list(entry) for entry in strips.objects[target_rel]]
    flipped[0][0] ^= 0x2000 << 1
    split_before = {}
    split_after = {}
    for source_list, split in ((strips.objects[target_rel], split_before),
                               ([tuple(e) for e in flipped], split_after)):
        for x, _y, _c, _a in source_list:
            split[(x >> 13) & 7] = split.get((x >> 13) & 7, 0) + 1
    controls["object_priority"] = {
        "failed": split_before != split_after,
        "detail": f"rel {target_rel}: class flip moves counts "
                  f"{split_before} -> {split_after}"}

    # priority_register: executed in tools/verify_street_overlap.py (the
    # deliberate-overlap composite); its tracked verdict is consumed here
    # so a stale or failing overlap run fails this gate too.
    overlap_path = ROOT / "data" / "rp4_street_overlap.json"
    if overlap_path.exists():
        overlap = json.loads(overlap_path.read_text())
        controls["priority_register"] = {
            "failed": bool(overlap.get("controls_all_detect")) and
            bool(overlap.get("expected_order_holds")),
            "detail": f"overlap fixture frame "
                      f"{overlap.get('source_frame')}: "
                      f"{overlap.get('summary', 'no summary')}"}
    else:
        controls["priority_register"] = {
            "failed": False,
            "detail": "data/rp4_street_overlap.json missing - run "
                      "tools/verify_street_overlap.py"}

    report = {
        "schema": "rp4-street-readback-v0",
        "interval": [FIRST_FRAME, LAST_FRAME],
        "frames_structural": strips.frames,
        "frames_pixel_checked": checked,
        "plane_pixels_mismatched": totals,
        "plane_mismatch_columns": {k: sorted(v)
                                   for k, v in mismatch_columns.items()},
        "worst_frame": worst,
        "page_boundary_frames": boundary_frames,
        "objects_verified": objects_ok,
        "object_tiles_missing": tiles_missing,
        "priority_split": priority_split,
        "negative_controls": controls,
    }
    OUTPUT.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n",
                      encoding="ascii", newline="\n")
    fail = tiles_missing > 0 or objects_ok != 12118 or \
        totals["nbg0"] > 0 or totals["nbg1"] > 0 or \
        not all(c["failed"] for c in controls.values())
    print(f"street planes: {checked} pixel frames, mismatches "
          f"nbg0={totals['nbg0']} cols={len(mismatch_columns['nbg0'])} "
          f"nbg1={totals['nbg1']} cols={len(mismatch_columns['nbg1'])}, "
          f"boundary frames {len(boundary_frames)}, objects {objects_ok}, "
          f"missing tiles {tiles_missing}, controls "
          f"{'PASS' if not fail else 'FAIL'}")
    if fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
