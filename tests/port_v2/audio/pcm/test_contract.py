#!/usr/bin/env python3
"""Strict host, approval-lock, and perturbation checks for PROMOTE-06."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
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
    executable = "build/port_v2/audio/pcm/pcm_test"
    command = (
        f"cd '{translated}' && mkdir -p build/port_v2/audio/pcm && "
        "gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 "
        "src/port_v2/audio/pcm/pcm.c tests/port_v2/audio/pcm/pcm_test.c "
        f"-o {executable} && {executable}" +
        (f" --{negative}" if negative else ""))
    subprocess.run(["wsl.exe", "sh", "-lc", command], check=True)


def static_contract() -> None:
    contract = json.loads((HERE / "approved_contract.json").read_text(
        encoding="utf-8"))
    source = (ROOT / "main.c").read_text(encoding="utf-8")
    pcm = (ROOT / "src/port_v2/audio/pcm/pcm.c").read_text(encoding="utf-8")
    header = (ROOT / "src/port_v2/audio/pcm/pcm.h").read_text(encoding="utf-8")
    build = (ROOT / "build.ps1").read_text(encoding="utf-8")
    verify = (ROOT / "verify.ps1").read_text(encoding="utf-8")
    makefile = (ROOT / "makefile").read_text(encoding="utf-8")
    ledger = json.loads((ROOT / "data/port_v2_migration_map.yaml").read_text(
        encoding="utf-8"))
    require(contract["task_id"] == "PROMOTE-06-PCM",
            "promotion contract task drifted")
    require(contract["approved_response"] ==
            "sound is great hud looks broken in terms of colors",
            "exact USER-05 PCM approval drifted")
    require(contract["physical_saturn"] == "UNRUN",
            "physical Saturn result was overstated")
    for lock in contract["approved_contracts"]:
        require(sha256(ROOT / lock["path"]) == lock["sha256"],
                f"approved PCM/HUD lock changed: {lock['path']}")
    require("PcmPromotionBench" in build and
            "pcm-promotion-bench" in build and
            "PcmPromotionBench" in verify,
            "dedicated PCM promotion profile is missing")
    require("AVSP_PCM_PROMOTION_BENCH" in makefile and
            "src/port_v2/audio/pcm/pcm.c" in makefile,
            "Saturn build omits promoted PCM interface")
    require("avsp_port_v2_pcm_step" in source and
            "avsp_port_v2_pcm_submit" in source,
            "promotion bench bypasses the semantic PCM interface")
    for text, label in ((pcm, "PCM source"), (header, "PCM header")):
        require("jo/" not in text.lower() and "sgl" not in text.lower(),
                f"{label} depends on Jo/SGL")
    subsystem = next(entry for entry in ledger["subsystems"]
                     if entry["id"] == "pcm")
    require(subsystem["user_status"] == "APPROVED" and
            subsystem["user_feedback"]["exact_response"] ==
            contract["approved_response"],
            "PCM lacks exact USER-05 approval")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--negative-control",
                        choices=("wrong-cue", "wrong-timing"))
    args = parser.parse_args()
    static_contract()
    compile_and_run(args.negative_control)
    print("PCM promotion negative control: PASS" if args.negative_control else
          "PCM promotion contract: PASS")


if __name__ == "__main__":
    main()
