#!/usr/bin/env python3
"""Validate the natural CPS2 Predator hit and KO timeline."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = ROOT / "tools"
CAPTURE_ROOT = ROOT / ".deps" / "mame" / "player_actions"
DAMAGE_ROOT = CAPTURE_ROOT / "damage"
OUTPUT_ROOT = ROOT / "build" / "rom_extract"
FIRST_FRAME = 2480
LAST_FRAME = 3400
ANALYSIS_LAST_FRAME = 2780
DETERMINISTIC_IDLE_LAST_FRAME = 2608
HIT_RANGES = ((2554, 2579), (2618, 2643))
KO_RANGE = (2680, 2776)
RESPAWN_FRAME = 2776

sys.path.insert(0, str(TOOLS_ROOT))
from analyze_player_actions import player_sample, pose_runs, sha256  # noqa: E402


def load_samples() -> dict[int, int]:
    path = DAMAGE_ROOT / "samples.tsv"
    lines = path.read_text(encoding="utf-8").splitlines()
    if lines[0] != "frame\taction\tactive_object_bank\tbank_writes":
        raise ValueError("damage: unexpected sample metadata header")
    samples: dict[int, int] = {}
    for line in lines[1:]:
        if not line:
            continue
        frame, action, bank, _ = line.split("\t")
        if action != "damage":
            raise ValueError(f"damage metadata contains action {action!r}")
        samples[int(frame)] = int(bank)
    if sorted(samples) != list(range(FIRST_FRAME, LAST_FRAME + 1)):
        raise ValueError(
            f"damage capture must contain every frame {FIRST_FRAME}-{LAST_FRAME}")
    if any(bank not in (1, 2) for bank in samples.values()):
        raise ValueError("damage capture contains an invalid active object bank")
    return samples


def verify_idle_prefix() -> None:
    idle_root = CAPTURE_ROOT / "idle"
    for frame in range(FIRST_FRAME, DETERMINISTIC_IDLE_LAST_FRAME + 1):
        pairs = (
            (idle_root / f"objram_active_{frame:05d}.tsv",
             DAMAGE_ROOT / f"objram_active_{frame:05d}.tsv"),
            (idle_root / f"palette_{frame:05d}.tsv",
             DAMAGE_ROOT / f"palette_{frame:05d}.tsv"),
            (idle_root / f"idle_{frame:05d}.png",
             DAMAGE_ROOT / f"damage_{frame:05d}.png"),
        )
        for idle_path, damage_path in pairs:
            if sha256(idle_path) != sha256(damage_path):
                raise ValueError(
                    f"damage frame {frame}: no-input prefix diverges from idle")


def clip_report(name: str, timeline_by_frame: dict[int, dict[str, object]],
                start: int, end: int) -> dict[str, object]:
    timeline = [timeline_by_frame[frame] for frame in range(start, end)]
    origin_x, origin_y = timeline[0]["pivot"]
    return {
        "name": name,
        "start_frame": start,
        "end_frame_exclusive": end,
        "frame_count": end - start,
        "origin_pivot": [origin_x, origin_y],
        "runs": pose_runs(timeline),
        "frame_offsets": [
            [int(sample["pivot"][0]) - int(origin_x),
             int(sample["pivot"][1]) - int(origin_y)]
            for sample in timeline
        ],
        "unique_pose_count": len({str(sample["pose"]) for sample in timeline}),
        "source_screenshot_sha256": {
            str(start): hashlib.sha256(
                (DAMAGE_ROOT / f"damage_{start:05d}.png").read_bytes()).hexdigest(),
            str(end - 1): hashlib.sha256(
                (DAMAGE_ROOT / f"damage_{end - 1:05d}.png").read_bytes()).hexdigest(),
        },
    }


def main() -> None:
    samples = load_samples()
    verify_idle_prefix()
    timeline = [
        player_sample("damage", frame, samples[frame])
        for frame in range(FIRST_FRAME, ANALYSIS_LAST_FRAME + 1)
    ]
    timeline_by_frame = {int(sample["frame"]): sample for sample in timeline}

    baseline_pose = str(timeline_by_frame[2514]["pose"])
    first_hit = clip_report("hit", timeline_by_frame, *HIT_RANGES[0])
    repeated_hit = clip_report("hit_repeat", timeline_by_frame, *HIT_RANGES[1])
    ko = clip_report("ko", timeline_by_frame, *KO_RANGE)
    if first_hit["frame_count"] != 25 or repeated_hit["frame_count"] != 25:
        raise ValueError("natural hit clips no longer span 25 frames")
    if str(timeline_by_frame[HIT_RANGES[0][1]]["pose"]) != baseline_pose:
        raise ValueError("first natural hit does not return to baseline")
    if str(timeline_by_frame[HIT_RANGES[1][1]]["pose"]) != baseline_pose:
        raise ValueError("repeated natural hit does not return to baseline")
    if ko["frame_count"] != 96:
        raise ValueError("natural KO no longer reaches respawn in 96 frames")
    ko_offsets = ko["frame_offsets"]
    if min(int(offset[1]) for offset in ko_offsets) > -80:
        raise ValueError("natural KO does not contain the observed airborne launch")
    respawn = timeline_by_frame[RESPAWN_FRAME]
    if int(respawn["pivot"][1]) > 140:
        raise ValueError("natural KO does not return to a standing respawn pose")

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT_ROOT / "player_damage_probe.json"
    report_path.write_text(json.dumps({
        "source_set": "avspu",
        "character": "Predator Warrior",
        "capture_frames": [FIRST_FRAME, LAST_FRAME],
        "analysis_frames": [FIRST_FRAME, ANALYSIS_LAST_FRAME],
        "cold_boot_state_traversal": True,
        "idle_prefix_verified_through": DETERMINISTIC_IDLE_LAST_FRAME,
        "baseline_pose": baseline_pose,
        "clips": [first_hit, ko],
        "repeated_hit_validation": repeated_hit,
        "respawn_frame": RESPAWN_FRAME,
        "respawn_sample": respawn,
        "timeline": timeline,
    }, indent=2) + "\n", encoding="utf-8")
    print(
        f"hit: {first_hit['frame_count']} frames, "
        f"{first_hit['unique_pose_count']} poses")
    print(
        f"ko: {ko['frame_count']} frames, {ko['unique_pose_count']} poses, "
        f"respawn={RESPAWN_FRAME}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
