#!/usr/bin/env python3
"""Record a CombatIntegrationBench build and approved asset locks."""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
from verify_iso_file import read_iso_path


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
    player = json.loads((ROOT / "tests/port_v2/player/approved_contract.json").read_text())
    enemy = json.loads((ROOT / "tests/port_v2/enemy/approved_contract.json").read_text())
    overlay = json.loads((HERE / "tile_overlay_contract.json").read_text())
    profile = (ROOT / "build/last_compile_profile.txt").read_text().strip()
    manifest = dict(line.split("=", 1) for line in
                    (ROOT / "build/hardware_release_manifest.txt").read_text(
                        encoding="ascii").splitlines() if "=" in line)
    if profile != inventory["compile_profile"]:
        raise ValueError(f"combat compile profile drifted: {profile}")
    if manifest.get("profile") != inventory["manifest_profile"]:
        raise ValueError("combat manifest profile drifted")
    image = (ROOT / "game.iso").read_bytes()
    members = {}
    for name in inventory["required_iso_members"]:
        payload = read_iso_path(image, name)
        members[name] = {"bytes": len(payload),
                         "sha256": hashlib.sha256(payload).hexdigest()}
    expected = dict(player["asset_sha256"])
    expected["/SPR4/TILES.BIN"] = enemy["tile_archive_sha256"]
    expected["/SPR4/COMBAT.BIN"] = overlay["archive_sha256"]
    if {name: value["sha256"] for name, value in members.items()} != expected:
        raise ValueError("combat image changed an approved component asset")
    artifacts = {}
    for key, relative in {
        "game_iso": "game.iso", "game_cue": "game.cue",
        "game_elf": "game.elf", "game_map": "game.map",
        "manifest": "build/hardware_release_manifest.txt"
    }.items():
        path = ROOT / relative
        artifacts[key] = {"path": relative, "bytes": path.stat().st_size,
                          "sha256": sha(path)}
    if manifest["iso_sha256"] != artifacts["game_iso"]["sha256"]:
        raise ValueError("manifest and combat ISO identities disagree")
    report = {
        "schema": 1, "task_id": inventory["task_id"],
        "card_profile": inventory["card_profile"],
        "source_commit": git("rev-parse", "HEAD"),
        "source_tree": git("rev-parse", "HEAD^{tree}"),
        "compile_profile": profile, "manifest_profile": manifest["profile"],
        "artifacts": artifacts, "asset_members": members,
        "physical_saturn": "UNRUN", "result": "PASS"
    }
    output = ROOT / inventory["build_root"] / f"run-{args.run}/build.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="ascii")
    print(f"recorded {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
