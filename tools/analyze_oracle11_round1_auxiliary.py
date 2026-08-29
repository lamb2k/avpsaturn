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
OPCODES=ROOT/'.deps/mame/actorprobe/decrypted_opcodes_2m.bin';PROGRAM=ROOT/'.deps/mame/actorprobe/decrypted_program_2m.bin'
OUT=ROOT/'data/oracle11_round1_auxiliary_authority.json'
TYPE36_A=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs15a';TYPE36_B=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs15b'
TYPE36_CONTEXT_A=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs16a'
TYPE36_CONTEXT_B=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs16b'
SCENE_COMPONENT_A=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs17a'
SCENE_COMPONENT_B=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs17b'
SCENE_COMPONENT_DETAIL_A=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs27a'
SCENE_COMPONENT_DETAIL_B=ROOT/'.deps/mame/oracle11_progression_lifecycle_cs27b'
TYPE16_TRACE_A=ROOT/'.deps/mame/reimplement13_type16_trace_g'
TYPE16_TRACE_B=ROOT/'.deps/mame/reimplement13_type16_trace_h'
TYPE16_ATTACK_A=ROOT/'.deps/mame/reimplement13_type16_collision_a/attack_table.bin'
TYPE16_ATTACK_B=ROOT/'.deps/mame/reimplement13_type16_collision_b/attack_table.bin'
TYPE16_HURT_A=ROOT/'.deps/mame/reimplement13_type16_hurt_a/player_hurt_window.bin'
TYPE16_HURT_B=ROOT/'.deps/mame/reimplement13_type16_hurt_b/player_hurt_window.bin'
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
 return {'address':f'0x{address:08x}','x_center_s8':int.from_bytes(record[0:1],'big',signed=True),'y_center_s8':int.from_bytes(record[1:2],'big',signed=True),'x_half_u8':record[2],'y_half_u8':record[3],'z_center_s8':int.from_bytes(record[4:5],'big',signed=True),'z_half_u8':record[5],'knockback_mode_s8':int.from_bytes(record[6:7],'big',signed=True),'damage_selector_u8':record[9],'hit_value_u8':record[14],'record_sha256':hashlib.sha256(record).hexdigest()}

def hurt_box(record,address):
 req(len(record)==8,f'hurt record {address:08x} size drift')
 return {'address':f'0x{address:08x}','x_center_s8':int.from_bytes(record[0:1],'big',signed=True),'y_center_s8':int.from_bytes(record[1:2],'big',signed=True),'x_half_u8':record[2],'y_half_u8':record[3],'z_center_s8':int.from_bytes(record[4:5],'big',signed=True),'z_half_u8':record[5],'record_sha256':hashlib.sha256(record).hexdigest()}

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
  'current_state_collision':{'scheduler':'record-type-16 attackers against player after actor movement/presentation selection','writer':'0x01d5ee','attack_table':'0x00035882','attack_selector_u8':1,'attack_record':attack,'player_table':'0x0011ae02','player_hurt_record':hurt,'contact_guard':'current animation attack selector 1 resolves table record 0x03589e; that record and current player hurt record overlap in x/y/z under shared 0x01d4aa collision arithmetic','damage_selector_u8':10,'route_character_damage_s16':17,'hit_value_u8':20,'contacts':contacts,'health_writes':[{'source_frame':int(row['frame']),'health_before_s16':int(row['health_before'],16),'health_after_s16':int(row['health_after'],16)} for row in damage]},
  'scene_lifetimes':lifetimes,'rng_calls':0,
  'capture_identity':{'collision_completion_a':identity_a,
   'collision_completion_b':identity_b,'byte_identical':True,
   'attack_table_sha256':sha(TYPE16_ATTACK_A),
   'player_hurt_window_sha256':sha(TYPE16_HURT_A)},
  'mutation_controls':['wrong parent state','wrong animation event branch',
   'fixed-frame spawn','wrong variant','wrong motion row','wrong facing sign',
   'wrong movement order','wrong state guard','wrong animation record',
   'wrong attack selector','wrong attack box','wrong player hurt box',
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
 detail_writes=rows(SCENE_COMPONENT_DETAIL_A/
                    'coffee_shop_component20_writes.tsv')
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
   'timer_u16':0}]}
 observed_spawns={
  '0x0015c108':(2072,'0x00ffb600'),
  '0x0015c128':(2072,'0x00ffb580'),
  '0x0015c158':(2242,'0x00ffb400'),
  '0x0015c178':(2617,'0x00ffb300')}
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
    '0x0200':'predecrement nonzero delay_timer and skip the subhandler until it reaches zero; substate 0 toggles in_camera_bounds on (u16)(x-camera_x+16)<=0x01a0 and binds/advances source animation; substate 0x0200 enters the state-0x0400 handler',
    '0x0400':'write state=0x0200; predecrement effect_count; if it reaches zero allocate one record28 child at x+8,y+64,z-8 with source class field 0x05 and field5c=1; always clear field40, bind selector effect_count, allocate four type-24/class-0x47 presentation actors, then emit command 0x0077',
    '0x0600':'release through type-20 fixed-pool release 0x017706'},
   'collision_damage':{
    'current_state_writer':'0x01d590 then signed clamp 0x01d598',
    'source_frame':2804,'attacker':'0x00ff8380','defender':'0x00ffb300',
    'attack_record':'0x0011af76','health_before_s16':0,
    'damage_s16':25,'health_after_clamp_s16':-1,
    'reaction_writer':'0x01d4aa writes state 0x0400',
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
    'reaction-direction attack-mode guard','reaction-direction x comparison',
    'effect-count predecrement','audio command','fixed-frame substitute']}}
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
 player_special=json.loads(PLAYER.read_text(encoding='ascii'))[
  'special_implementation_contract']
 class09_slots=('ffb480','ffb500');initial=[]
 for slot,x in zip(class09_slots,(992,940)):
  observed=next((r for r in ss if r['slot']==slot and r['class']=='09' and int(r['frame'])==2073),None)
  req(observed is not None and int(observed['type'])==20 and int(observed['state'])==512 and int(observed['phase'])==0 and int(observed['x'])==x and int(observed['y'])==240 and int(observed['z'])==240 and int(observed['anim'],16)==0x6dbda,'class-0x09 first-segment initialization drift')
  initial.append({'source_slot':f'0x00ff{slot[2:]}','x_s16':x,'y_s16':240,'z_s16':240,'state_u16':0x0200,'substate_u16':0,'facing_u8':0,'animation_record':'0x0006dbda'})
 class09_rng=[r for r in rr if r['class']=='09' and int(r['frame'])<=2244]
 req(len(class09_rng)==44 and class09_rng[0]['seed']=='44fb' and class09_rng[-1]['seed']=='99e8','class-0x09 first-segment RNG cadence drift')
 selector_starts=(0x6dbda,0x6dbfe,0x6dc22,0x6dc46,0x6dc6a)
 class09_sequences=[{'selector_u8':selector,'terminal_rule':'negative branch is consumed by state 0x0200 before generic animation update','records':[animation_record(program,start),animation_record(program,start+16)]} for selector,start in zip((0,7,8,9,10),selector_starts)]
 spawn_rows=[r for r in ww if r['pc']=='060e84' and r['class']=='4e' and int(r['frame'])==2249]
 req([(r['slot'],r['data']) for r in spawn_rows]==[('ffc500','00000404'),('ffc480','00000404')],'class-0x4e initial allocation order drift')
 class4e_rng=[r for r in rr if r['class']=='4e' and int(r['frame'])==2249]
 req([(r['slot'],r['seed']) for r in class4e_rng]==[('ffc480','cdb5'),('ffc500','691e')],'class-0x4e scheduler/RNG order drift')
 class4e_records=[animation_record(program,0x929b0+16*i) for i in range(5)]
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
   'class4b event sequence','class3d class/variant','class3d movement offset/sign',
   'animation terminal guard','fixed-pool release','fixed-frame substitute'],
  'rng_calls':0,'collision_or_damage_writes':0,
  'fixed_frame_substitute_forbidden':True,
  'retained_gameplay_authority':False}
 class44_samples=[r for r in ss if r['class']=='44' and r['slot']=='ffc580' and 2235<=int(r['frame'])<=2256]
 req(class44_samples and class44_samples[0]['state']=='512' and class44_samples[0]['anim']=='0008daf2' and any(r['frame']=='2250' and r['state']=='1024' for r in class44_samples) and any(r['frame']=='2251' and r['state']=='1026' for r in class44_samples) and any(r['frame']=='2254' and r['state']=='1028' and r['anim']=='0008db1a' for r in class44_samples),'class-0x44 command-guard lifecycle drift')
 class44_object_or=[r for r in ww if r['slot']=='ffc580' and r['class']=='44' and r['pc']=='08d9d8']
 req(len(class44_object_or)==1 and class44_object_or[0]['frame']=='2072' and class44_object_or[0]['state']=='512' and class44_object_or[0]['phase']=='0' and class44_object_or[0]['offset']=='2e' and class44_object_or[0]['old']=='00000000' and class44_object_or[0]['data']=='00008000' and class44_object_or[0]['mask']=='0000ffff','class-0x44 object priority writer drift')
 class44_records=[animation_record(program,0x8daf2),animation_record(program,0x8db1a)]
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
 return {'classification':'SOURCE_CLOSED_IMPLEMENTATION_FIELDS','class_0x09_type20_rng_owner':{'dispatch':'0x06d926','state':'0x0200','source_slots':initial,'state_guard':'signed animation branch at actor+0x24 is negative','rng_entry':'0x017c5e','rng_call_pc':'0x06d974','rng_mask_u16':'0x000e','selector_table_address':'0x06d9a4','selector_table_u16':[0,7,8,9,10,8,9,10],'first_segment_calls_before_class4e':44,'seed_after_first_call':'0x44fb','seed_after_last_call':'0x99e8','animation_sequences':class09_sequences,'movement_result':'x/y/z unchanged in the accepted first-segment window','scheduler_order':'type-20 ascending source slot: 0xffb480 then 0xffb500','source_window':window(op,0x06d96e),'fixed_frame_substitute_forbidden':True},'class_0x4e_type24_variant4_effect':{'dispatch':'0x0927f6','variant_u8':4,'allocation_routine':'0x0177da','release_routine':'0x0177f0','available_source_slots':['0x00ffc480','0x00ffc500'],'allocation_pop_order':['0x00ffc500','0x00ffc480'],'scheduler_order':['0x00ffc480','0x00ffc500'],'initial_positions_before_rng':[{'source_slot':'0x00ffc500','x_s16':816,'y_s16':384,'z_s16':296},{'source_slot':'0x00ffc480','x_s16':848,'y_s16':424,'z_s16':296}],'state_sequence_u16':[0,0x0200,0x0400],'state0_writes':{'coordinate_mode_u8':2,'object_or_u16':'0x8000'},'rng_entry':'0x017c5e','rng_call_pc':'0x09282a','rng_mask_u16':'0x001c','seed_after_by_scheduler_slot':[{'source_slot':'0x00ffc480','seed':'0xcdb5','table_index':28},{'source_slot':'0x00ffc500','seed':'0x691e','table_index':24}],'jitter_table_s16':[[0,0],[4,0],[4,-4],[4,4],[-4,0],[-4,-4],[-4,4],[-8,8]],'animation_records':class4e_records,'terminal_guard':'signed actor+0x24 becomes negative, then state advances to 0x0400 and the next scheduler visit releases the record','collision_or_damage_writes':0,'later_same-window_allocation_attempts':'fail while both source free-list entries are active','source_window':window(op,0x0927f6),'fixed_frame_release_forbidden':True,'variant1_collision_effect':class4e_variant1},'class_0x44_type24_command_guard_owner':{'dispatch':'0x08d9a4','source_slot':'0x00ffc580','initial_state_u16':0x0200,'initial_position_s16':[792,296,296],'state_sequence_u16':[0x0200,0x0400,0x0402,0x0404],'state0_presentation_actor':{'coordinate_mode_u8':0,'palette_u8':0,'facing_u8':0,'object_or_u16':'0x8000','object_or_writer_pc':'0x08d9d8','object_or_write_frame':2072,'object_or_write_mask':'0x0000ffff','zero_fields_source':'accepted zero-initialized type-24 record; generic allocation writes preserve coordinate mode, palette and facing at zero'},'state_0x0200_guard':'global 0xff9a10_u8 nonzero advances state to 0x0400','state_0x0400_substate_0_writes':['global 0xff9a10_u8 = 0','actor substate += 2','actor+0x2a_u8 = 3'],'state_0x0402_guard':'predecrement actor+0x2a_u8; zero advances substate to 0x0404 and binds second presentation record','state_0x0404_result':'holds source presentation in the accepted first-segment window; does not clear the second command guard','animation_records':class44_records,'first_guard_set_frame':2249,'guard_clear_frame':2250,'second_player_origin_command_frame':2255,'rng_calls':0,'collision_or_damage_writes':0,'source_window':window(op,0x08d9a4),'fixed_frame_guard_reset_forbidden':True},'class_0x45_type24_scene_population':class45,'class_0x47_type24_class02_child_presentation':class47,'predator_special_type24_effects':special_effects}
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
 deps=r['first_segment_dependencies'];c09=deps['class_0x09_type20_rng_owner'];c4e=deps['class_0x4e_type24_variant4_effect'];c4e1=c4e['variant1_collision_effect'];c44=deps['class_0x44_type24_command_guard_owner'];c45=deps['class_0x45_type24_scene_population'];c47=deps['class_0x47_type24_class02_child_presentation'];special=deps['predator_special_type24_effects'];c4b=special['class_0x4b'];c3d=special['class_0x3d'];c16=deps['class_0x1f_type16_0x06_projectile']
 req(deps['classification']=='SOURCE_CLOSED_IMPLEMENTATION_FIELDS','first-segment dependency classification drift')
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
     c4e1['release_state']['first_absent_frame']==2318 and
     c4e1['collision_damage_authority'].startswith('shared collision writer') and
     c4e1['fixed_frame_substitute_forbidden'] is True and
     c4e1['retained_gameplay_authority'] is False,
     'class-0x4e variant-1 collision-effect contract drift')
 req(c44['dispatch']=='0x08d9a4' and c44['source_slot']=='0x00ffc580' and c44['state_sequence_u16']==[0x0200,0x0400,0x0402,0x0404] and c44['state0_presentation_actor']=={'coordinate_mode_u8':0,'palette_u8':0,'facing_u8':0,'object_or_u16':'0x8000','object_or_writer_pc':'0x08d9d8','object_or_write_frame':2072,'object_or_write_mask':'0x0000ffff','zero_fields_source':'accepted zero-initialized type-24 record; generic allocation writes preserve coordinate mode, palette and facing at zero'} and len(c44['animation_records'])==2 and c44['guard_clear_frame']==2250 and c44['second_player_origin_command_frame']==2255 and c44['rng_calls']==0 and c44['collision_or_damage_writes']==0 and c44['fixed_frame_guard_reset_forbidden'] is True,'class-0x44 command-guard dependency drift')
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
         for x in scene_components['components'][2:]) and
     all(x['classification']=='SOURCE_CLOSED_IMPLEMENTATION_FIELDS' and
         x['implementation_status']=='SPEC_EXECUTABLE' and
         x['semantic_role']!='UNKNOWN' and
         x['implementation_contract'] is not None and
         len(x['implementation_contract']['stage_records'])==2 and
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
      ['audio_transactions'][0]['command_u16']=='0x0077',
     'Coffee Shop remaining component identity drift')
 req(len(r['phantom_census_aliases'])==4 and all(x['classification']=='NOT_REQUIRED_FOR_ROUND1' and x['scheduler_dispatch'] is None for x in r['phantom_census_aliases']),'phantom alias classification drift');req(all(v==0 for k,v in r['coverage'].items() if k.startswith('orphan_')) and r['coverage']['invalid_zero_removal_controls_accepted']==0,'aux zero gap drift');req(r['correction_record']['invalid_controls_removed_zero_actors'] is True and r['correction_record']['accepted_controls_all_remove_actors'] is True and r['negative_controls']['zero_removal_suppression_rejected'] is True,'invalid suppression admitted');req(r['protected_boundaries']['production_runtime_writes']==0 and r['protected_boundaries']['yaba_runs']==0 and r['protected_boundaries']['physical_saturn']=='UNRUN' and r['protected_boundaries']['spec02_active'] is False,'protected boundary drift')

if __name__=='__main__':
 report=build();OUT.write_bytes(canon(report));print('ORACLE-11 auxiliary authority: SOURCE_CLOSED; 12 dispatched pairs closed, 4 census aliases NOT_REQUIRED, zero orphans')
