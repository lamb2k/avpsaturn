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
    ('initial-hurt-selector',lambda x:x['actors'][0].__setitem__('hurt_selector_u8',2)),
    ('initial-attack-selector',lambda x:x['actors'][0].__setitem__('attack_selector_u8',0)),
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
    ('current-reaction-map',lambda x:x['damage_hit_ko_removal']['accepted_port_v2_reaction_mapping'].__setitem__('hit_entry_outer_state_u16',0x0400)),
    ('source-hit-selector',lambda x:x['damage_hit_ko_removal']['source_hit_entry_program']['reaction_table'].__setitem__('reaction_selector_actor_4d_u8',0)),
    ('source-hit-record',lambda x:x['damage_hit_ko_removal']['source_hit_entry_program']['visible_result'].__setitem__('animation_record','0x0012dc50')),
    ('source-hit-recovery',lambda x:x['damage_hit_ko_removal']['source_hit_entry_program']['recovery']['captured_values_before_decrement'].__setitem__(0,7)),
    ('source-hit-mutation',lambda x:x['damage_hit_ko_removal']['source_hit_entry_program']['mutation_control'].__setitem__('mutations',0)),
    ('source-hit-score-audio-correction',lambda x:x['damage_hit_ko_removal']['source_hit_entry_program'].__setitem__('score_correction','audio')),
    ('current-retained-authority',lambda x:x['authority_boundary'].__setitem__('retained_gameplay_authority_forbidden',False)),
    ('current-mutation-control',lambda x:x['mutation_controls'].pop()),
]:
    mutant=copy.deepcopy(report);target=next(item for item in mutant['archetypes'] if item['class']=='0x1f')['current_state_implementation_contract'];mutate(target);reject(mutant,label)
for label,mutate in [
    ('first-segment-action-writer',lambda x:x['suppression_control'].__setitem__('writer_pc','0x0607ee')),
    ('first-segment-action-target',lambda x:x['current_dispatch']['action_targets'][11].__setitem__('target','0x060c30')),
    ('first-segment-selector',lambda x:x['animation_selector_table']['selectors'][0].__setitem__('selector_u8',1)),
    ('first-segment-movement',lambda x:x['movement_tables'][1]['vectors'][8].__setitem__('x_delta_s16',2047)),
    ('first-segment-timer-table',lambda x:x['attack_timer_table_u8'].__setitem__(0,29)),
    ('first-segment-source-bound',lambda x:x['action_programs']['source_bounds'].__setitem__('x_max_u16',0x05ef)),
    ('first-segment-source-bound-activation',lambda x:x['action_programs']['source_bounds'].__setitem__('activation_field_u8','actor+0x02')),
    ('first-segment-movement-cadence',lambda x:x['action_programs']['animation_movement_helper_0x0165c4'].__setitem__('movement_cadence','every scheduler frame')),
    ('first-segment-direction',lambda x:x['action_programs']['direction_helper_0x061032']['upper_directions_by_a5_u8'].__setitem__(0,0x15)),
    ('first-segment-jump-vector',lambda x:x['action_programs']['action_0x0e']['z_velocity_table_s32_16_16'].__setitem__(0,-0x0000f000)),
    ('first-segment-attack-selector-group',lambda x:x['action_programs']['action_0x04']['selector_groups_u16'][2].__setitem__(0,44)),
    ('first-segment-loop-counter',lambda x:x['action_programs']['action_0x16'].__setitem__('loop_counter','timer')),
    ('first-segment-fixed-frame',lambda x:x['suppression_control'].__setitem__('fixed_frame_substitute',True)),
    ('first-segment-mutation-control',lambda x:x['mutation_controls'].pop()),
]:
    mutant=copy.deepcopy(report);target=next(item for item in mutant['archetypes'] if item['class']=='0x1f')['first_segment_action_execution_contract'];mutate(target);reject(mutant,label)
for label,mutate in [
    ('inner8-writer',lambda x:x['entry_transition'].__setitem__('writer_pc','0x0610ce')),
    ('inner8-timer',lambda x:x['entry_transition'].__setitem__('timer_u16',599)),
    ('inner8-movement-table',lambda x:x['movement']['tables'][0].__setitem__('table_index_u8',5)),
    ('inner8-motion-sign',lambda x:x['action_0x0e_motion']['phase_2_terminal'].__setitem__('y_acceleration_s32_16_16',38400)),
    ('inner8-fixed-frame',lambda x:x['type16_emission'].__setitem__('fixed_frame_spawn_forbidden',False)),
    ('inner8-suppression',lambda x:x['mutation_control'].__setitem__('mutant_type16_spawn_frames',[3253])),
    ('inner8-record-next',lambda x:x['animation_records'][0].__setitem__('next_animation_record','0x0012d424')),
    ('inner8-action0-rng',lambda x:x['observed_path_program']['action_0x00']['captured_rng_call_counts'].__setitem__('frame_3004_style_match',3)),
    ('inner8-action4-terminal',lambda x:x['observed_path_program']['action_0x04']['captured_terminals'].__setitem__('frame_3134','fixed frame')),
    ('inner8-action10-writer',lambda x:x['observed_path_program']['action_0x10']['overlap_transition'].__setitem__('writer','0x041310')),
    ('inner8-motion-selector',lambda x:x['observed_path_program']['action_0x0e']['captured_selection'].__setitem__('motion_selector_96_u16',22)),
    ('inner8-field88-table',lambda x:x['observed_path_program']['source_tables']['field88_by_rng_low_nibble_u8'].__setitem__(0,2)),
    ('inner8-direction-table',lambda x:x['observed_path_program']['source_tables']['direction_octant_base_u8'].__setitem__(0,0)),
]:
    mutant=copy.deepcopy(report);target=next(item for item in mutant['archetypes'] if item['class']=='0x1f')['first_segment_action_execution_contract']['inner_state_0x08_program'];mutate(target);reject(mutant,label)
print('ORACLE-11 Round 1 enemy tests: PASS (71 mutations rejected)')
