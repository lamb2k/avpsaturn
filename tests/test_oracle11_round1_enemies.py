#!/usr/bin/env python3
"""Mutation controls for route-reachable Round 1 enemy archetypes."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ARTIFACT=ROOT/'data'/'oracle11_round1_enemy_archetypes.json'
SPEC=importlib.util.spec_from_file_location('enemy',ROOT/'tools'/'analyze_oracle11_round1_enemies.py')
assert SPEC and SPEC.loader
enemy=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(enemy)

def reject(mutant,label):
    try:enemy.validate(mutant)
    except ValueError:return
    raise AssertionError(f'accepted enemy mutation: {label}')

report=json.loads(ARTIFACT.read_text(encoding='ascii'));enemy.validate(report)
mutant=copy.deepcopy(report);mutant['status']='PARTIAL';reject(mutant,'family reopened')
mutant=copy.deepcopy(report);mutant['capture_identity']['byte_identical']=False;reject(mutant,'nondeterministic completion')
mutant=copy.deepcopy(report);mutant['archetypes'].pop();reject(mutant,'class/type pair orphaned')
mutant=copy.deepcopy(report);mutant['archetypes'][0]['dispatch_entry']='fixed frame';reject(mutant,'fixed-frame dispatch')
mutant=copy.deepcopy(report);mutant['archetypes'][0]['dispatch_entry_sha256']='0'*64;reject(mutant,'source dispatch detached')
mutant=copy.deepcopy(report);mutant['archetypes'][0]['orphan_write_rows']=1;reject(mutant,'writer orphan hidden')
mutant=copy.deepcopy(report);mutant['archetypes'][0]['rng']['orphan_calls']=1;reject(mutant,'RNG orphan hidden')
mutant=copy.deepcopy(report);mutant['archetypes'][0]['presentation_and_collision']['record_count']=0;reject(mutant,'record/selector table dropped')
mutant=copy.deepcopy(report);mutant['archetypes'][0]['damage_hit_ko']['current_state_owner_bound']=False;reject(mutant,'damage detached from current state')
mutant=copy.deepcopy(report);mutant['archetypes'][0]['semantic_name_inferred']=True;reject(mutant,'semantic name inferred')
mutant=copy.deepcopy(report);mutant['scope_boundary']['boss_encounter_orchestration_closed_here']=True;reject(mutant,'boss encounter silently absorbed')
mutant=copy.deepcopy(report);mutant['negative_controls']['generic_enemy_behavior_tree_forbidden']=False;reject(mutant,'generic behavior tree admitted')
mutant=copy.deepcopy(report);mutant['protected_boundaries']['spec02_active']=True;reject(mutant,'SPEC-02 activated')
print('ORACLE-11 Round 1 enemy tests: PASS (13 mutations rejected)')
