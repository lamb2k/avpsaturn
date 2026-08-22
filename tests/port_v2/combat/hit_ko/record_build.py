#!/usr/bin/env python3
"""Bind one HitKoPromotionBench image to source and regression locks."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def sha(path, normalized=False):
    data = path.read_bytes()
    if normalized:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    args = parser.parse_args()
    inventory = json.loads((HERE / "inventory.json").read_text())
    contract = json.loads((HERE / "approved_contract.json").read_text())
    profile = (ROOT / "build/last_compile_profile.txt").read_text().strip()
    manifest = dict(line.split("=", 1) for line in
                    (ROOT / "build/hardware_release_manifest.txt").read_text(
                        encoding="ascii").splitlines() if "=" in line)
    if profile != inventory["compile_profile"]:
        raise ValueError(f"HIT/KO compile profile drifted: {profile}")
    if manifest.get("profile") != inventory["manifest_profile"]:
        raise ValueError("HIT/KO manifest profile drifted")
    source_manifest = ROOT / contract["source_manifest"]
    if sha(source_manifest, normalized=True) != contract["source_manifest_sha256"]:
        raise ValueError("accepted HIT/KO source manifest drifted")
    locks = {}
    for relative in ("tests/port_v2/player/approved_contract.json",
                     "tests/port_v2/enemy/approved_contract.json",
                     "data/avsp_collision.json"):
        locks[relative] = sha(ROOT / relative)
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
        "source_manifest_sha256": contract["source_manifest_sha256"],
        "approved_lock_sha256": locks,
        "physical_saturn": "UNRUN", "result": "PASS"
    }
    output = ROOT / f"build/port_v2/combat/hit_ko/run-{args.run}/build.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="ascii")
    print(f"recorded {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
