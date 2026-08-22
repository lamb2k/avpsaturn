#!/usr/bin/env python3
"""Bind an EnemyPromotionBench image to source and approved locks."""

import argparse, hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
from verify_iso_file import read_iso_path

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
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
                    (ROOT / "build/hardware_release_manifest.txt").read_text(encoding="ascii").splitlines()
                    if "=" in line)
    if profile != inventory["compile_profile"] or manifest.get("profile") != inventory["manifest_profile"]:
        raise ValueError("enemy promotion build profile drifted")
    image = (ROOT / "game.iso").read_bytes()
    payload = read_iso_path(image, "/SPR4/TILES.BIN")
    if hashlib.sha256(payload).hexdigest() != contract["tile_archive_sha256"]:
        raise ValueError("approved enemy tile archive changed")
    for relative, expected in contract["approved_lock_sha256"].items():
        if sha(ROOT / relative) != expected:
            raise ValueError(f"approved regression lock changed: {relative}")
    artifacts = {}
    for key, relative in {"game_iso":"game.iso", "game_cue":"game.cue", "game_elf":"game.elf",
                          "game_map":"game.map", "manifest":"build/hardware_release_manifest.txt"}.items():
        path = ROOT / relative
        artifacts[key] = {"path":relative, "bytes":path.stat().st_size, "sha256":sha(path)}
    if manifest["iso_sha256"] != artifacts["game_iso"]["sha256"]:
        raise ValueError("manifest/ISO identity mismatch")
    report = {"schema":1, "task_id":inventory["task_id"], "card_profile":inventory["card_profile"],
              "source_commit":git("rev-parse", "HEAD"), "source_tree":git("rev-parse", "HEAD^{tree}"),
              "compile_profile":profile, "manifest_profile":manifest["profile"], "artifacts":artifacts,
              "tile_archive":{"bytes":len(payload), "sha256":hashlib.sha256(payload).hexdigest()},
              "approved_lock_sha256":contract["approved_lock_sha256"],
              "physical_saturn":"UNRUN", "result":"PASS"}
    output = ROOT / inventory["build_root"] / f"run-{args.run}" / "build.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(f"recorded {output.relative_to(ROOT)}")

if __name__ == "__main__": main()
