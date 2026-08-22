#!/usr/bin/env python3
"""Strict host and approval-lock contract for PROMOTE-02."""

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
        f"cd '{translated}' && mkdir -p build/port_v2/enemy && "
        "gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 "
        "src/port_v2/enemy/enemy.c tests/port_v2/enemy/enemy_test.c "
        "-o build/port_v2/enemy/enemy_test && "
        "./build/port_v2/enemy/enemy_test" +
        (" --negative-control" if negative else ""))
    subprocess.run(["wsl.exe", "sh", "-lc", command], check=True)


def static_contract() -> None:
    contract = json.loads((HERE / "approved_contract.json").read_text())
    source = (ROOT / "main.c").read_text()
    build = (ROOT / "build.ps1").read_text()
    verify = (ROOT / "verify.ps1").read_text()
    makefile = (ROOT / "makefile").read_text()
    ledger = json.loads((ROOT / "data/port_v2_migration_map.yaml").read_text())
    require(contract["task_id"] == "PROMOTE-02-ENEMY-PIPELINE", "task drifted")
    require(contract["approved_response"] == "looks great proceed", "approval drifted")
    require(contract["physical_saturn"] == "UNRUN", "physical result overstated")
    require("EnemyPromotionBench" in build and "enemy-promotion-bench" in build,
            "dedicated promotion profile missing")
    require("EnemyPromotionBench" in verify, "promotion Target profile missing")
    require("AVSP_ENEMY_PROMOTION_BENCH" in makefile and
            "src/port_v2/enemy/enemy.c" in makefile,
            "Saturn build bypasses promoted interface")
    require("avsp_port_v2_enemy_step" in source and
            "avsp_port_v2_enemy_load" in source,
            "promotion bench bypasses port_v2 enemy")
    entries = {entry["id"]: entry for entry in ledger["subsystems"]}
    for identifier in ("enemy-assets", "enemy-rendering", "enemy-animation"):
        require(entries[identifier]["user_status"] == "APPROVED",
                f"{identifier} lacks approval")
        require(entries[identifier]["user_feedback"]["exact_response"] ==
                "looks great proceed", f"{identifier} response drifted")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--negative-control", action="store_true")
    args = parser.parse_args()
    static_contract()
    compile_and_run(args.negative_control)


if __name__ == "__main__":
    main()
