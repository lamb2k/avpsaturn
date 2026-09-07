#!/usr/bin/env python3
import copy,importlib.util,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];S=importlib.util.spec_from_file_location('aux',R/'tools/analyze_oracle11_round1_auxiliary.py');assert S and S.loader
m=importlib.util.module_from_spec(S);S.loader.exec_module(m);report=json.loads((R/'data/oracle11_round1_auxiliary_authority.json').read_text(encoding='ascii'));m.validate(report)
def reject(x,label):
 try:m.validate(x)
 except ValueError:return
 raise AssertionError('accepted auxiliary mutation: '+label)
def class0f(x):
 return next(c for c in x['coffee_shop_scene_component_identities']['components']
             if c['type']==20 and c['class']=='0x0f')['implementation_contract']
def type36_class04(x):
 return next(c for c in x['coffee_shop_type36_presentation']['classes']
             if c['class']=='0x04')['implementation_contract']
for label,mutate in [('status',lambda x:x.__setitem__('status','PARTIAL')),('determinism',lambda x:x['capture_identity'].__setitem__('byte_identical',False)),('pair',lambda x:x['archetypes'].pop()),('dispatch',lambda x:x['archetypes'][0].__setitem__('dispatch_entry','fixed frame')),('writer',lambda x:x['archetypes'][0].__setitem__('orphan_write_rows',1)),('rng',lambda x:x['archetypes'][0]['rng'].__setitem__('orphan_calls',1)),('record',lambda x:x['archetypes'][0]['presentation_and_collision'].__setitem__('record_count',0)),('suppression',lambda x:x['archetypes'][0]['counterfactual'].__setitem__('suppression_count',0)),('alias',lambda x:x['phantom_census_aliases'][0].__setitem__('classification','SOURCE_CLOSED')),('bad-control',lambda x:x['coverage'].__setitem__('invalid_zero_removal_controls_accepted',1)),('names',lambda x:x['archetypes'][0].__setitem__('semantic_name_inferred',True)),('spec',lambda x:x['protected_boundaries'].__setitem__('spec02_active',True)),('class09-selector',lambda x:x['first_segment_dependencies']['class_0x09_type20_rng_owner']['selector_table_u16'].__setitem__(0,1)),('class09-scene-rng',lambda x:x['first_segment_dependencies']['class_0x09_type20_rng_owner']['complete_coffee_shop_program'].__setitem__('source_rng_call_count_u16',897)),('class09-scene-guard',lambda x:x['first_segment_dependencies']['class_0x09_type20_rng_owner']['complete_coffee_shop_program']['state_0x0200'].__setitem__('terminal_guard','fixed frame')),('class09-scene-witness',lambda x:x['first_segment_dependencies']['class_0x09_type20_rng_owner']['complete_coffee_shop_program']['exit_presentation_witness']['frame_5493'][0].__setitem__('timer_u16',1)),('class09-fixed-frame',lambda x:x['first_segment_dependencies']['class_0x09_type20_rng_owner'].__setitem__('fixed_frame_substitute_forbidden',False)),('class4e-allocation',lambda x:x['first_segment_dependencies']['class_0x4e_type24_variant4_effect']['allocation_pop_order'].reverse()),('class4e-animation',lambda x:x['first_segment_dependencies']['class_0x4e_type24_variant4_effect']['animation_records'].pop()),('class4e-fixed-frame',lambda x:x['first_segment_dependencies']['class_0x4e_type24_variant4_effect'].__setitem__('fixed_frame_release_forbidden',False)),('class44-object-priority',lambda x:x['first_segment_dependencies']['class_0x44_type24_command_guard_owner']['state0_presentation_actor'].__setitem__('object_or_u16','0x0000')),('class44-guard',lambda x:x['first_segment_dependencies']['class_0x44_type24_command_guard_owner'].__setitem__('guard_clear_frame',2251)),('class44-fixed-frame',lambda x:x['first_segment_dependencies']['class_0x44_type24_command_guard_owner'].__setitem__('fixed_frame_guard_reset_forbidden',False)),('type36-pair',lambda x:x['coffee_shop_type36_presentation']['classes'].pop()),('type36-authority',lambda x:x['coffee_shop_type36_presentation'].__setitem__('retained_gameplay_authority',True)),('type36-collision',lambda x:x['coffee_shop_type36_presentation']['classes'][0].__setitem__('direct_collision_damage_writes',1)),('type36-suppression',lambda x:x['coffee_shop_type36_presentation']['classes'][0]['counterfactual'].__setitem__('remaining_target_actor_rows',1)),('type36-fixed-frame',lambda x:x['coffee_shop_type36_presentation']['classes'][0].__setitem__('fixed_frame_substitute_forbidden',False))]:
 x=copy.deepcopy(report);mutate(x);reject(x,label)
x=copy.deepcopy(report)
x['first_segment_dependencies']['class_0x4e_type24_variant4_effect'][
 'terminal_transition']['after']['timer_u16']=4095
reject(x,'class4e-terminal-order')
for label,mutate in [('type36-context',lambda x:x['coffee_shop_type36_presentation']['classes'][0]['source_spawn_contexts'][0].__setitem__('route_state_u16',3)),('type36-context-identity',lambda x:x['coffee_shop_type36_presentation']['capture_identity'].__setitem__('spawn_context_byte_identical',False))]:
 x=copy.deepcopy(report);mutate(x);reject(x,label)
for label,mutate in [('type36-class04-body',lambda x:type36_class04(x)['source_bodies']['class_dispatch'].__setitem__('sha256','0'*64)),('type36-class04-allocator',lambda x:type36_class04(x)['pool_and_scheduler'].__setitem__('allocator','0x01788c')),('type36-class04-state',lambda x:type36_class04(x)['state_dispatch']['entries'].pop()),('type36-class04-parent',lambda x:type36_class04(x)['allocation']['parent'].__setitem__('source_slot','0x00ff8400')),('type36-class04-offset',lambda x:type36_class04(x)['state_0x0000']['offset_lookup'].__setitem__('offset_y_s16',85)),('type36-class04-facing-offset',lambda x:type36_class04(x)['state_0x0000']['offset_lookup'].__setitem__('offset_sign_rule','always negative')),('type36-class04-animation',lambda x:type36_class04(x)['state_0x0000']['animation_binding']['record_sequence'].pop()),('type36-class04-global-guard',lambda x:type36_class04(x)['state_0x0200'].__setitem__('guard','fixed frame')),('type36-class04-global-delta',lambda x:type36_class04(x)['state_0x0200'].__setitem__('guard_true_arithmetic','actor x += 1')),('type36-class04-backlink',lambda x:type36_class04(x)['state_0x0400_and_0x0600'].__setitem__('backlink_guard','always clear')),('type36-class04-effect',lambda x:type36_class04(x)['effects'].__setitem__('audio_commands',[0x77]))]:
 x=copy.deepcopy(report);mutate(x);reject(x,label)
for label,mutate in [('scene-component-pair',lambda x:x['coffee_shop_scene_component_identities']['components'].pop()),('scene-component-role',lambda x:x['coffee_shop_scene_component_identities']['components'][3].__setitem__('semantic_role','guessed')),('scene-component-control',lambda x:x['coffee_shop_scene_component_identities']['components'][0]['suppression_control'].__setitem__('removed_lifetimes',0)),('scene-component-detail-identity',lambda x:x['coffee_shop_scene_component_identities']['capture_identity'].__setitem__('implementation_detail_byte_identical',False)),('scene-class01-body',lambda x:x['coffee_shop_scene_component_identities']['components'][0]['implementation_contract']['source_body'].__setitem__('sha256','0'*64)),('scene-class01-threshold',lambda x:x['coffee_shop_scene_component_identities']['components'][0]['implementation_contract']['stage_records'][0].__setitem__('camera_threshold_u16',511)),('scene-class01-camera-sample',lambda x:x['coffee_shop_scene_component_identities']['components'][0]['implementation_contract']['stage_spawn_guard']['camera_sample_order']['records'].pop()),('scene-class01-audio',lambda x:x['coffee_shop_scene_component_identities']['components'][0]['implementation_contract']['audio_transactions'][0].__setitem__('command_u16','0x006c')),('scene-class02-body',lambda x:x['coffee_shop_scene_component_identities']['components'][1]['implementation_contract']['source_body'].__setitem__('sha256','0'*64)),('scene-class02-writer',lambda x:x['coffee_shop_scene_component_identities']['components'][1]['implementation_contract']['collision_damage'].__setitem__('current_state_writer','fixed frame')),('scene-class02-attack',lambda x:x['coffee_shop_scene_component_identities']['components'][1]['implementation_contract']['collision_damage'].__setitem__('attack_record','0x0011af77')),('scene-class02-hurt-box',lambda x:x['coffee_shop_scene_component_identities']['components'][1]['implementation_contract']['collision_damage']['hurt_record'].__setitem__('x_half_u8',9)),('scene-class02-reaction-direction',lambda x:x['coffee_shop_scene_component_identities']['components'][1]['implementation_contract']['collision_damage']['reaction_direction'].__setitem__('result_u8',0)),('scene-class02-audio',lambda x:x['coffee_shop_scene_component_identities']['components'][1]['implementation_contract']['audio_transactions'][0].__setitem__('command_u16','0x0076')),('scene-class02-phase-owner',lambda x:x['coffee_shop_scene_component_identities']['components'][1]['implementation_contract']['scheduler_phase_evidence']['phase_owner'].__setitem__('indirect_caller_pc','fixed frame')),('scene-class02-phase-cadence',lambda x:x['coffee_shop_scene_component_identities']['components'][1]['implementation_contract']['scheduler_phase_evidence']['class02_source_update_cadence']['exceptions'][0].__setitem__('updates_u8',1)),('scene-class02-camera-entry',lambda x:x['coffee_shop_scene_component_identities']['components'][1]['implementation_contract']['scheduler_phase_evidence']['camera_entry_animation_rebind'].__setitem__('predicate_transition_source_frame_u16',2640))]:
 x=copy.deepcopy(report);mutate(x);reject(x,label)
x=copy.deepcopy(report)
next(c for c in x['coffee_shop_scene_component_identities']['components']
     if c['type']==24 and c['class']=='0x20')['implementation_contract'][
      'terminal_guard']='fixed frame'
reject(x,'scene-class20-terminal-guard')
x=copy.deepcopy(report)
x['coffee_shop_scene_component_identities']['components'][1][
 'implementation_contract']['collision_damage']['reaction_delay'][
  'value_u16']=2
reject(x,'scene-class02-reaction-delay')
for label,mutate in [
 ('scene-class0f-body',lambda x:class0f(x)['source_body'].__setitem__('sha256','0'*64)),
 ('scene-class0f-table',lambda x:class0f(x)['dispatch_tables'][2]['offsets_s16'].__setitem__(0,4)),
 ('scene-class0f-stage',lambda x:class0f(x)['stage_records'][0].__setitem__('record_sha256','0'*64)),
 ('scene-class0f-delay',lambda x:class0f(x)['state_program']['0x0200'].__setitem__('delay_guard','fixed frame')),
 ('scene-class0f-child-order',lambda x:class0f(x)['state_program']['0x0400']['selector_1']['allocation']['variant_iteration_s8'].reverse()),
 ('scene-class0f-selector',lambda x:class0f(x)['initialization']['animation_records'][1].__setitem__('attack_selector_u8',3)),
 ('scene-class0f-effect',lambda x:class0f(x)['state_program']['0x0400']['selector_0']['first_source_effect'].__setitem__('z_s16',240)),
 ('scene-class0f-audio',lambda x:class0f(x)['audio_transactions'][1].__setitem__('command_u16','0x0077')),
 ('scene-class0f-collision',lambda x:class0f(x)['collision_damage'].__setitem__('current_state_caller','fixed frame')),
 ('scene-class0f-rng',lambda x:class0f(x)['rng'].__setitem__('direct_calls',1)),
 ('scene-class0f-fixed-frame',lambda x:class0f(x).__setitem__('fixed_frame_substitute_forbidden',False))]:
 x=copy.deepcopy(report);mutate(x);reject(x,label)
for label,mutate in [('class45-slot-order',lambda x:x['first_segment_dependencies']['class_0x45_type24_scene_population']['source_slots_scheduler_order'].reverse()),('class45-motion',lambda x:x['first_segment_dependencies']['class_0x45_type24_scene_population']['state0']['motion_table'][0].__setitem__('primary_x_velocity_s16',1)),('class45-fixed-frame',lambda x:x['first_segment_dependencies']['class_0x45_type24_scene_population'].__setitem__('fixed_frame_substitute_forbidden',False))]:
 x=copy.deepcopy(report);mutate(x);reject(x,label)
for label,mutate in [('class43-owner',lambda x:x['first_segment_dependencies']['class_0x43_type24_class01_scene_population']['spawn_owner'].__setitem__('caller_pc','fixed frame')),('class43-group-order',lambda x:x['first_segment_dependencies']['class_0x43_type24_class01_scene_population']['allocation_pop_order_by_group'][0].reverse()),('class43-rng',lambda x:x['first_segment_dependencies']['class_0x43_type24_class01_scene_population'].__setitem__('rng_calls_total_u16',111)),('class43-selector',lambda x:x['first_segment_dependencies']['class_0x43_type24_class01_scene_population']['state0']['animation_selector_table_u8'].__setitem__(0,4)),('class43-motion',lambda x:x['first_segment_dependencies']['class_0x43_type24_class01_scene_population']['state0']['motion_table'][0].__setitem__('alternate_x_velocity_s16',895)),('class43-landing',lambda x:x['first_segment_dependencies']['class_0x43_type24_class01_scene_population']['state_0x0200'].__setitem__('landing_guard','fixed frame')),('class43-fixed-frame',lambda x:x['first_segment_dependencies']['class_0x43_type24_class01_scene_population'].__setitem__('fixed_frame_substitute_forbidden',False))]:
 x=copy.deepcopy(report);mutate(x);reject(x,label)
for label,mutate in [('class47-owner',lambda x:x['first_segment_dependencies']['class_0x47_type24_class02_child_presentation']['spawn_owner'].__setitem__('caller_pc','fixed frame')),('class47-slot-order',lambda x:x['first_segment_dependencies']['class_0x47_type24_class02_child_presentation']['source_slots_scheduler_order'].reverse()),('class47-rng',lambda x:x['first_segment_dependencies']['class_0x47_type24_class02_child_presentation'].__setitem__('rng_calls_total_u16',27)),('class47-motion',lambda x:x['first_segment_dependencies']['class_0x47_type24_class02_child_presentation']['state0']['motion_table'][0].__setitem__('alternate_x_velocity_s16',895)),('class47-fixed-frame',lambda x:x['first_segment_dependencies']['class_0x47_type24_class02_child_presentation'].__setitem__('fixed_frame_substitute_forbidden',False))]:
 x=copy.deepcopy(report);mutate(x);reject(x,label)
for label,mutate in [('class4e1-owner',lambda x:x['first_segment_dependencies']['class_0x4e_type24_variant4_effect']['variant1_collision_effect']['first_collision'].__setitem__('attacker_attack_record','0x00030ce2')),('class4e1-order',lambda x:x['first_segment_dependencies']['class_0x4e_type24_variant4_effect']['variant1_collision_effect']['allocation'].__setitem__('scheduler_guard','projectile first')),('class4e1-retained-presentation',lambda x:x['first_segment_dependencies']['class_0x4e_type24_variant4_effect']['variant1_collision_effect']['allocation']['fixed_slot_reuse_presentation'].__setitem__('animation_record','0x00092914')),('class4e1-fixed-frame',lambda x:x['first_segment_dependencies']['class_0x4e_type24_variant4_effect']['variant1_collision_effect'].__setitem__('fixed_frame_substitute_forbidden',False))]:
 x=copy.deepcopy(report);mutate(x);reject(x,label)
for label,mutate in [('special-collision-frame',lambda x:x['first_segment_dependencies']['class_0x4e_type24_variant4_effect']['variant1_collision_effect']['player_special_collision'].__setitem__('source_frame_u16',2805)),('special-collision-damage',lambda x:x['first_segment_dependencies']['class_0x4e_type24_variant4_effect']['variant1_collision_effect']['player_special_collision']['class1f_target'].__setitem__('damage_s16',126)),('special-collision-hurt',lambda x:x['first_segment_dependencies']['class_0x4e_type24_variant4_effect']['variant1_collision_effect']['player_special_collision']['class1f_target']['hurt_record'].__setitem__('x_half_u8',30)),('special-collision-order',lambda x:x['first_segment_dependencies']['class_0x4e_type24_variant4_effect']['variant1_collision_effect']['player_special_collision']['scheduler_order'].reverse()),('special-collision-target',lambda x:x['first_segment_dependencies']['class_0x4e_type24_variant4_effect']['variant1_collision_effect']['player_special_collision']['record20_targets'].pop()),('special-ko-record',lambda x:x['first_segment_dependencies']['class_0x4e_type24_variant4_effect']['variant1_collision_effect']['player_special_collision']['class1f_target']['source_ko']['reaction_records'][0].__setitem__('animation_record','0x0012e04c')),('special-ko-vector',lambda x:x['first_segment_dependencies']['class_0x4e_type24_variant4_effect']['variant1_collision_effect']['player_special_collision']['class1f_target']['source_ko'].__setitem__('launch_y_velocity_16_16',0x00098000)),('special-ko-hold',lambda x:x['first_segment_dependencies']['class_0x4e_type24_variant4_effect']['variant1_collision_effect']['player_special_collision']['class1f_target']['source_ko'].__setitem__('entry_hold_ticks_u8',6))]:
 x=copy.deepcopy(report);mutate(x);reject(x,label)
x=copy.deepcopy(report)
x['first_segment_dependencies']['class_0x4e_type24_variant4_effect'][
 'variant1_collision_effect']['player_special_collision'][
  'class1f_traversal_cadence']['max_damage_targets_per_frame_u8']=2
reject(x,'special-collision-cadence')
for label,mutate in [('class4e0-owner',lambda x:x['first_segment_dependencies']['class_0x4e_type24_variant4_effect']['variant0_collision_effect']['first_collision'].__setitem__('attacker_attack_record','0x00130b6c')),('class4e0-slot',lambda x:x['first_segment_dependencies']['class_0x4e_type24_variant4_effect']['variant0_collision_effect']['allocation'].__setitem__('source_slot','0x00ffc380')),('class4e0-rng',lambda x:x['first_segment_dependencies']['class_0x4e_type24_variant4_effect']['variant0_collision_effect']['state0'].__setitem__('first_seed_after','0x62d0')),('class4e0-animation',lambda x:x['first_segment_dependencies']['class_0x4e_type24_variant4_effect']['variant0_collision_effect']['active_state']['animation_records'].pop()),('class4e0-fixed-frame',lambda x:x['first_segment_dependencies']['class_0x4e_type24_variant4_effect']['variant0_collision_effect'].__setitem__('fixed_frame_substitute_forbidden',False))]:
 x=copy.deepcopy(report);mutate(x);reject(x,label)
for label,mutate in [('class4e10-impact-field',lambda x:x['first_segment_dependencies']['class_0x4e_type24_variant4_effect']['variant10_collision_effect']['allocation']['variant_field'].__setitem__('attack_record_offset_u8',10)),('class4e10-rng',lambda x:x['first_segment_dependencies']['class_0x4e_type24_variant4_effect']['variant10_collision_effect']['state0'].__setitem__('first_seed_after','0xe34d')),('class4e10-animation',lambda x:x['first_segment_dependencies']['class_0x4e_type24_variant4_effect']['variant10_collision_effect']['active_state']['animation_records'].pop()),('class4e10-fixed-frame',lambda x:x['first_segment_dependencies']['class_0x4e_type24_variant4_effect']['variant10_collision_effect'].__setitem__('fixed_frame_substitute_forbidden',False))]:
 x=copy.deepcopy(report);mutate(x);reject(x,label)
for label,mutate in [('special-player-dispatch',lambda x:x['first_segment_dependencies']['predator_special_type24_effects'].__setitem__('player_dispatch_entry','0x024f04')),('special-health',lambda x:x['first_segment_dependencies']['predator_special_type24_effects'].__setitem__('health_cost_s16',5)),('special-audio',lambda x:x['first_segment_dependencies']['predator_special_type24_effects']['source_audio_commands_u16'].__setitem__(0,0x90)),('special-fixed-frame',lambda x:x['first_segment_dependencies']['predator_special_type24_effects'].__setitem__('fixed_frame_substitute_forbidden',False)),('class4b-owner-guard',lambda x:x['first_segment_dependencies']['predator_special_type24_effects']['class_0x4b']['state_0x0200'].__setitem__('terminal_guard','fixed frame')),('class4b-contact-lifetime',lambda x:x['first_segment_dependencies']['predator_special_type24_effects']['class_0x4b']['state_0x0200'].__setitem__('owner_contact_lifetime','persistent contact')),('class4b-wrap',lambda x:x['first_segment_dependencies']['predator_special_type24_effects']['class_0x4b']['state_0x0200']['coffee_shop_wrap_witness'].__setitem__('wrapped_record_frame_u16',2837)),('class4b-animation',lambda x:x['first_segment_dependencies']['predator_special_type24_effects']['class_0x4b']['state0']['animation_records'].pop()),('class4b-offset',lambda x:x['first_segment_dependencies']['predator_special_type24_effects']['class_0x4b']['state0']['position_writes'].__setitem__(2,'x += 7')),('class3d-spawn',lambda x:x['first_segment_dependencies']['predator_special_type24_effects']['class_0x3d'].__setitem__('variant_rule','fixed frame')),('class3d-retained-y',lambda x:x['first_segment_dependencies']['predator_special_type24_effects']['class_0x3d']['unwritten_field_retention'].__setitem__('first_class3d_y_s16',0)),('class3d-animation',lambda x:x['first_segment_dependencies']['predator_special_type24_effects']['class_0x3d']['state0']['animation_records'].pop()),('class3d-motion',lambda x:x['first_segment_dependencies']['predator_special_type24_effects']['class_0x3d']['state_0x0200']['movement_offsets_s16'][0].__setitem__(0,-60))]:
 x=copy.deepcopy(report);mutate(x);reject(x,label)
for label,mutate in [('type16-owner-state',lambda x:x['first_segment_dependencies']['class_0x1f_type16_0x06_projectile']['spawn_owner'].__setitem__('outer_state_u16','fixed frame')),('type16-parent-event',lambda x:x['first_segment_dependencies']['class_0x1f_type16_0x06_projectile']['spawn_owner']['parent_animation_records'][3].__setitem__('branch_s16',0)),('type16-motion',lambda x:x['first_segment_dependencies']['class_0x1f_type16_0x06_projectile']['initialization']['variant_motion_16_16'][0].__setitem__('x_velocity_16_16',0)),('type16-animation',lambda x:x['first_segment_dependencies']['class_0x1f_type16_0x06_projectile']['active_state']['animation_records'].pop()),('type16-attack-box',lambda x:x['first_segment_dependencies']['class_0x1f_type16_0x06_projectile']['current_state_collision']['attack_record'].__setitem__('x_half_u8',7)),('type16-damage',lambda x:x['first_segment_dependencies']['class_0x1f_type16_0x06_projectile']['current_state_collision'].__setitem__('route_character_damage_s16',16)),('type16-contact',lambda x:x['first_segment_dependencies']['class_0x1f_type16_0x06_projectile']['current_state_collision']['contacts'].pop()),('type16-fixed-frame',lambda x:x['first_segment_dependencies']['class_0x1f_type16_0x06_projectile'].__setitem__('fixed_frame_substitute_forbidden',False))]:
 x=copy.deepcopy(report);mutate(x);reject(x,label)
for label,mutate in [('class08-stage-guard',lambda x:x['first_segment_dependencies']['class_0x08_type20_health_pickup']['stage_spawn']['record'].__setitem__('gate_u16',817)),('class08-fixed-frame',lambda x:x['first_segment_dependencies']['class_0x08_type20_health_pickup']['stage_spawn'].__setitem__('fixed_frame_substitute_forbidden',False)),('class08-attack',lambda x:x['first_segment_dependencies']['class_0x08_type20_health_pickup']['parent']['current_state_collision']['attack_record'].__setitem__('address','0x00030cd2')),('class08-rng',lambda x:x['first_segment_dependencies']['class_0x08_type20_health_pickup']['parent']['drop'].__setitem__('seed_after','0xea72')),('class08-drop-table',lambda x:x['first_segment_dependencies']['class_0x08_type20_health_pickup']['parent']['drop']['selector_source']['row_u8'].__setitem__(0,0x11)),('class08-post-drop-motion',lambda x:x['first_segment_dependencies']['class_0x08_type20_health_pickup']['parent']['post_drop_program']['debris']['primary'].__setitem__('x_velocity_s32',0x00040000)),('class08-visible-projection',lambda x:x['first_segment_dependencies']['class_0x08_type20_health_pickup']['parent']['post_drop_program']['debris'].__setitem__('visible_position_projection','copy complete internal long')),('pickup-scheduler-order',lambda x:x['first_segment_dependencies']['class_0x08_type20_health_pickup']['pickup'].__setitem__('scheduler_order','record28 before record20')),('pickup-motion-substate',lambda x:x['first_segment_dependencies']['class_0x08_type20_health_pickup']['pickup']['initialization'].__setitem__('motion_substate_u16',0)),('pickup-animation-loop',lambda x:x['first_segment_dependencies']['class_0x08_type20_health_pickup']['pickup']['movement'].__setitem__('animation_timer_rule','fixed frame')),('pickup-landing-fraction',lambda x:x['first_segment_dependencies']['class_0x08_type20_health_pickup']['pickup']['movement']['first_landing_result'].__setitem__('position_write','clear fractional word')),('pickup-input-sample',lambda x:x['first_segment_dependencies']['class_0x08_type20_health_pickup']['pickup']['player_interaction'].__setitem__('input_sample_rule','raw current-frame input')),('pickup-health',lambda x:x['first_segment_dependencies']['class_0x08_type20_health_pickup']['pickup']['player_interaction'].__setitem__('health_after_s16',94)),('pickup-audio',lambda x:x['first_segment_dependencies']['class_0x08_type20_health_pickup']['pickup']['player_interaction']['audio_edge'].__setitem__('command_u16','0x0207'))]:
 x=copy.deepcopy(report);mutate(x);reject(x,label)
x=copy.deepcopy(report)
x['first_segment_dependencies']['class_0x08_type20_health_pickup']['parent']['current_state_collision']['reaction_direction']['result_u8']=0
reject(x,'class08-reaction-direction')
for label,mutate in [('class05-stage-order',lambda x:x['first_segment_dependencies']['class_0x05_type20_reactive_prop']['stage_records'].reverse()),('class05-attack',lambda x:x['first_segment_dependencies']['class_0x05_type20_reactive_prop']['current_state_collision']['attack_record'].__setitem__('address','0x0011af77')),('class05-hurt',lambda x:x['first_segment_dependencies']['class_0x05_type20_reactive_prop']['current_state_collision']['hurt_record'].__setitem__('address','0x0006cd58')),('class05-impact-slot',lambda x:x['first_segment_dependencies']['class_0x05_type20_reactive_prop']['current_state_collision']['impact_allocation'].__setitem__('source_slot','0x00ffc180')),('class05-audio',lambda x:x['first_segment_dependencies']['class_0x05_type20_reactive_prop']['reaction_program']['state_0x0400'].__setitem__('audio_command_u16','0x0077')),('class05-rng',lambda x:x['first_segment_dependencies']['class_0x05_type20_reactive_prop']['reaction_program']['state_0x0400'].__setitem__('seed_before','0xcb47')),('class05-motion',lambda x:x['first_segment_dependencies']['class_0x05_type20_reactive_prop']['reaction_program']['state_0x0404']['primary'].__setitem__('x_velocity_s32',0x00050000)),('class05-fixed-frame',lambda x:x['first_segment_dependencies']['class_0x05_type20_reactive_prop'].__setitem__('fixed_frame_substitute_forbidden',False))]:
 x=copy.deepcopy(report);mutate(x);reject(x,label)
x=copy.deepcopy(report)
x['first_segment_dependencies']['class_0x09_type20_rng_owner'][
 'complete_coffee_shop_program']['fixed_frame_substitute_forbidden']=False
reject(x,'class09 complete-program fixed-frame substitute')
x=copy.deepcopy(report)
next(c for c in x['coffee_shop_scene_component_identities']['components']
     if c['type']==20 and c['class']=='0x02')['implementation_contract'][
      'scheduler_phase_evidence']['record20_exit_prefix_scheduler'][
       'route_teardown_dispatch_guard']['route_teardown_state_u16']=2
reject(x,'record20 route-teardown dispatch guard')
alias_controls = [
 ('address',lambda x:x.__setitem__('address_rule','source_actor_slot + 0x1c')),
 ('width',lambda x:x.__setitem__('width_bits',32)),
 ('value',lambda x:x.__setitem__('value_u8',0)),
 ('pointer-mask',lambda x:x['owners'][0].__setitem__('pointer_rule','clear pointer')),
 ('pair',lambda x:x['capture_identity']['b'].__setitem__('samples.tsv','0'*64)),
 ('no-causal-difference',lambda x:x['observation'].__setitem__('raw_pointer_difference_rows',0)),
 ('reader-overclaim',lambda x:x['observation'].__setitem__('reads_are_cpu_only',True)),
 ('suppression',lambda x:x['control'].__setitem__('suppressed_writes',0)),
 ('omit-write',lambda x:x['control'].__setitem__('permits_omitting_source_write',True)),
 ('normalized-gameplay',lambda x:x['capture_identity']['suppression'].__setitem__('samples.tsv','0'*64)),
 ('native-overclaim',lambda x:x.__setitem__('native_implemented',True)),
 ('physical-overclaim',lambda x:x.__setitem__('physical_saturn','PASS')),
]
for label,mutate in alias_controls:
 x=copy.deepcopy(report)
 alias=next(c for c in x['coffee_shop_type36_presentation']['classes']
            if c['class']=='0x0e')['cross_record_write_contract']
 mutate(alias)
 try:m.validate(x)
 except ValueError as error:
  assert str(error)=='class0e cross-record writer contract drift', (label,str(error))
 else:raise AssertionError('survived class0e contract control: '+label)
class0e_program_controls = [
 ('offset-sign',lambda x:x['attachment']['records'][34].__setitem__('x_offset_s8',4)),
 ('address-space',lambda x:x['attachment'].__setitem__('address_space','decrypted opcodes')),
 ('facing',lambda x:x['attachment']['records'][0].__setitem__('facing_u8',1)),
 ('selector',lambda x:x['attachment']['records'][24].__setitem__('selector_u8',0)),
 ('palette',lambda x:x['allocation']['palette_table']['values_u8'].__setitem__(31,17)),
 ('allocation-filter',lambda x:x['allocation']['effect_filter_table']['negative_indices'].pop()),
 ('state-guard',lambda x:x['active'].__setitem__('guard','fixed frame')),
 ('early-terminal-return',lambda x:x['active'].__setitem__('after_guard','return immediately')),
 ('decrement',lambda x:x['active'].__setitem__('local_timer_decrement',True)),
 ('record-offset',lambda x:x['animation_bind']['families'][0]['offsets_s16'].__setitem__(0,0)),
 ('assembly',lambda x:x['animation_bind']['records'][0].__setitem__('assembly','0x00000000')),
 ('backlink',lambda x:x['terminal'].__setitem__('backlink_guard','always clear')),
 ('release-residue',lambda x:x['terminal']['release_clears_u32_offsets'].append(0x1c)),
 ('extra-rng',lambda x:x['effects'].__setitem__('direct_rng_calls',1)),
 ('extra-audio',lambda x:x['effects'].__setitem__('direct_audio_commands',[0x77])),
 ('fixed-frame',lambda x:x.__setitem__('fixed_frame_substitute_forbidden',False)),
]
for label,mutate in class0e_program_controls:
 x=copy.deepcopy(report)
 program=next(c for c in x['coffee_shop_type36_presentation']['classes']
              if c['class']=='0x0e')['implementation_contract']
 mutate(program)
 try:m.validate(x)
 except ValueError as error:
  assert str(error)=='class0e whole-program contract drift', (label,str(error))
 else:raise AssertionError('survived class0e program control: '+label)
for label,mutate in [
 ('wrong-kind',lambda p:p['streams'][0].__setitem__('pointer_kind','SPRITE_ASSEMBLY')),
 ('wrong-destination',lambda p:p['streams'][0].__setitem__('destination_base','0x90c000')),
 ('wrong-source',lambda p:p['streams'][0].__setitem__('source_base','0x1f4600')),
 ('wrong-color',lambda p:p['streams'][0]['commands'][0]['source_colors_u16'].__setitem__(0,0)),
 ('omitted-command',lambda p:p['streams'][0]['commands'].pop()),
 ('wrong-terminator',lambda p:p['streams'][0].__setitem__('terminator_s16',0)),
 ('fixed-frame',lambda p:p.__setitem__('guard','every displayed frame')),
 ('brightness-loss',lambda p:p.__setitem__('arithmetic','destination=source')),
 ('order',lambda p:p.__setitem__('order','reverse commands'))]:
 x=copy.deepcopy(report)
 p=next(c for c in x['coffee_shop_scene_component_identities']['components']
        if c['type']==24 and c['class']=='0x0a')['implementation_contract']['palette_consumer']
 mutate(p)
 try:m.validate(x)
 except ValueError as error:assert str(error)=='class0a palette consumer source contract drift',label
 else:raise AssertionError('survived palette source-contract control: '+label)
print('Class0a palette contract: PASS (9 attributable specification controls; source suppression separately recorded)')
print('ORACLE-11 auxiliary authority tests: PASS '
      '(154 existing field controls; 12 alias and16 whole-program attributable '
      'class0e controls; these are not native behavioral kills)')
