#!/usr/bin/env python3
"""Chapter 2: scan the ENTIRE street scene for actor/foreground overlaps.

The RP4 contract needs a deliberate, measured overlap between a visible
priority-1 actor-class object and foreground-class content above it. The
previous interval (3474-3674) was falsified: all 402 actor entries were
parked offscreen. This scanner sweeps the complete street gameplay range
from the cadence-1 deterministic full-route capture and finds every
frame that can carry the proof.

Street bounds come from the semantic scene manifest
(round1-street-gameplay), not from hard-coded numbers.

Per frame:
  phase A (geometric): decode raw objram entries, classify priority,
    intersect actor and foreground bounding boxes with the visible
    window and each other;
  phase B (pixel, only for phase-A survivors): render both class
    surfaces, count exact same-pixel overlaps, and require a WITNESS
    pixel whose actor and foreground colours differ (so priority
    perturbations are observable).

Interval selection: the ~201-frame window with the most pixel-verified
overlap frames, then checked for independent scroll2/scroll3 motion and
an object-schedule change.

Tracked output data/rp4_overlap_candidates.json: counts, rejection
reasons, the selected interval, and the chosen overlap identity - no
pixel buffers, no captured frames.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import extract_avspu_stage1 as avsp                     # noqa: E402
from census_full_route import RouteState                # noqa: E402

CAPTURE = ROOT / ".deps" / "mame" / "full_route"
MANIFEST = ROOT / "data" / "avsp_scene_manifest.json"
OUTPUT = ROOT / "data" / "rp4_overlap_candidates.json"

ACTOR_PRIORITY = 1
FOREGROUND_PRIORITY = 4
WINDOW = 201


def street_bounds() -> tuple[int, int]:
    manifest = json.loads(MANIFEST.read_text())
    scene = next(s for s in manifest["scenes"]
                 if s["label"] == "round1-street-gameplay")
    return scene["first_frame"], scene["last_frame"]


def entries_of(active: bytes) -> list[dict]:
    out = []
    for off in range(0, len(active) - 7, 8):
        x = int.from_bytes(active[off:off + 2], "big")
        y = int.from_bytes(active[off + 2:off + 4], "big")
        code = int.from_bytes(active[off + 4:off + 6], "big")
        attr = int.from_bytes(active[off + 6:off + 8], "big")
        if y >= 0x8000 or attr >= 0xFF00:
            break
        w = (((attr >> 8) & 0xF) + 1) * 16 if attr & 0xFF00 else 16
        h = (((attr >> 12) & 0xF) + 1) * 16 if attr & 0xFF00 else 16
        sx = (x & 0x3FF) - 64
        sy = (y & 0x3FF) - 16
        out.append({"slot": off // 8, "x": sx, "y": sy, "w": w, "h": h,
                    "priority": (x >> 13) & 7, "code": code, "attr": attr})
    return out


def onscreen(e) -> bool:
    return (e["x"] + e["w"] > 0 and e["x"] < 384 and
            e["y"] + e["h"] > 0 and e["y"] < 224)


def bbox_overlap(a, b) -> bool:
    return (a["x"] < b["x"] + b["w"] and b["x"] < a["x"] + a["w"] and
            a["y"] < b["y"] + b["h"] and b["y"] < a["y"] + a["h"])


def words_for_priority(words, priority):
    out = []
    for offset in range(0, len(words) - 3, 4):
        x, y, code, attribute = words[offset:offset + 4]
        if y >= 0x8000 or attribute >= 0xFF00:
            break
        if ((x >> 13) & 7) == priority:
            out.extend([x, y, code, attribute])
    out.extend([0, 0x8000, 0, 0])
    return out


def main() -> None:
    first, last = street_bounds()
    state = RouteState(CAPTURE)
    gfx = avsp.load_gfx_region()

    per_frame: dict[int, dict] = {}
    rejections = {"no_actor_entries": 0, "actors_offscreen": 0,
                  "no_foreground_onscreen": 0, "no_bbox_overlap": 0,
                  "no_pixel_overlap": 0, "no_differing_witness": 0}
    pixel_frames: list[int] = []
    best_example: dict | None = None
    scanned = 0
    schedule = {}

    for rec in state.frames():
        f = rec["frame"]
        if f < first:
            continue
        if f > last:
            break
        scanned += 1
        active = state.current[
            "objram2" if rec["active_bank"] else "objram1"]
        entries = entries_of(active)
        schedule[f] = (rec["object_count"], rec["cps_a"][8],
                       rec["cps_a"][10])
        actors = [e for e in entries if e["priority"] == ACTOR_PRIORITY]
        fores = [e for e in entries
                 if e["priority"] == FOREGROUND_PRIORITY and onscreen(e)]
        if not actors:
            rejections["no_actor_entries"] += 1
            continue
        actors_on = [e for e in actors if onscreen(e)]
        if not actors_on:
            rejections["actors_offscreen"] += 1
            continue
        if not fores:
            rejections["no_foreground_onscreen"] += 1
            continue
        pairs = [(a, b) for a in actors_on for b in fores
                 if bbox_overlap(a, b)]
        if not pairs:
            rejections["no_bbox_overlap"] += 1
            per_frame[f] = {"verdict": "bbox-miss",
                            "actors_onscreen": len(actors_on),
                            "foreground_onscreen": len(fores)}
            continue

        # Phase B: exact pixel verification with a differing witness.
        words = [int.from_bytes(active[i:i + 2], "big")
                 for i in range(0, len(active), 2)]
        palette = [(((c >> 8) & 0xF) * 17, ((c >> 4) & 0xF) * 17,
                   (c & 0xF) * 17, 255)
                   for c in (int.from_bytes(
                       state.gfx_slice(rec["palette_base"] + i * 2, 2),
                       "big") for i in range(0xC00))]
        actor_img, _ = avsp.decode_objects(
            gfx, words_for_priority(words, ACTOR_PRIORITY), palette)
        fore_img, _ = avsp.decode_objects(
            gfx, words_for_priority(words, FOREGROUND_PRIORITY), palette)
        pa, pf = actor_img.load(), fore_img.load()
        count = 0
        witness = None
        for a, b in pairs:
            x0 = max(a["x"], b["x"], 0)
            x1 = min(a["x"] + a["w"], b["x"] + b["w"], 384)
            y0 = max(a["y"], b["y"], 0)
            y1 = min(a["y"] + a["h"], b["y"] + b["h"], 224)
            for y in range(y0, y1):
                for x in range(x0, x1):
                    if pa[x, y][3] and pf[x, y][3]:
                        count += 1
                        if witness is None and pa[x, y][:3] != pf[x, y][:3]:
                            witness = (x, y, a, b)
        if count == 0:
            rejections["no_pixel_overlap"] += 1
            per_frame[f] = {"verdict": "pixel-miss",
                            "bbox_pairs": len(pairs)}
            continue
        if witness is None:
            rejections["no_differing_witness"] += 1
            per_frame[f] = {"verdict": "identical-colours",
                            "overlap_pixels": count}
            continue
        wx, wy, wa, wb = witness
        pixel_frames.append(f)
        per_frame[f] = {"verdict": "QUALIFIES", "overlap_pixels": count,
                        "witness": [wx, wy],
                        "actor_slot": wa["slot"], "actor_code": wa["code"],
                        "foreground_slot": wb["slot"]}
        if best_example is None or count > best_example["overlap_pixels"]:
            best_example = {
                "frame": f, "overlap_pixels": count,
                "witness_source_xy": [wx, wy],
                "fitted_xy": [(wx * 351 - 175 + 382) // 383, wy],
                "actor_slot": wa["slot"], "actor_code": wa["code"],
                "actor_attr": wa["attr"],
                "actor_xy": [wa["x"], wa["y"]],
                "foreground_slot": wb["slot"],
                "foreground_code": wb["code"],
                "foreground_attr": wb["attr"],
                "foreground_xy": [wb["x"], wb["y"]],
                "expected_winner": "foreground-class VDP1",
            }
        if f % 100 == 0:
            print(f"frame {f}: {count} overlap pixels "
                  f"({len(pixel_frames)} qualifying so far)", flush=True)
    state.close()

    # Interval choice: densest WINDOW of qualifying frames, then check
    # independent scroll motion and a schedule change inside it.
    interval = None
    if pixel_frames:
        best_count = -1
        for start in pixel_frames:
            end = start + WINDOW - 1
            inside = [f for f in pixel_frames if start <= f <= end]
            if len(inside) > best_count and end <= last:
                best_count = len(inside)
                interval = {"first_frame": start, "last_frame": end,
                            "qualifying_frames": len(inside)}
        if interval:
            frames_in = [f for f in schedule
                         if interval["first_frame"] <= f <=
                         interval["last_frame"]]
            s2 = [schedule[f][1] for f in frames_in]
            s3 = [schedule[f][2] for f in frames_in]
            counts = [schedule[f][0] for f in frames_in]
            interval["scroll2_x_span"] = max(s2) - min(s2)
            interval["scroll3_x_span"] = max(s3) - min(s3)
            interval["independent_scroll"] = (
                interval["scroll2_x_span"] != interval["scroll3_x_span"]
                and interval["scroll2_x_span"] > 0)
            interval["object_count_min"] = min(counts)
            interval["object_count_max"] = max(counts)
            interval["schedule_changes"] = (max(counts) != min(counts))
            interval["cadence1_contiguous"] = (
                len(frames_in) == interval["last_frame"] -
                interval["first_frame"] + 1)

    rom = ROOT / ".deps" / "mame" / "actorprobe" / \
        "decrypted_program_2m.bin"
    report = {
        "schema": "rp4-overlap-candidates-v0",
        "classification": "semantic scan results: counts, coordinates, "
                          "identities and rejection reasons only - no "
                          "pixel buffers or captured frames",
        "street_bounds": {"first_frame": first, "last_frame": last,
                          "source": "scene manifest "
                                    "round1-street-gameplay"},
        "frames_scanned": scanned,
        "rejections": rejections,
        "qualifying_frame_count": len(pixel_frames),
        "qualifying_frames_sample": pixel_frames[:50],
        "best_example": best_example,
        "selected_interval": interval,
        "inputs_sha256": {
            "route_census": hashlib.sha256(
                (ROOT / "data" / "round1_route_census.json")
                .read_bytes()).hexdigest(),
            "scene_manifest": hashlib.sha256(
                MANIFEST.read_bytes()).hexdigest(),
        },
        "per_frame_verdicts_sample": {
            str(f): per_frame[f] for f in sorted(per_frame)[:100]},
    }
    OUTPUT.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n",
                      encoding="ascii", newline="\n")
    print(f"street scan {first}-{last}: {scanned} frames, "
          f"{len(pixel_frames)} qualifying, rejections {rejections}")
    if interval:
        print(f"selected interval: {interval}")
    else:
        print("HARD STOP: no visible actor/foreground overlap in the "
              "entire street scene")
        raise SystemExit(3)


if __name__ == "__main__":
    main()
