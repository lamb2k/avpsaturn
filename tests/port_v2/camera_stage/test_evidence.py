#!/usr/bin/env python3
"""Validate paired CameraStagePromotionBench target/emulator evidence."""

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


def deterministic_state(state: dict[str, object]) -> dict[str, object]:
    result = dict(state)
    result.pop("emulator_frame", None)
    return result


def check_state(state: dict[str, object], contract: dict[str, object]) -> None:
    require(state["runtime_ready"] == 1, "stage runtime not ready")
    require(state["interface_version"] == contract["stage_interface_version"],
            "stage diagnostic interface drifted")
    require(state["layer_count"] == 2, "two VDP2 layers not active")
    require((state["source_width"], state["output_width"]) == (384, 352),
            "384-to-352 framing drifted")
    require(state["priority_lock_ok"] == state["port_lock_ok"] == 1,
            "camera/stage port or priority lock failed")
    require(state["row_scroll_status"] == 1,
            "uncaptured row-scroll status was overstated")
    require(state["render_submissions"] > 0,
            "semantic stage events did not reach the render port")
    require(state["asset_failures"] == state["disc_late_reads"] == 0,
            "asset or late-read failure")
    require(state["vram_canaries_all_match"], "plane/PNT canary failed")
    require(all(value["match"] for value in state["cram"].values()),
            "CRAM content differs from approved fixture")
    require(state["priority"] == contract["priority"],
            "live priority order drifted")
    require(state["registers"]["TVMD"] == "0x8101",
            "scanout is not pinned NTSC 352x224")
    require(int(state["registers"]["BGON"], 16) & 3 == 3,
            "NBG0/NBG1 are not both displayed")
    require(state["cram"]["nbg0"]["offset"] == 2 and
            state["cram"]["nbg1"]["offset"] == 3,
            "live CRAM ownership drifted")
    require(int(state["vdp1_command_classes"].get("1", 0)) > 0 and
            int(state["vdp1_command_classes"].get("2", 0)) > 0,
            "actor/foreground priority classes were not exercised")


def main() -> None:
    inventory = json.loads((HERE / "inventory.json").read_text(
        encoding="utf-8"))
    contract = json.loads((HERE / "approved_contract.json").read_text(
        encoding="utf-8"))
    builds = [load(f"build/port_v2/camera_stage/run-{run}/build.json")
              for run in (1, 2)]
    normals = [load(f"build/port_v2/camera_stage/run-{run}/iso-normalization.json")
               for run in (1, 2)]
    reads = [load(f"build/port_v2/camera_stage/run-{run}/readback.json")
             for run in (1, 2)]
    require(builds[0]["source_commit"] == builds[1]["source_commit"],
            "repeat source commit drifted")
    require(builds[0]["source_tree"] == builds[1]["source_tree"],
            "repeat source tree drifted")
    require(builds[0]["compile_profile"] == inventory["compile_profile"] and
            builds[0]["manifest_profile"] == inventory["manifest_profile"],
            "promotion build profile drifted")
    require(normals[0]["normalized_iso_sha256"] ==
            normals[1]["normalized_iso_sha256"],
            "normalized promotion ISO is not deterministic")
    require(builds[0]["iso_members"] == builds[1]["iso_members"],
            "repeat promotion package drifted")
    require([deterministic_state(state) for state in reads[0]["fixed_samples"]] ==
            [deterministic_state(state) for state in reads[1]["fixed_samples"]],
            "fixed-checkpoint semantic readback is not deterministic")
    require({key: deterministic_state(value) for key, value in
             reads[0]["scroll_threshold"].items()} ==
            {key: deterministic_state(value) for key, value in
             reads[1]["scroll_threshold"].items()},
            "scroll-threshold semantic readback is not deterministic")
    require(builds[0]["iso_members"]["/ST1/STRIPS.BIN"]["sha256"] ==
            contract["fixture"]["strips_bin_sha256"],
            "approved stage fixture identity drifted")
    for name, expected in contract["approved_player_asset_sha256"].items():
        require(builds[0]["iso_members"][name]["sha256"] == expected,
                f"approved player asset changed: {name}")
    for report, build in zip(reads, builds):
        require(report["result"] == "PASS" and
                report["physical_saturn"] == "UNRUN" and
                report["row_scroll_status"] == "ADAPTED_UNCAPTURED",
                "promotion result failed or overstated evidence")
        require(report["source_commit"] == build["source_commit"] and
                report["iso_sha256"] == build["artifacts"]["game_iso"]["sha256"],
                "readback/build identity mismatch")
        first, repeat = report["fixed_samples"]
        before = report["scroll_threshold"]["before"]
        after = report["scroll_threshold"]["after"]
        for state in (first, repeat, before, after):
            check_state(state, contract)
        require(first["relative_frame"] == repeat["relative_frame"] == 20 and
                first["scroll_x"] == repeat["scroll_x"] == [0, 7] and
                first["objects"] == repeat["objects"] == 477,
                "fixed checkpoint repeat drifted")
        require(before["relative_frame"] == 45 and
                before["scroll_x"] == [0, 7] and
                after["relative_frame"] == 46 and
                after["scroll_x"] == [10, 15],
                "one-frame scroll threshold drifted")
        require(report["bounded_stability_frames"] > 0,
                "bounded stability interval was not observed")
        screenshot = ROOT / report["final_scanout"]["screenshot"]["path"]
        require(screenshot.is_file() and sha256(screenshot) ==
                report["final_scanout"]["screenshot"]["sha256"],
                "final-scanout screenshot is missing or changed")
        with Image.open(screenshot) as image:
            colours = image.convert("RGB").getcolors(
                maxcolors=image.width * image.height)
        require(colours is not None and len(colours) >= 16,
                "final scanout has no rendered stage")
    print("CameraStagePromotionBench evidence: PASS")


if __name__ == "__main__":
    main()
