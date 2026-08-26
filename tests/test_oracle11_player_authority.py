#!/usr/bin/env python3
"""ORACLE-11 player authority identity and mutation controls."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "data" / "oracle11_predator_warrior_authority.json"
SPEC = importlib.util.spec_from_file_location(
    "oracle11_player", ROOT / "tools" / "analyze_oracle11_player_authority.py")
assert SPEC and SPEC.loader
oracle11 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle11)


def reject(mutant: dict, label: str) -> None:
    try:
        oracle11.validate(mutant)
    except ValueError:
        return
    raise AssertionError(f"accepted ORACLE-11 player mutation: {label}")


report = json.loads(ARTIFACT.read_text(encoding="ascii"))
oracle11.validate(report)

mutant = copy.deepcopy(report)
mutant["locomotion_neutral_facing"]["release_transition"] \
    ["right_witness"]["retained_facing"] = 0
reject(mutant, "neutral resets right-facing")

mutant = copy.deepcopy(report)
decode = mutant["locomotion_neutral_facing"]["input_decode"]
decode["up_lane"]["actor_input_bit"], decode["down_lane"]["actor_input_bit"] = 2, 3
reject(mutant, "up/down actor bits inverted")

mutant = copy.deepcopy(report)
mutant["locomotion_neutral_facing"]["release_transition"] \
    ["stop_timer"]["ticks"] = 8
reject(mutant, "stop timer fitted")

mutant = copy.deepcopy(report)
mutant["locomotion_neutral_facing"]["release_transition"] \
    ["stop_entry_writer"] = "0x019a48"
reject(mutant, "wrong transition writer")

mutant = copy.deepcopy(report)
mutant["locomotion_neutral_facing"]["classification"] = "OBSERVED"
reject(mutant, "locomotion classification downgraded")

mutant = copy.deepcopy(report)
mutant["accepted_prior_player_bodies"]["attack_selector_order"] = [1, 3, 2, 4]
reject(mutant, "attack lock reordered")

mutant = copy.deepcopy(report)
mutant["route_reachable_melee_actions"]["classification"] = "PARTIAL"
reject(mutant, "melee classification downgraded")

mutant = copy.deepcopy(report)
mutant["route_reachable_melee_actions"]["close_combo"] \
    ["followup_window"]["ticks"] = 28
reject(mutant, "combo window fitted")

mutant = copy.deepcopy(report)
mutant["route_reachable_melee_actions"]["rng_consumption"] = \
    "random selector choice"
reject(mutant, "random attack selection introduced")

mutant = copy.deepcopy(report)
mutant["route_reachable_melee_actions"]["counterfactuals"] \
    ["held_button_no_auto_chain"] = False
reject(mutant, "held attack auto-chain admitted")

mutant = copy.deepcopy(report)
mutant["normal_jump_air_landing"]["witness"]["apex_world_y"] = 394
reject(mutant, "jump apex fitted")

mutant = copy.deepcopy(report)
mutant["normal_jump_air_landing"]["state_machine"]["landing_writer"] = \
    "0x023634"
reject(mutant, "wrong jump landing writer")

mutant = copy.deepcopy(report)
mutant["normal_jump_air_landing"]["rng_consumption"] = "one call"
reject(mutant, "jump RNG introduced")

mutant = copy.deepcopy(report)
mutant["normal_jump_air_landing"]["counterfactuals"] \
    ["directional_variant_does_not_authorize_normal_jump_changes"] = False
reject(mutant, "directional jump widened into normal authority")

mutant = copy.deepcopy(report)
mutant["status"] = "PARTIAL"
mutant["remaining_player_backlog"] = ["false restored player backlog"]
reject(mutant, "player-family closure removed")

mutant = copy.deepcopy(report)
mutant["player_origin_gameplay_audio"]["boundary"]["global_transport_owner"] = \
    "predator-warrior-player-authority"
reject(mutant, "global audio transport assigned to player")

mutant = copy.deepcopy(report)
mutant["directional_airborne_interruption"]["status"] = "PARTIAL"
reject(mutant, "air checkpoint downgraded")

mutant = copy.deepcopy(report)
mutant["hit_ko_failure_continue_respawn"]["status"] = "PARTIAL"
reject(mutant, "HIT/KO checkpoint downgraded")

mutant = copy.deepcopy(report)
mutant["hit_ko_failure_continue_respawn"]["failure_continue"] \
    ["direction_only_confirms"] = True
reject(mutant, "direction-only continue confirmation")

mutant = copy.deepcopy(report)
mutant["route_pickup_resource_audio_load_ownership"] \
    ["action_phase_reconciliation"]["unmapped_player_phases"] = ["0x0e00"]
reject(mutant, "unmapped route interaction phase")

mutant = copy.deepcopy(report)
mutant["route_pickup_resource_audio_load_ownership"] \
    ["audio_ownership"]["route_audio_owner"] = "predator-warrior-player-authority"
reject(mutant, "global route audio assigned to player")

rebuilt = oracle11.build_report()
assert oracle11.canonical(rebuilt) == ARTIFACT.read_bytes(), "derived report drift"
print("ORACLE-11 player authority tests: PASS (21 mutations rejected)")
