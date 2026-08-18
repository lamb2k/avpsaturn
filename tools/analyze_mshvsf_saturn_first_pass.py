#!/usr/bin/env python3
"""Validate and summarize the deterministic Saturn Ryu first pass."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops


ANCHORS = {
    "idle": 3540,
    "walk": 3620,
    "jump": 3720,
    "normal_input": 3820,
    "normal_attack_active": 3828,
    "collision_damage_hit_reaction": 3840,
    "recovery": 3900,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def changed_pixels(first: Image.Image, second: Image.Image) -> int:
    diff = ImageChops.difference(first.convert("RGB"), second.convert("RGB"))
    pixels = (
        diff.get_flattened_data()
        if hasattr(diff, "get_flattened_data")
        else diff.getdata()
    )
    return sum(1 for pixel in pixels if pixel != (0, 0, 0))


def pngs_by_name(root: Path) -> dict[str, Path]:
    return {path.name: path for path in root.glob("*.png")}


def validate_replays(
    record_a: Path,
    record_b: Path,
    capture_a: Path,
    capture_b: Path,
) -> tuple[dict[str, object], dict[str, object]]:
    record_hash_a = sha256(record_a)
    record_hash_b = sha256(record_b)
    if record_hash_a != record_hash_b:
        raise RuntimeError("Replay records differ")

    record = json.loads(record_a.read_text(encoding="utf-8"))
    images_a = pngs_by_name(capture_a)
    images_b = pngs_by_name(capture_b)
    expected = {f"{frame}.png" for frame in record["screenshots"]}
    if set(images_a) != expected or set(images_b) != expected:
        raise RuntimeError("One or both replay captures are incomplete")

    mismatches = [
        name for name in sorted(expected) if sha256(images_a[name]) != sha256(images_b[name])
    ]
    if mismatches:
        raise RuntimeError(f"Replay screenshot hashes differ: {mismatches}")

    anchor_report: dict[str, object] = {}
    previous: Image.Image | None = None
    for name, frame in ANCHORS.items():
        path = images_a[f"{frame}.png"]
        image = Image.open(path)
        anchor_report[name] = {
            "frame": frame,
            "png_sha256": sha256(path),
            "size": list(image.size),
            "changed_pixels_vs_previous_anchor": (
                None if previous is None else changed_pixels(image, previous)
            ),
        }
        previous = image.copy()

    replay_report = {
        "cold_replay_count": 2,
        "controller_state_count": len(record["records"]),
        "screenshot_anchor_count": len(expected),
        "record_sha256": record_hash_a,
        "all_anchor_hashes_identical": True,
        "mismatch_count": 0,
    }
    return replay_report, anchor_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--record-a",
        type=Path,
        default=Path(
            ".deps/mshvsf_saturn_playrecord/saturn_ryu_first_pass_b/record.json"
        ),
    )
    parser.add_argument(
        "--record-b",
        type=Path,
        default=Path(
            ".deps/mshvsf_saturn_playrecord/saturn_ryu_first_pass_c/record.json"
        ),
    )
    parser.add_argument(
        "--capture-a",
        type=Path,
        default=Path(
            ".deps/mshvsf_saturn_playrecord/out/saturn_ryu_first_pass_b"
        ),
    )
    parser.add_argument(
        "--capture-b",
        type=Path,
        default=Path(
            ".deps/mshvsf_saturn_playrecord/out/saturn_ryu_first_pass_c"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/mshvsf_saturn_first_pass.json"),
    )
    args = parser.parse_args()

    replay, anchors = validate_replays(
        args.record_a.resolve(),
        args.record_b.resolve(),
        args.capture_a.resolve(),
        args.capture_b.resolve(),
    )
    backup_hash = sha256(args.record_a.resolve().parent / "backup.bin.gz")

    report = {
        "title": "Marvel Super Heroes vs. Street Fighter Saturn Ryu first pass",
        "purpose": "Official-port research lane augmenting the AvP Saturn conversion",
        "source": {
            "emulator": "Yaba Sanshiro 2 v1.20.37",
            "disc_product": "T-1238G V1.000 19980903",
            "cartridge": "32 Mbit (4 MB) DRAM",
            "temporary_cue_sha256": "5319d8063444e1a5f8c2949bbca6735627f28df86ac85aca9020a68e5d830305",
            "route": "Two-player Ryu/Ken vs Spider-Man/Captain America; P2 remains neutral after setup",
        },
        "scope": {
            "included": [
                "cold boot and deterministic menu route",
                "idle",
                "forward walk",
                "jump",
                "standing normal attack",
                "collision",
                "visible health response",
                "Spider-Man hit reaction",
                "recovery",
            ],
            "deferred": [
                "Hadouken command acceptance and projectile lifecycle",
                "exact damage and collision-state fields",
                "Saturn RAM, VDP, SCSP, CD, and DMA traces",
            ],
        },
        "input_edges": [
            {"frame": 3600, "action": "P1 right press"},
            {"frame": 3645, "action": "P1 right release"},
            {"frame": 3690, "action": "P1 up press"},
            {"frame": 3698, "action": "P1 up release"},
            {"frame": 3820, "action": "P1 X press"},
            {"frame": 3828, "action": "P1 X release"},
        ],
        "replay": replay,
        "backup_bin_gz_sha256": backup_hash,
        "semantic_anchors": anchors,
        "claims": [
            {
                "claim": "The official Saturn port reaches a controllable Ryu/Ken versus Spider-Man/Captain America match with P2 neutral after setup.",
                "evidence": [
                    "recorded two-port controller states",
                    "idle frame 3540",
                    "two cold replays with 25 identical screenshot hashes",
                ],
                "test": "Cold boot with the same disc, cartridge, backup state, and replay record.",
                "falsification": "A replay reaches different teams, accepts a P2 gameplay input, or changes any screenshot hash.",
                "confidence": "HIGH",
            },
            {
                "claim": "The deterministic first pass contains idle, forward walk, jump, standing normal, collision, a visible HUD health response, Spider-Man hit reaction, and recovery in that order.",
                "evidence": [
                    "input edges at frames 3600-3828",
                    "anchor screenshots at frames 3540, 3620, 3720, 3828, 3840, and 3900",
                    "FIRST ATTACK and Spider-Man reaction visible at frame 3840",
                ],
                "test": "Replay the controller record and require the same event order and anchor hashes.",
                "falsification": "The normal whiffs, P2 moves before impact, the HUD does not respond, or an anchor hash changes.",
                "confidence": "HIGH",
            },
        ],
        "remaining_uncertainty": [
            "The exact Saturn health value, damage amount, collision boxes, hitstop, and actor structures are not mapped.",
            "The first pass deliberately defers Hadouken command acceptance and projectile spawn, travel, ownership, collision, and recovery.",
            "Saturn audio-event routing is not captured.",
            "Visual equivalence does not establish identical CPS-2 and Saturn mechanics or timing.",
        ],
        "rights_boundary": "Replay records, raw screenshots, backup data, and disc media remain ignored private inputs; this tracked report contains hashes and derived observations only.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"Validated {replay['cold_replay_count']} cold replays and "
        f"{replay['screenshot_anchor_count']} identical screenshot anchors."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
