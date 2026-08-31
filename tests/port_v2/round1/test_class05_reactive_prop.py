#!/usr/bin/env python3
"""Focused source differential and real mutations for Coffee Shop class 0x05."""
from __future__ import annotations

import csv
import io
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ROUND1 = ROOT / "src/port_v2/gameplay/round1/round1.c"
SOURCE = ROOT / ".deps/mame/oracle11_progression_lifecycle_cs21a/coffee_shop_scene_actors.tsv"


def wsl(path: Path) -> str:
    return subprocess.run(
        ["wsl.exe", "-d", "Ubuntu-24.04", "-u", "root", "--",
         "wslpath", "-a", str(path).replace("\\", "/")],
        check=True, capture_output=True, text=True).stdout.strip()


def run(body: str) -> tuple[int, list[dict[str, str]]]:
    body = body.replace('#include "../../integration/combat/combat.h"',
                        '#include "combat.h"')
    body = body.replace('#include "../../../../avsp_actor.h"',
                        '#include "avsp_actor.h"')
    body = body.replace('#include "../../../../avsp_collision.h"',
                        '#include "avsp_collision.h"')
    with tempfile.TemporaryDirectory(prefix="round1-class05-") as name:
        temp = Path(name)
        source = temp / "round1.c"
        source.write_text(body, encoding="ascii", newline="\n")
        output = f"/tmp/{temp.name}-class05"
        command = (
            f"cd '{wsl(ROOT)}' && gcc -std=c90 -pedantic -Wall -Wextra "
            f"-Werror -I '{wsl(temp)}' -I . "
            f"-I src/port_v2/gameplay/round1 "
            f"-I src/port_v2/gameplay/player_action "
            f"-I src/port_v2/gameplay/street_alien_ai "
            f"-I src/port_v2/combat/hit_ko "
            f"-I src/port_v2/integration/combat "
            f"'{wsl(source)}' avsp_actor.c avsp_collision.c "
            f"src/port_v2/gameplay/player_action/player_action.c "
            f"src/port_v2/gameplay/street_alien_ai/street_alien_ai.c "
            f"src/port_v2/combat/hit_ko/hit_ko.c "
            f"src/port_v2/player/player.c src/port_v2/enemy/enemy.c "
            f"src/port_v2/integration/player_enemy/player_enemy.c "
            f"src/port_v2/integration/combat/combat.c "
            f"tests/port_v2/round1/round1_coffee_shop_scene_census.c "
            f"-o '{output}' && ulimit -s unlimited && '{output}'")
        result = subprocess.run(
            ["wsl.exe", "-d", "Ubuntu-24.04", "-u", "root", "--",
             "bash", "-lc", command], check=False, capture_output=True,
            text=True)
    if result.returncode not in (0, 5):
        raise AssertionError(
            f"class-0x05 focused census failed ({result.returncode})\n"
            f"{result.stderr[-2000:]}")
    return result.returncode, list(csv.DictReader(
        io.StringIO(result.stdout), delimiter="\t"))


def selected_source() -> dict[tuple[int, str, str], tuple[int, ...]]:
    result: dict[tuple[int, str, str], tuple[int, ...]] = {}
    with SOURCE.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            frame = int(row["frame"])
            type_id = int(row["type"])
            slot = row["slot"]
            class_id = row["class"]
            if not ((type_id == 20 and class_id == "05" and
                     slot in ("ffb180", "ffb280") and frame <= 3932) or
                    (type_id == 24 and class_id == "4e" and
                     slot == "ffc200" and 3891 <= frame <= 3901)):
                continue
            result[(frame, slot, class_id)] = (
                int(row["state"], 16), int(row["substate"], 16),
                int(row["x_fp"], 16) >> 16,
                int(row["y_fp"], 16) >> 16, int(row["z"]),
                int(row["facing"]), int(row["animation_record"], 16),
                int(row["animation_timer"], 16),
                int(row["animation_branch"]))
    return result


def selected_native(rows: list[dict[str, str]]) -> \
        dict[tuple[int, str, str], tuple[int, ...]]:
    result: dict[tuple[int, str, str], tuple[int, ...]] = {}
    for row in rows:
        frame = int(row["frame"])
        type_id = int(row["type"])
        slot = row["source_slot"][-6:]
        class_id = row["class"]
        if not ((type_id == 20 and class_id == "05" and
                 slot in ("ffb180", "ffb280") and frame <= 3932) or
                (type_id == 24 and class_id == "4e" and
                 slot == "ffc200" and 3891 <= frame <= 3901)):
            continue
        result[(frame, slot, class_id)] = (
            int(row["state"], 16), int(row["substate"], 16),
            int(row["x"]), int(row["y"]), int(row["z"]),
            int(row["facing"]), int(row["animation_record"], 16),
            int(row["animation_timer"]), int(row["animation_branch"]))
    return result


source_rows = selected_source()
body = ROUND1.read_text(encoding="ascii")
_, baseline = run(body)
assert selected_native(baseline) == source_rows

mutations = (
    ("phase projection", "if ((runtime->frame & 1u) != 0u)",
     "if ((runtime->frame & 1u) == 0u)"),
    ("RNG owner",
     "(void)avsp_round1_source_rng(runtime);\n        ++runtime->class05_rng_calls;",
     "/* class-0x05 RNG call suppressed */\n        ++runtime->class05_rng_calls;"),
    ("trajectory sign",
     "actor->source_x_velocity = motion->primary_x_velocity;",
     "actor->source_x_velocity = -motion->primary_x_velocity;"),
    ("release guard",
     "actor->state = spec->release_state;\n            actor->substate = spec->release_substate;",
     "actor->state = spec->debris_state;\n            actor->substate = spec->release_substate;"),
)
for label, old, new in mutations:
    assert body.count(old) == 1, label
    _, mutant = run(body.replace(old, new))
    assert selected_native(mutant) != source_rows, label

print("REIMPLEMENT-13 class-0x05 source differential: PASS "
      "(4 real mutations rejected)")
