#!/usr/bin/env python3
"""Bind one EnemySalvageBench image to source and approved locks."""

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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    args = parser.parse_args()
    inventory = json.loads((HERE / "inventory.json").read_text())
    contract = json.loads((HERE / "enemy_contract.json").read_text())
    profile = (ROOT / "build/last_compile_profile.txt").read_text().strip()
    manifest = dict(line.split("=", 1) for line in
                    (ROOT / "build/hardware_release_manifest.txt").read_text(
                        encoding="ascii").splitlines() if "=" in line)
    if profile != inventory["compile_profile"] or manifest.get("profile") != inventory["manifest_profile"]:
        raise ValueError("enemy build profile drifted")
    image = (ROOT / "game.iso").read_bytes()
    payload = read_iso_path(image, "/SPR4/TILES.BIN")
    if hashlib.sha256(payload).hexdigest() != contract["tile_archive_sha256"]:
        raise ValueError("class-0x1F tile archive changed")
    for group in ("approved_lock_sha256", "local_build_dependency_sha256"):
        for relative, expected in contract[group].items():
            if sha256(ROOT / relative) != expected:
                raise ValueError(f"regression lock changed: {relative}")
    artifacts = {}
    for key, relative in {"game_iso":"game.iso", "game_cue":"game.cue",
                          "game_elf":"game.elf", "game_map":"game.map",
                          "manifest":"build/hardware_release_manifest.txt"}.items():
        path = ROOT / relative
        artifacts[key] = {"path": relative, "bytes": path.stat().st_size, "sha256": sha256(path)}
    report = {"schema":1, "task_id":inventory["task_id"],
              "card_profile":inventory["card_profile"], "source_commit":git("rev-parse","HEAD"),
              "source_tree":git("rev-parse","HEAD^{tree}"), "compile_profile":profile,
              "manifest_profile":manifest["profile"], "artifacts":artifacts,
              "tile_archive":{"bytes":len(payload), "sha256":hashlib.sha256(payload).hexdigest()},
              "approved_lock_sha256":contract["approved_lock_sha256"],
              "local_build_dependency_sha256":contract["local_build_dependency_sha256"],
              "physical_saturn":"UNRUN", "result":"PASS"}
    if manifest["iso_sha256"] != artifacts["game_iso"]["sha256"]:
        raise ValueError("manifest/ISO identity mismatch")
    output = ROOT / f"build/port_v2/enemy_bench/run-{args.run}/build.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(f"recorded {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
