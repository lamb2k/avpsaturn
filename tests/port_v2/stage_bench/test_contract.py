#!/usr/bin/env python3
"""Deterministic stage/camera contract and real perturbation controls."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate(contract: dict[str, object]) -> None:
    fixture = contract["fixture"]
    priority = contract["priority"]
    framing = contract["framing"]
    require(contract["task_id"] == "SALVAGE-04-CAMERA-STAGE-LAYERS",
            "task identity drifted")
    require(set(fixture["plane_pixel_sha256"]) == {"scroll2", "scroll3"},
            "both independently scrolling planes are required")
    require(fixture["strips_bin_sha256"] ==
            "7c28617351ec2bb2099d10e28de561f0ef64feb2fbb1784c5dae11d29c7f1c22",
            "stale or substituted stage fixture")
    require(priority["nbg1"] < priority["nbg0"] < priority["actor"] <
            priority["foreground"], "stage/actor priority order is inverted")
    require((framing["source_width"], framing["output_width"],
             framing["output_height"]) == (384, 352, 224),
            "384-to-352 final framing drifted")
    fixed = contract["fixed_frame"]
    threshold = contract["scroll_threshold"]
    require((fixed["relative_frame"], fixed["scroll_x"], fixed["objects"]) ==
            (20, [0, 7], 477), "fixed checkpoint drifted")
    require(threshold["after_frame"] == threshold["before_frame"] + 1 and
            threshold["before_scroll_x"] == [0, 7] and
            threshold["after_scroll_x"] == [10, 15],
            "deterministic scroll threshold drifted")
    require(contract["physical_saturn"] == "UNRUN",
            "physical Saturn evidence was overstated")


def static_wiring() -> None:
    contract = json.loads((HERE / "stage_contract.json").read_text(
        encoding="utf-8"))
    validate(contract)
    build = (ROOT / "build.ps1").read_text(encoding="utf-8")
    verify = (ROOT / "verify.ps1").read_text(encoding="utf-8")
    makefile = (ROOT / "makefile").read_text(encoding="utf-8")
    source = (ROOT / "main.c").read_text(encoding="utf-8")
    for token, text in (
            ("CameraStageSalvageBench", build),
            ("camera-stage-salvage-bench", build),
            ("CameraStageSalvageBench", verify),
            ("AVSP_CAMERA_STAGE_SALVAGE_BENCH", makefile),
            ("avsp_diag_stage_priority_lock_ok", source),
            ("avsp_diag_stage_scroll_steps", source)):
        require(token in text, f"missing stage bench wiring: {token}")


def negative_controls() -> None:
    original = json.loads((HERE / "stage_contract.json").read_text(
        encoding="utf-8"))
    mutations = []
    missing_plane = copy.deepcopy(original)
    del missing_plane["fixture"]["plane_pixel_sha256"]["scroll3"]
    mutations.append(("missing plane", missing_plane))
    stale_disc = copy.deepcopy(original)
    stale_disc["fixture"]["strips_bin_sha256"] = "0" * 64
    mutations.append(("stale disc", stale_disc))
    priority = copy.deepcopy(original)
    priority["priority"]["actor"], priority["priority"]["foreground"] = 6, 4
    mutations.append(("priority inversion", priority))
    framing = copy.deepcopy(original)
    framing["framing"]["output_width"] = 384
    mutations.append(("wrong framing", framing))
    threshold = copy.deepcopy(original)
    threshold["scroll_threshold"]["after_scroll_x"] = [0, 7]
    mutations.append(("missing scroll step", threshold))
    for name, mutation in mutations:
        try:
            validate(mutation)
        except AssertionError:
            continue
        raise AssertionError(f"{name} perturbation was not rejected")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--negative-control", action="store_true")
    args = parser.parse_args()
    static_wiring()
    if args.negative_control:
        negative_controls()
        print("Camera/stage perturbation controls: PASS")
    else:
        print("Camera/stage contract: PASS")


if __name__ == "__main__":
    main()
