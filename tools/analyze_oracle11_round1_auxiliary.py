#!/usr/bin/env python3
"""Close Round 1 projectile/pickup/hazard/destructible actor authority."""
from __future__ import annotations
import csv,hashlib,json
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
A=ROOT/'.deps/mame/oracle11_round1_auxiliary_a';B=ROOT/'.deps/mame/oracle11_round1_auxiliary_b'
ROUTE=ROOT/'data/oracle10_round1_route.json';SCHED=ROOT/'data/oracle11_actor_scheduler_lifecycle.json'
PLAYER=ROOT/'data/oracle11_predator_weapon_projectile_resource.json';NAV=ROOT/'data/oracle11_round1_navigation.json'
PLAYER_ROUTE=ROOT/'data/oracle11_predator_route_ownership.json'
PLAYER_AUDIO=ROOT/'data/oracle11_predator_player_audio.json'
OPCODES=ROOT/'.deps/mame/actorprobe/decrypted_opcodes_2m.bin';PROGRAM=ROOT/'.deps/mame/actorprobe/decrypted_program_2m.bin'
OUT=ROOT/'data/oracle11_round1_auxiliary_authority.json'
TYPE36_A=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs15a';TYPE36_B=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs15b'
TYPE36_CONTEXT_A=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs16a'
TYPE36_CONTEXT_B=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs16b'
SCENE_COMPONENT_A=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs17a'
SCENE_COMPONENT_B=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs17b'
SCENE_COMPONENT_DETAIL_A=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs27a'
SCENE_COMPONENT_DETAIL_B=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs27b'
SCENE_CADENCE_A=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs39a'
SCENE_CADENCE_B=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs39b'
SCENE_PHASE_A=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs45a'
SCENE_PHASE_B=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs45b'
CLASS0F_DETAIL_A=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs61a'
CLASS0F_DETAIL_B=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs61b'
CLASS0F_COUNTER_A=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs61m1'
CLASS0F_COUNTER_B=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs61m2'
CLASS0A_DETAIL_A=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs64a'
CLASS0A_DETAIL_B=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs64b'
CLASS0A_COUNTER_A=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs64m1'
CLASS0A_COUNTER_B=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs64m2'
SCENE_FULL_A=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs21a'
SCENE_FULL_B=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs21b'
TYPE16_TRACE_A=ROOT/'.deps/mame/reimplement13_type16_trace_g'
TYPE16_TRACE_B=ROOT/'.deps/mame/reimplement13_type16_trace_h'
TYPE16_ATTACK_A=ROOT/'.deps/mame/reimplement13_type16_collision_a/attack_table.bin'
TYPE16_ATTACK_B=ROOT/'.deps/mame/reimplement13_type16_collision_b/attack_table.bin'
TYPE16_HURT_A=ROOT/'.deps/mame/reimplement13_type16_hurt_a/player_hurt_window.bin'
TYPE16_HURT_B=ROOT/'.deps/mame/reimplement13_type16_hurt_b/player_hurt_window.bin'
PICKUP_CAPTURE=ROOT/'.deps/mame/reimplement13_coffee_shop_pickup_e'
SCENE_COMPONENT_SUPPRESS={
 (20,'0x01'):ROOT/'.deps/mame/oracle11_progression_lifecycle_cs17s201',
 (20,'0x02'):ROOT/'.deps/mame/oracle11_progression_lifecycle_cs17s202',
 (20,'0x0f'):ROOT/'.deps/mame/oracle11_progression_lifecycle_cs17s20f',
 (24,'0x05'):ROOT/'.deps/mame/oracle11_progression_lifecycle_cs17s245',
 (24,'0x0a'):ROOT/'.deps/mame/oracle11_progression_lifecycle_cs17s24a',
 (24,'0x20'):ROOT/'.deps/mame/oracle11_progression_lifecycle_cs17s2420',
 (28,'0x00'):ROOT/'.deps/mame/oracle11_progression_lifecycle_cs17s280',
 (28,'0x0c'):ROOT/'.deps/mame/oracle11_progression_lifecycle_cs17s28c',
 (28,'0x0e'):ROOT/'.deps/mame/oracle11_progression_lifecycle_cs17s28e'}
SCENE_COMPONENT_DISPATCH={(20,'0x01'):0x06b2fa,(20,'0x02'):0x06b534,
 (20,'0x0f'):0x06ed3e,(24,'0x05'):0x076254,(24,'0x0a'):0x077ccc,
 (24,'0x20'):0x07f9a8,(28,'0x00'):0x09e098,(28,'0x0c'):0x0a4922,
 (28,'0x0e'):0x0a726c}
SCENE_COMPONENT_LIFETIMES={(20,'0x01'):2,(20,'0x02'):2,(20,'0x0f'):1,
 (24,'0x05'):1,(24,'0x0a'):2,(24,'0x20'):1,(28,'0x00'):1,
 (28,'0x0c'):1,(28,'0x0e'):1}
TYPE36_SUPPRESS={
 '0x03':ROOT/'.deps/mame/oracle11_progression_lifecycle_cs15s3',
 '0x04':ROOT/'.deps/mame/oracle11_progression_lifecycle_cs15s4all',
 '0x05':ROOT/'.deps/mame/oracle11_progression_lifecycle_cs15s5',
 '0x0e':ROOT/'.deps/mame/oracle11_progression_lifecycle_cs15se'}
TYPE36_BODY={'0x03':(0x09a67e,0x09a7c6),'0x04':(0x09aa90,0x09ac18),'0x05':(0x09bb66,0x09bbe4),'0x0e':(0x09d440,0x09d60e)}
TYPE36_LIFETIMES={'0x03':50,'0x04':15,'0x05':4,'0x0e':16}
FILES=('aux_samples.tsv','aux_entries.tsv','aux_writes.tsv','aux_rng.tsv','aux_player_effects.tsv','samples.tsv','dispatches.tsv','projectiles.tsv','score_writes.tsv','result.tsv')
DISPATCH={(16,'0x06'):0x03537e,(20,'0x07'):0x06d1aa,(20,'0x08'):0x06d53c,(20,'0x09'):0x06d926,(20,'0x0a'):0x06de92,(24,'0x10'):0x079ffc,(24,'0x3d'):0x0887c8,(24,'0x43'):0x08ce44,(24,'0x45'):0x08dc1c,(24,'0x49'):0x08f080,(24,'0x4b'):0x08f86e,(24,'0x4e'):0x0927f6}
EXPECTED={(16,'0x06'):(505,514,4991,0,2),(20,'0x07'):(28446,26565,26619,0,0),(20,'0x08'):(275,276,811,1,0),(20,'0x09'):(6956,7194,21606,898,0),(20,'0x0a'):(603,602,1708,1,0),(24,'0x10'):(4694,4769,23665,0,0),(24,'0x3d'):(12811,11476,121404,0,0),(24,'0x43'):(828,844,16860,112,0),(24,'0x45'):(1364,1308,30536,196,0),(24,'0x49'):(4209,4808,19339,0,0),(24,'0x4b'):(810,661,4080,0,0),(24,'0x4e'):(909,848,3732,80,0)}
CLASS4E_VARIANT0_CONTRACT=None
CLASS4E_TERMINAL_TRANSITION=None

def req(x,m):
 if not x:raise ValueError(m)
def next_seed(seed):
 high=((3*seed)&0xffff)>>8;low=((seed&0xff)+high)&0xff
 return (high<<8)|low
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
 with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def canon(x):return json.dumps(x,sort_keys=True,indent=2).encode('ascii')+b'\n'
def ident(p,files=FILES):
 m=json.loads((p/'input_manifest.json').read_text(encoding='utf-8-sig'))
 for f in files:req(sha(p/f)==m['sha256'][f],f'{p.name}:{f} identity drift')
 return {'manifest_sha256':sha(p/'input_manifest.json'),'files':{f:m['sha256'][f] for f in files},'mame_sha256':m['mame_sha256'],'nvram_baseline_sha256':m['nvram_baseline_sha256']}
def window(op,pc):
 a=max(0,pc-8);b=min(len(op),pc+16);return {'first':f'0x{a:06x}','last_exclusive':f'0x{b:06x}','sha256':hashlib.sha256(op[a:b]).hexdigest()}
def source_records(ss,typ,cls,program):
 out={}
 for r in ss:
  if int(r['type'])!=typ or f"0x{r['class']}"!=cls:continue
  a=int(r['anim'],16)
  if not a:continue
  req(a+16<=len(program),f'{typ}/{cls}:record outside program')
  assembly=int(r['assembly'],16);hurt=int(r['hurt']);attack=int(r['attack'])
  req(int.from_bytes(program[a+4:a+8],'big')==assembly and program[a+8]==hurt and program[a+9]==attack,f'{typ}/{cls}:record data drift')
  out[a]={'animation_record':f'0x{a:08x}','assembly':f'0x{assembly:08x}','hurt_selector':hurt,'attack_selector':attack,'record_sha256':hashlib.sha256(program[a:a+16]).hexdigest(),'classification':'SOURCE_CLOSED'}
 return [out[k] for k in sorted(out)]

def animation_record(program,address):
 r=program[address:address+16];req(len(r)==16,f'animation record {address:08x} outside program')
 return {'timer_u16':int.from_bytes(r[0:2],'big'),'branch_s16':int.from_bytes(r[2:4],'big',signed=True),'animation_record':f'0x{address:08x}','assembly':f"0x{int.from_bytes(r[4:8],'big'):08x}",'hurt_selector_u8':r[8],'attack_selector_u8':r[9],'record_sha256':hashlib.sha256(r).hexdigest()}

def attack_box(record,address):
 req(len(record)==16,f'attack record {address:08x} size drift')
 return {'address':f'0x{address:08x}','x_center_s8':int.from_bytes(record[0:1],'big',signed=True),'y_center_s8':int.from_bytes(record[1:2],'big',signed=True),'x_half_u8':record[2],'y_half_u8':record[3],'z_center_s8':int.from_bytes(record[4:5],'big',signed=True),'z_half_u8':record[5],'impact_variant_u8':record[8],'knockback_mode_s8':int.from_bytes(record[6:7],'big',signed=True),'damage_selector_u8':record[9],'hit_value_u8':record[14],'record_sha256':hashlib.sha256(record).hexdigest()}

def hurt_box(record,address):
 req(len(record)==8,f'hurt record {address:08x} size drift')
 return {'address':f'0x{address:08x}','x_center_s8':int.from_bytes(record[0:1],'big',signed=True),'y_center_s8':int.from_bytes(record[1:2],'big',signed=True),'x_half_u8':record[2],'y_half_u8':record[3],'z_center_s8':int.from_bytes(record[4:5],'big',signed=True),'z_half_u8':record[5],'record_sha256':hashlib.sha256(record).hexdigest()}

def coffee_shop_class05_reactive_prop(op,program,aux_writes,aux_rng):
 scene_file='coffee_shop_scene_actors.tsv'
 req(sha(SCENE_FULL_A/scene_file)==sha(SCENE_FULL_B/scene_file),
     'Coffee Shop class-0x05 completion captures differ')
 scene=rows(SCENE_FULL_A/scene_file)
 actors={slot:[r for r in scene if r['slot']==slot and r['class']=='05']
         for slot in ('ffb180','ffb280')}
 req([(slot,x[0]['frame'],x[-1]['frame']) for slot,x in actors.items()]==[
      ('ffb180','2673','5550'),('ffb280','2673','3931')],
     'Coffee Shop class-0x05 lifetime drift')
 reaction=actors['ffb280']
 states=[]
 for r in reaction:
  pair=[int(r['state'],16),int(r['substate'],16)]
  if not states or states[-1]!=pair:states.append(pair)
 req(states==[[0x0200,0],[0x0400,0],[0x0402,0],[0x0404,0],
              [0x0404,0x0200],[0x0604,0x0300]],
     'Coffee Shop class-0x05 state program drift')
 records=[]
 for address in (0x6cc62,0x6cc8a,0x6cc9a,0x6ccae,0x6ccc2):
  records.append(animation_record(program,address))
 req([x['hurt_selector_u8'] for x in records]==[1,0,0,0,0] and
     [x['attack_selector_u8'] for x in records]==[1,0,0,0,0],
     'Coffee Shop class-0x05 presentation selector drift')
 stage=[]
 for address,slot,frame in ((0x15c188,'0x00ffb280',2672),
                            (0x15c1a8,'0x00ffb180',2672)):
  raw=program[address:address+16]
  req(len(raw)==16,'Coffee Shop class-0x05 stage record truncated')
  stage.append({'address':f'0x{address:08x}','observed_source_slot':slot,
   'observed_source_frame':frame,
   'camera_threshold_u16':int.from_bytes(raw[0:2],'big'),
   'x_s16':int.from_bytes(raw[2:4],'big',signed=True),
   'y_s16':int.from_bytes(raw[4:6],'big',signed=True),
   'allocator_u16':int.from_bytes(raw[6:8],'big'),
   'class_u8':raw[8],'variant_u8':raw[9],
   'guard_0a_s8':int.from_bytes(raw[10:11],'big',signed=True),
   'guard_0b_u8':raw[11],'facing_u8':raw[12],
   'field_0d_u8':raw[13],'timer_u16':int.from_bytes(raw[14:16],'big'),
   'record_sha256':hashlib.sha256(raw).hexdigest()})
 req([(x['camera_threshold_u16'],x['x_s16'],x['y_s16'],x['allocator_u16'],
       x['class_u8'],x['field_0d_u8']) for x in stage]==
     [(816,1264,293,4,5,0x30),(816,1284,268,4,5,0x22)],
     'Coffee Shop class-0x05 stage record decode drift')
 writes=[r for r in aux_writes if r['slot']=='ffb280' and
         3890<=int(r['frame'])<=3931]
 req(any(r['frame']=='3890' and r['pc']=='01d4aa' and
         r['offset']=='04' and r['data']=='00000400' for r in writes) and
     any(r['frame']=='3931' and r['pc']=='01770c' and
         r['offset']=='00' and r['data']=='00000000' for r in writes),
     'Coffee Shop class-0x05 collision/release writer drift')
 rng=[r for r in aux_rng if r['slot']=='ffb280' and r['frame']=='3891']
 req(len(rng)==1 and rng[0]['pc']=='0bc6ba' and rng[0]['seed']=='cb46' and
     next_seed(0xcb46)==0x61a7,
     'Coffee Shop class-0x05 RNG transaction drift')
 audio=json.loads((ROOT/'data/oracle11_global_audio_trigger_owners.json').
                  read_text(encoding='ascii'))
 edge=next(x for x in audio['trigger_groups']
           if x['id']=='global-audio-ffb280-003a8e-0074')
 req(edge['command']=='0x0074' and edge['occurrences']==1 and
     edge['transition_guard']['contexts'][0]['source_call']['address']==
      '0x06ca6c','Coffee Shop class-0x05 audio edge drift')
 attack=attack_box(program[0x11af76:0x11af86],0x11af76)
 hurt=hurt_box(program[0x6cd50:0x6cd58],0x6cd50)
 impact=next((r for r in scene if r['frame']=='3891' and
              r['slot']=='ffc200' and r['class']=='4e' and
              r['variant']=='01'),None)
 req(impact is not None and impact['state']=='0000' and
     int(impact['x_fp'],16)>>16==1312 and int(impact['y_fp'],16)>>16==324 and
     int(impact['z'])==292,'Coffee Shop class-0x05 impact allocation drift')
 return {
  'classification':'SOURCE_CLOSED_IMPLEMENTATION_FIELDS',
  'spec_executable':True,'retained_gameplay_authority':False,
  'dispatch':'0x06c9ee','bounded_source_body':{
   'first':'0x0006c9ee','last_exclusive':'0x0006cc56',
   'sha256':hashlib.sha256(op[0x6c9ee:0x6cc56]).hexdigest()},
  'record_type_u8':20,'class_u8':'0x05','stage_records':stage,
  'source_slots':['0x00ffb180','0x00ffb280'],
  'scheduler_order':'record-type-20 ascending source-slot order; class-0x05 reaction and RNG precede record-type-24 impact initialization',
  'initialization':{'state_u16':'0x0200','substate_u16':'0x0000',
   'table_set':'0x0006cd44','object_or_u16':'0x8000','field64_u8':0x19,
   'ground_copy':'y_s16 -> z_s16','facing_u8':0,
   'animation_record':records[0]},
  'current_state_collision':{
   'guard':'player selector 11 is contact-ready; target state is 0x0200; target player guard is zero; current attack and hurt boxes overlap',
   'source_update_frame_u16':3890,'attacker_source_slot':'0x00ff8380',
   'attack_record':attack,'hurt_selector_u8':1,'hurt_record':hurt,
   'damage_s16':25,'health_before_s16':0,'health_after_clamp_s16':-1,
   'reaction_state_u16':'0x0400','reaction_substate_u16':'0x0000',
   'reaction_direction_rule':'write player_x < target_x to target+0x4f; state-4 entry XORs that value with 1 for visible facing',
   'impact_allocation':{'record_type_u8':24,'class_u8':'0x4e',
    'variant_u8':1,'source_slot':'0x00ffc200','visible_frame_u16':3891,
    'x_s16':1312,'y_s16':324,'z_s16':292}},
  'reaction_program':{
   'state_sequence_u16':states,
   'state_0x0400':{'next_state_u16':'0x0402','timer_u16':8,
    'facing_rule':'source_facing_selector_u8 XOR 1','rng_calls_u8':1,
    'seed_before':'0xcb46','seed_after':'0x61a7',
    'audio_command_u16':'0x0074','animation_record':records[1]},
   'state_0x0402':{'timer_rule':'decrement timer through zero; only the signed animation terminal advances to state 0x0404',
    'terminal_animation_record':records[2]},
   'state_0x0404':{
    'primary':{'animation_record':records[3],'x_velocity_s32':-0x00050000,
     'y_velocity_s32':0x00060000,'x_acceleration_s32':0,
     'y_acceleration_s32':-0x00008000,'initial_y_offset_s16':27},
    'alternate':{'animation_record':records[4],'x_velocity_s32':-0x00040000,
     'y_velocity_s32':0x00050000,'x_acceleration_s32':0,
     'y_acceleration_s32':-0x00008000,'initial_y_offset_s16':0,
     'landing_substate_u16':'0x0200'},
    'projection_rule':'(source global phase byte + scheduler d7) & 1 selects primary on zero and alternate on one; the accepted Coffee Shop adapter maps odd native runtime frames to the zero/primary source phase',
    'landing_rule':'unsigned trajectory high word below ground z sets its landing bit; both bits advance to state 0x0604/substate 0x0300',
    'release_guard':'state 0x0604/substate 0x0300 releases the fixed-pool record on its next scheduler update'}},
  'presentation_records':records,
  'capture_identity':{'completion_a_sha256':sha(SCENE_FULL_A/scene_file),
   'completion_b_sha256':sha(SCENE_FULL_B/scene_file),
   'byte_identical':True},
  'mutation_controls':['reject fixed-frame spawn','reject reversed stage-record order',
   'reject wrong current attack record','reject wrong hurt selector',
   'reject missing damage clamp','reject wrong reaction facing XOR',
   'reject missing class-0x05 RNG call','reject guessed audio identity',
   'reject early timer transition','reject authored debris delay',
   'reject wrong trajectory sign','reject wrong phase projection',
   'reject early release','reject missing class-0x4e variant-1 impact'],
  'fixed_frame_substitute_forbidden':True}

def coffee_shop_class08_health_pickup(op,program,aux_writes,aux_rng):
 manifest=json.loads((PICKUP_CAPTURE/'input_manifest.json').read_text(
     encoding='utf-8-sig'))
 req(manifest['authority']==
     'coffee-shop-record28-class0a-health-pickup-corrective-oracle' and
     manifest['frame_window']==[2600,3120] and
     manifest['mame']['sha256']==
     'af6966108d9b52c22465c6d50f4e5d50cc371b50f2d27dc443935f287aad37a3',
     'Coffee Shop health-pickup capture manifest drift')
 variants={row['name']:row for row in manifest['variants']}
 req(set(variants)=={'baseline_1','baseline_2','pickup_suppressed'} and
     variants['baseline_1']['sha256']==variants['baseline_2']['sha256'],
     'Coffee Shop health-pickup baseline identity drift')
 for name,row in variants.items():
  for filename,digest in row['sha256'].items():
   req(sha(PICKUP_CAPTURE/name/filename)==digest,
       f'Coffee Shop health-pickup {name}/{filename} identity drift')
 baseline=rows(PICKUP_CAPTURE/'baseline_1'/'samples.tsv')
 suppressed=rows(PICKUP_CAPTURE/'pickup_suppressed'/'samples.tsv')
 pickup_writes=rows(PICKUP_CAPTURE/'baseline_1'/'record28_writes.tsv')
 spawn_guard=rows(PICKUP_CAPTURE/'baseline_1'/'source_spawn_guard.tsv')
 req(spawn_guard==rows(PICKUP_CAPTURE/'baseline_2'/'source_spawn_guard.tsv') and
     len(spawn_guard)==1 and spawn_guard[0]=={
      'frame':'2672','variant':'baseline','pc':'01bf1e','a1':'15c198',
      'a4':'ffb200','a5':'ff8000','a6':'ff1812','record_gate':'0330',
      'record_x':'0500','record_y':'013d','record_type':'0004',
      'record_arg':'0800','record_lane_guard':'00',
      'record_character_guard':'00','global_gate':'0331',
      'global_lane_limit':'09','global_character':'01','camera_x':'0331',
      'player_x':'0427'}, 'Coffee Shop class-0x08 source spawn guard drift')
 scene_actors=rows(SCENE_COMPONENT_DETAIL_A/'coffee_shop_scene_actors.tsv')
 scene_health=rows(SCENE_COMPONENT_DETAIL_A/
                   'coffee_shop_scene_health_writes.tsv')
 parent_rows=[r for r in scene_actors if r['slot']=='ffb200' and
              r['class']=='08']
 pickup_rows=[r for r in scene_actors if r['slot']=='ffcd00' and
              r['class']=='0a' and r['variant']=='12']
 req(parent_rows[0]['frame']=='2673' and parent_rows[-1]['frame']=='2947' and
     pickup_rows[0]['frame']=='2907' and pickup_rows[-1]['frame']=='3102',
     'Coffee Shop class-0x08/pickup lifetime drift')
 damage=[r for r in scene_health if int(r['frame'])==2905 and
         r['target_slot']=='ffb200']
 req([(r['pc'],r['attacker'],r['attack_record'],r['health_before'],
       r['health_after']) for r in damage]==[
      ('01d590','ff8880','02fc58','0000','ffe7'),
      ('01d598','ff8880','02fc58','ffe7','ffff')],
     'Coffee Shop class-0x08 current-state collision drift')
 parent_rng=[r for r in aux_rng if r['slot']=='ffb200' and
             int(r['frame'])==2906]
 req(len(parent_rng)==1 and parent_rng[0]['pc']=='0bc6ba' and
     parent_rng[0]['seed']=='8be5' and next_seed(0x8be5)==0xa388,
     'Coffee Shop class-0x08 drop RNG drift')
 parent_dispatch=[r for r in rows(A/'dispatches.tsv') if r['a6']=='ffb200' and
                  int(r['frame'])==2906]
 req(len(parent_dispatch)==1 and parent_dispatch[0]['return1']=='06d5c0' and
     parent_dispatch[0]['shared_dispatch']=='001922' and
     parent_dispatch[0]['command']=='0077',
     'Coffee Shop class-0x08 audio ownership drift')
 init=[r for r in pickup_writes if int(r['frame'])==2906]
 req([(r['pc'],r['offset'],r['data']) for r in init[:26]]==[
  ('0bc712','00','0101'),('0bc714','02','1212'),
  ('0bc71a','02','0a0a'),('0bc720','5c','0101'),
  ('0bc730','30','fffc'),('0bc730','32','8000'),
  ('0bc734','38','0000'),('0bc734','3a','0000'),
  ('0bc738','34','0005'),('0bc738','36','0000'),
  ('0bc73c','3c','ffff'),('0bc73c','3e','8000'),
  ('0bc742','10','0500'),('0bc748','14','013d'),
  ('0bc74e','18','013d'),('0a38fe','04','0202'),
  ('0a3902','2e','8000'),('0a3908','08','0000'),
  ('0a390e','50','000a'),('0a390e','52','40a2'),
  ('0a3914','18','013d'),('0a391a','64','2929'),
  ('01652a','1c','000a'),('01652a','1e','3d1c'),
  ('01652e','0a','0008'),('016534','24','8000')],
  'Coffee Shop class-0x08 drop allocation/init writes drift')
 transition_writes=[(int(r['frame']),r['pc'],r['offset'],r['data'])
  for r in pickup_writes if r['pc'] in
  {'0a3988','0a39c2','0a39c6','0a39ce','0a39d6','0a3a12','0a3a18','0a3a1e',
   '0a3a36','017844'}]
 req(transition_writes==[
  (2907,'0a3988','06','0202'),
  (2929,'0a39c2','06','0404'),(2929,'0a39c6','14','013d'),
  (2929,'0a39ce','34','0001'),(2929,'0a39ce','36','0000'),
  (2929,'0a39d6','3c','ffff'),(2929,'0a39d6','3e','c000'),
  (2939,'0a3a12','06','0200'),(2939,'0a3a18','14','013d'),
  (2939,'0a3a1e','5c','0000'),(3101,'0a3a36','04','0606'),
  (3102,'017844','00','0000'),(3102,'017844','02','0000')],
  'Coffee Shop class-0x0a transition/release writer drift')
 base_3102=next(r for r in baseline if r['frame']=='3102')
 suppress_3102=next(r for r in suppressed if r['frame']=='3102')
 req((base_3102['player_action'],base_3102['player_health'],
      base_3102['pickup_state'])==('0e00','95','0600') and
     (suppress_3102['player_action'],suppress_3102['player_health'],
      suppress_3102['pickup_active'])==('1400','85','0'),
     'Coffee Shop health-pickup suppression control drift')
 route=json.loads(PLAYER_ROUTE.read_text(encoding='ascii'))
 audio=json.loads(PLAYER_AUDIO.read_text(encoding='ascii'))
 route_pickup=route['health_pickup']
 audio_edge=next(x for x in audio['trigger_edges']
                 if x['id']=='player-audio-01a18c-0206')
 req(route_pickup['status'] if 'status' in route_pickup else True,
     'unreachable route-pickup status drift')
 req(route_pickup['remaining_unknowns']==[] and
     audio_edge['command_identity']=='0x0206' and
     audio_edge['transition_guard']['contexts']==[{
      'count':1,'first_frame':3101,'input_words':[40],'last_frame':3101,
      'player_action_u16':3584,'player_state_u16':512,
      'player_substate_u8':0}], 'Coffee Shop player pickup owner drift')
 attack=attack_box(program[0x2fc58:0x2fc68],0x2fc58)
 parent_hurt=hurt_box(program[0x6d90c:0x6d914],0x6d90c)
 player_hurt=hurt_box(program[0x11ae8e:0x11ae96],0x11ae8e)
 pickup_hurt=hurt_box(program[0xa40b6:0xa40be],0xa40b6)
 navigation=json.loads(NAV.read_text(encoding='ascii'))
 navigation_parent=next(x for x in navigation['navigation_bodies']['instances']
  if x['slot']=='0xffb200')
 expected_parent_transitions=[
  {'count':1,'first_frame':2906,'from':[0x0200,0],'to':[0x0400,0]},
  {'count':1,'first_frame':2907,'from':[0x0400,0],'to':[0x0402,0]},
  {'count':1,'first_frame':2917,'from':[0x0402,0],'to':[0x0404,0]},
  {'count':1,'first_frame':2939,'from':[0x0404,0],'to':[0x0404,0x0200]},
  {'count':1,'first_frame':2947,'from':[0x0404,0x0200],
   'to':[0x0604,0x0300]}]
 req(navigation_parent['state_transitions']==expected_parent_transitions and
     navigation_parent['bounded_source_block']=='0x06d53c..0x06d7b8' and
     navigation_parent['source_block_sha256']==
      '7b72396aa82ef452ba51b8b933c3258ee662c908190cab232ec6c2c05025cc5b',
     'Coffee Shop class-0x08 post-drop navigation evidence drift')
 return {
  'classification':'SOURCE_CLOSED_IMPLEMENTATION_FIELDS',
  'spec_executable':True,'retained_gameplay_authority':False,
  'stage_spawn':{
   'owner':'route stage-record interpreter 0x01bece..0x01bf4e',
   'caller_chain':['0x0084bc','0x0080a2'],
   'stage_record_address':'0x0015c198','source_slot':'0x00ffb200',
   'guard':'record_gate_u16 <= global camera/right-edge gate_u16; lane and character guards are zero',
   'record':{'gate_u16':816,'x_s16':1280,'y_s16':317,
    'allocator_selector_u16':4,'class_variant_word_u16':'0x0800',
    'lane_guard_s8':0,'character_guard_u8':0},
   'accepted_witness':{'source_update_frame_u16':2672,
    'visible_frame_u16':2673,'global_gate_u16':817,'player_x_u16':1063},
   'writes':['active_u8 += 1','class/variant word = 0x0800',
    'x_s16 = 1280','y_s16 = 317','facing_u8 = 0','source flags = 0x1b',
    'timer_u8 = 0'],'fixed_frame_substitute_forbidden':True},
  'parent':{'record_type_u8':20,'class_u8':'0x08','variant_u8':0,
   'dispatch':'0x06d53c','source_slot':'0x00ffb200',
   'state_sequence_u16':[0,0x0200,0x0400,0x0402,0x0404,0x0604],
   'initialization':{'table_set':'0x0006d900','object_or_u16':'0x8000',
    'field64_u8':0x1c,'ground_copy':'y_s16 -> z_s16',
    'animation_record':animation_record(program,0x6d7b8)},
   'current_state_collision':{'attacker_source_slot':'0x00ff8880',
    'attacker_record_type_u8':4,'source_update_frame_u16':2905,
    'attack_record':attack,'hurt_selector_u8':1,'hurt_record':parent_hurt,
    'damage_s16':25,'health_before_s16':0,'health_after_damage_s16':-25,
    'health_after_clamp_s16':-1,'damage_writer':'0x01d590',
    'clamp_writer':'0x01d598','reaction_writer':'0x01d4aa',
    'reaction_direction':{
     'source_body':{'first':'0x0001d0c8','last_exclusive':'0x0001d0fa',
      'sha256':hashlib.sha256(op[0x1d0c8:0x1d0fa]).hexdigest()},
     'field':'defender+0x4f:u8; distinct from visible facing at defender+0x0f',
     'attack_mode_s8':0,
     'rule':'zero attack mode preserves the initial 0x01d0c8 copy of attacker+0x0f:u8 into defender+0x4f:u8',
     'attacker_facing_u8':1,'result_u8':1,
     'consumer':'0x01d622 copies defender+0x4f:u8 to the allocated class-0x4e impact facing field',
     'visible_witness':{'impact_source_slot':'0x00ffb680',
      'impact_visible_frame_u16':2906,'impact_facing_u8':1}}},
   'drop':{'guard':'state 0x0400/substate 0 after current-state collision',
    'rng_entry':'0x017c5e','rng_calls_u8':1,'seed_before':'0x8be5',
    'seed_after':'0xa388','selector_mask_u8':'0x1f',
    'selector_source':{'actor_offset_u8':'0x0c','value_u8':'0x1b',
     'lookup_base':'0x000bceaa','row_address':'0x000bd20a',
     'row_u8':[0x12]*32},
    'selected_subtype_u8':'0x12','allocation_routine':'0x017828',
    'audio':{'player_side_caller':'0x06d5ba','wrapper_return':'0x06d5c0',
     'command_u16':'0x0077','shared_dispatch_entry':'0x001922'},
    'reaction_timer_u8':8,'animation_record':animation_record(program,0x6d7f0)},
   'post_drop_program':{
    'source_block':'0x06d53c..0x06d7b8',
    'source_block_sha256':navigation_parent['source_block_sha256'],
    'state_transitions':expected_parent_transitions,
    'collision_write_visibility_guard':
     'record-20 drop handler consumes state 0x0400 on the following source update; the collision-written 0x0400 state remains visible for one sample',
    'reaction_hold':{'state_u16':0x0402,'timer_u8':8,
     'decrement_guard':'decrement timer once per source update while nonzero',
     'terminal_prelude':animation_record(program,0x6d800)},
    'debris':{
     'state_u16':0x0404,'ground_s16':317,
     'internal_coordinate_format':
      'two signed 24.8 trajectories at actor+0x60/+0x68 and actor+0x64/+0x6c; signed 8.8 velocities are extended and shifted left 8 before each long add',
     'integration_order':['x_fp += x_velocity','y_fp += y_velocity',
                          'y_velocity += y_acceleration'],
     'visible_position_projection':
      '0x06d72e copies only the selected internal x/y high words to actor+0x10/+0x14 and preserves the actor visible low u16 words',
     'projection_source_block':'0x06d610..0x06d7a6',
     'presentation_selector':'visible source-frame parity: odd selects primary, even selects alternate',
     'primary':{'animation_record':animation_record(program,0x6d83c),
      'initial_x_fp_s32':0x05000000,'initial_y_fp_s32':0x01620000,
      'x_velocity_s32':0x00050000,'y_velocity_s32':0x00060000,
      'y_acceleration_s32':-0x00008000,
      'landing_guard':'unsigned y_high < ground_s16',
      'landing_state_u16':0x0604,'landing_substate_u16':0x0300},
     'alternate':{'animation_record':animation_record(program,0x6d850),
      'initial_x_fp_s32':0x05000000,'initial_y_fp_s32':0x013d0000,
      'x_velocity_s32':0x00040000,'y_velocity_s32':0x00050000,
      'y_acceleration_s32':-0x00008000,
      'landing_guard':'unsigned y_high < ground_s16',
      'landing_substate_u16':0x0200,
      'freeze_result':{'x_fp_s32':0x05580000,
                       'y_fp_s32':0x01370000}},
     'release_guard':'state 0x0604/substate 0x0300 on the following record-20 update'},
    'fixed_frame_substitute_forbidden':True},
   'lifetime':{'first_visible_frame_u16':2673,
    'last_visible_frame_u16':2947}},
  'pickup':{'record_type_u8':28,'class_u8':'0x0a','subtype_u8':'0x12',
   'dispatch':'0x0a38e4','source_slot':'0x00ffcd00',
   'scheduler_order':'record-type-20 parent drop allocation precedes record-type-28 dispatch in the same source update',
   'initialization':{'state_substate_u16':[0x0200,0],
    'motion_substate_u16':0x0002,
    'motion_substate_guard':
     'the first post-allocation record-28 update writes substate 0x0002 and returns before movement',
    'field2e_u16':'0x8000','table_set':'0x000a40a2',
    'field64_u8':0x29,'field5c_u8':1,
    'animation_record':animation_record(program,0xa3d1c),
    'position_s16':[1280,317,317],
    'velocity_acceleration_16_16':{'x':-0x00038000,'y':0x00050000,
     'z':0,'y_acceleration':-0x00008000}},
   'movement':{'integration_order':['x += vx','z_fp += vz','y += vy',
     'vy += ay'],
    'animation_timer_rule':
     'decrement once on every active source update, including the substate-0 to substate-2 update; when zero and branch is negative reload the same record timer 8',
    'first_landing_guard':'unsigned y_high < ground_z',
    'first_landing_result':{'substate_u16':0x0004,'y_s16':317,
     'position_write':'replace only y_fp high word with ground_z and preserve the current fractional low word',
     'y_velocity_16_16':0x00010000,
     'y_acceleration_16_16':-0x00004000},
    'second_landing_guard':'unsigned y_high < ground_z',
    'second_landing_result':{'substate_u16':0x0200,'y_s16':317,
     'position_write':'replace only y_fp high word with ground_z and preserve the current fractional low word',
     'field5c_u8':0}},
   'player_interaction':{'target_scan':'0x01ce98..0x01cece',
    'target_writer':'0x01cec2','player_table_set':'0x0011ae02',
    'input_sample_rule':
     'the eligible current-frame target/input guard latches pickup ownership and suppresses the normal attack path; the interaction writer consumes that latch on the following player update',
    'player_hurt_selector_u8':17,'player_hurt_record':player_hurt,
    'pickup_hurt_selector_u8':2,'pickup_hurt_record':pickup_hurt,
    'interaction_writer':'0x019fec','action_u16':'0x0e00',
    'health_writer':'0x0bc5fc..0x0bc64a','health_before_s16':85,
    'subtype_amount_s16':10,'health_after_s16':95,'health_cap_s16':101,
    'audio_edge':{'caller':'0x01a18a','command_u16':'0x0206',
     'shared_dispatch_entry':'0x001922'},
    'presentation_records':[animation_record(program,0x15fa04),
                            animation_record(program,0x15fa14)],
    'completion_guard':'advance source animation; terminal negative branch returns to neutral, never a fixed-frame timer'},
   'collection':{'state_writer':'0x0bc5fc then 0x0a3a30',
    'collected_state_u16':0x0600,'release_routine':'0x01783e..0x017866',
    'first_absent_frame_u16':3103},
   'lifetime':{'first_visible_frame_u16':2907,
    'last_visible_frame_u16':3102}},
  'capture_identity':{'manifest_sha256':sha(PICKUP_CAPTURE/
      'input_manifest.json'),'baseline_files':variants['baseline_1']['sha256'],
    'baseline_byte_identical':True,
    'suppression_files':variants['pickup_suppressed']['sha256']},
  'mutation_controls':['stage gate','stage record x/y','allocator selector',
   'parent current attack record','parent hurt selector','signed damage clamp',
  'drop RNG seed/order','drop subtype','record20-before-record28 scheduler order',
   'visible actor high-word projection','pickup motion-substate guard',
   'pickup animation timer loop',
   'pickup initial velocity','pickup acceleration','first landing guard',
   'landing fractional-low-word retention','second landing guard',
   'prior sampled input ownership',
   'player/pickup hurt boxes','health amount','health cap',
   'audio command','animation-terminal completion','pickup release'],
  'fixed_frame_substitute_forbidden':True}

def coffee_shop_class1f_type16_projectile(op,program,aux_writes):
 trace_files=('coffee_shop_type16_class06_collision.tsv',
              'coffee_shop_scene_health_writes.tsv')
 identity_a={name:sha(TYPE16_TRACE_A/name) for name in trace_files}
 identity_b={name:sha(TYPE16_TRACE_B/name) for name in trace_files}
 req(identity_a==identity_b,'type-16/class-0x06 collision captures differ')
 req(sha(TYPE16_ATTACK_A)==sha(TYPE16_ATTACK_B),
     'type-16 attack-table source dumps differ')
 req(sha(TYPE16_HURT_A)==sha(TYPE16_HURT_B),
     'type-16 player-hurt source dumps differ')
 actors=rows(SCENE_COMPONENT_A/'coffee_shop_scene_actors.tsv')
 samples=[row for row in actors if row['pool']=='record16' and
          row['class']=='06']
 lifetimes=[];active={}
 for row in samples:
  frame=int(row['frame']);slot=row['slot'];prior=active.get(slot)
  if prior is None or frame!=prior['last_frame']+1:
   prior={'source_slot':f"0x00ff{slot[2:]}",'variant_u8':int(row['variant'],16),
          'first_frame':frame,'last_frame':frame}
   lifetimes.append(prior);active[slot]=prior
  else:prior['last_frame']=frame
 req(len(lifetimes)==9 and len(samples)==505,
     'type-16/class-0x06 Coffee Shop lifetimes drift')
 records=[animation_record(program,address) for address in
          sorted({int(row['animation_record'],16) for row in samples})]
 req(len(records)==11 and records[0]['animation_record']=='0x000355dc' and
     records[-1]['animation_record']=='0x00035680',
     'type-16/class-0x06 presentation sequence drift')
 initial_frames={item['first_frame']-1 for item in lifetimes}
 init=[row for row in aux_writes if row['class']=='06' and
       int(row['type'])==16 and int(row['frame']) in initial_frames and
       row['pc'] in {'035410','035414','035418','03541c','035420'}]
 motion=[]
 for frame in sorted(initial_frames):
  current=[row for row in init if int(row['frame'])==frame]
  values={(row['pc'],row['offset']):int(row['data'],16)&0xffff
          for row in current}
  motion.append({'spawn_frame':frame+1,
   'x_velocity_16_16':(values[('035410','30')]<<16)|values[('035410','32')],
   'x_acceleration_16_16':(values[('035414','38')]<<16)|values[('035414','3a')],
   'y_velocity_16_16':(values[('035418','34')]<<16)|values[('035418','36')],
   'y_acceleration_16_16':(values[('03541c','3c')]<<16)|values[('03541c','3e')],
   'z_velocity_16_16':(values[('035420','54')]<<16)|values[('035420','56')]})
 unique_motion=[]
 for item in motion:
  body={key:value for key,value in item.items() if key!='spawn_frame'}
  if body not in unique_motion:unique_motion.append(body)
 req(unique_motion==[
  {'x_velocity_16_16':0x00080000,'x_acceleration_16_16':0xffffe000,
   'y_velocity_16_16':0x00040000,'y_acceleration_16_16':0xffffc000,
   'z_velocity_16_16':0},
  {'x_velocity_16_16':0x00074000,'x_acceleration_16_16':0xffffdc00,
   'y_velocity_16_16':0x0003c000,'y_acceleration_16_16':0xffffb000,
   'z_velocity_16_16':0},
  {'x_velocity_16_16':0x00068000,'x_acceleration_16_16':0xffffd800,
   'y_velocity_16_16':0x00038000,'y_acceleration_16_16':0xffff9000,
   'z_velocity_16_16':0}],
  'type-16/class-0x06 motion table drift')
 trace=rows(TYPE16_TRACE_A/'coffee_shop_type16_class06_collision.tsv')
 contacts=[]
 for frame in (3263,3855):
  row=next((item for item in trace if int(item['frame'])==frame and
            item['pc']=='01d5ee'),None)
  req(row is not None and row['a1']=='ff8380' and row['a3']=='03589e' and
      row['attacker_table']=='00035882' and
      row['defender_table']=='0011ae02' and row['a2']=='11ae8e',
      f'type-16 collision register provenance drift at {frame}')
  contacts.append({'source_frame':frame,
   'attacker_source_slot':f"0x00{row['a6']}",
   'attacker_animation_record':f"0x{row['attacker_animation_record']}",
   'attacker_state_u16':int(row['attacker_state'],16),
   'defender_source_slot':'0x00ff8380',
   'defender_animation_record':f"0x{row['defender_animation_record']}",
   'defender_state_u16':int(row['defender_state'],16),
   'defender_substate_u16':int(row['defender_substate'],16),
   'attack_record':'0x0003589e','hurt_record':'0x0011ae8e'})
 defender_records=[animation_record(program,
                   int(item['defender_animation_record'],16))
                   for item in contacts]
 req({item['hurt_selector_u8'] for item in defender_records}=={17},
     'type-16 collision current player hurt-selector drift')
 attack_dump=TYPE16_ATTACK_A.read_bytes();hurt_dump=TYPE16_HURT_A.read_bytes()
 attack=attack_box(attack_dump[0x1c:0x2c],0x03589e)
 hurt=hurt_box(hurt_dump[0x0e:0x16],0x11ae8e)
 health=rows(TYPE16_TRACE_A/'coffee_shop_scene_health_writes.tsv')
 damage=[row for row in health if row['pc']=='01d5ee' and
         row['attack_record']=='03589e']
 req([(int(row['frame']),int(row['health_before'],16),
       int(row['health_after'],16)) for row in damage]==
     [(3263,95,78),(3855,68,51)],
     'type-16/class-0x06 player damage drift')
 parent_records=[animation_record(program,address) for address in
                 range(0x12e550,0x12e600,16)]
 req([item['branch_s16'] for item in parent_records]==
     [0,0,0,1,0,2,0,3,0,0,-32768],
     'class-0x1f type-16 emitter event sequence drift')
 return {'classification':'SOURCE_CLOSED_IMPLEMENTATION_FIELDS',
  'spec_executable':True,'record_type_u8':16,'class_u8':'0x06',
  'dispatch':'0x03537e','state_sequence_u16':[0,0x0200,0x0400,0x0600],
  'pool':{'base':'0xffa480','capacity_u8':20,'stride_u16':0x80,
          'scheduler':'record-type-16 ascending source-slot order'},
  'spawn_owner':{'record_type_u8':12,'class_u8':'0x1f',
   'outer_state_u16':'0x0208','action_substate_u16':'0x0e02',
   'animation_event_guard':'parent animation branch 1, 2 or 3 while parent+0x25_u8 is nonzero',
   'variant_rule':'parent animation branch_u8 - 1','allocator':'0x01778c',
   'routine':'0x0413d2','camera_guard':'parent_x-camera_x+0x58 <= 0x0232 unsigned',
   'position_offset_s16':[-59,64,0],
   'position_rule':'x=parent_x+facing-adjusted -59; y=parent_y+64; z=parent_z',
   'facing_rule':'copy parent facing','field_0x5e_u8':0x28,
   'parent_animation_records':parent_records},
  'initialization':{'state_write_u16':'0x0200','object_or_u16':'0x8000',
   'collision_table':'0x00035882','coordinate_mode_u8':1,
   'field_0x65_u8':0xff,'health_s16':0,'variant_motion_16_16':unique_motion,
   'facing_arithmetic':'negate x velocity, x acceleration, y velocity, y acceleration and z velocity when facing_u8 != 0; then xor facing with table d5_u8',
   'rng_calls_u8':0,'initial_animation_record':'0x000355dc'},
  'active_state':{'state_u16':'0x0200',
   'screen_release_guard':'release when unsigned(x-camera_x+32)>0x01c0 or unsigned(y-camera_z+16)>0x0120',
   'movement_order':['x_fp += x_velocity','x_velocity += x_acceleration','y_fp += y_velocity','y_velocity += y_acceleration','z_fp += z_velocity'],
   'ground_guard':'compare z_s16 with y_s16 after movement',
   'ground_transition':'when z>=y: bind selector 1, set state 0x0400, timer_u16=2, coordinate_mode_u8=0 and y=z',
   'collision_transition':'source terrain/collision result selects attack-table selector 3, state 0x0400 and timer_u16=0x001c',
   'animation_records':records[:4]},
  'terminal_state':{'state_u16':'0x0400','guard':'signed animation branch negative decrements timer_u16; zero advances to 0x0600','animation_records':records[4:]},
  'release_state':{'state_u16':'0x0600','release_routine':'0x0177a2'},
  'current_state_collision':{'scheduler':'record-type-16 attackers against player after actor movement/presentation selection','writer':'0x01d5ee','attack_table':'0x00035882','attack_selector_u8':1,'attack_record':attack,'player_table':'0x0011ae02','player_hurt_selector_u8':17,'player_hurt_record':hurt,'contact_guard':'current animation attack selector 1 resolves table record 0x03589e; current player animation hurt selector 17 resolves table record 0x11ae8e; those current records overlap in x/y/z under shared 0x01d4aa collision arithmetic','damage_selector_u8':10,'route_character_damage_s16':17,'hit_value_u8':20,'contacts':contacts,'health_writes':[{'source_frame':int(row['frame']),'health_before_s16':int(row['health_before'],16),'health_after_s16':int(row['health_after'],16)} for row in damage]},
  'scene_lifetimes':lifetimes,'rng_calls':0,
  'capture_identity':{'collision_completion_a':identity_a,
   'collision_completion_b':identity_b,'byte_identical':True,
   'attack_table_sha256':sha(TYPE16_ATTACK_A),
   'player_hurt_window_sha256':sha(TYPE16_HURT_A)},
  'mutation_controls':['wrong parent state','wrong animation event branch',
   'fixed-frame spawn','wrong variant','wrong motion row','wrong facing sign',
   'wrong movement order','wrong state guard','wrong animation record',
   'wrong attack selector','wrong attack box','wrong current player hurt selector',
   'wrong player hurt box',
   'damage without overlap','wrong damage selector','wrong scheduler position',
   'fixed-frame release'],
  'suppression_control':suppression(16,'0x06'),
  'fixed_frame_substitute_forbidden':True,
  'retained_gameplay_authority':False}

def coffee_shop_type36_presentation(op,program):
 files=('coffee_shop_type36_writes.tsv','coffee_shop_scene_actors.tsv',
        'coffee_shop_scene_frames.tsv','coffee_shop_scene_health_writes.tsv',
        'dispatches.tsv','progression_result.tsv')
 identity_a={name:sha(TYPE36_A/name) for name in files}
 identity_b={name:sha(TYPE36_B/name) for name in files}
 req(identity_a==identity_b,'Coffee Shop type-36 baseline captures differ')
 context_files=('coffee_shop_type36_writes.tsv','coffee_shop_scene_actors.tsv')
 context_identity_a={name:sha(TYPE36_CONTEXT_A/name) for name in context_files}
 context_identity_b={name:sha(TYPE36_CONTEXT_B/name) for name in context_files}
 req(context_identity_a==context_identity_b,
     'Coffee Shop type-36 spawn-context captures differ')
 actors=rows(TYPE36_A/'coffee_shop_scene_actors.tsv')
 writes=rows(TYPE36_A/'coffee_shop_type36_writes.tsv')
 context_writes=rows(TYPE36_CONTEXT_A/'coffee_shop_type36_writes.tsv')
 dispatches=rows(TYPE36_A/'dispatches.tsv')
 health=rows(TYPE36_A/'coffee_shop_scene_health_writes.tsv')
 baseline_last=rows(TYPE36_A/'coffee_shop_scene_frames.tsv')[-1]
 classes=[]
 spawn_pcs={'0x03':['0x09a66e'],'0x04':['0x02417a','0x023946'],
            '0x05':['0x06deea'],'0x0e':['0x09d3e4']}
 parent_fields={'0x03':'actor+0x26:u16','0x04':'actor+0x28:u16',
                '0x05':'actor+0x26:u16','0x0e':'actor+0x26:u16'}
 parent_writers={'0x03':'09a67c','0x04':'024182',
                 '0x05':'06def6','0x0e':'09d3ec'}
 state_rules={
  '0x03':['state 0 initializes four phase positions from parent+0x10, parent+0x14 and parent+0x18, binds variant animation and parent backlink','state 0x0200 cycles four signed 16.16 movement accumulators and advances source animation','negative animation branch advances to state 0x0400','state 0x0400 clears the matching parent backlink and releases through 0x01788c'],
  '0x04':['state 0 copies the parent position, applies the variant-0 source offset and binds animation','state 0x0200 applies global offset only when s16(0xff81e8)==10 and advances source animation','negative animation branch advances to state 0x0400','state 0x0400 clears parent+0x7c when it owns this slot and releases through 0x01788c'],
  '0x05':['state 0 copies the type-20 parent position, sets object priority 0x8000 and binds one of four variant animations','state 0x0200 waits while parent state_u8 is below 4 and advances source animation','parent state_u8 at least 4 advances to state 0x0400 and binds selector 4','negative animation branch advances to state 0x0600','state 0x0600 clears this slot from the parent backlink array and releases through 0x01788c'],
  '0x0e':['state 0 sets object priority 0x8000, coordinate/presentation fields, parent backlink and source attachment selector','state 0x0200 follows the parent position and facing-selected attachment offset','parent state_u8 equal to 6 writes state 0x0600','state 0x0600 clears parent+0x7c when it owns this slot and releases through 0x01788c']}
 for cls in TYPE36_BODY:
  sample=[r for r in actors if r['pool']=='record36' and
          f"0x{r['class']}"==cls]
  lifetimes=[];active={}
  for row in sample:
   slot=row['slot'];frame=int(row['frame']);prior=active.get(slot)
   if prior is None or frame!=prior['last_frame']+1:
    prior={'slot':f"0x00ff{slot[2:]}",'first_frame':frame,
           'last_frame':frame};lifetimes.append(prior);active[slot]=prior
   prior['last_frame']=frame
  req(len(lifetimes)==TYPE36_LIFETIMES[cls],f'type-36 {cls} lifetime drift')
  record_addresses=sorted({int(r['animation_record'],16) for r in sample})
  records=[animation_record(program,address) for address in record_addresses]
  parent_rows=[r for r in writes if r['pc']==parent_writers[cls]]
  parent_slots=sorted({f"0x00ff{int(r['data'],16)&0xffff:04x}" for r in parent_rows})
  spawn_rows=[r for r in context_writes
              if f"0x{int(r['pc'],16):06x}" in spawn_pcs[cls] and
                 int(r['inner'],16)==0]
  req(len(spawn_rows)==TYPE36_LIFETIMES[cls],
      f'type-36 {cls} spawn-context count drift')
  spawn_contexts=[]
  for key in sorted({(r['pc'],r['parent_active'],r['parent_class'],
                      r['parent_type'],r['parent_state'],r['parent_substate'],
                      r['parent_animation_record'],r['route'])
                     for r in spawn_rows}):
   matching=[r for r in spawn_rows if
             (r['pc'],r['parent_active'],r['parent_class'],r['parent_type'],
              r['parent_state'],r['parent_substate'],
              r['parent_animation_record'],r['route'])==key]
   pc,active,parent_class,parent_type,state,substate,animation,route=key
   spawn_contexts.append({
       'writer_pc':f'0x{int(pc,16):06x}',
       'count':len(matching),'parent_active_u8':int(active),
       'parent_class_u8':int(parent_class,16),
       'parent_record_type_u8':int(parent_type),
       'parent_state_u16':int(state,16),
       'parent_substate_u16':int(substate,16),
       'parent_animation_record':f'0x{int(animation,16):08x}',
       'route_state_u16':int(route),
       'allocation_rule':'pop next free type-36 record from shared fixed pool'})
  suppression_path=TYPE36_SUPPRESS[cls]
  suppression_actors=rows(suppression_path/'coffee_shop_scene_actors.tsv')
  suppression_result=rows(suppression_path/'progression_result.tsv')[0]
  suppression_last=rows(suppression_path/'coffee_shop_scene_frames.tsv')[-1]
  projection_fields=('route_state','living_enemy_count','encounter_progress',
                     'player_state','player_substate','player_x_fp','player_y_fp',
                     'player_z','player_health','camera_x','camera_z','rng')
  remaining=sum(r['pool']=='record36' and f"0x{r['class']}"==cls
                for r in suppression_actors)
  direct_audio=sum(0xffd280<=int(r['a6'],16)<=0xffe27f
                   for r in dispatches)
  direct_health=sum(0xffd280<=int(r['attacker'],16)<=0xffe27f or
                    0xffd280<=int(r['defender'],16)<=0xffe27f for r in health)
  first,last=TYPE36_BODY[cls]
  classes.append({'type':36,'class':cls,
   'classification':'SOURCE_CLOSED_PRESENTATION','semantic_name':'UNKNOWN',
   'scheduler':'0x01bd48, ascending 0x40-byte fixed-pool slots',
   'dispatch_entry':f'0x{first:06x}','source_body_end_exclusive':f'0x{last:06x}',
   'source_body_sha256':hashlib.sha256(op[first:last]).hexdigest(),
   'source_spawn_writers':spawn_pcs[cls],'parent_field':parent_fields[cls],
   'source_spawn_contexts':spawn_contexts,
   'parent_slots':parent_slots,'lifetime_count':len(lifetimes),
   'lifetimes':lifetimes,'state_substate_contexts':sorted({
       f"0x{int(r['state'],16):04x}:0x{int(r['substate'],16):04x}" for r in sample}),
   'variants_u8':sorted({int(r['variant'],16) for r in sample}),
   'animation_records':records,'state_transition_rules':state_rules[cls],
   'rng_calls':0,'direct_collision_damage_writes':direct_health,
   'direct_audio_writes':direct_audio,'direct_route_camera_writes':0,
   'fixed_pool_allocation_is_observable':True,
   'counterfactual':{'capture':suppression_path.name,
      'suppressed_writes':int(suppression_result['type36_suppressed_writes']),
      'remaining_target_actor_rows':remaining,
      'actor_population_difference':remaining==0,
      'final_gameplay_projection_unchanged':all(
          baseline_last[field]==suppression_last[field]
          for field in projection_fields),
      'fixed_pool_order_may_change_downstream_projection':cls in ('0x04','0x05')},
   'implementation_rule':'native source-owned presentation actor in the shared fixed pool; it must not become independent gameplay authority',
   'fixed_frame_substitute_forbidden':True})
 req(all(item['direct_collision_damage_writes']==0 and
         item['direct_audio_writes']==0 and
         item['direct_route_camera_writes']==0 and
         item['counterfactual']['actor_population_difference']
         for item in classes),'type-36 presentation authority drift')
 return {'classification':'SOURCE_CLOSED_IMPLEMENTATION_FIELDS',
   'capture_identity':{'completion_a':identity_a,'completion_b':identity_b,
                       'byte_identical':True,
                       'spawn_context_a':context_identity_a,
                       'spawn_context_b':context_identity_b,
                       'spawn_context_byte_identical':True},
   'pool':{'record_type_u8':36,'base':'0xffd280','capacity':64,
           'stride_u16':0x40,'scheduler':'0x01bd48'},
   'classes':classes,'required_pairs':4,'closed_pairs':4,
   'retained_gameplay_authority':False}

def coffee_shop_scene_component_identities(op,program):
 files=('coffee_shop_scene_actors.tsv','coffee_shop_scene_frames.tsv',
        'coffee_shop_scene_health_writes.tsv','coffee_shop_rng_calls.tsv',
        'dispatches.tsv','progression_result.tsv')
 identity_a={name:sha(SCENE_COMPONENT_A/name) for name in files}
 identity_b={name:sha(SCENE_COMPONENT_B/name) for name in files}
 req(identity_a==identity_b,'Coffee Shop component baseline captures differ')
 baseline={name:rows(SCENE_COMPONENT_A/name) for name in files}
 detail_files=('coffee_shop_component20_writes.tsv',
               'coffee_shop_component20_dispatch.tsv',
               'coffee_shop_component20_collision.tsv',
               'coffee_shop_component20_global.tsv',
               'coffee_shop_scene_health_writes.tsv')
 detail_identity_a={name:sha(SCENE_COMPONENT_DETAIL_A/name)
                    for name in detail_files}
 detail_identity_b={name:sha(SCENE_COMPONENT_DETAIL_B/name)
                    for name in detail_files}
 req(detail_identity_a==detail_identity_b,
     'Coffee Shop type-20 implementation captures differ')
 cadence_files=('coffee_shop_scene_actors.tsv',
                'coffee_shop_component20_dispatch.tsv',
                'progression_transactions.tsv','progression_result.tsv')
 cadence_identity_a={name:sha(SCENE_CADENCE_A/name)
                     for name in cadence_files}
 cadence_identity_b={name:sha(SCENE_CADENCE_B/name)
                     for name in cadence_files}
 req(cadence_identity_a==cadence_identity_b,
     'Coffee Shop scheduler-phase cadence captures differ')
 cadence_dispatch=rows(SCENE_CADENCE_A/
                       'coffee_shop_component20_dispatch.tsv')
 cadence_controller=rows(SCENE_CADENCE_A/'progression_transactions.tsv')
 class02_cadence=[]
 controller_cadence=[]
 for frame in range(2073,2078):
  class02_cadence.append({
   'source_frame_u16':frame,
   'dispatch_count_u8':sum(r['slot']=='ffb600' and r['pc']=='06b534' and
                           int(r['frame'])==frame for r in cadence_dispatch)})
  controller_cadence.append({
   'source_frame_u16':frame,
   'dispatch_count_u8':sum(r['pc']=='0288e2' and int(r['frame'])==frame
                           for r in cadence_controller)})
 req([r['dispatch_count_u8'] for r in class02_cadence]==[1,1,2,2,1] and
     [r['dispatch_count_u8'] for r in controller_cadence]==[0,1,3,1,1],
     'Coffee Shop controller/type-20 scheduler-phase cadence drift')
 phase_files=('coffee_shop_component20_callers.tsv',
              'coffee_shop_scheduler_phase.tsv')
 phase_identity_a={name:sha(SCENE_PHASE_A/name) for name in phase_files}
 phase_identity_b={name:sha(SCENE_PHASE_B/name) for name in phase_files}
 req(phase_identity_a==phase_identity_b,
     'Coffee Shop class-0x02 phase-owner captures differ')
 phase_callers=rows(SCENE_PHASE_A/'coffee_shop_component20_callers.tsv')
 req(phase_callers and all(r['caller_pc']=='01bc6e' and
                           r['target']=='06b534' and r['a5']=='ff8000'
                           for r in phase_callers),
     'Coffee Shop class-0x02 phase caller provenance drift')
 class02_phase_counts=Counter(int(r['frame']) for r in phase_callers
                              if r['a6']=='ffb600')
 class02_phase_exceptions=[
  {'source_frame_u16':frame,
   'updates_u8':class02_phase_counts[frame]}
  for frame in range(2072,5567) if class02_phase_counts[frame]!=1]
 req(len(class02_phase_exceptions)==113 and
     Counter(r['updates_u8'] for r in class02_phase_exceptions)==
      Counter({0:45,2:2,3:53,4:13}) and
     class02_phase_exceptions[:5]==[
      {'source_frame_u16':2075,'updates_u8':2},
      {'source_frame_u16':2076,'updates_u8':2},
      {'source_frame_u16':2165,'updates_u8':4},
      {'source_frame_u16':2260,'updates_u8':0},
      {'source_frame_u16':2265,'updates_u8':0}] and
     class02_phase_exceptions[-1]==
      {'source_frame_u16':5566,'updates_u8':0},
     'Coffee Shop class-0x02 full-scene phase cadence drift')
 class02_phase_exceptions_sha256=hashlib.sha256(
  canon(class02_phase_exceptions)).hexdigest()
 record20_exit_prefix_counts=Counter(
  int(r['frame']) for r in phase_callers if r['a6']=='ffb300' and
  5453<=int(r['frame'])<=5523)
 record20_exit_prefix_groups=[]
 for frame in range(5453,5524):
  updates=record20_exit_prefix_counts[frame]
  if (record20_exit_prefix_groups and
      record20_exit_prefix_groups[-1]['updates_u8']==updates):
   record20_exit_prefix_groups[-1]['display_ticks_u8']+=1
  else:
   record20_exit_prefix_groups.append({
    'program_tick_u8':frame-5453,
    'display_ticks_u8':1,
    'updates_u8':updates})
 req(record20_exit_prefix_groups==[
      {'program_tick_u8':0,'display_ticks_u8':5,'updates_u8':1},
      {'program_tick_u8':5,'display_ticks_u8':10,'updates_u8':3},
      {'program_tick_u8':15,'display_ticks_u8':1,'updates_u8':4},
      {'program_tick_u8':16,'display_ticks_u8':15,'updates_u8':3},
      {'program_tick_u8':31,'display_ticks_u8':1,'updates_u8':4},
      {'program_tick_u8':32,'display_ticks_u8':7,'updates_u8':3},
      {'program_tick_u8':39,'display_ticks_u8':1,'updates_u8':4},
      {'program_tick_u8':40,'display_ticks_u8':6,'updates_u8':3},
      {'program_tick_u8':46,'display_ticks_u8':1,'updates_u8':4},
      {'program_tick_u8':47,'display_ticks_u8':6,'updates_u8':3},
      {'program_tick_u8':53,'display_ticks_u8':1,'updates_u8':4},
      {'program_tick_u8':54,'display_ticks_u8':4,'updates_u8':3},
      {'program_tick_u8':58,'display_ticks_u8':1,'updates_u8':4},
      {'program_tick_u8':59,'display_ticks_u8':5,'updates_u8':3},
      {'program_tick_u8':64,'display_ticks_u8':6,'updates_u8':4},
      {'program_tick_u8':70,'display_ticks_u8':1,'updates_u8':1}],
     'Coffee Shop record-20 exit prefix phase drift')
 auxiliary_entries_a=rows(A/'aux_entries.tsv')
 req(sha(A/'aux_entries.tsv')==sha(B/'aux_entries.tsv'),
     'Coffee Shop route-teardown dispatcher identity drift')
 teardown_type20_entries=[r for r in auxiliary_entries_a
  if int(r['type'])==20 and 5524<=int(r['frame'])<=5550]
 req(not teardown_type20_entries,
     'Coffee Shop route-teardown dispatched record-20 actor')
 scene_frames_by_id={int(r['frame']):r for r in
                     baseline['coffee_shop_scene_frames.tsv']}
 req(int(scene_frames_by_id[5523]['route_state'])==6 and
     all(int(scene_frames_by_id[frame]['route_state'])==0
         for frame in range(5524,5551)),
     'Coffee Shop route-teardown route guard drift')
 teardown_type20_rows=[r for r in baseline['coffee_shop_scene_actors.tsv']
  if int(r['type'])==20 and 5524<=int(r['frame'])<=5550]
 teardown_slots=sorted({r['slot'] for r in teardown_type20_rows})
 teardown_projection_fields=('state','substate','x_fp','y_fp','z','facing',
                             'animation_record','animation_timer',
                             'animation_branch')
 teardown_projections={slot:{tuple(r[field] for field in
   teardown_projection_fields) for r in teardown_type20_rows
   if r['slot']==slot} for slot in teardown_slots}
 req(teardown_slots==['ffb100','ffb180','ffb300','ffb480','ffb500','ffb600'] and
     all(len(values)==1 for values in teardown_projections.values()),
     'Coffee Shop route-teardown record-20 freeze drift')
 record20_route_teardown_guard={
  'classification':'SOURCE_CLOSED_IMPLEMENTATION_FIELDS',
  'transition_source_frame_u16':5524,
  'prior_route_state_u16':6,'route_teardown_state_u16':0,
  'last_source_dispatch_frame_u16':5523,
  'freeze_frame_range_inclusive_u16':[5524,5550],
  'central_release_source_frame_u16':5551,
  'active_source_slots':['0x00'+slot for slot in teardown_slots],
  'frozen_fields':list(teardown_projection_fields),
  'source_dispatch_count_u16':len(teardown_type20_entries),
  'guard':'route_state == 0 and exit_route_updates != 0 suppresses the complete record-20 pool dispatch until centralized release',
  'transition_dispatch':'exit_route_updates == 0 permits the final traversal whose result is visible on source frame 5524',
  'scheduler_scope':'complete record-20 pool; record12/class-0x1f teardown continues independently',
  'capture_identity':{
   'actors_sha256':identity_a['coffee_shop_scene_actors.tsv'],
   'frames_sha256':identity_a['coffee_shop_scene_frames.tsv'],
   'entries_sha256':sha(A/'aux_entries.tsv')},
  'mutation_control':'dispatching any active record-20 actor after route state 6 -> 0 changes a frozen animation timer or record before centralized release',
  'fixed_frame_substitute_forbidden':True}
 class02_out_camera=[r for r in phase_callers if r['a6']=='ffb300' and
                     2618<=int(r['frame'])<=2621]
 req([(int(r['frame']),r['animation_timer'],r['field4c'])
      for r in class02_out_camera]==
     [(2618,'0fff','00'),(2619,'0fff','00'),
      (2620,'0fff','00'),(2621,'0fff','00')],
     'Coffee Shop class-0x02 out-of-camera animation retention drift')
 detail_writes=rows(SCENE_COMPONENT_DETAIL_A/
                    'coffee_shop_component20_writes.tsv')
 class02_camera_entry_rows=[r for r in phase_callers
  if r['a6']=='ffb300' and 2638<=int(r['frame'])<=2641]
 req([(int(r['frame']),r['field4c'],r['animation_timer'],
       int(r['camera_x'])) for r in class02_camera_entry_rows]==[
      (2638,'00','0fff',751),(2639,'00','0fff',752),
      (2640,'01','0fff',753),(2641,'01','0ffe',754)],
     'Coffee Shop class-0x02 camera-entry animation phase drift')
 class02_camera_entry_writes=[r for r in detail_writes
  if r['slot']=='ffb300' and 2639<=int(r['frame'])<=2640 and
     r['pc'] in ('06b5ba','016e1e','016e22','016e28','016e08')]
 req([(int(r['frame']),r['pc'],r['inner'],r['data'])
      for r in class02_camera_entry_writes]==[
      (2639,'06b5ba','4c','00000101'),
      (2639,'016e1e','1c','00000006'),
      (2639,'016e1e','1e','0000b66c'),
      (2639,'016e22','0a','00000fff'),
      (2639,'016e28','24','00008000'),
      (2640,'016e08','0a','00000ffe')],
     'Coffee Shop class-0x02 camera-entry bind/decrement writes drift')
 class02_camera_entry={
  'source_slot':'0x00ffb300',
  'predicate_transition_source_frame_u16':2639,
  'entry_samples':[{
   'source_frame_u16':int(r['frame']),
   'in_camera_bounds_u8':int(r['field4c'],16),
   'animation_timer_u16':int(r['animation_timer'],16),
   'camera_x_u16':int(r['camera_x'])} for r in class02_camera_entry_rows],
  'predicate_writer_pc':'0x06b5ba',
  'animation_bind_writers':['0x016e1e','0x016e22','0x016e28'],
  'first_decrement_writer_pc':'0x016e08',
  'bound_animation_record':'0x0006b66c',
  'bound_animation_timer_u16':4095,
  'bound_animation_branch_s16':-32768,
  'rule':'when actor+0x4c changes from zero to nonzero, bind the current selector and return without advancing it; the next in-camera dispatch performs the first timer decrement',
  'mutation_control':'immediate decrement on the zero-to-nonzero dispatch changes the frame-2640 entry timer from 4095 to 4094'}
 detail_health=rows(SCENE_COMPONENT_DETAIL_A/
                    'coffee_shop_scene_health_writes.tsv')
 detail_collision=rows(SCENE_COMPONENT_DETAIL_A/
                       'coffee_shop_component20_collision.tsv')
 detail_global=rows(SCENE_COMPONENT_DETAIL_A/
                    'coffee_shop_component20_global.tsv')
 spawn_rows=[r for r in detail_writes if r['pc']=='01bf1e' and
             r['a1'] in ('15c108','15c128','15c158','15c178')]
 req([(int(r['frame']),r['a1'],r['slot']) for r in spawn_rows]==[
     (2072,'15c108','ffb600'),(2072,'15c128','ffb580'),
     (2242,'15c158','ffb400'),(2617,'15c178','ffb300')],
     'Coffee Shop type-20 stage-record ownership drift')
 class02_damage=[r for r in detail_health if r['target_pool']=='record20'
                 and r['target_slot']=='ffb300' and int(r['frame'])==2804]
 req([(r['pc'],r['attacker'],r['attack_record'],r['health_before'],
       r['health_after'],r['damage_writer']) for r in class02_damage]==[
      ('01d590','ff8380','11af76','0000','ffe7','1'),
      ('01d598','ff8380','11af76','ffe7','ffff','0')],
     'Coffee Shop class-0x02 collision/damage writer drift')
 req([(r['frame'],r['pc'],r['a0'],r['a1'],r['a2'],r['a3'],r['a6'])
      for r in detail_collision]==[
      ('2804','01d590','06b66c','ffb300','06b6f4','11af76','ff8380'),
      ('2804','01d598','06b66c','ffb300','06b6f4','11af76','ff8380'),
      ('2804','01d4aa','06b66c','ffb300','06b6f4','11af76','ff8380')],
     'Coffee Shop class-0x02 collision pointer provenance drift')
 class02_positions=[r for r in baseline['coffee_shop_scene_actors.tsv']
                    if r['frame']=='2804' and
                    r['slot'] in ('ff8380','ffb300')]
 req([(r['slot'],r['x_fp'],r['facing']) for r in class02_positions]==[
      ('ff8380','04430000','1'),('ffb300','04800000','0')],
     'Coffee Shop class-0x02 reaction-direction inputs drift')
 req([(r['frame'],r['pc'],r['old'],r['data'],r['a6'])
      for r in detail_global]==[
      ('2072','028814','0000','00000001','ffd180'),
      ('5151','028a02','0001','00000000','ffd180')],
     'Coffee Shop class-0x01 external scene-active flag ownership drift')
 stage_records={
  (20,'0x01'):[
   {'address':'0x0015c128','camera_threshold_u16':512,'x_s16':816,
    'y_s16':336,'allocator_u16':4,'class_u8':1,'variant_u8':0,
    'guard_0a_s8':0,'guard_0b_u8':0,'facing_u8':0,'field_0d_u8':0,
   'timer_u16':0},
   {'address':'0x0015c158','camera_threshold_u16':672,'x_s16':1104,
    'y_s16':336,'allocator_u16':4,'class_u8':1,'variant_u8':1,
    'guard_0a_s8':0,'guard_0b_u8':0,'facing_u8':0,'field_0d_u8':0,
   'timer_u16':0}],
  (20,'0x02'):[
   {'address':'0x0015c108','camera_threshold_u16':512,'x_s16':752,
    'y_s16':336,'allocator_u16':4,'class_u8':2,'variant_u8':0,
    'guard_0a_s8':0,'guard_0b_u8':0,'facing_u8':0,'field_0d_u8':0,
   'timer_u16':0},
   {'address':'0x0015c178','camera_threshold_u16':736,'x_s16':1152,
    'y_s16':336,'allocator_u16':4,'class_u8':2,'variant_u8':0,
    'guard_0a_s8':0,'guard_0b_u8':0,'facing_u8':0,'field_0d_u8':0,
    'timer_u16':0}],
   (20,'0x0f'):[
    {'address':'0x0015c1b8','camera_threshold_u16':816,'x_s16':1301,
     'y_s16':240,'allocator_u16':4,'class_u8':15,'variant_u8':0,
     'guard_0a_s8':0,'guard_0b_u8':0,'facing_u8':0,'field_0d_u8':0,
     'timer_u16':0}]}
 observed_spawns={
  '0x0015c108':(2072,'0x00ffb600'),
   '0x0015c128':(2072,'0x00ffb580'),
   '0x0015c158':(2242,'0x00ffb400'),
   '0x0015c178':(2617,'0x00ffb300'),
   '0x0015c1b8':(2672,'0x00ffb100')}
 scene_frame_by_id={int(r['frame']):r for r in
                    baseline['coffee_shop_scene_frames.tsv']}
 scene_actor_rows=baseline['coffee_shop_scene_actors.tsv']
 stage_camera_order=[]
 for address,(writer_frame,source_slot) in observed_spawns.items():
  slot=source_slot[4:]
  first_actor_frame=min(int(r['frame']) for r in scene_actor_rows
                        if r['slot']==slot)
  stage_camera_order.append({
   'address':address,'writer_source_frame_u16':writer_frame,
   'camera_x_u16':int(scene_frame_by_id[writer_frame]['camera_x']),
   'first_actor_visible_frame_u16':first_actor_frame,
   'source_slot':source_slot})
 stage_camera_order.sort(key=lambda r:int(r['address'],16))
 req(stage_camera_order==[
      {'address':'0x0015c108','writer_source_frame_u16':2072,
       'camera_x_u16':640,'first_actor_visible_frame_u16':2073,
       'source_slot':'0x00ffb600'},
      {'address':'0x0015c128','writer_source_frame_u16':2072,
       'camera_x_u16':640,'first_actor_visible_frame_u16':2073,
       'source_slot':'0x00ffb580'},
      {'address':'0x0015c158','writer_source_frame_u16':2242,
       'camera_x_u16':675,'first_actor_visible_frame_u16':2243,
       'source_slot':'0x00ffb400'},
       {'address':'0x0015c178','writer_source_frame_u16':2617,
        'camera_x_u16':736,'first_actor_visible_frame_u16':2618,
        'source_slot':'0x00ffb300'},
       {'address':'0x0015c1b8','writer_source_frame_u16':2672,
        'camera_x_u16':817,'first_actor_visible_frame_u16':2673,
        'source_slot':'0x00ffb100'}],
     'Coffee Shop stage camera-sample chronology drift')
 for records_ in stage_records.values():
  for record in records_:
   address=int(record['address'],16)
   raw=bytes.fromhex(
       f"{record['camera_threshold_u16']:04x}"
       f"{record['x_s16'] & 0xffff:04x}{record['y_s16'] & 0xffff:04x}"
       f"{record['allocator_u16']:04x}{record['class_u8']:02x}"
       f"{record['variant_u8']:02x}{record['guard_0a_s8'] & 0xff:02x}"
       f"{record['guard_0b_u8']:02x}{record['facing_u8']:02x}"
       f"{record['field_0d_u8']:02x}{record['timer_u16']:04x}")
   req(program[address:address+16]==raw,
       f"Coffee Shop stage record {address:06x} bytes drift")
   record['record_sha256']=hashlib.sha256(raw).hexdigest()
   record['observed_source_frame'],record['observed_source_slot']=\
    observed_spawns[record['address']]
  class0f_files=('coffee_shop_component20_writes.tsv',
                 'coffee_shop_component20_dispatch.tsv',
                 'coffee_shop_component20_collision.tsv',
                 'coffee_shop_scene_actors.tsv',
                 'coffee_shop_scene_frames.tsv','coffee_shop_rng_calls.tsv',
                 'coffee_shop_scene_health_writes.tsv','dispatches.tsv',
                 'progression_result.tsv')
  class0f_detail_a={name:sha(CLASS0F_DETAIL_A/name)
                    for name in class0f_files}
  class0f_detail_b={name:sha(CLASS0F_DETAIL_B/name)
                    for name in class0f_files}
  class0f_counter_a={name:sha(CLASS0F_COUNTER_A/name)
                     for name in class0f_files}
  class0f_counter_b={name:sha(CLASS0F_COUNTER_B/name)
                     for name in class0f_files}
  req(class0f_detail_a==class0f_detail_b,
      'Coffee Shop class-0x0f cold-reference captures differ')
  req(class0f_counter_a==class0f_counter_b,
      'Coffee Shop class-0x0f counterfactual captures differ')
  class0f_base_actors=[r for r in rows(
      CLASS0F_DETAIL_A/'coffee_shop_scene_actors.tsv')
      if r['slot']=='ffb100']
  req(len(class0f_base_actors)==2878 and
      class0f_base_actors[0]['frame']=='2673' and
      class0f_base_actors[-1]['frame']=='5550' and
      {r['state'] for r in class0f_base_actors}=={'0200'} and
      {r['substate'] for r in class0f_base_actors}=={'0000'} and
      {r['animation_record'] for r in class0f_base_actors}=={'0006ee4a'} and
      {r['x_fp'] for r in class0f_base_actors}=={'05150000'} and
      {r['y_fp'] for r in class0f_base_actors}=={'00f00000'} and
      {r['z'] for r in class0f_base_actors}=={'240'},
      'Coffee Shop class-0x0f baseline lifetime/state drift')
  class0f_base_dispatch=[r for r in rows(
      CLASS0F_DETAIL_A/'coffee_shop_component20_dispatch.tsv')
      if r['slot']=='ffb100' and r['pc'] in
      ('06ed3e','06ed52','06ed8a','06edb8','06edba','06ee02','06ee08','06ee3c')]
  class0f_base_counts=Counter((r['pc'],r['state'])
                              for r in class0f_base_dispatch)
  req(class0f_base_counts==Counter({
      ('06ed3e','0200'):2993,('06ed8a','0200'):2993,
      ('06edb8','0200'):2993,('06edba','0200'):2993,
      ('06ed3e','0000'):1,('06ed52','0000'):1}),
      'Coffee Shop class-0x0f baseline dispatch drift')
  class0f_base_collision=[r for r in rows(
      CLASS0F_DETAIL_A/'coffee_shop_component20_collision.tsv')
      if r['a6']=='ffb100']
  req(len(class0f_base_collision)==151 and
      all(r['pc']=='01d87a' and r['state']=='0200'
          for r in class0f_base_collision),
      'Coffee Shop class-0x0f collision caller drift')
  class0f_base_health=[r for r in rows(
      CLASS0F_DETAIL_A/'coffee_shop_scene_health_writes.tsv')
      if r['target_slot']=='ffb100' or r['attacker']=='ffb100' or
         r['defender']=='ffb100']
  req(class0f_base_health and
      all(r['damage_writer']=='0' for r in class0f_base_health),
      'Coffee Shop class-0x0f unexpected direct damage write')
  class0f_base_rng=[r for r in rows(
      CLASS0F_DETAIL_A/'coffee_shop_rng_calls.tsv') if r['a6']=='ffb100']
  req(not class0f_base_rng,'Coffee Shop class-0x0f direct RNG drift')
  class0f_counter_writes=[r for r in rows(
      CLASS0F_COUNTER_A/'coffee_shop_component20_writes.tsv')
      if r['slot']=='ffb100']
  forced_state_writes=[r for r in class0f_counter_writes
      if r['pc'] in ('000d9c','000da8') and r['inner']=='04']
  req([(r['frame'],r['data'],r['mask']) for r in forced_state_writes]==[
      ('2673','00000400','0000ffff'),('2674','00000400','0000ffff')],
      'Coffee Shop class-0x0f counterfactual injection drift')
  class0f_counter_dispatch=[r for r in rows(
      CLASS0F_COUNTER_A/'coffee_shop_component20_dispatch.tsv')
      if r['slot']=='ffb100']
  class0f_counter_counts=Counter((r['pc'],r['state'])
                                 for r in class0f_counter_dispatch)
  req(class0f_counter_counts[('06ed3e','0400')]==2 and
      class0f_counter_counts[('06edba','0400')]==2 and
      class0f_counter_counts[('06ee02','0200')]==1 and
      class0f_counter_counts[('06ee08','0200')]==1,
      'Coffee Shop class-0x0f reaction branch coverage drift')
  class0f_counter_audio=[r for r in rows(CLASS0F_COUNTER_A/'dispatches.tsv')
                         if r['a6']=='ffb100']
  req([(r['frame'],r['command'],r['return1'],r['d2'])
       for r in class0f_counter_audio]==[
       ('2673','0077','06edc0','00002000'),
       ('2674','0142','06edc0','00002000')],
      'Coffee Shop class-0x0f audio transactions drift')
  class0f_counter_actors=rows(CLASS0F_COUNTER_A/
                              'coffee_shop_scene_actors.tsv')
  class0f_effect=[r for r in class0f_counter_actors if r['slot']=='ffcd80']
  req(class0f_effect and class0f_effect[0]['frame']=='2675' and
      class0f_effect[0]['type']=='28' and class0f_effect[0]['class']=='09' and
      class0f_effect[0]['active']=='2' and
      class0f_effect[0]['x_fp']=='05150000' and
      class0f_effect[0]['y_fp']=='01400000' and
      class0f_effect[0]['z']=='232' and
      class0f_effect[1]['animation_record']=='000a34da',
      'Coffee Shop class-0x0f record28 effect allocation drift')
  class0f_class11=[r for r in class0f_counter_actors
                   if r['frame']=='2674' and r['type']=='24' and
                      r['class']=='11']
  req([(r['slot'],r['variant'],r['z']) for r in class0f_class11]==[
      ('ffb900','00','239'),('ffbb00','02','239'),
      ('ffbf00','01','239'),('ffc300','03','239')],
      'Coffee Shop class-0x0f class-0x11 child population drift')
  class0f_child_rng=[r for r in rows(
      CLASS0F_COUNTER_A/'coffee_shop_rng_calls.tsv')
      if r['frame']=='2673' and r['type']=='24' and r['class']=='11']
  req(len(class0f_child_rng)==28 and
      Counter(r['a6'] for r in class0f_child_rng)==Counter({
       'ffb900':7,'ffbb00':7,'ffbf00':7,'ffc300':7}),
      'Coffee Shop class-0x0f class-0x11 child RNG ownership drift')
  class0f_counter_rng=[r for r in rows(
      CLASS0F_COUNTER_A/'coffee_shop_rng_calls.tsv') if r['a6']=='ffb100']
  req(not class0f_counter_rng,
      'Coffee Shop class-0x0f counterfactual consumed direct RNG')
  class0f_program={
   'semantic_role':'SOURCE_STATIC_COLLIDABLE_SCENE_COMPONENT',
   'source_body':{'first':'0x0006ed3e','last_exclusive':'0x0006ee42',
    'sha256':hashlib.sha256(op[0x6ed3e:0x6ee42]).hexdigest()},
   'dispatch_tables':[
    {'address':'0x0006ed4a','index':'actor+0x04 high byte:u8',
     'entry_count_u8':4,'offsets_s16':[8,64,112,242],
     'targets':['0x0006ed52','0x0006ed8a','0x0006edba','0x0006ee3c']},
    {'address':'0x0006edb4','index':'actor+0x05 low byte:u8',
     'entry_count_u8':2,'offsets_s16':[4,6],
     'targets':['0x0006edb8','0x0006edba']},
    {'address':'0x0006edfe','index':'2 * actor+0x42:u16 after decrement',
     'entry_count_u8':2,'offsets_s16':[10,4],
     'targets':['0x0006ee08','0x0006ee02']}],
   'stage_records':stage_records[(20,'0x0f')],
   'stage_spawn_guard':{
    'order':'16-byte records in source order; allocate all eligible records',
    'camera_predicate':'record.camera_threshold_u16 <= camera_x_u16',
    'guard_0b':'zero or equal to global route byte +0x20e',
    'guard_0a':'if negative abs(value)>global+0x1eb; otherwise value<=global+0x1eb',
    'allocation':'type-20 fixed pool under ascending scheduler 0x01bc38'},
   'scheduler':{'pool':'record20','scheduler':'0x01bc38..0x01bc78',
    'indirect_caller_pc':'0x01bc6e','source_slot':'0x00ffb100',
    'measured_lifetime_inclusive_u16':[2673,5550],
    'baseline_dispatch_counts':[
     {'pc':pc,'state_u16':f'0x{int(state,16):04x}','count_u16':count}
     for (pc,state),count in sorted(class0f_base_counts.items())]},
   'fields':{
    'active':'u8 at actor+0x00','class_and_type':'u16 at actor+0x02',
    'outer_state':'u16 at actor+0x04; high byte selects the outer table',
    'inner_phase':'u8 at actor+0x05; low byte selects the state-0x0200 table',
    'visible_facing':'u8 at actor+0x0f','x_y':'s16 source positions mirrored by signed 16.16 native coordinates',
    'z':'s16 at actor+0x18','animation_record':'u32 at actor+0x1c',
    'animation_timer':'u16 at actor+0x0a','animation_branch':'s16 at actor+0x24',
    'delay_timer':'u8 at actor+0x2c','object_flags':'u16 at actor+0x2e',
    'mode':'u16 at actor+0x40','reaction_selector':'u16 at actor+0x42',
    'hidden_reaction_facing':'u8 at actor+0x4f','table_set':'u32 at actor+0x50',
    'presentation_mode':'u8 at actor+0x64'},
   'initialization':{
    'entry':'0x0006ed52',
    'writes':['outer_state += 0x0200','table_set = 0x0006eee6',
              'object_flags = 0x8000','presentation_mode = 0x1d',
              'z = y','reaction_selector = 2','mode = 0',
              'bind animation selector 2'],
    'animation_selector_base':'0x0006ee42',
    'animation_records':[animation_record(program,0x6ee4a),
                         animation_record(program,0x6ee5e),
                         animation_record(program,0x6ee72)]},
   'state_program':{
    '0x0200':{'entry':'0x0006ed8a',
     'delay_guard':'if delay_timer:u8 is nonzero, predecrement; skip the inner handler while the result remains nonzero',
     'inner_0x00':'0x0006edb8 returns without actor-owned state changes',
     'post_handler_order':['current-state collision 0x01d87a',
                           'type-20 navigation 0x06b2e2',
                           'scheduler/presentation tail 0x0167ac']},
    '0x0202':{'entry':'outer 0x0006ed8a then inner 0x0006edba',
     'rule':'the low-byte inner phase aliases the reaction program; it is not a separate actor+0x06 substate'},
    '0x0400':{'entry':'0x0006edba',
     'order':['source command owner 0x002630','write outer_state = 0x0200',
              'predecrement reaction_selector:u16',
              'dispatch selector branch','visible_facing = hidden_reaction_facing XOR 1',
              'bind animation selector reaction_selector',
              'current-state collision 0x01d87a',
              'scheduler/presentation tail 0x0167ac'],
     'selector_1':{'entry':'0x0006ee02','shared_program':'0x0007a926',
      'allocation':{'allocator':'record24 0x0177da',
       'variant_iteration_s8':[3,2,1,0],
       'writes':['child.active += 2','child.class = 0x11',
                 'child.variant = loop counter','child.x/y/z = parent.x/y/z',
                 'child.z -= 1','child anchor x/y pairs = parent.x/y',
                 'child.hidden_reaction_facing = parent.hidden_reaction_facing',
                 'child.visible_facing = parent.visible_facing'],
       'first_visible_source_frame_u16':2674,
       'observed_source_slots_by_variant':{
        '0':'0x00ffb900','1':'0x00ffbf00','2':'0x00ffbb00',
        '3':'0x00ffc300'},
       'scheduler_order':'record20 source program allocates before the following record24 pool traversal; every child consumes seven RNG calls in its independently owned class-0x11 program',
       'child_rng_calls_u8':28,
       'child_program_ownership':'separate type24/class-0x11 source program'},
      'animation_record':'0x0006ee5e'},
     'selector_0':{'entry':'0x0006ee08','allocator':'record28 0x017828',
      'success_writes':['child.active += 2','child.class/type word = 0x0900',
                        'child+0x5c = 1','child.x = parent.x',
                        'child.y = parent.y + 80','child.z = parent.z - 8'],
      'first_source_effect':{'source_frame_u16':2675,
       'source_slot':'0x00ffcd80','record_type_u8':28,'class_u8':9,
       'active_u8':2,'x_s16':1301,'y_s16':320,'z_s16':232,
       'next_animation_record':'0x000a34da'},
      'animation_record':'0x0006ee72'}},
    '0x0600':{'entry':'0x0006ee3c',
              'rule':'release through type-20 fixed-pool release 0x017706'}},
   'collision_damage':{
    'current_state_caller':'0x0001d87a',
    'baseline_captured_calls_u16':len(class0f_base_collision),
    'animation_selectors':[
     {'animation_record':'0x0006ee4a','hurt_u8':1,'attack_u8':1},
     {'animation_record':'0x0006ee5e','hurt_u8':2,'attack_u8':2},
     {'animation_record':'0x0006ee72','hurt_u8':0,'attack_u8':3}],
    'direct_damage_writes_u8':0,
    'rule':'collision consequences, including a state 0x0202 reaction write, remain owned by the accepted current-state collision program; this class does not synthesize health or damage'},
   'audio_transactions':[
    {'trigger':'reaction_selector predecrements 2 -> 1',
     'source_frame_u16':2673,'source_slot':'0x00ffb100',
     'source_caller':'0x00002630','return_pc':'0x0006edc0',
     'command_u16':'0x0077','argument1_u32':'0x00002000',
     'shared_dispatch':'0x001922'},
    {'trigger':'reaction_selector predecrements 1 -> 0',
     'source_frame_u16':2674,'source_slot':'0x00ffb100',
     'source_caller':'0x00002630','return_pc':'0x0006edc0',
     'command_u16':'0x0142','argument1_u32':'0x00002000',
     'shared_dispatch':'0x001922'}],
   'rng':{'direct_calls':0,'direct_consumption_order':[],
    'rule':'the class-0x0f program consumes no RNG; the allocated record28/class-0x09 child owns any downstream RNG changes'},
   'route_teardown':record20_route_teardown_guard,
   'counterfactual':{
    'classification':'SOURCE_STATE_MUTATION_CONTROL',
    'capture_a':CLASS0F_COUNTER_A.name,'capture_b':CLASS0F_COUNTER_B.name,
    'byte_identical':True,'files_sha256':class0f_counter_a,
    'injection':'write source outer_state 0x0400 for the first two active class-0x0f traversals only',
    'injection_writers':['0x000d9c','0x000da8'],
    'production_authority':False,
    'covered_branches':['reaction selector 1 -> 0x06ee02',
                        'reaction selector 0 -> 0x06ee08'],
    'downstream_differences':{
     name:{'baseline_sha256':class0f_detail_a[name],
           'counterfactual_sha256':class0f_counter_a[name],
           'different':class0f_detail_a[name]!=class0f_counter_a[name]}
     for name in class0f_files},
    'changed_outcomes':['animation selector and assembly output',
                        'two source-owned audio commands',
                        'record28/class-0x09 effect allocation',
                        'downstream scene/RNG chronology']},
   'capture_identity':{
    'completion_a':CLASS0F_DETAIL_A.name,'completion_b':CLASS0F_DETAIL_B.name,
    'byte_identical':True,'files_sha256':class0f_detail_a},
   'mutation_controls':['source body','outer dispatch table','inner dispatch table',
    'reaction selector table','stage threshold/class/allocator','initial selector',
    'delay predecrement','reaction-selector predecrement','selector branch order',
    'visible-facing XOR','animation selector','collision invocation',
    'direct RNG absence','audio command identity','record28 allocation geometry',
    'route-teardown freeze/release','fixed-frame substitute'],
   'spec_executable':True,'retained_gameplay_authority':False,
   'fixed_frame_substitute_forbidden':True}
  class0a_files=('coffee_shop_class0a_program.tsv',
                 'coffee_shop_scene_actors.tsv',
                 'coffee_shop_scene_frames.tsv','coffee_shop_rng_calls.tsv',
                 'coffee_shop_scene_health_writes.tsv','dispatches.tsv',
                 'progression_result.tsv')
  class0a_detail_a={name:sha(CLASS0A_DETAIL_A/name)
                    for name in class0a_files}
  class0a_detail_b={name:sha(CLASS0A_DETAIL_B/name)
                    for name in class0a_files}
  class0a_counter_a={name:sha(CLASS0A_COUNTER_A/name)
                     for name in class0a_files}
  class0a_counter_b={name:sha(CLASS0A_COUNTER_B/name)
                     for name in class0a_files}
  req(class0a_detail_a==class0a_detail_b,
      'Coffee Shop class-0x0a cold-reference captures differ')
  req(class0a_counter_a==class0a_counter_b,
      'Coffee Shop class-0x0a counterfactual captures differ')
  class0a_base_actors=[r for r in rows(
      CLASS0A_DETAIL_A/'coffee_shop_scene_actors.tsv')
      if r['type']=='24' and r['class']=='0a']
  class0a_lifetimes={slot:[r for r in class0a_base_actors
                           if r['slot']==slot]
                       for slot in ('ffc600','ffc580')}
  req(len(class0a_lifetimes['ffc600'])==3478 and
      class0a_lifetimes['ffc600'][0]['frame']=='2073' and
      class0a_lifetimes['ffc600'][-1]['frame']=='5550' and
      {r['variant'] for r in class0a_lifetimes['ffc600']}=={'26'} and
      {r['state'] for r in class0a_lifetimes['ffc600']}=={'0200'} and
      {r['substate'] for r in class0a_lifetimes['ffc600']}=={'0000'} and
      {r['x_fp'] for r in class0a_lifetimes['ffc600']}=={'00000000'} and
      {r['y_fp'] for r in class0a_lifetimes['ffc600']}=={'00000000'} and
      {r['z'] for r in class0a_lifetimes['ffc600']}=={'0'} and
      {r['facing'] for r in class0a_lifetimes['ffc600']}=={'0'} and
      {r['animation_record'] for r in
       class0a_lifetimes['ffc600']}=={'000782a4','000782ac'},
      'Coffee Shop class-0x0a first lifetime/state drift')
  req(len(class0a_lifetimes['ffc580'])==1 and
      class0a_lifetimes['ffc580'][0]['frame']=='5566' and
      class0a_lifetimes['ffc580'][0]['variant']=='06' and
      class0a_lifetimes['ffc580'][0]['state']=='0200' and
      class0a_lifetimes['ffc580'][0]['substate']=='0000' and
      class0a_lifetimes['ffc580'][0]['animation_record']=='00077e54' and
      class0a_lifetimes['ffc580'][0]['animation_timer']=='0010' and
      class0a_lifetimes['ffc580'][0]['animation_branch']=='3072',
      'Coffee Shop class-0x0a second lifetime/state drift')
  class0a_writes=rows(CLASS0A_DETAIL_A/'coffee_shop_class0a_program.tsv')
  class0a_init_writes=[r for r in class0a_writes if r['event']=='write' and
      r['actual_pc'] in ('01bf1e','01bf22','01bf28','01bf2e','01bf34',
                         '01bf3a','01bf40','077ce6','016d4a','016d4e',
                         '016d5a') and
      ((r['frame']=='2072' and r['slot']=='ffc600') or
       (r['frame']=='5565' and r['slot']=='ffc580'))]
  req(len(class0a_init_writes)==24 and
      [(r['frame'],r['slot'],r['actual_pc'],r['inner'])
       for r in class0a_init_writes if r['actual_pc']=='077ce6']==[
        ('2072','ffc600','077ce6','04'),
        ('5565','ffc580','077ce6','04')],
      'Coffee Shop class-0x0a initialization writer drift')
  class0a_dispatch_counts={frame:0 for frame in range(2073,5524)}
  for row in class0a_writes:
   if (row['event']=='write' and row['actual_pc']=='016d34' and
       row['slot']=='ffc600' and 2073<=int(row['frame'])<=5523):
    class0a_dispatch_counts[int(row['frame'])]+=1
  class0a_cadence_exceptions=[
      {'source_frame_u16':frame,'updates_u8':count}
      for frame,count in sorted(class0a_dispatch_counts.items()) if count!=1]
  req(len(class0a_cadence_exceptions)==70 and
      sum(class0a_dispatch_counts.values())==3596 and
      class0a_cadence_exceptions[:3]==[
       {'source_frame_u16':2075,'updates_u8':2},
       {'source_frame_u16':2076,'updates_u8':2},
       {'source_frame_u16':2165,'updates_u8':4}] and
      class0a_cadence_exceptions[-1]==
       {'source_frame_u16':5522,'updates_u8':4},
      'Coffee Shop class-0x0a fixed-pool dispatch cadence drift')
  class0a_release=[r for r in class0a_writes if r['event']=='write' and
      r['frame']=='5550' and r['slot']=='ffc600' and
      r['actual_pc']=='0173c6' and r['inner']=='00']
  req(len(class0a_release)==1 and class0a_release[0]['active']=='1' and
      class0a_release[0]['class']=='0a' and
      class0a_release[0]['state']=='0200',
      'Coffee Shop class-0x0a central release writer drift')
  class0a_direct_rng=[r for r in rows(
      CLASS0A_DETAIL_A/'coffee_shop_rng_calls.tsv')
      if r['a6'] in ('ffc580','ffc600') and r['class']=='0a']
  class0a_direct_audio=[r for r in rows(CLASS0A_DETAIL_A/'dispatches.tsv')
      if r['a6'] in ('ffc580','ffc600') and r['origin_class']=='0a']
  class0a_direct_health=[r for r in rows(
      CLASS0A_DETAIL_A/'coffee_shop_scene_health_writes.tsv')
      if ((r['target_slot']=='ffc600' or r['attacker']=='ffc600' or
           r['defender']=='ffc600') and 2073<=int(r['frame'])<=5550) or
         ((r['target_slot']=='ffc580' or r['attacker']=='ffc580' or
           r['defender']=='ffc580') and int(r['frame'])==5566)]
  class0a_collision_membership=[]
  for r in rows(CLASS0A_DETAIL_A/'coffee_shop_collision_lists.tsv'):
   frame=int(r['frame'])
   class0a_collision_membership.extend(
       slot for slot in ('ffc580','ffc600')
       if ((slot=='ffc600' and 2073<=frame<=5550) or
           (slot=='ffc580' and frame==5566)) and
          (slot in r['attacker_slots'].split(',') or
           slot in r['defender_slots'].split(',')))
  req(not class0a_direct_rng and not class0a_direct_audio and
      not class0a_direct_health and not class0a_collision_membership,
      'Coffee Shop class-0x0a direct gameplay effect drift')
  class0a_counter_rows=rows(
      CLASS0A_COUNTER_A/'coffee_shop_class0a_program.tsv')
  class0a_counter_state=[r for r in class0a_counter_rows
      if r['event']=='write' and r['frame']=='2073' and
         r['slot']=='ffc600' and r['actual_pc']=='077d1c' and
         r['inner']=='04']
  class0a_counter_release=[r for r in class0a_counter_rows
      if r['event']=='write' and r['frame']=='2074' and
         r['slot']=='ffc600' and r['actual_pc']=='0177f6' and
         r['inner']=='00']
  class0a_counter_markers=[r for r in class0a_counter_rows
      if r['event'].startswith('counterfactual_')]
  req(len(class0a_counter_state)==1 and
      class0a_counter_state[0]['data']=='00000404' and
      class0a_counter_state[0]['mask']=='0000ff00' and
      len(class0a_counter_release)==1 and
      class0a_counter_release[0]['state']=='0400' and
      [(r['event'],r['tap_pc'],r['actual_pc'])
       for r in class0a_counter_markers]==[
        ('counterfactual_begin','077cf6','077cd6'),
        ('counterfactual_end','077d1a','077d18')],
      'Coffee Shop class-0x0a counterfactual branch/release drift')
  class0a_offset_bytes=op[0x77d26:0x77d26+52]
  class0a_offsets=[int.from_bytes(class0a_offset_bytes[index:index+2],
                                  'big',signed=True)
                   for index in range(0,len(class0a_offset_bytes),2)]
  req(class0a_offsets==[74,126,178,302,338,390,514,638,762,814,866,
      918,970,1022,1074,1126,1178,1230,1282,1406,1426,1462,1514,
      1638,1666,1774],
      'Coffee Shop class-0x0a animation offset table drift')
  class0a_program={
   'semantic_role':'SOURCE_PRESENTATION_FIXED_POOL_RESIDENT',
   'source_body':{'first':'0x00077ccc','last_exclusive':'0x00077d26',
    'sha256':hashlib.sha256(op[0x77ccc:0x77d26]).hexdigest()},
   'dispatch_table':{'address':'0x00077cd8',
    'index':'actor+0x04 high byte:u8','entry_count_u8':3,
    'offsets_s16':[8,30,72],
    'targets':['0x00077ce0','0x00077cf6','0x00077d20']},
   'fields':{
    'active':'u8 at actor+0x00','class_and_variant':'u16 at actor+0x02',
    'outer_state':'u16 at actor+0x04; high byte indexes dispatch table',
    'animation_timer':'u16 at actor+0x0a',
    'coordinate_mode':'u8 at actor+0x0d','visible_facing':'u8 at actor+0x0f',
    'x_y':'s16 at actor+0x10/+0x14, mirrored by signed 16.16 native fields',
    'z':'s16 at actor+0x18','animation_record':'u32 at actor+0x1c',
    'animation_branch':'s16 at actor+0x24','field_2a':'u8 at actor+0x2a'},
   'allocation_initialization':{
    'allocator':'type-24 fixed pool stage allocator 0x01bf1e..0x01bf40',
    'writes':['active = 1','class/variant word from source record',
              'x = 0','y = 0','facing = 0','coordinate_mode = 0',
              'actor+0x2a:u8 = 0'],
    'program_init_entry':'0x00077ce0',
    'program_writes':['outer_state += 0x0200',
                      'bind animation at 0x016d46 from variant byte offset'],
    'lifetimes':[
     {'source_slot':'0x00ffc600','allocator_source_frame_u16':2072,
      'first_visible_source_frame_u16':2073,
      'last_visible_source_frame_u16':5550,'variant_u8':'0x26',
      'initial_animation_record':'0x000782a4'},
     {'source_slot':'0x00ffc580','allocator_source_frame_u16':5565,
      'first_visible_source_frame_u16':5566,
      'last_visible_source_frame_u16':5566,'variant_u8':'0x06',
      'initial_animation_record':'0x00077e54'}],
    'scheduler_order':'type-24 fixed pool traverses ascending source slots under 0x01ba62; an allocation into an unvisited slot dispatches in the same traversal'},
   'scheduler_cadence':{
    'classification':'SOURCE_CAPTURE_PROJECTION_ONLY',
    'source_frame_range_inclusive_u16':[2072,5523],
    'default_updates_per_source_frame_u8':1,
    'exceptions':class0a_cadence_exceptions,
    'exception_count_u8':len(class0a_cadence_exceptions),
    'dispatch_count_u16':1+sum(class0a_dispatch_counts.values()),
    'writer_witness':'animation timer writer 0x016d34 plus initialization writer 0x077ce6',
    'rule':'align the complete-scene source scheduler projection only; never own gameplay state, release, or production timing'},
   'animation_selector':{
    'table_address':'0x00077d26','index':'actor+0x03 variant:u8 byte offset',
    'offsets_s16':class0a_offsets,
    'table_sha256':hashlib.sha256(class0a_offset_bytes).hexdigest(),
    'coffee_shop_records':[animation_record(program,0x77e54),
                           animation_record(program,0x77e5c),
                           animation_record(program,0x782a4),
                           animation_record(program,0x782ac)],
    'variant_bindings':[
     {'variant_u8':'0x06','table_entry_u8':3,
      'records':['0x00077e54','0x00077e5c']},
     {'variant_u8':'0x26','table_entry_u8':19,
      'records':['0x000782a4','0x000782ac']}]},
   'state_program':{
    '0x0000':{'entry':'0x00077ce0',
              'next_state_u16':'0x0200',
              'result':'bind the variant-selected animation record'},
    '0x0200':{'entry':'0x00077cf6',
     'variant_guard':'only variants 0x0a, 0x0c and 0x0e test the camera threshold; every other variant jumps directly to the animation runtime',
     'camera_guard':'unsigned camera_x_u16 at A5+0x0278 >= 0x0920',
     'guard_result':'outer_state += 0x0200 to 0x0400',
     'coffee_shop_result':'variants 0x26 and 0x06 bypass the threshold and remain 0x0200 while the shared animation runtime 0x016d2e advances their records'},
    '0x0400':{'entry':'0x00077d20',
              'rule':'release through type-24 fixed-pool release 0x0177f0'}},
   'presentation':{
    'variant_0x26':'two-record four-tick loop; negative branch 0x8800 returns to 0x000782a4',
    'variant_0x06':'sixteen-tick sequence beginning at 0x00077e54; only the first visible frame is inside this scene boundary',
    'position_facing_rule':'both measured lifetimes retain zero x/y/z and facing',
    'collision_selectors':'assembly records carry hurt selector 0 and attack selectors 4/7 for variant 0x26 and 16 for variant 0x06; the actors are absent from collision lists'},
   'direct_effects':{'rng_calls_u8':0,'collision_memberships_u8':0,
    'health_or_damage_writes_u8':0,'audio_transactions_u8':0,
    'route_camera_load_writes_u8':0,
    'rule':'presentation-only source actors still own fixed-pool occupancy and lifecycle; downstream allocation identity must not omit them'},
   'route_teardown':{
    'first_lifetime_release_owner':'centralized scene record clear 0x0173c6',
    'release_writer_source_frame_u16':5550,
    'first_absent_visible_source_frame_u16':5551,
    'second_lifetime_owner':'next-entry source stage allocation before the stable frame-5566 seam',
    'fixed_frame_release_forbidden':True},
   'counterfactual':{
    'classification':'SOURCE_STATE_MUTATION_CONTROL',
    'capture_a':CLASS0A_COUNTER_A.name,'capture_b':CLASS0A_COUNTER_B.name,
    'byte_identical':True,'files_sha256':class0a_counter_a,
    'injection':'for one source traversal only, change variant 0x26 to source-supported 0x0a and camera_x to 0x0920, then restore both after the guard',
    'injection_boundary':'opcode read taps are prefetch/capture projection only; actual source writer 0x077d1c and release 0x0177f6 establish execution authority',
    'production_authority':False,
    'covered_branches':['variant 0x0a camera comparison',
                        'state 0x0200 -> 0x0400','type-24 release'],
    'downstream_differences':{
     name:{'baseline_sha256':class0a_detail_a[name],
           'counterfactual_sha256':class0a_counter_a[name],
           'different':class0a_detail_a[name]!=class0a_counter_a[name]}
     for name in class0a_files},
    'changed_outcomes':['first lifetime releases at source frame 2074',
                        'later fixed-pool allocation identity',
                        'route, RNG, health and audio projection chronology']},
   'capture_identity':{
    'completion_a':CLASS0A_DETAIL_A.name,'completion_b':CLASS0A_DETAIL_B.name,
    'byte_identical':True,'files_sha256':class0a_detail_a},
   'mutation_controls':['source body','outer dispatch table',
    'variant animation offset table','variant byte-offset indexing',
    'initial state increment','animation record binding',
    'animation timer/branch/assembly/selectors','variant camera guard',
    'unsigned camera threshold','type-24 release','fixed-pool occupancy',
    'central scene clear','direct RNG absence','collision-list absence',
    'health/damage absence','audio absence','fixed-frame substitute'],
   'spec_executable':True,'retained_gameplay_authority':False,
   'fixed_frame_substitute_forbidden':True}
  implementation_contracts={
   (20,'0x01'):{
   'semantic_role':'SOURCE_CLASS_0X1F_SPAWN_CONTROLLER',
   'source_body':{'first':'0x0006b2fa','last_exclusive':'0x0006b458',
    'sha256':hashlib.sha256(op[0x6b2fa:0x6b458]).hexdigest()},
   'stage_records':stage_records[(20,'0x01')],
   'stage_spawn_guard':{
    'order':'16-byte records in source order; allocate all eligible records',
    'camera_predicate':'record.camera_threshold_u16 <= camera_x_u16',
    'guard_0b':'zero or equal to global route byte +0x20e',
    'guard_0a':'if negative abs(value)>global+0x1eb; otherwise value<=global+0x1eb',
    'allocation':'type-20 fixed pool; new actor dispatches later in the same ascending scheduler pass only when its slot has not already passed'},
   'fields':{
    'state':'u16; dispatch uses high byte','substate':'u16; nested dispatch uses high byte',
    'x_y':'s16 source coordinates mirrored by signed 16.16 native coordinates',
    'z':'s16 copied from y','action_timer':'u16 wrapping decrement',
    'remaining_spawns':'u8 at actor+0x66','variant':'u8',
    'living_enemy_count':'u16'},
   'initialization':{
    'writes':['state += 0x0200','animation_record = 0x0006b520',
              'object_flags |= 0x8000','z = y','field30_s16 = -32',
              'field34_s16 = 96','field40_u16 = 0','active_u8 = 2',
              'action_timer_u16 = 240 when variant 0 else 60',
              'remaining_spawns_u8 = 5','bind animation selector 0'],
    'animation_records':[animation_record(program,0x6b45a),
                         animation_record(program,0x6b46a),
                         animation_record(program,0x6b47a)]},
   'state_program':{
    '0x0200':'when global 0xff1a1c:u16 is zero, state=0x0400; otherwise when camera_x+192 >= x, advance the low-byte phase to state=0x0202; substate remains 0',
    '0x0202':'when action_timer_u16 is zero, advance the low-byte phase to state=0x0204; decrement timer after the zero test with u16 wrap; substate remains 0',
    '0x0204':'advance source animation while branch_s16>=0; on negative branch set state=0x0206, spawn one class-0x1f actor, allocate two four-actor type-24/class-0x43 presentation groups, and emit the source audio command; substate remains 0',
    '0x0206':'if x<camera_x set state=0x0400; else, while remaining_spawns!=0, decrement nonzero timer; when zero and living_enemy_count<6 spawn one class-0x1f actor, decrement remaining_spawns and set timer=360; substate remains 0',
    '0x0400':'when x+40 < camera_x set state=0x0600',
    '0x0600':'release through type-20 fixed-pool release 0x017706'},
   'route_interaction':{
    'scene_active_flag':'0xff1a1c:u16; read only by this component',
    'initial_writer':'0x028812 in recurring controller initialization writes 1',
    'clear_writer':'0x0289fc (captured successor 0x028a02) in recurring controller writes 0',
    'clear_guard':'after the controller progress/field48 branch, source readiness call 0x020a10 must return nonzero; controller timer42 becomes 300 and controller state/substate becomes 0x0400:0x0000 before the flag is cleared',
    'native_owner':'first-segment recurring encounter/route controller; class-0x01 must not synthesize the clear'},
   'class_0x1f_allocation':{
    'allocator':'record12 fixed pool 0x01769e','writes':['active += 1',
     'class_u8 = 0x1f','x/y/z copied from controller','variant_u8 = 5',
     'action_timer_u16 = 0','living_enemy_count += 1'],
    'scheduler_order':'record12 scheduler 0x01b934 precedes type20 scheduler 0x01bc38; newly allocated record12 dispatches on the next scheduler tick'},
   'audio_transactions':[
    {'source_frame':2328,'source_slot':'0x00ffb580','command_u16':'0x006d','argument1_u32':'0x00000500','player_side_caller':'0x0084bc','shared_dispatch':'0x001922'},
    {'source_frame':3605,'source_slot':'0x00ffb400','command_u16':'0x0139','argument1_u32':'0x00000500','player_side_caller':'0x0084bc','shared_dispatch':'0x001922'}],
   'rng':{'calls':0,'consumption_order':[]},
   'mutation_controls':['stage threshold','stage class/variant','initial timer',
    'camera predicate','living-enemy guard','spawn timer','remaining-spawn count',
    'animation terminal branch','audio command','fixed-frame substitute']},
  (20,'0x02'):{
   'semantic_role':'SOURCE_DAMAGEABLE_SCENE_PROP_CONTROLLER',
   'source_body':{'first':'0x0006b534','last_exclusive':'0x0006b660',
    'sha256':hashlib.sha256(op[0x6b534:0x6b660]).hexdigest()},
   'stage_records':stage_records[(20,'0x02')],
   'stage_spawn_guard':{
    'order':'16-byte records in source order; allocate all eligible records',
    'camera_predicate':'record.camera_threshold_u16 <= camera_x_u16',
    'guard_0b':'zero or equal to global route byte +0x20e',
    'guard_0a':'if negative abs(value)>global+0x1eb; otherwise value<=global+0x1eb',
    'allocation':'type-20 fixed pool under ascending scheduler 0x01bc38'},
   'fields':{
    'state':'u16; dispatch uses high byte','substate':'u16; dispatch uses high byte',
    'x_y':'s16 source coordinates mirrored by signed 16.16 native coordinates',
    'z':'s16 copied from y','delay_timer':'u16 at actor+0x2c',
    'effect_count':'u8 at actor+0x42','in_camera_bounds':'u8 at actor+0x4c',
    'health':'s16 at actor+0x66'},
   'initialization':{
    'writes':['state += 0x0200','animation_record = 0x0006b6ea',
              'object_flags |= 0x8000','z = y','field30_s16 = 0',
              'field34_s16 = 80','field40_u16 = 0','effect_count_u8 = 5',
              'in_camera_bounds = ((u16)(x-camera_x+16) <= 0x01a0)',
              'bind selector effect_count when in bounds else 0'],
    'animation_records':[animation_record(program,0x6b66c),
                         animation_record(program,0x6b680)]},
   'state_program':{
    '0x0200':'predecrement nonzero delay_timer and skip the subhandler until it reaches zero; substate 0 recomputes in_camera_bounds from (u16)(x-camera_x+16)<=0x01a0, retains the bound animation timer while the result is zero, and advances source animation only while it is nonzero; substate 0x0200 enters the state-0x0400 handler',
    '0x0400':'write state=0x0200; predecrement effect_count; if it reaches zero allocate one record28 child at x+8,y+64,z-8 with source class field 0x05 and field5c=1; always clear field40, bind selector effect_count, allocate four type-24/class-0x47 presentation actors, then emit command 0x0077',
    '0x0600':'release through type-20 fixed-pool release 0x017706'},
   'scheduler_phase_evidence':{
    'classification':'SOURCE_CLOSED_IMPLEMENTATION_FIELDS',
    'capture_a':SCENE_CADENCE_A.name,'capture_b':SCENE_CADENCE_B.name,
    'byte_identical':True,'files_sha256':cadence_identity_a,
    'source_frame_range_inclusive_u16':[2073,2077],
    'class02_dispatch_entry':'0x06b534',
    'class02_source_slot':'0x00ffb600',
    'class02_dispatch_counts':class02_cadence,
    'controller_dispatch_entry':'0x0288e2',
    'controller_dispatch_counts':controller_cadence,
    'finding':'captured controller invocations are not a full-scheduler cadence proxy; frame 2075 has three controller dispatches but two record-20/class-0x02 dispatches, while frame 2076 has one controller dispatch and two class-0x02 dispatches',
    'phase_owner':{
     'capture_a':SCENE_PHASE_A.name,'capture_b':SCENE_PHASE_B.name,
     'byte_identical':True,'files_sha256':phase_identity_a,
     'indirect_caller_pc':'0x01bc6e','dispatch_target':'0x06b534',
     'global_base_a5':'0xff8000','source_pool':'record20',
     'source_pool_scheduler':'0x01bc38..0x01bc78'},
    'class02_source_update_cadence':{
     'classification':'SOURCE_CLOSED_IMPLEMENTATION_FIELDS',
     'source_frame_range_inclusive_u16':[2072,5566],
     'source_slot':'0x00ffb600','default_updates_per_source_frame_u8':1,
     'exceptions':class02_phase_exceptions,
     'exceptions_sha256':class02_phase_exceptions_sha256,
     'rule':'diagnostic source-frame replay dispatches the native class-0x02 body once per captured source call from the record-20 scheduler; this does not own gameplay transitions',
     'mutation_control':'controller cadence 3/1 at frames 2075/2076 is rejected in favor of the captured class-0x02 cadence 2/2',
     'fixed_frame_gameplay_authority_forbidden':True},
    'record20_exit_prefix_scheduler':{
     'classification':'SOURCE_CLOSED_IMPLEMENTATION_FIELDS',
     'source_frame_range_inclusive_u16':[5453,5523],
     'source_pool':'record20','source_pool_scheduler':'0x01bc38..0x01bc78',
     'indirect_caller_pc':'0x01bc6e','dispatch_target':'0x06b534',
     'prefix_probe_slot':'0x00ffb300',
     'prefix_source_slot_range_inclusive':['0x00ffb180','0x00ffb500'],
     'source_phase_split_after_slot':'0x00ffb500',
     'suffix_first_slot':'0x00ffb600',
     'groups':record20_exit_prefix_groups,
     'files_sha256':phase_identity_a,
     'byte_identical':True,
     'rule':'a complete record-20 pool traversal may cross a display boundary; Coffee Shop exit differential replay therefore preserves the captured prefix phase for every active slot below 0x00ffb600 and the existing suffix cadence from slot 0x00ffb600 onward',
     'gameplay_transition_owner':'actor state/substate program; scheduler phase changes dispatch count only',
     'mutation_control':'using the suffix cadence for prefix slots changes frame 5469 class-0x02 timer 1411 to 1412 and class-0x09 timers 2 to 3',
     'route_teardown_dispatch_guard':record20_route_teardown_guard,
     'fixed_frame_gameplay_authority_forbidden':True},
    'out_of_camera_animation_retention':{
     'source_slot':'0x00ffb300','source_frames_inclusive_u16':[2618,2621],
     'in_camera_bounds_u8':0,'animation_timer_u16':4095,
     'rule':'actor+0x4c == 0 retains the bound animation timer; no animation advance occurs until the source bounds predicate becomes nonzero',
     'mutation_control':'unconditional per-dispatch animation decrement changes frame 2619 from 4095 to 4094'},
    'camera_entry_animation_rebind':class02_camera_entry,
    'exact_native_blocker':'resolved implementation field: differential replay must separate class-0x02 dispatch cadence from recurring-controller cadence',
    'fixed_frame_gameplay_authority_forbidden':True},
   'collision_damage':{
    'current_state_writer':'0x01d590 then signed clamp 0x01d598',
    'source_frame':2804,'attacker':'0x00ff8380','defender':'0x00ffb300',
    'attack_record':'0x0011af76','health_before_s16':0,
    'damage_s16':25,'health_after_clamp_s16':-1,
    'reaction_writer':'0x01d4aa writes state 0x0400',
    'reaction_delay':{
     'field':'defender+0x2c:u16','value_u16':3,
     'value_source':'current attack record 0x0011af76 hit_value_u8',
     'consumer':'class-0x02 state 0x0200 predecrements the nonzero delay and suppresses its animation subhandler until the third update reaches zero',
     'coffee_shop_witness':{'bound_frame_u16':2806,
      'retained_through_frame_u16':2808,
      'first_animation_decrement_frame_u16':2809,
      'retained_animation_timer_u16':4095}},
    'hurt_selector_u8':1,'attack_selector_u8':0,
    'attack_box':{'address':'0x0011af76','x_center_s8':0,
     'y_center_s8':48,'x_half_u8':88,'y_half_u8':48,
     'z_center_s8':0,'z_half_u8':40,'hit_value_u8':3,
     'knockback_mode_s8':1},
    'hurt_record':{'address':'0x0006b6f4','record_bytes':'08400820fc04ff00',
     'x_center_s8':8,'y_center_s8':64,'x_half_u8':8,'y_half_u8':32,
     'z_center_s8':-4,'z_half_u8':4,'flags_u16':'0xff00'},
   'overlap':'strict per-axis rectangle overlap using the sum of player attack and defender hurt half extents',
   'reaction_direction':{
    'field':'defender+0x4f:u8; hidden reaction direction, distinct from visible facing at defender+0x0f',
    'caller_chain':['0x01c984 selects the active player',
                    '0x01ced0 loops the record-20 pointer list',
                    '0x01cf1c resolves current attack/hurt records',
                    '0x01d0a8 owns the accepted overlap successor'],
    'source_body':{'first':'0x0001d0c8','last_exclusive':'0x0001d0fa',
     'sha256':hashlib.sha256(op[0x1d0c8:0x1d0fa]).hexdigest()},
    'initial_writer':'0x01d0c8 copies attacker+0x0f:u8',
    'attack_mode_guard':'attack_record+0x0a:s8 is +1; zero preserves the copied attacker facing and negative XORs it',
    'positive_mode_writers':['0x01d0dc clears defender+0x4f',
                             '0x01d0ec increments defender+0x4f when attacker_x_u16 < defender_x_u16'],
    'comparison':'move.w attacker+0x10,d0; cmp.w defender+0x10,d0; bcc skips increment when attacker_x_u16 >= defender_x_u16',
    'rule':'positive attack mode writes 1 when attacker_x_u16 < defender_x_u16, otherwise 0',
    'observed_inputs':{'source_frame':2804,'attacker_x_u16':1091,
                       'defender_x_u16':1152,'attack_mode_s8':1},
    'result_u8':1,
    'consumer':'0x08eb6c copies defender+0x4f into every spawned class-0x47 child direction field',
    'evidence':{'capture_a':'oracle11_progression_lifecycle_cs27a',
                'capture_b':'oracle11_progression_lifecycle_cs27b',
                'actor_rows_sha256':identity_a['coffee_shop_scene_actors.tsv'],
                'collision_rows_sha256':detail_identity_a['coffee_shop_component20_collision.tsv'],
                'byte_identical':True}}},
   'audio_transactions':[{'source_frame':2805,'source_slot':'0x00ffb300',
    'command_u16':'0x0077','argument1_u32':'0x00001d00',
    'player_side_caller':'0x0084bc','shared_dispatch':'0x001922'}],
   'rng':{'calls':0,'consumption_order':[]},
    'mutation_controls':['stage threshold','stage class','camera-bounds span',
     'bounds sign','collision writer','attack record','signed health clamp',
     'reaction delay/hit-value','reaction-direction attack-mode guard',
     'reaction-direction x comparison',
     'effect-count predecrement','audio command','fixed-frame substitute']}}
 implementation_contracts[(20,'0x0f')]=class0f_program
 implementation_contracts[(24,'0x0a')]=class0a_program
 for contract in implementation_contracts.values():
   if 'stage_records' not in contract:
    continue
   addresses={row['address'] for row in contract['stage_records']}
   contract['stage_spawn_guard']['camera_sample_order']={
    'rule':'compare against the camera position projected for the current source frame, before the native player step computes the next frame camera',
    'records':[row for row in stage_camera_order
               if row['address'] in addresses],
    'mutation_control':'using the post-player next-frame camera moves the threshold-736 actor one visible frame early'}
 player_route=json.loads(PLAYER_ROUTE.read_text(encoding='ascii'))
 class20=dict(player_route['interaction_action_and_interruption']
              ['implementation_contract']['class20_effect'])
 class20['semantic_role']='PLAYER_INTERACTION_PRESENTATION_COORDINATION'
 class20['source_body']={
  'first':'0x0007f9a8','last_exclusive':'0x0007fb52',
  'sha256':hashlib.sha256(op[0x7f9a8:0x7fb52]).hexdigest()}
 class20['spec_executable']=True
 class20['retained_gameplay_authority']=False
 implementation_contracts[(24,'0x20')]=class20
 components=[]
 for pair in sorted(SCENE_COMPONENT_DISPATCH):
  typ,cls=pair;mutant_path=SCENE_COMPONENT_SUPPRESS[pair]
  suppression=rows(mutant_path/'coffee_shop_pair_suppression.tsv')
  req(len(suppression)>0 and len(suppression)<=SCENE_COMPONENT_LIFETIMES[pair],
      f'Coffee Shop {pair} suppression count drift')
  mutant={name:rows(mutant_path/name) for name in files}
  actor_rows=[r for r in baseline['coffee_shop_scene_actors.tsv']
              if int(r['type'])==typ and f"0x{r['class']}"==cls]
  req(actor_rows,f'Coffee Shop {pair} missing baseline actor rows')
  routine=SCENE_COMPONENT_DISPATCH[pair]
  differences={name:{'baseline_sha256':identity_a[name],
                     'mutant_sha256':sha(mutant_path/name),
                     'different':identity_a[name]!=sha(mutant_path/name)}
               for name in files}
  last_base=baseline['coffee_shop_scene_frames.tsv'][-1]
  last_mutant=mutant['coffee_shop_scene_frames.tsv'][-1]
  final_fields=('route_state','living_enemy_count','encounter_progress',
                'player_state','player_substate','player_x_fp','player_y_fp',
                'player_z','player_health','camera_x','camera_z','rng')
  executable=(typ,cls) in implementation_contracts
  contract=implementation_contracts.get((typ,cls))
  components.append({
      'type':typ,'class':cls,
      'classification':('SOURCE_CLOSED_IMPLEMENTATION_FIELDS' if executable
                        else 'SOURCE_CLOSED_IDENTITY'),
      'semantic_role':(contract['semantic_role'] if executable else 'UNKNOWN'),
      'dispatch_entry':f'0x{routine:06x}',
      'dispatch_prefix_sha256':hashlib.sha256(op[routine:routine+64]).hexdigest(),
      'source_scheduler':('0x01bc38' if typ==20 else
                          '0x01ba62' if typ==24 else '0x01bcda'),
      'lifetime_count':SCENE_COMPONENT_LIFETIMES[pair],
      'first_frame':min(int(r['frame']) for r in actor_rows),
      'last_frame':max(int(r['frame']) for r in actor_rows),
      'state_substate_contexts':sorted({
          f"0x{int(r['state'],16):04x}:0x{int(r['substate'],16):04x}"
          for r in actor_rows}),
      'animation_records':sorted({
          f"0x{int(r['animation_record'],16):08x}" for r in actor_rows}),
      'suppression_control':{
          'capture':mutant_path.name,'removed_lifetimes':len(suppression),
          'first_removed':suppression[0],
          'downstream_differences':differences,
          'final_projection_unchanged':all(
              last_base[field]==last_mutant[field] for field in final_fields),
          'downstream_window_complete':not (typ==24 and cls=='0x05')},
      'implementation_status':('SPEC_EXECUTABLE' if executable else
                               'BLOCKED_MISSING_SPEC_FIELDS'),
      'implementation_contract':contract,
      'fixed_frame_substitute_forbidden':True})
 return {'classification':'SOURCE_CLOSED_IDENTITY',
   'capture_identity':{'completion_a':identity_a,'completion_b':identity_b,
                       'byte_identical':True,
                       'implementation_detail_a':detail_identity_a,
                       'implementation_detail_b':detail_identity_b,
                       'implementation_detail_byte_identical':True},
   'components':components,'identified_pairs':len(components),
   'unidentified_pairs':0,'semantic_names_inferred':False}

def first_segment_dependencies(ss,ee,ww,rr,op,program):
 global CLASS4E_TERMINAL_TRANSITION
 player_authority=json.loads(PLAYER.read_text(encoding='ascii'))
 player_special=player_authority['special_implementation_contract']
 class09_slots=('ffb480','ffb500');initial=[]
 for slot,x in zip(class09_slots,(992,940)):
  observed=next((r for r in ss if r['slot']==slot and r['class']=='09' and int(r['frame'])==2073),None)
  req(observed is not None and int(observed['type'])==20 and int(observed['state'])==512 and int(observed['phase'])==0 and int(observed['x'])==x and int(observed['y'])==240 and int(observed['z'])==240 and int(observed['anim'],16)==0x6dbda,'class-0x09 first-segment initialization drift')
  initial.append({'source_slot':f'0x00ff{slot[2:]}','x_s16':x,'y_s16':240,'z_s16':240,'state_u16':0x0200,'substate_u16':0,'facing_u8':0,'animation_record':'0x0006dbda'})
 class09_rng=[r for r in rr if r['class']=='09' and int(r['frame'])<=2244]
 req(len(class09_rng)==44 and class09_rng[0]['seed']=='44fb' and class09_rng[-1]['seed']=='99e8','class-0x09 first-segment RNG cadence drift')
 selector_starts=(0x6dbda,0x6dbfe,0x6dc22,0x6dc46,0x6dc6a)
 class09_sequences=[{'selector_u8':selector,'terminal_rule':'negative branch is consumed by state 0x0200 before generic animation update','records':[animation_record(program,start),animation_record(program,start+16)]} for selector,start in zip((0,7,8,9,10),selector_starts)]
 class09_scene_file='coffee_shop_scene_actors.tsv'
 class09_rng_file='coffee_shop_rng_calls.tsv'
 req(sha(SCENE_COMPONENT_A/class09_scene_file)==
     sha(SCENE_COMPONENT_B/class09_scene_file),
     'class-0x09 complete-scene actor capture identity drift')
 req(sha(SCENE_COMPONENT_A/class09_rng_file)==
     sha(SCENE_COMPONENT_B/class09_rng_file),
     'class-0x09 complete-scene RNG capture identity drift')
 class09_scene=[r for r in rows(SCENE_COMPONENT_A/class09_scene_file)
                if r['class']=='09' and int(r['type'])==20]
 class09_scene_rng=[r for r in rows(SCENE_COMPONENT_A/class09_rng_file)
                    if r['class']=='09' and int(r['type'])==20]
 class09_record_addresses=sorted({int(r['animation_record'],16)
                                  for r in class09_scene})
 req(len(class09_scene)==6956 and
     [int(class09_scene[0]['frame']),int(class09_scene[-1]['frame'])]==
      [2073,5550] and
     sorted({(r['state'],r['substate']) for r in class09_scene})==
      [('0200','0000')] and
     class09_record_addresses==sorted(
      start+offset for start in selector_starts for offset in (0,16)),
     'class-0x09 complete-scene state/presentation coverage drift')
 req(len(class09_scene_rng)==898 and
     [int(class09_scene_rng[0]['frame']),
      int(class09_scene_rng[-1]['frame'])]==[2079,5522],
     'class-0x09 complete-scene RNG coverage drift')
 class09_5493=[r for r in class09_scene if int(r['frame'])==5493]
 class09_5494=[r for r in class09_scene if int(r['frame'])==5494]
 req([(r['slot'],int(r['animation_record'],16),
       int(r['animation_timer'],16),int(r['animation_branch']))
      for r in class09_5493]==[
       ('ffb480',0x6dbda,0,0),('ffb500',0x6dc6a,1,0)] and
     [(r['slot'],int(r['animation_record'],16),
       int(r['animation_timer'],16),int(r['animation_branch']))
      for r in class09_5494]==[
       ('ffb480',0x6dc22,5,0),('ffb500',0x6dc22,5,0)],
     'class-0x09 exit presentation witness drift')
 class09_complete_program={
  'classification':'SOURCE_CLOSED_IMPLEMENTATION_FIELDS',
  'source_frame_range_u16':[2073,5550],
  'source_slots':['0x00ffb480','0x00ffb500'],
  'reachable_state_substate_u16':['0x0200:0x0000'],
  'source_row_count_u16':len(class09_scene),
  'source_rng_call_count_u16':len(class09_scene_rng),
  'source_rng_frame_range_u16':[2079,5522],
  'scheduler_order':'record-type-20 ascending source slot; display boundary may fall between pool records',
  'state_dispatch':{
   'entry':'0x06d926','table_address':'0x06d932',
   'state_0_target':'0x06d93a','state_0x0200_target':'0x06d96e',
   'source_body_sha256':hashlib.sha256(op[0x6d926:0x6d9a4]).hexdigest()},
  'state_0':{
   'writes':['state += 0x0200','table_set = 0x0006de6c',
    'object_or_u16 = 0x8000','actor+0x64:u8 = 0x1a',
    'z_s16 = y_s16','actor+0x40:u16 = 0','actor+0x42:u16 = 0'],
   'animation_selector_u8':0,'animation_table':'0x0006dbc2',
   'animation_bind_entry':'0x016518',
   'source_body':{'first':'0x06d93a','last_exclusive':'0x06d96e',
    'sha256':hashlib.sha256(op[0x6d93a:0x6d96e]).hexdigest()}},
  'state_0x0200':{
   'terminal_guard':'signed actor+0x24 animation branch is negative',
   'terminal_order':['consume one RNG call at 0x017c5e',
    'mask result with 0x000e','read u16 selector at 0x06d9a4 + masked offset',
    'bind selected sequence through 0x016518',
    'advance generic animation through 0x016536'],
   'nonterminal_order':['advance generic animation through 0x016536'],
   'post_animation_calls':['0x01d87a','0x06b2e2','0x0167ac'],
   'movement_result':'x/y/z unchanged across every Coffee Shop-reachable branch',
   'collision_damage_result':'no direct collision or damage writes',
   'source_body':{'first':'0x06d96e','last_exclusive':'0x06d9a4',
    'sha256':hashlib.sha256(op[0x6d96e:0x6d9a4]).hexdigest()},
   'animation_update_body':{'first':'0x016536','last_exclusive':'0x01656e',
    'sha256':hashlib.sha256(op[0x16536:0x1656e]).hexdigest()}},
  'selector_table_u16':[0,7,8,9,10,8,9,10],
  'animation_sequences':class09_sequences,
  'animation_record_count_u8':len(class09_record_addresses),
  'exit_presentation_witness':{
   'frame_5493':[{'source_slot':'0x00ffb480','animation_record':'0x0006dbda','timer_u16':0,'branch_s16':0},
                 {'source_slot':'0x00ffb500','animation_record':'0x0006dc6a','timer_u16':1,'branch_s16':0}],
   'frame_5494':[{'source_slot':'0x00ffb480','animation_record':'0x0006dc22','timer_u16':5,'branch_s16':0},
                 {'source_slot':'0x00ffb500','animation_record':'0x0006dc22','timer_u16':5,'branch_s16':0}]},
  'capture_identity':{
   'actors_sha256':sha(SCENE_COMPONENT_A/class09_scene_file),
   'rng_sha256':sha(SCENE_COMPONENT_A/class09_rng_file)},
  'mutation_controls':['state dispatch','terminal guard','RNG count/order',
   'selector mask/table','animation bind/update order','record identity',
   'scheduler slot order','frame-5493 presentation witness'],
  'fixed_frame_substitute_forbidden':True,
  'retained_gameplay_authority':False}
 spawn_rows=[r for r in ww if r['pc']=='060e84' and r['class']=='4e' and int(r['frame'])==2249]
 req([(r['slot'],r['data']) for r in spawn_rows]==[('ffc500','00000404'),('ffc480','00000404')],'class-0x4e initial allocation order drift')
 class4e_rng=[r for r in rr if r['class']=='4e' and int(r['frame'])==2249]
 req([(r['slot'],r['seed']) for r in class4e_rng]==[('ffc480','cdb5'),('ffc500','691e')],'class-0x4e scheduler/RNG order drift')
 class4e_records=[animation_record(program,0x929b0+16*i) for i in range(5)]
 class4e_scene_rows=rows(SCENE_COMPONENT_A/'coffee_shop_scene_actors.tsv')
 reachable_variant_programs={}
 for variant,addresses,owner in (
  (5,range(0x92a04,0x92a45,0x10),'player-melee-current-collision'),
  (20,range(0x935b0,0x93621,0x10),'type16-class06-current-collision')):
  actor_rows=[r for r in class4e_scene_rows if r['class']=='4e' and
              int(r['variant'],16)==variant]
  lifetimes=[];active={}
  for row in actor_rows:
   frame=int(row['frame']);slot=row['slot'];prior=active.get(slot)
   if prior is None or frame!=prior['last_visible_frame_u16']+1:
    prior={'source_slot':f"0x00ff{slot[2:]}",
           'first_visible_frame_u16':frame,'last_visible_frame_u16':frame}
    lifetimes.append(prior);active[slot]=prior
   else:prior['last_visible_frame_u16']=frame
  req(len(lifetimes)==(1 if variant==5 else 2),
      f'class-0x4e variant-{variant} lifetime count drift')
  allocations=[]
  for lifetime in lifetimes:
   frame=lifetime['first_visible_frame_u16'];slot=lifetime['source_slot'][-6:]
   state0=next(r for r in actor_rows if int(r['frame'])==frame and
               r['slot']==slot)
   active_row=next(r for r in actor_rows if int(r['frame'])==frame+1 and
                   r['slot']==slot)
   writes=[r for r in ww if r['class']=='4e' and r['slot']==slot and
           int(r['frame'])==frame-1]
   rng=next(r for r in rr if r['class']=='4e' and r['slot']==slot and
            int(r['frame'])==frame)
   req([(r['pc'],r['offset']) for r in writes[:6]]==[
       ('01d64e','02'),('01d654','0e'),('01d6c4','10'),
       ('01d6d6','14'),('01d6dc','18'),('01d6e2','18')],
       f'class-0x4e variant-{variant} allocation writer drift')
   allocations.append({
    'source_slot':lifetime['source_slot'],'allocation_frame_u16':frame-1,
    'visible_frame_u16':frame,'owner_source_slot':f"0x00{writes[0]['a6']}",
    'position_before_rng_s16':[int(state0['x_fp'],16)>>16,
                               int(state0['y_fp'],16)>>16,int(state0['z'])],
    'position_after_rng_s16':[int(active_row['x_fp'],16)>>16,
                              int(active_row['y_fp'],16)>>16,
                              int(active_row['z'])],
    'facing_u8':int(state0['facing']),
    'seed_before':f"0x{int(rng['seed'],16):04x}",
    'seed_after':f"0x{next_seed(int(rng['seed'],16)):04x}",
    'table_offset_u8':next_seed(int(rng['seed'],16))&0x1c})
  reachable_variant_programs[str(variant)]={
   'classification':'SOURCE_CLOSED_IMPLEMENTATION_FIELDS',
   'variant_u8':variant,'owner':owner,'dispatch':'0x0927f6',
   'allocation_writer':'0x01d64e','allocation_routine':'0x0177da',
   'release_routine':'0x0177f0','rng_entry':'0x017c5e',
   'rng_call_pc':'0x09282a','rng_mask_u16':'0x001c',
   'state_sequence_u16':[0,0x0200,0x0400],
   'state0_writes':{'coordinate_mode_u8':2,'object_or_u16':'0x8000'},
   'animation_records':[animation_record(program,address)
                        for address in addresses],
   'lifetimes':lifetimes,'allocations':allocations,
   'terminal_guard':'decrement the current animation timer, then signed negative branch writes state 0x0400; release on the next scheduler visit',
   'scheduler_rule':'collision allocation occurs after the type-24 pool; state-0 initialization and RNG occur on the next source frame',
   'mutation_controls':['variant','owner','allocation scheduler phase',
    'RNG order','jitter','animation record','terminal order','release'],
   'fixed_frame_substitute_forbidden':True}
 req({int(r['variant'],16) for r in class4e_scene_rows
      if r['class']=='4e'}=={0,1,4,5,10,20},
     'Coffee Shop class-0x4e reachable variant census drift')
 class4e_scene_rows=rows(SCENE_COMPONENT_A/'coffee_shop_scene_actors.tsv')
 class4e_terminal_rows=[r for r in class4e_scene_rows if
                        r['slot'] in ('ffc480','ffc500') and
                        r['class']=='4e' and
                        int(r['frame']) in (2258,2259)]
 req([(int(r['frame']),r['slot'],r['state'],
       r['animation_record'],r['animation_timer'],
       int(r['animation_branch'])) for r in class4e_terminal_rows]==[
      (2258,'ffc480','0200','000929f0','0fff',-32768),
      (2258,'ffc500','0200','000929f0','0fff',-32768),
      (2259,'ffc480','0400','000929f0','0ffe',-32768),
      (2259,'ffc500','0400','000929f0','0ffe',-32768)],
     'class-0x4e terminal timer/state ordering drift')
 class4e_terminal_transition={
  'classification':'SOURCE_CLOSED_IMPLEMENTATION_FIELDS',
  'state_guard':'state_u16 == 0x0200 and signed actor+0x24 < 0',
  'timer_rule':'decrement actor+0x0a_u16 once before writing state 0x0400',
  'source_slots':['0x00ffc480','0x00ffc500'],
  'before':{'visible_frame_u16':2258,'state_u16':'0x0200',
            'animation_record':'0x000929f0','timer_u16':4095,
            'branch_s16':-32768},
  'after':{'visible_frame_u16':2259,'state_u16':'0x0400',
           'animation_record':'0x000929f0','timer_u16':4094,
           'branch_s16':-32768},
  'scheduler_rule':'each active source slot consumes the same terminal update in ascending slot order',
  'mutation_control':'reject state advance before terminal timer decrement',
  'capture_sha256':sha(SCENE_COMPONENT_A/'coffee_shop_scene_actors.tsv')}
 CLASS4E_TERMINAL_TRANSITION=class4e_terminal_transition
 impact_writes=[r for r in ww if r['class']=='4e' and
                r['slot']=='ffbd80' and int(r['frame']) in (2306,2307)]
 req([(r['pc'],r['offset'],r['data']) for r in impact_writes[:6]]==[
      ('01d64e','02','00000101'),('01d654','0e','00000000'),
      ('01d6c4','10','000002cd'),('01d6d6','14','00000150'),
      ('01d6dc','18','00000136'),('01d6e2','18','00000135')],
     'class-0x4e variant-1 collision allocation writes drift')
 impact_entry=next((r for r in ee if r['class']=='4e' and
                    r['slot']=='ffbd80' and int(r['frame'])==2307),None)
 impact_rng=next((r for r in rr if r['class']=='4e' and
                  r['slot']=='ffbd80' and int(r['frame'])==2307),None)
 req(impact_entry is not None and impact_entry['state']=='0' and
     impact_entry['phase']=='0' and impact_entry['x']=='717' and
     impact_entry['z']=='309' and impact_entry['anim']=='0008df2c',
     'class-0x4e variant-1 entry context drift')
 req(impact_rng is not None and impact_rng['pc']=='092830' and
     impact_rng['seed']=='19c4','class-0x4e variant-1 RNG context drift')
 scene_actors=rows(SCENE_COMPONENT_A/'coffee_shop_scene_actors.tsv')
 scene_health=rows(SCENE_COMPONENT_A/'coffee_shop_scene_health_writes.tsv')
 prior_impact_owner=next((r for r in scene_actors if r['slot']=='ffbd80' and
                          int(r['frame'])==2306),None)
 allocated_impact=next((r for r in scene_actors if r['slot']=='ffbd80' and
                        int(r['frame'])==2307),None)
 initialized_impact=next((r for r in scene_actors if r['slot']=='ffbd80' and
                          int(r['frame'])==2308),None)
 req(prior_impact_owner is not None and allocated_impact is not None and
     initialized_impact is not None and
     prior_impact_owner['class']=='45' and
     prior_impact_owner['animation_record']=='0008df2c' and
     prior_impact_owner['animation_timer']=='0fcd' and
     prior_impact_owner['animation_branch']=='-32768' and
     allocated_impact['class']=='4e' and
     allocated_impact['state']=='0000' and
     allocated_impact['animation_record']=='0008df2c' and
     allocated_impact['animation_timer']=='0fcd' and
     allocated_impact['animation_branch']=='-32768' and
     initialized_impact['state']=='0200' and
     initialized_impact['animation_record']=='00092914' and
     initialized_impact['animation_timer']=='0004',
     'class-0x4e fixed-slot retained presentation chronology drift')
 impact_health=next((r for r in scene_health if int(r['frame'])==2306 and
                     r['attacker']=='ff8880' and r['defender']=='ffa180'),None)
 req(impact_health is not None and impact_health['pc']=='01d590' and
     impact_health['attack_record']=='030cd2' and
     impact_health['health_before']=='0057' and
     impact_health['health_after']=='0038' and
     impact_health['damage_writer']=='1',
     'class-0x4e variant-1 collision/damage owner drift')
 variant1_rows=[r for r in scene_actors if r['pool']=='record24' and
                r['class']=='4e' and r['variant']=='01']
 variant1_lifetimes=[];active_variant1={}
 for row in variant1_rows:
  frame=int(row['frame']);slot=row['slot'];prior=active_variant1.get(slot)
  if prior is None or frame!=prior['last_frame']+1:
   prior={'source_slot':f"0x00ff{slot[2:]}",'first_frame':frame,
          'last_frame':frame}
   variant1_lifetimes.append(prior);active_variant1[slot]=prior
  else:prior['last_frame']=frame
 req(len(variant1_lifetimes)==23 and len(variant1_rows)==253 and
     variant1_lifetimes[0]=={'source_slot':'0x00ffbd80',
      'first_frame':2307,'last_frame':2317},
     'class-0x4e variant-1 Coffee Shop lifetimes drift')
 class4e_variant1_records=[animation_record(program,address) for address in
                            (0x92914,0x92924,0x92934)]
 detail_scene_actors=rows(
      SCENE_COMPONENT_DETAIL_A/'coffee_shop_scene_actors.tsv')
 detail_scene_health=rows(
      SCENE_COMPONENT_DETAIL_A/'coffee_shop_scene_health_writes.tsv')
 detail_scene_health_b=rows(
      SCENE_COMPONENT_DETAIL_B/'coffee_shop_scene_health_writes.tsv')
 req(detail_scene_health==detail_scene_health_b,
      'player-special multi-target health captures differ')
 special_health=[r for r in detail_scene_health if int(r['frame'])==2804]
 req([(r['target_pool'],r['target_slot'],r['pc'],r['attacker'],
        r['attack_record'],r['health_before'],r['health_after'])
       for r in special_health]==[
        ('record12','ffa240','01d590','ff8380','11af76','0057','ffd8'),
        ('record12','ffa240','01d598','ff8380','11af76','ffd8','ffff'),
        ('record20','ffb300','01d590','ff8380','11af76','0000','ffe7'),
        ('record20','ffb300','01d598','ff8380','11af76','ffe7','ffff'),
        ('record20','ffb380','01d590','ff8380','11af76','0000','ffe7'),
        ('record20','ffb380','01d598','ff8380','11af76','ffe7','ffff')],
      'player-special multi-target write order drift')
 later_class1f_multi=[r for r in scene_health
                      if int(r['frame']) in (4394,4395) and
                      r['target_pool']=='record12' and
                      r['attack_record']=='11af76']
 req([(int(r['frame']),r['target_slot'],r['pc'])
      for r in later_class1f_multi]==[
       (4394,'ff9c40','01d590'),(4394,'ff9c40','01d598'),
       (4395,'ff9e80','01d590'),(4395,'ff9e80','01d598')],
     'player-special class-0x1f traversal cadence drift')
 special_source={r['slot']:r for r in detail_scene_actors
                  if int(r['frame'])==2804 and r['slot'] in
                  {'ff8380','ffa240','ffb300','ffb380'}}
 special_impacts={r['slot']:r for r in detail_scene_actors
                   if int(r['frame'])==2805 and r['pool']=='record24' and
                   r['class']=='4e' and r['variant']=='01' and
                   r['slot'] in {'ffbf00','ffb900','ffb680'}}
 special_ko_rows=[r for r in detail_scene_actors
                  if r['slot']=='ffa240' and 2805<=int(r['frame'])<=2916]
 req(set(special_source)=={'ff8380','ffa240','ffb300','ffb380'} and
      set(special_impacts)=={'ffbf00','ffb900','ffb680'} and
      [(slot,int(special_impacts[slot]['x_fp'],16)>>16,
        int(special_impacts[slot]['y_fp'],16)>>16,
        int(special_impacts[slot]['z']),
        int(special_impacts[slot]['facing'])) for slot in
       ('ffbf00','ffb900','ffb680')]==[
        ('ffbf00',1083,354,308,0),
        ('ffb900',1125,390,335,1),
        ('ffb680',1107,379,322,1)],
      'player-special class-0x4e allocation result drift')
 special_ko_by_frame={int(r['frame']):r for r in special_ko_rows}
 req([(frame,special_ko_by_frame[frame]['active'],
       special_ko_by_frame[frame]['state'],
       special_ko_by_frame[frame]['substate'],
       special_ko_by_frame[frame]['animation_record'],
       int(special_ko_by_frame[frame]['animation_timer'],16))
      for frame in (2805,2806,2809,2810,2842,2845,2856,2916)]==[
       (2805,'1','0400','0000','0012d890',7),
       (2806,'2','0402','0000','0012e214',1),
       (2809,'2','0402','0000','0012e214',1),
       (2810,'2','0402','0200','0012e224',2),
       (2842,'2','0402','0400','0012e268',4095),
       (2845,'2','0402','0600','0012e254',4094),
       (2856,'2','0404','0000','0012e268',4095),
       (2916,'2','0600','0000','0012e268',4095)],
      'player-special class-0x1f lethal reaction chronology drift')
 special_ko_records=[animation_record(program,address) for address in
                     (0x12e214,0x12e224,0x12e234,0x12e244)]
 special_ko_falling=animation_record(program,0x12e254)
 special_ko_landing=animation_record(program,0x12e268)
 req([(r['timer_u16'],r['branch_s16']) for r in special_ko_records]==
      [(1,0),(2,34),(5,35),(7,36)] and
      (special_ko_falling['timer_u16'],special_ko_falling['branch_s16'])==
      (4095,-32744) and
      (special_ko_landing['timer_u16'],special_ko_landing['branch_s16'])==
      (4095,-32743),
      'player-special class-0x1f lethal reaction records drift')
 special_attack=attack_box(program[0x11af76:0x11af86],0x11af76)
 special_class1f_hurt=hurt_box(program[0x130ad4:0x130adc],0x130ad4)
 req(special_attack['x_center_s8']==0 and
      special_attack['y_center_s8']==48 and
      special_attack['x_half_u8']==88 and
      special_attack['y_half_u8']==48 and
      special_attack['z_center_s8']==0 and
      special_attack['z_half_u8']==40 and
      special_attack['impact_variant_u8']==1 and
      special_attack['knockback_mode_s8']==3 and
      special_attack['hit_value_u8']==3 and
      special_class1f_hurt['x_center_s8']==-12 and
      special_class1f_hurt['y_center_s8']==42 and
      special_class1f_hurt['x_half_u8']==29 and
      special_class1f_hurt['y_half_u8']==39 and
      special_class1f_hurt['z_center_s8']==0 and
      special_class1f_hurt['z_half_u8']==8,
      'player-special class-0x1f collision records drift')
 special_collision_attack={
  'address':special_attack['address'],
  'x_center_s8':special_attack['x_center_s8'],
  'y_center_s8':special_attack['y_center_s8'],
  'x_half_u8':special_attack['x_half_u8'],
  'y_half_u8':special_attack['y_half_u8'],
  'z_center_s8':special_attack['z_center_s8'],
  'z_half_u8':special_attack['z_half_u8'],
  'knockback_mode_s8':special_attack['impact_variant_u8'],
  'hit_value_u8':special_attack['hit_value_u8'],
  'record_sha256':special_attack['record_sha256']}
 player_special_collision={
   'classification':'SOURCE_CLOSED_IMPLEMENTATION_FIELDS',
   'source_frame_u16':2804,
   'player_state_substate':'0x0200:0x0802',
   'registration_guard':('source player animation advances from 0x0015fd40 '
       'to attack-selector-11 record 0x0015fd50 before the current-state '
       'collision traversal'),
   'attack_selector_u8':11,'attack_record':special_collision_attack,
   'class1f_target':{
    'source_slot':'0x00ffa240','state_substate':'0x0200:0x0402',
    'animation_record':'0x0012d890','table_set':'0x00130ac8',
    'hurt_selector_u8':1,'hurt_record':special_class1f_hurt,
   'health_before_s16':87,'damage_s16':127,
    'health_after_damage_s16':-40,'health_after_clamp_s16':-1,
    'damage_writer':'0x01d590','clamp_writer':'0x01d598',
    'reaction_writer':'0x01d4aa','reaction_state_substate':'0x0400:0x0000',
    'impact_source_slot':'0x00ffbf00','impact_visible_frame_u16':2805,
    'impact_spawn_position_s16':[1083,354,308],
    'impact_facing_u8':0,
    'source_ko':{
     'collision_state_substate':'0x0400:0x0000',
     'dispatch_visible_frame_u16':2806,'dispatch_active_u8':2,
     'dispatch_state_substate':'0x0402:0x0000',
     'entry_hold_ticks_u8':3,'motion_first_frame_u16':2810,
     'action_phases_u16':[0x0000,0x0200,0x0400,0x0600],
     'reaction_records':special_ko_records,
     'falling_record':special_ko_falling,
     'landing_record':special_ko_landing,
     'selector_rule':'retain pre-collision hurt=1 and attack=1 selectors',
     'hurt_selector_u8':1,'attack_selector_u8':1,
     'launch_x_velocity_before_facing_16_16':0x0003a000,
     'launch_x_acceleration_16_16':0,
     'launch_y_velocity_16_16':0x000c0000,
     'launch_y_acceleration_16_16':-0x0000c000,
     'landing_hold_ticks_u8':3,
     'bounce_x_velocity_before_facing_16_16':0x00020000,
     'bounce_x_acceleration_16_16':0,
     'bounce_y_velocity_16_16':0x00040000,
     'bounce_y_acceleration_16_16':-0x0000c000,
     'hold_state_substate':'0x0404:0x0000',
     'removal_hold_ticks_u8':60,
     'release_state_substate':'0x0600:0x0000',
     'movement_rule':('apply x/y 16.16 velocity then acceleration each '
         'scheduler visit; negate x terms when reaction-facing selector is 0; '
         'clamp y high word to z while retaining the source fractional word'),
     'capture_range_u16':[2805,2916]}},
   'record20_targets':[
    {'source_slot':'0x00ffb300','class_u8':'0x02','damage_s16':25,
     'impact_source_slot':'0x00ffb900',
     'impact_spawn_position_s16':[1125,390,335],
     'impact_facing_u8':1},
    {'source_slot':'0x00ffb380','class_u8':'0x0a','damage_s16':25,
     'impact_source_slot':'0x00ffb680',
     'impact_spawn_position_s16':[1107,379,322],
     'impact_facing_u8':1}],
   'scheduler_order':[
    'record-type-24 dispatch/release completes before collision allocation',
    'the source player attack registration traverses record-type-12 targets',
    'the same registration then traverses record-type-20 targets'],
   'multi_target_rule':('one active player attack registration may damage '
       'every overlapping target in source pool order; the first contact '
       'must not consume the registration'),
   'class1f_traversal_cadence':{
    'max_damage_targets_per_frame_u8':1,
    'registration_retained_after_contact':True,
    'next_frame_resumes_after_ineligible_prior_targets':True,
    'coffee_shop_witnesses':[
     {'source_frame_u16':4394,'source_slot':'0x00ff9c40'},
     {'source_frame_u16':4395,'source_slot':'0x00ff9e80'}]},
   'impact_allocation':{
    'entry':'0x01d116','allocator':'0x01d622','pool_allocator':'0x0177da',
    'record_type_u8':24,'class_u8':'0x4e','variant_u8':1,
    'variant_rule':'absolute signed attack-record knockback_mode_s8',
    'position_rule':('signed midpoint of attack and hurt centres after depth '
                     'projection; z is defender z_s16 - 1'),
    'facing_rule':'copy defender reaction-facing actor+0x4f_u8',
    'allocation_failure_rule':'damage remains applied; omit only the impact'},
   'capture_identity':{
    'completion_a':sha(
        SCENE_COMPONENT_DETAIL_A/'coffee_shop_scene_health_writes.tsv'),
    'completion_b':sha(
        SCENE_COMPONENT_DETAIL_B/'coffee_shop_scene_health_writes.tsv'),
    'byte_identical':True},
   'mutation_controls':[
    'reject first-target consumption of the active player registration',
    'reject record-type-20 before record-type-12 target traversal',
    'reject damage before the attack-selector-11 registration',
    'reject impact initialization during the already-completed record-type-24 pass',
    'reject class-0x1f damage other than 127 or signed clamp other than -1',
    'reject player hitstop other than attack-record hit_value 3 or rearming it per target',
    'reject the projectile KO program in place of the source 0x0012e214 lethal reaction']}
 class4e_variant1={
  'classification':'SOURCE_CLOSED_IMPLEMENTATION_FIELDS',
  'scene_lifetime_count_u16':len(variant1_lifetimes),
  'scene_actor_rows_u16':len(variant1_rows),'lifetimes':variant1_lifetimes,
  'first_collision':{'source_frame':2306,'attacker_source_slot':'0x00ff8880',
   'attacker_record_type_u8':4,'attacker_class_u8':'0x04',
   'attacker_attack_record':'0x00030cd2','attacker_attack_selector_u8':14,
   'defender_source_slot':'0x00ffa180','defender_record_type_u8':12,
   'defender_class_u8':'0x1f','defender_state_substate':'0x0200:0x1600',
   'damage_writer':'0x01d590','health_before_s16':87,
   'health_after_s16':56,'damage_s16':31},
  'allocation':{'collision_entry':'0x01d116','impact_allocator':'0x01d622',
   'pool_allocator':'0x0177da','global_suppression_guard':'u8(0xff8244) == 0',
   'scheduler_guard':'record-type-24 release/dispatch at 0x01ba62 precedes record-type-4 collision scheduler at 0x01cbcc',
   'source_slot':'0x00ffbd80','record_type_u8':24,'class_u8':'0x4e',
   'variant_rule':'absolute signed attack-record knockback_mode_s8',
   'variant_u8':1,'facing_rule':'copy defender reaction-facing actor+0x4f_u8',
   'x_rule':'signed midpoint of attacker attack-box center and defender hurt-box center',
   'y_rule':'signed midpoint of depth-projected attacker attack-box center and defender hurt-box center',
   'z_rule':'defender z_s16 - 1','first_spawn_position_s16':[717,336,309],
   'allocation_failure_rule':'damage remains applied; omit only the impact actor',
   'visible_frame_u16':2307,
   'fixed_slot_reuse_presentation':{
    'prior_visible_frame_u16':2306,'prior_class_u8':'0x45',
    'allocation_visible_frame_u16':2307,'allocated_class_u8':'0x4e',
    'rule':'0x0177da pops the released fixed slot without clearing fields not written by 0x01d622; retain the prior presentation until class-0x4e state 0 runs on its next scheduler visit',
    'retained_fields':['animation_record','animation_timer','animation_branch'],
    'animation_record':'0x0008df2c','assembly':'0x0008df96',
    'animation_timer_u16':4045,'animation_branch_s16':-32768,
    'state0_scheduler_frame_u16':2307,
    'state0_visible_frame_u16':2308,
    'state0_animation_record':'0x00092914',
    'state0_assembly':'0x00092c04'}},
  'state0':{'state_write_u16':'0x0200','coordinate_mode_u8':2,
   'object_or_u16':'0x8000','rng_entry':'0x017c5e','rng_calls_u8':1,
   'rng_mask_u16':'0x001c','first_seed_before':'0x19c4',
   'first_seed_after':'0x4d11','first_jitter_s16':[-4,0],
   'jitter_table_s16':[[0,0],[4,0],[4,-4],[4,4],[-4,0],[-4,-4],[-4,4],[-8,8]],
   'first_visible_position_after_state0_s16':[713,336,309]},
  'active_state':{'state_u16':'0x0200','animation_records':class4e_variant1_records,
   'terminal_guard':'signed animation branch actor+0x24 < 0 advances state to 0x0400',
   'movement_result':'x/y/z unchanged after state-0 jitter'},
   'player_special_collision':player_special_collision,
   'release_state':{'state_u16':'0x0400','release_routine':'0x0177f0',
   'first_last_visible_frame':2317,'first_absent_frame':2318},
  'source_bodies':{'collision_impact':{'first':'0x01d622',
    'last_exclusive':'0x01d6b2','sha256':hashlib.sha256(op[0x1d622:0x1d6b2]).hexdigest()},
   'class_dispatch':{'first':'0x0927f6','last_exclusive':'0x0928aa',
    'sha256':hashlib.sha256(op[0x927f6:0x928aa]).hexdigest()}},
  'capture_identity':{
   'scene_actors_sha256':sha(SCENE_COMPONENT_A/'coffee_shop_scene_actors.tsv'),
   'scene_health_sha256':sha(SCENE_COMPONENT_A/'coffee_shop_scene_health_writes.tsv')},
  'collision_damage_authority':'shared collision writer; this actor is presentation-only',
  'rng_authority':'shared source RNG consumed by class-0x4e state 0',
 'fixed_frame_substitute_forbidden':True,
 'retained_gameplay_authority':False}
 variant0_rows=[r for r in scene_actors if r['pool']=='record24' and
                r['class']=='4e' and r['variant']=='00']
 variant0_lifetimes=[];active_variant0={}
 for row in variant0_rows:
  frame=int(row['frame']);slot=row['slot'];prior=active_variant0.get(slot)
  if prior is None or frame!=prior['last_frame']+1:
   prior={'source_slot':f"0x00ff{slot[2:]}",'first_frame':frame,
          'last_frame':frame}
   variant0_lifetimes.append(prior);active_variant0[slot]=prior
  else:prior['last_frame']=frame
 req(len(variant0_lifetimes)==2 and len(variant0_rows)==22 and
     variant0_lifetimes[0]=={'source_slot':'0x00ffc300',
      'first_frame':2751,'last_frame':2761},
     'class-0x4e variant-0 Coffee Shop lifetimes drift')
 variant0_writes=[r for r in ww if r['class']=='4e' and
                   r['slot']=='ffc300' and int(r['frame'])==2750]
 req([(r['pc'],r['offset'],r['data']) for r in variant0_writes[:6]]==[
      ('01d64e','02','00000000'),('01d654','0e','00000101'),
      ('01d6c4','10','00000447'),('01d6d6','14','00000171'),
      ('01d6dc','18','00000140'),('01d6e2','18','0000013f')],
     'class-0x4e variant-0 collision allocation writes drift')
 variant0_entry=next((r for r in ee if r['class']=='4e' and
                       r['slot']=='ffc300' and int(r['frame'])==2751),None)
 variant0_rng=next((r for r in rr if r['class']=='4e' and
                     r['slot']=='ffc300' and int(r['frame'])==2751),None)
 variant0_health=next((r for r in scene_health if int(r['frame'])==2750 and
                        r['attacker']=='ffa240' and
                        r['defender']=='ff8380'),None)
 req(variant0_entry is not None and variant0_entry['state']=='0' and
     variant0_entry['x']=='1095' and variant0_entry['z']=='319' and
     variant0_entry['facing']=='1' and
     variant0_entry['anim']=='0007a12c' and
     variant0_rng is not None and variant0_rng['pc']=='092830' and
     variant0_rng['seed']=='eea3' and
     variant0_health is not None and variant0_health['pc']=='01d5ee' and
     variant0_health['attack_record']=='130b5c' and
     variant0_health['health_before']=='0065' and
     variant0_health['health_after']=='005b' and
     variant0_health['damage_writer']=='1',
     'class-0x4e variant-0 causal collision/RNG context drift')
 variant0_initialized=next((r for r in scene_actors if r['slot']=='ffc300' and
                             int(r['frame'])==2752),None)
 req(variant0_initialized is not None and
     variant0_initialized['state']=='0200' and
     variant0_initialized['x_fp']=='044b0000' and
     variant0_initialized['y_fp']=='01750000' and
     variant0_initialized['z']=='319' and
     variant0_initialized['animation_record']=='000928e0' and
     variant0_initialized['animation_timer']=='0004',
     'class-0x4e variant-0 state-0 result drift')
 variant0_records=[animation_record(program,address) for address in
                    (0x928e0,0x928f0,0x92900)]
 req([r['timer_u16'] for r in variant0_records]==[4,4,4095] and
     [r['branch_s16'] for r in variant0_records]==[0,0,-32768],
     'class-0x4e variant-0 presentation sequence drift')
 class4e_variant0={
  'classification':'SOURCE_CLOSED_IMPLEMENTATION_FIELDS',
  'scene_lifetime_count_u16':len(variant0_lifetimes),
  'scene_actor_rows_u16':len(variant0_rows),'lifetimes':variant0_lifetimes,
  'first_collision':{'source_frame':2750,
   'attacker_source_slot':'0x00ffa240','attacker_record_type_u8':12,
   'attacker_class_u8':'0x1f','attacker_attack_record':'0x00130b5c',
   'attacker_attack_selector_u8':1,
   'defender_source_slot':'0x00ff8380','defender_record_type_u8':0,
   'defender_class_u8':'0x00','defender_state_substate':'0x0200:0x0202',
   'defender_hurt_record':'0x0011ae8e','defender_hurt_selector_u8':17,
   'damage_writer':'0x01d5ee','health_before_s16':101,
   'health_after_s16':91,'damage_s16':10,'hitstop_u8':10},
  'allocation':{'collision_entry':'0x01d116',
   'impact_allocator':'0x01d622','pool_allocator':'0x0177da',
   'global_suppression_guard':'u8(0xff8244) == 0',
   'scheduler_guard':'record-type-24 release/dispatch precedes record-type-12 collision scheduler',
   'source_slot':'0x00ffc300','record_type_u8':24,'class_u8':'0x4e',
   'variant_field':{'attack_record_offset_u8':8,'type':'u8',
    'signed':False,'rule':'copy absolute signed byte at attack-record +0x08',
    'raw_u8':0,'variant_u8':0},
   'facing_rule':'copy defender reaction-facing actor+0x4f_u8',
   'x_rule':'signed midpoint of attacker attack-box center and defender hurt-box center',
   'y_rule':'signed midpoint of depth-projected attacker attack-box center and defender hurt-box center',
   'z_rule':'defender z_s16 - 1','first_spawn_position_s16':[1095,369,319],
   'allocation_failure_rule':'damage remains applied; omit only the impact actor',
   'visible_frame_u16':2751,
   'fixed_slot_reuse_presentation':{
    'rule':'0x0177da pops the released fixed slot without clearing fields not written by 0x01d622; retain prior presentation until class-0x4e state 0 runs on its next scheduler visit',
    'retained_fields':['animation_record','animation_timer','animation_branch'],
    'animation_record':'0x0007a12c','assembly':'0x0007a3a0',
    'animation_timer_u16':4094,'animation_branch_s16':-32767,
    'state0_scheduler_frame_u16':2751,'state0_visible_frame_u16':2752,
    'state0_animation_record':'0x000928e0',
    'state0_assembly':'0x00092be8'}},
  'state0':{'state_write_u16':'0x0200','coordinate_mode_u8':2,
   'object_or_u16':'0x8000','rng_entry':'0x017c5e','rng_calls_u8':1,
   'rng_mask_u16':'0x001c','first_seed_before':'0xeea3',
   'first_seed_after':'0xcb6e','first_table_offset_u8':12,
   'first_jitter_s16':[4,4],
   'jitter_table_s16':[[0,0],[4,0],[4,-4],[4,4],[-4,0],[-4,-4],[-4,4],[-8,8]],
   'first_visible_position_after_state0_s16':[1099,373,319]},
  'active_state':{'state_u16':'0x0200',
   'animation_records':variant0_records,
   'terminal_guard':'signed animation branch actor+0x24 < 0 advances state to 0x0400',
   'movement_result':'x/y/z unchanged after state-0 jitter'},
  'release_state':{'state_u16':'0x0400','release_routine':'0x0177f0',
   'first_last_visible_frame':2761,'first_absent_frame':2762},
  'source_bodies':{'collision_impact':{'first':'0x01d622',
    'last_exclusive':'0x01d6b2',
    'sha256':hashlib.sha256(op[0x1d622:0x1d6b2]).hexdigest()},
   'class_dispatch':{'first':'0x0927f6','last_exclusive':'0x0928aa',
    'sha256':hashlib.sha256(op[0x927f6:0x928aa]).hexdigest()}},
  'capture_identity':{
   'scene_actors_sha256':sha(SCENE_COMPONENT_A/'coffee_shop_scene_actors.tsv'),
   'scene_health_sha256':sha(SCENE_COMPONENT_A/'coffee_shop_scene_health_writes.tsv')},
  'collision_damage_authority':'shared collision writer; this actor is presentation-only',
  'rng_authority':'shared source RNG consumed by class-0x4e state 0',
  'fixed_frame_substitute_forbidden':True,
  'retained_gameplay_authority':False}
 global CLASS4E_VARIANT0_CONTRACT
 CLASS4E_VARIANT0_CONTRACT=class4e_variant0
 parent_attack=player_authority['implementation_contract'][
  'record4_parent_class0'][
   'collision_table']['attack_entries'][1]
 req(parent_attack['address']=='0x0002fc58' and
     parent_attack['impact_variant_u8']==10 and
     parent_attack['damage_selector_u8']==25 and
     parent_attack['hit_value_u8']==8,
     'class-0x4e variant-10 owning attack record drift')
 variant10_rows=[r for r in scene_actors if r['pool']=='record24' and
                 r['class']=='4e' and r['variant']=='0a']
 variant10_lifetimes=[];active_variant10={}
 for row in variant10_rows:
  frame=int(row['frame']);slot=row['slot'];prior=active_variant10.get(slot)
  if prior is None or frame!=prior['last_frame']+1:
   prior={'source_slot':f"0x00ff{slot[2:]}",'first_frame':frame,
          'last_frame':frame}
   variant10_lifetimes.append(prior);active_variant10[slot]=prior
  else:prior['last_frame']=frame
 req(len(variant10_lifetimes)==5 and len(variant10_rows)==40 and
     variant10_lifetimes[0]=={'source_slot':'0x00ffc200',
      'first_frame':2363,'last_frame':2370},
     'class-0x4e variant-10 Coffee Shop lifetimes drift')
 variant10_writes=[r for r in ww if r['class']=='4e' and
                   r['slot']=='ffc200' and int(r['frame'])==2362]
 req([(r['pc'],r['offset'],r['data']) for r in variant10_writes[:6]]==[
      ('01d64e','02','00000a0a'),('01d654','0e','00000000'),
      ('01d6c4','10','00000341'),('01d6d6','14','00000145'),
      ('01d6dc','18','00000138'),('01d6e2','18','00000137')],
     'class-0x4e variant-10 collision allocation writes drift')
 variant10_entry=next((r for r in ee if r['class']=='4e' and
                       r['slot']=='ffc200' and int(r['frame'])==2363),None)
 variant10_rng=next((r for r in rr if r['class']=='4e' and
                     r['slot']=='ffc200' and int(r['frame'])==2363),None)
 variant10_health=next((r for r in scene_health if int(r['frame'])==2362 and
                        r['attacker']=='ff8880' and
                        r['defender']=='ffa3c0'),None)
 req(variant10_entry is not None and variant10_entry['state']=='0' and
     variant10_entry['x']=='833' and variant10_entry['z']=='311' and
     variant10_entry['anim']=='0008def0' and
     variant10_rng is not None and variant10_rng['pc']=='092830' and
     variant10_rng['seed']=='37cd' and
     variant10_health is not None and variant10_health['pc']=='01d590' and
     variant10_health['attack_record']=='02fc58' and
     variant10_health['health_before']=='0057' and
     variant10_health['health_after']=='ffd8',
     'class-0x4e variant-10 causal collision/RNG context drift')
 variant10_records=[animation_record(program,0x92e50+16*i)
                    for i in range(6)]
 req([r['timer_u16'] for r in variant10_records]==[1,1,1,1,1,4095] and
     [r['branch_s16'] for r in variant10_records]==[0,0,0,0,0,-32768],
     'class-0x4e variant-10 presentation sequence drift')
 req(sha(SCENE_COMPONENT_A/'coffee_shop_scene_actors.tsv')==
     sha(SCENE_COMPONENT_B/'coffee_shop_scene_actors.tsv') and
     sha(SCENE_COMPONENT_A/'coffee_shop_scene_health_writes.tsv')==
     sha(SCENE_COMPONENT_B/'coffee_shop_scene_health_writes.tsv'),
     'class-0x4e variant-10 independent completion drift')
 class4e_variant10={
  'classification':'SOURCE_CLOSED_IMPLEMENTATION_FIELDS',
  'scene_lifetime_count_u16':len(variant10_lifetimes),
  'scene_actor_rows_u16':len(variant10_rows),'lifetimes':variant10_lifetimes,
  'first_collision':{'source_frame':2362,
   'attacker_source_slot':'0x00ff8880','attacker_record_type_u8':4,
   'attacker_class_u8':'0x00','attacker_attack_record':'0x0002fc58',
   'attacker_attack_selector_u8':25,
   'defender_source_slot':'0x00ffa3c0','defender_record_type_u8':12,
   'defender_class_u8':'0x1f','defender_state_substate':'0x0200:0x0600',
   'damage_writer':'0x01d590 then clamp 0x01d598',
   'health_before_s16':87,'health_after_damage_s16':-40,
   'health_after_clamp_s16':-1,'damage_s16':127},
  'allocation':{'collision_entry':'0x01d116',
   'impact_allocator':'0x01d622','pool_allocator':'0x0177da',
   'global_suppression_guard':'u8(0xff8244) == 0',
   'scheduler_guard':'record-type-24 release/dispatch at 0x01ba62 precedes record-type-4 collision scheduler at 0x01cbcc',
   'source_slot':'0x00ffc200','record_type_u8':24,'class_u8':'0x4e',
   'variant_field':{'attack_record_offset_u8':8,'type':'u8',
    'signed':False,'rule':'copy absolute signed byte at attack-record +0x08',
    'raw_u8':10,'variant_u8':10},
   'facing_rule':'copy defender reaction-facing actor+0x4f_u8',
   'x_rule':'signed midpoint of attacker attack-box center and defender hurt-box center',
   'y_rule':'signed midpoint of depth-projected attacker attack-box center and defender hurt-box center',
   'z_rule':'defender z_s16 - 1','first_spawn_position_s16':[833,325,311],
   'allocation_failure_rule':'damage remains applied; omit only the impact actor',
   'visible_frame_u16':2363,
   'fixed_slot_reuse_presentation':{
    'rule':'0x0177da preserves fields not written by 0x01d622 until class-0x4e state 0 runs on its next scheduler visit',
    'retained_fields':['animation_record','animation_timer','animation_branch'],
    'animation_record':'0x0008def0','assembly':'0x0008df62',
    'animation_timer_u16':4050,'animation_branch_s16':-32768,
    'state0_scheduler_frame_u16':2363,'state0_visible_frame_u16':2364,
    'state0_animation_record':'0x00092e50',
    'state0_assembly':'0x000931f8'}},
  'state0':{'state_write_u16':'0x0200','coordinate_mode_u8':2,
   'object_or_u16':'0x8000','rng_entry':'0x017c5e','rng_calls_u8':1,
   'rng_mask_u16':'0x001c','first_seed_before':'0x37cd',
   'first_seed_after':'0xa774','first_table_offset_u8':20,
   'first_jitter_s16':[-4,-4],
   'jitter_table_s16':[[0,0],[4,0],[4,-4],[4,4],[-4,0],[-4,-4],[-4,4],[-8,8]],
   'first_visible_position_after_state0_s16':[829,321,311]},
  'active_state':{'state_u16':'0x0200',
   'animation_records':variant10_records,
   'terminal_guard':'signed animation branch actor+0x24 < 0 advances state to 0x0400',
   'movement_result':'x/y/z unchanged after state-0 jitter'},
  'release_state':{'state_u16':'0x0400','release_routine':'0x0177f0',
   'first_last_visible_frame':2370,'first_absent_frame':2371},
  'source_bodies':{'collision_impact':{'first':'0x01d622',
    'last_exclusive':'0x01d6b2',
    'sha256':hashlib.sha256(op[0x1d622:0x1d6b2]).hexdigest()},
   'class_dispatch':{'first':'0x0927f6','last_exclusive':'0x0928aa',
    'sha256':hashlib.sha256(op[0x927f6:0x928aa]).hexdigest()}},
  'capture_identity':{
   'completion_a_actors_sha256':sha(SCENE_COMPONENT_A/'coffee_shop_scene_actors.tsv'),
   'completion_b_actors_sha256':sha(SCENE_COMPONENT_B/'coffee_shop_scene_actors.tsv'),
   'completion_a_health_sha256':sha(SCENE_COMPONENT_A/'coffee_shop_scene_health_writes.tsv'),
   'completion_b_health_sha256':sha(SCENE_COMPONENT_B/'coffee_shop_scene_health_writes.tsv'),
   'byte_identical':True},
  'collision_damage_authority':'shared collision writer; this actor is presentation-only',
  'rng_authority':'shared source RNG consumed by class-0x4e state 0',
  'mutation_controls':['attack-record +0x08 variant field',
   'variant-10 class-0x4e suppression','RNG call/order','animation sequence',
   'fixed-pool release'],
  'fixed_frame_substitute_forbidden':True,
  'retained_gameplay_authority':False}
 scene_class4b=[r for r in scene_actors if r['pool']=='record24' and
                r['class']=='4b']
 scene_class3d=[r for r in scene_actors if r['pool']=='record24' and
                r['class']=='3d']
 req(len(scene_class4b)==244 and len(scene_class3d)==4032 and
     any(r['slot']=='ffc300' and int(r['frame'])==2805
         for r in scene_class4b) and
     any(int(r['frame'])==2805 for r in scene_class3d),
     'Predator special Coffee Shop effect population drift')
 class4b_records=[animation_record(program,0x8f8e0+index*16)
                  for index in range(32)]
 req([row['branch_s16'] for row in class4b_records]==
     list(range(16))+list(range(15))+[-32753],
     'class-0x4b event sequence drift')
 class3d_records=[animation_record(program,0x9a918+index*16)
                  for index in range(9)]
 req(class3d_records[-1]['branch_s16']==-32768,
     'class-0x3d terminal presentation drift')
 class3d_offsets=[]
 for index in range(16):
  address=0x88864+index*4
  class3d_offsets.append([
   int.from_bytes(op[address:address+2],'big',signed=True),
   int.from_bytes(op[address+2:address+4],'big',signed=True)])
 req(class3d_offsets[0]==[-61,-13] and
     class3d_offsets[8]==[61,13] and len(set(map(tuple,class3d_offsets)))==16,
     'class-0x3d movement offset table drift')
 special_effects={
  'classification':'SOURCE_CLOSED_IMPLEMENTATION_FIELDS',
  'record_type_u8':24,
  'player_dispatch_entry':player_special['state_dispatch']['entry'],
  'player_active_handler':player_special['state_dispatch']['handlers']['0x00'],
  'action_writer':player_special['source_input']['action_writer'],
  'allocation_routine':'0x0177da','release_routine':'0x0177f0',
  'source_audio_commands_u16':[int(x,16) for x in
   player_special['active_state']['source_audio_commands']],
  'health_cost_s16':player_special['completion']['health_cost_s16'],
  'class_0x4b':{
   'record_type_u8':24,
   'dispatch':'0x08f86e','allocation_writer':'0x0231c2..0x0231f2',
   'allocation_routine':'0x0177da','release_routine':'0x0177f0',
   'class_u8':'0x4b','variant_u8':0,
   'allocation_writes':['active_u8 += 1','class_u8 = 0x4b',
    'copy player x/y/z','copy player facing','player+0x26 = actor low word',
    'actor+0x26 = player low word'],
   'state_sequence_u16':[0,0x0200,0x0400],
   'state0':{'object_or_u16':'0x8000','coordinate_mode_u8':0,
    'palette_u8':0,'facing_rule':'copy player facing; add signed x offset +8 when facing is one and -8 when zero',
    'position_writes':['z -= 1','y += 62','x += facing-adjusted 8'],
    'animation_records':class4b_records},
   'state_0x0200':{'owner':'player low-word pointer at actor+0x26',
    'terminal_guard':'advance to 0x0400 when player+0x5c_u8 != 0 OR player+0x25_u8 != 0; zero animation event continues the active update',
    'owner_contact_lifetime':'player writer 0x01986a clears player+0x5c at the start of every player update; collision may set it after the type-24 scheduler, so a prior-frame contact cannot terminate the linked actor',
    'negative_animation_rule':'record 31 branch -32753 wraps the shared animation sequence to record 0 on the next update while the owner terminal guard remains false',
    'coffee_shop_wrap_witness':{'terminal_record_frame_u16':2835,
     'wrapped_record_frame_u16':2836,'wrapped_animation_record':'0x0008f8e0'},
    'active_update_order':['terminal guard','shared animation 0x016536',
                           'shared visibility 0x017176','shared display 0x0167ac']},
   'state_0x0400':'release on next scheduler visit',
   'coffee_shop_first_lifetime':{'source_slot':'0x00ffc300',
    'first_frame':2805,'last_frame':2840},
   'scene_actor_rows_u16':len(scene_class4b),
   'rng_calls':0,'collision_or_damage_writes':0,
   'source_body':{'first':'0x08f86e','last_exclusive':'0x08f8e0',
    'sha256':hashlib.sha256(op[0x8f86e:0x8f8e0]).hexdigest()}},
  'class_0x3d':{
   'record_type_u8':24,
   'dispatch':'0x0887c8','allocation_writer':'0x023220..0x023246',
   'allocation_routine':'0x0177da','release_routine':'0x0177f0',
   'class_u8':'0x3d','variant_rule':'copy current class-0x4b animation branch low byte',
   'allocation_writes':['active_u8 += 1','class_u8 = 0x3d',
    'variant_u8 = class4b event','copy class4b x/z',
    'direction_u8 at +0x0c = player facing'],
   'unwritten_field_retention':{
    'rule':'source type-24 allocation and 0x023220 writer do not clear or write actor+0x14_s16; preserve the prior fixed-pool slot y field',
    'first_source_slot':'0x00ffbb00','prior_actor_class_u8':'0x49',
    'prior_last_frame_u16':2471,'prior_y_s16':343,
    'first_class3d_frame_u16':2805,'first_class3d_y_s16':343},
   'state_sequence_u16':[0,0x0200,0x0400],
   'state0':{'coordinate_mode_u8':0,'palette_u8':0,
    'object_or_u16':'0x8000','anchor_x':'copy spawn x to actor+0x38_s16',
    'anchor_z':'copy spawn z to actor+0x3c_s16',
    'presentation_selector_u8':0,'animation_records':class3d_records},
   'state_0x0200':{'terminal_guard':'signed animation branch < 0 advances state to 0x0400',
    'movement_offsets_s16':class3d_offsets,
    'movement_rule':'each scheduler visit restores anchor x/z, applies variant-indexed x/z offsets with x negated when direction_u8 is nonzero, copies z to y, then variant=(variant+8)&0x0f',
    'update_order':['terminal guard','movement','shared animation 0x016536',
                    'shared display 0x0167ac']},
   'state_0x0400':'release on next scheduler visit',
   'coffee_shop_first_lifetime':{'source_slot':'0x00ffbb00',
    'first_frame':2805},
   'scene_actor_rows_u16':len(scene_class3d),
   'rng_calls':0,'collision_or_damage_writes':0,
   'source_body':{'first':'0x0887c8','last_exclusive':'0x0888a0',
    'sha256':hashlib.sha256(op[0x887c8:0x888a0]).hexdigest()}},
  'spawn_owner':{'player_dispatch':'0x023132',
   'class4b_writer':'0x0231c2','class3d_writer':'0x023220',
   'scheduler_order':'player before type-24 ascending source slot'},
  'capture_identity':{
   'actors_sha256':sha(SCENE_COMPONENT_A/'coffee_shop_scene_actors.tsv'),
   'independent_capture_b_sha256':sha(SCENE_COMPONENT_B/'coffee_shop_scene_actors.tsv')},
  'mutation_controls':['wrong player routine','class4b allocation or owner guard',
   'class4b owner-contact lifetime','class4b event sequence/wrap',
   'class3d class/variant','class3d movement offset/sign',
   'animation terminal guard','fixed-pool release','fixed-frame substitute'],
  'rng_calls':0,'collision_or_damage_writes':0,
  'fixed_frame_substitute_forbidden':True,
  'retained_gameplay_authority':False}
 class44_samples=[r for r in ss if r['class']=='44' and r['slot']=='ffc580' and 2235<=int(r['frame'])<=2256]
 req(class44_samples and class44_samples[0]['state']=='512' and class44_samples[0]['anim']=='0008daf2' and any(r['frame']=='2250' and r['state']=='1024' for r in class44_samples) and any(r['frame']=='2251' and r['state']=='1026' for r in class44_samples) and any(r['frame']=='2254' and r['state']=='1028' and r['anim']=='0008db1a' for r in class44_samples),'class-0x44 command-guard lifecycle drift')
 class44_object_or=[r for r in ww if r['slot']=='ffc580' and r['class']=='44' and r['pc']=='08d9d8']
 req(len(class44_object_or)==1 and class44_object_or[0]['frame']=='2072' and class44_object_or[0]['state']=='512' and class44_object_or[0]['phase']=='0' and class44_object_or[0]['offset']=='2e' and class44_object_or[0]['old']=='00000000' and class44_object_or[0]['data']=='00008000' and class44_object_or[0]['mask']=='0000ffff','class-0x44 object priority writer drift')
 class44_records=[animation_record(program,0x8daf2),animation_record(program,0x8db1a)]
 class43_scene=[r for r in scene_actors if r['pool']=='record24' and
                r['class']=='43']
 class43_slots_by_group=[
  ['0x00ffbd80','0x00ffc300','0x00ffc380','0x00ffc180'],
  ['0x00ffc200','0x00ffc080','0x00ffbe00','0x00ffb900']]
 class43_scheduler_slots=[
  ['0x00ffb680','0x00ffb900','0x00ffbb00','0x00ffbd80',
   '0x00ffbf00','0x00ffc180','0x00ffc300','0x00ffc380'],
  ['0x00ffb900','0x00ffbd80','0x00ffbe00','0x00ffbf00',
   '0x00ffc080','0x00ffc180','0x00ffc200','0x00ffc380']]
 class43_rng=[r for r in rr if r['class']=='43']
 req(len(class43_scene)==828 and len(class43_rng)==112 and
     [(int(r['frame']),f"0x00ff{r['slot'][2:]}")
      for r in class43_rng[::7]]==
     [(2328,slot) for slot in class43_scheduler_slots[0]]+
     [(3605,slot) for slot in class43_scheduler_slots[1]],
     'class-0x43 Coffee Shop population/RNG order drift')
 class43_selector_table=list(op[0x8cf74:0x8cf94])
 req(class43_selector_table==[5,6,7,15,5,6,7,15,0,1,2,3,4,8,9,10,
                              11,12,13,14,0,1,2,3,4,8,9,10,11,12,13,14],
     'class-0x43 animation selector table drift')
 class43_selector_starts=[0x8d128+int.from_bytes(
     program[0x8d128+2*index:0x8d12a+2*index],'big')
     for index in range(16)]
 req(class43_selector_starts==[0x8d14a,0x8d1ae,0x8d212,0x8d276,
     0x8d2da,0x8d33e,0x8d3a2,0x8d3e6,0x8d42a,0x8d46e,0x8d4f2,
     0x8d576,0x8d59a,0x8d5ae,0x8d5c2,0x8d5d6],
     'class-0x43 animation offset table drift')
 class43_sequences=[]
 for selector,start in enumerate(class43_selector_starts):
  records=[];address=start
  while True:
   record=animation_record(program,address);records.append(record)
   if record['branch_s16']<0: break
   address+=16
  class43_sequences.append({'selector_u8':selector,'records':records})
 class43_motion=[]
 for index in range(8):
  address=0x8d0a8+index*16
  values=[int.from_bytes(op[address+offset:address+offset+2],
                         'big',signed=True) for offset in range(0,16,2)]
  class43_motion.append({'primary_x_velocity_s16':values[0],
   'primary_y_velocity_s16':values[1],
   'primary_x_acceleration_s16':values[2],
   'primary_y_acceleration_s16':values[3],
   'alternate_x_velocity_s16':values[4],
   'alternate_y_velocity_s16':values[5],
   'alternate_x_acceleration_s16':values[6],
   'alternate_y_acceleration_s16':values[7]})
 class43_lifetimes=[]
 for slot in sorted({r['slot'] for r in class43_scene}):
  actor_rows=sorted((r for r in class43_scene if r['slot']==slot),
                    key=lambda r:int(r['frame']))
  run=[];prior=None
  for row in actor_rows:
   frame=int(row['frame'])
   if prior is not None and frame!=prior+1:
    class43_lifetimes.append(run);run=[]
   run.append(row);prior=frame
  if run: class43_lifetimes.append(run)
 class43_lifetime_records=[{
  'source_slot':f"0x00ff{run[0]['slot'][2:]}",
  'first_frame':int(run[0]['frame']),'last_frame':int(run[-1]['frame']),
  'state_words_u16':sorted({int(r['state'],16) for r in run}),
  'animation_records':sorted({f"0x{int(r['animation_record'],16):08x}"
                              for r in run})} for run in class43_lifetimes]
 req(len(class43_lifetime_records)==16 and
     {(r['source_slot'],r['first_frame'],r['last_frame']) for r in
      class43_lifetime_records} >= {
       ('0x00ffb680',2329,2378),('0x00ffb900',3606,3651)},
     'class-0x43 Coffee Shop lifetime segmentation drift')
 class43={'classification':'SOURCE_CLOSED_IMPLEMENTATION_FIELDS',
  'dispatch':'0x08ce44','spawn_routine':'0x08cde6',
  'allocation_routine':'0x0177da','release_routine':'0x0177f0',
  'record_type_u8':24,'class_u8':'0x43','variant_u8':0,
  'allocation_pop_order_by_group':class43_slots_by_group,
  'source_slots_scheduler_order_by_spawn':class43_scheduler_slots,
  'spawn_owner':{'record_type_u8':20,'class_u8':'0x01',
   'source_slots':['0x00ffb580','0x00ffb400'],
   'state_substate_guard':'0x0204:0x0000 and signed animation branch < 0',
   'caller_pc':'0x06b3a8 then 0x06b3ae',
   'spawn_frames_u16':[2328,3605],
   'groups_u8':2,'attempts_per_group_u8':4,
   'allocation_failure_rule':'stop only the current four-actor group',
   'writes':['allocator active_u8 += 2','class_u8 = 0x43',
             'variant_u8 = owner+0x42_u8 = 0',
             'x_s16 = owner.x_s16','y_s16 = owner.y_s16 + 80',
             'z_s16 = owner.z_s16 - 1',
             'primary and alternate x/y accumulators copy spawn x/y',
             'direction_u8 = owner+0x4f_u8 = 0']},
  'state_sequence':{
   'phase_byte_u8':[0,2,4],
   'landing_bits_u8':[0,1,2,3],
   'visible_state_word_rule':'(phase_byte_u8 << 8) | landing_bits_u8'},
  'state0':{'object_or_u16':'0x8000','rng_calls_u8':7,
   'rng_order':['alternate animation selector','primary animation selector',
                'primary x jitter','primary y jitter','alternate x jitter',
                'alternate y jitter','motion table selector'],
   'animation_selector_mask_variant0_u16':'0x001f',
   'animation_selector_mask_other_u16':'0x0007',
   'animation_selector_table_u8':class43_selector_table,
   'animation_offset_table_address':'0x0008d128',
   'animation_sequences':class43_sequences,
   'jitter_rule':'each position jitter uses (rng_low & 0x1f) - 0x10 signed pixels',
   'motion_selector':'table_index=(rng_low&0x70)>>4; no extra RNG call',
   'motion_table':class43_motion,
   'direction_rule':'negate both x velocity and x acceleration fields when direction_u8 is zero',
   'position_fields':'primary and alternate signed 16.16 accumulators seeded from spawn x/y'},
  'state_0x0200':{
   'movement_arithmetic':'for each channel whose landing bit is clear, sign-extend x/y velocity, shift left 8, add to signed 16.16 positions, then add signed y acceleration to signed y velocity',
   'animation_arithmetic':'decrement both timers independently; advance by 16 bytes, or follow the negative terminal branch back to the sequence start',
   'position_projection':'select primary or alternate by (global phase byte + type-24 scheduler index)&1; selected signed 16.16 high words own x/y; z remains spawn z',
   'landing_guard':'set channel landing bit when unsigned channel_y < unsigned z; a landed channel stops moving; when both bits are set advance phase byte to 4',
   'display_guard':'submit presentation only while selected unsigned y > unsigned z'},
  'state_0x0400':'release on the next scheduler visit',
  'rng_entry':'0x017c5e','rng_calls_per_actor_u8':7,
  'rng_calls_total_u16':112,'lifetimes':class43_lifetime_records,
  'collision_or_damage_writes':0,'audio_writes':0,
  'route_or_camera_writes':0,
  'source_bodies':{
   'spawn':{'first':'0x08cde6','last_exclusive':'0x08ce44',
    'sha256':hashlib.sha256(op[0x8cde6:0x8ce44]).hexdigest()},
   'dispatch':{'first':'0x08ce44','last_exclusive':'0x08d0a8',
    'sha256':hashlib.sha256(op[0x8ce44:0x8d0a8]).hexdigest()}},
  'capture_identity':{
   'actors_sha256':sha(SCENE_COMPONENT_A/'coffee_shop_scene_actors.tsv'),
   'rng_sha256':sha(A/'aux_rng.tsv')},
  'mutation_controls':['spawn owner guard','group count','allocation order',
   'class or variant','spawn y/z offset','RNG count or order',
   'selector mask/table','animation offset or terminal loop','jitter mask/sign',
   'motion row','direction sign','per-channel landing bit',
   'dual landing transition','channel projection parity','fixed-pool release'],
  'semantic_role':'SOURCE_OWNED_PRESENTATION_POPULATION',
  'fixed_frame_substitute_forbidden':True,
  'retained_gameplay_authority':False}
 class45_slots=[f'0x00ff{x:04x}' for x in range(0xb680,0xc480,0x80)]
 class45_entries=[r for r in ss if r['class']=='45' and int(r['frame'])==2254]
 req([f"0x00ff{r['slot'][2:]}" for r in class45_entries]==class45_slots,
     'class-0x45 Coffee Shop source allocation/scheduler order drift')
 class45_rng=[r for r in rr if r['class']=='45' and int(r['frame'])==2254]
 req(len(class45_rng)==196 and class45_rng[0]['slot']=='ffb680' and
     class45_rng[-1]['slot']=='ffc400',
     'class-0x45 Coffee Shop RNG transaction drift')
 selector_table=list(op[0x8ddfe:0x8de1e])
 req(selector_table==[0,1,0,3,4,5,0,1,1,3,4,5,0,1,3,3,
                      4,5,0,1,4,3,4,5,0,1,5,3,4,5,0,1],
     'class-0x45 animation selector table drift')
 motion_table=[]
 for index in range(8):
  address=0x8dcf4+index*16
  values=[int.from_bytes(op[address+offset:address+offset+2],
                         'big',signed=True) for offset in range(0,16,2)]
  motion_table.append({'primary_x_velocity_s16':values[0],
   'primary_y_velocity_s16':values[1],
   'primary_y_acceleration_s16':values[3],
   'alternate_x_velocity_s16':values[4],
   'alternate_y_velocity_s16':values[5],
   'alternate_y_acceleration_s16':values[7]})
 class45_records=[animation_record(program,address) for address in
                  (0x8dedc,0x8def0,0x8df18,0x8df2c,0x8df40)]
 class45={'classification':'SOURCE_CLOSED_IMPLEMENTATION_FIELDS',
  'dispatch':'0x08dc1c','allocation_routine':'0x0177da',
  'release_routine':'0x0177f0','record_type_u8':24,'class_u8':'0x45',
  'source_slots_scheduler_order':class45_slots,
  'allocation_pop_order':list(reversed(class45_slots)),
  'spawn_owner':{'source_slot':'0x00ffc580','class_u8':'0x44',
   'state_substate_guard':'0x0400:0x0402 predecrement actor+0x2a_u8 equals zero',
   'groups':[{'attempts_u16':5,'x_offset_s16':0,'y_offset_s16':128,
              'z_offset_s16':-1},
             {'attempts_u16':5,'x_offset_s16':0,'y_offset_s16':128,
              'z_offset_s16':-1},
             {'attempts_u16':'until allocation failure','x_offset_s16':48,
              'y_offset_s16':64,'z_offset_s16':-1}],
   'spawn_frame':2253,'first_visible_state0_frame':2254},
  'initial_active_write':'allocator adds 2 to record+0x00_u8; class=0x45; state remains 0',
  'state_sequence_u16':[0,0x0200,0x0400],
  'state0':{'object_or_u16':'0x8000','rng_calls_u8':7,
   'animation_rng_calls_u8':2,'animation_selector_mask_u16':'0x001f',
   'animation_selector_table_u8':selector_table,
   'animation_record_base':'0x0008dece','animation_records':class45_records,
   'facing_and_primary_x_jitter':
      'rng3: facing=(low&3), primary_x += (low&0x3f)-0x20',
   'primary_y_jitter':'rng4: primary_y += (low&0x7f)-0x40',
   'alternate_x_jitter':'rng5: alternate_x += (low&0x3f)-0x20',
   'alternate_y_jitter':'rng6: alternate_y += (low&0x7f)-0x40',
   'motion_selector':'rng7: direction_bit=low&1; table_index=(low&0x70)>>4',
   'motion_table':motion_table,
   'position_fields':'primary and alternate signed 16.16 accumulators seeded from spawn x/y'},
  'state_0x0200':{'movement_arithmetic':
   'sign-extend each s16 velocity, negate both x velocities when direction_bit is zero, shift left 8, add to signed 16.16 positions; then add signed y accelerations to signed y velocities',
   'animation_arithmetic':
   'advance both source animation records independently; presentation selects primary or alternate by (global parity byte + scheduler index)&1',
   'position_projection':'selected signed 16.16 high words own x/y; z remains spawn z',
   'terminal_guard':'when both unsigned primary_y and alternate_y are less than or equal to z, advance state to 0x0400'},
  'state_0x0400':'release on the next scheduler visit',
  'rng_entry':'0x017c5e','rng_calls_per_actor_u8':7,
  'rng_calls_total_u16':196,'collision_or_damage_writes':0,
  'audio_writes':0,'route_or_camera_writes':0,
  'source_body':{'first':'0x08dc1c','last_exclusive':'0x08dece',
   'sha256':hashlib.sha256(op[0x8dc1c:0x8dece]).hexdigest()},
  'fixed_frame_substitute_forbidden':True,
  'retained_gameplay_authority':False}
 scene_class47=[r for r in scene_actors if r['pool']=='record24' and
                r['class']=='47']
 class47_slots=sorted({f"0x00ff{r['slot'][2:]}" for r in scene_class47})
 req(class47_slots==['0x00ffbd80','0x00ffc180','0x00ffc200','0x00ffc380'] and
     len(scene_class47)==197,
     'class-0x47 Coffee Shop actor population drift')
 class47_rng=[r for r in rows(SCENE_COMPONENT_A/'coffee_shop_rng_calls.tsv')
              if r['type']=='24' and r['class']=='47']
 req(len(class47_rng)==28 and
     [r['a6'] for r in class47_rng[::7]]==
      ['ffbd80','ffc180','ffc200','ffc380'],
     'class-0x47 Coffee Shop RNG order drift')
 class47_lifetimes=[]
 for slot in class47_slots:
  short_slot=slot[-6:]
  actor_rows=[r for r in scene_class47 if r['slot']==short_slot]
  class47_lifetimes.append({
   'source_slot':slot,'first_frame':int(actor_rows[0]['frame']),
   'last_frame':int(actor_rows[-1]['frame']),
   'states_u16':sorted({int(r['state'],16) for r in actor_rows}),
   'animation_records':sorted({f"0x{int(r['animation_record'],16):08x}"
                               for r in actor_rows})})
 class47_selectors=list(op[0x8ed54:0x8ed74])
 req(class47_selectors==[0,1,2,3,4,5,6,0,1,2,3,4,5,6,0,1,
                         2,3,4,5,6,7,8,7,8,7,8,0,1,2,3,4],
     'class-0x47 selector table drift')
 class47_motion=[]
 for index in range(8):
  address=0x8ec4a+index*16
  values=[int.from_bytes(op[address+offset:address+offset+2],
                         'big',signed=True) for offset in range(0,16,2)]
  class47_motion.append({'primary_x_velocity_s16':values[0],
   'primary_y_velocity_s16':values[1],
   'primary_y_acceleration_s16':values[3],
   'alternate_x_velocity_s16':values[4],
   'alternate_y_velocity_s16':values[5],
   'alternate_y_acceleration_s16':values[7]})
 class47_records=[animation_record(program,address) for address in
                  (0x8ee38,0x8ee4c,0x8ee60,0x8ee74,0x8ee88,0x8ee9c,
                   0x8eeb0,0x8eec4,0x8eed8)]
 class47={'classification':'SOURCE_CLOSED_IMPLEMENTATION_FIELDS',
  'dispatch':'0x08eb86','spawn_routine':'0x08eb1c',
  'allocation_routine':'0x0177da','release_routine':'0x0177f0',
  'record_type_u8':24,'class_u8':'0x47','variant_u8':0,
  'source_slots_scheduler_order':class47_slots,
  'allocation_pop_order':list(reversed(class47_slots)),
  'spawn_owner':{'source_slot':'0x00ffb300','record_type_u8':20,
   'class_u8':'0x02','state_substate_guard':'0x0400:0x0000',
   'caller_pc':'0x06b61a','spawn_frame':2805,'attempts_u16':4,
   'allocation_failure_rule':'stop the remaining group on first failed allocation',
   'writes':['allocator active_u8 += 2','class_u8 = 0x47',
             'variant_u8 = D4 = 0','x_s16 = owner.x_s16',
             'y_s16 = owner.y_s16 + 80','z_s16 = owner.z_s16 - 1',
             'primary and alternate x/y accumulators copy spawn x/y',
             'direction_u8 = owner+0x4f_u8']},
  'state_sequence_u16':[0,0x0200,0x0400],
  'state0':{'object_or_u16':'0x8000','rng_calls_u8':7,
   'rng_order':['primary animation selector','alternate animation selector',
                'primary x jitter','primary y jitter','alternate x jitter',
                'alternate y jitter','motion table selector'],
   'animation_selector_mask_variant0_u16':'0x000f',
   'animation_selector_mask_other_u16':'0x001f',
   'animation_selector_table_u8':class47_selectors,
   'animation_record_offset_table_u16':[20,40,60,80,100,120,140,160,180],
   'animation_records':class47_records,
   'jitter_rule':'each position jitter uses (rng_low & 0x1f) - 0x10 signed pixels',
   'motion_selector':'table_index=(rng_low&0x70)>>4; no direction RNG consumption',
   'motion_table':class47_motion,
   'position_fields':'primary and alternate signed 16.16 accumulators seeded from spawn x/y'},
  'state_0x0200':{'movement_arithmetic':
   'sign-extend each s16 velocity, negate both x velocities when owner direction_u8 is zero, shift left 8, add to signed 16.16 positions; add signed y accelerations to signed y velocities after position integration',
   'animation_arithmetic':
   'advance primary and alternate source animation records independently; select visible channel by (global frame parity byte + scheduler index)&1',
   'position_projection':'selected signed 16.16 high words own x/y; z remains spawn z',
   'terminal_guard':'when both unsigned primary_y and alternate_y are less than or equal to z, advance state to 0x0400'},
  'state_0x0400':'release on the next scheduler visit',
  'rng_entry':'0x017c5e','rng_calls_per_actor_u8':7,
  'rng_calls_total_u16':28,'lifetimes':class47_lifetimes,
  'collision_or_damage_writes':0,'audio_writes':0,
  'route_or_camera_writes':0,
  'source_bodies':{
   'spawn':{'first':'0x08eb1c','last_exclusive':'0x08eb86',
    'sha256':hashlib.sha256(op[0x8eb1c:0x8eb86]).hexdigest()},
   'dispatch':{'first':'0x08eb86','last_exclusive':'0x08ee24',
    'sha256':hashlib.sha256(op[0x8eb86:0x8ee24]).hexdigest()}},
  'capture_identity':{
   'actors_sha256':sha(SCENE_COMPONENT_A/'coffee_shop_scene_actors.tsv'),
   'rng_sha256':sha(SCENE_COMPONENT_A/'coffee_shop_rng_calls.tsv')},
  'mutation_controls':['spawn count','owner guard','class','variant',
   'spawn y offset','spawn z offset','RNG count/order','selector mask/table',
   'jitter mask/sign','motion table','direction sign','dual terminal guard',
   'fixed-pool release'],
 'semantic_role':'SOURCE_OWNED_PRESENTATION_CHILD',
 'fixed_frame_substitute_forbidden':True,
 'retained_gameplay_authority':False}
 class4e_variant10['shared_dispatch_reachable_variant_programs']=\
  reachable_variant_programs
 return {'classification':'SOURCE_CLOSED_IMPLEMENTATION_FIELDS','class_0x09_type20_rng_owner':{'dispatch':'0x06d926','state':'0x0200','source_slots':initial,'state_guard':'signed animation branch at actor+0x24 is negative','rng_entry':'0x017c5e','rng_call_pc':'0x06d974','rng_mask_u16':'0x000e','selector_table_address':'0x06d9a4','selector_table_u16':[0,7,8,9,10,8,9,10],'first_segment_calls_before_class4e':44,'seed_after_first_call':'0x44fb','seed_after_last_call':'0x99e8','animation_sequences':class09_sequences,'movement_result':'x/y/z unchanged in the accepted first-segment window','scheduler_order':'type-20 ascending source slot: 0xffb480 then 0xffb500','source_window':window(op,0x06d96e),'complete_coffee_shop_program':class09_complete_program,'fixed_frame_substitute_forbidden':True},'class_0x4e_type24_variant4_effect':{'dispatch':'0x0927f6','variant_u8':4,'allocation_routine':'0x0177da','release_routine':'0x0177f0','available_source_slots':['0x00ffc480','0x00ffc500'],'allocation_pop_order':['0x00ffc500','0x00ffc480'],'scheduler_order':['0x00ffc480','0x00ffc500'],'initial_positions_before_rng':[{'source_slot':'0x00ffc500','x_s16':816,'y_s16':384,'z_s16':296},{'source_slot':'0x00ffc480','x_s16':848,'y_s16':424,'z_s16':296}],'state_sequence_u16':[0,0x0200,0x0400],'state0_writes':{'coordinate_mode_u8':2,'object_or_u16':'0x8000'},'rng_entry':'0x017c5e','rng_call_pc':'0x09282a','rng_mask_u16':'0x001c','seed_after_by_scheduler_slot':[{'source_slot':'0x00ffc480','seed':'0xcdb5','table_index':28},{'source_slot':'0x00ffc500','seed':'0x691e','table_index':24}],'jitter_table_s16':[[0,0],[4,0],[4,-4],[4,4],[-4,0],[-4,-4],[-4,4],[-8,8]],'animation_records':class4e_records,'collision_or_damage_writes':0,'later_same-window_allocation_attempts':'fail while both source free-list entries are active','source_window':window(op,0x0927f6),'fixed_frame_release_forbidden':True,'variant1_collision_effect':class4e_variant1,'variant10_collision_effect':class4e_variant10},'class_0x44_type24_command_guard_owner':{'dispatch':'0x08d9a4','source_slot':'0x00ffc580','initial_state_u16':0x0200,'initial_position_s16':[792,296,296],'state_sequence_u16':[0x0200,0x0400,0x0402,0x0404],'state0_presentation_actor':{'coordinate_mode_u8':0,'palette_u8':0,'facing_u8':0,'object_or_u16':'0x8000','object_or_writer_pc':'0x08d9d8','object_or_write_frame':2072,'object_or_write_mask':'0x0000ffff','zero_fields_source':'accepted zero-initialized type-24 record; generic allocation writes preserve coordinate mode, palette and facing at zero'},'state_0x0200_guard':'global 0xff9a10_u8 nonzero advances state to 0x0400','state_0x0400_substate_0_writes':['global 0xff9a10_u8 = 0','actor substate += 2','actor+0x2a_u8 = 3'],'state_0x0402_guard':'predecrement actor+0x2a_u8; zero advances substate to 0x0404 and binds second presentation record','state_0x0404_result':'holds source presentation in the accepted first-segment window; does not clear the second command guard','animation_records':class44_records,'first_guard_set_frame':2249,'guard_clear_frame':2250,'second_player_origin_command_frame':2255,'rng_calls':0,'collision_or_damage_writes':0,'source_window':window(op,0x08d9a4),'fixed_frame_guard_reset_forbidden':True},'class_0x43_type24_class01_scene_population':class43,'class_0x45_type24_scene_population':class45,'class_0x47_type24_class02_child_presentation':class47,'predator_special_type24_effects':special_effects}
def suppression(typ,cls):
 raw=int(cls,16);p=ROOT/f'.deps/mame/oracle11_aux_suppress_{typ}_{raw:02x}_v2';files=('suppression.tsv','samples.tsv','dispatches.tsv','projectiles.tsv','score_writes.tsv','result.tsv');identity=ident(p,files)
 s=rows(p/'suppression.tsv')[0];r=rows(p/'result.tsv')[0]
 req(int(s['suppression_count'])>0 and int(s['first_frame'])>0,'accepted auxiliary suppression removed nothing')
 return {'capture':p.name,'identity':identity,'suppression_count':int(s['suppression_count']),'first_frame':int(s['first_frame']),'final_route':int(r['final_route']),'final_player_active':int(r['final_active']),'final_player_state':int(r['final_state']),'final_health':int(r['final_health']),'final_resource':int(r['final_resource']),'final_score':r['final_score'],'classification':'PASS'}

def build():
 ia,ib=ident(A),ident(B);req(ia['files']==ib['files'],'auxiliary baselines differ')
 ss,ee,ww,rr,ff=[rows(A/f) for f in FILES[:5]];op=OPCODES.read_bytes();program=PROGRAM.read_bytes()
 route=json.loads(ROUTE.read_text());sched=json.loads(SCHED.read_text());player=json.loads(PLAYER.read_text(encoding='ascii'));nav=json.loads(NAV.read_text(encoding='ascii'))
 req(player['status']=='SOURCE_CLOSED' and nav['status']=='SOURCE_CLOSED','accepted dependent family reopened')
 archetypes=[];owned=set()
 for (typ,cls),entry in DISPATCH.items():
  filt=lambda r:int(r['type'])==typ and f"0x{r['class']}"==cls
  s=[r for r in ss if filt(r)];e=[r for r in ee if filt(r)];w=[r for r in ww if filt(r)];rng=[r for r in rr if filt(r)];effects=[r for r in ff if int(r['owner_type'])==typ and f"0x{r['owner_class']}"==cls]
  counts=(len(s),len(e),len(w),len(rng),len(effects));req(counts==EXPECTED[(typ,cls)],f'{typ}/{cls}:count drift')
  groups=defaultdict(list)
  for r in w:groups[r['pc']].append(r)
  writers=[]
  for pc,obs in sorted(groups.items()):
   owned.add(f'0x{pc}');writers.append({'pc':f'0x{pc}','count':len(obs),'offsets':sorted({f"0x{x['offset']}" for x in obs}),'state_phase_contexts':sorted({f"{int(x['state']):04x}:{int(x['phase']):04x}" for x in obs}),'source_window':window(op,int(pc,16))})
  rngpcs=Counter(f"0x{x['pc']}" for x in rng);owned.update(rngpcs);owned.add(f'0x{entry:06x}')
  records=source_records(ss,typ,cls,program)
  archetypes.append({'type':typ,'class':cls,'classification':'SOURCE_CLOSED','dispatch_entry':f'0x{entry:06x}','dispatch_entry_sha256':hashlib.sha256(op[entry:entry+64]).hexdigest(),'counts':{'samples':counts[0],'entries':counts[1],'writes':counts[2],'rng':counts[3],'player_effects':counts[4]},'state_phase_contexts':sorted({f"{int(x['state']):04x}:{int(x['phase']):04x}" for x in s}),'facing_values':sorted({int(x['facing']) for x in s}),'target_pointers':sorted({f"0x{int(x['target'],16):04x}" for x in s}),'writer_provenance':writers,'rng':{'calls':len(rng),'caller_pcs':dict(sorted(rngpcs.items())),'orphan_calls':0},'presentation_and_collision':{'records':records,'record_count':len(records),'orphan_records':0},'player_effects':[{k:x[k] for k in ('frame','field','pc','owner_slot','owner_state','owner_phase','old','data','mask')} for x in effects],'counterfactual':suppression(typ,cls),'orphan_write_rows':0,'semantic_name_inferred':False})
  req(records,f'{typ}/{cls}:no source presentation records')
 phantom=[]
 for actor_id,reason in [('actor-class-00-type-0','contains the player record plus a half-stride census alias; no source pool dispatch'),('actor-class-80-type-0','all six addresses are half-stride aliases between type-24 source records'),('actor-class-00-type-240','address 0xffb2c0 is a half-stride alias between type-20 source records'),('actor-class-80-type-240','same half-stride alias after source lifecycle writes')]:phantom.append({'id':actor_id,'classification':'NOT_REQUIRED_FOR_ROUND1','reason':reason,'scheduler_dispatch':None})
 report={'schema':'oracle11-round1-auxiliary-authority-v1','task':'ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE','status':'SOURCE_CLOSED','scope':'Round 1 pickups, equipment, weapons, projectiles, hazards and destructibles','capture_identity':{'completion_a':ia,'completion_b':ib,'byte_identical':True,'sample_rows':len(ss),'entry_rows':len(ee),'write_rows':len(ww),'rng_rows':len(rr),'player_effect_rows':len(ff)},'archetypes':archetypes,'phantom_census_aliases':phantom,'player_side_contract':{'classification':'SOURCE_CLOSED','evidence':'data/oracle11_predator_weapon_projectile_resource.json'},'navigation_body_geometry_contract':{'classification':'SOURCE_CLOSED','evidence':'data/oracle11_round1_navigation.json'},'owned_authoritative_writer_pcs':sorted(owned),'coverage':{'required_dispatched_pairs':12,'closed_dispatched_pairs':12,'not_required_alias_pairs':4,'orphan_dispatched_pairs':0,'orphan_state_phase_contexts':0,'orphan_write_rows':0,'orphan_rng_calls':0,'orphan_animation_records':0,'orphan_player_effects':0,'invalid_zero_removal_controls_accepted':0},'correction_record':{'finding':'initial suppression notifier handle was local and garbage-collected','invalid_capture_suffix':'no suffix','invalid_controls_removed_zero_actors':True,'accepted_capture_suffix':'v2','accepted_controls_all_remove_actors':True},'negative_controls':{'zero_removal_suppression_rejected':True,'semantic_names_inferred':False,'appearance_only_classification_forbidden':True,'fixed_frame_effect_forbidden':True,'generic_effect_framework_forbidden':True},'protected_boundaries':{'production_runtime_writes':0,'yaba_runs':0,'frontend_active':False,'user09_status':'CHANGES_REQUESTED','physical_saturn':'UNRUN','spec02_active':False,'oracle11_active':True}}
 report['first_segment_dependencies']=first_segment_dependencies(ss,ee,ww,rr,op,program)
 report['first_segment_dependencies']['class_0x08_type20_health_pickup']=\
  coffee_shop_class08_health_pickup(op,program,ww,rr)
 report['first_segment_dependencies']['class_0x05_type20_reactive_prop']=\
  coffee_shop_class05_reactive_prop(op,program,ww,rr)
 req(CLASS4E_VARIANT0_CONTRACT is not None,
     'class-0x4e variant-0 implementation contract missing')
 report['first_segment_dependencies']['class_0x4e_type24_variant4_effect'][
  'variant0_collision_effect']=CLASS4E_VARIANT0_CONTRACT
 req(CLASS4E_TERMINAL_TRANSITION is not None,
     'class-0x4e terminal transition implementation contract missing')
 report['first_segment_dependencies']['class_0x4e_type24_variant4_effect'][
  'terminal_transition']=CLASS4E_TERMINAL_TRANSITION
 report['first_segment_dependencies']['class_0x4e_type24_variant4_effect'][
  'terminal_guard']='signed actor+0x24 becomes negative, then state advances to 0x0400 and the next scheduler visit releases the record'
 report['first_segment_dependencies']['class_0x1f_type16_0x06_projectile']=\
  coffee_shop_class1f_type16_projectile(op,program,ww)
 report['coffee_shop_type36_presentation']=coffee_shop_type36_presentation(
  op,program)
 report['coffee_shop_scene_component_identities']=\
  coffee_shop_scene_component_identities(op,program)
 c4e=report['first_segment_dependencies']['class_0x4e_type24_variant4_effect']
 mislabeled=c4e.pop('seed_after_by_scheduler_slot')
 c4e['seed_transaction_by_scheduler_slot']=[
  {'source_slot':row['source_slot'],'seed_before':row['seed'],
   'seed_after':f"0x{next_seed(int(row['seed'],16)):04x}",
   'table_index':row['table_index']} for row in mislabeled]
 c4e['seed_field_correction']='accepted RNG rows are pre-call seeds; post-call seeds are the source recurrence result'
 validate(report);return report

def validate(r):
 req(r['schema']=='oracle11-round1-auxiliary-authority-v1' and r['status']=='SOURCE_CLOSED','aux family status drift');req(r['capture_identity']['byte_identical'] is True and r['capture_identity']['sample_rows']==120620 and r['capture_identity']['entry_rows']==59865 and r['capture_identity']['write_rows']==428764 and r['capture_identity']['rng_rows']==1348 and r['capture_identity']['player_effect_rows']==2,'aux capture drift')
 op=OPCODES.read_bytes();req(len(r['archetypes'])==12 and {(x['type'],x['class']) for x in r['archetypes']}==set(DISPATCH),'aux inventory drift')
 for x in r['archetypes']:
  key=(x['type'],x['class']);entry=DISPATCH[key];exp=EXPECTED[key];req(x['classification']=='SOURCE_CLOSED' and x['dispatch_entry']==f'0x{entry:06x}' and x['dispatch_entry_sha256']==hashlib.sha256(op[entry:entry+64]).hexdigest() and tuple(x['counts'][k] for k in ('samples','entries','writes','rng','player_effects'))==exp and x['writer_provenance'] and x['orphan_write_rows']==0 and x['rng']['orphan_calls']==0 and x['presentation_and_collision']['record_count']>0 and x['presentation_and_collision']['orphan_records']==0 and x['counterfactual']['suppression_count']>0 and x['counterfactual']['first_frame']>0 and x['counterfactual']['classification']=='PASS' and x['semantic_name_inferred'] is False,f'{key}:aux authority drift')
 deps=r['first_segment_dependencies'];c09=deps['class_0x09_type20_rng_owner'];c09c=c09['complete_coffee_shop_program'];c08=deps['class_0x08_type20_health_pickup'];c05=deps['class_0x05_type20_reactive_prop'];c4e=deps['class_0x4e_type24_variant4_effect'];c4e0=c4e['variant0_collision_effect'];c4e1=c4e['variant1_collision_effect'];c4e10=c4e['variant10_collision_effect'];c44=deps['class_0x44_type24_command_guard_owner'];c43=deps['class_0x43_type24_class01_scene_population'];c45=deps['class_0x45_type24_scene_population'];c47=deps['class_0x47_type24_class02_child_presentation'];special=deps['predator_special_type24_effects'];c4b=special['class_0x4b'];c3d=special['class_0x3d'];c16=deps['class_0x1f_type16_0x06_projectile'];psc=c4e1['player_special_collision']
 req(c09c['classification']=='SOURCE_CLOSED_IMPLEMENTATION_FIELDS' and
     c09c['source_frame_range_u16']==[2073,5550] and
     c09c['source_slots']==['0x00ffb480','0x00ffb500'] and
     c09c['reachable_state_substate_u16']==['0x0200:0x0000'] and
     c09c['source_row_count_u16']==6956 and
     c09c['source_rng_call_count_u16']==898 and
     c09c['source_rng_frame_range_u16']==[2079,5522] and
     c09c['state_dispatch']['entry']=='0x06d926' and
     c09c['state_dispatch']['state_0_target']=='0x06d93a' and
     c09c['state_dispatch']['state_0x0200_target']=='0x06d96e' and
     c09c['state_0']['animation_bind_entry']=='0x016518' and
     c09c['state_0x0200']['terminal_guard'].startswith('signed actor+0x24') and
     c09c['state_0x0200']['terminal_order'][-1].endswith('0x016536') and
     c09c['selector_table_u16']==[0,7,8,9,10,8,9,10] and
     c09c['animation_record_count_u8']==10 and
     c09c['exit_presentation_witness']['frame_5493'][0]=={
      'source_slot':'0x00ffb480','animation_record':'0x0006dbda',
      'timer_u16':0,'branch_s16':0} and
     len(c09c['mutation_controls'])==8 and
     c09c['fixed_frame_substitute_forbidden'] is True and
     c09c['retained_gameplay_authority'] is False,
     'class-0x09 complete Coffee Shop program drift')
 req(c05['classification']=='SOURCE_CLOSED_IMPLEMENTATION_FIELDS' and
     c05['spec_executable'] is True and c05['dispatch']=='0x06c9ee' and
     c05['source_slots']==['0x00ffb180','0x00ffb280'] and
     [(x['address'],x['x_s16'],x['y_s16']) for x in c05['stage_records']]==
      [('0x0015c188',1264,293),('0x0015c1a8',1284,268)] and
     c05['current_state_collision']['attack_record']['address']==
      '0x0011af76' and
     c05['current_state_collision']['hurt_record']['address']==
      '0x0006cd50' and
     c05['current_state_collision']['impact_allocation']['source_slot']==
      '0x00ffc200' and
     c05['reaction_program']['state_0x0400']['audio_command_u16']==
      '0x0074' and
     c05['reaction_program']['state_0x0400']['seed_before']=='0xcb46' and
     c05['reaction_program']['state_0x0404']['primary']
      ['x_velocity_s32']==-0x00050000 and
     c05['capture_identity']['byte_identical'] is True and
     len(c05['mutation_controls'])==14 and
     c05['fixed_frame_substitute_forbidden'] is True and
     c05['retained_gameplay_authority'] is False,
     'Coffee Shop class-0x05 implementation contract drift')
 reachable=c4e10['shared_dispatch_reachable_variant_programs']
 req(set(reachable)=={'5','20'} and
     len(reachable['5']['lifetimes'])==1 and
     len(reachable['20']['lifetimes'])==2 and
     len(reachable['5']['animation_records'])==5 and
     len(reachable['20']['animation_records'])==8 and
     reachable['5']['allocations'][0]['visible_frame_u16']==4034 and
     [x['visible_frame_u16'] for x in reachable['20']['allocations']]==
      [3264,3856] and
     all(x['scheduler_rule'].startswith('collision allocation occurs')
         for x in reachable.values()),
     'Coffee Shop class-0x4e reachable variant program drift')
 req(deps['classification']=='SOURCE_CLOSED_IMPLEMENTATION_FIELDS','first-segment dependency classification drift')
 req(c08['classification']=='SOURCE_CLOSED_IMPLEMENTATION_FIELDS' and
     c08['spec_executable'] is True and
     c08['stage_spawn']['source_slot']=='0x00ffb200' and
     c08['stage_spawn']['record']['gate_u16']==816 and
     c08['stage_spawn']['record']['allocator_selector_u16']==4 and
     c08['stage_spawn']['accepted_witness']['global_gate_u16']==817 and
     c08['stage_spawn']['fixed_frame_substitute_forbidden'] is True and
     c08['parent']['record_type_u8']==20 and
     c08['parent']['class_u8']=='0x08' and
     c08['parent']['current_state_collision']['attack_record']['address']==
      '0x0002fc58' and
     c08['parent']['current_state_collision']['damage_s16']==25 and
     c08['parent']['current_state_collision']['health_after_clamp_s16']==-1 and
     c08['parent']['current_state_collision']['reaction_direction'] == {
      'source_body':{'first':'0x0001d0c8','last_exclusive':'0x0001d0fa',
       'sha256':hashlib.sha256(op[0x1d0c8:0x1d0fa]).hexdigest()},
      'field':'defender+0x4f:u8; distinct from visible facing at defender+0x0f',
      'attack_mode_s8':0,
      'rule':'zero attack mode preserves the initial 0x01d0c8 copy of attacker+0x0f:u8 into defender+0x4f:u8',
      'attacker_facing_u8':1,'result_u8':1,
      'consumer':'0x01d622 copies defender+0x4f:u8 to the allocated class-0x4e impact facing field',
      'visible_witness':{'impact_source_slot':'0x00ffb680',
       'impact_visible_frame_u16':2906,'impact_facing_u8':1}} and
     c08['parent']['drop']['rng_calls_u8']==1 and
     c08['parent']['drop']['seed_before']=='0x8be5' and
     c08['parent']['drop']['seed_after']=='0xa388' and
     c08['parent']['drop']['selected_subtype_u8']=='0x12' and
     c08['parent']['drop']['selector_source']=={
      'actor_offset_u8':'0x0c','value_u8':'0x1b',
      'lookup_base':'0x000bceaa','row_address':'0x000bd20a',
      'row_u8':[0x12]*32} and
     c08['parent']['drop']['audio']['command_u16']=='0x0077' and
     c08['parent']['state_sequence_u16']==
      [0,0x0200,0x0400,0x0402,0x0404,0x0604] and
     c08['parent']['post_drop_program']['state_transitions'][-1]=={
      'count':1,'first_frame':2947,'from':[0x0404,0x0200],
      'to':[0x0604,0x0300]} and
     c08['parent']['post_drop_program']['debris']['primary']
      ['x_velocity_s32']==0x00050000 and
     c08['parent']['post_drop_program']['debris']
      ['internal_coordinate_format'].startswith('two signed 24.8 trajectories') and
     c08['parent']['post_drop_program']['debris']
      ['visible_position_projection'].startswith('0x06d72e copies only') and
     c08['parent']['post_drop_program']['debris']['alternate']
      ['freeze_result']=={'x_fp_s32':0x05580000,
                          'y_fp_s32':0x01370000} and
     c08['parent']['post_drop_program']
      ['fixed_frame_substitute_forbidden'] is True and
     c08['pickup']['record_type_u8']==28 and
     c08['pickup']['class_u8']=='0x0a' and
     c08['pickup']['subtype_u8']=='0x12' and
     c08['pickup']['scheduler_order'].startswith('record-type-20') and
     c08['pickup']['initialization']['motion_substate_u16']==0x0002 and
     c08['pickup']['initialization']['velocity_acceleration_16_16']=={
      'x':-0x00038000,'y':0x00050000,'z':0,
      'y_acceleration':-0x00008000} and
     c08['pickup']['movement']['first_landing_result']=={
      'substate_u16':0x0004,'y_s16':317,
      'position_write':'replace only y_fp high word with ground_z and preserve the current fractional low word',
      'y_velocity_16_16':0x00010000,
      'y_acceleration_16_16':-0x00004000} and
     c08['pickup']['movement']['second_landing_result']=={
      'substate_u16':0x0200,'y_s16':317,
      'position_write':'replace only y_fp high word with ground_z and preserve the current fractional low word',
      'field5c_u8':0} and
     'including the substate-0 to substate-2 update' in
      c08['pickup']['movement']['animation_timer_rule'] and
     c08['pickup']['player_interaction']['action_u16']=='0x0e00' and
     c08['pickup']['player_interaction']['input_sample_rule'].startswith(
      'the eligible current-frame target/input guard latches pickup ownership') and
     c08['pickup']['player_interaction']['health_before_s16']==85 and
     c08['pickup']['player_interaction']['health_after_s16']==95 and
     c08['pickup']['player_interaction']['audio_edge']['command_u16']==
      '0x0206' and
     [x['animation_record'] for x in
      c08['pickup']['player_interaction']['presentation_records']]==
      ['0x0015fa04','0x0015fa14'] and
     c08['pickup']['collection']['first_absent_frame_u16']==3103 and
     c08['capture_identity']['baseline_byte_identical'] is True and
     len(c08['mutation_controls'])==24 and
     c08['fixed_frame_substitute_forbidden'] is True and
     c08['retained_gameplay_authority'] is False,
     'class-0x08 health-pickup implementation contract drift')
 req(c16['classification']=='SOURCE_CLOSED_IMPLEMENTATION_FIELDS' and
     c16['spec_executable'] is True and c16['record_type_u8']==16 and
     c16['class_u8']=='0x06' and c16['dispatch']=='0x03537e' and
     c16['state_sequence_u16']==[0,0x0200,0x0400,0x0600] and
     c16['spawn_owner']['outer_state_u16']=='0x0208' and
     c16['spawn_owner']['action_substate_u16']=='0x0e02' and
     c16['spawn_owner']['position_offset_s16']==[-59,64,0] and
     len(c16['spawn_owner']['parent_animation_records'])==11 and
     [item['branch_s16'] for item in
      c16['spawn_owner']['parent_animation_records']]==
     [0,0,0,1,0,2,0,3,0,0,-32768] and
     c16['initialization']['variant_motion_16_16']==[
      {'x_velocity_16_16':0x00080000,'x_acceleration_16_16':0xffffe000,
       'y_velocity_16_16':0x00040000,'y_acceleration_16_16':0xffffc000,
       'z_velocity_16_16':0},
      {'x_velocity_16_16':0x00074000,'x_acceleration_16_16':0xffffdc00,
       'y_velocity_16_16':0x0003c000,'y_acceleration_16_16':0xffffb000,
       'z_velocity_16_16':0},
      {'x_velocity_16_16':0x00068000,'x_acceleration_16_16':0xffffd800,
       'y_velocity_16_16':0x00038000,'y_acceleration_16_16':0xffff9000,
       'z_velocity_16_16':0}] and
     c16['initialization']['rng_calls_u8']==0 and
     len(c16['active_state']['animation_records'])==4 and
     len(c16['terminal_state']['animation_records'])==7 and
     c16['current_state_collision']['writer']=='0x01d5ee' and
     c16['current_state_collision']['attack_selector_u8']==1 and
     c16['current_state_collision']['attack_record']['address']=='0x0003589e' and
     c16['current_state_collision']['attack_record']['x_half_u8']==8 and
     c16['current_state_collision']['attack_record']['damage_selector_u8']==10 and
     c16['current_state_collision']['attack_record']['hit_value_u8']==20 and
     c16['current_state_collision']['player_hurt_selector_u8']==17 and
     c16['current_state_collision']['player_hurt_record']['address']=='0x0011ae8e' and
     c16['current_state_collision']['player_hurt_record']['x_half_u8']==20 and
     c16['current_state_collision']['route_character_damage_s16']==17 and
     len(c16['current_state_collision']['contacts'])==2 and
     c16['current_state_collision']['health_writes']==[
      {'source_frame':3263,'health_before_s16':95,'health_after_s16':78},
      {'source_frame':3855,'health_before_s16':68,'health_after_s16':51}] and
     len(c16['scene_lifetimes'])==9 and c16['rng_calls']==0 and
     c16['capture_identity']['byte_identical'] is True and
     c16['suppression_control']['suppression_count']>0 and
     len(c16['mutation_controls'])>=16 and
     c16['fixed_frame_substitute_forbidden'] is True and
     c16['retained_gameplay_authority'] is False,
     'class-0x1f type-16/class-0x06 projectile contract drift')
 req(c09['dispatch']=='0x06d926' and c09['state']=='0x0200' and len(c09['source_slots'])==2 and c09['first_segment_calls_before_class4e']==44 and c09['seed_after_first_call']=='0x44fb' and c09['seed_after_last_call']=='0x99e8' and c09['selector_table_u16']==[0,7,8,9,10,8,9,10] and [x['selector_u8'] for x in c09['animation_sequences']]==[0,7,8,9,10] and all(len(x['records'])==2 for x in c09['animation_sequences']) and c09['fixed_frame_substitute_forbidden'] is True,'class-0x09 first-segment dependency drift')
 req(c4e['dispatch']=='0x0927f6' and c4e['variant_u8']==4 and c4e['allocation_pop_order']==['0x00ffc500','0x00ffc480'] and c4e['scheduler_order']==['0x00ffc480','0x00ffc500'] and c4e['state_sequence_u16']==[0,0x0200,0x0400] and [(x['seed_before'],x['seed_after'],x['table_index']) for x in c4e['seed_transaction_by_scheduler_slot']]==[('0xcdb5','0x691e',28),('0x691e','0x3b59',24)] and c4e['seed_field_correction'].startswith('accepted RNG rows are pre-call seeds') and len(c4e['jitter_table_s16'])==8 and len(c4e['animation_records'])==5 and c4e['collision_or_damage_writes']==0 and c4e['fixed_frame_release_forbidden'] is True,'class-0x4e first-segment dependency drift')
 req(c4e['terminal_transition']['classification']==
     'SOURCE_CLOSED_IMPLEMENTATION_FIELDS' and
     c4e['terminal_transition']['source_slots']==
     ['0x00ffc480','0x00ffc500'] and
     c4e['terminal_transition']['before']==
     {'visible_frame_u16':2258,'state_u16':'0x0200',
      'animation_record':'0x000929f0','timer_u16':4095,
      'branch_s16':-32768} and
     c4e['terminal_transition']['after']==
     {'visible_frame_u16':2259,'state_u16':'0x0400',
      'animation_record':'0x000929f0','timer_u16':4094,
      'branch_s16':-32768} and
     c4e['terminal_transition']['mutation_control']==
     'reject state advance before terminal timer decrement',
     'class-0x4e terminal transition drift')
 req(c4e0['classification']=='SOURCE_CLOSED_IMPLEMENTATION_FIELDS' and
     c4e0['scene_lifetime_count_u16']==2 and
     c4e0['scene_actor_rows_u16']==22 and
     c4e0['first_collision']['source_frame']==2750 and
     c4e0['first_collision']['attacker_attack_record']=='0x00130b5c' and
     c4e0['first_collision']['defender_source_slot']=='0x00ff8380' and
     c4e0['first_collision']['health_before_s16']==101 and
     c4e0['first_collision']['health_after_s16']==91 and
     c4e0['allocation']['source_slot']=='0x00ffc300' and
     c4e0['allocation']['variant_field']['variant_u8']==0 and
     c4e0['allocation']['first_spawn_position_s16']==[1095,369,319] and
     c4e0['state0']['first_seed_before']=='0xeea3' and
     c4e0['state0']['first_seed_after']=='0xcb6e' and
     c4e0['state0']['first_table_offset_u8']==12 and
     c4e0['state0']['first_jitter_s16']==[4,4] and
     c4e0['state0']['first_visible_position_after_state0_s16']==[1099,373,319] and
     len(c4e0['active_state']['animation_records'])==3 and
     c4e0['release_state']['first_absent_frame']==2762 and
     c4e0['fixed_frame_substitute_forbidden'] is True and
     c4e0['retained_gameplay_authority'] is False,
     'class-0x4e variant-0 collision effect drift')
 req(c4e1['classification']=='SOURCE_CLOSED_IMPLEMENTATION_FIELDS' and
     c4e1['scene_lifetime_count_u16']==23 and
     c4e1['scene_actor_rows_u16']==253 and
     c4e1['first_collision']['attacker_attack_record']=='0x00030cd2' and
     c4e1['first_collision']['defender_source_slot']=='0x00ffa180' and
     c4e1['first_collision']['health_before_s16']==87 and
     c4e1['first_collision']['health_after_s16']==56 and
     c4e1['allocation']['scheduler_guard'].startswith(
      'record-type-24 release/dispatch') and
     c4e1['allocation']['source_slot']=='0x00ffbd80' and
     c4e1['allocation']['variant_u8']==1 and
     c4e1['allocation']['first_spawn_position_s16']==[717,336,309] and
     c4e1['allocation']['fixed_slot_reuse_presentation']=={
      'prior_visible_frame_u16':2306,'prior_class_u8':'0x45',
      'allocation_visible_frame_u16':2307,'allocated_class_u8':'0x4e',
      'rule':'0x0177da pops the released fixed slot without clearing fields not written by 0x01d622; retain the prior presentation until class-0x4e state 0 runs on its next scheduler visit',
      'retained_fields':['animation_record','animation_timer','animation_branch'],
      'animation_record':'0x0008df2c','assembly':'0x0008df96',
      'animation_timer_u16':4045,'animation_branch_s16':-32768,
      'state0_scheduler_frame_u16':2307,
      'state0_visible_frame_u16':2308,
      'state0_animation_record':'0x00092914',
      'state0_assembly':'0x00092c04'} and
     c4e1['state0']['first_seed_before']=='0x19c4' and
     c4e1['state0']['first_seed_after']=='0x4d11' and
     c4e1['state0']['first_jitter_s16']==[-4,0] and
      c4e1['state0']['first_visible_position_after_state0_s16']==[713,336,309] and
      len(c4e1['active_state']['animation_records'])==3 and
      psc['classification']=='SOURCE_CLOSED_IMPLEMENTATION_FIELDS' and
      psc['source_frame_u16']==2804 and
      psc['attack_selector_u8']==11 and
      psc['attack_record']['address']=='0x0011af76' and
      psc['attack_record']['x_half_u8']==88 and
      psc['class1f_target']['source_slot']=='0x00ffa240' and
      psc['class1f_target']['hurt_record']['address']=='0x00130ad4' and
      psc['class1f_target']['hurt_record']['x_center_s8']==-12 and
      psc['class1f_target']['hurt_record']['y_center_s8']==42 and
      psc['class1f_target']['hurt_record']['x_half_u8']==29 and
      psc['class1f_target']['hurt_record']['y_half_u8']==39 and
      psc['class1f_target']['hurt_record']['z_half_u8']==8 and
      psc['class1f_target']['damage_s16']==127 and
      psc['class1f_target']['health_after_clamp_s16']==-1 and
      psc['class1f_target']['impact_source_slot']=='0x00ffbf00' and
      psc['class1f_target']['source_ko']['entry_hold_ticks_u8']==3 and
      [x['animation_record'] for x in
       psc['class1f_target']['source_ko']['reaction_records']]==[
        '0x0012e214','0x0012e224','0x0012e234','0x0012e244'] and
      psc['class1f_target']['source_ko']['falling_record'][
       'animation_record']=='0x0012e254' and
      psc['class1f_target']['source_ko']['landing_record'][
       'animation_record']=='0x0012e268' and
      psc['class1f_target']['source_ko'][
       'launch_x_velocity_before_facing_16_16']==0x0003a000 and
      psc['class1f_target']['source_ko'][
       'launch_y_velocity_16_16']==0x000c0000 and
      psc['class1f_target']['source_ko'][
       'launch_y_acceleration_16_16']==-0x0000c000 and
      psc['class1f_target']['source_ko']['landing_hold_ticks_u8']==3 and
      psc['class1f_target']['source_ko']['removal_hold_ticks_u8']==60 and
      [x['source_slot'] for x in psc['record20_targets']]==
       ['0x00ffb300','0x00ffb380'] and
      psc['scheduler_order']==[
       'record-type-24 dispatch/release completes before collision allocation',
       'the source player attack registration traverses record-type-12 targets',
       'the same registration then traverses record-type-20 targets'] and
      psc['class1f_traversal_cadence']=={
       'max_damage_targets_per_frame_u8':1,
       'registration_retained_after_contact':True,
       'next_frame_resumes_after_ineligible_prior_targets':True,
       'coffee_shop_witnesses':[
        {'source_frame_u16':4394,'source_slot':'0x00ff9c40'},
        {'source_frame_u16':4395,'source_slot':'0x00ff9e80'}]} and
      psc['impact_allocation']['variant_u8']==1 and
      psc['capture_identity']['byte_identical'] is True and
      len(psc['mutation_controls'])==7 and
      c4e1['release_state']['first_absent_frame']==2318 and
     c4e1['collision_damage_authority'].startswith('shared collision writer') and
     c4e1['fixed_frame_substitute_forbidden'] is True and
     c4e1['retained_gameplay_authority'] is False,
     'class-0x4e variant-1 collision-effect contract drift')
 req(c4e10['classification']=='SOURCE_CLOSED_IMPLEMENTATION_FIELDS' and
     c4e10['scene_lifetime_count_u16']==5 and
     c4e10['scene_actor_rows_u16']==40 and
     c4e10['first_collision']['source_frame']==2362 and
     c4e10['first_collision']['attacker_attack_record']=='0x0002fc58' and
     c4e10['first_collision']['defender_source_slot']=='0x00ffa3c0' and
     c4e10['first_collision']['health_before_s16']==87 and
     c4e10['first_collision']['health_after_clamp_s16']==-1 and
     c4e10['allocation']['variant_field']=={
      'attack_record_offset_u8':8,'type':'u8','signed':False,
      'rule':'copy absolute signed byte at attack-record +0x08',
      'raw_u8':10,'variant_u8':10} and
     c4e10['allocation']['source_slot']=='0x00ffc200' and
     c4e10['allocation']['first_spawn_position_s16']==[833,325,311] and
     c4e10['state0']['first_seed_before']=='0x37cd' and
     c4e10['state0']['first_seed_after']=='0xa774' and
     c4e10['state0']['first_table_offset_u8']==20 and
     c4e10['state0']['first_jitter_s16']==[-4,-4] and
     c4e10['state0']['first_visible_position_after_state0_s16']==[829,321,311] and
     len(c4e10['active_state']['animation_records'])==6 and
     c4e10['active_state']['animation_records'][-1]['branch_s16']==-32768 and
     c4e10['release_state']['first_absent_frame']==2371 and
     c4e10['capture_identity']['byte_identical'] is True and
     len(c4e10['mutation_controls'])==5 and
     c4e10['fixed_frame_substitute_forbidden'] is True and
     c4e10['retained_gameplay_authority'] is False,
     'class-0x4e variant-10 collision-effect contract drift')
 req(c44['dispatch']=='0x08d9a4' and c44['source_slot']=='0x00ffc580' and c44['state_sequence_u16']==[0x0200,0x0400,0x0402,0x0404] and c44['state0_presentation_actor']=={'coordinate_mode_u8':0,'palette_u8':0,'facing_u8':0,'object_or_u16':'0x8000','object_or_writer_pc':'0x08d9d8','object_or_write_frame':2072,'object_or_write_mask':'0x0000ffff','zero_fields_source':'accepted zero-initialized type-24 record; generic allocation writes preserve coordinate mode, palette and facing at zero'} and len(c44['animation_records'])==2 and c44['guard_clear_frame']==2250 and c44['second_player_origin_command_frame']==2255 and c44['rng_calls']==0 and c44['collision_or_damage_writes']==0 and c44['fixed_frame_guard_reset_forbidden'] is True,'class-0x44 command-guard dependency drift')
 req(c43['classification']=='SOURCE_CLOSED_IMPLEMENTATION_FIELDS' and
     c43['dispatch']=='0x08ce44' and c43['spawn_routine']=='0x08cde6' and
     c43['record_type_u8']==24 and c43['class_u8']=='0x43' and
     c43['variant_u8']==0 and
     c43['allocation_pop_order_by_group'][0]==
      ['0x00ffbd80','0x00ffc300','0x00ffc380','0x00ffc180'] and
     c43['source_slots_scheduler_order_by_spawn'][0]==
      ['0x00ffb680','0x00ffb900','0x00ffbb00','0x00ffbd80',
       '0x00ffbf00','0x00ffc180','0x00ffc300','0x00ffc380'] and
     c43['spawn_owner']['caller_pc']=='0x06b3a8 then 0x06b3ae' and
     c43['spawn_owner']['groups_u8']==2 and
     c43['spawn_owner']['attempts_per_group_u8']==4 and
     c43['state0']['rng_calls_u8']==7 and
     c43['state0']['animation_selector_table_u8']==
      [5,6,7,15,5,6,7,15,0,1,2,3,4,8,9,10,
       11,12,13,14,0,1,2,3,4,8,9,10,11,12,13,14] and
     len(c43['state0']['animation_sequences'])==16 and
     len(c43['state0']['motion_table'])==8 and
     c43['state0']['motion_table'][0]=={
      'primary_x_velocity_s16':0,'primary_y_velocity_s16':2048,
      'primary_x_acceleration_s16':0,'primary_y_acceleration_s16':-96,
      'alternate_x_velocity_s16':896,'alternate_y_velocity_s16':1792,
      'alternate_x_acceleration_s16':0,
      'alternate_y_acceleration_s16':-96} and
     c43['rng_calls_total_u16']==112 and len(c43['lifetimes'])==16 and
     c43['state_0x0200']['landing_guard'].startswith(
      'set channel landing bit when unsigned channel_y') and
     c43['collision_or_damage_writes']==0 and c43['audio_writes']==0 and
     c43['route_or_camera_writes']==0 and
     len(c43['mutation_controls'])>=15 and
     c43['fixed_frame_substitute_forbidden'] is True and
     c43['retained_gameplay_authority'] is False,
     'class-0x43 Coffee Shop implementation contract drift')
 req(c45['classification']=='SOURCE_CLOSED_IMPLEMENTATION_FIELDS' and
     c45['dispatch']=='0x08dc1c' and c45['record_type_u8']==24 and
     c45['class_u8']=='0x45' and
     len(c45['source_slots_scheduler_order'])==28 and
     c45['source_slots_scheduler_order'][0]=='0x00ffb680' and
     c45['source_slots_scheduler_order'][-1]=='0x00ffc400' and
     c45['allocation_pop_order']==list(reversed(
         c45['source_slots_scheduler_order'])) and
     c45['spawn_owner']['source_slot']=='0x00ffc580' and
     c45['spawn_owner']['spawn_frame']==2253 and
     c45['state_sequence_u16']==[0,0x0200,0x0400] and
     c45['state0']['rng_calls_u8']==7 and
     len(c45['state0']['animation_selector_table_u8'])==32 and
     len(c45['state0']['animation_records'])==5 and
     len(c45['state0']['motion_table'])==8 and
     c45['state0']['motion_table'][0]=={
      'primary_x_velocity_s16':0,'primary_y_velocity_s16':2048,
      'primary_y_acceleration_s16':-96,
      'alternate_x_velocity_s16':-896,
      'alternate_y_velocity_s16':2048,
      'alternate_y_acceleration_s16':-96} and
     c45['rng_calls_total_u16']==196 and
     c45['collision_or_damage_writes']==0 and c45['audio_writes']==0 and
     c45['route_or_camera_writes']==0 and
     c45['fixed_frame_substitute_forbidden'] is True and
     c45['retained_gameplay_authority'] is False,
     'class-0x45 Coffee Shop implementation contract drift')
 req(c47['classification']=='SOURCE_CLOSED_IMPLEMENTATION_FIELDS' and
     c47['dispatch']=='0x08eb86' and c47['spawn_routine']=='0x08eb1c' and
     c47['record_type_u8']==24 and c47['class_u8']=='0x47' and
     c47['variant_u8']==0 and
     c47['source_slots_scheduler_order']==
      ['0x00ffbd80','0x00ffc180','0x00ffc200','0x00ffc380'] and
     c47['allocation_pop_order']==
      ['0x00ffc380','0x00ffc200','0x00ffc180','0x00ffbd80'] and
     c47['spawn_owner']['source_slot']=='0x00ffb300' and
     c47['spawn_owner']['caller_pc']=='0x06b61a' and
     c47['spawn_owner']['attempts_u16']==4 and
     c47['state_sequence_u16']==[0,0x0200,0x0400] and
     c47['state0']['rng_calls_u8']==7 and
     len(c47['state0']['animation_selector_table_u8'])==32 and
     len(c47['state0']['animation_records'])==9 and
     len(c47['state0']['motion_table'])==8 and
     c47['state0']['motion_table'][0]=={
      'primary_x_velocity_s16':0,'primary_y_velocity_s16':2048,
      'primary_y_acceleration_s16':-96,
      'alternate_x_velocity_s16':896,
      'alternate_y_velocity_s16':1792,
      'alternate_y_acceleration_s16':-96} and
     c47['rng_calls_total_u16']==28 and len(c47['lifetimes'])==4 and
     c47['collision_or_damage_writes']==0 and c47['audio_writes']==0 and
     c47['route_or_camera_writes']==0 and
     len(c47['mutation_controls'])>=13 and
     c47['fixed_frame_substitute_forbidden'] is True and
     c47['retained_gameplay_authority'] is False,
     'class-0x47 Coffee Shop child-presentation contract drift')
 req(special['classification']=='SOURCE_CLOSED_IMPLEMENTATION_FIELDS' and
     special['player_dispatch_entry']=='0x023132' and
     special['player_active_handler']=='0x02314e' and
     special['action_writer']=='0x01a89a' and
     special['allocation_routine']=='0x0177da' and
     special['release_routine']=='0x0177f0' and
     special['source_audio_commands_u16']==[0x0091,0x0096] and
     special['health_cost_s16']==6 and
     special['rng_calls']==0 and
     special['collision_or_damage_writes']==0 and
     special['fixed_frame_substitute_forbidden'] is True and
     special['retained_gameplay_authority'] is False,
     'Predator special type-24 owner contract drift')
 req(c4b['record_type_u8']==24 and c4b['class_u8']=='0x4b' and
     c4b['dispatch']=='0x08f86e' and
     c4b['state_sequence_u16']==[0,0x0200,0x0400] and
     c4b['state0']['position_writes']==
      ['z -= 1','y += 62','x += facing-adjusted 8'] and
     c4b['state_0x0200']['terminal_guard']==
      'advance to 0x0400 when player+0x5c_u8 != 0 OR player+0x25_u8 != 0; zero animation event continues the active update' and
     c4b['state_0x0200']['owner_contact_lifetime'].startswith(
      'player writer 0x01986a clears') and
     c4b['state_0x0200']['coffee_shop_wrap_witness']=={
      'terminal_record_frame_u16':2835,'wrapped_record_frame_u16':2836,
      'wrapped_animation_record':'0x0008f8e0'} and
     len(c4b['state0']['animation_records'])==32 and
     [x['branch_s16'] for x in c4b['state0']['animation_records'][:16]]==
      list(range(16)) and
     c4b['state0']['animation_records'][-1]['branch_s16']==-32753 and
     c4b['coffee_shop_first_lifetime']['first_frame']==2805 and
     c4b['scene_actor_rows_u16']==244,
     'class-0x4b Predator special presentation contract drift')
 req(c3d['record_type_u8']==24 and c3d['class_u8']=='0x3d' and
     c3d['dispatch']=='0x0887c8' and
     c3d['state_sequence_u16']==[0,0x0200,0x0400] and
     c3d['variant_rule']==
      'copy current class-0x4b animation branch low byte' and
     c3d['unwritten_field_retention']=={
      'rule':'source type-24 allocation and 0x023220 writer do not clear or write actor+0x14_s16; preserve the prior fixed-pool slot y field',
      'first_source_slot':'0x00ffbb00','prior_actor_class_u8':'0x49',
      'prior_last_frame_u16':2471,'prior_y_s16':343,
      'first_class3d_frame_u16':2805,'first_class3d_y_s16':343} and
     len(c3d['state0']['animation_records'])==9 and
     c3d['state0']['animation_records'][-1]['branch_s16']==-32768 and
     len(c3d['state_0x0200']['movement_offsets_s16'])==16 and
     c3d['state_0x0200']['movement_offsets_s16'][0]==[-61,-13] and
     c3d['state_0x0200']['movement_offsets_s16'][8]==[61,13] and
     c3d['state_0x0200']['movement_rule'].endswith(
      'variant=(variant+8)&0x0f') and
     c3d['coffee_shop_first_lifetime']['first_frame']==2805 and
     c3d['scene_actor_rows_u16']==4032,
     'class-0x3d Predator special effect contract drift')
 type36=r['coffee_shop_type36_presentation']
 req(type36['classification']=='SOURCE_CLOSED_IMPLEMENTATION_FIELDS' and
     type36['capture_identity']['byte_identical'] is True and
     type36['capture_identity']['spawn_context_byte_identical'] is True and
     type36['pool']=={'record_type_u8':36,'base':'0xffd280',
      'capacity':64,'stride_u16':0x40,'scheduler':'0x01bd48'} and
     type36['required_pairs']==4 and type36['closed_pairs']==4 and
     [(x['class'],x['lifetime_count']) for x in type36['classes']]==
      [('0x03',50),('0x04',15),('0x05',4),('0x0e',16)] and
     all(x['classification']=='SOURCE_CLOSED_PRESENTATION' and
         x['semantic_name']=='UNKNOWN' and x['animation_records'] and
         x['source_spawn_contexts'] and
         sum(y['count'] for y in x['source_spawn_contexts'])==x['lifetime_count'] and
         all(y['route_state_u16']==4 and
             y['allocation_rule'].startswith('pop next free type-36')
             for y in x['source_spawn_contexts']) and
         x['rng_calls']==0 and x['direct_collision_damage_writes']==0 and
         x['direct_audio_writes']==0 and x['direct_route_camera_writes']==0 and
         x['counterfactual']['suppressed_writes']==x['lifetime_count'] and
         x['counterfactual']['remaining_target_actor_rows']==0 and
         x['counterfactual']['actor_population_difference'] is True and
         x['fixed_frame_substitute_forbidden'] is True
         for x in type36['classes']) and
     type36['retained_gameplay_authority'] is False,
     'Coffee Shop type-36 presentation contract drift')
 scene_components=r['coffee_shop_scene_component_identities']
 class0f_component=next(x for x in scene_components['components']
                        if x['type']==20 and x['class']=='0x0f')
 class0f_contract=class0f_component['implementation_contract']
 class0a_component=next(x for x in scene_components['components']
                        if x['type']==24 and x['class']=='0x0a')
 class0a_contract=class0a_component['implementation_contract']
 req(scene_components['classification']=='SOURCE_CLOSED_IDENTITY' and
     scene_components['capture_identity']['byte_identical'] is True and
     scene_components['capture_identity']['implementation_detail_byte_identical'] is True and
     scene_components['identified_pairs']==9 and
     scene_components['unidentified_pairs']==0 and
     scene_components['semantic_names_inferred'] is False and
     [(x['type'],x['class'],x['lifetime_count'])
      for x in scene_components['components']]==
     [(20,'0x01',2),(20,'0x02',2),(20,'0x0f',1),(24,'0x05',1),
      (24,'0x0a',2),(24,'0x20',1),(28,'0x00',1),(28,'0x0c',1),
      (28,'0x0e',1)] and
     all(x['classification']=='SOURCE_CLOSED_IDENTITY' and
         x['semantic_role']=='UNKNOWN' and x['state_substate_contexts'] and
         x['animation_records'] and
         0<x['suppression_control']['removed_lifetimes']<=x['lifetime_count'] and
          x['implementation_status']=='BLOCKED_MISSING_SPEC_FIELDS' and
          x['fixed_frame_substitute_forbidden'] is True
          for x in scene_components['components'][2:]
          if not ((x['type']==20 and x['class']=='0x0f') or
                  (x['type']==24 and x['class']=='0x0a') or
                  (x['type']==24 and x['class']=='0x20'))) and
     next(x for x in scene_components['components']
          if x['type']==20 and x['class']=='0x0f')['classification']==
      'SOURCE_CLOSED_IMPLEMENTATION_FIELDS' and
     next(x for x in scene_components['components']
          if x['type']==20 and x['class']=='0x0f')['implementation_status']==
      'SPEC_EXECUTABLE' and
     next(x for x in scene_components['components']
          if x['type']==24 and x['class']=='0x20')['classification']==
      'SOURCE_CLOSED_IMPLEMENTATION_FIELDS' and
     next(x for x in scene_components['components']
          if x['type']==24 and x['class']=='0x20')['implementation_status']==
      'SPEC_EXECUTABLE' and
     class0a_component['classification']==
      'SOURCE_CLOSED_IMPLEMENTATION_FIELDS' and
     class0a_component['implementation_status']=='SPEC_EXECUTABLE' and
     class0a_component['semantic_role']==
      'SOURCE_PRESENTATION_FIXED_POOL_RESIDENT' and
     class0a_contract['source_body']=={
      'first':'0x00077ccc','last_exclusive':'0x00077d26',
      'sha256':'43f6bb2d20750b41ec6e03b6eed22488fee5db651d0680ad2c600e2b53ac0089'} and
     class0a_contract['dispatch_table']['offsets_s16']==[8,30,72] and
     class0a_contract['animation_selector']['table_sha256']==
      '3ab654d4e8b0c544fed45f5fe188549b2ecd20addb7dee9a415157ea5727ae66' and
     class0a_contract['scheduler_cadence']['exception_count_u8']==70 and
     class0a_contract['scheduler_cadence']['dispatch_count_u16']==3597 and
     class0a_contract['scheduler_cadence']['classification']==
      'SOURCE_CAPTURE_PROJECTION_ONLY' and
     [x['variant_u8'] for x in
      class0a_contract['allocation_initialization']['lifetimes']]==
      ['0x26','0x06'] and
     class0a_contract['direct_effects']=={
      'rng_calls_u8':0,'collision_memberships_u8':0,
      'health_or_damage_writes_u8':0,'audio_transactions_u8':0,
      'route_camera_load_writes_u8':0,
      'rule':'presentation-only source actors still own fixed-pool occupancy and lifecycle; downstream allocation identity must not omit them'} and
     class0a_contract['counterfactual']['production_authority'] is False and
     all(x['different'] for x in
         class0a_contract['counterfactual']['downstream_differences'].values()) and
     class0a_contract['retained_gameplay_authority'] is False and
     next(x for x in scene_components['components']
          if x['type']==24 and x['class']=='0x20')['implementation_contract']
      ['retained_gameplay_authority'] is False and
     next(x for x in scene_components['components']
          if x['type']==24 and x['class']=='0x20')['implementation_contract']
      ['terminal_guard']==
       'negative actor+0x24 animation event advances state 0x0200 to 0x0400' and
     all(x['classification']=='SOURCE_CLOSED_IMPLEMENTATION_FIELDS' and
         x['implementation_status']=='SPEC_EXECUTABLE' and
         x['semantic_role']!='UNKNOWN' and
         x['implementation_contract'] is not None and
         len(x['implementation_contract']['stage_records'])==2 and
         len(x['implementation_contract']['stage_spawn_guard']
              ['camera_sample_order']['records'])==2 and
         x['implementation_contract']['stage_spawn_guard']
          ['camera_sample_order']['rule'].startswith(
           'compare against the camera position projected for the current source frame') and
         0<x['suppression_control']['removed_lifetimes']<=x['lifetime_count'] and
         x['implementation_contract']['rng']==
          {'calls':0,'consumption_order':[]} and
         len(x['implementation_contract']['mutation_controls'])>=10 and
         x['fixed_frame_substitute_forbidden'] is True
         for x in scene_components['components'][:2]) and
     scene_components['components'][0]['implementation_contract']
      ['source_body']['sha256']==
      '6c1a8399fc4fb09a16ada8fb19265dc8c984392e3037ad3f4addcbb9bc4704e8' and
     [(x['camera_threshold_u16'],x['class_u8'],x['variant_u8']) for x in
      scene_components['components'][0]['implementation_contract']
       ['stage_records']]==[(512,1,0),(672,1,1)] and
     scene_components['components'][0]['implementation_contract']
      ['audio_transactions'][0]['command_u16']=='0x006d' and
     scene_components['components'][0]['implementation_contract']
      ['audio_transactions'][1]['command_u16']=='0x0139' and
     scene_components['components'][1]['implementation_contract']
      ['source_body']['sha256']==
      '7c13ff10db6bb02c95b96a60a7d2f3d45f4179f139edaa0e8c442d3fe5b0b3bd' and
     [(x['camera_threshold_u16'],x['class_u8'],x['variant_u8']) for x in
      scene_components['components'][1]['implementation_contract']
       ['stage_records']]==[(512,2,0),(736,2,0)] and
     scene_components['components'][1]['implementation_contract']
      ['collision_damage']['current_state_writer']==
      '0x01d590 then signed clamp 0x01d598' and
     scene_components['components'][1]['implementation_contract']
      ['collision_damage']['attack_record']=='0x0011af76' and
     scene_components['components'][1]['implementation_contract']
      ['collision_damage']['reaction_delay']['value_u16']==3 and
     scene_components['components'][1]['implementation_contract']
      ['collision_damage']['reaction_delay']['coffee_shop_witness']=={
       'bound_frame_u16':2806,'retained_through_frame_u16':2808,
       'first_animation_decrement_frame_u16':2809,
       'retained_animation_timer_u16':4095} and
     scene_components['components'][1]['implementation_contract']
      ['collision_damage']['attack_box']==
      {'address':'0x0011af76','x_center_s8':0,'y_center_s8':48,
       'x_half_u8':88,'y_half_u8':48,'z_center_s8':0,'z_half_u8':40,
       'hit_value_u8':3,'knockback_mode_s8':1} and
     scene_components['components'][1]['implementation_contract']
      ['collision_damage']['hurt_record']==
      {'address':'0x0006b6f4','record_bytes':'08400820fc04ff00',
       'x_center_s8':8,'y_center_s8':64,'x_half_u8':8,'y_half_u8':32,
       'z_center_s8':-4,'z_half_u8':4,'flags_u16':'0xff00'} and
     scene_components['components'][1]['implementation_contract']
      ['collision_damage']['reaction_direction']['result_u8']==1 and
     scene_components['components'][1]['implementation_contract']
      ['collision_damage']['reaction_direction']['source_body']['sha256']==
      hashlib.sha256(op[0x1d0c8:0x1d0fa]).hexdigest() and
     scene_components['components'][1]['implementation_contract']
      ['collision_damage']['reaction_direction']['evidence']['byte_identical']
      is True and
     scene_components['components'][1]['implementation_contract']
      ['scheduler_phase_evidence']['byte_identical'] is True and
     scene_components['components'][1]['implementation_contract']
      ['scheduler_phase_evidence']['phase_owner']['byte_identical'] is True and
     scene_components['components'][1]['implementation_contract']
      ['scheduler_phase_evidence']['phase_owner']['indirect_caller_pc']==
      '0x01bc6e' and
     scene_components['components'][1]['implementation_contract']
      ['scheduler_phase_evidence']['class02_source_update_cadence']
      ['exceptions_sha256']==
      'edef59d16bb596ec4b9a583eeb19052e125c371f2b72bc61ffb3b2f7410728da' and
     hashlib.sha256(canon(scene_components['components'][1]
      ['implementation_contract']['scheduler_phase_evidence']
      ['class02_source_update_cadence']['exceptions'])).hexdigest()==
     scene_components['components'][1]['implementation_contract']
      ['scheduler_phase_evidence']['class02_source_update_cadence']
      ['exceptions_sha256'] and
     len(scene_components['components'][1]['implementation_contract']
      ['scheduler_phase_evidence']['class02_source_update_cadence']
      ['exceptions'])==113 and
     scene_components['components'][1]['implementation_contract']
      ['scheduler_phase_evidence']['record20_exit_prefix_scheduler']
      ['byte_identical'] is True and
     scene_components['components'][1]['implementation_contract']
      ['scheduler_phase_evidence']['record20_exit_prefix_scheduler']
      ['source_phase_split_after_slot']=='0x00ffb500' and
     scene_components['components'][1]['implementation_contract']
      ['scheduler_phase_evidence']['record20_exit_prefix_scheduler']
      ['suffix_first_slot']=='0x00ffb600' and
     [(row['program_tick_u8'],row['display_ticks_u8'],row['updates_u8'])
      for row in scene_components['components'][1]['implementation_contract']
       ['scheduler_phase_evidence']['record20_exit_prefix_scheduler']
       ['groups']]==[(0,5,1),(5,10,3),(15,1,4),(16,15,3),
                     (31,1,4),(32,7,3),(39,1,4),(40,6,3),
                     (46,1,4),(47,6,3),(53,1,4),(54,4,3),
                     (58,1,4),(59,5,3),(64,6,4),(70,1,1)] and
     scene_components['components'][1]['implementation_contract']
      ['scheduler_phase_evidence']['out_of_camera_animation_retention']
      ['animation_timer_u16']==4095 and
     scene_components['components'][1]['implementation_contract']
      ['scheduler_phase_evidence']['camera_entry_animation_rebind']
      ['predicate_transition_source_frame_u16']==2639 and
     scene_components['components'][1]['implementation_contract']
      ['scheduler_phase_evidence']['camera_entry_animation_rebind']
      ['entry_samples']==[
       {'source_frame_u16':2638,'in_camera_bounds_u8':0,
        'animation_timer_u16':4095,'camera_x_u16':751},
       {'source_frame_u16':2639,'in_camera_bounds_u8':0,
        'animation_timer_u16':4095,'camera_x_u16':752},
       {'source_frame_u16':2640,'in_camera_bounds_u8':1,
        'animation_timer_u16':4095,'camera_x_u16':753},
       {'source_frame_u16':2641,'in_camera_bounds_u8':1,
        'animation_timer_u16':4094,'camera_x_u16':754}] and
     [x['dispatch_count_u8'] for x in
      scene_components['components'][1]['implementation_contract']
       ['scheduler_phase_evidence']['class02_dispatch_counts']]==
      [1,1,2,2,1] and
     [x['dispatch_count_u8'] for x in
      scene_components['components'][1]['implementation_contract']
       ['scheduler_phase_evidence']['controller_dispatch_counts']]==
      [0,1,3,1,1] and
     scene_components['components'][1]['implementation_contract']
      ['audio_transactions'][0]['command_u16']=='0x0077' and
     next(x for x in scene_components['components']
          if x['type']==20 and x['class']=='0x0f')['implementation_contract']
      ['source_body']=={
       'first':'0x0006ed3e','last_exclusive':'0x0006ee42',
       'sha256':'d3ae68e588d84042b1f937279588d4974bc1bbd64778c8e77625735b859ba8de'} and
     [(x['address'],x['offsets_s16']) for x in
      class0f_contract['dispatch_tables']]==[
       ('0x0006ed4a',[8,64,112,242]),('0x0006edb4',[4,6]),
       ('0x0006edfe',[10,4])] and
     next(x for x in scene_components['components']
          if x['type']==20 and x['class']=='0x0f')['implementation_contract']
      ['stage_records'][0]['record_sha256']==
       '4cbbe2b63951094c908d42f83436d66f29177b96257a190304549889eb6379e1' and
     next(x for x in scene_components['components']
          if x['type']==20 and x['class']=='0x0f')['implementation_contract']
      ['stage_spawn_guard']['camera_sample_order']['records']==[
       {'address':'0x0015c1b8','writer_source_frame_u16':2672,
        'camera_x_u16':817,'first_actor_visible_frame_u16':2673,
        'source_slot':'0x00ffb100'}] and
     [x['animation_record'] for x in next(x for x in
       scene_components['components'] if x['type']==20 and
       x['class']=='0x0f')['implementation_contract']['initialization']
       ['animation_records']]==[
        '0x0006ee4a','0x0006ee5e','0x0006ee72'] and
     [(x['hurt_selector_u8'],x['attack_selector_u8']) for x in next(x for x in
       scene_components['components'] if x['type']==20 and
       x['class']=='0x0f')['implementation_contract']['initialization']
       ['animation_records']]==[(1,1),(2,2),(0,3)] and
     next(x for x in scene_components['components']
          if x['type']==20 and x['class']=='0x0f')['implementation_contract']
      ['state_program']['0x0202']['entry'].endswith('0x0006edba') and
     class0f_contract['state_program']['0x0200']['delay_guard'].startswith(
      'if delay_timer:u8 is nonzero, predecrement') and
     class0f_contract['state_program']['0x0400']['selector_1']['allocation']
      ['variant_iteration_s8']==[3,2,1,0] and
     class0f_contract['state_program']['0x0400']['selector_1']['allocation']
      ['observed_source_slots_by_variant']=={
       '0':'0x00ffb900','1':'0x00ffbf00','2':'0x00ffbb00',
       '3':'0x00ffc300'} and
     class0f_contract['state_program']['0x0400']['selector_1']['allocation']
      ['child_rng_calls_u8']==28 and
     next(x for x in scene_components['components']
          if x['type']==20 and x['class']=='0x0f')['implementation_contract']
      ['state_program']['0x0400']['selector_0']['first_source_effect']=={
       'source_frame_u16':2675,'source_slot':'0x00ffcd80',
       'record_type_u8':28,'class_u8':9,'active_u8':2,
       'x_s16':1301,'y_s16':320,'z_s16':232,
       'next_animation_record':'0x000a34da'} and
     [x['command_u16'] for x in next(x for x in
       scene_components['components'] if x['type']==20 and
       x['class']=='0x0f')['implementation_contract']['audio_transactions']]==
      ['0x0077','0x0142'] and
     all(x['argument1_u32']=='0x00002000' and
         x['source_caller']=='0x00002630' for x in
         class0f_contract['audio_transactions']) and
     class0f_contract['collision_damage']['current_state_caller']==
      '0x0001d87a' and
     class0f_contract['collision_damage']['direct_damage_writes_u8']==0 and
     [(x['hurt_u8'],x['attack_u8']) for x in
       class0f_contract['collision_damage']['animation_selectors']]==
      [(1,1),(2,2),(0,3)] and
     next(x for x in scene_components['components']
          if x['type']==20 and x['class']=='0x0f')['implementation_contract']
      ['rng']['direct_calls']==0 and
     next(x for x in scene_components['components']
          if x['type']==20 and x['class']=='0x0f')['implementation_contract']
      ['counterfactual']['byte_identical'] is True and
     class0f_contract['counterfactual']['production_authority'] is False and
     all(v['different'] for v in next(x for x in
       scene_components['components'] if x['type']==20 and
       x['class']=='0x0f')['implementation_contract']['counterfactual']
       ['downstream_differences'].values()) and
     next(x for x in scene_components['components']
          if x['type']==20 and x['class']=='0x0f')['implementation_contract']
      ['retained_gameplay_authority'] is False and
     len(class0f_contract['mutation_controls'])>=16 and
     next(x for x in scene_components['components']
          if x['type']==20 and x['class']=='0x0f')['implementation_contract']
      ['fixed_frame_substitute_forbidden'] is True,
     'Coffee Shop remaining component identity drift')
 teardown=scene_components['components'][1]['implementation_contract'][
  'scheduler_phase_evidence']['record20_exit_prefix_scheduler'][
   'route_teardown_dispatch_guard']
 req(teardown['classification']=='SOURCE_CLOSED_IMPLEMENTATION_FIELDS' and
     teardown['transition_source_frame_u16']==5524 and
     teardown['prior_route_state_u16']==6 and
     teardown['route_teardown_state_u16']==0 and
     teardown['last_source_dispatch_frame_u16']==5523 and
     teardown['freeze_frame_range_inclusive_u16']==[5524,5550] and
     teardown['central_release_source_frame_u16']==5551 and
     teardown['active_source_slots']==[
      '0x00ffb100','0x00ffb180','0x00ffb300','0x00ffb480',
      '0x00ffb500','0x00ffb600'] and
     len(teardown['frozen_fields'])==9 and
     teardown['source_dispatch_count_u16']==0 and
     teardown['guard'].startswith(
      'route_state == 0 and exit_route_updates != 0') and
     teardown['transition_dispatch'].startswith(
      'exit_route_updates == 0 permits') and
     teardown['fixed_frame_substitute_forbidden'] is True,
     'Coffee Shop record-20 route-teardown guard drift')
 req(len(r['phantom_census_aliases'])==4 and all(x['classification']=='NOT_REQUIRED_FOR_ROUND1' and x['scheduler_dispatch'] is None for x in r['phantom_census_aliases']),'phantom alias classification drift');req(all(v==0 for k,v in r['coverage'].items() if k.startswith('orphan_')) and r['coverage']['invalid_zero_removal_controls_accepted']==0,'aux zero gap drift');req(r['correction_record']['invalid_controls_removed_zero_actors'] is True and r['correction_record']['accepted_controls_all_remove_actors'] is True and r['negative_controls']['zero_removal_suppression_rejected'] is True,'invalid suppression admitted');req(r['protected_boundaries']['production_runtime_writes']==0 and r['protected_boundaries']['yaba_runs']==0 and r['protected_boundaries']['physical_saturn']=='UNRUN' and r['protected_boundaries']['spec02_active'] is False,'protected boundary drift')

if __name__=='__main__':
 report=build();OUT.write_bytes(canon(report));print('ORACLE-11 auxiliary authority: SOURCE_CLOSED; 12 dispatched pairs closed, 4 census aliases NOT_REQUIRED, zero orphans')
