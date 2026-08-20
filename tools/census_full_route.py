#!/usr/bin/env python3
"""RP2 census: group the full-route cadence-1 capture into provisional scenes.

Input is the private, git-ignored capture produced by
tools/mame_capture_full_route.lua (delta-encoded region blobs + per-frame
screenshots). Output is a tracked semantic census carrying hashes, counts,
addresses, and ranges only - never ROM bytes, framebuffer payloads, or audio.

Frame signature (stable within a scene, changing between scenes):
  - CPS-A base registers (scroll1/2/3 maps, row-scroll table, palette) and
    the video-control word, using the exact register semantics of
    tools/extract_avspu_stage1.py render_background;
  - the full CPS-B block hash (layer order/enable/priority);
  - the palette population bitmap (which 16-entry pages are non-zero),
    which separates scenes without treating palette fades as boundaries.

A group boundary opens whenever the signature changes or a single frame
rewrites more than GFX_CUT_BYTES of gfxram (a full-frame rewrite cut).
Every group receives a provisional AvspSceneDef v0 ID (bit 15 set); groups
whose boundary was a cut with no signature change are flagged for review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CAPTURE = ROOT / ".deps" / "mame" / "full_route"
DEFAULT_OUTPUT = ROOT / "data" / "round1_route_census.json"
CONTROL_OUTPUT = ROOT / "data" / "round1_route_census_controls.json"

REGION_SIZES = {
    "gfxram0": 0x10000, "gfxram1": 0x10000, "gfxram2": 0x10000,
    "cps_a": 0x40, "cps_b": 0x40, "objram1": 0x2000, "objram2": 0x2000,
    "output": 0x0C, "workram": 0x10000, "qsound": 0x2000,
}
GFX_REGIONS = ("gfxram0", "gfxram1", "gfxram2")
# The capture snapshots whole 64 KiB gfxram thirds, so the per-frame delta is
# quantized to 0x10000/0x20000/0x30000. Ordinary gameplay tile streaming and
# palette writes touch exactly one third per frame (measured p99.9 = 0x10000
# over the 18000-frame route); a frame rewriting two or more thirds is a
# full-frame scene rewrite. The cut therefore fires above one third.
GFX_CUT_BYTES = 0x1FFFF
PALETTE_BYTES = 0xC00 * 2          # 6 pages x 16 palettes x 16 entries
MAP_BYTES = 0x4000                 # one CPS scroll tilemap
ROWSCROLL_BYTES = 0x800


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_index(capture: Path) -> dict[int, list[tuple[str, int, int]]]:
    per_frame: dict[int, list[tuple[str, int, int]]] = {}
    with (capture / "region_index.tsv").open() as stream:
        next(stream)
        for line in stream:
            frame_text, region, offset, length = line.rstrip("\n").split("\t")
            per_frame.setdefault(int(frame_text), []).append(
                (region, int(offset), int(length)))
    return per_frame


def load_samples(capture: Path) -> list[tuple[int, int, int, int]]:
    rows = []
    with (capture / "samples.tsv").open() as stream:
        next(stream)
        for line in stream:
            frame, word, bank, writes = (int(v) for v in line.split("\t"))
            rows.append((frame, word, bank, writes))
    return rows


def words_be(data: bytes) -> list[int]:
    return [int.from_bytes(data[i:i + 2], "big")
            for i in range(0, len(data), 2)]


def object_count(objram: bytes) -> int:
    count = 0
    for offset in range(0, len(objram) - 7, 8):
        y = int.from_bytes(objram[offset + 2:offset + 4], "big")
        attribute = int.from_bytes(objram[offset + 6:offset + 8], "big")
        if y >= 0x8000 or attribute >= 0xFF00:
            break
        count += 1
    return count


def run_length(values: list[int]) -> list[list[int]]:
    runs: list[list[int]] = []
    for value in values:
        if runs and runs[-1][0] == value:
            runs[-1][1] += 1
        else:
            runs.append([value, 1])
    return runs


class RouteState:
    """Streams the delta capture and yields one feature record per frame."""

    def __init__(self, capture: Path):
        self.capture = capture
        self.index = load_index(capture)
        self.samples = load_samples(capture)
        self.blobs = {name: (capture / f"region_{name}.bin").open("rb")
                      for name in REGION_SIZES}
        self.current: dict[str, bytes] = {}
        self.slice_hash_cache: dict[tuple[str, int, int], str] = {}

    def close(self) -> None:
        for blob in self.blobs.values():
            blob.close()

    def gfx_slice(self, byte_address: int, length: int) -> bytes:
        data = b""
        while length > 0:
            region = GFX_REGIONS[byte_address // 0x10000]
            inner = byte_address % 0x10000
            take = min(length, 0x10000 - inner)
            data += self.current[region][inner:inner + take]
            byte_address += take
            length -= take
        return data

    def frames(self):
        for frame, input_word, bank, writes in self.samples:
            changed: dict[str, int] = {}
            for region, offset, length in self.index.get(frame, ()):
                blob = self.blobs[region]
                blob.seek(offset)
                data = blob.read(length)
                if len(data) != length:
                    raise ValueError(
                        f"short read: {region} frame {frame}")
                self.current[region] = data
                changed[region] = length
            cps_a = words_be(self.current["cps_a"])
            palette_base = (cps_a[5] * 256) & 0x3FFFF
            map_bases = [((cps_a[reg] * 256) & 0x3FFFF) & ~(MAP_BYTES - 1)
                         for reg in (1, 2, 3)]
            rowscroll_base = ((cps_a[4] * 256) & 0x3FFFF) & \
                ~(ROWSCROLL_BYTES - 1)
            palette = self.gfx_slice(palette_base, PALETTE_BYTES)
            population = 0
            for page in range(PALETTE_BYTES // 32):
                if palette[page * 32:page * 32 + 32].strip(b"\x00"):
                    population |= 1 << page
            active = self.current["objram2" if bank else "objram1"]
            yield {
                "frame": frame,
                "input_word": input_word,
                "changed": changed,
                "cps_a": cps_a,
                "cps_b_hash": sha(self.current["cps_b"]),
                "palette_hash": sha(palette),
                "palette_population": f"{population:048x}",
                "map_hashes": [sha(self.gfx_slice(base, MAP_BYTES))
                               for base in map_bases],
                "rowscroll_hash": sha(
                    self.gfx_slice(rowscroll_base, ROWSCROLL_BYTES)),
                "map_bases": map_bases,
                "palette_base": palette_base,
                "rowscroll_base": rowscroll_base,
                "object_count": object_count(active),
                "qsound_changed": "qsound" in changed,
                "workram_hash": sha(self.current["workram"]),
                "scroll": (cps_a[6], cps_a[7], cps_a[8],
                           cps_a[9], cps_a[10], cps_a[11]),
                "video_control": cps_a[17],
                "layer_bases": tuple(cps_a[1:6]),
            }


def signature(record: dict) -> tuple:
    return (record["layer_bases"], record["video_control"],
            record["cps_b_hash"], record["palette_population"])


def build_groups(records: list[dict],
                 cut_bytes: int = GFX_CUT_BYTES,
                 boundary_shift: int = 0,
                 perturb_frame: int | None = None) -> list[dict]:
    groups: list[dict] = []
    previous_signature = None
    for position, record in enumerate(records):
        gfx_delta = sum(record["changed"].get(name, 0)
                        for name in GFX_REGIONS)
        sig = signature(record)
        if perturb_frame is not None and record["frame"] == perturb_frame:
            sig = sig + ("perturbed",)
        boundary_position = max(0, position - boundary_shift)
        effective = records[boundary_position]
        effective_delta = sum(effective["changed"].get(name, 0)
                              for name in GFX_REGIONS) \
            if boundary_shift else gfx_delta
        reason = None
        if not groups:
            reason = "route-start"
        elif sig != previous_signature:
            reason = "signature-change"
        elif effective_delta > cut_bytes:
            reason = "gfx-rewrite-cut"
        if reason:
            groups.append({
                "first_frame": record["frame"],
                "last_frame": record["frame"],
                "boundary_reason": reason,
                "signature": sig,
                "records": [],
            })
        group = groups[-1]
        group["last_frame"] = record["frame"]
        group["records"].append(record)
        previous_signature = sig
    return groups


def summarize_groups(groups: list[dict]) -> list[dict]:
    summary = []
    for index, group in enumerate(groups):
        records = group["records"]
        scroll_min = [min(r["scroll"][axis] for r in records)
                      for axis in range(6)]
        scroll_max = [max(r["scroll"][axis] for r in records)
                      for axis in range(6)]
        counts = [r["object_count"] for r in records]
        input_events = run_length([r["input_word"] for r in records])
        map_hash_sets = [len({r["map_hashes"][layer] for r in records})
                         for layer in range(3)]
        summary.append({
            "provisional_scene_id": f"0x{0x8000 | index:04x}",
            "first_frame": group["first_frame"],
            "last_frame": group["last_frame"],
            "frames": len(records),
            "boundary_reason": group["boundary_reason"],
            "layer_bases": [f"0x{b:04x}" for b in group["signature"][0]],
            "video_control": f"0x{group['signature'][1]:04x}",
            "cps_b_sha256": group["signature"][2],
            "palette_population": group["signature"][3],
            "palette_hashes": len({r["palette_hash"] for r in records}),
            "map_unique_hashes": map_hash_sets,
            "rowscroll_unique_hashes":
                len({r["rowscroll_hash"] for r in records}),
            "scroll_min": scroll_min,
            "scroll_max": scroll_max,
            "object_count_min": min(counts),
            "object_count_max": max(counts),
            "input_word_runs": input_events,
            "qsound_change_frames":
                sum(1 for r in records if r["qsound_changed"]),
            "review_flags": (["unexplained-full-frame-rewrite"]
                             if group["boundary_reason"] ==
                             "gfx-rewrite-cut" else []),
        })
    return summary


def region_summaries(records: list[dict],
                     state: RouteState) -> dict[str, dict]:
    change_frames: dict[str, list[int]] = {n: [] for n in REGION_SIZES}
    for record in records:
        for name in record["changed"]:
            change_frames[name].append(record["frame"])
    timeline = {}
    workram_stream = hashlib.sha256()
    for record in records:
        workram_stream.update(record["workram_hash"].encode())
    for name, frames in change_frames.items():
        timeline[name] = {
            "change_count": len(frames),
            "first_change": frames[0] if frames else None,
            "last_change": frames[-1] if frames else None,
            "change_frames_sha256": sha(
                ",".join(str(f) for f in frames).encode()),
        }
    timeline["workram"]["per_frame_hash_stream_sha256"] = \
        workram_stream.hexdigest()
    return timeline


def screenshot_summary(capture: Path, frames: list[int]) -> dict:
    from PIL import Image
    stream = hashlib.sha256()
    held_runs: list[list[int]] = []
    previous = None
    unique = 0
    for frame in frames:
        path = capture / f"reference_{frame:05d}.png"
        with Image.open(path) as image:
            digest = sha(image.convert("RGB").tobytes())
        stream.update(digest.encode())
        if digest == previous:
            held_runs[-1][1] = frame
        else:
            unique += 1
            held_runs.append([frame, frame])
        previous = digest
    holds = [run for run in held_runs if run[1] > run[0]]
    return {
        "frames": len(frames),
        "unique_frames": unique,
        "pixel_hash_stream_sha256": stream.hexdigest(),
        "held_runs": holds,
    }


def negative_controls(records: list[dict]) -> dict:
    baseline = build_groups(records)
    base_boundaries = [g["first_frame"] for g in baseline]

    shifted = build_groups(records, boundary_shift=1)
    shifted_boundaries = [g["first_frame"] for g in shifted]
    shift_detected = shifted_boundaries != base_boundaries

    longest = max(baseline, key=lambda g: g["last_frame"] - g["first_frame"])
    middle = (longest["first_frame"] + longest["last_frame"]) // 2
    perturbed = build_groups(records, perturb_frame=middle)
    boundary_detected = len(perturbed) == len(baseline) + 2 or \
        [g["first_frame"] for g in perturbed] != base_boundaries

    return {
        "baseline_groups": len(baseline),
        "one_frame_shift": {
            "detected": shift_detected,
            "groups": len(shifted),
            "boundaries_moved": sum(
                1 for a, b in zip(base_boundaries, shifted_boundaries)
                if a != b),
        },
        "perturbed_boundary": {
            "detected": boundary_detected,
            "perturbed_frame": middle,
            "groups": len(perturbed),
        },
        "pass": shift_detected and boundary_detected,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-root", type=Path, default=DEFAULT_CAPTURE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--controls", action="store_true",
                        help="also run the negative controls and write "
                             "the tracked control report")
    parser.add_argument("--skip-screenshots", action="store_true")
    args = parser.parse_args()

    state = RouteState(args.capture_root)
    records = list(state.frames())
    state.close()

    groups = build_groups(records)
    summary = summarize_groups(groups)
    regions = region_summaries(records, state)
    frames = [r["frame"] for r in records]

    census = {
        "schema": "round1-route-census-v0",
        "classification":
            "semantic census of the private full-route cadence-1 capture; "
            "hashes, counts, addresses and ranges only - no ROM bytes, "
            "framebuffer payloads, or audio",
        "route": {
            "first_frame": frames[0],
            "last_frame": frames[-1],
            "frame_count": len(frames),
            "cadence": 1,
        },
        "group_count": len(summary),
        "unclassified_groups": [],
        "groups": summary,
        "regions": regions,
    }
    if not args.skip_screenshots:
        census["screenshots"] = screenshot_summary(args.capture_root, frames)

    args.output.write_text(
        json.dumps(census, indent=1, sort_keys=True) + "\n",
        encoding="ascii", newline="\n")
    print(f"census: {len(frames)} frames, {len(summary)} groups "
          f"-> {args.output}")

    if args.controls:
        controls = negative_controls(records)
        CONTROL_OUTPUT.write_text(
            json.dumps(controls, indent=1, sort_keys=True) + "\n",
            encoding="ascii", newline="\n")
        print(f"controls: shift detected={controls['one_frame_shift']['detected']} "
              f"boundary detected={controls['perturbed_boundary']['detected']} "
              f"pass={controls['pass']}")
        if not controls["pass"]:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
