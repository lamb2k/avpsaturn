#!/usr/bin/env python3
"""Strict host, approval-lock, and perturbation checks for PROMOTE-07."""

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


def compile_and_run(negative: str | None) -> str:
    translated = subprocess.run(
        ["wsl.exe", "wslpath", "-a", str(ROOT).replace("\\", "/")],
        check=True, capture_output=True, text=True).stdout.strip()
    executable = "build/port_v2/cdda_residency/cdda_residency_test"
    command = (
        f"cd '{translated}' && mkdir -p build/port_v2/cdda_residency && "
        "gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 "
        "src/port_v2/audio/cdda/cdda.c "
        "src/port_v2/residency/residency.c "
        "tests/port_v2/cdda_residency/cdda_residency_test.c "
        f"-o {executable} && {executable}" +
        (f" --{negative}" if negative else ""))
    result = subprocess.run(["wsl.exe", "sh", "-lc", command], check=True,
                            capture_output=True, text=True)
    return result.stdout


def static_contract() -> dict:
    contract = json.loads((HERE / "approved_contract.json").read_text(
        encoding="utf-8"))
    cdda_source = (ROOT / "src/port_v2/audio/cdda/cdda.c").read_text(
        encoding="utf-8")
    cdda_header = (ROOT / "src/port_v2/audio/cdda/cdda.h").read_text(
        encoding="utf-8")
    residency_source = (ROOT / "src/port_v2/residency/residency.c").read_text(
        encoding="utf-8")
    residency_header = (ROOT / "src/port_v2/residency/residency.h").read_text(
        encoding="utf-8")
    card = (ROOT / "docs/archive/decomp-reset-20261106/task_cards/USER-07-CDDA-RESIDENCY-REVIEW.md").read_text(
        encoding="utf-8")
    build = (ROOT / "build.ps1").read_text(encoding="utf-8")
    verify = (ROOT / "verify.ps1").read_text(encoding="utf-8")
    makefile = (ROOT / "makefile").read_text(encoding="utf-8")
    integration = (ROOT / "main.c").read_text(encoding="utf-8")
    ledger = json.loads((ROOT / "data/port_v2_migration_map.yaml").read_text(
        encoding="utf-8"))
    require(contract["task_id"] == "PROMOTE-07-CDDA-RESIDENCY",
            "promotion contract task drifted")
    require(contract["approved_response"] in card,
            "exact USER-07 response is absent from the accepted card")
    require(contract["physical_saturn"] == "UNRUN" and
            contract["normal_release"] == "UNRUN",
            "unrun evidence tier was overstated")
    for lock in contract["approved_contracts"]:
        require(sha256(ROOT / lock["path"]) == lock["sha256"],
                f"approved component lock changed: {lock['path']}")
    for text, label in (
            (cdda_source, "CDDA source"), (cdda_header, "CDDA header"),
            (residency_source, "residency source"),
            (residency_header, "residency header")):
        require("jo/" not in text.lower() and "sgl" not in text.lower(),
                f"{label} depends on Jo/SGL")
    require("AvspPortV2CddaAudioOps" in cdda_header and
            "avsp_port_v2_cdda_submit" in cdda_source,
            "CDDA audio port is incomplete")
    require("AvspPortV2ResidencyAssetOps" in residency_header and
            "avsp_port_v2_residency_submit_read" in residency_source,
            "residency asset/load port is incomplete")
    require("CddaResidencyPromotionBench" in build and
            "CddaResidencyPromotionBench" in verify and
            "AVSP_CDDA_RESIDENCY_PROMOTION_BENCH" in makefile,
            "dedicated promotion target profile is not wired")
    require("avsp_port_v2_cdda_step" in integration and
            "avsp_port_v2_cdda_submit" in integration and
            "avsp_port_v2_residency_submit_read" in integration and
            "avsp_diag_cdda_fallback_used" in integration,
            "Saturn promotion adapter does not consume both production ports")
    subsystem = next(entry for entry in ledger["subsystems"]
                     if entry["id"] == "cdda-residency")
    require(subsystem["user_status"] == "APPROVED" and
            subsystem["user_feedback"]["exact_response"] ==
            contract["approved_response"],
            "CDDA/residency lacks exact USER-07 approval")
    return contract


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--negative-control",
                        choices=("wrong-track", "missing-region", "illegal-read"))
    args = parser.parse_args()
    contract = static_contract()
    if args.negative_control:
        compile_and_run(args.negative_control)
        print("CDDA/residency promotion negative control: PASS")
        return
    first = compile_and_run(None)
    second = compile_and_run(None)
    require(first == second,
            "CDDA/residency promotion host repeat is not deterministic")
    for negative in contract["negative_controls"]:
        compile_and_run(negative)
    print("CDDA/residency promotion contract: PASS (repeat + controls)")


if __name__ == "__main__":
    main()
