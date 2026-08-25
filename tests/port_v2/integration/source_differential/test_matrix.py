#!/usr/bin/env python3
"""QA-12 host/Saturn cadence-1 differential and scenario matrix."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
FIELDS = ("frame","input_mask","player_x","player_lane","player_health","player_state",
          "player_selector","player_attack_active","player_facing",
          "player_animation_record","player_assembly","player_screen_y",
          "alien_x","alien_lane","alien_health","alien_state","alien_inner",
          "alien_action","alien_facing","alien_animation_record","alien_assembly",
          "alien_screen_y","alien_rng","player_contact","alien_contact","player_damage",
          "alien_damage","attack_miss","encounter_state","route_unlocked",
          "continued_after_unlock","camera_world_x","failures")
EXPECTED_CANDIDATE = "e23733545af0bebe1f9ae26c4f391a9080c7006f"
EXPECTED_TREE = "ebc54deb94a0d5c6a826b63ab9e3b36ec9b70828"
EXPECTED_ISO = "8e20cb7e8c482035578422d8d1734cd9713adfc525ac5bf7c6dd8eade386bea8"


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def translated(path: Path) -> str:
    return subprocess.run(["wsl.exe", "wslpath", "-a", str(path).replace("\\", "/")],
                          check=True, capture_output=True, text=True).stdout.strip()


root_wsl = translated(ROOT)
binary_wsl = translated(ROOT / "build/port_v2/qa12/qa12_matrix")
command = (
    f"cd '{root_wsl}' && mkdir -p build/port_v2/qa12 && "
    "gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 "
    "-I src/port_v2/gameplay/player_action "
    "-I src/port_v2/gameplay/street_alien_ai "
    "-I src/port_v2/integration/live_encounter "
    "src/port_v2/gameplay/player_action/player_action.c "
    "src/port_v2/gameplay/street_alien_ai/street_alien_ai.c "
    "src/port_v2/integration/live_encounter/live_encounter.c "
    "src/port_v2/combat/hit_ko/hit_ko.c "
    "src/port_v2/integration/combat/combat.c "
    "src/port_v2/integration/player_enemy/player_enemy.c "
    "src/port_v2/player/player.c src/port_v2/enemy/enemy.c "
    "avsp_actor.c avsp_collision.c "
    "tests/port_v2/integration/source_differential/qa12_matrix.c "
    f"-o '{binary_wsl}' && '{binary_wsl}'")
run = subprocess.run(["wsl.exe", "bash", "-lc", command],
                     capture_output=True, text=True)
require(run.returncode == 0, f"QA-12 C matrix failed:\n{run.stdout}\n{run.stderr}")

main_source = (ROOT / "main.c").read_text()
require("live_encounter_frame.player_screen_y + 200 - JO_TV_HEIGHT / 2 - 88 +"
        in main_source and
        "live_encounter_frame.alien_screen_y + 200 - JO_TV_HEIGHT / 2 - 88;"
        in main_source,
        "source screen-Y was not converted through the captured cel pivot")

cases = {}
host_samples = []
for line in run.stdout.splitlines():
    parts = line.split(",")
    if parts[0] == "CASE":
        cases[parts[1]] = parts[2]
    elif parts[0] == "FRAME":
        values = [int(value) for value in parts[1:]]
        require(len(values) == len(FIELDS), "host cadence field count drift")
        host_samples.append(dict(zip(FIELDS, values)))
require(len(cases) >= 30 and all(value == "PASS" for value in cases.values()),
        f"scenario matrix incomplete: {cases}")
require(len(host_samples) == 471, "host cadence ledger is not 471 frames")

base = ROOT / "build/port_v2/live_encounter"
builds = [json.loads((base / f"run-{index}/build.json").read_text()) for index in (1, 2)]
reads = [json.loads((base / f"run-{index}/readback.json").read_text()) for index in (1, 2)]
for build, read in zip(builds, reads):
    require(build["source_commit"] == read["source_commit"] == EXPECTED_CANDIDATE,
            "Saturn evidence candidate drift")
    require(build["source_tree"] == EXPECTED_TREE, "Saturn source tree drift")
    require(read["iso_sha256"] == EXPECTED_ISO, "Saturn ISO drift")
    require(read["samples"] == host_samples, "host/Saturn cadence-1 divergence")
require(reads[0]["samples"] == reads[1]["samples"] and
        reads[0]["state"] == reads[1]["state"], "paired Saturn nondeterminism")


def invariant(samples: list[dict]) -> bool:
    if len(samples) != 471 or any(sample["frame"] != index
                                  for index, sample in enumerate(samples)):
        return False
    if any(sample["failures"] != 0 for sample in samples):
        return False
    if any(sample["player_assembly"] == 0 for sample in samples):
        return False
    if any(sample["alien_state"] != 0 and sample["alien_assembly"] == 0
           for sample in samples):
        return False
    if any(sample["player_lane"] >= 320 and sample["player_x"] > 1091
           for sample in samples):
        return False
    if any(sample["player_contact"] and
           (not sample["player_attack_active"] or sample["alien_damage"] not in (9, 24, 31))
           for sample in samples):
        return False
    return True


require(invariant(host_samples), "accepted host/Saturn ledger violates QA invariants")
def differential(samples: list[dict]) -> bool:
    return invariant(samples) and samples == host_samples


mutations = []
for label, frame, field, value in (
    ("wrong-facing", 10, "player_facing", 0),
    ("weapon-discontinuity", 200, "player_assembly", 0),
    ("wall-traversal", 10, "player_x", 1200),
    ("alien-family-substitution", 100, "alien_assembly", 0),
    ("unsupported-contact", 0, "player_contact", 1),
    ("runtime-failure", 0, "failures", 1),
):
    changed = [dict(sample) for sample in host_samples]
    changed[frame][field] = value
    require(not differential(changed), f"QA mutation passed: {label}")
    mutations.append(label)

semantic = json.dumps(host_samples, sort_keys=True, separators=(",", ":")).encode("ascii")
summary = {
    "candidate": EXPECTED_CANDIDATE,
    "source_tree": EXPECTED_TREE,
    "iso_sha256": EXPECTED_ISO,
    "scenario_count": len(cases),
    "scenarios": sorted(cases),
    "cadence_frames": len(host_samples),
    "cadence_sha256": hashlib.sha256(semantic).hexdigest(),
    "paired_saturn_exact": True,
    "host_saturn_exact": True,
    "rejected_qa_mutations": mutations,
}
print(json.dumps(summary, sort_keys=True))
