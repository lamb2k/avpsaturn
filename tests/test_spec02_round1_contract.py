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
assert weapon["projectile_lifecycle_implementation_blocker"][
    "spec_executable"] is False
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
m = copy.deepcopy(contract); m["protected_boundaries"]["physical_saturn"] = "PASS"; mutations.append((m, fixtures, "hardware overclaim"))
m = copy.deepcopy(contract); m["next_card"] = "SALVAGE-08-FRONTEND"; mutations.append((m, fixtures, "frontend bypass"))
for args in mutations:
    reject(*args)
print(f"SPEC-02 Round 1 executable contract: PASS ({len(mutations)} mutations rejected)")
