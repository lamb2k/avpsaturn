"""Validate capture-exact Chrysalis movement and attack timelines.

The boss occupies the native actor slot at FF A3C0. Palette 27 uniquely owns
the ordinary Chrysalis assembly in this capture, so each source frame can be
bound to its actor state without guessing from a whole-screen screenshot.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_avspu_stage1 as avsp  # noqa: E402


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CAPTURE_ROOT = PROJECT_ROOT / ".deps" / "mame" / "boss_actions"
OUTPUT_PATH = PROJECT_ROOT / "data" / "boss_action_capture.json"
WORKRAM_START = 0xFF8000
ACTOR_ADDRESS = 0xFFA3C0
ACTOR_OFFSET = ACTOR_ADDRESS - WORKRAM_START
FIRST_FRAME = 12661
LAST_FRAME = 13560
BOSS_PALETTE = 27
CLIPS = (
    ("leap", 12661, 12704),
    ("walk", 12885, 12990),
    ("attack", 12992, 13180),
)


def read_words(path: Path) -> list[int]:
    return [
        int(line.split("\t")[1], 16)
        for line in path.read_text(encoding="utf-8").splitlines()[1:]
        if line
    ]


def actor_state(frame: int) -> dict[str, int]:
    data = (CAPTURE_ROOT / f"workram_{frame:05d}.bin").read_bytes()
    if len(data) != 0x8000:
        raise ValueError(f"frame {frame}: expected a 32 KiB work-RAM capture")
    slot = data[ACTOR_OFFSET:ACTOR_OFFSET + 0xC0]

    def word(offset: int) -> int:
        return int.from_bytes(slot[offset:offset + 2], "big")

    return {
        "active": slot[0],
        "actor_id": slot[2],
        "action": word(0x06),
        "state": word(0x0C),
        "substate": word(0x0E),
        "world_x": word(0x10),
        "world_y": word(0x14),
        "world_z": word(0x18),
        "animation": word(0x1E),
        "animation_timer": word(0x2A),
        "health": int.from_bytes(slot[0x40:0x42], "big", signed=True),
        "latched_health": int.from_bytes(
            slot[0x42:0x44], "big", signed=True),
        "maximum_health_field": word(0x44),
    }


def sample_metadata() -> tuple[dict[int, int], list[dict[str, int]]]:
    result: dict[int, int] = {}
    contacts: list[dict[str, int]] = []
    lines = (CAPTURE_ROOT / "samples.tsv").read_text(
        encoding="utf-8").splitlines()
    if not lines or lines[0] != (
            "frame\tactive_object_bank\tbank_writes\tprobe_phase\tplayer_health"):
        raise ValueError("boss sample metadata header is invalid")
    previous_writes = -1
    for line in lines[1:]:
        if not line:
            continue
        frame_text, bank_text, writes_text, _, health_text = line.split("\t")
        frame = int(frame_text)
        bank = int(bank_text)
        writes = int(writes_text)
        if bank not in (1, 2) or writes < previous_writes:
            raise ValueError(f"frame {frame}: invalid object-bank metadata")
        result[frame] = bank
        health = int(health_text)
        # The save state begins with 65 health. It is restored after this first
        # sample; subsequent deviations from 101 are natural boss contacts.
        if frame > FIRST_FRAME and health != 101:
            contacts.append({"frame": frame, "health": health,
                             "damage": 101 - health})
        previous_writes = writes
    if sorted(result) != list(range(FIRST_FRAME, LAST_FRAME + 1)):
        raise ValueError("boss sample ledger is not a contiguous 900-frame run")
    return result, contacts


def shifted_boss_commands(frame: int) -> tuple[list[dict[str, int]], int]:
    entries = avsp.decode_object_entries(read_words(
        CAPTURE_ROOT / f"objram_active_{frame:05d}.tsv"))
    runs = avsp.contiguous_palette_runs(entries, BOSS_PALETTE)
    if len(runs) != 1:
        raise ValueError(
            f"frame {frame}: expected one palette-{BOSS_PALETTE} boss run")
    commands = runs[0]

    # CPS2 X positions wrap at 1024. Shift the complete assembly to the middle
    # of that ring before hashing or rendering so a pose crossing X=0 remains
    # one contiguous boss rather than a false 1024-pixel-wide object.
    best: tuple[int, int, int, list[int]] | None = None
    raw_positions = [(command["screen_x"] + avsp.VISIBLE_LEFT) & 0x3FF
                     for command in commands]
    for base in raw_positions:
        unwrapped = [
            base + ((position - base + 512) & 0x3FF) - 512
            for position in raw_positions
        ]
        left = min(unwrapped)
        right = max(value + command["width"]
                    for value, command in zip(unwrapped, commands))
        candidate = (right - left, left, right, unwrapped)
        if best is None or candidate[0] < best[0]:
            best = candidate
    assert best is not None
    _, left, right, _ = best
    circular_center = (left + right) // 2
    shift = (512 - circular_center + 512) % 1024 - 512

    shifted = []
    for command in commands:
        clone = dict(command)
        raw_x = (command["screen_x"] + avsp.VISIBLE_LEFT + shift) & 0x3FF
        clone["screen_x"] = raw_x - avsp.VISIBLE_LEFT
        shifted.append(clone)
    return shifted, shift


def analyze_clip(name: str, first: int, last: int,
                 banks: dict[int, int]) -> dict[str, object]:
    timeline = []
    pose_ids: dict[str, int] = {}
    palette_hashes: set[str] = set()

    for frame in range(first, last + 1):
        state = actor_state(frame)
        if state["active"] != 1 or state["actor_id"] != 6:
            raise ValueError(f"frame {frame}: Chrysalis actor slot is not active")
        commands, shift = shifted_boss_commands(frame)
        bounds = avsp.command_bounds(commands)
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        # The close swipe reaches 272 pixels; a 288-pixel, 8-pixel-aligned
        # Saturn cel preserves it without clipping and matches the alien pool.
        if width > 288 or height > 192:
            raise ValueError(
                f"frame {frame}: boss assembly exceeds the 288x192 canvas")
        pivot_x = (bounds[0] + bounds[2]) // 2
        pivot_bottom = bounds[3] + 8
        signature = tuple(
            (command["screen_x"] - pivot_x,
             command["screen_y"] - pivot_bottom,
             command["tile_code"], command["attribute"],
             command["width"], command["height"])
            for command in commands)
        digest = hashlib.sha256(repr(signature).encode("ascii")).hexdigest()
        pose = pose_ids.setdefault(digest, len(pose_ids))
        palette = avsp.load_palette_path(
            CAPTURE_ROOT / f"palette_{frame:05d}.tsv")
        palette_bytes = bytes(
            component
            for pen in palette[BOSS_PALETTE * 16:BOSS_PALETTE * 16 + 15]
            for component in pen[:3])
        palette_hashes.add(hashlib.sha256(palette_bytes).hexdigest())
        timeline.append({
            "frame": frame,
            "pose": pose,
            "active_object_bank": banks[frame],
            "object_offsets": [command["offset"] for command in commands],
            "object_shift_x": shift,
            "pivot_x": pivot_x,
            "pivot_bottom": pivot_bottom,
            "bounds": list(bounds),
            "actor_action": state["action"],
            "actor_state": state["state"],
            "actor_substate": state["substate"],
            "actor_animation": state["animation"],
            "actor_x": state["world_x"],
            "actor_y": state["world_y"],
            "actor_z": state["world_z"],
            "health": state["health"],
        })

    if len(palette_hashes) != 1:
        raise ValueError(f"{name}: palette 27 changed during the exact clip")
    runs: list[dict[str, int]] = []
    for sample in timeline:
        pose = int(sample["pose"])
        if runs and runs[-1]["pose"] == pose:
            runs[-1]["frames"] += 1
        else:
            runs.append({"pose": pose, "frames": 1})
    return {
        "name": name,
        "first_frame": first,
        "last_frame": last,
        "frame_count": last - first + 1,
        "unique_object_poses": len(pose_ids),
        "pose_runs": runs,
        "palette_sha256": next(iter(palette_hashes)),
        "timeline": timeline,
    }


def main() -> int:
    banks, contacts = sample_metadata()
    clips = [analyze_clip(name, first, last, banks)
             for name, first, last in CLIPS]
    attack_first = CLIPS[2][1]
    attack_last = CLIPS[2][2]
    attack_contacts = [contact for contact in contacts
                       if attack_first <= contact["frame"] <= attack_last]
    expected_contacts = [
        {"frame": 13013, "health": 91, "damage": 10},
        {"frame": 13047, "health": 91, "damage": 10},
        {"frame": 13089, "health": 85, "damage": 16},
    ]
    if attack_contacts != expected_contacts:
        raise ValueError(
            f"clean Chrysalis attack contacts changed: {attack_contacts}")
    initial = actor_state(FIRST_FRAME)
    report = {
        "schema": 1,
        "source": "deterministic avspu frame-12660 Chrysalis save state",
        "capture_first_frame": FIRST_FRAME,
        "capture_last_frame": LAST_FRAME,
        "capture_frames": LAST_FRAME - FIRST_FRAME + 1,
        "actor": {
            "actor_address": hex(ACTOR_ADDRESS),
            "actor_id": initial["actor_id"],
            "initial_health": initial["health"],
            "maximum_health_field": initial["maximum_health_field"],
            "cps2_palette": BOSS_PALETTE,
        },
        "player_contacts": contacts,
        "attack_contract": {
            "first_frame": attack_first,
            "last_frame": attack_last,
            "total_frames": attack_last - attack_first + 1,
            "contact_offsets": [contact["frame"] - attack_first
                                for contact in attack_contacts],
            "contact_damage": [contact["damage"]
                               for contact in attack_contacts],
        },
        "clips": clips,
    }
    OUTPUT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for clip in clips:
        print(f"{clip['name']}: {clip['frame_count']} frames, "
              f"{clip['unique_object_poses']} exact object poses")
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
