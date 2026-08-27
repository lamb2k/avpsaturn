#!/usr/bin/env python3
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True,
                          capture_output=True, text=True).stdout.strip()
parser = argparse.ArgumentParser(); parser.add_argument("--run", type=int, choices=(1,2), required=True)
args = parser.parse_args()
inventory = json.loads((HERE / "inventory.json").read_text())
profile = (ROOT / "build/last_compile_profile.txt").read_text().strip()
manifest = dict(line.split("=",1) for line in (ROOT / "build/hardware_release_manifest.txt").read_text(encoding="ascii").splitlines() if "=" in line)
if profile != inventory["compile_profile"] or manifest.get("profile") != inventory["manifest_profile"]:
    raise ValueError("INTEGRATE-04A build profile drifted")
artifacts = {}
for key, relative in {"game_iso":"game.iso", "game_cue":"game.cue", "game_elf":"game.elf",
                      "game_map":"game.map", "manifest":"build/hardware_release_manifest.txt",
                      "tile_archive":"build/avsp_cd/SPR4/TILES.BIN"}.items():
    target = ROOT / relative
    artifacts[key] = {"path":relative, "bytes":target.stat().st_size, "sha256":sha(target)}
if manifest["iso_sha256"] != artifacts["game_iso"]["sha256"]:
    raise ValueError("manifest/ISO identity mismatch")
report = {"schema":1, "task_id":inventory["task_id"], "card_profile":inventory["card_profile"],
          "source_commit":git("rev-parse","HEAD"), "source_tree":git("write-tree"),
          "compile_profile":profile, "manifest_profile":manifest["profile"],
          "artifacts":artifacts, "physical_saturn":"UNRUN", "result":"PASS"}
output = ROOT / inventory["build_root"] / f"run-{args.run}/build.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="ascii")
print(f"recorded {output.relative_to(ROOT)}")
