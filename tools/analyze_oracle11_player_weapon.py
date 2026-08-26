#!/usr/bin/env python3
"""Build the ORACLE-11 Predator Warrior weapon/projectile/resource closure."""
from __future__ import annotations
import csv, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'.deps/mame/oracle11_player_weapon_a'
RAW_ZERO=ROOT/'.deps/mame/oracle11_player_weapon_zero_a'
RAW_DAMAGE=ROOT/'.deps/mame/oracle11_player_weapon_damage_a'
OPCODES=ROOT/'.deps/mame/actorprobe/decrypted_opcodes_2m.bin'
PROGRAM=ROOT/'.deps/mame/actorprobe/decrypted_program_2m.bin'
AUTH=ROOT/'data/oracle11_predator_warrior_authority.json'
AUX=ROOT/'data/oracle11_round1_auxiliary_authority.json'
OUT=ROOT/'data/oracle11_predator_weapon_projectile_resource.json'
VARIANTS=('cold_run_1','cold_run_2','resource_empty','b1_held','repeat_startup',
 'repeat_active','repeat_recovery','special_ok','special_low_health','special_zero_health',
 'target_inside','target_outside','allocation_unavailable','target_removed',
 'lifetime_writer_suppressed','recharge_writer_frozen','pickup_actor_removed',
 'projectile_class_removed','facing_reversed')

def require(v,m):
    if not v: raise ValueError(m)
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def run(name,root=RAW):
    return {n:rows(root/name/n) for n in ('samples.tsv','writes.tsv','actors.tsv','qsound.tsv')}
def action_set(r): return {int(x['action']) for x in r['samples.tsv']}
def actor_classes(r,kind): return {x['class'] for x in r['actors.tsv'] if x['kind']==kind}
def spawned(r,kind,klass,pc):
    return [x for x in r['writes.tsv'] if x['kind']==kind and x['data']==klass+klass and x['mask']=='ff00' and x['pc']==pc]
def window(blob,a,b): return {'start':f'0x{a:06x}','end_exclusive':f'0x{b:06x}','bytes':b-a,'sha256':hashlib.sha256(blob[a:b]).hexdigest()}
def s16(blob,address): return int.from_bytes(blob[address:address+2],'big',signed=True)
def pairs_s16(blob,address,count):
    return [[s16(blob,address+i*4),s16(blob,address+i*4+2)] for i in range(count)]
def animation_record(program,address):
    return {'animation_record':f'0x{address:08x}',
      'timer':int.from_bytes(program[address:address+2],'big'),
      'branch':int.from_bytes(program[address+2:address+4],'big',signed=True),
      'assembly':f'0x{int.from_bytes(program[address+4:address+8],"big"):08x}',
      'hurt_selector':program[address+8],'attack_selector':program[address+9],
      'record_sha256':hashlib.sha256(program[address:address+16]).hexdigest()}
def box_record(program,address,stride):
    raw=list(program[address:address+stride])
    signed=lambda value:value-256 if value>127 else value
    result={'address':f'0x{address:08x}','x_center':signed(raw[0]),
      'y_center':signed(raw[1]),'x_half':raw[2],'y_half':raw[3],
      'z_center':signed(raw[4]),'z_half':raw[5],
      'record_sha256':hashlib.sha256(bytes(raw)).hexdigest()}
    if stride==16:
        result.update({'hit_value':raw[14],'knockback_mode':signed(raw[10]),
          'unknown_bytes':{f'0x{offset:02x}':raw[offset]
            for offset in (6,7,8,9,11,12,13,15)}})
    return result
def first_frame(samples,predicate):
    return int(next(x['frame'] for x in samples if predicate(x)))
def presentation(program,row,origin):
    address=int(row['anim'],16)
    return {'tick':int(row['frame'])-origin,'action':int(row['action']),
      'substate':int(row['inner']),'animation_record':f'0x{address:08x}',
      'assembly':f'0x{int.from_bytes(program[address+4:address+8],"big"):08x}',
      'hurt_selector':program[address+8],'attack_selector':program[address+9]}

manifest=json.loads((RAW/'input_manifest.json').read_text(encoding='utf-8-sig'))
require(tuple(x['name'] for x in manifest['variants'])==VARIANTS,'variant inventory drift')
for item in manifest['variants']:
    for n,h in item['sha256'].items(): require(digest(RAW/item['name']/n)==h,f"{item['name']} {n} drift")
for n in ('samples.tsv','writes.tsv','actors.tsv','qsound.tsv'):
    require(digest(RAW/'cold_run_1'/n)==digest(RAW/'cold_run_2'/n),f'baseline mismatch {n}')
r={v:run(v) for v in VARIANTS}
rz=run('special_zero_health',RAW_ZERO)
b=r['cold_run_1']
damage_runs={name:rows(RAW_DAMAGE/name/'damage.tsv') for name in
    ('cold_run_1','cold_run_2','target_removed','damage_attack_class_2')}
impact_audio_runs={name:rows(RAW_DAMAGE/name/'impact_audio.tsv') for name in
    ('cold_run_1','cold_run_2','target_removed','damage_attack_class_2')}
presentation_actor_runs={name:rows(RAW_DAMAGE/name/'actors.tsv') for name in
    ('cold_run_1','cold_run_2','facing_reversed')}
for n in ('samples.tsv','writes.tsv','actors.tsv','qsound.tsv','damage.tsv',
          'impact_audio.tsv'):
    require(digest(RAW_DAMAGE/'cold_run_1'/n)==
            digest(RAW_DAMAGE/'cold_run_2'/n),
            f'damage supplement baseline mismatch {n}')
for n in ('samples.tsv',):
    require(digest(RAW_DAMAGE/'cold_run_1'/n)==digest(RAW/'cold_run_1'/n),
            f'damage supplement changed gameplay projection {n}')
require(0x0c00 in action_set(b),'Button1 did not dispatch 0x0c00')
require(len(spawned(b,'record4','05','0257f4'))==12,'PW shot count/cadence drift')
require(min(int(x['resource']) for x in b['samples.tsv'])==28,'resource debit drift')
require(0x1a00 in action_set(r['resource_empty']),'empty fallback action missing')
require('10' in actor_classes(r['resource_empty'],'record24'),'empty fallback class 0x10 missing')
require(not spawned(r['resource_empty'],'record4','05','0257f4'),'empty fallback spawned damaging projectile')
for v in ('b1_held','repeat_startup','repeat_active'):
    require(len(spawned(r[v],'record4','05','0257f4'))==12,f'{v} repeated startup')
require(len(spawned(r['repeat_recovery'],'record4','05','0257f4'))==22,'recovery repeat did not start bounded second volley')
require(0x0800 in action_set(r['special_ok']),'special dispatch missing')
require({'20','47'} <= actor_classes(r['special_ok'],'record24'),'PW special actor family missing')
require(0x0800 not in action_set(rz) and 0x0c00 in action_set(rz),'zero-health special guard drift')
require(min(int(x['health']) for x in r['special_low_health']['samples.tsv'])<=0,'low health special clamp drift')
require(not spawned(r['allocation_unavailable'],'record4','05','0257f4'),'empty allocator still spawned class 5')
require(max(int(x['award_timer']) for x in r['pickup_actor_removed']['samples.tsv'])==600,'resource award timer lost with display actor')
require(sum(1 for x in r['pickup_actor_removed']['actors.tsv'] if x['class']=='54')==1,'class 0x54 removal control drift')
require(len({x['frame'] for x in r['lifetime_writer_suppressed']['actors.tsv'] if x['kind']=='record4' and x['class']=='05'})>200,'lifetime suppression had no causal effect')
require(min(int(x['resource']) for x in r['recharge_writer_frozen']['samples.tsv'][120:])==24,'recharge freeze drift')
require(not spawned(r['projectile_class_removed'],'record4','05','0257f4'),'scheduler-class removal ineffective')

op=OPCODES.read_bytes()
program=PROGRAM.read_bytes()
aux=json.loads(AUX.read_text(encoding='utf-8'))
class10_aux=next(x for x in aux['archetypes']
    if x['type']==24 and x['class']=='0x10')
require(class10_aux['classification']=='SOURCE_CLOSED' and
        class10_aux['dispatch_entry']=='0x079ffc' and
        class10_aux['rng']['calls']==0 and
        class10_aux['counterfactual']['classification']=='PASS',
        'accepted class-0x10 auxiliary authority drift')

projectile_spawn_offsets=pairs_s16(program,0x030e58,16)
projectile_presentation_selectors=list(program[0x030f19:0x030f29])
projectile_presentation_offsets=[int.from_bytes(program[0x030f48+i*2:0x030f4a+i*2],'big') for i in range(16)]
projectile_presentation=[]
for offset in projectile_presentation_offsets:
    first=0x030f48+offset
    projectile_presentation.append({
      'first':animation_record(program,first),
      'terminal':animation_record(program,first+16)})
projectile_angles_facing0=list(program[0x025ad2:0x025ade])
projectile_angles_facing1=[(-x)&0x3f for x in projectile_angles_facing0]
projectile_player_selectors=list(program[0x025ac6:0x025ad2])
projectile_motion=pairs_s16(program,0x001fc1c0,64)
class10_offsets=pairs_s16(op,0x07a050,4)
class10_presentation_offsets=[int.from_bytes(program[0x07a08e+i*2:0x07a090+i*2],'big') for i in range(4)]
class10_variant1_records=[animation_record(program,0x07a09c+i*16) for i in range(10)]
class3a_dispatch=int.from_bytes(op[0x01bb7c:0x01bb80],'big')
class3a_variant_offsets=[s16(program,0x086fd0+i*2) for i in range(5)]
class3a_variant0_records=[animation_record(program,0x086fdc+i*16) for i in range(5)]
class3a_audio_commands=[int.from_bytes(op[0x002702+i*2:0x002704+i*2],'big') for i in range(2)]
projectile_hurt_rel=s16(program,0x03136a)
projectile_attack_rel=s16(program,0x03136c)
projectile_hurt=[box_record(program,0x03136a+projectile_hurt_rel,8)]
projectile_attack=[box_record(program,0x03136a+projectile_attack_rel+i*16,16) for i in range(3)]
require(projectile_spawn_offsets==[[-21,84],[22,79],[36,68],[43,55],[43,38],[32,26],[16,16],[-10,12],[-24,11],[-46,14],[-54,17],[-66,25],[-75,37],[-76,51],[-70,64],[-47,79]],'class-0x05 spawn offset table drift')
require(projectile_presentation_selectors==list(range(15,-1,-1)),'class-0x05 presentation selector table drift')
require(projectile_presentation_offsets==[34+36*i for i in range(16)],'class-0x05 presentation base table drift')
require(projectile_angles_facing0==[40,42,44,46,48,50,49,47,45,43,41,40] and
        projectile_angles_facing1==[24,22,20,18,16,14,15,17,19,21,23,24],
        'class-0x05 angle/facing table drift')
require(projectile_player_selectors==[6,6,5,5,4,3,3,4,5,5,6,6],
        'class-0x05 player presentation selector drift')
require(projectile_motion[0]==[0,3510] and projectile_motion[16]==[3072,0] and
        projectile_motion[32]==[0,-3510] and projectile_motion[48]==[-3072,0] and
        projectile_motion[63]==[-300,3492], 'class-0x05 64-vector table drift')
require(class10_offsets==[[0,84],[0,78],[0,84],[0,68]] and
        class10_presentation_offsets==[14,14,14,862],
        'class-0x10 offset/presentation table drift')
require([(x['timer'],x['branch']) for x in class10_variant1_records]==
        [(1,0)]*8+[(8,1),(4095,-32767)],
        'class-0x10 variant-1 presentation sequence drift')
require(class3a_dispatch==0x086f62 and
        class3a_variant_offsets==[12,96,196,248,348],
        'class-0x3a dispatch/variant table drift')
require([(x['timer'],x['branch'],x['assembly']) for x in class3a_variant0_records]==[
        (2,0,'0x00087180'),(2,0,'0x0008718e'),(2,0,'0x0008719c'),
        (2,0,'0x000871aa'),(2,-32768,'0x000871aa')],
        'class-0x3a variant-0 presentation drift')
require(class3a_audio_commands==[0x007e,0x0148],
        'class-0x3a audio command table drift')
require(projectile_hurt_rel==4 and projectile_attack_rel==12 and
        projectile_hurt[0]['x_half']==0 and
        [(x['x_center'],x['x_half'],x['y_half'],x['z_half'],x['hit_value'],x['knockback_mode']) for x in projectile_attack]==[
          (0,0,0,0,0,0),(16,18,5,8,0,-1),(16,18,5,8,0,0)],
        'class-0x05 collision table drift')
base_samples=b['samples.tsv']
entry=first_frame(base_samples,lambda x:int(x['action'])==0x0c00)
complete=first_frame(base_samples,lambda x:int(x['frame'])>entry and int(x['action'])==0)
returned=first_frame(base_samples,lambda x:int(x['frame'])>complete and int(x['action'])==2)
spawn_frames=[int(x['frame']) for x in spawned(b,'record4','05','0257f4')]
require([x-entry for x in spawn_frames]==list(range(0,48,4)),
        'Button1 source cadence implementation boundary drift')
require(complete-entry==49 and returned-entry==50,
        'Button1 recovery implementation boundary drift')
repeat_samples=r['repeat_recovery']['samples.tsv']
repeat_second_entry=first_frame(repeat_samples,lambda x:
  int(x['frame'])>entry and int(x['action'])==0x0c00)
repeat_edge=first_frame(repeat_samples,lambda x:
  int(x['frame'])>entry and int(x['input'])&0x10 and
  not (int(repeat_samples[repeat_samples.index(x)-1]['input'])&0x10))
require(repeat_edge-entry==48 and repeat_second_entry-entry==50,
        'Button1 recovery-edge redispatch boundary drift')
weapon_rows=[x for x in base_samples if entry<=int(x['frame'])<=complete]
require(len({(x['x'],x['y'],x['z'],x['facing']) for x in weapon_rows})==1,
        'Button1 movement/facing hold drift')
empty_samples=r['resource_empty']['samples.tsv']
empty_entry=first_frame(empty_samples,lambda x:int(x['action'])==0x1a00)
empty_complete=first_frame(empty_samples,lambda x:int(x['frame'])>empty_entry and int(x['action'])==0)
empty_return=first_frame(empty_samples,lambda x:int(x['frame'])>empty_complete and int(x['action'])==2)
require(empty_complete-empty_entry==17 and empty_return-empty_entry==18,
        'empty-resource recovery implementation boundary drift')
class3a_rows=[x for x in b['actors.tsv'] if x['kind']=='record24' and x['class']=='3a']
require(class3a_rows and not [x for x in r['projectile_class_removed']['actors.tsv']
        if x['kind']=='record24' and x['class']=='3a'],
        'class-0x3a downstream suppression drift')
class3a_slot=[x for x in b['actors.tsv'] if x['slot']=='ffc100' and x['class']=='3a']
require([int(x['frame']) for x in class3a_slot]==list(range(4535,4544)) and
        [int(x['state']) for x in class3a_slot]==[2]*8+[4] and
        [int(x['anim'],16) for x in class3a_slot]==
          [0x086fdc,0x086fec,0x086fec,0x086ffc,0x086ffc,
           0x08700c,0x08700c,0x08701c,0x08701c],
        'class-0x3a captured lifecycle drift')
collision_writes=[x for x in b['writes.tsv'] if x['kind']=='record4' and
        x['address']=='ff86c0' and x['frame']=='4492']
require([(x['pc'],x['data'],x['mask']) for x in collision_writes]==
        [('030d6e','0000','ffff'),('01cc1a','ffff','ffff')],
        'class-0x05 collision writer order drift')
target_before=next(x for x in b['actors.tsv'] if x['slot']=='ff9e80' and x['frame']=='4492')
target_after=next(x for x in b['actors.tsv'] if x['slot']=='ff9e80' and x['frame']=='4493')
require((target_before['class'],int(target_before['state']),int(target_before['inner']),
         int(target_before['health']),int(target_before['anim'],16))==
        ('1f',2,0,63,0x12d8d0) and
         (int(target_after['state']),int(target_after['inner']),int(target_after['health']))==
        (2,2,39), 'class-0x05 target damage/HIT projection drift')
damage_base=damage_runs['cold_run_1']
damage_removed=damage_runs['target_removed']
damage_mutated=damage_runs['damage_attack_class_2']
require(len(damage_base)==8 and len(damage_removed)==4 and
        max(int(x['frame']) for x in damage_removed)==4504,
        'class-0x05 target-removal damage suppression drift')
base_damage_row=damage_base[0]
require({k:base_damage_row[k] for k in (
        'pc','attacker','defender','attack_record','a5','global_mode_word',
        'defender_active8','global_modifier244','defender_modifier73',
        'attacker_5e','route_1ea','defender_57','attack_selector',
        'offense_address','offense_value','defense_address','defense_value',
        'matrix_address','damage','health_before','health_after')}=={
        'pc':'01d590','attacker':'ff8680','defender':'ff9e80',
        'attack_record':'031396','a5':'ff8000','global_mode_word':'0000',
        'defender_active8':'0c','global_modifier244':'00',
        'defender_modifier73':'00','attacker_5e':'00','route_1ea':'000a',
        'defender_57':'10','attack_selector':'06',
        'offense_address':'11542a','offense_value':'00',
        'defense_address':'11420a','defense_value':'21',
        'matrix_address':'115326','damage':'18','health_before':'003f',
        'health_after':'0027'}, 'class-0x05 exact damage lookup drift')
mutated_damage_row=next(x for x in damage_mutated
    if x['attacker_5e']=='02')
require({k:mutated_damage_row[k] for k in (
        'frame','route_1ea','attack_selector','offense_address','offense_value',
        'defense_address','defense_value','matrix_address','damage',
        'health_before','health_after')}=={
        'frame':'4525','route_1ea':'000a','attack_selector':'06',
        'offense_address':'11546a','offense_value':'04',
        'defense_address':'11420a','defense_value':'21',
        'matrix_address':'11532a','damage':'1f','health_before':'0027',
        'health_after':'0008'}, 'class-0x05 attacker-class table mutation drift')
impact_audio_base=impact_audio_runs['cold_run_1']
impact_audio_by_frame={int(x['frame']):x for x in impact_audio_base}
require((impact_audio_by_frame[4534]['selector_ff0eda'],
         impact_audio_by_frame[4534]['class3a_count'])==('00','0') and
        (impact_audio_by_frame[4535]['selector_ff0eda'],
         impact_audio_by_frame[4535]['class3a_count'])==('02','1') and
        (impact_audio_by_frame[4537]['selector_ff0eda'],
         impact_audio_by_frame[4537]['class3a_count'])==('00','4'),
        'class-0x3a alternating audio selector chronology drift')
projectile_presentation_actors=[x for x in
    presentation_actor_runs['cold_run_1']
    if x['kind']=='record4' and x['class']=='05' and int(x['frame'])>=4493]
impact_presentation_actors=[x for x in
    presentation_actor_runs['cold_run_1']
    if x['kind']=='record24' and x['class']=='3a']
reversed_projectile_actors=[x for x in
    presentation_actor_runs['facing_reversed']
    if x['kind']=='record4' and x['class']=='05' and int(x['frame'])>=4493]
require(projectile_presentation_actors and impact_presentation_actors and
        reversed_projectile_actors,
        'bounded projectile/impact presentation actor evidence missing')
require({(x['mode'],x['palette'],x['facing'],x['object_or'])
         for x in projectile_presentation_actors}=={('0','0','0','8000')},
        'class-0x05 presentation actor fields drift')
require({(x['mode'],x['palette'],x['facing'],x['object_or'])
         for x in impact_presentation_actors}=={('0','0','0','8000')},
        'class-0x3a presentation actor fields drift')
require({x['facing'] for x in reversed_projectile_actors}=={'1'} and
        int(reversed_projectile_actors[0]['x']) >
            int(projectile_presentation_actors[0]['x']),
        'class-0x05 facing presentation mutation was not discriminating')
presentation_actor_fields={
  'coordinate_mode_u8':0,'palette_u8':0,'object_or_u16':'0x8000',
  'source_fields':{'coordinate_mode':'actor +0x0d u8',
    'palette':'actor +0x0e u8','facing':'actor +0x0f u8',
    'object_or':'actor +0x2e u16'},
  'determinism':{'cold_runs':2,'actors_tsv_byte_identical':True},
  'mutation':{'control':'player facing forced from 0 to 1 before Button1 dispatch',
    'projectile_facing_before':0,'projectile_facing_after':1,
    'first_projectile_x_before':int(projectile_presentation_actors[0]['x']),
    'first_projectile_x_after':int(reversed_projectile_actors[0]['x'])}}
implementation_contract={
 'classification':'SOURCE_CLOSED_IMPLEMENTATION_FIELDS',
 'source_input':{'button1_mask':'0x0010','guard':'new Button1 edge after B1+B2 guard; normal player state and no conflicting action latch'},
 'state_dispatch':{'sufficient_entry_action':'0x0c00','sufficient_active_action':'0x0c02','empty_entry_action':'0x1a00','empty_active_action':'0x1a02','cleanup_action':'0x0000','return_locomotion_action':'0x0002'},
 'sufficient_volley':{'attempt_counter_type':'s8','attempt_counter_initial':12,
   'attempt_counter_rule':'decrement before allocation; signed negative completes without allocation',
   'cadence_counter_type':'u8','cadence_initial':1,'cadence_reload':4,
   'spawn_tick_offsets':[x-entry for x in spawn_frames],
   'cleanup_tick_offset':complete-entry,'return_to_locomotion_tick_offset':returned-entry,
   'recovery_edge':{'input_tick_offset':repeat_edge-entry,
     'cleanup_tick_offset':complete-entry,
     'second_entry_tick_offset':repeat_second_entry-entry},
   'allocator_guard':'record-type-4 allocator returns nonzero','allocation_failure_rule':'advance cadence without resource debit',
   'successful_allocation_writes':{'active_increment':1,'class':'0x05','variant':'0 except attempt counter 4 writes 1','position':'copy player x/y/z','facing':'copy player facing','owner':'player low-word pointer','attack_table':'0x03136a'},
   'resource_debit':3,'resource_clamp_min':0,'resource_capacity':64,
   'recharge_countdown_after_success':12,'rng_calls':0,
   'scheduler_position':'record type 4 at 0x01b846 before 8/12/16/20/24/28/36'},
 'resource_tick':{'order':'after player action/projectile allocation and before HUD projection',
   'normal_recharge_reload':2,'depleted_recharge_reload':6,
   'rule':'when meter is below 64, decrement u8 countdown; zero increments meter by one and reloads by depleted latch'},
 'empty_fallback':{'timer_type':'u8','timer_initial':16,
   'cleanup_tick_offset':empty_complete-empty_entry,
   'return_to_locomotion_tick_offset':empty_return-empty_entry,
   'auxiliary_actor':{'record_type':24,'class':'0x10','position':'copy player x/y','facing':'copy player facing'},
   'damaging_projectile_count':0,
   'presentation_timeline':[presentation(program,x,empty_entry) for x in empty_samples
     if empty_entry<=int(x['frame'])<=empty_complete]},
 'movement_facing':{'rule':'hold x/y/z and facing for the complete Button1 action','baseline_invariant':True},
 'presentation_timeline':[presentation(program,x,entry) for x in weapon_rows],
 'return_frame':presentation(program,next(x for x in base_samples
   if int(x['frame'])==returned),entry),
 'projectile_lifecycle_contract':{
   'spec_executable':True,
   'record_type':4,'class':'0x05','dispatch':'0x030d34','state_type':'u8',
   'state_sequence':[0,2,4,6],
   'scheduler_position':'record type 4 before record types 8/12/16/20/24/28/36',
   'rng_calls':0,
    'initialization':{
      'guard':'state 0','writes':{
        'state':2,'motion_table':'0x001fc1c0','attack_table':'0x0003136a',
        'target_pointer':'0x8000','collision_result':0,
        'visibility_latch':0,'active_collision':1},
      'presentation_actor_fields':presentation_actor_fields,
     'parent_presentation_selector':{
       'read':'parent +0x24 low byte u8','route_reachable_values':[3,4,5,6],
       'spawn_offsets_s16':projectile_spawn_offsets,
       'animation_selector_u8':projectile_presentation_selectors,
       'presentation_offsets_u16':projectile_presentation_offsets,
       'presentation_sequences':projectile_presentation},
     'position_rule':'add selected signed s16 x/y offsets to the high words of signed 16.16 x/y; negate x offset when facing byte +0x0f is zero; add one to z high word',
     'angle':{
       'attempt_indices_after_decrement':'11 down to 0 in time order',
       'facing0_u8':projectile_angles_facing0,
       'facing1_u8':projectile_angles_facing1,
       'rule':'read signed source angle byte by attempt index; when player facing is nonzero negate it, then mask to 0x3f'},
     'player_presentation_selector_u8':projectile_player_selectors},
   'active_state':{
     'guard':'state 2','collision_guard':'signed s16 +0x40 < 0 writes state/substate long 0x06000000; release occurs through state 6 on the next class dispatch',
     'bounds_guards':[
       {'axis':'x','type':'u16','expression':'u16(x_high - A5+0x278 + 0x50) > 0x0220','result':'immediate record-type-4 release'},
       {'axis':'y','type':'u16','expression':'u16(y_high - A5+0x27c + 0x10) > 0x0120','result':'immediate record-type-4 release'}],
     'ground_guard':'u16(y_high) < u16(z_high) enters state 4 before motion/animation/visibility',
     'motion':{'angle_type':'u8 masked 0x3f','table':'0x001fc1c0','vectors_s16':projectile_motion,'arithmetic':'sign-extend each s16 component, shift left 8, then add in x-before-y order to signed 16.16 positions'},
     'update_order':['collision guard','x bounds','y bounds','ground guard','motion','animation','visibility']},
   'impact_state':{
     'guard':'state 4','writes':{'projectile_state':6,
       'allocation':'record type 24 via 0x0177da if available',
       'impact_active':1,'impact_class':'0x3a','impact_variant':0,
       'impact_position':'copy projectile x/y/z high words'},
     'allocation_failure':'projectile remains state 6 and proceeds to release'},
   'impact_actor_contract':{
     'spec_executable':True,'record_type':24,'class':'0x3a','variant':0,
     'dispatch':'0x086f62','state_type':'u8','state_sequence':[0,2,4],
     'scheduler_position':'record type 24 after record types 4/8/12/16/20',
     'rng_calls':0,
      'initialization':{'guard':'state 0','writes':{'state':2,'substate':0,
        'facing':0,'target_pointer':'0x8000'},
        'presentation_actor_fields':presentation_actor_fields,
       'variant_offsets_s16':class3a_variant_offsets,
       'variant0_presentation_records':class3a_variant0_records,
       'audio':{'guard':'variant == 0','caller':'0x0026c2',
         'shared_dispatch_entry':'0x003a88','command_table':'0x002702',
         'alternating_command_u16':class3a_audio_commands,
         'selector':{'storage':'A5-0x7126 u8','route_initial':0,
           'read_rule':'use selector value 0 or 2 as byte offset into the two-word command table',
           'write_rule':'selector = u8(selector + 2) & 2 after the table read',
           'capture_projection':{'frame_4534':[0,0],
             'frame_4535':[2,1],'frame_4537':[0,4]}},
         'argument_rule':'d2 starts at 6, 0x003abc adds source spatial bits, and facing selects high word 0x00060000 or 0x00050000 before the shared wrapper',
         'semantic_sound_name':'UNKNOWN'}},
     'active_state':{'guard':'state 2','terminal_guard':'signed animation branch word +0x24 < 0 enters state 4 before animation','variant2_only_movement':'when variant == 2 and A5+0x1e8 == 10, add A5+0x2c0 s16 to x high word','variant0_movement':'none','update_order':['terminal branch guard','variant-2 movement guard','animation','visibility']},
     'release_state':{'guard':'state 4 or 6','routine':'0x0177f0','result':'zero/release record type 24 in the same dispatch'},
     'capture_projection':{'slot':'0xffc100','first_active_frame':4535,
       'state4_frame':4543,'release_frame':4543,
       'animation_records':[f'0x{int(x["anim"],16):08x}' for x in class3a_slot]},
     'suppression_control':'removing class-0x05 from its scheduler produces zero downstream type-24 class-0x3a actors'},
   'release_state':{'guard':'state 6','routine':'0x017754','result':'zero/release record type 4 in the same dispatch'},
   'current_state_interfaces':{
     'bounds':'A5+0x278:s16 and A5+0x27c:s16 are the accepted current route/navigation bound fields',
      'collision':{'scheduler_pass':'0x01cbcc record-type-4 attackers against record-type-12 defenders in ascending pool/list order','predicate':'0x01d116 then shared overlap 0x01d25e','guards':['defender active byte == 1','defender +0x70 suppress == 0','per-attacker latch differs when attacker +0x65 is nonnegative','attacker attack selector nonzero','defender hurt selector nonzero'],'writer_order':['0x030d6e clears projectile +0x40 during class-0x05 state 0','0x01cc14 writes -1 to projectile +0x40 after successful current-state contact; trace reports successor PC 0x01cc1a','0x01cc1a writes projectile +0x6e = 1','0x01cc20 clears projectile +0x71 unless the global branch increments it'],'projectile_table':{'table_set':'0x03136a','hurt_relative_s16':projectile_hurt_rel,'attack_relative_s16':projectile_attack_rel,'hurt_entries':projectile_hurt,'attack_entries':projectile_attack},'target_table_set':'0x130ac8','captured_contact':{'frame':4492,'projectile_slot':'0xff8680','target_slot':'0xff9e80','target_animation_record':'0x0012d8d0','target_hurt_selector':1,'target_state_before':'2:0','target_state_after':'2:2','health_before':63,'health_after':39,'projectile_collision_result':-1,'projectile_consumes_result_next_dispatch':True},
        'damage':{'routine':'0x01d504','write_pc_successor':'0x01d590',
          'route_current_guards':{'A5_minus_0x6762_u16':0,
            'defender_plus_0x08_u8':12,'A5_plus_0x244_u8':0,
            'defender_plus_0x73_u8':0},
          'reads':{'attacker_class_index':'u8 attacker +0x5e',
            'route_index':'u16 A5 +0x1ea','defender_class_index':'u8 defender +0x57',
            'attack_selector':'u8 attack record +9'},
          'arithmetic':['offense = u8(0x115420 + attacker_class_index * 32 + route_index)',
            'damage_index = u8(offense + attack_selector)',
            'defense = u8(0x114000 + defender_class_index * 32 + route_index)',
            'damage = u8(0x1142a0 + defense * 128 + damage_index)',
            'health = s16(health - damage); clamp negative result to -1'],
          'baseline':{'attacker_class_index':0,'route_index':10,
            'defender_class_index':16,'attack_selector':6,
            'offense_address':'0x11542a','offense':0,
            'defense_address':'0x11420a','defense':33,
            'matrix_address':'0x115326','damage':24,
            'health_before':63,'health_after':39},
          'mutation':{'control':'attacker +0x5e = 2 for later projectiles',
            'offense_address':'0x11546a','offense':4,
            'matrix_address':'0x11532a','damage':31,
            'health_before':39,'health_after':8},
          'suppression':{'control':'target removed at the accepted guard',
            'baseline_writes':8,'mutated_writes':4,'last_mutated_frame':4504}}}},
   'implementation_blocker':None},
 'empty_effect_variant1_contract':{
   'spec_executable':True,'record_type':24,'class':'0x10','variant':1,
   'dispatch':'0x079ffc','state_type':'u8','state_sequence':[0,2,4],
   'scheduler_position':'record type 24 after record types 4/8/12/16/20',
   'rng_calls':0,
   'allocation':{'guard':'Button1 empty-resource entry and record-type-24 allocator succeeds','writes':{'active':1,'class':'0x10','variant':1,'x':'copy player x high word','y':'copy player y high word','spawn_facing_selector':'copy player facing'}},
   'initialization':{'guard':'state 0','writes':{'state':2,'target_pointer':'0x8000','record_type':24,'facing':0},'variant_offsets_s16':class10_offsets,'variant_presentation_offsets_u16':class10_presentation_offsets,'position_rule':'add variant signed s16 x/y offsets; negate x when spawn-facing selector is zero'},
   'active_state':{'guard':'state 2','terminal_guard':'signed animation branch word +0x24 < 0 enters state 4','movement_guard':'animation branch low byte +0x25 == 0 adds 4 to y high word before animation and visibility','update_order':['terminal branch guard','conditional y movement','animation','visibility'],'presentation_records':class10_variant1_records},
   'release_state':{'guard':'state 4 or 6','routine':'0x0177f0','result':'zero/release record type 24 in the same dispatch'},
   'capture_projection':{'spawn_frame':4492,'first_active_frame':4493,'spawn_position':[1197,395],'movement_frames':[4494,4495,4496,4497,4498,4499,4500,4501],'last_position':[1197,427],'state4_frame':4510},
   'accepted_auxiliary_evidence':{'artifact':'data/oracle11_round1_auxiliary_authority.json','artifact_sha256':digest(AUX),'suppression_capture':class10_aux['counterfactual']['capture'],'suppression_count':class10_aux['counterfactual']['suppression_count']}},
   'mutation_controls':['reject Button1 held redispatch','reject cadence other than ticks 0..44 step 4','reject debit without allocation','reject debit other than 3 or missing zero clamp','reject recovery before tick 49','reject movement or facing during action','reject recharge before action update','reject fixed-frame projectile hit or removal','reject fitted damage by mutating attacker class and requiring the selected source-table result','reject projectile/impact coordinate mode, palette, object priority, or facing drift']}
report={
 'schema':1,'task':'ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE','status':'SOURCE_CLOSED',
 'scope':'one-player Predator Warrior Round 1 route-reachable Button1 volley, empty-resource fallback, B1+B2 special, projectile/effect actors, resource meter/recharge, temporary resource award, collision/damage and gameplay audio ownership',
 'determinism':{'independent_cold_runs':2,'byte_identical':True,'identical_files':['samples.tsv','writes.tsv','actors.tsv','qsound.tsv']},
 'source_identity':{
  'button_dispatch':window(op,0x01a75e,0x01a8a0),'pw_button1_action':window(op,0x02576a,0x0258a8),
  'empty_fallback':window(op,0x019f34,0x019f98),'record4_class5':window(op,0x030d34,0x030e58),
  'record4_class5_motion':window(op,0x016248,0x016284),'record4_class5_spawn_table':window(program,0x030e58,0x030e98),
   'record4_class5_presentation_tables':window(program,0x030f19,0x030f68),
   'record4_class5_presentation_assemblies':window(program,0x0311aa,0x03136a),
   'record24_class3a_presentation_assemblies':window(program,0x087180,0x0871b8),
   'record24_class10':window(op,0x079ffc,0x07a08e),
  'record24_class10_variant1_tables':window(program,0x07a08e,0x07a13c),
  'special_action':window(op,0x024f04,0x02501e),'special_health_debit':window(op,0x01b492,0x01b4bc),
  'special_class20':window(op,0x07f9a8,0x07fb42),'special_class47':window(op,0x08eb86,0x08ed32),
   'resource_hud_writer':window(op,0x0ade9e,0x0ae00e),'award_display_class54':window(op,0x094b3a,0x094bf0),
   'damage_routine_current_path':window(op,0x01d504,0x01d59e),
   'damage_defense_class_table':window(program,0x114000,0x1142a0),
   'damage_matrix':window(program,0x1142a0,0x115420),
   'damage_offense_class_table':window(program,0x115420,0x1154a0)},
 'authority_separation':{
  'player_action':{'dispatch':'new Button1 edge after B1+B2 guard','sufficient':'action 0x0c00','empty':'action 0x1a00','held':'does not redispatch during startup/active; a recovery edge may start another bounded volley'},
  'equipment_resource':{'meter':'+0x8c u8','capacity':64,'recharge_countdown':'+0x8d u8','depleted_latch':'+0x8b u8','temporary_award_timer':'+0xae u16','action_latch':'+0xad u8 is not ownership','visible_equipment':'animation record and assembly, never +0xad'},
  'projectile_lifecycle':{'pool':'record type 4; base 0xff8680; capacity 24; stride 0x80','class':'0x05','allocator':'0x01773e','release':'0x017754','scheduler':'0x01b846 before record types 8/12/16/20/24/28/36','volley':'12 attempts, one every 4 source ticks','resource_debit':'3 per successful attempt; clamp at zero','state_sequence':[0,2,4,6],'current_state_removal':['collision result +0x40 negative','x/camera bounds','y/camera bounds','world y below z'],'impact_actor':'type24 class0x3a'},
  'collision_damage':{'projectile_attack_table':'+0x50 = 0x03136a','collision_identity':'0x001fc1c0','current_state_writer':'current collision system writes projectile +0x40; class routine consumes it','target_removed':'prevents later current-state contact; no fixed-frame damage authority','special':'damage remains player animation attack-selector-owned; class0x20 and class0x47 are coordination/presentation actors'},
  'pickup_award':{'grant_writer':'0x01a1a4..0x01a1c0','timer_ticks':600,'display_actor':'type24 class0x54 follows player and renders remaining-timer bands','causal_rule':'removing class0x54 does not remove or freeze +0xae gameplay state'},
  'audio':{'empty_fallback':'character-indexed source call table at 0x01b814','other_events':'retained as exact QSound bus ledgers; no semantic sound name inferred','presentation_owns_gameplay':False}},
 'resource_causal_trace':{
  'sufficient':{'dispatch_frame':4492,'action':'0x0c00','spawn_count':12,'spawn_writer':'0x0257f4','resource_start':64,'resource_min':28},
  'empty':{'dispatch_frame':4492,'action':'0x1a00','auxiliary_class':'0x10','damaging_projectile_count':0,'depleted_recharge_observed':'one unit each 6-countdown cycle'},
  'normal_recharge_observed':'after the volley, one unit each 2-countdown cycle on the selected PW route',
  'hud_dependency':'0x0ade9e..0x0ae00e both draws the meter and mutates +0x8b/+0x8c/+0x8d; native translation must separate the gameplay tick from rendering without changing order'},
 'implementation_contract':implementation_contract,
 'special_causal_trace':{'guard':'at least two new/current B1/B2/B3 bits, health nonzero, normal player state and no conflicting latch','action':'0x0800','player_routine':'0x024f04','health_cost':'six via +0x9f event count and 0x01b492; values 1..5 clamp to zero','zero_health':'special rejected; Button1 independently falls through to 0x0c00','actors':['type24 class0x20','type24 class0x47'],'rng':'class0x47 consumes source RNG for visual particle motion; player damage selector does not consume it'},
  'counterfactuals':[
  {'class':'resource_sufficient_vs_insufficient','result':'0x0c00/class5 versus 0x1a00/class10'},
  {'class':'button1_edge_vs_held','result':'held input does not restart the active volley'},
  {'class':'repeat_startup_active_recovery','result':'startup/active repeats remain 12 shots; recovery edge produces a second bounded volley'},
  {'class':'b1_b2_health_sufficient_insufficient','result':'nonzero health enters 0x0800; zero rejects special and permits Button1 fallback dispatch'},
  {'class':'target_in_vs_out_of_range','result':'source aiming/projectile path changes while dispatch and debit remain identical'},
  {'class':'allocation_available_vs_unavailable','result':'unavailable record4 pool produces zero class5 actors and no resource debit'},
  {'class':'collision_enabled_vs_target_removed','result':'projectile lifecycle continues but removed target cannot receive later contacts'},
  {'class':'lifetime_writer_suppressed','result':'forcing class5 back to active state retains it for over 200 frames'},
  {'class':'recharge_writer_frozen','result':'meter remains 24 instead of source recovery'},
  {'class':'pickup_resource_actor_removed','result':'class0x54 disappears while +0xae remains 600'},
  {'class':'projectile_class_removed_from_scheduler','result':'class5 population and downstream impact actors disappear'},
   {'class':'facing_reversed_before_dispatch','result':'same volley/debit, source projectile horizontal sign reversed'},
   {'class':'damage_attacker_class_index','result':'attacker +0x5e 0 -> 2 selects offense 0 -> 4 and table-derived damage 24 -> 31'}],
  'mutation_controls':{'count':13,'all_downstream_effects_asserted':True,'no_fixed_frame_result':True,'no_visible_weapon_inference_from_0xad':True},
 'rng':{'button1_action':'none','record4_class5':'none','special_class47':'source RNG calls at init only; captured order retained'},
 'presentation_locks':{'melee_selector_timing':'unchanged','accepted_attack_assemblies':'unchanged','class_0x1f_tracking':'unchanged','neutral_transition':'accepted prior checkpoint and unchanged'},
  'provenance':{'capture_manifest_sha256':digest(RAW/'input_manifest.json'),'zero_health_supplement_manifest_sha256':digest(RAW_ZERO/'input_manifest.json'),'damage_capture_script_sha256':digest(ROOT/'tools/mame_capture_oracle11_player_weapon.lua'),'damage_cold_run_sha256':digest(RAW_DAMAGE/'cold_run_1'/'damage.tsv'),'damage_mutation_sha256':digest(RAW_DAMAGE/'damage_attack_class_2'/'damage.tsv'),'impact_audio_selector_sha256':digest(RAW_DAMAGE/'cold_run_1'/'impact_audio.tsv'),'presentation_actor_cold_run_sha256':digest(RAW_DAMAGE/'cold_run_1'/'actors.tsv'),'presentation_actor_facing_mutation_sha256':digest(RAW_DAMAGE/'facing_reversed'/'actors.tsv'),'mame':manifest['mame'],'nvram_baseline_sha256':manifest['nvram_baseline_sha256']},
 'physical_saturn':'UNRUN','saturn_emulator':'UNRUN'
}
OUT.write_text(json.dumps(report,sort_keys=True,separators=(',',':'))+'\n',encoding='ascii')
auth=json.loads(AUTH.read_text(encoding='utf-8'))
auth['weapon_projectile_resource']=report
pending=[x for x in auth.get('remaining_player_backlog',[]) if not any(k in x.lower() for k in ('button1','projectile','special action resource'))]
auth['remaining_player_backlog']=pending
auth.pop('remaining_round1_authority',None)
AUTH.write_bytes(json.dumps(auth,sort_keys=True,indent=2).encode('ascii')+b'\n')
print(f'wrote {OUT.relative_to(ROOT)} and updated {AUTH.relative_to(ROOT)}')
