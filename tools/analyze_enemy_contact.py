"""Validate the unfrozen CPS2 enemy-contact probe and emit compact evidence."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAPTURE_ROOT = ROOT / ".deps" / "mame" / "enemy_contact"
ROUTE_ROOT = ROOT / ".deps" / "mame" / "captures"
ACTION_REPORT = ROOT / "data" / "enemy_action_capture.json"
OUTPUT_PATH = ROOT / "data" / "enemy_contact_capture.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_timeline() -> list[dict[str, int]]:
    with (CAPTURE_ROOT / "timeline.tsv").open(
            encoding="utf-8", newline="") as source:
        rows = [
            {key: int(value) for key, value in row.items()}
            for row in csv.DictReader(source, delimiter="\t")
        ]
    if [row["frame"] for row in rows] != list(range(4080, 4501)):
        raise ValueError("enemy-contact timeline must contain every frame 4080-4500")
    return rows


def verify_route_prefix() -> list[dict[str, object]]:
    checks = []
    for frame in (4080, 4164, 4200):
        for kind, old_name, new_name in (
                ("object_ram", f"objram_active_{frame}.tsv",
                 f"objram_active_{frame:05d}.tsv"),
                ("palette", f"palette_{frame}.tsv",
                 f"palette_{frame:05d}.tsv")):
            old_path = ROUTE_ROOT / old_name
            new_path = CAPTURE_ROOT / new_name
            if old_path.read_bytes() != new_path.read_bytes():
                raise ValueError(
                    f"frame {frame}: contact probe diverged from verified {kind}")
            checks.append({"frame": frame, "kind": kind,
                           "sha256": sha256(new_path)})
    return checks


def main() -> None:
    rows = load_timeline()
    by_frame = {row["frame"]: row for row in rows}
    events = []
    prior_health = rows[0]["player_health"]
    for row in rows[1:]:
        health = row["player_health"]
        if health != prior_health:
            events.append({
                "frame": row["frame"],
                "from": prior_health,
                "to": health,
                "tracked_enemy_action": row["enemy_action"],
                "tracked_enemy_animation": row["enemy_animation"],
                "tracked_enemy_x_delta": row["enemy_x"] - row["player_x"],
                "tracked_enemy_floor_delta":
                    (row["enemy_y"] - row["enemy_z"]) -
                    (row["player_y"] - row["player_z"]),
            })
            prior_health = health
    expected_health = [(4243, 30, 22), (4301, 22, 14),
                       (4372, 14, 6), (4433, 6, 0)]
    actual_health = [(event["frame"], event["from"], event["to"])
                     for event in events]
    if actual_health != expected_health:
        raise ValueError(f"unexpected player-health events: {actual_health}")

    attack_start, attack_end = 4253, 4372
    contacts = [event for event in events
                if attack_start <= event["frame"] <= attack_end and
                event["tracked_enemy_action"] == 6144]
    contact_frames = [event["frame"] for event in contacts]
    if contact_frames != [4301, 4372]:
        raise ValueError(f"unexpected tracked attack contacts: {contact_frames}")

    rival_attack_starts: dict[int, int | None] = {}
    prior_rival_action = by_frame[4200]["rival_action"]
    rival_attack_start = 4200 if prior_rival_action == 6144 else None
    for frame in range(4201, attack_end + 1):
        rival_action = by_frame[frame]["rival_action"]
        if rival_action == 6144 and prior_rival_action != 6144:
            rival_attack_start = frame
        elif rival_action != 6144:
            rival_attack_start = None
        if frame in contact_frames:
            rival_attack_starts[frame] = rival_attack_start
        prior_rival_action = rival_action
    rival_phases = [
        None if rival_attack_starts[frame] is None else
        frame - int(rival_attack_starts[frame])
        for frame in contact_frames
    ]
    if by_frame[4301]["rival_action"] == 6144 or rival_phases[1] != 32:
        raise ValueError(
            f"rival actor does not disambiguate tracked contacts: {rival_phases}")

    action_report = json.loads(ACTION_REPORT.read_text(encoding="utf-8"))
    attack_clip = next(clip for clip in action_report["clips"]
                       if clip["name"] == "attack")
    action_by_frame = {sample["frame"]: sample
                       for sample in attack_clip["timeline"]}
    contact_poses = [action_by_frame[frame]["pose"] for frame in contact_frames]
    if contact_poses != [4, 4]:
        raise ValueError(f"tracked contacts did not share attack pose 4: {contact_poses}")

    walk_first, walk_last = by_frame[4214], by_frame[4252]
    walk_delta = walk_last["enemy_x"] - walk_first["enemy_x"]
    if walk_delta != 111:
        raise ValueError(f"unexpected tracked walk displacement: {walk_delta}")

    report = {
        "schema": 1,
        "source": "user-supplied avspu ROM set captured with MAME 0.289",
        "probe": {
            "player_state_modified": False,
            "enemy_state_modified": False,
            "capture_scope": [4080, 4500],
        },
        "route_prefix_checks": verify_route_prefix(),
        "player_health_events": events,
        "tracked_attack": {
            "start_frame": attack_start,
            "end_frame": attack_end,
            "frame_count": attack_end - attack_start + 1,
            "contact_frames": contact_frames,
            "contact_action_offsets":
                [frame - attack_start for frame in contact_frames],
            "contact_pose": 4,
            "contact_animation": contacts[0]["tracked_enemy_animation"],
            "damage_per_contact_native_health_units": 8,
            "maximum_observed_contact_distance_x": max(
                abs(event["tracked_enemy_x_delta"]) for event in contacts),
            "contact_floor_deltas":
                [event["tracked_enemy_floor_delta"] for event in contacts],
            "rival_action_at_contacts":
                [by_frame[frame]["rival_action"] for frame in contact_frames],
            "rival_attack_phase_at_contacts": rival_phases,
            "attribution_note": (
                "At the first health write the rival is not attacking. At the "
                "second it is only 32 frames into its attack, while the tracked "
                "actor is on its repeated contact pose at offset 119."),
        },
        "tracked_walk": {
            "start_frame": 4214,
            "end_frame": 4252,
            "frame_intervals": 38,
            "source_x_displacement": walk_delta,
            "source_x_pixels_per_frame_numerator": walk_delta,
            "source_x_pixels_per_frame_denominator": 38,
        },
    }
    OUTPUT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Validated natural alien contacts at attack offsets 48 and 119; "
          "walk displacement 111/38 CPS2 pixels per frame.")


if __name__ == "__main__":
    main()
