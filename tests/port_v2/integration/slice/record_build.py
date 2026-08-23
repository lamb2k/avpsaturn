#!/usr/bin/env python3
"""Bind one playable-slice image to its promoted component locks."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
from verify_iso_file import read_iso_path  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def linked_high_water() -> dict:
    nm = ROOT / ".deps/joengine/Compiler/WINDOWS/sh-elf/bin/nm.exe"
    output = subprocess.run([str(nm), "--target=coff-sh", str(ROOT / "game.elf")],
                            check=True, capture_output=True, text=True).stdout
    bend = next(int(line.split()[0], 16) for line in output.splitlines()
                if len(line.split()) == 3 and line.split()[2] == "__bend")
    limit = 0x060C0000
    if bend > limit:
        raise ValueError("playable slice exceeds work RAM")
    return {"bend": f"0x{bend:08x}", "limit": f"0x{limit:08x}",
            "headroom_bytes": limit - bend, "status": "MEASURED"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    parser.add_argument("--release", action="store_true")
    args = parser.parse_args()
    inventory = json.loads((HERE / "inventory.json").read_text())
    locks = json.loads((HERE / "approved_locks.json").read_text())
    profile = (ROOT / "build/last_compile_profile.txt").read_text().strip()
    manifest = dict(line.split("=", 1) for line in
                    (ROOT / "build/hardware_release_manifest.txt").read_text(
                        encoding="ascii").splitlines() if "=" in line)
    expected_compile = (inventory["release_compile_profile"] if args.release
                        else inventory["compile_profile"])
    expected_manifest = (inventory["release_manifest_profile"] if args.release
                         else inventory["manifest_profile"])
    if profile != expected_compile or manifest.get("profile") != expected_manifest:
        raise ValueError("playable-slice build profile drifted")
    for lock in locks["approved_contracts"]:
        if sha(ROOT / lock["path"]) != lock["sha256"]:
            raise ValueError(f"approved lock drifted: {lock['path']}")
    image = (ROOT / "game.iso").read_bytes()
    members = {}
    for name in inventory["required_iso_members"]:
        payload = read_iso_path(image, name)
        members[name] = {"bytes": len(payload),
                         "sha256": hashlib.sha256(payload).hexdigest()}
    player = json.loads((ROOT / "tests/port_v2/player/approved_contract.json").read_text())
    enemy = json.loads((ROOT / "tests/port_v2/enemy/approved_contract.json").read_text())
    stage = json.loads((ROOT / "tests/port_v2/camera_stage/approved_contract.json").read_text())
    hud = json.loads((ROOT / "tests/port_v2/hud/approved_contract.json").read_text())
    cdda = json.loads((ROOT / "tests/port_v2/cdda_residency/approved_contract.json").read_text())
    expected = dict(player["asset_sha256"])
    expected["/SPR4/TILES.BIN"] = enemy["tile_archive_sha256"]
    expected["/SPR4/COMBAT.BIN"] = "070443fb8dd7c6791fd846fb95cce100e89eee301ba9ad6dffeea581f72cf40c"
    expected["/ST1/STRIPS.BIN"] = stage["fixture"]["strips_bin_sha256"]
    expected.update(hud["payload_sha256"])
    expected["/DIAG/RESCHK.BIN"] = cdda["fixture"]["sha256"]
    actual = {name: value["sha256"] for name, value in members.items()}
    if actual != expected:
        raise ValueError("playable-slice ISO member identity drifted")
    if sha(ROOT / "stage1_audio.wav") != cdda["track_audio"]["sha256"]:
        raise ValueError("Track 2 identity drifted")
    artifacts = {}
    for key, relative in {"game_iso": "game.iso", "game_cue": "game.cue",
                          "stage1_audio": "stage1_audio.wav",
                          "game_elf": "game.elf", "game_map": "game.map",
                          "manifest": "build/hardware_release_manifest.txt"}.items():
        path = ROOT / relative
        artifacts[key] = {"path": relative, "bytes": path.stat().st_size,
                          "sha256": sha(path)}
    if manifest["iso_sha256"] != artifacts["game_iso"]["sha256"]:
        raise ValueError("manifest and playable-slice ISO disagree")
    report = {"schema": 1, "task_id": inventory["task_id"],
              "card_profile": inventory["card_profile"],
              "source_commit": git("rev-parse", "HEAD"),
              "source_tree": git("rev-parse", "HEAD^{tree}"),
              "compile_profile": profile, "manifest_profile": manifest["profile"],
              "exact_normal_release": args.release,
              "linked_work_ram_high_water": linked_high_water(),
              "iso_members": members, "artifacts": artifacts,
              "physical_saturn": "UNRUN", "result": "PASS"}
    output = ROOT / inventory["build_root"] / f"run-{args.run}/build.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"recorded {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
