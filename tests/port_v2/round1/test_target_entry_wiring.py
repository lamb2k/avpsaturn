#!/usr/bin/env python3
"""Mutation controls for the target-visible Round 1 entry wiring."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MAIN = (ROOT / "main.c").read_text()

REQUIRED = (
    '#include "src/port_v2/gameplay/round1/round1.h"',
    "static AvspRound1Runtime round1_runtime;",
    "avsp_round1_init(&round1_runtime);",
    "avsp_diag_round1_entry_valid = avsp_round1_entry_valid(&round1_runtime);",
    "avsp_diag_round1_route_state = round1_runtime.route_state;",
    "avsp_diag_round1_rng_seed = round1_runtime.rng_seed;",
    "avsp_diag_round1_canaries_ok = avsp_round1_canaries_ok(&round1_runtime);",
    "avsp_frontend_load_round1_text(&frontend_runtime);",
)

def accepts(body):
    return all(token in body for token in REQUIRED)

assert accepts(MAIN)
for token in REQUIRED[2:]:
    assert not accepts(MAIN.replace(token, "/* suppressed Round 1 binding */", 1))
assert "if (round1_runtime.frame < AVSP_FRONTEND_R1TEXT_CLEAR_FRAME)" in MAIN
assert "avsp_frontend_draw_round1_text(&frontend_runtime);" in MAIN
print("REIMPLEMENT-13 target entry wiring: PASS (6 suppressions rejected)")
