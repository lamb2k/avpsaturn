#!/usr/bin/env python3
"""Record one unchanged OldBuildBaseline/StreetTest build."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
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
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], check=True, capture_output=True,
        text=True).stdout.strip()


def manifest() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in (ROOT / "build/hardware_release_manifest.txt").read_text(
            encoding="ascii").splitlines():
        if not line:
            continue
        if "=" not in line:
            raise ValueError(f"malformed manifest line: {line!r}")
        key, value = line.split("=", 1)
        if key in values:
            raise ValueError(f"duplicate manifest key: {key}")
        values[key] = value
    return values


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    args = parser.parse_args()

    inventory_path = HERE / "inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    compile_profile = (ROOT / "build/last_compile_profile.txt").read_text(
        encoding="ascii").strip()
    release_manifest = manifest()
    normalization_path = (
        ROOT / f"build/port_v2/old_build_baseline/run-{args.run}/iso-normalization.json")
    normalization = json.loads(normalization_path.read_text(encoding="ascii"))
    if compile_profile != inventory["underlying_compile_profile"]:
        raise ValueError(f"unexpected compile profile: {compile_profile}")
    if release_manifest.get("profile") != inventory["underlying_manifest_profile"]:
        raise ValueError(f"unexpected manifest profile: {release_manifest.get('profile')}")

    image_path = ROOT / "game.iso"
    image = image_path.read_bytes()
    members: dict[str, dict[str, object]] = {}
    for iso_path, relative in inventory["required_iso_members"].items():
        local = ROOT / relative
        payload = read_iso_path(image, iso_path)
        expected = local.read_bytes()
        if payload != expected:
            raise ValueError(f"{iso_path} differs from {relative}")
        members[iso_path] = {
            "source": relative,
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }

    artifacts = {}
    for name, relative in {
        "game_iso": "game.iso",
        "game_cue": "game.cue",
        "game_elf": "game.elf",
        "game_map": "game.map",
        "hardware_manifest": "build/hardware_release_manifest.txt",
        "compile_profile": "build/last_compile_profile.txt",
        "street_fixture": "build/rp4_fixture/STRIPS.BIN",
    }.items():
        path = ROOT / relative
        artifacts[name] = {
            "path": relative,
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }

    generated_inputs: dict[str, dict[str, object]] = {}
    include_pattern = re.compile(r'^#include "(generated/[^"]+)"', re.MULTILINE)
    for source in sorted(ROOT.glob("*.c")):
        for relative in include_pattern.findall(source.read_text(encoding="ascii")):
            path = ROOT / relative
            if not path.is_file():
                raise ValueError(f"required ignored generated input is missing: {relative}")
            generated_inputs[relative] = {
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }

    ignored_build_inputs: dict[str, dict[str, object]] = {}
    for relative in ("loader/loader.c", "loader/loader.linker",
                     "loader/trampoline.s", "tools/build_loader_ip.py"):
        path = ROOT / relative
        if not path.is_file():
            raise ValueError(f"required local build input is missing: {relative}")
        ignored_build_inputs[relative] = {
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }

    status = git("status", "--porcelain", "--untracked-files=no")
    report = {
        "schema": 1,
        "task_id": inventory["task_id"],
        "card_profile": inventory["card_profile"],
        "source_commit": git("rev-parse", "HEAD"),
        "source_tree": git("rev-parse", "HEAD^{tree}"),
        "tracked_source_dirty": bool(status),
        "compile_profile": compile_profile,
        "manifest_profile": release_manifest["profile"],
        "manifest_iso_sha256": release_manifest["iso_sha256"],
        "inventory_sha256": sha256(inventory_path),
        "iso_normalization": normalization,
        "artifacts": artifacts,
        "generated_inputs": dict(sorted(generated_inputs.items())),
        "ignored_build_inputs": ignored_build_inputs,
        "required_iso_members": members,
        "result": "PASS",
        "evidence_tier": "BUILD_ONLY",
        "physical_saturn": "UNRUN",
    }
    if not re.fullmatch(r"[0-9a-f]{40}", report["source_commit"]):
        raise ValueError("source commit is not pinned")
    if report["manifest_iso_sha256"] != artifacts["game_iso"]["sha256"]:
        raise ValueError("hardware manifest ISO identity disagrees with game.iso")

    output = ROOT / f"build/port_v2/old_build_baseline/run-{args.run}/build.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="ascii", newline="\n")
    print(f"recorded {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
