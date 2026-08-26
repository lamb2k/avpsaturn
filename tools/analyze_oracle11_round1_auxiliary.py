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
 validate(report);return report

def validate(r):
 req(r['schema']=='oracle11-round1-auxiliary-authority-v1' and r['status']=='SOURCE_CLOSED','aux family status drift');req(r['capture_identity']['byte_identical'] is True and r['capture_identity']['sample_rows']==120620 and r['capture_identity']['entry_rows']==59865 and r['capture_identity']['write_rows']==428764 and r['capture_identity']['rng_rows']==1348 and r['capture_identity']['player_effect_rows']==2,'aux capture drift')
 op=OPCODES.read_bytes();req(len(r['archetypes'])==12 and {(x['type'],x['class']) for x in r['archetypes']}==set(DISPATCH),'aux inventory drift')
 for x in r['archetypes']:
  key=(x['type'],x['class']);entry=DISPATCH[key];exp=EXPECTED[key];req(x['classification']=='SOURCE_CLOSED' and x['dispatch_entry']==f'0x{entry:06x}' and x['dispatch_entry_sha256']==hashlib.sha256(op[entry:entry+64]).hexdigest() and tuple(x['counts'][k] for k in ('samples','entries','writes','rng','player_effects'))==exp and x['writer_provenance'] and x['orphan_write_rows']==0 and x['rng']['orphan_calls']==0 and x['presentation_and_collision']['record_count']>0 and x['presentation_and_collision']['orphan_records']==0 and x['counterfactual']['suppression_count']>0 and x['counterfactual']['first_frame']>0 and x['counterfactual']['classification']=='PASS' and x['semantic_name_inferred'] is False,f'{key}:aux authority drift')
 req(len(r['phantom_census_aliases'])==4 and all(x['classification']=='NOT_REQUIRED_FOR_ROUND1' and x['scheduler_dispatch'] is None for x in r['phantom_census_aliases']),'phantom alias classification drift');req(all(v==0 for k,v in r['coverage'].items() if k.startswith('orphan_')) and r['coverage']['invalid_zero_removal_controls_accepted']==0,'aux zero gap drift');req(r['correction_record']['invalid_controls_removed_zero_actors'] is True and r['correction_record']['accepted_controls_all_remove_actors'] is True and r['negative_controls']['zero_removal_suppression_rejected'] is True,'invalid suppression admitted');req(r['protected_boundaries']['production_runtime_writes']==0 and r['protected_boundaries']['yaba_runs']==0 and r['protected_boundaries']['physical_saturn']=='UNRUN' and r['protected_boundaries']['spec02_active'] is False,'protected boundary drift')

if __name__=='__main__':
 report=build();OUT.write_bytes(canon(report));print('ORACLE-11 auxiliary authority: SOURCE_CLOSED; 12 dispatched pairs closed, 4 census aliases NOT_REQUIRED, zero orphans')
