#!/usr/bin/env python3
"""Focused host contract for the isolated PlayerSalvageBench."""

from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from tools.extract_avspu_stage1 import (  # noqa: E402
    player_canvas_bounds,
    player_presentation_pivot,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def step(state: dict[str, int], sample: dict[str, int], walk_duration: int = 19) -> dict[str, int]:
    """Mirror only the fixed-camera player presentation adapter."""
    result = dict(state)
    moving = 0
    if sample["left"] and not sample["right"]:
        result["x"] -= 2
        result["facing"] = -1
        moving = 1
    elif sample["right"] and not sample["left"]:
        result["x"] += 2
        result["facing"] = 1
        moving = 1
    if sample["up"] and not sample["down"]:
        result["lane"] -= 1
        moving = 1
    elif sample["down"] and not sample["up"]:
        result["lane"] += 1
        moving = 1
    result["x"] = min(304, max(48, result["x"]))
    result["lane"] = min(218, max(138, result["lane"]))
    result["action"] = moving
    if moving:
        result["locomotion"] += 1
        result["pose_phase"] = result["locomotion"] % walk_duration
    else:
        result["pose_phase"] = -1
    return result


def replay(walk_duration: int = 19) -> list[dict[str, int]]:
    state = {"x": 192, "lane": 178, "facing": 1, "action": 0,
             "locomotion": 0, "pose_phase": -1}
    sequence = ([{"left": 0, "right": 1, "up": 0, "down": 0}] * 6 +
                [{"left": 0, "right": 0, "up": 0, "down": 1}] * 3 +
                [{"left": 1, "right": 0, "up": 1, "down": 0}] * 4 +
                [{"left": 0, "right": 0, "up": 0, "down": 0}] * 2)
    result = []
    for sample in sequence:
        state = step(state, sample, walk_duration)
        result.append(state)
    return result


def visibility_contract(negative: bool) -> None:
    # Exact selected-command geometry from isolated idle source frame 2525.
    commands = [
        {"colour": 0, "screen_x": 175, "screen_y": 84, "width": 80, "height": 48},
        {"colour": 0, "screen_x": 191, "screen_y": 132, "width": 64, "height": 48},
        {"colour": 0, "screen_x": 200, "screen_y": 96, "width": 32, "height": 32},
        {"colour": 7, "screen_x": 226, "screen_y": 146, "width": 16, "height": 16},
        {"colour": 7, "screen_x": 210, "screen_y": 114, "width": 32, "height": 32},
        {"colour": 7, "screen_x": 196, "screen_y": 86, "width": 32, "height": 32},
        {"colour": 7, "screen_x": 196, "screen_y": 70, "width": 16, "height": 16},
    ]
    pivot = player_presentation_pivot(commands, grounded=True)
    bounds = player_canvas_bounds(commands, pivot)
    require(pivot == (215, 180), f"grounded source pivot drifted: {pivot}")
    require(bounds == (56, 74, 136, 184), f"grounded cel bounds drifted: {bounds}")
    require(0 <= bounds[0] < bounds[2] <= 192 and
            0 <= bounds[1] < bounds[3] <= 192,
            "grounded player cel is not fully visible")
    if negative:
        rejected_pivot = player_presentation_pivot(commands, grounded=False)
        rejected_bounds = player_canvas_bounds(commands, rejected_pivot)
        require(rejected_pivot == (215, 132),
                "negative control did not restore the rejected pivot")
        require(rejected_bounds[3] == 232 and rejected_bounds[3] > 192,
                "rejected pivot no longer reproduces the real crop")


def static_contract(inventory: dict[str, object]) -> None:
    source = (ROOT / "main.c").read_text(encoding="utf-8")
    build = (ROOT / "build.ps1").read_text(encoding="utf-8")
    verify = (ROOT / "verify.ps1").read_text(encoding="utf-8")
    runner = (HERE / "run_pinned_emulator.ps1").read_text(encoding="utf-8")
    normalizer = (HERE / "normalize_iso.py").read_text(encoding="utf-8")
    require(inventory["card_profile"] == "PlayerSalvageBench", "profile drifted")
    require("AVSP_PLAYER_SALVAGE_BENCH" in source, "bench compile guard missing")
    require("player_bench_frame_callback" in source, "bench callback missing")
    require("read_input();" in source, "bench does not reuse the existing pad sampler")
    require("draw_player(actor" in source, "bench does not reuse player VDP1 path")
    require("cap_world_step(&world, &input)" in source, "legacy runtime step disappeared")
    section = source[source.index("static void player_bench_frame_callback"):source.index("#ifdef AVSP_ENCOUNTER_TEST")]
    require("cap_world_step" not in section, "player bench entered mixed-world gameplay")
    for disabled in inventory["disabled_systems"]:
        require(disabled in inventory["disabled_systems"], f"disabled system drifted: {disabled}")
    require("PlayerSalvageBench" in build and "player-salvage-bench" in build,
            "build profile missing")
    require("PlayerSalvageBench" in verify, "Target profile missing")
    require(runner.count("$LASTEXITCODE -ne 0") >= 4,
            "pinned emulator runner does not stop on normalize, record, launch, and readback errors")
    require("production_payload_changed\": False" in normalizer,
            "normalizer does not declare its production-payload boundary")


def model_contract(negative: bool) -> None:
    first = replay()
    second = replay()
    require(first == second, "player-only replay is not deterministic")
    require(first[5]["x"] == 204 and first[5]["facing"] == 1,
            "right input did not set x/facing")
    require(first[8]["lane"] == 181, "down input did not set lane")
    require(first[12]["x"] == 196 and first[12]["facing"] == -1,
            "left input did not set x/facing")
    require(first[-1]["action"] == 0 and first[-1]["pose_phase"] == -1,
            "neutral input did not return to idle")
    if negative:
        mutated = replay(walk_duration=8)
        require(mutated != first, "mutated animation duration was accepted")
        process = subprocess.run(
            [sys.executable, "-B", str(ROOT / "tools" / "verify_iso_file.py"),
             str(ROOT / "game.iso"), "/SPR4/MISSING-PPLAYER.RLE"],
            capture_output=True, text=True)
        require(process.returncode != 0,
                "missing-player-asset negative control was accepted")
    visibility_contract(negative)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--negative-control", action="store_true")
    args = parser.parse_args()
    inventory = json.loads((HERE / "inventory.json").read_text(encoding="utf-8"))
    static_contract(inventory)
    model_contract(args.negative_control)
    print("PlayerSalvageBench contract: PASS")


if __name__ == "__main__":
    main()
