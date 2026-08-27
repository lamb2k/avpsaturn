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
class1f=next(item for item in report['archetypes'] if item['class']=='0x1f')
mutant=copy.deepcopy(report);target=next(item for item in mutant['archetypes'] if item['class']=='0x1f')['presentation_and_collision'];target['records']=[row for row in target['records'] if row['animation_record']!='0x0012dd50'];target['record_count']-=1;reject(mutant,'accepted HIT presentation record dropped')
mutant=copy.deepcopy(report);target=next(item for item in mutant['archetypes'] if item['class']=='0x1f')['presentation_and_collision'];next(row for row in target['records'] if row['animation_record']=='0x0012e214')['hurt_selector']=1;reject(mutant,'accepted KO hurt selector changed')
for label,mutate in [
    ('initial-delay',lambda x:x['actors'][-1].__setitem__('entry_delay_u8',15)),
    ('presentation-mode',lambda x:x['actors'][0].__setitem__('coordinate_mode_u8',0)),
    ('presentation-palette',lambda x:x['actors'][0].__setitem__('palette_u8',0)),
    ('presentation-object-priority',lambda x:x['actors'][0].__setitem__('object_or_u16','0x0000')),
    ('initial-rng',lambda x:x['initialization']['rng_seed_after_each_source_slot'].__setitem__(-1,'0x0000')),
    ('fixed-frame-init',lambda x:x['initialization'].__setitem__('fixed_frame_initialization_forbidden',False)),
    ('post-clear-main-state',lambda x:x['phase_0x1000_and_0x1200'].__setitem__('next_state_substate','0x0000:0000')),
    ('substate-map',lambda x:x['phase_0x1400']['substates'][1].__setitem__('substate_u16',0x1404)),
    ('motion-sign',lambda x:x['phase_0x1400']['substates'][1]['writes'].__setitem__('y_acceleration_s32_16_16',0x5000)),
    ('audio-command',lambda x:x['phase_0x1400']['substates'][2]['audio_edges'][0].__setitem__('command','0x0118')),
    ('animation-selector',lambda x:x['animation_sequences'][0].__setitem__('selector_u8',1)),
    ('mutation-control',lambda x:x['mutation_controls'].pop()),
]:
    mutant=copy.deepcopy(report);target=next(item for item in mutant['archetypes'] if item['class']=='0x1f')['initial_transition_contract'];mutate(target);reject(mutant,label)
for label,mutate in [
    ('current-dynamic-slot',lambda x:x['spawn']['bounded_current_state_dynamic'].__setitem__('slot','0xff9c40')),
    ('current-dynamic-writer',lambda x:x['spawn']['bounded_current_state_dynamic'].__setitem__('writer_pc','0x06b3fe')),
    ('current-spawn-reload',lambda x:x['spawn']['controller']['writes'].__setitem__(-1,'owner.timer = 359')),
    ('current-approach-x',lambda x:x['actions']['approach_0x1600'].__setitem__('x_delta_s16',110)),
    ('current-approach-z',lambda x:x['actions']['approach_0x1600'].__setitem__('z_delta_s16',-22)),
    ('current-contact-tick',lambda x:x['actions']['attack_0x1800']['contact_offsets_u16'].__setitem__(0,47)),
    ('current-damage',lambda x:x['actions']['attack_0x1800'].__setitem__('damage_s16',7)),
    ('current-hit-timer',lambda x:x['damage_hit_ko_removal'].__setitem__('hit_ticks_u16',38)),
    ('current-ko-timer',lambda x:x['damage_hit_ko_removal'].__setitem__('ko_ticks_u16',140)),
    ('current-retained-authority',lambda x:x['authority_boundary'].__setitem__('retained_gameplay_authority_forbidden',False)),
    ('current-mutation-control',lambda x:x['mutation_controls'].pop()),
]:
    mutant=copy.deepcopy(report);target=next(item for item in mutant['archetypes'] if item['class']=='0x1f')['current_state_implementation_contract'];mutate(target);reject(mutant,label)
print('ORACLE-11 Round 1 enemy tests: PASS (38 mutations rejected)')
