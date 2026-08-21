#!/usr/bin/env python3
"""Static and evidence checks for the SALVAGE-00 baseline bench."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
EXPECTED_TASK = "SALVAGE-00-OLD-BUILD-BASELINE"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="ascii"))


def validate_inventory(inventory: dict) -> None:
    require(inventory.get("schema") == 1, "inventory schema drifted")
    require(inventory.get("task_id") == EXPECTED_TASK, "task identity drifted")
    require(inventory.get("card_profile") == "OldBuildBaseline",
            "card profile drifted")
    require(inventory.get("underlying_build_switch") == "StreetTest",
            "baseline no longer reuses StreetTest")
    require(inventory.get("production_behavior_changed") is False,
            "baseline claims production behavior changed")
    require(len(inventory.get("subsystems", [])) >= 8,
            "major subsystem inventory is incomplete")
    required = {"/0.bin", "/GAME.BIN", "/ST1/STRIPS.BIN"}
    require(set(inventory.get("required_iso_members", {})) == required,
            "required ISO member contract drifted")


def validate_build(report: dict, inventory: dict) -> None:
    require(report.get("schema") == 1, "build schema drifted")
    require(report.get("task_id") == EXPECTED_TASK, "build task drifted")
    require(report.get("card_profile") == "OldBuildBaseline",
            "build card profile drifted")
    require(report.get("compile_profile") ==
            inventory["underlying_compile_profile"], "compile profile drifted")
    require(report.get("manifest_profile") ==
            inventory["underlying_manifest_profile"], "manifest profile drifted")
    require(report.get("tracked_source_dirty") is False,
            "build was not made from a tracked-clean source tree")
    require(report.get("result") == "PASS", "build did not pass")
    require(report.get("evidence_tier") == "BUILD_ONLY",
            "build evidence tier drifted")
    require(report.get("physical_saturn") == "UNRUN",
            "build was relabeled as physical evidence")
    members = report.get("required_iso_members", {})
    require(set(members) == set(inventory["required_iso_members"]),
            "required ISO member is absent")
    for name, entry in members.items():
        require(entry.get("bytes", 0) > 0, f"{name} is empty")
        require(len(entry.get("sha256", "")) == 64, f"{name} hash missing")
    artifacts = report.get("artifacts", {})
    require(report.get("manifest_iso_sha256") ==
            artifacts.get("game_iso", {}).get("sha256"),
            "manifest and ISO identities disagree")
    generated = report.get("generated_inputs", {})
    require(len(generated) >= 20, "ignored generated-input inventory is incomplete")
    for name, entry in generated.items():
        require(name.startswith("generated/"), f"generated input escapes root: {name}")
        require(entry.get("bytes", 0) > 0 and len(entry.get("sha256", "")) == 64,
                f"generated input identity is incomplete: {name}")
    local = report.get("ignored_build_inputs", {})
    require(set(local) == {"loader/loader.c", "loader/loader.linker",
                           "loader/trampoline.s", "tools/build_loader_ip.py"},
            "local staged-loader input inventory is incomplete")
    for name, entry in local.items():
        require(entry.get("bytes", 0) > 0 and len(entry.get("sha256", "")) == 64,
                f"local build input identity is incomplete: {name}")


def validate_readback(report: dict, build: dict) -> None:
    require(report.get("schema") == 1, "readback schema drifted")
    require(report.get("task_id") == EXPECTED_TASK, "readback task drifted")
    require(report.get("source_commit") == build.get("source_commit"),
            "readback commit differs from build")
    require(report.get("manifest_sha256") ==
            build["artifacts"]["hardware_manifest"]["sha256"],
            "readback manifest differs from build")
    require(report.get("iso_sha256") ==
            build["artifacts"]["game_iso"]["sha256"],
            "readback ISO differs from build")
    require(report.get("physical_saturn") == "UNRUN",
            "emulator evidence was relabeled physical")
    emulator = report.get("emulator", {})
    require(emulator.get("identity") == "Yaba Sanshiro 1.20.37-2986eb",
            "emulator identity is not pinned")
    require(emulator.get("evidence_tier") == "ONE_EMULATOR",
            "emulator evidence tier drifted")
    require(len(emulator.get("executable_sha256", "")) == 64,
            "emulator executable hash missing")
    samples = report.get("samples", [])
    require(len(samples) == 2, "bounded stability needs two samples")
    period = report.get("fixture_period")
    target = report.get("target_relative_frame")
    for index, sample in enumerate(samples):
        require(sample.get("runtime_ready") == 1,
                f"sample {index} runtime is not ready")
        require(sample.get("asset_failure_count") == 0,
                f"sample {index} reports an asset failure")
        require(sample.get("frontend_late_reads") == 0,
                f"sample {index} reports a late disc read")
        require(sample.get("street_objects", 0) > 0,
                f"sample {index} rendered no objects")
        require(sample.get("street_frame", -1) % period == target,
                f"sample {index} is not at the target fixture frame")
    require(samples[1]["street_frame"] > samples[0]["street_frame"],
            "bounded stability did not advance")
    require(samples[0]["street_scx"] == samples[1]["street_scx"],
            "scroll readback is unstable at the repeated fixture frame")
    require(samples[0]["street_objects"] == samples[1]["street_objects"],
            "render count is unstable at the repeated fixture frame")
    screenshot = ROOT / report["screenshot"]["path"]
    require(screenshot.is_file() and screenshot.stat().st_size > 0,
            "emulator screenshot is missing")
    require(hashlib.sha256(screenshot.read_bytes()).hexdigest() ==
            report["screenshot"]["sha256"], "screenshot hash disagrees")


def stable_build(report: dict) -> dict:
    return {
        "source_commit": report["source_commit"],
        "source_tree": report["source_tree"],
        "compile_profile": report["compile_profile"],
        "manifest_profile": report["manifest_profile"],
        "artifacts": report["artifacts"],
        "generated_inputs": report["generated_inputs"],
        "ignored_build_inputs": report["ignored_build_inputs"],
        "required_iso_members": report["required_iso_members"],
    }


def stable_readback(report: dict) -> dict:
    return {
        "source_commit": report["source_commit"],
        "compile_profile": report["compile_profile"],
        "manifest_profile": report["manifest_profile"],
        "manifest_sha256": report["manifest_sha256"],
        "iso_sha256": report["iso_sha256"],
        "fixture_period": report["fixture_period"],
        "target_relative_frame": report["target_relative_frame"],
        "emulator_identity": report["emulator"]["identity"],
        "emulator_executable_sha256": report["emulator"]["executable_sha256"],
        "sample_states": [{
            key: sample[key] for key in (
                "runtime_ready", "street_scx", "street_objects",
                "asset_failure_count", "frontend_late_reads")
        } for sample in report["samples"]],
    }


def invalid_disc_control(inventory: dict) -> None:
    image = ROOT / "game.iso"
    original_hash = hashlib.sha256(image.read_bytes()).hexdigest()
    invalid = ROOT / "build/port_v2/old_build_baseline/invalid-disc.iso"
    invalid.parent.mkdir(parents=True, exist_ok=True)
    payload = bytearray(image.read_bytes())
    payload[16 * 2048 + 1] ^= 0x01
    invalid.write_bytes(payload)
    verifier = ROOT / "tools/verify_iso_file.py"
    expected = ROOT / inventory["required_iso_members"]["/GAME.BIN"]
    process = subprocess.run(
        [sys.executable, "-B", str(verifier), str(invalid), "/GAME.BIN",
         "--equals", str(expected)], capture_output=True, text=True)
    invalid_hash = hashlib.sha256(invalid.read_bytes()).hexdigest()
    invalid.unlink()
    require(process.returncode != 0,
            "invalid-disc control was incorrectly accepted")
    require(hashlib.sha256(image.read_bytes()).hexdigest() == original_hash,
            "negative control altered the valid ISO")
    report = {
        "schema": 1,
        "control": "invalid ISO-9660 primary volume descriptor",
        "valid_iso_sha256": original_hash,
        "invalid_iso_sha256": invalid_hash,
        "validator_exit_code": process.returncode,
        "rejected": True,
        "physical_saturn": "UNRUN",
    }
    output = ROOT / "build/port_v2/old_build_baseline/negative-control.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="ascii", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", choices=("none", "build", "full"),
                        default="none")
    parser.add_argument("--negative-control", action="store_true")
    args = parser.parse_args()

    inventory = load(HERE / "inventory.json")
    validate_inventory(inventory)
    mutation = copy.deepcopy(inventory)
    mutation["required_iso_members"].pop("/GAME.BIN")
    try:
        validate_inventory(mutation)
    except ValueError:
        pass
    else:
        raise ValueError("inventory missing-member mutation was accepted")

    if args.evidence in ("build", "full"):
        builds = [load(ROOT / f"build/port_v2/old_build_baseline/run-{run}/build.json")
                  for run in (1, 2)]
        for build in builds:
            validate_build(build, inventory)
        require(stable_build(builds[0]) == stable_build(builds[1]),
                "two clean baseline builds are not deterministic")
        if args.negative_control:
            invalid_disc_control(inventory)
        if args.evidence == "full":
            readbacks = [load(ROOT / f"build/port_v2/old_build_baseline/run-{run}/readback.json")
                         for run in (1, 2)]
            for readback, build in zip(readbacks, builds):
                validate_readback(readback, build)
            require(stable_readback(readbacks[0]) == stable_readback(readbacks[1]),
                    "two pinned-emulator readbacks are not deterministic")
    print(f"OldBuildBaseline contract: PASS ({args.evidence})")


if __name__ == "__main__":
    main()
