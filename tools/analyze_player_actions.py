#!/usr/bin/env python3
"""Validate deterministic, isolated CPS2 Predator Warrior action captures."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = ROOT / "tools"
CAPTURE_ROOT = ROOT / ".deps" / "mame" / "player_actions"
OUTPUT_ROOT = ROOT / "build" / "rom_extract"
ACTIONS = ("idle", "gun", "melee", "jump", "dash", "special")
FIRST_FRAME = 2480
LAST_FRAME = 2608
INPUT_FRAME = 2525

sys.path.insert(0, str(TOOLS_ROOT))
import extract_avspu_stage1 as avsp  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_words(path: Path) -> list[int]:
    lines = path.read_text(encoding="utf-8").splitlines()[1:]
    return [int(line.split("\t")[1], 16) for line in lines if line]


def load_samples(action: str) -> dict[int, int]:
    path = CAPTURE_ROOT / action / "samples.tsv"
    lines = path.read_text(encoding="utf-8").splitlines()
    if lines[0] != "frame\taction\tactive_object_bank\tbank_writes":
        raise ValueError(f"{action}: unexpected sample metadata header")
    samples: dict[int, int] = {}
    for line in lines[1:]:
        if not line:
            continue
        frame, recorded_action, bank, _ = line.split("\t")
        if recorded_action != action:
            raise ValueError(
                f"{action}: metadata contains action {recorded_action!r}")
        samples[int(frame)] = int(bank)
    expected = list(range(FIRST_FRAME, LAST_FRAME + 1))
    if sorted(samples) != expected:
        raise ValueError(
            f"{action}: capture must contain every frame {FIRST_FRAME}-{LAST_FRAME}")
    if any(bank not in (1, 2) for bank in samples.values()):
        raise ValueError(f"{action}: invalid active object bank")
    return samples


def player_sample(action: str, frame: int, bank: int) -> dict[str, object]:
    action_root = CAPTURE_ROOT / action
    object_path = action_root / f"objram_active_{frame:05d}.tsv"
    screenshot_path = action_root / f"{action}_{frame:05d}.png"
    palette_path = action_root / f"palette_{frame:05d}.tsv"
    entries = avsp.decode_object_entries(load_words(object_path))
    commands = avsp.isolated_player_animation_commands(entries)
    primary_commands = [entry for entry in commands if entry["colour"] == 0]
    if not primary_commands:
        raise ValueError(f"{action} frame {frame}: missing Predator primary layer")
    primary = max(primary_commands,
                  key=lambda entry: entry["width"] * entry["height"])
    pivot_x = primary["screen_x"] + primary["width"] // 2
    pivot_y = primary["screen_y"] + primary["height"]
    normalized = [
        {
            "tile_code": entry["tile_code"],
            "attribute": entry["attribute"],
            "palette": entry["colour"],
            "priority": entry["priority"],
            "x": entry["screen_x"] - pivot_x,
            "y": entry["screen_y"] - pivot_y,
            "width": entry["width"],
            "height": entry["height"],
        }
        for entry in sorted(commands, key=lambda item: item["offset"], reverse=True)
    ]
    signature = json.dumps(normalized, separators=(",", ":"), sort_keys=True)
    pose_id = hashlib.sha256(signature.encode("ascii")).hexdigest()[:12]
    return {
        "frame": frame,
        "active_object_bank": bank,
        "pose": pose_id,
        "pivot": [pivot_x, pivot_y],
        "command_offsets": sorted(entry["offset"] for entry in commands),
        "command_count": len(commands),
        "palettes": sorted({entry["colour"] for entry in commands}),
        "object_ram_sha256": sha256(object_path),
        "palette_sha256": sha256(palette_path),
        "screenshot_sha256": sha256(screenshot_path),
    }


def pose_runs(timeline: list[dict[str, object]]) -> list[dict[str, object]]:
    runs: list[dict[str, object]] = []
    for sample in timeline:
        if runs and runs[-1]["pose"] == sample["pose"]:
            runs[-1]["end_frame"] = sample["frame"]
            runs[-1]["samples"] = int(runs[-1]["samples"]) + 1
        else:
            runs.append({
                "start_frame": sample["frame"],
                "end_frame": sample["frame"],
                "samples": 1,
                "pose": sample["pose"],
            })
    return runs


def main() -> None:
    for action in ACTIONS:
        if not (CAPTURE_ROOT / action).is_dir():
            raise ValueError(f"missing isolated action capture: {action}")

    baseline_frame = INPUT_FRAME - 1
    baseline_object_hashes = {
        action: sha256(CAPTURE_ROOT / action /
                       f"objram_active_{baseline_frame:05d}.tsv")
        for action in ACTIONS
    }
    baseline_palette_hashes = {
        action: sha256(CAPTURE_ROOT / action /
                       f"palette_{baseline_frame:05d}.tsv")
        for action in ACTIONS
    }
    if len(set(baseline_object_hashes.values())) != 1:
        raise ValueError("pre-input object RAM differs between action probes")
    if len(set(baseline_palette_hashes.values())) != 1:
        raise ValueError("pre-input palette differs between action probes")

    timelines: dict[str, list[dict[str, object]]] = {}
    results = []
    for action in ACTIONS:
        samples = load_samples(action)
        timeline = [player_sample(action, frame, samples[frame])
                    for frame in range(FIRST_FRAME, LAST_FRAME + 1)]
        timelines[action] = timeline

    idle_poses = {
        int(sample["frame"]): str(sample["pose"])
        for sample in timelines["idle"]
    }
    for action in ACTIONS:
        timeline = timelines[action]
        timeline_by_frame = {
            int(sample["frame"]): sample for sample in timeline
        }
        changed_frames = [
            int(sample["frame"])
            for sample in timeline
            if int(sample["frame"]) >= INPUT_FRAME and
            str(sample["pose"]) != idle_poses[int(sample["frame"])]
        ]
        if action != "idle" and not changed_frames:
            raise ValueError(f"{action}: input did not produce a distinct player pose")
        return_frame = None
        clip_timeline: list[dict[str, object]] = []
        if action != "idle":
            baseline_pose = str(timeline_by_frame[INPUT_FRAME]["pose"])
            for frame in range(changed_frames[0] + 1, LAST_FRAME - 1):
                if all(str(timeline_by_frame[candidate]["pose"]) == baseline_pose
                       for candidate in range(frame, frame + 3)):
                    return_frame = frame
                    break
            if return_frame is None:
                raise ValueError(f"{action}: action did not return to idle in capture window")
            clip_timeline = [
                timeline_by_frame[frame]
                for frame in range(INPUT_FRAME, return_frame)
            ]
        action_result = {
            "action": action,
            "input_frame": INPUT_FRAME if action != "idle" else None,
            "accepted": action == "idle" or bool(changed_frames),
            "first_pose_difference": changed_frames[0] if changed_frames else None,
            "last_pose_difference": changed_frames[-1] if changed_frames else None,
            "return_to_idle_frame": return_frame,
            "clip_frame_count": (return_frame - INPUT_FRAME
                                 if return_frame is not None else 0),
            "clip_runs": pose_runs(clip_timeline),
            "unique_pose_count": len({str(sample["pose"]) for sample in timeline}),
            "maximum_command_count": max(int(sample["command_count"])
                                         for sample in timeline),
            "palettes": sorted({
                int(palette)
                for sample in timeline
                for palette in sample["palettes"]
            }),
            "runs": pose_runs(timeline),
            "timeline": timeline,
        }
        results.append(action_result)

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT_ROOT / "player_action_probe.json"
    report_path.write_text(json.dumps({
        "source_set": "avspu",
        "character": "Predator Warrior",
        "capture_frames": [FIRST_FRAME, LAST_FRAME],
        "input_frame": INPUT_FRAME,
        "sample_stride_frames": 1,
        "cold_boot_state_traversal": True,
        "pre_input_baseline_frame": baseline_frame,
        "pre_input_object_ram_sha256": next(iter(baseline_object_hashes.values())),
        "pre_input_palette_sha256": next(iter(baseline_palette_hashes.values())),
        "actions": results,
    }, indent=2) + "\n", encoding="utf-8")

    for result in results:
        print(
            f"{result['action']}: accepted={result['accepted']} "
            f"poses={result['unique_pose_count']} "
            f"difference={result['first_pose_difference']}-"
            f"{result['last_pose_difference']}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
