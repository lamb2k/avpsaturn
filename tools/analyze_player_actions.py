#!/usr/bin/env python3
"""Validate deterministic, isolated CPS2 Predator Warrior action captures."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = ROOT / "tools"
CAPTURE_ROOT = ROOT / ".deps" / "mame" / "player_actions"
OUTPUT_ROOT = ROOT / "build" / "rom_extract"
HUD_OUTPUT_PATH = ROOT / "data" / "player_hud_capture.json"
ACTIONS = ("idle", "walk", "gun", "melee", "jump", "dash", "special")
FIRST_FRAME = 2480
LAST_FRAME = 2608
INPUT_FRAME = 2525
WALK_REPEAT_VALIDATION_FRAMES = 24

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
    if lines[0] != (
            "frame\taction\tactive_object_bank\tbank_writes\tplayer_health"):
        raise ValueError(f"{action}: unexpected sample metadata header")
    samples: dict[int, int] = {}
    for line in lines[1:]:
        if not line:
            continue
        frame, recorded_action, bank, _, health = line.split("\t")
        if recorded_action != action:
            raise ValueError(
                f"{action}: metadata contains action {recorded_action!r}")
        samples[int(frame)] = int(bank)
        if not 0 <= int(health) <= 0xFFFF:
            raise ValueError(f"{action}: invalid player health")
    expected = list(range(FIRST_FRAME, LAST_FRAME + 1))
    if sorted(samples) != expected:
        raise ValueError(
            f"{action}: capture must contain every frame {FIRST_FRAME}-{LAST_FRAME}")
    if any(bank not in (1, 2) for bank in samples.values()):
        raise ValueError(f"{action}: invalid active object bank")
    return samples


def verify_hud_state() -> dict[str, object]:
    def health_events_for(action: str) -> list[list[int]]:
        rows = []
        for line in (CAPTURE_ROOT / action / "hud_state.tsv").read_text(
                encoding="utf-8").splitlines()[1:]:
            if line:
                frame, health = line.split("\t")
                rows.append((int(frame), int(health)))
        events = []
        prior = rows[0][1]
        for frame, health in rows[1:]:
            if health != prior:
                events.append([frame, prior, health])
                prior = health
        return events

    health_events = health_events_for("gun")
    if health_events != [[2072, 0, 101], [2426, 101, 91],
                         [2487, 91, 81]]:
        raise ValueError(f"unexpected isolated-route health events: {health_events}")

    def gauge_width(frame: int) -> int:
        image = Image.open(CAPTURE_ROOT / "gun" /
                           f"gun_{frame:05d}.png").convert("RGB")
        return sum(image.getpixel((x, 218)) == (187, 255, 119)
                   for x in range(48, 112))

    if gauge_width(2520) != 64 or gauge_width(2528) != 24:
        raise ValueError("isolated gun did not consume 40 of 64 HUD pixels")
    recharge = [[frame, gauge_width(frame)]
                for frame in range(2540, 2607, 3)]
    if [width for _, width in recharge] != list(range(25, 48)):
        raise ValueError("weapon HUD did not recharge one pixel every 3 frames")
    special_events = health_events_for("special")
    if special_events[-1] != [2606, 81, 75]:
        raise ValueError(
            f"unexpected emergency-attack health cost: {special_events[-1]}")
    return {
        "maximum_observed_player_health": 101,
        "health_events": health_events,
        "weapon_meter_source_range": [48, 111],
        "weapon_meter_source_rows": [218, 221],
        "weapon_meter_capacity": 64,
        "isolated_shot_frame": 2525,
        "meter_drop_visible_frame": 2528,
        "meter_after_shot": 24,
        "meter_cost": 40,
        "recharge_samples": recharge,
        "recharge_cadence_frames": 3,
        "emergency_attack_health_event": special_events[-1],
        "emergency_attack_health_cost": 6,
    }


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
        loop_frame = None
        clip_timeline: list[dict[str, object]] = []
        clip_start_frame = INPUT_FRAME
        if action == "walk":
            clip_start_frame = changed_frames[0]
            first_walk_pose = str(timeline_by_frame[clip_start_frame]["pose"])
            for frame in range(clip_start_frame + 1, LAST_FRAME - 3):
                if all(str(timeline_by_frame[candidate]["pose"]) == first_walk_pose
                       for candidate in range(frame, frame + 4)):
                    loop_frame = frame
                    break
            if loop_frame is None:
                raise ValueError("walk: no complete repeating locomotion cycle")
            if any(
                    str(timeline_by_frame[clip_start_frame + offset]["pose"]) !=
                    str(timeline_by_frame[loop_frame + offset]["pose"])
                    for offset in range(WALK_REPEAT_VALIDATION_FRAMES)):
                raise ValueError("walk: repeated cycle prefix no longer matches")
            clip_timeline = [
                timeline_by_frame[frame]
                for frame in range(clip_start_frame, loop_frame)
            ]
            walk_runs = pose_runs(clip_timeline)
            if len(walk_runs) < 2 or any(
                    int(run["samples"]) != 4 for run in walk_runs):
                raise ValueError("walk: expected a four-frame CPS2 pose cadence")
        elif action != "idle":
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
            "clip_start_frame": clip_start_frame if action != "idle" else None,
            "accepted": action == "idle" or bool(changed_frames),
            "first_pose_difference": changed_frames[0] if changed_frames else None,
            "last_pose_difference": changed_frames[-1] if changed_frames else None,
            "return_to_idle_frame": return_frame,
            "loop_frame": loop_frame,
            "clip_frame_count": len(clip_timeline),
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
    hud_state = verify_hud_state()
    HUD_OUTPUT_PATH.write_text(json.dumps({
        "schema": 1,
        "source": "user-supplied avspu ROM set captured with MAME 0.289",
        "character": "Predator Warrior",
        "probe": {
            "cold_boot_state_traversal": True,
            "isolated_action": "gun",
            "player_memory_patched": False,
            "enemy_memory_patched": False,
        },
        **hud_state,
    }, indent=2) + "\n", encoding="utf-8")
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
        "hud_state": hud_state,
        "actions": results,
    }, indent=2) + "\n", encoding="utf-8")

    for result in results:
        print(
            f"{result['action']}: accepted={result['accepted']} "
            f"poses={result['unique_pose_count']} "
            f"difference={result['first_pose_difference']}-"
            f"{result['last_pose_difference']}")
    print(f"Wrote {report_path}")
    print(f"Wrote {HUD_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
