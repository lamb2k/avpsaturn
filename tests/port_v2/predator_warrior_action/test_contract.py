#!/usr/bin/env python3
"""Production-interface and exact-behavior checks for PROMOTE-10."""

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def require(value, message):
    if not value:
        raise AssertionError(message)


contract = json.loads((HERE / "contract.json").read_text())
header = ROOT / "src/port_v2/gameplay/player_action/player_action.h"
source = ROOT / "src/port_v2/gameplay/player_action/player_action.c"
compat_header = ROOT / "tests/port_v2/predator_warrior_action_bench/predator_warrior_action_bench.h"
compat_source = ROOT / "tests/port_v2/predator_warrior_action_bench/predator_warrior_action_bench.c"
body = source.read_text()
require(header.is_file() and source.is_file(), "production player-action interface missing")
require(not re.search(r"\bjo_|\bsl[A-Z]|spr[A-Z]|VDP1|VDP2", body),
        "production gameplay core has Saturn/render dependency")
require("../../../src/port_v2/gameplay/player_action/player_action.h" in compat_header.read_text(),
        "salvage compatibility include no longer points to production")
require("avsp_pw_step" not in compat_source.read_text(),
        "compatibility translation unit owns gameplay behavior")
require(contract["adapter_deletion_condition"].startswith("delete with SALVAGE-10"),
        "compatibility adapter has no deletion condition")
require(not re.search(r"5185|5230|5275|5320|5190|5236|5283|5329", body),
        "production core embeds review/source absolute frames")

translated = subprocess.run(
    ["wsl.exe", "wslpath", "-a", str(ROOT).replace("\\", "/")],
    check=True, capture_output=True, text=True).stdout.strip()
command = (
    f"cd '{translated}' && mkdir -p build/port_v2/predator_warrior_action && "
    "gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 "
    "src/port_v2/gameplay/player_action/player_action.c "
    "tests/port_v2/predator_warrior_action_bench/predator_warrior_action_test.c "
    "-Itests/port_v2/predator_warrior_action_bench "
    "-o build/port_v2/predator_warrior_action/action_test && "
    "./build/port_v2/predator_warrior_action/action_test")
subprocess.run(["wsl.exe", "sh", "-lc", command], check=True)
print("PROMOTE-10 production player-action contract: PASS")
