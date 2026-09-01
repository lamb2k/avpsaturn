#!/usr/bin/env python3
"""Mutation controls for Predator route interaction/resource ownership."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "data" / "oracle11_predator_route_ownership.json"
SPEC = importlib.util.spec_from_file_location(
    "oracle11_route_ownership",
    ROOT / "tools" / "analyze_oracle11_player_route_ownership.py")
assert SPEC and SPEC.loader
oracle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle)


def reject(mutant: dict, label: str) -> None:
    try:
        oracle.validate(mutant)
    except ValueError:
        return
    raise AssertionError(f"accepted route-ownership mutation: {label}")


report = json.loads(ARTIFACT.read_text(encoding="ascii"))
oracle.validate(report)

mutant = copy.deepcopy(report)
mutant["status"] = "PARTIAL"
reject(mutant, "player audio closure removed")

mutant = copy.deepcopy(report)
mutant["action_phase_reconciliation"]["unmapped_player_phases"] = ["0x0e00"]
reject(mutant, "unmapped interaction phase")

mutant = copy.deepcopy(report)
mutant["health_pickup"]["natural_witness"]["health_after"] = 96
reject(mutant, "fitted health result")

mutant = copy.deepcopy(report)
mutant["temporary_resource_pickup"]["grant"]["value"] = 599
reject(mutant, "fitted resource timer")

mutant = copy.deepcopy(report)
mutant["temporary_resource_pickup"]["natural_route_classification"] = "SOURCE_CLOSED"
reject(mutant, "unreached resource pickup called required")

mutant = copy.deepcopy(report)
mutant["interaction_action_and_interruption"]["natural_completion"]["last"] = 4058
reject(mutant, "fitted interaction completion")

mutant = copy.deepcopy(report)
mutant["interaction_action_and_interruption"]["implementation_contract"][
    "entry"]["allocation"]["variant_u8"] = 3
reject(mutant, "guessed interaction effect variant")

mutant = copy.deepcopy(report)
mutant["interaction_action_and_interruption"]["implementation_contract"][
    "active"]["natural_completion"]["writer"] = "fixed-frame"
reject(mutant, "fixed-frame interaction completion")

mutant = copy.deepcopy(report)
mutant["interaction_action_and_interruption"]["implementation_contract"][
    "class20_effect"]["rng"]["calls"] = [1]
reject(mutant, "invented class20 RNG")

mutant = copy.deepcopy(report)
mutant["interaction_action_and_interruption"]["implementation_contract"][
    "current_state_collision"]["target_reaction"]["reaction_entry"][
        "record"]["animation_record"] = "0x0012dd88"
reject(mutant, "wrong interaction target reaction record")

mutant = copy.deepcopy(report)
mutant["interaction_action_and_interruption"]["implementation_contract"][
    "current_state_collision"]["target_eligibility"][
        "reaction_state_exclusion"] = True
reject(mutant, "invented interaction reaction-state exclusion")

mutant = copy.deepcopy(report)
mutant["interaction_action_and_interruption"]["implementation_contract"][
    "current_state_collision"]["collision_identity_latch"][
        "independent_from_melee_attack_active"] = False
reject(mutant, "interaction collision latch coupled to melee state")

mutant = copy.deepcopy(report)
mutant["interaction_action_and_interruption"]["implementation_contract"][
    "current_state_collision"]["target_reaction"]["first_flight"][
        "x_velocity_s32_16_16"] = -0x20000
reject(mutant, "wrong interaction target launch motion")

mutant = copy.deepcopy(report)
mutant["interaction_action_and_interruption"]["implementation_contract"][
    "current_state_collision"]["target_reaction"]["audio"][
        "command_u16"] = 0x003c
reject(mutant, "wrong interaction target audio command")

mutant = copy.deepcopy(report)
mutant["interaction_action_and_interruption"]["implementation_contract"][
    "active"]["button1_interruption"]["source_stage_progress"][
        "source_frame_u16"] = 4051
reject(mutant, "early interaction interruption stage progress")

mutant = copy.deepcopy(report)
mutant["interaction_action_and_interruption"]["implementation_contract"][
    "active"]["button1_interruption"]["source_stage_progress"][
        "calls_u8"] = 2
reject(mutant, "duplicate interaction interruption stage progress")

mutant = copy.deepcopy(report)
mutant["interaction_action_and_interruption"]["implementation_contract"][
    "active"]["button1_interruption"][
        "weapon_dispatch_delay_updates_u8"] = 1
reject(mutant, "invented interaction interruption dispatch delay")

mutant = copy.deepcopy(report)
mutant["audio_ownership"]["route_audio_owner"] = "predator-warrior-player-authority"
reject(mutant, "route audio assigned to player")

mutant = copy.deepcopy(report)
mutant["audio_ownership"]["health_max_score_award"] = \
    "0x0abdd2 is a QSound dispatcher"
reject(mutant, "BCD score routine mislabeled audio")

mutant = copy.deepcopy(report)
mutant["load_release_ownership"]["bulk_loader_uses_player_actor_base"] = True
reject(mutant, "bulk loader assigned to player")

mutant = copy.deepcopy(report)
mutant["remaining_player_unknowns"] = ["restored false player backlog"]
reject(mutant, "player audio backlog restored")

mutant = copy.deepcopy(report)
mutant["audio_ownership"]["player_trigger_boundary"]["global_backlog_begins"] = "0x001922"
reject(mutant, "global transport absorbed into player boundary")

mutant = copy.deepcopy(report)
mutant["protected_boundaries"]["yaba_runs"] = 1
reject(mutant, "Yaba run admitted")

rebuilt = oracle.build_report()
assert oracle.canonical(rebuilt) == ARTIFACT.read_bytes(), "derived report drift"
print("ORACLE-11 player route-ownership tests: PASS (18 mutations rejected)")
