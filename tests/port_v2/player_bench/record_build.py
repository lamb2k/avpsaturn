#!/usr/bin/env python3
"""Bind one PlayerSalvageBench image to its profile and player asset members."""

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
    args = parser.parse_args()
    inventory = json.loads((HERE / "inventory.json").read_text(encoding="utf-8"))
    actual_profile = (ROOT / "build/last_compile_profile.txt").read_text(
        encoding="ascii").strip()
    release_manifest = manifest()
    if actual_profile != inventory["compile_profile"]:
        raise ValueError(f"compile profile is {actual_profile!r}")
    if release_manifest.get("profile") != inventory["manifest_profile"]:
        raise ValueError(f"manifest profile is {release_manifest.get('profile')!r}")
    image = (ROOT / "game.iso").read_bytes()
    members = {}
    for iso_path in inventory["required_iso_members"]:
        payload = read_iso_path(image, iso_path)
        if not payload:
            raise ValueError(f"empty player asset member: {iso_path}")
        members[iso_path] = {"bytes": len(payload),
                             "sha256": hashlib.sha256(payload).hexdigest()}
    artifacts = {}
    for name, relative in {
        "game_iso": "game.iso", "game_cue": "game.cue", "game_elf": "game.elf",
        "game_map": "game.map", "hardware_manifest": "build/hardware_release_manifest.txt",
        "compile_profile": "build/last_compile_profile.txt",
    }.items():
        path = ROOT / relative
        artifacts[name] = {"path": relative, "bytes": path.stat().st_size,
                           "sha256": sha256(path)}
    report = {
        "schema": 1, "task_id": inventory["task_id"],
        "card_profile": inventory["card_profile"],
        "source_commit": git("rev-parse", "HEAD"),
        "source_tree": git("rev-parse", "HEAD^{tree}"),
        "compile_profile": actual_profile,
        "manifest_profile": release_manifest["profile"],
        "manifest_iso_sha256": release_manifest["iso_sha256"],
        "artifacts": artifacts, "player_asset_members": members,
        "physical_saturn": "UNRUN", "result": "PASS",
    }
    if report["manifest_iso_sha256"] != artifacts["game_iso"]["sha256"]:
        raise ValueError("manifest and ISO identities disagree")
    output = ROOT / f"build/port_v2/player_bench/run-{args.run}/build.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="ascii", newline="\n")
    print(f"recorded {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
