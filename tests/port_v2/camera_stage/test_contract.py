#!/usr/bin/env python3
"""Strict host, approval-lock, and perturbation checks for PROMOTE-04."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_and_run(negative: bool) -> None:
    translated = subprocess.run(
        ["wsl.exe", "wslpath", "-a", str(ROOT).replace("\\", "/")],
        check=True, capture_output=True, text=True).stdout.strip()
    command = (
        f"cd '{translated}' && mkdir -p build/port_v2/camera_stage && "
        "gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 "
        "src/port_v2/camera/camera.c src/port_v2/stage/stage.c "
        "tests/port_v2/camera_stage/camera_stage_test.c "
        "-o build/port_v2/camera_stage/camera_stage_test && "
        "./build/port_v2/camera_stage/camera_stage_test" +
        (" --negative-control" if negative else ""))
    subprocess.run(["wsl.exe", "sh", "-lc", command], check=True)


def static_contract() -> None:
    contract = json.loads((HERE / "approved_contract.json").read_text(
        encoding="utf-8"))
    salvage = ROOT / contract["approved_salvage_contract"]["path"]
    source = (ROOT / "main.c").read_text(encoding="utf-8")
    build = (ROOT / "build.ps1").read_text(encoding="utf-8")
    verify = (ROOT / "verify.ps1").read_text(encoding="utf-8")
    makefile = (ROOT / "makefile").read_text(encoding="utf-8")
    ledger = json.loads((ROOT / "data/port_v2_migration_map.yaml").read_text(
        encoding="utf-8"))
    camera = (ROOT / "src/port_v2/camera/camera.c").read_text(
        encoding="utf-8")
    stage = (ROOT / "src/port_v2/stage/stage.c").read_text(
        encoding="utf-8")
    require(contract["task_id"] == "PROMOTE-04-CAMERA-STAGE",
            "promotion contract task drifted")
    require(contract["approved_response"] == "pass for camera and stage",
            "exact USER-04 approval drifted")
    require(contract["row_scroll_status"] == "ADAPTED_UNCAPTURED",
            "row-scroll limitation was overstated")
    require(contract["physical_saturn"] == "UNRUN",
            "physical Saturn result was overstated")
    require(sha256(salvage) ==
            contract["approved_salvage_contract"]["sha256"],
            "approved salvage contract changed")
    require("CameraStagePromotionBench" in build and
            "camera-stage-promotion-bench" in build and
            "CameraStagePromotionBench" in verify,
            "dedicated promotion profile is missing")
    require("AVSP_CAMERA_STAGE_PROMOTION_BENCH" in makefile and
            "src/port_v2/camera/camera.c" in makefile and
            "src/port_v2/stage/stage.c" in makefile,
            "Saturn build omits promoted camera/stage interfaces")
    require("avsp_port_v2_camera_step" in source and
            "avsp_port_v2_stage_submit" in source,
            "promotion bench bypasses the bounded interfaces")
    for text, label in ((camera, "camera"), (stage, "stage")):
        require("jo/" not in text.lower() and "sgl" not in text.lower(),
                f"{label} production interface depends on Jo/SGL")
    subsystems = {entry["id"]: entry for entry in ledger["subsystems"]}
    for identifier in ("palette-cram", "vdp2-stage-layers",
                       "camera-framing"):
        require(subsystems[identifier]["user_status"] == "APPROVED",
                f"{identifier} lacks explicit approval")
        require(subsystems[identifier]["user_feedback"]["exact_response"] ==
                "pass for camera and stage",
                f"{identifier} exact USER-04 response drifted")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--negative-control", action="store_true")
    args = parser.parse_args()
    static_contract()
    compile_and_run(args.negative_control)
    print("Camera/stage promotion negative control: PASS" if
          args.negative_control else "Camera/stage promotion contract: PASS")


if __name__ == "__main__":
    main()
