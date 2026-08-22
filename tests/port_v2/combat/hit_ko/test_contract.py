#!/usr/bin/env python3
"""Manifest-derived host differential for the bounded HIT/KO promotion."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
FIELDS = ("state", "sub_state", "action", "anim_record", "anim_timer",
          "health", "hit_value")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def manifest_state(manifest: dict, sample: int) -> tuple[int, ...]:
    values = {}
    for field in FIELDS:
        transitions = manifest["field_transitions"][field]
        value = transitions[0]["before_value"]
        for transition in transitions:
            if transition["semantic_sample_after"] <= sample:
                value = transition["after_value"]
        values[field] = value
    return tuple(values[field] for field in FIELDS)


def expected_trace(manifest: dict, first: int, last: int) -> list[tuple[int, ...]]:
    rows = []
    for sample in range(first, last + 1):
        active = int(sample != last)
        rows.append((sample,) + manifest_state(manifest, sample) + (active,))
    return rows


def parse_trace(text: str) -> list[tuple[int, ...]]:
    return [tuple(int(value) for value in line.split(","))
            for line in text.strip().splitlines()]


def compile_source(root_wsl: str, source: str, output: str) -> None:
    command = (
        f"cd '{root_wsl}' && mkdir -p build/port_v2/combat/hit_ko && "
        "gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 "
        "-Isrc/port_v2/combat/hit_ko "
        f"{source} tests/port_v2/combat/hit_ko/hit_ko_test.c -o {output}")
    subprocess.run(["wsl.exe", "sh", "-lc", command], check=True)


def run_trace(root_wsl: str, executable: str, kind: str) -> str:
    command = f"cd '{root_wsl}' && ./{executable} {kind}"
    return subprocess.run(["wsl.exe", "sh", "-lc", command], check=True,
                          capture_output=True, text=True).stdout


def validate_manifest(contract: dict, manifest: dict) -> None:
    path = ROOT / contract["source_manifest"]
    require(sha256(path) == contract["source_manifest_sha256"],
            "accepted writer manifest identity drifted")
    require(manifest["schema"] == contract["source_manifest_schema"],
            "accepted writer manifest schema drifted")
    require(manifest["target"] == contract["target"], "source target drifted")
    require(not manifest["forbidden_content_present"],
            "committed manifest contains forbidden private content")
    for name in ("hit", "ko"):
        expected = contract[name]
        correlation = manifest["correlations"][name]
        require(correlation["anim_writer_instance_index"] ==
                expected["writer_instance"], f"{name} writer index drifted")
        anim_change = next(item for item in correlation["semantic_changes"]
                           if item["field"] == "anim_record")
        require(anim_change["after"] == expected["anim_record"],
                f"{name} animation binding drifted")
        writer = manifest["writer_instances"][expected["writer_instance"]]
        binding = contract["writer_binding"]
        require(writer["index"] == expected["writer_instance"] and
                writer["instruction_pc"] == binding["instruction_pc"] and
                writer["watchpoint_reported_pc"] == binding["successor_pc"] and
                writer["bus_event_count"] == binding["bus_event_count"] and
                writer["write_width_bytes"] == binding["write_width_bytes"] and
                writer["dynamic_register_binding"]["a6"] == binding["a6"],
                f"{name} live writer binding drifted")
    binding_hashes = contract["accepted_binding_sha256"]
    require(manifest["integrity"]["field_transition_sha256"] ==
            binding_hashes["field_transitions"], "transition binding drifted")
    require(manifest["integrity"]["writer_instance_sha256"] ==
            binding_hashes["writer_instances"], "writer binding drifted")
    require(contract["physical_saturn"] == "UNRUN",
            "physical Saturn result was overstated")
    build = (ROOT / "build.ps1").read_text()
    makefile = (ROOT / "makefile").read_text()
    main_source = (ROOT / "main.c").read_text()
    verify = (ROOT / "verify.ps1").read_text()
    require("HitKoPromotionBench" in build and
            "hit-ko-promotion-bench" in build,
            "dedicated HIT/KO target profile is missing")
    require("AVSP_HIT_KO_PROMOTION_BENCH" in makefile and
            "src/port_v2/combat/hit_ko/hit_ko.c" in makefile,
            "Saturn diagnostic bypasses the promoted interface")
    require("avsp_hit_ko_diagnostic_init" in main_source and
            "avsp_hit_ko_diagnostic_step" in main_source,
            "main target wiring bypasses the bounded diagnostic adapter")
    require("HitKoPromotionBench" in verify,
            "HIT/KO Target verification profile is missing")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--negative-control", action="store_true")
    args = parser.parse_args()
    contract = json.loads((HERE / "approved_contract.json").read_text())
    manifest_path = ROOT / contract["source_manifest"]
    manifest = json.loads(manifest_path.read_text())
    validate_manifest(contract, manifest)
    root_wsl = subprocess.run(
        ["wsl.exe", "wslpath", "-a", str(ROOT)], check=True,
        capture_output=True, text=True).stdout.strip()
    executable = "build/port_v2/combat/hit_ko/hit_ko_test"
    compile_source(root_wsl, "src/port_v2/combat/hit_ko/hit_ko.c", executable)
    for kind in ("hit", "ko"):
        first = run_trace(root_wsl, executable, kind)
        second = run_trace(root_wsl, executable, kind)
        require(first == second, f"{kind} deterministic repeat drifted")
        limits = contract[kind]
        expected = expected_trace(manifest, limits["first_sample"],
                                  limits["last_sample"])
        require(parse_trace(first) == expected,
                f"{kind} multi-frame source differential failed")
    negative = subprocess.run(
        ["wsl.exe", "sh", "-lc",
         f"cd '{root_wsl}' && ./{executable} --negative-prestate"],
        check=True, capture_output=True, text=True).stdout
    require(negative == "unsupported pre-state rejected\n",
            "unsupported source pre-state was accepted")
    if args.negative_control:
        source = (ROOT / "src/port_v2/combat/hit_ko/hit_ko.c").read_text()
        original = "runtime->actor.anim_record = AVSP_PORT_V2_HIT_ANIM_RECORD;"
        mutation = ("runtime->actor.anim_record = "
                    "AVSP_PORT_V2_HIT_RECOVERY_ANIM_RECORD;")
        require(source.count(original) == 1, "mutation anchor drifted")
        mutated = source.replace(original, mutation)
        mutated_path = ROOT / "build/port_v2/combat/hit_ko/hit_ko_mutated.c"
        mutated_path.write_text(mutated)
        mutated_executable = "build/port_v2/combat/hit_ko/hit_ko_mutated"
        compile_source(root_wsl,
                       "build/port_v2/combat/hit_ko/hit_ko_mutated.c",
                       mutated_executable)
        wrong = parse_trace(run_trace(root_wsl, mutated_executable, "hit"))
        expected = expected_trace(manifest, contract["hit"]["first_sample"],
                                  contract["hit"]["last_sample"])
        require(wrong != expected,
                "constant-substitution negative control was not rejected")
        print("V2-B1 constant-substitution negative control: REJECTED")
    print("V2-B1 exact HIT/KO host differential: PASS")


if __name__ == "__main__":
    main()
