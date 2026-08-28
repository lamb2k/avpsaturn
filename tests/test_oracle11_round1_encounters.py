#!/usr/bin/env python3
import copy
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location(
    'encounters',ROOT/'tools/analyze_oracle11_round1_encounters.py')
assert spec and spec.loader
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
report=json.loads((ROOT/'data/oracle11_round1_encounter_route_authority.json').read_text(encoding='ascii'))
m.validate(report)

def reject(mutant,label):
    try:m.validate(mutant)
    except ValueError:return
    raise AssertionError('accepted encounter mutation: '+label)

mutations=[]
for label,change in (
    ('status',lambda x:x.__setitem__('status','PARTIAL')),
    ('determinism',lambda x:x['capture_identity'].__setitem__('byte_identical',False)),
    ('segment',lambda x:x['segment_bindings'].pop()),
    ('edge',lambda x:x['route_state_edges'].pop()),
    ('spawn',lambda x:x['enemy_spawns'].pop()),
    ('timer',lambda x:x['coverage'].__setitem__('fixed_frame_substitutes',1)),
    ('actor-count',lambda x:x['coverage'].__setitem__('actor_count_clear_substitutes',1)),
    ('presentation',lambda x:x['negative_controls'].__setitem__('presentation_signature_can_advance_gameplay',True)),
    ('spec',lambda x:x['protected_boundaries'].__setitem__('spec02_active',True)),
    ('entry-row',lambda x:x['first_entry_body']['spawn_table']['rows'][0].__setitem__('x',657)),
    ('entry-gate',lambda x:x['first_entry_body']['player_entry_script'].__setitem__('gate_writer_pc','0x0abdd2')),
    ('entry-timer',lambda x:x['first_entry_body']['player_entry_script']['timer_semantics']['loads'].__setitem__(0,59)),
    ('entry-fixed-frame',lambda x:x['first_entry_body']['suppression_control'].__setitem__('fixed_frame_substitute',True)),
    ('progression-guard',lambda x:x['first_segment_recurring_spawn']['controller_guard']['first_operands'].__setitem__('timer_after_u16',3705)),
    ('progression-phase',lambda x:x['first_segment_recurring_spawn']['phase_counter'].__setitem__('writer_pc','0x000e86')),
    ('progression-write',lambda x:x['first_segment_recurring_spawn']['primary_writer']['write_order'][3].__setitem__('effect','x_s16 = fixed_frame_position')),
    ('progression-rng',lambda x:x['first_segment_recurring_spawn']['primary_writer']['rng'].__setitem__('calls',0)),
    ('progression-suppression',lambda x:x['first_segment_recurring_spawn']['suppression_control'].__setitem__('suppressed_writer_count',0)),
    ('controller-init',lambda x:x['first_segment_recurring_spawn']['controller_program']['initializer']['limit_table_u16'].__setitem__(1,34)),
    ('intro-gate-owner',lambda x:x['first_segment_recurring_spawn']['controller_program']['intro_gate_transition']['gate_owner'].__setitem__('class_u8','0x1f')),
    ('intro-gate-suppression',lambda x:x['first_segment_recurring_spawn']['intro_gate_suppression_control'].__setitem__('suppressed_writer_count',0)),
    ('lifecycle-release-writer',lambda x:x['first_segment_recurring_spawn']['lifecycle_release_boundary'].__setitem__('writer_pc','0x061150')),
    ('ko-progress-increment',lambda x:x['first_segment_recurring_spawn']['progress_increment_boundary'].__setitem__('increment_u16',2)),
    ('scene-lifetime-omission',lambda x:x['coffee_shop_scene_census']['actor_lifetimes'].pop()),
    ('scene-pool-omission',lambda x:x['coffee_shop_scene_census']['pool_scan'].pop()),
    ('scene-silent-unknown',lambda x:x['coffee_shop_scene_census']['negative_controls'].__setitem__('unknown_pair_silently_omitted',True)),
):
    mutant=copy.deepcopy(report);change(mutant);reject(mutant,label)
print('ORACLE-11 encounter/route authority tests: PASS (25 mutations rejected)')
