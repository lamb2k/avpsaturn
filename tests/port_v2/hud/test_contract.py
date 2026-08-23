#!/usr/bin/env python3
"""Strict host, approval-lock, and perturbation checks for PROMOTE-05."""

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


def compile_and_run(negative: str | None) -> None:
    translated = subprocess.run(
        ["wsl.exe", "wslpath", "-a", str(ROOT).replace("\\", "/")],
        check=True, capture_output=True, text=True).stdout.strip()
    executable = "build/port_v2/hud/hud_test"
    command = (
        f"cd '{translated}' && mkdir -p build/port_v2/hud && "
        "gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 "
        "src/port_v2/hud/hud.c tests/port_v2/hud/hud_test.c "
        f"-o {executable} && {executable}" +
        (f" --{negative}" if negative else ""))
    subprocess.run(["wsl.exe", "sh", "-lc", command], check=True)


def static_contract() -> None:
    contract = json.loads((HERE / "approved_contract.json").read_text(
        encoding="utf-8"))
    source = (ROOT / "main.c").read_text(encoding="utf-8")
    hud = (ROOT / "src/port_v2/hud/hud.c").read_text(encoding="utf-8")
    header = (ROOT / "src/port_v2/hud/hud.h").read_text(encoding="utf-8")
    build = (ROOT / "build.ps1").read_text(encoding="utf-8")
    verify = (ROOT / "verify.ps1").read_text(encoding="utf-8")
    makefile = (ROOT / "makefile").read_text(encoding="utf-8")
    ledger = json.loads((ROOT / "data/port_v2_migration_map.yaml").read_text(
        encoding="utf-8"))
    require(contract["task_id"] == "PROMOTE-05-HUD",
            "promotion contract task drifted")
    require(contract["approved_response"] == "keep going",
            "exact USER-05 approval drifted")
    require(contract["physical_saturn"] == "UNRUN",
            "physical Saturn result was overstated")
    for lock in contract["approved_contracts"]:
        require(sha256(ROOT / lock["path"]) == lock["sha256"],
                f"approved HUD lock changed: {lock['path']}")
    require("HudPromotionBench" in build and
            "hud-promotion-bench" in build and
            "HudPromotionBench" in verify,
            "dedicated HUD promotion profile is missing")
    require("AVSP_HUD_PROMOTION_BENCH" in makefile and
            "src/port_v2/hud/hud.c" in makefile,
            "Saturn build omits promoted HUD interface")
    require("avsp_port_v2_hud_build_frame" in source and
            "avsp_port_v2_hud_submit" in source,
            "promotion bench bypasses the semantic HUD interface")
    for text, label in ((hud, "HUD source"), (header, "HUD header")):
        require("jo/" not in text.lower() and "sgl" not in text.lower(),
                f"{label} depends on Jo/SGL")
    subsystems = {entry["id"]: entry for entry in ledger["subsystems"]}
    require(subsystems["hud"]["user_status"] == "APPROVED",
            "HUD lacks explicit approval")
    require(subsystems["hud"]["user_feedback"]["exact_response"] ==
            "keep going", "HUD exact USER-05 response drifted")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--negative-control",
                        choices=("broken-colors", "missing-p2"))
    args = parser.parse_args()
    static_contract()
    compile_and_run(args.negative_control)
    print("HUD promotion negative control: PASS" if args.negative_control else
          "HUD promotion contract: PASS")


if __name__ == "__main__":
    main()
