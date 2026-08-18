#!/usr/bin/env python3
"""Validate and summarize the deterministic CPS-2 Ryu vertical slice."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, ImageChops


ANCHORS = {
    "idle": 1610,
    "walk": 1650,
    "jump": 1720,
    "normal_attack_active": 1788,
    "hadouken_input_complete": 1860,
    "hadouken_visible": 1875,
    "projectile_collision_hit_reaction": 1890,
    "recovery": 1920,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def changed_pixels(first: Image.Image, second: Image.Image) -> int:
    diff = ImageChops.difference(first.convert("RGB"), second.convert("RGB"))
    pixels = (
        diff.get_flattened_data()
        if hasattr(diff, "get_flattened_data")
        else diff.getdata()
    )
    return sum(1 for pixel in pixels if pixel != (0, 0, 0))


def anchor_metrics(root: Path) -> dict[str, object]:
    idle = Image.open(root / f"frame_{ANCHORS['idle']:05d}.png")
    metrics: dict[str, object] = {}
    for name, frame in ANCHORS.items():
        path = root / f"frame_{frame:05d}.png"
        image = Image.open(path)
        previous = Image.open(root / f"frame_{frame - 1:05d}.png")
        metrics[name] = {
            "frame": frame,
            "png_sha256": sha256(path),
            "size": list(image.size),
            "changed_pixels_vs_previous": changed_pixels(image, previous),
            "changed_pixels_vs_idle": changed_pixels(image, idle),
        }
    return metrics


def validate_capture(root: Path, first: int, last: int) -> dict[str, object]:
    required_prefixes = {
        "screenshots": "frame_{frame:05d}.png",
        "workram": "workram_{frame:05d}.bin",
        "object_ram": "objram_active_{frame:05d}.tsv",
        "palette": "palette_{frame:05d}.tsv",
        "cps_a_regs": "cps_a_regs_{frame:05d}.tsv",
        "cps_b_regs": "cps_b_regs_{frame:05d}.tsv",
    }
    missing: dict[str, list[int]] = {}
    for kind, template in required_prefixes.items():
        absent = [frame for frame in range(first, last + 1) if not (root / template.format(frame=frame)).is_file()]
        if absent:
            missing[kind] = absent
    if missing:
        raise RuntimeError(f"Capture is incomplete: {missing}")

    workram_sizes = {
        (root / f"workram_{frame:05d}.bin").stat().st_size
        for frame in range(first, last + 1)
    }
    if workram_sizes != {0x8000}:
        raise RuntimeError(f"Unexpected work-RAM sizes: {sorted(workram_sizes)}")

    return {
        "first_frame": first,
        "last_frame": last,
        "frame_count": last - first + 1,
        "all_required_streams_contiguous": True,
        "workram_address_range": "0xff8000..0xffffff",
        "workram_bytes_per_frame": 0x8000,
    }


def qsound_summary(path: Path) -> dict[str, object]:
    rows = read_tsv(path)
    commits_by_frame: dict[int, list[int]] = defaultdict(list)
    for row in rows:
        if row.get("register"):
            commits_by_frame[int(row["frame"])].append(int(row["register"], 16))

    def window(first: int, last: int) -> list[dict[str, object]]:
        return [
            {
                "frame": frame,
                "register_write_count": len(registers),
                "registers": [f"0x{register:02x}" for register in sorted(set(registers))],
            }
            for frame, registers in sorted(commits_by_frame.items())
            if first <= frame <= last
        ]

    return {
        "bus_write_rows": len(rows),
        "register_commit_rows": sum(len(items) for items in commits_by_frame.values()),
        "normal_attack_window": window(1778, 1810),
        "hadouken_collision_window": window(1848, 1910),
        "log_sha256": sha256(path),
    }


def persistent_step_decreases(root: Path, first: int = 1870, last: int = 1920) -> list[dict[str, object]]:
    frames = {
        frame: (root / f"workram_{frame:05d}.bin").read_bytes()
        for frame in range(first, last + 1)
    }
    candidates: list[dict[str, object]] = []
    size = len(frames[first])
    for offset in range(size):
        values = [frames[frame][offset] for frame in range(first, last + 1)]
        for index in range(3, len(values) - 3):
            before = values[index - 1]
            after = values[index]
            if not (0 < before - after <= 127):
                continue
            if len(set(values[index - 3:index])) != 1:
                continue
            if len(set(values[index:index + 4])) != 1:
                continue
            frame = first + index
            candidates.append(
                {
                    "workram_address": f"0x{0xff8000 + offset:06x}",
                    "frame": frame,
                    "before": before,
                    "after": after,
                    "delta": before - after,
                }
            )
            break
    candidates.sort(key=lambda item: (int(item["frame"]), int(item["workram_address"], 16)))
    return candidates[:64]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--capture-root",
        type=Path,
        default=Path(".deps/mame/mshvsf_vertical_slice"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/mshvsf_cps2_vertical_slice.json"),
    )
    args = parser.parse_args()

    root = args.capture_root.resolve()
    capture = validate_capture(root, 1560, 1960)
    samples = read_tsv(root / "samples.tsv")
    inputs = read_tsv(root / "input_events.tsv")
    phase_counts = Counter(row["phase"] for row in samples)

    report = {
        "title": "Marvel Super Heroes vs. Street Fighter CPS-2 Ryu vertical slice",
        "purpose": "Official-port research lane augmenting the AvP Saturn conversion",
        "source": {
            "emulator": "MAME 0.289",
            "romset": "mshvsf (Europe 970625)",
            "rom_audit": "pass",
            "route": "Two-player Ryu/Ken vs Spider-Man/Captain America; P2 remains neutral",
        },
        "capture": capture,
        "phase_frame_counts": dict(sorted(phase_counts.items())),
        "input_events": inputs,
        "semantic_anchors": anchor_metrics(root),
        "qsound": qsound_summary(root / "qsound_writes.tsv"),
        "workram_candidate_step_decreases": {
            "confidence": "LOW",
            "warning": "Candidates are timing leads only; none is labeled health or damage until a writer/read path and actor ownership are proven.",
            "items": persistent_step_decreases(root),
        },
        "claims": [
            {
                "claim": "The deterministic route reaches a native two-player match with Ryu active and a neutral Spider-Man target.",
                "evidence": ["frame 1610 screenshot", "recorded frontend input edges"],
                "test": "Cold boot from blank state and replay the recorded inputs.",
                "falsification": "Different active characters, an AI-controlled target, or a non-identical frame-1610 image hash.",
                "confidence": "HIGH",
            },
            {
                "claim": "The slice contains idle, forward walk, jump, standing light punch, Hadouken generation, projectile collision, and Spider-Man hit reaction in that order.",
                "evidence": [
                    "cadence-1 screenshots at frames 1610, 1650, 1720, 1788, 1875, and 1890",
                    "recorded input edges",
                    "synchronized object RAM, work RAM, palette/register, and QSound streams",
                ],
                "test": "Replay the route and require identical anchor hashes and contiguous evidence streams.",
                "falsification": "An anchor hash changes, an action appears out of order, or P2 receives an input before the reaction.",
                "confidence": "HIGH",
            },
        ],
        "remaining_uncertainty": [
            "Player and opponent actor-structure addresses are not yet mapped.",
            "The exact health/damage field and collision-box records are not yet identified.",
            "QSound register activity is captured but event-to-voice semantics are not yet decoded.",
            "No CPS-2-to-Saturn correspondence is claimed until the same slice is captured on the official Saturn port.",
        ],
        "rights_boundary": "Raw captures and ROM data remain ignored private inputs; this tracked report contains hashes and derived measurements only.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"Validated {capture['frame_count']} frames; "
        f"{len(report['workram_candidate_step_decreases']['items'])} low-confidence step-decrease leads."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
