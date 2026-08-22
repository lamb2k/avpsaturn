#!/usr/bin/env python3
"""Validate paired PlayerSalvageBench build and pinned-emulator evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load(relative: str) -> dict[str, object]:
    return json.loads((ROOT / relative).read_text(encoding="ascii"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_readback(report: dict[str, object], inventory: dict[str, object]) -> None:
    require(report["result"] == "PASS", "readback did not pass")
    require(report["physical_saturn"] == "UNRUN", "physical result was overstated")
    require(report["emulator"]["evidence_tier"] == "ONE_EMULATOR", "emulator tier drifted")
    initial = report["initial"]
    for key, expected in {"runtime_ready": 1, "asset_failures": 0,
                          "canary_ok": 1, "disc_late_reads": 0,
                          "render_count": 2, "cel_left": 56,
                          "cel_top": 74, "cel_right": 136,
                          "cel_bottom": 184}.items():
        require(initial[key] == expected, f"initial {key} was {initial[key]}")
    cases = report["input_cases"]
    expected_bits = {"right": 2, "down": 8, "left": 1}
    for direction, bit in expected_bits.items():
        require(cases[direction]["during"]["input_mask"] & bit,
                f"{direction} input was not sampled live")
        require(cases[direction]["during"]["input_edges"] & bit,
                f"{direction} input edge was not sampled")
    require(cases["right"]["after"]["x"] > cases["right"]["before"]["x"],
            "right did not move x")
    require(cases["right"]["after"]["facing"] == 1, "right did not face right")
    require(cases["right"]["during"]["render_count"] == 3,
            "walk did not use all player action layers")
    for direction in expected_bits:
        state = cases[direction]["during"]
        require(0 <= state["cel_left"] < state["cel_right"] <= 192 and
                0 <= state["cel_top"] < state["cel_bottom"] <= 192,
                f"{direction} walk pose exceeds the player cel")
    require(cases["down"]["after"]["lane"] > cases["down"]["before"]["lane"],
            "down did not move lane")
    require(cases["left"]["after"]["x"] < cases["left"]["before"]["x"],
            "left did not move x")
    require(cases["left"]["after"]["facing"] == 0xFFFFFFFF, "left did not face left")
    require(report["vdp1_command_count"] >= initial["render_count"], "VDP1 list is too short")
    screenshot = ROOT / report["screenshot"]["path"]
    require(screenshot.is_file(), "emulator screenshot is missing")
    require(sha256(screenshot) == report["screenshot"]["sha256"], "screenshot hash drifted")
    with Image.open(screenshot) as image:
        colours = image.convert("RGB").getcolors(maxcolors=image.width * image.height)
    require(colours is not None and len(colours) >= 16, "emulator screenshot has no rendered scene")
    clip = ROOT / report["movement_clip"]["path"]
    require(clip.is_file(), "movement clip is missing")
    require(sha256(clip) == report["movement_clip"]["sha256"], "movement clip hash drifted")
    require(report["movement_clip"]["frame_count"] == 4, "movement clip is incomplete")
    require(len(report["movement_frames"]) == 4, "movement frame evidence is incomplete")
    require(report["task_id"] == inventory["task_id"], "readback task drifted")


def main() -> None:
    inventory = json.loads((HERE / "inventory.json").read_text(encoding="utf-8"))
    builds = [load(f"build/port_v2/player_bench/run-{run}/build.json") for run in (1, 2)]
    normalizations = [load(f"build/port_v2/player_bench/run-{run}/iso-normalization.json") for run in (1, 2)]
    readbacks = [load(f"build/port_v2/player_bench/run-{run}/readback.json") for run in (1, 2)]
    require(builds[0]["result"] == builds[1]["result"] == "PASS", "a build record failed")
    require(builds[0]["source_commit"] == builds[1]["source_commit"], "repeat source commit drifted")
    require(builds[0]["source_tree"] == builds[1]["source_tree"], "repeat source tree drifted")
    require(builds[0]["compile_profile"] == inventory["compile_profile"], "compile profile drifted")
    require(builds[0]["manifest_profile"] == inventory["manifest_profile"], "manifest profile drifted")
    require(normalizations[0]["normalized_iso_sha256"] ==
            normalizations[1]["normalized_iso_sha256"], "normalized repeat ISO identity drifted")
    for build, normalization in zip(builds, normalizations):
        require(normalization["production_payload_changed"] is False,
                "normalizer changed production payloads")
        require(build["artifacts"]["game_iso"]["sha256"] == normalization["normalized_iso_sha256"],
                "build did not bind to its normalized ISO")
        require({name: member["sha256"] for name, member in
                 build["player_asset_members"].items()} ==
                normalization["required_payload_sha256"],
                "normalization changed a player asset member")
    require(builds[0]["player_asset_members"] == builds[1]["player_asset_members"],
            "repeat player asset payload drifted")
    for report, build in zip(readbacks, builds):
        require(report["source_commit"] == build["source_commit"], "readback/build commit mismatch")
        require(report["iso_sha256"] == build["artifacts"]["game_iso"]["sha256"],
                "readback/build ISO mismatch")
        check_readback(report, inventory)
    print("PlayerSalvageBench evidence: PASS")


if __name__ == "__main__":
    main()
