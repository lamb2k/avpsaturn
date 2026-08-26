#!/usr/bin/env python3
"""Mutation controls for the target-visible Round 1 entry wiring."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MAIN = (ROOT / "main.c").read_text()

REQUIRED = (
    '#include "src/port_v2/gameplay/round1/round1.h"',
    "static AvspRound1Runtime round1_runtime;",
    "avsp_round1_init(&round1_runtime);",
    "avsp_round1_begin_first_entry(&round1_runtime);",
    "avsp_round1_step_first_entry(&round1_runtime)",
    "avsp_round1_step_player(&round1_runtime, input.player_mask, 0)",
    "avsp_diag_round1_entry_valid = avsp_round1_entry_valid(&round1_runtime);",
    "avsp_diag_round1_route_state = round1_runtime.route_state;",
    "avsp_diag_round1_rng_seed = round1_runtime.rng_seed;",
    "avsp_diag_round1_canaries_ok = avsp_round1_canaries_ok(&round1_runtime);",
    "avsp_diag_round1_entry_spawn_count = round1_runtime.entry.spawn_count;",
    "avsp_diag_round1_control_enabled =",
    "avsp_diag_round1_player_controller_updates =",
    "avsp_frontend_load_round1_text(&frontend_runtime);",
)

def accepts(body):
    return all(token in body for token in REQUIRED)

assert accepts(MAIN)
for token in REQUIRED[2:]:
    assert not accepts(MAIN.replace(token, "/* suppressed Round 1 binding */", 1))
assert "if (round1_runtime.route_state == AVSP_ROUND1_ROUTE_ENTRY_STATE)" in MAIN
assert "avsp_frontend_draw_round1_text(&frontend_runtime);" in MAIN
assert "round1_runtime.frame < AVSP_FRONTEND_R1TEXT_CLEAR_FRAME" not in MAIN
print("REIMPLEMENT-13 target first-entry/current-input wiring: PASS (12 suppressions rejected)")
