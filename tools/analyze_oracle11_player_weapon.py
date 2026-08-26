#!/usr/bin/env python3
"""Build the ORACLE-11 Predator Warrior weapon/projectile/resource closure."""
from __future__ import annotations
import csv, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'.deps/mame/oracle11_player_weapon_a'
RAW_ZERO=ROOT/'.deps/mame/oracle11_player_weapon_zero_a'
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
   'spec_executable':False,
   'record_type':4,'class':'0x05','dispatch':'0x030d34','state_type':'u8',
   'state_sequence':[0,2,4,6],
   'scheduler_position':'record type 4 before record types 8/12/16/20/24/28/36',
   'rng_calls':0,
   'initialization':{
     'guard':'state 0','writes':{
       'state':2,'motion_table':'0x001fc1c0','attack_table':'0x0003136a',
       'target_pointer':'0x8000','collision_result':0,
       'visibility_latch':0,'active_collision':1},
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
   'release_state':{'guard':'state 6','routine':'0x017754','result':'zero/release record type 4 in the same dispatch'},
   'current_state_interfaces':{
     'bounds':'A5+0x278:s16 and A5+0x27c:s16 are the accepted current route/navigation bound fields',
     'collision':'current collision system owns signed s16 +0x40; projectile class only consumes it'},
   'implementation_blocker':{
     'missing_fields':['type-24 class-0x3a impact handler state/presentation/release contract','native current-state collision writer binding for class-0x05 attack table 0x03136a'],
     'unblock':'close only the class-0x3a handler and bind the accepted current collision interface before native ground impact or damage is claimed'}},
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
 'mutation_controls':['reject Button1 held redispatch','reject cadence other than ticks 0..44 step 4','reject debit without allocation','reject debit other than 3 or missing zero clamp','reject recovery before tick 49','reject movement or facing during action','reject recharge before action update','reject fixed-frame projectile hit or removal']}
report={
 'schema':1,'task':'ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE','status':'SOURCE_CLOSED',
 'scope':'one-player Predator Warrior Round 1 route-reachable Button1 volley, empty-resource fallback, B1+B2 special, projectile/effect actors, resource meter/recharge, temporary resource award, collision/damage and gameplay audio ownership',
 'determinism':{'independent_cold_runs':2,'byte_identical':True,'identical_files':['samples.tsv','writes.tsv','actors.tsv','qsound.tsv']},
 'source_identity':{
  'button_dispatch':window(op,0x01a75e,0x01a8a0),'pw_button1_action':window(op,0x02576a,0x0258a8),
  'empty_fallback':window(op,0x019f34,0x019f98),'record4_class5':window(op,0x030d34,0x030e58),
  'record4_class5_motion':window(op,0x016248,0x016284),'record4_class5_spawn_table':window(program,0x030e58,0x030e98),
  'record4_class5_presentation_tables':window(program,0x030f19,0x030f68),'record24_class10':window(op,0x079ffc,0x07a08e),
  'record24_class10_variant1_tables':window(program,0x07a08e,0x07a13c),
  'special_action':window(op,0x024f04,0x02501e),'special_health_debit':window(op,0x01b492,0x01b4bc),
  'special_class20':window(op,0x07f9a8,0x07fb42),'special_class47':window(op,0x08eb86,0x08ed32),
  'resource_hud_writer':window(op,0x0ade9e,0x0ae00e),'award_display_class54':window(op,0x094b3a,0x094bf0)},
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
  {'class':'facing_reversed_before_dispatch','result':'same volley/debit, source projectile horizontal sign reversed'}],
 'mutation_controls':{'count':12,'all_downstream_effects_asserted':True,'no_fixed_frame_result':True,'no_visible_weapon_inference_from_0xad':True},
 'rng':{'button1_action':'none','record4_class5':'none','special_class47':'source RNG calls at init only; captured order retained'},
 'presentation_locks':{'melee_selector_timing':'unchanged','accepted_attack_assemblies':'unchanged','class_0x1f_tracking':'unchanged','neutral_transition':'accepted prior checkpoint and unchanged'},
 'provenance':{'capture_manifest_sha256':digest(RAW/'input_manifest.json'),'zero_health_supplement_manifest_sha256':digest(RAW_ZERO/'input_manifest.json'),'mame':manifest['mame'],'nvram_baseline_sha256':manifest['nvram_baseline_sha256']},
 'physical_saturn':'UNRUN','saturn_emulator':'UNRUN'
}
OUT.write_text(json.dumps(report,sort_keys=True,separators=(',',':'))+'\n',encoding='ascii')
auth=json.loads(AUTH.read_text(encoding='utf-8'))
auth['weapon_projectile_resource']=report
pending=[x for x in auth.get('remaining_player_backlog',[]) if not any(k in x.lower() for k in ('button1','projectile','special action resource'))]
auth['remaining_player_backlog']=pending
auth.pop('remaining_round1_authority',None)
auth['scope']='Round 1 one-player source authority; locomotion, melee, jump, weapon/projectile/resource and special ownership are closed while HIT/KO/continue and route-wide pickup/audio/load bodies remain active backlog'
AUTH.write_bytes(json.dumps(auth,sort_keys=True,indent=2).encode('ascii')+b'\n')
print(f'wrote {OUT.relative_to(ROOT)} and updated {AUTH.relative_to(ROOT)}')
