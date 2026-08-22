#!/usr/bin/env python3
"""Bind one CollisionSalvageBench image to source and approval locks."""

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
        raise ValueError(f"collision compile profile drifted: {profile}")
    if manifest.get("profile") != inventory["manifest_profile"]:
        raise ValueError("collision manifest profile drifted")
    if sha(ROOT / "data/avsp_collision.json") != contract["source_report_sha256"]:
        raise ValueError("tracked collision source report drifted")
    if sha(ROOT / "generated/avsp_collision.h") != contract["generated_header_sha256"]:
        raise ValueError("generated collision table drifted")
    for relative, expected in contract["approved_lock_sha256"].items():
        if sha(ROOT / relative) != expected:
            raise ValueError(f"approved regression lock changed: {relative}")
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
        "source_report_sha256": contract["source_report_sha256"],
        "generated_header_sha256": contract["generated_header_sha256"],
        "approved_lock_sha256": contract["approved_lock_sha256"],
        "physical_saturn": "UNRUN", "result": "PASS"
    }
    output = ROOT / f"build/port_v2/collision_bench/run-{args.run}/build.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="ascii")
    print(f"recorded {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
