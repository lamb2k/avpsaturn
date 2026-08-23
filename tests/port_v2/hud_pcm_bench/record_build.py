#!/usr/bin/env python3
"""Bind one HudPcmSalvageBench image to HUD/PCM and regression locks."""

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


APPROVED_PLAYER = {
    "/BG/CORRIDOR.TGA": "a931c606875e0a6d9d71f01e9cc1579d39ce9911ac1574f1aa2312db018bccf8",
    "/SPR4/PACT.RLE": "10d6e77394582ce3ce09018bce26d0389e39464ec85b00e920dada807049fe90",
    "/SPR4/PXI0.BIN": "3fe466467e5f01cadfd3cd4e5263da9ff3c943fab0e3de4517840935c5eb91a8",
    "/SPR4/PXI1.BIN": "c78b9e0676d903da8da846193706b51a07cf6daf567e884d647fa41fb583a14c",
}


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
    parser.add_argument("--suite", choices=("hud_pcm_bench", "hud"),
                        default="hud_pcm_bench")
    args = parser.parse_args()
    suite_here = ROOT / "tests/port_v2" / args.suite
    contract_name = ("hud_pcm_contract.json" if
                     args.suite == "hud_pcm_bench" else
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
            raise ValueError(f"empty HUD/PCM member: {name}")
        members[name] = {"bytes": len(payload),
                         "sha256": hashlib.sha256(payload).hexdigest()}
    for name, expected in contract["payload_sha256"].items():
        if members[name]["sha256"] != expected:
            raise ValueError(f"HUD/PCM payload changed: {name}")
    for name, expected in APPROVED_PLAYER.items():
        if members[name]["sha256"] != expected:
            raise ValueError(f"approved player payload changed: {name}")
    local_dependencies = {}
    for relative, expected in contract["local_build_dependency_sha256"].items():
        path = ROOT / relative
        actual = sha256(path)
        if actual != expected:
            raise ValueError(f"local build dependency changed: {relative}")
        local_dependencies[relative] = actual
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
        "schema": 1,
        "task_id": inventory["task_id"],
        "card_profile": inventory["card_profile"],
        "source_commit": git("rev-parse", "HEAD"),
        "source_tree": git("rev-parse", "HEAD^{tree}"),
        "compile_profile": profile,
        "manifest_profile": release["profile"],
        "manifest_iso_sha256": release["iso_sha256"],
        "artifacts": artifacts,
        "iso_members": members,
        "local_build_dependency_sha256": local_dependencies,
        "approved_stage_contract_sha256": sha256(
            ROOT / "tests/port_v2/stage_bench/stage_contract.json"),
        "physical_saturn": "UNRUN",
        "result": "PASS",
    }
    if report["manifest_iso_sha256"] != artifacts["game_iso"]["sha256"]:
        raise ValueError("manifest and ISO identities disagree")
    if report["approved_stage_contract_sha256"] != \
            contract["approved_stage_contract_sha256"]:
        raise ValueError("approved stage contract changed")
    if args.suite == "hud":
        approved = {}
        for lock in contract["approved_contracts"]:
            actual = sha256(ROOT / lock["path"])
            if actual != lock["sha256"]:
                raise ValueError(f"approved HUD contract changed: {lock['path']}")
            approved[lock["path"]] = actual
        report["approved_contract_sha256"] = approved
    output = ROOT / f"build/port_v2/{args.suite}/run-{args.run}/build.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="ascii", newline="\n")
    print(f"recorded {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
