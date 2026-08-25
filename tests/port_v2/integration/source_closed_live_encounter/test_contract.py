#!/usr/bin/env python3
"""Strict C90 replay plus real implementation mutations for REIMPLEMENT-12."""
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
SPEC = ROOT / "data" / "spec01_first_live_encounter_executable_contract.json"
EXPECTED_SPEC = "a8a8d5ff06d70a8df4cc7687928e0eb5200927ac8901adb3eb76745c4b42bd0f"


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


require(hashlib.sha256(SPEC.read_bytes()).hexdigest() == EXPECTED_SPEC,
        "SPEC-01 identity drift")
contract = json.loads(SPEC.read_text(encoding="utf-8"))
require(contract["required_behavior_unknown_count"] == 0 and
        contract["physical_saturn"] == "UNRUN", "SPEC-01 status drift")

sources = {
    "player_action.c": ROOT / "src/port_v2/gameplay/player_action/player_action.c",
    "street_alien_ai.c": ROOT / "src/port_v2/gameplay/street_alien_ai/street_alien_ai.c",
    "live_encounter.c": ROOT / "src/port_v2/integration/live_encounter/live_encounter.c",
}

main_source = (ROOT / "main.c").read_text(encoding="utf-8")
require("avsp_diag_live_contract_flags == 127" in main_source,
        "Saturn runtime handoff does not require the complete source-closed contract")
require("avsp_diag_live_contract_flags == 15" not in main_source,
        "obsolete four-flag live encounter contract remains reachable")


def translated(path: Path) -> str:
    return subprocess.run(
        ["wsl.exe", "wslpath", "-a", str(path).replace("\\", "/")],
        check=True, capture_output=True, text=True).stdout.strip()


root_wsl = translated(ROOT)
common = (
    "src/port_v2/combat/hit_ko/hit_ko.c "
    "src/port_v2/integration/combat/combat.c "
    "src/port_v2/integration/player_enemy/player_enemy.c "
    "src/port_v2/player/player.c src/port_v2/enemy/enemy.c "
    "avsp_actor.c avsp_collision.c "
    "tests/port_v2/integration/source_closed_live_encounter/reimplement12_test.c"
)


def compile_and_run(player: str, alien: str, live: str, expect_pass: bool,
                    label: str) -> None:
    with tempfile.TemporaryDirectory(prefix="reimplement12-") as temp_name:
        temp = Path(temp_name)
        (temp / "player_action.c").write_text(player, encoding="utf-8")
        (temp / "street_alien_ai.c").write_text(alien, encoding="utf-8")
        (temp / "live_encounter.c").write_text(live, encoding="utf-8")
        temp_wsl = translated(temp)
        command = (
            f"cd '{root_wsl}' && gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 "
            f"-I src/port_v2/gameplay/player_action "
            f"-I src/port_v2/gameplay/street_alien_ai "
            f"-I src/port_v2/integration/live_encounter "
            f"'{temp_wsl}/player_action.c' '{temp_wsl}/street_alien_ai.c' "
            f"'{temp_wsl}/live_encounter.c' {common} "
            f"-o '{temp_wsl}/reimplement12_test' && "
            f"'{temp_wsl}/reimplement12_test'"
        )
        result = subprocess.run(["wsl.exe", "bash", "-lc", command],
                                capture_output=True, text=True)
        if expect_pass:
            require(result.returncode == 0,
                    f"{label} failed:\n{result.stdout}\n{result.stderr}")
        else:
            require(result.returncode != 0, f"implementation mutation passed: {label}")


base = {name: path.read_text(encoding="utf-8") for name, path in sources.items()}
compile_and_run(base["player_action.c"], base["street_alien_ai.c"],
                base["live_encounter.c"], True, "accepted implementation")

mutations = (
    ("combo-90", "player_action.c", "#define AVSP_PW_COMBO_RESET_FRAMES 30",
     "#define AVSP_PW_COMBO_RESET_FRAMES 90"),
    ("equipment-visible", "player_action.c",
     "runtime->action_local_equipment_flag = 0u;",
     "runtime->action_local_equipment_flag = 1u;"),
    ("upper-wall", "player_action.c", "#define AVSP_PW_UPPER_WORLD_X_MAX 1091",
     "#define AVSP_PW_UPPER_WORLD_X_MAX 1184"),
    ("generic-facing", "street_alien_ai.c",
     "runtime->source_action = 0x1600u;\n    runtime->facing = 1;",
     "runtime->source_action = 0x1600u;\n    runtime->facing = 0;"),
    ("random-assembly", "street_alien_ai.c",
     "case 0x0012E8ECUL: return 0x0012F5DEUL;",
     "case 0x0012E8ECUL: return 0x0012FA0CUL;"),
    ("ko-assembly", "street_alien_ai.c",
     "case 0x0012E224UL: return 0x0013020CUL;",
     "case 0x0012E224UL: return 0x00130346UL;"),
    ("wide-contact", "street_alien_ai.c", "#define AVSP_ALIEN_MAX_CONTACT_X 68",
     "#define AVSP_ALIEN_MAX_CONTACT_X 160"),
    ("projection-sign", "live_encounter.c",
     "(world_z - AVSP_LIVE_ENCOUNTER_WORLD_Z_ANCHOR) - height",
     "-(world_z - AVSP_LIVE_ENCOUNTER_WORLD_Z_ANCHOR) - height"),
    ("camera-origin", "live_encounter.c",
     "target = AVSP_LIVE_ENCOUNTER_CAMERA_LOCK_X +\n        runtime->player.x - AVSP_LIVE_ENCOUNTER_PLAYER_X;",
     "target = runtime->player.x - AVSP_LIVE_ENCOUNTER_PLAYER_X;"),
    ("presentation-clear", "live_encounter.c",
     "return target_ko != 0u && target_inactive != 0u;",
     "return presentation_flag != 0u;"),
)
for label, filename, before, after in mutations:
    require(base[filename].count(before) >= 1, f"mutation site missing: {label}")
    changed = dict(base)
    changed[filename] = changed[filename].replace(before, after, 1)
    compile_and_run(changed["player_action.c"], changed["street_alien_ai.c"],
                    changed["live_encounter.c"], False, label)

print("REIMPLEMENT-12 strict replay and real mutations: PASS")
