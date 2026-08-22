#!/usr/bin/env python3
"""Strict host and approval-lock contract for PROMOTE-01."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def compile_and_run(negative: bool) -> None:
    root = str(ROOT).replace("\\", "/")
    translated = subprocess.run(
        ["wsl.exe", "wslpath", "-a", root], check=True,
        capture_output=True, text=True).stdout.strip()
    command = (
        f"cd '{translated}' && mkdir -p build/port_v2/player && "
        "gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 "
        "src/port_v2/player/player.c tests/port_v2/player/player_test.c "
        "-o build/port_v2/player/player_test && "
        "./build/port_v2/player/player_test" +
        (" --negative-control" if negative else "")
    )
    subprocess.run(["wsl.exe", "sh", "-lc", command], check=True)


def static_contract() -> None:
    contract = json.loads((HERE / "approved_contract.json").read_text(
        encoding="utf-8"))
    source = (ROOT / "main.c").read_text(encoding="utf-8")
    build = (ROOT / "build.ps1").read_text(encoding="utf-8")
    verify = (ROOT / "verify.ps1").read_text(encoding="utf-8")
    makefile = (ROOT / "makefile").read_text(encoding="utf-8")
    ledger = json.loads((ROOT / "data/port_v2_migration_map.yaml").read_text(
        encoding="utf-8"))
    require(contract["task_id"] == "PROMOTE-01-PLAYER-PIPELINE",
            "promotion contract task drifted")
    require(contract["approved_response"] == "Looks good keep going",
            "exact USER-01 approval drifted")
    require(contract["physical_saturn"] == "UNRUN",
            "physical Saturn result was overstated")
    require("PlayerPromotionBench" in build and
            "player-promotion-bench" in build,
            "dedicated promotion build profile is missing")
    require("PlayerPromotionBench" in verify,
            "promotion Target profile is missing")
    require("AVSP_PLAYER_PROMOTION_BENCH" in makefile and
            "src/port_v2/player/player.c" in makefile,
            "Saturn build does not compile the promoted interface")
    require("avsp_port_v2_player_step" in source and
            "avsp_port_v2_player_load" in source,
            "promotion bench bypasses the port_v2 player interface")
    approved = {entry["id"]: entry for entry in ledger["subsystems"]}
    for identifier in ("loading-memory-ownership", "controller-input",
                       "player-assets", "player-rendering", "player-animation"):
        require(approved[identifier]["user_status"] == "APPROVED",
                f"{identifier} lacks explicit approval")
        require(approved[identifier]["user_feedback"]["exact_response"] ==
                "Looks good keep going", f"{identifier} response drifted")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--negative-control", action="store_true")
    args = parser.parse_args()
    static_contract()
    compile_and_run(args.negative_control)


if __name__ == "__main__":
    main()
