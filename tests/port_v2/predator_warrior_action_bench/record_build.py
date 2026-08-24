#!/usr/bin/env python3
"""Bind a SALVAGE-10 diagnostic image to source-oracle identities."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    args = parser.parse_args()
    inventory = json.loads((HERE / "inventory.json").read_text())
    contract = json.loads((HERE / "contract.json").read_text())
    profile = (ROOT / "build/last_compile_profile.txt").read_text().strip()
    manifest = dict(line.split("=", 1) for line in
                    (ROOT / "build/hardware_release_manifest.txt").read_text(
                        encoding="ascii").splitlines() if "=" in line)
    if profile != inventory["compile_profile"]:
        raise ValueError(f"SALVAGE-10 compile profile drifted: {profile}")
    if manifest.get("profile") != inventory["manifest_profile"]:
        raise ValueError("SALVAGE-10 manifest profile drifted")
    if sha(ROOT / "data/oracle04_predator_warrior_control_actions.json") != contract["oracle04_sha256"]:
        raise ValueError("ORACLE-04 identity drifted")
    if sha(ROOT / "data/oracle06_round1_encounter.json") != contract["oracle06_sha256"]:
        raise ValueError("ORACLE-06 identity drifted")
    artifacts = {}
    for key, relative in {
        "game_iso": "game.iso", "game_cue": "game.cue",
        "game_elf": "game.elf", "game_map": "game.map",
        "manifest": "build/hardware_release_manifest.txt"
    }.items():
        target = ROOT / relative
        artifacts[key] = {"path": relative, "bytes": target.stat().st_size,
                          "sha256": sha(target)}
    if manifest["iso_sha256"] != artifacts["game_iso"]["sha256"]:
        raise ValueError("manifest/ISO identity mismatch")
    report = {
        "schema": 1, "task_id": inventory["task_id"],
        "card_profile": inventory["card_profile"],
        "source_commit": git("rev-parse", "HEAD"),
        "source_tree": git("write-tree"),
        "compile_profile": profile, "manifest_profile": manifest["profile"],
        "artifacts": artifacts,
        "oracle04_sha256": contract["oracle04_sha256"],
        "oracle06_sha256": contract["oracle06_sha256"],
        "physical_saturn": "UNRUN", "result": "PASS"
    }
    output = ROOT / f"build/port_v2/predator_warrior_action_bench/run-{args.run}/build.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(f"recorded {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
