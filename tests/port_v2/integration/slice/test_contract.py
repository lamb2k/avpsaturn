#!/usr/bin/env python3
"""Strict deterministic and approved-lock checks for INTEGRATE-03."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_and_run(argument: str = "") -> str:
    root_wsl = subprocess.run(
        ["wsl.exe", "wslpath", "-a", str(ROOT)], check=True,
        capture_output=True, text=True).stdout.strip()
    output = "build/port_v2/integration/slice/slice_test"
    sources = (
        "src/port_v2/player/player.c src/port_v2/enemy/enemy.c "
        "src/port_v2/integration/player_enemy/player_enemy.c "
        "avsp_collision.c src/port_v2/combat/hit_ko/hit_ko.c "
        "src/port_v2/integration/combat/combat.c "
        "src/port_v2/camera/camera.c src/port_v2/stage/stage.c "
        "src/port_v2/hud/hud.c src/port_v2/audio/pcm/pcm.c "
        "src/port_v2/audio/cdda/cdda.c src/port_v2/residency/residency.c "
        "src/port_v2/integration/slice/slice.c "
        "tests/port_v2/integration/slice/slice_test.c"
    )
    command = (
        f"cd '{root_wsl}' && mkdir -p build/port_v2/integration/slice && "
        "gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 -I. "
        f"{sources} -o {output} && ./{output} {argument}")
    return subprocess.run(
        ["wsl.exe", "sh", "-lc", command], check=True,
        capture_output=True, text=True).stdout


def validate_approved_locks() -> None:
    contract = json.loads((HERE / "approved_locks.json").read_text())
    for lock in contract["approved_contracts"]:
        require(sha256(ROOT / lock["path"]) == lock["sha256"],
                f"approved lock drifted: {lock['path']}")
    require(contract["physical_saturn"] == "UNRUN",
            "physical Saturn evidence was overstated")
    header = (ROOT / "src/port_v2/integration/slice/slice.h").read_text()
    source = (ROOT / "src/port_v2/integration/slice/slice.c").read_text()
    main_source = (ROOT / "main.c").read_text()
    require("jo/" not in header.lower() + source.lower() and
            "sgl" not in header.lower() + source.lower(),
            "slice core depends on Jo/SGL")
    require("fallback_used" in header and "fallback_used" in source,
            "fallback readback is missing")
    require("frame_counter < street_frames" in main_source and
            "frame_counter : street_frames - 1" in main_source,
            "playable slice permits the captured stage loop to reset mid-scene")


def main() -> None:
    validate_approved_locks()
    first = compile_and_run()
    second = compile_and_run()
    require(first == second, "playable slice replay drifted")
    require(first == (
        "F3000 A2 C4 HP-1 HIT1 KO1 HUD4 PCM1/1 CDDA1/1 "
        "LATE1 NEG1 SCROLL6 FALLBACK0 CANARY1\n"
        "Playable slice deterministic integration: PASS\n"),
        "playable slice semantic contract drifted")
    negative = compile_and_run("--negative-control")
    require(negative == "Playable slice negative controls: PASS\n",
            "dependency-order, illegal-read, or canary control failed")
    mutated = (ROOT / "src/port_v2/stage/stage.c").read_text().replace(
        "    4,\n    6,", "    5,\n    6,", 1)
    require(mutated != (ROOT / "src/port_v2/stage/stage.c").read_text(),
            "stage mutation anchor drifted")
    require("actor_priority != approved->actor_priority" in mutated,
            "stage approval validation disappeared")
    print("INTEGRATE-03 playable slice host contract: PASS")


if __name__ == "__main__":
    main()
