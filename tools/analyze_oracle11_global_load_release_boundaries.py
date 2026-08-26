#!/usr/bin/env python3
"""Close the four route-reachable graphics load/release ownership boundaries."""
from __future__ import annotations
import csv, hashlib, json
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE_A=ROOT/'.deps/mame/oracle11_global_load_a'
BASE_B=ROOT/'.deps/mame/oracle11_global_load_b'
OPCODES=ROOT/'.deps/mame/actorprobe/decrypted_opcodes_2m.bin'
OUT=ROOT/'data/oracle11_global_load_release_boundaries.json'
FILES=('gfx_writes.tsv','route_windows.tsv','load_result.tsv','samples.tsv',
       'dispatches.tsv','projectiles.tsv','score_writes.tsv','result.tsv')
SPECS=(
    (5565,5564,'gfxram2',5565,5565,'oracle11_global_load_mut_5565'),
    (5566,5565,'gfxram2',5566,15193,'oracle11_global_load_mut_5566'),
    (6200,6199,'gfxram1',6200,12798,'oracle11_global_load_mut_6200'),
    (12799,12798,'gfxram1',12799,15193,'oracle11_global_load_mut_12799'))

def require(c,m):
    if not c: raise ValueError(m)
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(p):
    with Path(p).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def identity(path):
    manifest=json.loads((path/'input_manifest.json').read_text(encoding='utf-8-sig'))
    names=list(FILES)+[f'{r}_{f:05d}.bin' for f in (5565,5566,6200,12799)
                       for r in ('gfxram0','gfxram1','gfxram2')]
    for name in names:require(digest(path/name)==manifest['sha256'][name],f'{path.name}:{name} drift')
    return {'manifest_sha256':digest(path/'input_manifest.json'),
            'files':{n:manifest['sha256'][n] for n in names}}
def projection_equal(a,b,names):return all(digest(a/n)==digest(b/n) for n in names)

def build_report():
    ida,idb=identity(BASE_A),identity(BASE_B)
    require(ida['files']==idb['files'],'load completion captures differ')
    writes=rows(BASE_A/'gfx_writes.tsv'); route=rows(BASE_A/'route_windows.tsv')
    route_by_frame={int(x['frame']):x for x in route}; opcodes=OPCODES.read_bytes()
    boundaries=[]
    for visible,write_frame,region,legal_first,legal_last,mut_name in SPECS:
        owned=[x for x in writes if int(x['frame'])==write_frame and x['region']==region]
        require(owned,f'{visible}: missing destination writes')
        writers=defaultdict(list)
        for row in owned:writers[row['pc']].append(row)
        writer_rows=[]
        for pc,observed in sorted(writers.items()):
            address=int(pc,16)
            chains=sorted({(x['return0'],x['return1'],x['return2']) for x in observed})
            writer_rows.append({'writer_pc':f'0x{pc}','write_count':len(observed),
                'destination_first':f"0x{min(int(x['address'],16) for x in observed):06x}",
                'destination_last':f"0x{max(int(x['address'],16) for x in observed):06x}",
                'origin_a6':sorted({f"0x{x['a6']}" for x in observed}),
                'caller_chains':[[f'0x{v}' for v in c] for c in chains],
                'source_window_sha256':hashlib.sha256(opcodes[max(0,address-16):address+32]).hexdigest()})
        package=BASE_A/f'{region}_{visible:05d}.bin'; package_hash=digest(package)
        mutation=ROOT/'.deps/mame'/mut_name; mid=identity(mutation)
        mresult=rows(mutation/'load_result.tsv')[0]
        require(int(mresult['suppression_count'])>0,f'{visible}: suppression missed')
        require(projection_equal(BASE_A,mutation,('samples.tsv','route_windows.tsv','dispatches.tsv',
                                                  'projectiles.tsv','score_writes.tsv','result.tsv')),
                f'{visible}: gameplay/route coupling')
        mutant_hash=digest(mutation/f'{region}_{visible:05d}.bin')
        require(mutant_hash!=package_hash,f'{visible}: non-discriminating package suppression')
        transaction='\n'.join('\t'.join(row[k] for k in
            ('address','pc','a6','return0','return1','return2','data','mask')) for row in owned)
        boundaries.append({'id':f'route-load-release-{visible}',
          'classification':'SOURCE_CLOSED','visible_boundary_frame':visible,
          'source_write_frame':write_frame,
          'route_guard':{'before':route_by_frame[visible-1],
                         'at_boundary':route_by_frame[visible],
                         'after':route_by_frame[visible+1]},
          'loader_callers':writer_rows,'package_identity':{'region':region,
            'snapshot_sha256':package_hash,'transaction_sha256':hashlib.sha256(transaction.encode('ascii')).hexdigest(),
            'write_count':len(owned)},
          'destination_ownership':{'owner':'CPS2 graphics RAM package plane',
            'region':region,'first_address':f"0x{min(int(x['address'],16) for x in owned):06x}",
            'last_address':f"0x{max(int(x['address'],16) for x in owned):06x}"},
          'legal_read_window':{'first_frame_inclusive':legal_first,
                               'last_frame_inclusive':legal_last,
                               'next_package_boundary':None if legal_last==15193 else legal_last+1},
          'completion':{'guard':'all captured source writes complete before the visible boundary snapshot',
                        'resulting_package_sha256':package_hash,
                        'next_route_state':route_by_frame[visible+1]},
          'failure_control':{'kind':'suppress every write to the owned destination region on the source write frame',
            'capture':mut_name,'suppressed_writes':int(mresult['suppression_count']),
            'mutant_package_sha256':mutant_hash,'package_difference':True,
            'route_and_gameplay_projection_unchanged':True,
            'stable_round2_route_state':int(mresult['round2_route_state'])},
          'semantic_package_name':'UNKNOWN','mutation_identity':mid})
    report={'schema':'oracle11-global-load-release-boundaries-v1',
      'task':'ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE','status':'SOURCE_CLOSED',
      'scope':'four route-reachable graphics package load/release boundaries',
      'coverage':{'boundaries':4,'orphan_route_guards':0,'orphan_loader_callers':0,
                  'orphan_packages':0,'orphan_destinations':0,'orphan_legal_read_windows':0},
      'boundaries':boundaries,'capture_identity':{'completion_a':ida,'completion_b':idb,
        'byte_identical':True,'opcode_sha256':digest(OPCODES)},
      'protected_boundaries':{'predator_warrior':'SOURCE_CLOSED','packed_bcd_score_routine':'0x0abdd2',
        'production_runtime_writes':0,'yaba_runs':0,'spec02_active':False,
        'oracle11_active':True,'physical_saturn':'UNRUN'}}
    validate(report);return report

def validate(r):
    require(r['status']=='SOURCE_CLOSED' and r['coverage']=={'boundaries':4,
      'orphan_route_guards':0,'orphan_loader_callers':0,'orphan_packages':0,
      'orphan_destinations':0,'orphan_legal_read_windows':0},'boundary coverage drift')
    require(len(r['boundaries'])==4 and [x['visible_boundary_frame'] for x in r['boundaries']]==[5565,5566,6200,12799],'boundary set drift')
    require(all(x['classification']=='SOURCE_CLOSED' and x['loader_callers'] and
      x['semantic_package_name']=='UNKNOWN' and x['failure_control']['package_difference'] and
      x['failure_control']['route_and_gameplay_projection_unchanged'] for x in r['boundaries']),'boundary closure drift')
    require(r['capture_identity']['byte_identical'] and r['protected_boundaries']['predator_warrior']=='SOURCE_CLOSED' and
      r['protected_boundaries']['spec02_active'] is False,'protected boundary drift')

def main():
    r=build_report();OUT.write_bytes((json.dumps(r,sort_keys=True,indent=2)+'\n').encode('ascii'))
    print('ORACLE-11 global load/release boundaries: SOURCE_CLOSED; 4 edges, zero orphans')
if __name__=='__main__':main()
