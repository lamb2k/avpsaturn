#!/usr/bin/env python3
"""Evidence-bound host differential for INTEGRATE-02-COMBAT."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def normalized_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def compile_test(root_wsl: str, hit_ko_source: str, output: str) -> None:
    sources = (
        "src/port_v2/player/player.c src/port_v2/enemy/enemy.c "
        "src/port_v2/integration/player_enemy/player_enemy.c "
        "avsp_collision.c " + hit_ko_source + " "
        "src/port_v2/integration/combat/combat.c "
        "tests/port_v2/integration/combat/combat_test.c"
    )
    command = (
        f"cd '{root_wsl}' && mkdir -p build/port_v2/integration/combat && "
        "gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 -I. "
        "-Isrc/port_v2/combat/hit_ko "
        f"{sources} -o {output}"
    )
    subprocess.run(["wsl.exe", "sh", "-lc", command], check=True)


def run(root_wsl: str, executable: str, negative: bool = False) -> str:
    suffix = " --negative-control" if negative else ""
    command = f"cd '{root_wsl}' && ./{executable}{suffix}"
    return subprocess.run(["wsl.exe", "sh", "-lc", command], check=True,
                          capture_output=True, text=True).stdout


def validate_sources(contract: dict) -> None:
    for source in contract["source_files"].values():
        path = ROOT / source["path"]
        require(normalized_sha(path) == source["normalized_sha256"],
                f"accepted source identity drifted: {source['path']}")
    collision = json.loads((ROOT / contract["source_files"]["collision"]["path"]).read_text())
    player = next(item for item in collision["families"]
                  if item["table_set"] == contract["player_table_set"])
    enemy = next(item for item in collision["families"]
                 if item["table_set"] == contract["enemy_table_set"])
    require(player["observed"]["actor_slots"] == ["0xff8380"] and
            player["observed"]["actor_types"] == [0],
            "player collision-family ownership drifted")
    require(not enemy["hurt_entries"][contract["enemy_hurt_selector"]]["inactive"],
            "enemy hurt selector became inactive")
    damage = json.loads((ROOT / contract["source_files"]["damage"]["path"]).read_text())
    health = damage["actor"]["health_events"][:4]
    for index, event in enumerate(contract["events"]):
        attack = player["attack_entries"][event["attack_selector"]]
        require(attack["hit_value"] == event["hit_value"] and
                not attack["inactive"], "player attack record drifted")
        require(health[index] == {"frame": event["sample"],
                                  "from": event["health_before"],
                                  "to": event["health_after"]},
                "enemy health event drifted")
    require(contract["physical_saturn"] == "UNRUN",
            "physical Saturn evidence was overstated")
    build = (ROOT / "build.ps1").read_text()
    makefile = (ROOT / "makefile").read_text()
    main_source = (ROOT / "main.c").read_text()
    verify = (ROOT / "verify.ps1").read_text()
    require("CombatIntegrationBench" in build and
            "combat-integration-bench" in build,
            "dedicated combat target profile is missing")
    require("AVSP_COMBAT_INTEGRATION_BENCH" in makefile and
            "src/port_v2/integration/combat/combat.c" in makefile and
            "src/port_v2/combat/hit_ko/hit_ko.c" in makefile,
            "combat target bypasses an accepted interface")
    require("avsp_combat_diagnostic_step" in main_source and
            "avsp_diag_combat_transition_anim_record" in main_source,
            "Saturn combat diagnostic wiring is missing")
    require("CombatIntegrationBench" in verify,
            "combat Target verification profile is missing")


def validate_alignment_analysis(negative: bool) -> None:
    command = ["py.exe", "-3", "-B", str(HERE / "analyze_alignment.py")]
    if negative:
        command.append("--negative-control")
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    require("REPAIR-03 retained-MAME actor alignment fields: PASS" in result.stdout,
            "retained MAME alignment analysis failed")
    if negative:
        require("facing mutation: REJECTED" in result.stdout,
                "retained MAME facing mutation was not rejected")


def expected_lines(contract: dict) -> list[str]:
    kinds = {"DAMAGE": 2, "HIT": 3, "KO": 4}
    lines = []
    for event in contract["events"]:
        lines.append(
            f"{event['sample']},{event['attack_selector']},{kinds[event['kind']]},"
            f"1,{event['hit_value']},{event['health_before']},{event['health_after']}")
        if event["kind"] == "HIT":
            lines.append("T,5190,36,1,512,0,1233656,1024,63,0")
        elif event["kind"] == "KO":
            lines.append("T,5329,139,2,1536,0,1237608,6,-1,0")
    lines.append("Combat integration contract: PASS")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--negative-control", action="store_true")
    args = parser.parse_args()
    contract = json.loads((HERE / "approved_contract.json").read_text())
    validate_sources(contract)
    validate_alignment_analysis(args.negative_control)
    root_wsl = subprocess.run(
        ["wsl.exe", "wslpath", "-a", str(ROOT)], check=True,
        capture_output=True, text=True).stdout.strip()
    executable = "build/port_v2/integration/combat/combat_test"
    compile_test(root_wsl, "src/port_v2/combat/hit_ko/hit_ko.c", executable)
    first = run(root_wsl, executable)
    second = run(root_wsl, executable)
    require(first == second, "deterministic combat replay drifted")
    require(first.strip().splitlines() == expected_lines(contract),
            "source-derived combat differential failed")
    if args.negative_control:
        negative = run(root_wsl, executable, True)
        require(negative.endswith("Combat integration negative controls: PASS\n"),
                "no-contact or wrong-selector control failed")
        source = (ROOT / "src/port_v2/combat/hit_ko/hit_ko.c").read_text()
        original = "runtime->actor.anim_record = AVSP_PORT_V2_KO_ANIM_RECORD_5;"
        require(source.count(original) == 2, "writer mutation anchors drifted")
        mutated = source.replace(
            original,
            "runtime->actor.anim_record = AVSP_PORT_V2_KO_ANIM_RECORD_4;")
        mutated_path = ROOT / "build/port_v2/integration/combat/hit_ko_mutated.c"
        mutated_path.write_text(mutated)
        mutated_executable = "build/port_v2/integration/combat/combat_mutated"
        compile_test(root_wsl,
                     "build/port_v2/integration/combat/hit_ko_mutated.c",
                     mutated_executable)
        wrong = run(root_wsl, mutated_executable)
        require(wrong != first, "mutated writer was not rejected")
        print("INTEGRATE-02 mutated-writer control: REJECTED")
    print("INTEGRATE-02 exact combat host differential: PASS")


if __name__ == "__main__":
    main()
