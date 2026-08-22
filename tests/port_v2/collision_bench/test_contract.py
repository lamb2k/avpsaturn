#!/usr/bin/env python3
"""Strict host contract, deterministic repeat, source binding, and mutation."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_host(negative=False):
    root = subprocess.run(
        ["wsl.exe", "wslpath", "-a", str(ROOT)], check=True,
        capture_output=True, text=True).stdout.strip()
    output = "build/port_v2/collision_bench/collision_test"
    command = (
        f"cd '{root}' && mkdir -p build/port_v2/collision_bench && "
        "gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 -I. "
        "avsp_collision.c tests/port_v2/collision_bench/collision_bench.c "
        f"tests/port_v2/collision_bench/collision_test.c -o {output} && "
        f"./{output}" + (" --negative-control" if negative else ""))
    return subprocess.run(["wsl.exe", "sh", "-lc", command], check=True,
                          capture_output=True, text=True).stdout


def regenerate(run):
    output = ROOT / f"build/port_v2/collision_bench/decode-{run}"
    output.mkdir(parents=True, exist_ok=True)
    report = output / "collision.json"
    header = output / "collision.h"
    subprocess.run([
        "py.exe", "-3", "-B", str(ROOT / "tools/decode_avsp_collision.py"),
        "--rom", ".deps/mame/actorprobe/decrypted_program_2m.bin",
        "--census-workram", ".deps/mame/collision_probe/workram.bin",
        "--census-workram", ".deps/mame/collision_probe_boss/workram.bin",
        "--report", str(report), "--header", str(header),
        "--verify-deterministic"
    ], cwd=ROOT, check=True, capture_output=True, text=True)
    return json.loads(report.read_text()), header.read_text().replace("\r\n", "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--negative-control", action="store_true")
    args = parser.parse_args()
    contract = json.loads((HERE / "contract.json").read_text())
    report_path = ROOT / "data/avsp_collision.json"
    report = json.loads(report_path.read_text())
    assert sha(report_path) == contract["source_report_sha256"]
    assert sha(ROOT / "generated/avsp_collision.h") == contract["generated_header_sha256"]
    assert report["routines"]["overlap_test"] == "0x01D25E..0x01D312"
    assert report["routines"]["hit_apply"] == "0x01CFCA..0x01D036"
    family = next(item for item in report["families"]
                  if item["table_set"] == contract["table_set"])
    assert family["hurt_table"] == "0x130acc"
    assert family["attack_table"] == "0x130b4c"
    assert family["attack_entries"][1]["hit_value"] == contract["expected_hit_value"]
    private_inputs = [report["inputs"]["program_image"]]
    private_inputs.extend(report["inputs"]["census_workram"])
    for item in private_inputs:
        path = ROOT / item["path"]
        assert path.stat().st_size == item["bytes"]
        assert sha(path) == item["sha256"]
    for relative, expected in contract["approved_lock_sha256"].items():
        assert sha(ROOT / relative) == expected
    decode_first = regenerate(1)
    decode_second = regenerate(2)
    assert decode_first == decode_second
    assert decode_first[0] == report
    assert decode_first[1] == (ROOT / "generated/avsp_collision.h").read_text().replace("\r\n", "\n")
    first = run_host(False)
    second = run_host(False)
    assert first == second
    assert len(first.strip().splitlines()) == contract["expected_case_count"]
    if args.negative_control:
        negative = run_host(True)
        assert negative.endswith("negative control rejected\n")
    print("SALVAGE-03 collision contract: PASS")


if __name__ == "__main__":
    main()
