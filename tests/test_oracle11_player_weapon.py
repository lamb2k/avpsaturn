#!/usr/bin/env python3
"""Committed ORACLE-11 weapon/projectile/resource contract controls."""
import copy, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'data/oracle11_predator_weapon_projectile_resource.json'

def validate(d):
    assert d['status']=='SOURCE_CLOSED'
    assert d['determinism']['byte_identical'] is True
    assert d['mutation_controls']=={'all_downstream_effects_asserted':True,'count':13,'no_fixed_frame_result':True,'no_visible_weapon_inference_from_0xad':True}
    p=d['authority_separation']['projectile_lifecycle']
    assert p['class']=='0x05' and p['volley'].startswith('12 attempts')
    assert p['resource_debit'].startswith('3 per successful')
    e=d['authority_separation']['equipment_resource']
    assert e['capacity']==64 and e['action_latch'].endswith('not ownership')
    assert d['resource_causal_trace']['empty']['damaging_projectile_count']==0
    assert d['resource_causal_trace']['sufficient']['spawn_count']==12
    assert d['special_causal_trace']['zero_health'].startswith('special rejected')
    implementation=d['implementation_contract']
    assert implementation['classification']=='SOURCE_CLOSED_IMPLEMENTATION_FIELDS'
    assert implementation['source_input']['button1_mask']=='0x0010'
    volley=implementation['sufficient_volley']
    assert volley['attempt_counter_type']=='s8'
    assert volley['attempt_counter_initial']==12
    assert volley['cadence_counter_type']=='u8'
    assert volley['cadence_initial']==1 and volley['cadence_reload']==4
    assert volley['spawn_tick_offsets']==list(range(0,48,4))
    assert volley['cleanup_tick_offset']==49
    assert volley['return_to_locomotion_tick_offset']==50
    assert volley['recovery_edge']=={'input_tick_offset':48,
        'cleanup_tick_offset':49,'second_entry_tick_offset':50}
    assert volley['resource_debit']==3 and volley['resource_clamp_min']==0
    assert volley['resource_capacity']==64 and volley['rng_calls']==0
    assert implementation['resource_tick']['order'].startswith('after player action')
    assert implementation['resource_tick']['normal_recharge_reload']==2
    assert implementation['resource_tick']['depleted_recharge_reload']==6
    empty=implementation['empty_fallback']
    assert empty['timer_type']=='u8' and empty['timer_initial']==16
    assert empty['cleanup_tick_offset']==17
    assert empty['return_to_locomotion_tick_offset']==18
    assert empty['damaging_projectile_count']==0
    assert len(empty['presentation_timeline'])==18
    assert empty['presentation_timeline'][1]['animation_record']=='0x001645d4'
    assert implementation['movement_facing']['baseline_invariant'] is True
    assert len(implementation['presentation_timeline'])==50
    assert implementation['return_frame']=={
        'tick':50,'action':2,'substate':2,
        'animation_record':'0x00163158','assembly':'0x00165488',
        'hurt_selector':1,'attack_selector':0}
    projectile=implementation['projectile_lifecycle_contract']
    assert projectile['spec_executable'] is True
    assert projectile['state_sequence']==[0,2,4,6] and projectile['rng_calls']==0
    init=projectile['initialization']
    assert init['writes']['motion_table']=='0x001fc1c0'
    assert init['writes']['attack_table']=='0x0003136a'
    assert init['parent_presentation_selector']['spawn_offsets_s16'][0]==[-21,84]
    assert init['parent_presentation_selector']['spawn_offsets_s16'][15]==[-47,79]
    assert init['parent_presentation_selector']['animation_selector_u8']==list(range(15,-1,-1))
    assert init['angle']['facing0_u8']==[40,42,44,46,48,50,49,47,45,43,41,40]
    assert init['angle']['facing1_u8']==[24,22,20,18,16,14,15,17,19,21,23,24]
    assert init['player_presentation_selector_u8']==[6,6,5,5,4,3,3,4,5,5,6,6]
    actor_fields=init['presentation_actor_fields']
    assert actor_fields['coordinate_mode_u8']==0
    assert actor_fields['palette_u8']==0
    assert actor_fields['object_or_u16']=='0x8000'
    assert actor_fields['determinism']=={
        'actors_tsv_byte_identical':True,'cold_runs':2}
    assert actor_fields['mutation']['projectile_facing_before']==0
    assert actor_fields['mutation']['projectile_facing_after']==1
    assert actor_fields['mutation']['first_projectile_x_before']==1181
    assert actor_fields['mutation']['first_projectile_x_after']==1213
    active=projectile['active_state']
    assert active['motion']['vectors_s16'][16]==[3072,0]
    assert active['motion']['vectors_s16'][48]==[-3072,0]
    assert active['bounds_guards'][0]['expression']=='u16(x_high - A5+0x278 + 0x50) > 0x0220'
    assert active['bounds_guards'][1]['expression']=='u16(y_high - A5+0x27c + 0x10) > 0x0120'
    assert active['update_order']==['collision guard','x bounds','y bounds','ground guard','motion','animation','visibility']
    assert projectile['impact_state']['writes']['impact_class']=='0x3a'
    assert projectile['impact_actor_contract']['spec_executable'] is True
    impact_audio=projectile['impact_actor_contract']['initialization']['audio']
    assert impact_audio['alternating_command_u16']==[0x007e,0x0148]
    assert impact_audio['selector']['route_initial']==0
    assert impact_audio['selector']['write_rule'].endswith('& 2 after the table read')
    impact_fields=projectile['impact_actor_contract']['initialization'][
        'presentation_actor_fields']
    assert impact_fields['coordinate_mode_u8']==0
    assert impact_fields['palette_u8']==0
    assert impact_fields['object_or_u16']=='0x8000'
    assert projectile['implementation_blocker'] is None
    damage=projectile['current_state_interfaces']['collision']['damage']
    assert damage['routine']=='0x01d504'
    assert damage['route_current_guards']=={
        'A5_minus_0x6762_u16':0,'A5_plus_0x244_u8':0,
        'defender_plus_0x08_u8':12,'defender_plus_0x73_u8':0}
    assert damage['baseline']=={
        'attack_selector':6,'attacker_class_index':0,'damage':24,
        'defender_class_index':16,'defense':33,
        'defense_address':'0x11420a','health_after':39,'health_before':63,
        'matrix_address':'0x115326','offense':0,
        'offense_address':'0x11542a','route_index':10}
    assert damage['mutation']['damage']==31
    assert damage['mutation']['matrix_address']=='0x11532a'
    assert damage['suppression']['baseline_writes']==8
    assert damage['suppression']['mutated_writes']==4
    empty_effect=implementation['empty_effect_variant1_contract']
    assert empty_effect['spec_executable'] is True
    assert empty_effect['state_sequence']==[0,2,4] and empty_effect['variant']==1
    assert empty_effect['initialization']['variant_offsets_s16'][1]==[0,78]
    assert [(x['timer'],x['branch']) for x in empty_effect['active_state']['presentation_records']]==[(1,0)]*8+[(8,1),(4095,-32767)]
    assert empty_effect['capture_projection']['movement_frames']==list(range(4494,4502))
    assert len(d['counterfactuals'])==13
    assert d['physical_saturn']=='UNRUN' and d['saturn_emulator']=='UNRUN'

def reject(mut,label):
    try:validate(mut)
    except AssertionError:return
    raise AssertionError('accepted mutation: '+label)

d=json.loads(ART.read_text(encoding='ascii'));validate(d)
for path,value,label in [
 (('mutation_controls','count'),12,'counterfactual removed'),
 (('authority_separation','projectile_lifecycle','class'),'0x00','wrong projectile class'),
 (('authority_separation','equipment_resource','capacity'),63,'fitted resource capacity'),
 (('resource_causal_trace','empty','damaging_projectile_count'),1,'empty fallback damage'),
 (('special_causal_trace','zero_health'),'special accepted','zero-health guard removed'),
 (('mutation_controls','no_visible_weapon_inference_from_0xad'),False,'action latch treated as equipment'),
 (('implementation_contract','source_input','button1_mask'),'0x0020','wrong Button1 mask'),
 (('implementation_contract','sufficient_volley','attempt_counter_type'),'u8','lost signed attempt counter'),
 (('implementation_contract','sufficient_volley','cadence_reload'),3,'guessed volley cadence'),
 (('implementation_contract','sufficient_volley','spawn_tick_offsets'),list(range(1,49,4)),'fixed-frame shifted volley'),
 (('implementation_contract','sufficient_volley','recovery_edge','second_entry_tick_offset'),49,'early recovery redispatch'),
 (('implementation_contract','sufficient_volley','resource_debit'),2,'wrong successful-allocation debit'),
 (('implementation_contract','resource_tick','normal_recharge_reload'),1,'wrong normal recharge'),
 (('implementation_contract','empty_fallback','timer_initial'),15,'wrong empty timer'),
 (('implementation_contract','movement_facing','baseline_invariant'),False,'movement during weapon action'),
 (('implementation_contract','projectile_lifecycle_contract','initialization','angle','facing1_u8',0),25,'wrong facing angle mapping'),
 (('implementation_contract','projectile_lifecycle_contract','initialization','presentation_actor_fields','object_or_u16'),'0x0000','wrong projectile object priority'),
 (('implementation_contract','projectile_lifecycle_contract','initialization','presentation_actor_fields','mutation','projectile_facing_after'),0,'nondiscriminating projectile facing mutation'),
 (('implementation_contract','projectile_lifecycle_contract','active_state','motion','vectors_s16',48,0),-3071,'wrong signed 16.16 motion vector'),
 (('implementation_contract','projectile_lifecycle_contract','active_state','bounds_guards',0,'expression'),'u16(x) > 0x0220','wrong bounds arithmetic'),
 (('implementation_contract','projectile_lifecycle_contract','impact_state','writes','impact_class'),'0x39','wrong impact class'),
 (('implementation_contract','projectile_lifecycle_contract','impact_actor_contract','initialization','presentation_actor_fields','palette_u8'),1,'wrong impact palette'),
 (('implementation_contract','projectile_lifecycle_contract','spec_executable'),False,'projectile contract reopened'),
 (('implementation_contract','projectile_lifecycle_contract','current_state_interfaces','collision','damage','baseline','damage'),23,'fitted baseline damage'),
 (('implementation_contract','projectile_lifecycle_contract','current_state_interfaces','collision','damage','mutation','damage'),24,'damage table mutation ignored'),
 (('implementation_contract','empty_effect_variant1_contract','variant'),0,'wrong class-0x10 variant'),
 (('implementation_contract','empty_effect_variant1_contract','initialization','variant_offsets_s16',1,1),79,'wrong empty-effect y offset'),
 (('implementation_contract','empty_effect_variant1_contract','active_state','presentation_records',9,'branch'),-32768,'wrong empty-effect terminal branch')]:
    m=copy.deepcopy(d);x=m
    for k in path[:-1]:x=x[k]
    x[path[-1]]=value;reject(m,label)
print('ORACLE-11 weapon/projectile/resource tests: PASS (28 invariant mutations rejected)')
