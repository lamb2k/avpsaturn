#!/usr/bin/env python3
"""Strict portable-core and provenance checks for SALVAGE-10."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


contract = json.loads((HERE / "contract.json").read_text(encoding="utf-8"))
oracle04 = ROOT / "data" / "oracle04_predator_warrior_control_actions.json"
oracle06 = ROOT / "data" / "oracle06_round1_encounter.json"
import hashlib
require(hashlib.sha256(oracle04.read_bytes()).hexdigest() == contract["oracle04_sha256"],
        "ORACLE-04 identity drift")
require(hashlib.sha256(oracle06.read_bytes()).hexdigest() == contract["oracle06_sha256"],
        "ORACLE-06 identity drift")
require(contract["direction_latency_frames"] == 2 and
        contract["attack_selectors"] == [1, 2, 3, 4] and
        contract["active_first"] == [4, 5, 7, 8] and
        contract["return_frames"] == [21, 21, 26, 33], "source timing drift")
require(contract["selection_authority"] ==
        "accepted controller attack edge and combo state" and
        contract["contact_reports_are_selection_authority"] is False,
        "contact/fixed event count became selection authority")

core = (HERE / "predator_warrior_action_bench.c").read_text(encoding="utf-8")
require(not re.search(r"\bjo_|\bsl[A-Z]|spr[A-Z]|VDP1|VDP2", core),
        "portable core has Jo/SGL/render dependency")
require(not re.search(r"5185|5230|5275|5320|5190|5236|5283|5329", core),
        "portable core embeds review/source absolute frames")
require("contact_reports" in core and "combo_next" in core and
        "input_edges" in core, "authority separation is absent")

translated = subprocess.run(
    ["wsl.exe", "wslpath", "-a", str(ROOT).replace("\\", "/")],
    check=True, capture_output=True, text=True).stdout.strip()
command = (
    f"cd '{translated}' && mkdir -p build/port_v2/predator_warrior_action_bench && "
    "gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 "
    "tests/port_v2/predator_warrior_action_bench/predator_warrior_action_bench.c "
    "tests/port_v2/predator_warrior_action_bench/predator_warrior_action_test.c "
    "-o build/port_v2/predator_warrior_action_bench/action_test && "
    "./build/port_v2/predator_warrior_action_bench/action_test")
subprocess.run(["wsl.exe", "sh", "-lc", command], check=True)
print("SALVAGE-10 portable contract and provenance: PASS")
