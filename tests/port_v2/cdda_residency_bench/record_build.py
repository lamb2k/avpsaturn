#!/usr/bin/env python3
"""Bind one CddaResidencySalvageBench image to its manifest and locks."""

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


def release_manifest() -> dict[str, str]:
    result = {}
    for line in (ROOT / "build/hardware_release_manifest.txt").read_text(
            encoding="ascii").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            result[key] = value
    return result


def linked_high_water() -> dict[str, int | str]:
    nm = ROOT / ".deps/joengine/Compiler/WINDOWS/sh-elf/bin/nm.exe"
    output = subprocess.run([str(nm), "--target=coff-sh", str(ROOT / "game.elf")],
                            check=True, capture_output=True, text=True).stdout
    bend = None
    for line in output.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[2] == "__bend":
            bend = int(parts[0], 16)
            break
    if bend is None:
        raise ValueError("linked __bend high-water is missing")
    limit = 0x060C0000
    if bend > limit:
        raise ValueError("CDDA/residency profile exceeds work RAM")
    return {"bend": f"0x{bend:08x}", "limit": f"0x{limit:08x}",
            "headroom_bytes": limit - bend, "status": "MEASURED"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    args = parser.parse_args()
    inventory = json.loads((HERE / "inventory.json").read_text(encoding="utf-8"))
    contract = json.loads((HERE / "contract.json").read_text(encoding="utf-8"))
    profile = (ROOT / "build/last_compile_profile.txt").read_text(
        encoding="ascii").strip()
    release = release_manifest()
    if profile != inventory["compile_profile"] or \
            release.get("profile") != inventory["manifest_profile"]:
        raise ValueError("CDDA/residency build profile drifted")
    image = (ROOT / "game.iso").read_bytes()
    members = {}
    for name in inventory["required_iso_members"]:
        payload = read_iso_path(image, name)
        members[name] = {"bytes": len(payload),
                         "sha256": hashlib.sha256(payload).hexdigest()}
    fixture = contract["fixture"]
    if members[fixture["iso_path"]] != {
            "bytes": fixture["bytes"], "sha256": fixture["sha256"]}:
        raise ValueError("CDDA residency fixture changed in the ISO")
    source_audio = ROOT / contract["source_audio"]["path"]
    staged_audio = ROOT / "stage1_audio.wav"
    if sha256(source_audio) != contract["source_audio"]["sha256"] or \
            sha256(staged_audio) != contract["source_audio"]["sha256"]:
        raise ValueError("Track 2 source/staged identity drifted")
    cue = (ROOT / "game.cue").read_text(encoding="ascii")
    for required in ('FILE "game.iso" BINARY', 'TRACK 01 MODE1/2048',
                     'FILE "stage1_audio.wav" WAVE', 'TRACK 02 AUDIO'):
        if required not in cue:
            raise ValueError(f"cue layout missing {required}")
    approved = {}
    for lock in contract["approved_contracts"]:
        actual = sha256(ROOT / lock["path"])
        if actual != lock["sha256"]:
            raise ValueError(f"approved lock changed: {lock['path']}")
        approved[lock["path"]] = actual
    artifacts = {}
    for key, relative in {
        "game_iso": "game.iso", "game_cue": "game.cue",
        "stage1_audio": "stage1_audio.wav", "game_elf": "game.elf",
        "game_map": "game.map",
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
        "linked_work_ram_high_water": linked_high_water(),
        "phase_owned_high_water": json.loads(
            (HERE / "phase_manifest.json").read_text(encoding="utf-8"))[
                "allocations"],
        "iso_members": members,
        "approved_contract_sha256": approved,
        "artifacts": artifacts,
        "physical_saturn": "UNRUN",
        "result": "PASS",
    }
    if report["manifest_iso_sha256"] != artifacts["game_iso"]["sha256"]:
        raise ValueError("hardware manifest and ISO identity disagree")
    output = ROOT / f"build/port_v2/cdda_residency_bench/run-{args.run}/build.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="ascii", newline="\n")
    print(f"recorded {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
