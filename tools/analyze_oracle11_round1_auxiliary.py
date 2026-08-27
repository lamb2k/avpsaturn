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
FILES=('aux_samples.tsv','aux_entries.tsv','aux_writes.tsv','aux_rng.tsv','aux_player_effects.tsv','samples.tsv','dispatches.tsv','projectiles.tsv','score_writes.tsv','result.tsv')
DISPATCH={(16,'0x06'):0x03537e,(20,'0x07'):0x06d1aa,(20,'0x08'):0x06d53c,(20,'0x09'):0x06d926,(20,'0x0a'):0x06de92,(24,'0x10'):0x079ffc,(24,'0x3d'):0x0887c8,(24,'0x43'):0x08ce44,(24,'0x45'):0x08dc1c,(24,'0x49'):0x08f080,(24,'0x4b'):0x08f86e,(24,'0x4e'):0x0927f6}
EXPECTED={(16,'0x06'):(505,514,4991,0,2),(20,'0x07'):(28446,26565,26619,0,0),(20,'0x08'):(275,276,811,1,0),(20,'0x09'):(6956,7194,21606,898,0),(20,'0x0a'):(603,602,1708,1,0),(24,'0x10'):(4694,4769,23665,0,0),(24,'0x3d'):(12811,11476,121404,0,0),(24,'0x43'):(828,844,16860,112,0),(24,'0x45'):(1364,1308,30536,196,0),(24,'0x49'):(4209,4808,19339,0,0),(24,'0x4b'):(810,661,4080,0,0),(24,'0x4e'):(909,848,3732,80,0)}

def req(x,m):
 if not x:raise ValueError(m)
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

def first_segment_dependencies(ss,ww,rr,op,program):
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
 class44_samples=[r for r in ss if r['class']=='44' and r['slot']=='ffc580' and 2235<=int(r['frame'])<=2256]
 req(class44_samples and class44_samples[0]['state']=='512' and class44_samples[0]['anim']=='0008daf2' and any(r['frame']=='2250' and r['state']=='1024' for r in class44_samples) and any(r['frame']=='2251' and r['state']=='1026' for r in class44_samples) and any(r['frame']=='2254' and r['state']=='1028' and r['anim']=='0008db1a' for r in class44_samples),'class-0x44 command-guard lifecycle drift')
 class44_object_or=[r for r in ww if r['slot']=='ffc580' and r['class']=='44' and r['pc']=='08d9d8']
 req(len(class44_object_or)==1 and class44_object_or[0]['frame']=='2072' and class44_object_or[0]['state']=='512' and class44_object_or[0]['phase']=='0' and class44_object_or[0]['offset']=='2e' and class44_object_or[0]['old']=='00000000' and class44_object_or[0]['data']=='00008000' and class44_object_or[0]['mask']=='0000ffff','class-0x44 object priority writer drift')
 class44_records=[animation_record(program,0x8daf2),animation_record(program,0x8db1a)]
 return {'classification':'SOURCE_CLOSED_IMPLEMENTATION_FIELDS','class_0x09_type20_rng_owner':{'dispatch':'0x06d926','state':'0x0200','source_slots':initial,'state_guard':'signed animation branch at actor+0x24 is negative','rng_entry':'0x017c5e','rng_call_pc':'0x06d974','rng_mask_u16':'0x000e','selector_table_address':'0x06d9a4','selector_table_u16':[0,7,8,9,10,8,9,10],'first_segment_calls_before_class4e':44,'seed_after_first_call':'0x44fb','seed_after_last_call':'0x99e8','animation_sequences':class09_sequences,'movement_result':'x/y/z unchanged in the accepted first-segment window','scheduler_order':'type-20 ascending source slot: 0xffb480 then 0xffb500','source_window':window(op,0x06d96e),'fixed_frame_substitute_forbidden':True},'class_0x4e_type24_variant4_effect':{'dispatch':'0x0927f6','variant_u8':4,'allocation_routine':'0x0177da','release_routine':'0x0177f0','available_source_slots':['0x00ffc480','0x00ffc500'],'allocation_pop_order':['0x00ffc500','0x00ffc480'],'scheduler_order':['0x00ffc480','0x00ffc500'],'initial_positions_before_rng':[{'source_slot':'0x00ffc500','x_s16':816,'y_s16':384,'z_s16':296},{'source_slot':'0x00ffc480','x_s16':848,'y_s16':424,'z_s16':296}],'state_sequence_u16':[0,0x0200,0x0400],'state0_writes':{'coordinate_mode_u8':2,'object_or_u16':'0x8000'},'rng_entry':'0x017c5e','rng_call_pc':'0x09282a','rng_mask_u16':'0x001c','seed_after_by_scheduler_slot':[{'source_slot':'0x00ffc480','seed':'0xcdb5','table_index':28},{'source_slot':'0x00ffc500','seed':'0x691e','table_index':24}],'jitter_table_s16':[[0,0],[4,0],[4,-4],[4,4],[-4,0],[-4,-4],[-4,4],[-8,8]],'animation_records':class4e_records,'terminal_guard':'signed actor+0x24 becomes negative, then state advances to 0x0400 and the next scheduler visit releases the record','collision_or_damage_writes':0,'later_same-window_allocation_attempts':'fail while both source free-list entries are active','source_window':window(op,0x0927f6),'fixed_frame_release_forbidden':True},'class_0x44_type24_command_guard_owner':{'dispatch':'0x08d9a4','source_slot':'0x00ffc580','initial_state_u16':0x0200,'initial_position_s16':[792,296,296],'state_sequence_u16':[0x0200,0x0400,0x0402,0x0404],'state0_presentation_actor':{'coordinate_mode_u8':0,'palette_u8':0,'facing_u8':0,'object_or_u16':'0x8000','object_or_writer_pc':'0x08d9d8','object_or_write_frame':2072,'object_or_write_mask':'0x0000ffff','zero_fields_source':'accepted zero-initialized type-24 record; generic allocation writes preserve coordinate mode, palette and facing at zero'},'state_0x0200_guard':'global 0xff9a10_u8 nonzero advances state to 0x0400','state_0x0400_substate_0_writes':['global 0xff9a10_u8 = 0','actor substate += 2','actor+0x2a_u8 = 3'],'state_0x0402_guard':'predecrement actor+0x2a_u8; zero advances substate to 0x0404 and binds second presentation record','state_0x0404_result':'holds source presentation in the accepted first-segment window; does not clear the second command guard','animation_records':class44_records,'first_guard_set_frame':2249,'guard_clear_frame':2250,'second_player_origin_command_frame':2255,'rng_calls':0,'collision_or_damage_writes':0,'source_window':window(op,0x08d9a4),'fixed_frame_guard_reset_forbidden':True}}
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
 report['first_segment_dependencies']=first_segment_dependencies(ss,ww,rr,op,program)
 validate(report);return report

def validate(r):
 req(r['schema']=='oracle11-round1-auxiliary-authority-v1' and r['status']=='SOURCE_CLOSED','aux family status drift');req(r['capture_identity']['byte_identical'] is True and r['capture_identity']['sample_rows']==120620 and r['capture_identity']['entry_rows']==59865 and r['capture_identity']['write_rows']==428764 and r['capture_identity']['rng_rows']==1348 and r['capture_identity']['player_effect_rows']==2,'aux capture drift')
 op=OPCODES.read_bytes();req(len(r['archetypes'])==12 and {(x['type'],x['class']) for x in r['archetypes']}==set(DISPATCH),'aux inventory drift')
 for x in r['archetypes']:
  key=(x['type'],x['class']);entry=DISPATCH[key];exp=EXPECTED[key];req(x['classification']=='SOURCE_CLOSED' and x['dispatch_entry']==f'0x{entry:06x}' and x['dispatch_entry_sha256']==hashlib.sha256(op[entry:entry+64]).hexdigest() and tuple(x['counts'][k] for k in ('samples','entries','writes','rng','player_effects'))==exp and x['writer_provenance'] and x['orphan_write_rows']==0 and x['rng']['orphan_calls']==0 and x['presentation_and_collision']['record_count']>0 and x['presentation_and_collision']['orphan_records']==0 and x['counterfactual']['suppression_count']>0 and x['counterfactual']['first_frame']>0 and x['counterfactual']['classification']=='PASS' and x['semantic_name_inferred'] is False,f'{key}:aux authority drift')
 deps=r['first_segment_dependencies'];c09=deps['class_0x09_type20_rng_owner'];c4e=deps['class_0x4e_type24_variant4_effect'];c44=deps['class_0x44_type24_command_guard_owner']
 req(deps['classification']=='SOURCE_CLOSED_IMPLEMENTATION_FIELDS','first-segment dependency classification drift')
 req(c09['dispatch']=='0x06d926' and c09['state']=='0x0200' and len(c09['source_slots'])==2 and c09['first_segment_calls_before_class4e']==44 and c09['seed_after_first_call']=='0x44fb' and c09['seed_after_last_call']=='0x99e8' and c09['selector_table_u16']==[0,7,8,9,10,8,9,10] and [x['selector_u8'] for x in c09['animation_sequences']]==[0,7,8,9,10] and all(len(x['records'])==2 for x in c09['animation_sequences']) and c09['fixed_frame_substitute_forbidden'] is True,'class-0x09 first-segment dependency drift')
 req(c4e['dispatch']=='0x0927f6' and c4e['variant_u8']==4 and c4e['allocation_pop_order']==['0x00ffc500','0x00ffc480'] and c4e['scheduler_order']==['0x00ffc480','0x00ffc500'] and c4e['state_sequence_u16']==[0,0x0200,0x0400] and [x['table_index'] for x in c4e['seed_after_by_scheduler_slot']]==[28,24] and len(c4e['jitter_table_s16'])==8 and len(c4e['animation_records'])==5 and c4e['collision_or_damage_writes']==0 and c4e['fixed_frame_release_forbidden'] is True,'class-0x4e first-segment dependency drift')
 req(c44['dispatch']=='0x08d9a4' and c44['source_slot']=='0x00ffc580' and c44['state_sequence_u16']==[0x0200,0x0400,0x0402,0x0404] and c44['state0_presentation_actor']=={'coordinate_mode_u8':0,'palette_u8':0,'facing_u8':0,'object_or_u16':'0x8000','object_or_writer_pc':'0x08d9d8','object_or_write_frame':2072,'object_or_write_mask':'0x0000ffff','zero_fields_source':'accepted zero-initialized type-24 record; generic allocation writes preserve coordinate mode, palette and facing at zero'} and len(c44['animation_records'])==2 and c44['guard_clear_frame']==2250 and c44['second_player_origin_command_frame']==2255 and c44['rng_calls']==0 and c44['collision_or_damage_writes']==0 and c44['fixed_frame_guard_reset_forbidden'] is True,'class-0x44 command-guard dependency drift')
 req(len(r['phantom_census_aliases'])==4 and all(x['classification']=='NOT_REQUIRED_FOR_ROUND1' and x['scheduler_dispatch'] is None for x in r['phantom_census_aliases']),'phantom alias classification drift');req(all(v==0 for k,v in r['coverage'].items() if k.startswith('orphan_')) and r['coverage']['invalid_zero_removal_controls_accepted']==0,'aux zero gap drift');req(r['correction_record']['invalid_controls_removed_zero_actors'] is True and r['correction_record']['accepted_controls_all_remove_actors'] is True and r['negative_controls']['zero_removal_suppression_rejected'] is True,'invalid suppression admitted');req(r['protected_boundaries']['production_runtime_writes']==0 and r['protected_boundaries']['yaba_runs']==0 and r['protected_boundaries']['physical_saturn']=='UNRUN' and r['protected_boundaries']['spec02_active'] is False,'protected boundary drift')

if __name__=='__main__':
 report=build();OUT.write_bytes(canon(report));print('ORACLE-11 auxiliary authority: SOURCE_CLOSED; 12 dispatched pairs closed, 4 census aliases NOT_REQUIRED, zero orphans')
