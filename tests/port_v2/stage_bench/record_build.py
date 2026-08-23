#!/usr/bin/env python3
"""Bind one CameraStageSalvageBench image to its stage/player locks."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
from verify_iso_file import read_iso_path  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def manifest() -> dict[str, str]:
    values = {}
    for line in (ROOT / "build/hardware_release_manifest.txt").read_text(
            encoding="ascii").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    parser.add_argument("--suite", choices=("stage_bench", "camera_stage"),
                        default="stage_bench")
    args = parser.parse_args()
    suite_here = ROOT / "tests/port_v2" / args.suite
    contract_name = ("stage_contract.json" if args.suite == "stage_bench" else
                     "approved_contract.json")
    inventory = json.loads((suite_here / "inventory.json").read_text(
        encoding="utf-8"))
    contract = json.loads((suite_here / contract_name).read_text(
        encoding="utf-8"))
    profile = (ROOT / "build/last_compile_profile.txt").read_text(
        encoding="ascii").strip()
    release = manifest()
    if profile != inventory["compile_profile"]:
        raise ValueError(f"compile profile is {profile!r}")
    if release.get("profile") != inventory["manifest_profile"]:
        raise ValueError(f"manifest profile is {release.get('profile')!r}")
    image = (ROOT / "game.iso").read_bytes()
    members = {}
    for name in inventory["required_iso_members"]:
        payload = read_iso_path(image, name)
        if not payload:
            raise ValueError(f"empty stage member: {name}")
        members[name] = {"bytes": len(payload),
                         "sha256": hashlib.sha256(payload).hexdigest()}
    if members["/ST1/STRIPS.BIN"]["sha256"] != \
            contract["fixture"]["strips_bin_sha256"]:
        raise ValueError("stale or substituted stage fixture in ISO")
    actual_player = {name: members[name]["sha256"]
                     for name in contract["approved_player_asset_sha256"]}
    if actual_player != contract["approved_player_asset_sha256"]:
        raise ValueError("stage build changed an approved player asset")
    artifacts = {}
    for key, relative in {
        "game_iso": "game.iso", "game_cue": "game.cue",
        "game_elf": "game.elf", "game_map": "game.map",
        "hardware_manifest": "build/hardware_release_manifest.txt",
        "compile_profile": "build/last_compile_profile.txt",
    }.items():
        path = ROOT / relative
        artifacts[key] = {"path": relative, "bytes": path.stat().st_size,
                          "sha256": sha256(path)}
    report = {
        "schema": 1, "task_id": inventory["task_id"],
        "card_profile": inventory["card_profile"],
        "source_commit": git("rev-parse", "HEAD"),
        "source_tree": git("rev-parse", "HEAD^{tree}"),
        "compile_profile": profile,
        "manifest_profile": release["profile"],
        "manifest_iso_sha256": release["iso_sha256"],
        "artifacts": artifacts, "iso_members": members,
        "physical_saturn": "UNRUN", "result": "PASS",
    }
    if report["manifest_iso_sha256"] != artifacts["game_iso"]["sha256"]:
        raise ValueError("manifest and ISO identities disagree")
    output = ROOT / f"build/port_v2/{args.suite}/run-{args.run}/build.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="ascii", newline="\n")
    print(f"recorded {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
