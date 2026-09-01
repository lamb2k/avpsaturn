#!/usr/bin/env python3
"""Focused Coffee Shop exit-program differential and real mutations."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "src/port_v2/gameplay/round1/round1.c"
HEADER = ROOT / "src/port_v2/gameplay/round1/round1.h"
GENERATED = ROOT / "src/port_v2/gameplay/round1/spec02_round1_entry_data.h"
TEST = ROOT / "tests/port_v2/round1/round1_coffee_exit_test.c"


def wsl(path: Path) -> str:
    return subprocess.run(
        ["wsl.exe", "-d", "Ubuntu-24.04", "-u", "root", "--",
         "wslpath", "-a", str(path).replace("\\", "/")],
        check=True, capture_output=True, text=True).stdout.strip()


def run(generated: str, passes: bool, label: str) -> None:
    with tempfile.TemporaryDirectory(prefix="round1-exit-") as name:
        temp = Path(name)
        source = SOURCE.read_text().replace(
            '#include "../../integration/combat/combat.h"',
            '#include "combat.h"').replace(
            '#include "../../../../avsp_actor.h"',
            '#include "avsp_actor.h"').replace(
            '#include "../../../../avsp_collision.h"',
            '#include "avsp_collision.h"')
        header = HEADER.read_text().replace(
            '#include "../player_action/player_action.h"',
            '#include "player_action.h"').replace(
            '#include "../street_alien_ai/street_alien_ai.h"',
            '#include "street_alien_ai.h"').replace(
            '#include "../../combat/hit_ko/hit_ko.h"',
            '#include "hit_ko.h"')
        (temp / "round1.c").write_text(source)
        (temp / "round1.h").write_text(header)
        (temp / "spec02_round1_entry_data.h").write_text(generated)
        command = (
            f"cd '{wsl(ROOT)}' && gcc -std=c90 -pedantic -Wall -Wextra -Werror "
            f"-I '{wsl(temp)}' -I . -I src/port_v2/gameplay/player_action "
            f"-I src/port_v2/gameplay/street_alien_ai "
            f"-I src/port_v2/combat/hit_ko -I src/port_v2/integration/combat "
            f"'{wsl(temp / 'round1.c')}' avsp_actor.c avsp_collision.c "
            f"src/port_v2/gameplay/player_action/player_action.c "
            f"src/port_v2/gameplay/street_alien_ai/street_alien_ai.c "
            f"src/port_v2/combat/hit_ko/hit_ko.c src/port_v2/player/player.c "
            f"src/port_v2/enemy/enemy.c "
            f"src/port_v2/integration/player_enemy/player_enemy.c "
            f"src/port_v2/integration/combat/combat.c '{wsl(TEST)}' "
            f"-o /tmp/{temp.name}-test && /tmp/{temp.name}-test")
        result = subprocess.run(
            ["wsl.exe", "-d", "Ubuntu-24.04", "-u", "root", "--",
             "bash", "-lc", command], capture_output=True)
        assert (result.returncode == 0) == passes, (
            f"{label}: returncode={result.returncode}\n" +
            result.stdout.decode(errors="replace") +
            result.stderr.decode(errors="replace"))


body = GENERATED.read_text()
run(body, True, "baseline")
mutations = {
    "callback-cadence": ("{ 0u, 5u, 1u }", "{ 0u, 5u, 2u }"),
    "ballistic-x-acceleration":
        ("327680L, -4096L, 524288L, -24576L, 6u, 4u",
         "327680L, -8192L, 524288L, -24576L, 6u, 4u"),
    "route-loader-stall":
        ("26u, 9u, 1u, 5551u, 5564u",
         "25u, 9u, 1u, 5551u, 5564u"),
}
for label, (before, after) in mutations.items():
    assert before in body, label
    run(body.replace(before, after, 1), False, label)
print("REIMPLEMENT-13 Coffee Shop exit program: PASS (3 real mutations)")
