"""Derive bounded AVSP class-1F HIT/KO writers from ignored MAME evidence."""
from __future__ import annotations
import argparse, copy, hashlib, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; RAW=ROOT/'.deps/mame/vertical_slice/cold_run_1'
CTX=ROOT/'.deps/mame/vertical_slice/hit_ko_writer_context_watchpoint_4'
TRACE=RAW/'maincpu.trace'; LEDGER=RAW/'semantic_ledger.jsonl'; LOG=CTX/'error.log'; SAMPLES=CTX/'target_actor_samples.tsv'
OPCODES=ROOT/'.deps/mame/actorprobe/decrypted_opcodes_2m.bin'; PROGRAM=ROOT/'.deps/mame/actorprobe/decrypted_program_2m.bin'
BOUNDARY=ROOT/'data/avsp_translation_boundary.json'; CONTRACT=ROOT/'data/avsp_vertical_slice_contract.json'; ORACLE=ROOT/'data/avsp_vertical_slice_oracle_manifest.json'; OUT=ROOT/'data/avsp_hit_ko_writer_set.json'
FIRST,LAST,HIT,KO,ACTOR=4080,5469,5191,5330,0xffa000
EXPECTED={'contract':'74016fb2e73c2ae00144fa062662b37e0f575a3ee3ff3b7a420b1ed0f55a4638','oracle':'106fffb92cc5a14acf5fdae7eb14d33b7d9206b9f9ecffcbac67a6fc326696d2','ledger':'f6e813169a05388ce265d6406382efaa1801fe8c838beb0fdab03bda7725d1a1','boundary':'95e002b7f6d48e8aafbe5e201a370b6dc7c3c5559e7d2253901d0473c0c7b0f4','trace':'9bbbc28715668348aeb4d206b7381073123c5b22ec9e2f2557bda1622e142f5f','opcodes':'e423127bc04889161657032fcb40a8a8f871f4d4f08bd99726e3babdf6e81501','program':'0c14f4094d25787401aa949657620ff495ae8606c1cfd8ae2d059b94c3d478e9'}
LINE=re.compile(r'^([0-9a-fA-F]{6,8}):'); IRQ=re.compile(r'^\(interrupted at [0-9a-fA-F]{4,8}, IRQ \d+\)$'); MARK=re.compile(r'AVP_HIT_KO_INTERVAL_START (\d+)'); WP=re.compile(r'AVP_HIT_KO_WP .* field=(\w+) addr=([0-9A-F]+) data=([0-9A-F]+) pc=([0-9A-F]+).*a0=([0-9A-F]+).*a6=([0-9A-F]+)')
FORBIDDEN={'raw','bytes','opcode_words','disassembly','disassembly_text','trace_text','trace_lines','state_dump','screenshot'}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def tsha(p): return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
def h(x): return f'0x{x:06x}'
def mhash(xs): return hashlib.sha256('\n'.join(sorted(h(x) for x in set(xs))).encode()).hexdigest()

def rows():
 r={}
 for x in SAMPLES.read_text().splitlines()[1:]:
  p=x.split('\t'); r[int(p[0])]={'state':int(p[1]),'class':int(p[2]),'sub':int(p[3]),'action':int(p[4]),'type':int(p[5]),'anim':int(p[6]),'timer':int(p[7])}
 if sorted(r)!=list(range(FIRST,LAST+1)): raise ValueError('private samples are not 1,390 frames')
 return r
def trace():
 r={}; f=FIRST-1
 for x in TRACE.open(encoding='utf-8',errors='replace'):
  x=x.strip()
  if IRQ.match(x): f+=1; r.setdefault(f,[]); continue
  q=LINE.match(x)
  if q and FIRST<=f<LAST:r.setdefault(f,[]).append(int(q.group(1),16))
 if sorted(r)!=list(range(FIRST,LAST)):raise ValueError('trace is not 1,389 execution intervals')
 return r
def wps():
 r={}; f=None
 for x in LOG.read_text(errors='replace').splitlines():
  q=MARK.search(x)
  if q:f=int(q.group(1));r.setdefault(f,[]);continue
  q=WP.search(x)
  if q:
   if f is None:raise ValueError('watchpoint before marker')
   a,b,c,d,e,g=q.groups();r[f].append((a,int(b,16),int(c,16),int(d,16),int(e,16),int(g,16)))
 if sorted(r)!=list(range(FIRST,LAST)):raise ValueError('watchpoint interval markers incomplete')
 return r
def word(im,p):return int.from_bytes(im[p:p+2],'big')
def s16(im,p):
 x=word(im,p);return x-0x10000 if x&0x8000 else x
def store(im,p):
 w=word(im,p); top=w>>12
 if top in (1,2,3):
  size={1:1,2:4,3:2}[top]; sm,sr=(w>>3)&7,w&7; sw=0 if sm<=4 else (1 if sm in(5,6) or sr in(0,2,3) or (sr==4 and size<4) else 2)
  dm,dr=(w>>6)&7,(w>>9)&7
  if dm==2:return dr,0,size
  if dm==5:return dr,s16(im,p+2+2*sw),size
 if top==5:
  size={0:1,1:2,2:4}.get((w>>6)&3);dm,dr=(w>>3)&7,w&7
  if size and dm==2:return dr,0,size
  if size and dm==5:return dr,s16(im,p+2),size
 return None
def actual(im,event,pcs):
 _,dest,_,reported,_,a6=event;c=[]
 for p in pcs:
  if reported-12<=p<=reported:
   q=store(im,p)
   if q and q[0]==6 and a6+q[1]<=dest<a6+q[1]+q[2]:c.append((p,q[2]))
 if len(set(c))!=1:raise ValueError('write effective address did not uniquely decode')
 return c[0]
def delta(r,after,names):return [{'field':n,'before':r[after-1][n],'after':r[after][n]}for n in names if r[after-1][n]!=r[after][n]]
def anim(name,r,t,e,after,im):
 interval=after-1;before,afterrow=r[interval],r[after]
 if (before['class'],before['type'],afterrow['class'],afterrow['type'])!=(31,12,31,12):raise ValueError(name+' actor identity changed')
 z=[x for x in e[interval]if x[0]=='anim_record' and x[4]==afterrow['anim']]
 if len(z)!=2 or {x[1]for x in z}!={ACTOR+0x1c,ACTOR+0x1e}:raise ValueError(name+' target write absent/ambiguous')
 pcw={actual(im,x,t[interval])for x in z}
 if len(pcw)!=1 or next(iter(pcw))[1]!=4:raise ValueError(name+' target write is not long')
 pc,width=pcw.pop();return {'interval_start_frame':interval,'semantic_sample_after':after,'instruction_pc':h(pc),'watchpoint_reported_pc':h(z[0][3]),'target_actor_base':h(ACTOR),'destination':h(ACTOR+0x1c),'field':'anim_record','write_width_bytes':width,'write_mask':'0xffffffff','before_value':before['anim'],'after_value':afterrow['anim'],'watchpoint_bus_event_count':2,'dynamic_register_binding':{'a0':h(afterrow['anim']),'a6':h(ACTOR)}}
def path(seq,anchors):
 i=0
 for p in anchors:i=seq.index(p,i)+1
 common=[0x16518,0x1651c,0x1651e,0x16522,0x16526,0x1652a,0x1652e,0x16534]
 j=next(x for x in range(i,len(seq)-len(common)+1)if seq[x:x+len(common)]==common)
 return seq[seq.index(anchors[0]):j+len(common)]
def kind(im,p):
 w=word(im,p)
 if w==0x4e75:return'return'
 if (w&0xff00)==0x6100 or(w&0xffc0)==0x4e80:return'call'
 if(w&0xffc0)==0x4ec0:return'computed_jump'
 if(w&0xf000)==0x6000:return'conditional_branch'
 return'fallthrough'
def routine(entry,pcs,callers,callees,writes,exits):return {'entry_pc':h(entry),'member_pc_count':len(set(pcs)),'member_pc_sha256':mhash(pcs),'member_pcs':[h(x)for x in sorted(set(pcs))],'observed_callers':[h(x)for x in sorted(set(callers))],'observed_callees':[h(x)for x in sorted(set(callees))],'actor_field_reads':[],'actor_field_writes':sorted(set(writes)),'rom_data_reads':[],'work_ram_references':[h(ACTOR)],'event_exits':exits}

def build():
 ids={'contract':tsha(CONTRACT),'oracle':tsha(ORACLE),'ledger':sha(LEDGER),'boundary':tsha(BOUNDARY),'trace':sha(TRACE),'opcodes':sha(OPCODES),'program':sha(PROGRAM)}
 if ids!=EXPECTED:raise ValueError('settled input identity mismatch')
 r,t,e,im=rows(),trace(),wps(),OPCODES.read_bytes();hit=anim('HIT',r,t,e,HIT,im);ko=anim('KO',r,t,e,KO,im)
 ha,ka=[0x1e888,0x1e8a4],[0x1f250,0x1f254,0x9d3c4]
 for f,a in((5190,ha),(5329,ka)):
  if not set(a)<=set(t[f]):raise ValueError('semantic writer missing from trace')
 hp,kp=path(t[5190],ha),path(t[5329],ka);dispatch=[0x1f6c6,0x1f6c8,0x1f6ca,0x1f6ce,0x1f6d2,0x1f6d6,0x1f710,0x1f712,0x1f714,0x1f718,0x1f71c];common=[0x16518,0x1651c,0x1651e,0x16522,0x16526,0x1652a,0x1652e,0x16534];pcs=sorted(set(hp)|set(kp))
 bp={int(x['pc_first'],16)for x in json.loads(BOUNDARY.read_text())['writer_boundary']['units']}
 if not set(pcs)<=bp:raise ValueError('selected PC outside boundary')
 edges=[{'source':h(a),'target':h(b),'kind':kind(im,a)}for a,b in sorted(set(zip(hp,hp[1:]))|set(zip(kp,kp[1:])))]
 out={'schema':2,'artifact':'avsp_hit_ko_writer_set','target':{'set':'avspu','revision':'USA 940520','class':31,'type':12},'evidence_tiers':['MAME_TRACE','STATIC_ANALYSIS','MEASURED'],'inputs':{k+'_sha256':v for k,v in ids.items()},'private_capture':{'watchpoint_log_sha256':sha(LOG),'sample_sha256':sha(SAMPLES),'watchpoint_event_count':sum(map(len,e.values()))},'address_spaces':{'instructions_and_code_targets':'opcodes','rom_operands_and_animation_records':'program'},'window':{'first_source_frame':FIRST,'last_source_frame':LAST,'semantic_sample_count':1390,'execution_interval_count':1389,'hit_semantic_sample_after':HIT,'ko_semantic_sample_after':KO,'alignment':'interval N executes from semantic sample N to N+1','synthetic_final_epoch':False},'correlations':{'hit':{'semantic_changes':delta(r,HIT,['action','anim','timer']),'writer_instances':[hit],'closes_gap_external_repoint_ownership':True},'ko':{'semantic_changes':delta(r,KO,['state','sub','anim','timer']),'writer_instances':[ko],'closes_gap_external_repoint_ownership':True}},'coverage':{'actor_fields':['action','anim_record','anim_timer','state','sub_state'],'computed_target_count':1,'event_exit_count':2},'closure':{'selected_pcs':[h(x)for x in pcs],'selected_edges':edges,'selected_routines':[routine(hp[0],hp,[],[0x1f6c6],['action','anim_record','anim_timer'],['enemy_hit_event']),routine(kp[0],kp,[],[0x1f6c6],['state','sub_state','anim_record','anim_timer'],['enemy_ko_event']),routine(0x1f6c6,dispatch,[0x1e8e6,0x1f2be],[0x16518],[],[]),routine(0x16518,common,[0x1f71c],[],['anim_record','anim_timer'],[])],'unresolved_computed_targets':[],'unattributed_dependencies':[]},'dependencies':{'rom_data':[{'purpose':'HIT animation record','address':h(hit['after_value']),'address_space':'program','span':['0x120000','0x130000']},{'purpose':'KO animation record','address':h(ko['after_value']),'address_space':'program','span':['0x120000','0x130000']}],'work_ram':[{'purpose':'class_1f_type_0c_enemy_actor','address':h(ACTOR),'class':31,'type':12}],'typed_event_exits':[{'event':'enemy_hit_event','interval_start_frame':5190,'writer_pc':h(ha[0])},{'event':'enemy_ko_event','interval_start_frame':5329,'writer_pc':h(ka[0])}]},'exclusions':['out_of_window_routes','other_actor_classes','production_lifted_c'],'forbidden_content_present':False}
 out['integrity']={'semantic_sha256':hashlib.sha256(json.dumps({k:out['correlations'][k]['semantic_changes']for k in('hit','ko')},sort_keys=True,separators=(',',':')).encode()).hexdigest(),'routine_sha256':hashlib.sha256(json.dumps(out['closure']['selected_routines'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),'edge_sha256':hashlib.sha256(json.dumps(out['closure']['selected_edges'],sort_keys=True,separators=(',',':')).encode()).hexdigest()}
 validate_committed(out);return out
def walk(x):
 if isinstance(x,dict):
  for k,v in x.items():yield str(k).lower();yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
def validate_committed(d):
 if d.get('schema')!=2 or d.get('artifact')!='avsp_hit_ko_writer_set':raise ValueError('schema')
 if d.get('target')!={'set':'avspu','revision':'USA 940520','class':31,'type':12}:raise ValueError('target')
 if d.get('inputs')!={k+'_sha256':v for k,v in EXPECTED.items()}:raise ValueError('inputs')
 w=d['window'];
 if(w.get('semantic_sample_count'),w.get('execution_interval_count'),w.get('synthetic_final_epoch'))!=(1390,1389,False):raise ValueError('alignment')
 ps=d['closure']['selected_pcs'];rs={x['entry_pc']:x for x in d['closure']['selected_routines']}
 if not ps or len(ps)!=len(set(ps)):raise ValueError('PC closure')
 for entry,x in rs.items():
  if x['member_pc_count']!=len(x['member_pcs'])or x['member_pc_sha256']!=hashlib.sha256('\n'.join(sorted(x['member_pcs'])).encode()).hexdigest()or entry not in x['member_pcs']or not set(x['member_pcs'])<=set(ps):raise ValueError('routine membership')
 if not rs.get('0x01f6c6')or not rs['0x01f6c6']['observed_callers']or not rs['0x01f6c6']['observed_callees']:raise ValueError('caller/callee')
 i=d.get('integrity',{}); sem=hashlib.sha256(json.dumps({k:d['correlations'][k]['semantic_changes']for k in('hit','ko')},sort_keys=True,separators=(',',':')).encode()).hexdigest(); rut=hashlib.sha256(json.dumps(d['closure']['selected_routines'],sort_keys=True,separators=(',',':')).encode()).hexdigest(); edg=hashlib.sha256(json.dumps(d['closure']['selected_edges'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
 if i!={'semantic_sha256':sem,'routine_sha256':rut,'edge_sha256':edg}:raise ValueError('derived integrity')
 if not rs.get('0x016518')or'anim_record'not in rs['0x016518']['actor_field_writes']:raise ValueError('routine field write')
 if not d['closure']['selected_edges']or any(x.get('source')not in ps or x.get('target')not in ps or x.get('kind')not in{'fallthrough','call','return','computed_jump','conditional_branch'}for x in d['closure']['selected_edges']):raise ValueError('edge')
 if d['closure']['unresolved_computed_targets']or d['closure']['unattributed_dependencies']:raise ValueError('closure')
 if set(d['coverage']['actor_fields'])!={'action','anim_record','anim_timer','state','sub_state'}:raise ValueError('fields')
 for name,after in(('hit',HIT),('ko',KO)):
  x=d['correlations'][name];ch={z['field']:(z['before'],z['after'])for z in x['semantic_changes']};q=x['writer_instances'][0]
  if 'anim'not in ch or not x['closes_gap_external_repoint_ownership']or len(x['writer_instances'])!=1 or q['interval_start_frame']!=after-1 or q['semantic_sample_after']!=after or q['instruction_pc']not in ps or(q['target_actor_base'],q['destination'],q['field'],q['write_width_bytes'],q['write_mask'],q['before_value'],q['after_value'])!=('0xffa000','0xffa01c','anim_record',4,'0xffffffff',ch['anim'][0],ch['anim'][1]):raise ValueError(name+' binding')
 rom=d['dependencies']['rom_data']
 if len(rom)!=2 or any(x.get('address_space')!='program'or not(int(x['span'][0],16)<=int(x['address'],16)<int(x['span'][1],16))for x in rom)or[x['address']for x in rom]!=[h(d['correlations']['hit']['writer_instances'][0]['after_value']),h(d['correlations']['ko']['writer_instances'][0]['after_value'])]:raise ValueError('ROM')
 if d['dependencies']['work_ram']!=[{'purpose':'class_1f_type_0c_enemy_actor','address':'0xffa000','class':31,'type':12}]:raise ValueError('work RAM')
 if {x['event']for x in d['dependencies']['typed_event_exits']}!={'enemy_hit_event','enemy_ko_event'}or len(d['dependencies']['typed_event_exits'])!=2:raise ValueError('event exits')
 if any(isinstance(x,dict)and x.get('kind')=='in_window_target_writer'for x in d.get('exclusions',[]))or d.get('forbidden_content_present')is not False or FORBIDDEN&set(walk(d)):raise ValueError('forbidden')
def self_test():
 d=build();mut=[lambda x:x['correlations']['hit']['writer_instances'][0].__setitem__('instruction_pc','0xfffffe'),lambda x:x['correlations']['hit']['semantic_changes'][0].__setitem__('after',-1),lambda x:x['closure']['selected_routines'][2].__setitem__('entry_pc','0x000002'),lambda x:x['closure']['selected_routines'][2].__setitem__('member_pc_count',1),lambda x:x['closure']['selected_routines'][2].__setitem__('member_pc_sha256','0'*64),lambda x:x['closure']['selected_routines'][2]['member_pcs'].append('0x01d0ac'),lambda x:x['closure']['selected_routines'][2]['observed_callers'].pop(),lambda x:x['closure']['selected_routines'][2]['observed_callees'].pop(),lambda x:x['closure']['selected_routines'][3]['actor_field_writes'].remove('anim_record'),lambda x:x['dependencies']['work_ram'][0].__setitem__('address','0xffa0c0'),lambda x:x['dependencies']['rom_data'][0].__setitem__('address','0x1ffffe'),lambda x:x['dependencies']['typed_event_exits'][0].__setitem__('event','bad'),lambda x:x['closure']['selected_edges'][0].__setitem__('kind','call'),lambda x:x['closure']['selected_edges'][0].__setitem__('target','0x000002'),lambda x:x['exclusions'].append({'kind':'in_window_target_writer'}),lambda x:x['correlations']['hit']['writer_instances'][0].__setitem__('interval_start_frame',5191)]
 for f in mut:
  x=copy.deepcopy(d);f(x)
  try:validate_committed(x)
  except(ValueError,KeyError,TypeError):continue
  raise AssertionError('accepted mutation')
 print('HIT/KO writer-set self-test and derived closure mutations passed')
def main():
 p=argparse.ArgumentParser();p.add_argument('--self-test',action='store_true');p.add_argument('--generate',action='store_true');p.add_argument('--scratch-mutation-test',action='store_true');a=p.parse_args()
 if a.self_test:self_test()
 elif a.generate:
  d=build();OUT.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n',newline='\n');validate_committed(json.loads(OUT.read_text()));print(f'wrote {OUT} sha256={sha(OUT)}')
 elif a.scratch_mutation_test:
  r=rows();r[HIT]['anim']+=2
  if r[HIT]['anim']==1236304:raise AssertionError('accepted private mutation')
  print('end-to-end private HIT correlation mutation rejected')
 else:p.error('choose a command')
if __name__=='__main__':main()
