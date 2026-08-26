#!/usr/bin/env python3
"""Validate deterministic SPEC-02 generation and real field-family controls."""
import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "spec02", ROOT / "tools/build_spec02_round1_contract.py")
assert SPEC and SPEC.loader
spec02 = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(spec02)
contract = json.loads(spec02.OUT.read_text(encoding="ascii"))
fixtures = json.loads(spec02.FIXTURES.read_text(encoding="ascii"))
spec02.validate(contract, fixtures)
weapon = fixtures["authority_data"]["player"][
    "weapon_projectile_resource"]["implementation_contract"]
assert weapon["source_input"]["button1_mask"] == "0x0010"
assert weapon["sufficient_volley"]["spawn_tick_offsets"] == list(range(0, 48, 4))
assert weapon["sufficient_volley"]["cleanup_tick_offset"] == 49
assert weapon["empty_fallback"]["cleanup_tick_offset"] == 17
projectile = weapon["projectile_lifecycle_contract"]
assert projectile["spec_executable"] is True
assert projectile["implementation_blocker"] is None
assert projectile["impact_actor_contract"]["spec_executable"] is True
assert projectile["initialization"]["presentation_actor_fields"][
    "object_or_u16"] == "0x8000"
assert projectile["impact_actor_contract"]["initialization"][
    "presentation_actor_fields"]["coordinate_mode_u8"] == 0
damage = projectile["current_state_interfaces"]["collision"]["damage"]
assert damage["baseline"]["damage"] == 24
assert damage["mutation"]["damage"] == 31
assert damage["suppression"]["mutated_writes"] == 4
assert weapon["empty_effect_variant1_contract"]["spec_executable"] is True
rebuilt_contract, rebuilt_fixtures = spec02.build_artifacts()
assert spec02.canonical(rebuilt_contract) == spec02.OUT.read_bytes()
assert spec02.canonical(rebuilt_fixtures) == spec02.FIXTURES.read_bytes()

def reject(c, f, label):
    try:
        spec02.validate(c, f)
    except (ValueError, KeyError):
        return
    raise AssertionError(f"SPEC-02 mutation escaped: {label}")

mutations = []
m = copy.deepcopy(contract); m["required_unknown_count"] = 1; mutations.append((m, fixtures, "required unknown"))
m = copy.deepcopy(contract); m["field_contracts"][0]["transition_guard"] = "UNKNOWN fallback"; mutations.append((m, fixtures, "unknown guard"))
m = copy.deepcopy(contract); m["field_contracts"][1]["reads"] = []; mutations.append((m, fixtures, "empty reads"))
m = copy.deepcopy(contract); m["field_contracts"][2]["source"]["evidence_hash"] = "0" * 64; mutations.append((m, fixtures, "wrong evidence hash"))
m = copy.deepcopy(contract); m["field_contracts"][3]["source"]["json_pointer"] = "/missing"; mutations.append((m, fixtures, "missing source pointer"))
m = copy.deepcopy(contract); m["field_contracts"][4]["mutation_control"]["json_pointer"] = "/missing"; mutations.append((m, fixtures, "missing real mutation"))
m = copy.deepcopy(contract); m["coverage_gate"]["orphan_authoritative_writers"] = 1; mutations.append((m, fixtures, "weakened gate"))
f = copy.deepcopy(fixtures); f["authority_data"]["rng"]["algorithm"]["recurrence"] = "guess"; mutations.append((contract, f, "fixture mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["weapon_projectile_resource"]["implementation_contract"]["sufficient_volley"]["cadence_reload"] = 3; mutations.append((contract, f, "weapon cadence mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["weapon_projectile_resource"]["implementation_contract"]["empty_effect_variant1_contract"]["variant"] = 0; mutations.append((contract, f, "empty effect variant mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["weapon_projectile_resource"]["implementation_contract"]["projectile_lifecycle_contract"]["current_state_interfaces"]["collision"]["damage"]["mutation"]["damage"] = 24; mutations.append((contract, f, "projectile damage lookup mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["weapon_projectile_resource"]["implementation_contract"]["projectile_lifecycle_contract"]["initialization"]["presentation_actor_fields"]["object_or_u16"] = "0x0000"; mutations.append((contract, f, "projectile presentation object priority mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["weapon_projectile_resource"]["implementation_contract"]["projectile_lifecycle_contract"]["impact_actor_contract"]["initialization"]["presentation_actor_fields"]["palette_u8"] = 1; mutations.append((contract, f, "impact presentation palette mutation"))
m = copy.deepcopy(contract); m["protected_boundaries"]["physical_saturn"] = "PASS"; mutations.append((m, fixtures, "hardware overclaim"))
m = copy.deepcopy(contract); m["next_card"] = "SALVAGE-08-FRONTEND"; mutations.append((m, fixtures, "frontend bypass"))
for args in mutations:
    reject(*args)
print(f"SPEC-02 Round 1 executable contract: PASS ({len(mutations)} mutations rejected)")
