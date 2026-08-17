"""Validate the capture-exact Chrysalis lethal-hit and KO timeline."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_avspu_stage1 as avsp  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
CAPTURE_ROOT = ROOT / ".deps" / "mame" / "boss_ko"
OUTPUT_PATH = ROOT / "data" / "boss_ko_capture.json"
FIRST_SAMPLE = 13420
LAST_SAMPLE = 14260
IMPACT_FRAME = 13491
KO_FIRST = 13492
KO_LAST = 13919
BOSS_PALETTE = 27


def read_words(path: Path) -> list[int]:
    return [
        int(line.split("\t")[1], 16)
        for line in path.read_text(encoding="utf-8").splitlines()[1:]
        if line
    ]


def sample_rows() -> dict[int, dict[str, int]]:
    lines = (CAPTURE_ROOT / "samples.tsv").read_text(
        encoding="utf-8").splitlines()
    expected = (
        "frame\tactive_object_bank\tbank_writes\tactive\taction\tstate\t"
        "substate\tanimation\thealth\tlatched_health\tplayer_health"
    )
    if not lines or lines[0] != expected:
        raise ValueError("boss KO sample metadata header is invalid")
    result: dict[int, dict[str, int]] = {}
    names = expected.split("\t")
    previous_writes = -1
    for line in lines[1:]:
        if not line:
            continue
        values = [int(value) for value in line.split("\t")]
        row = dict(zip(names, values))
        frame = row["frame"]
        if row["active_object_bank"] not in (1, 2):
            raise ValueError(f"frame {frame}: invalid active object bank")
        if row["bank_writes"] < previous_writes:
            raise ValueError(f"frame {frame}: object-bank counter regressed")
        result[frame] = row
        previous_writes = row["bank_writes"]
    if sorted(result) != list(range(FIRST_SAMPLE, LAST_SAMPLE + 1)):
        raise ValueError("boss KO sample ledger is not contiguous")
    return result


def unwrap_axis(values: list[int], sizes: list[int]) -> tuple[list[int], int]:
    """Unwrap a CPS2 10-bit coordinate ring and return a centering shift."""
    best: tuple[int, int, int, list[int]] | None = None
    for base in values:
        unwrapped = [
            base + ((value - base + 512) & 0x3FF) - 512
            for value in values
        ]
        low = min(unwrapped)
        high = max(value + size for value, size in zip(unwrapped, sizes))
        candidate = (high - low, low, high, unwrapped)
        if best is None or candidate[0] < best[0]:
            best = candidate
    assert best is not None
    _, low, high, unwrapped = best
    center = (low + high) // 2
    return unwrapped, (512 - center + 512) % 1024 - 512


def shifted_commands(
        frame: int) -> tuple[list[dict[str, int]], int, int, int, int]:
    entries = avsp.decode_object_entries(read_words(
        CAPTURE_ROOT / f"objram_active_{frame:05d}.tsv"))
    runs = avsp.contiguous_palette_runs(entries, BOSS_PALETTE)
    if len(runs) != 1:
        raise ValueError(
            f"frame {frame}: expected one palette-{BOSS_PALETTE} boss run")
    commands = runs[0]
    raw_x = [(command["screen_x"] + avsp.VISIBLE_LEFT) & 0x3FF
             for command in commands]
    raw_y = [(command["screen_y"] + avsp.VISIBLE_TOP) & 0x3FF
             for command in commands]
    unwrapped_x, shift_x = unwrap_axis(
        raw_x, [command["width"] for command in commands])
    unwrapped_y, shift_y = unwrap_axis(
        raw_y, [command["height"] for command in commands])
    raw_left = min(unwrapped_x)
    raw_right = max(value + command["width"]
                    for value, command in zip(unwrapped_x, commands))
    raw_bottom = max(value + command["height"]
                     for value, command in zip(unwrapped_y, commands))
    raw_pivot_x = (raw_left + raw_right) // 2
    raw_pivot_bottom = raw_bottom + 8
    shifted = []
    for command in commands:
        clone = dict(command)
        clone["screen_x"] = (
            (command["screen_x"] + avsp.VISIBLE_LEFT + shift_x) & 0x3FF
        ) - avsp.VISIBLE_LEFT
        clone["screen_y"] = (
            (command["screen_y"] + avsp.VISIBLE_TOP + shift_y) & 0x3FF
        ) - avsp.VISIBLE_TOP
        shifted.append(clone)
    return (shifted, shift_x, shift_y,
            raw_pivot_x, raw_pivot_bottom)


def main() -> int:
    rows = sample_rows()
    before = rows[IMPACT_FRAME - 1]
    impact = rows[IMPACT_FRAME]
    start = rows[KO_FIRST]
    settled = rows[KO_LAST]
    if (before["health"], impact["health"], start["health"]) != (3, 0, 0):
        raise ValueError("natural lethal Chrysalis health transition changed")
    if (impact["latched_health"], start["latched_health"]) != (3, 0):
        raise ValueError("lethal Chrysalis latched-health transition changed")
    if (start["action"], rows[13531]["action"], rows[13534]["action"]) != (
            2, 516, 512):
        raise ValueError("Chrysalis KO action boundary changed")
    if settled["animation"] != 56456:
        raise ValueError("Chrysalis grounded-corpse boundary changed")

    timeline = []
    pose_ids: dict[str, int] = {}
    palette_hashes: set[str] = set()
    previous_pivot: tuple[int, int] | None = None
    origin_pivot: tuple[int, int] | None = None
    for frame in range(KO_FIRST, KO_LAST + 1):
        commands, shift_x, shift_y, raw_pivot_x, raw_pivot_bottom = (
            shifted_commands(frame))
        if previous_pivot is not None:
            raw_pivot_x = previous_pivot[0] + (
                (raw_pivot_x - previous_pivot[0] + 512) & 0x3FF) - 512
            raw_pivot_bottom = previous_pivot[1] + (
                (raw_pivot_bottom - previous_pivot[1] + 512) & 0x3FF) - 512
        previous_pivot = (raw_pivot_x, raw_pivot_bottom)
        if origin_pivot is None:
            origin_pivot = previous_pivot
        bounds = avsp.command_bounds(commands)
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        if width > 288 or height > 192:
            raise ValueError(
                f"frame {frame}: KO assembly exceeds the 288x192 canvas")
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
            "active_object_bank": rows[frame]["active_object_bank"],
            "object_offsets": [command["offset"] for command in commands],
            "object_shift_x": shift_x,
            "object_shift_y": shift_y,
            "pivot_x": pivot_x,
            "pivot_bottom": pivot_bottom,
            "screen_offset_x": raw_pivot_x - origin_pivot[0],
            "screen_offset_y": raw_pivot_bottom - origin_pivot[1],
            "bounds": list(bounds),
            "actor_active": rows[frame]["active"],
            "actor_action": rows[frame]["action"],
            "actor_state": rows[frame]["state"],
            "actor_substate": rows[frame]["substate"],
            "actor_animation": rows[frame]["animation"],
            "health": rows[frame]["health"],
        })
    if len(palette_hashes) != 1:
        raise ValueError("Chrysalis palette changed during the KO clip")

    runs: list[dict[str, int]] = []
    for sample in timeline:
        pose = int(sample["pose"])
        if runs and runs[-1]["pose"] == pose:
            runs[-1]["frames"] += 1
        else:
            runs.append({"pose": pose, "frames": 1})
    report = {
        "schema": 1,
        "source": (
            "deterministic avspu frame-12660 Chrysalis state with prior "
            "health reduced to one natural melee hit"),
        "capture_first_frame": FIRST_SAMPLE,
        "capture_last_frame": LAST_SAMPLE,
        "lethal_impact_frame": IMPACT_FRAME,
        "health_before": before["health"],
        "health_after": impact["health"],
        "damage": before["health"] - impact["health"],
        "ko": {
            "name": "ko",
            "first_frame": KO_FIRST,
            "last_frame": KO_LAST,
            "frame_count": KO_LAST - KO_FIRST + 1,
            "unique_object_poses": len(pose_ids),
            "origin_pivot": list(origin_pivot),
            "pose_runs": runs,
            "palette_sha256": next(iter(palette_hashes)),
            "timeline": timeline,
        },
    }
    OUTPUT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"Validated Chrysalis KO: {report['ko']['frame_count']} frames, "
        f"{len(pose_ids)} exact object poses, {len(runs)} pose runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
