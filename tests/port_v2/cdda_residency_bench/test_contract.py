#!/usr/bin/env python3
"""Focused host, manifest, regression-lock, and mutation checks for SALVAGE-07."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DOMAINS = ("work_ram", "cartridge", "vdp1", "vdp2", "cram", "scsp")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_test() -> Path:
    translated = subprocess.run(
        ["wsl.exe", "wslpath", "-a", str(ROOT).replace("\\", "/")],
        check=True, capture_output=True, text=True).stdout.strip()
    executable = "build/port_v2/cdda_residency_bench/cdda_residency_test"
    command = (
        f"cd '{translated}' && mkdir -p build/port_v2/cdda_residency_bench && "
        "gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 "
        "tests/port_v2/cdda_residency_bench/cdda_residency_bench.c "
        "tests/port_v2/cdda_residency_bench/cdda_residency_test.c "
        f"-o {executable}")
    subprocess.run(["wsl.exe", "sh", "-lc", command], check=True)
    return ROOT / executable


def run(executable: Path, negative: str | None = None) -> str:
    translated = subprocess.run(
        ["wsl.exe", "wslpath", "-a", str(executable).replace("\\", "/")],
        check=True, capture_output=True, text=True).stdout.strip()
    args = ["wsl.exe", translated]
    if negative:
        args += ["--negative-control", negative]
    return subprocess.run(args, check=True, capture_output=True,
                          text=True).stdout


def static_contract() -> tuple[dict, dict]:
    contract = json.loads((HERE / "contract.json").read_text(encoding="utf-8"))
    manifest = json.loads((HERE / "phase_manifest.json").read_text(
        encoding="utf-8"))
    inventory = json.loads((HERE / "inventory.json").read_text(
        encoding="utf-8"))
    fixture = ROOT / contract["fixture"]["source_path"]
    route = json.loads((ROOT / contract["source_event"]["route_manifest"])
                       .read_text(encoding="utf-8"))
    source = (ROOT / "main.c").read_text(encoding="utf-8")
    build = (ROOT / "build.ps1").read_text(encoding="utf-8")
    verify = (ROOT / "verify.ps1").read_text(encoding="utf-8")
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    require(contract["task_id"] == inventory["task_id"] ==
            manifest["task_id"] == "SALVAGE-07-CDDA-RESIDENCY",
            "task identity drifted")
    require(contract["physical_saturn"] == manifest["physical_saturn"] ==
            "UNRUN", "physical Saturn evidence was overstated")
    require(contract["human_review"] ==
            "REQUIRED_BEFORE_SUBJECTIVE_APPROVAL",
            "audible review gate is missing")
    require(fixture.stat().st_size == contract["fixture"]["bytes"] == 64 and
            sha256(fixture) == contract["fixture"]["sha256"] ==
            manifest["disc"]["legal_data_read_windows"][0]["sha256"],
            "bounded residency fixture changed")
    event = next((event for event in route["events"]
                  if event["id"] == contract["source_event"]["event_id"]), None)
    require(event is not None and event["frame"] ==
            contract["source_event"]["frame"] == 2520,
            "Stage 1 source-event binding drifted")
    private_audio = ROOT / contract["source_audio"]["path"]
    require(private_audio.is_file() and
            private_audio.stat().st_size == contract["source_audio"]["bytes"] and
            sha256(private_audio) == contract["source_audio"]["sha256"],
            "private Stage 1 audio capture identity drifted")
    require(manifest["classification"] == "ADAPTED" and
            manifest["source_binding"]["binding_status"] == "ADAPTED",
            "source binding was overstated as exact/measured")
    allocations = manifest["allocations"]
    require(tuple(allocations) == DOMAINS,
            "phase manifest does not enumerate every memory domain")
    require(allocations["work_ram"]["phase_high_water_bytes"] == 72 and
            allocations["work_ram"]["canary_policy"] == "REQUIRED",
            "work-RAM read buffer or canary allocation drifted")
    for domain in DOMAINS[1:]:
        require(allocations[domain]["phase_high_water_bytes"] == 0 and
                allocations[domain]["canary_policy"] ==
                "NOT_REQUIRED_ZERO_ALLOCATION",
                f"{domain} allocation is missing or unknown")
    linked = manifest["linked_profile_high_water"]
    require(int(linked["limit"], 16) - int(linked["bend"], 16) ==
            linked["headroom_bytes"] and linked["status"] == "MEASURED",
            "linked work-RAM high-water does not recompute")
    require("CddaResidencySalvageBench" in build and
            "cdda-residency-salvage-bench" in build and
            "CddaResidencySalvageBench" in verify,
            "dedicated CDDA/residency target profile is missing")
    require("AVSP_CDDA_RESIDENCY_SALVAGE_BENCH" in makefile and
            "cdda_residency_bench.c" in makefile,
            "Saturn build omits the CDDA/residency diagnostic")
    require("jo_audio_play_cd_track(2, 2, true)" in source and
            "\"RESCHK.BIN\", \"DIAG\"" in source,
            "runtime bench does not exercise real CDDA and guarded reads")
    for lock in contract["approved_contracts"]:
        require(sha256(ROOT / lock["path"]) == lock["sha256"],
                f"approved component lock changed: {lock['path']}")
    return contract, manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--negative-control", choices=(
        "permit-illegal-read", "missing-allocation", "wrong-source-event"))
    args = parser.parse_args()
    contract, _ = static_contract()
    executable = compile_test()
    if args.negative_control:
        run(executable, args.negative_control)
        print("CDDA/residency negative control: PASS")
        return
    first = run(executable)
    second = run(executable)
    require(first == second, "host CDDA ownership repeat is not deterministic")
    for negative in contract["negative_controls"]:
        run(executable, negative)
    print("CDDA/residency contract: PASS (deterministic repeat + controls)")


if __name__ == "__main__":
    main()
