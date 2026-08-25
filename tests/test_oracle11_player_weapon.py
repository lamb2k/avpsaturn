#!/usr/bin/env python3
"""Committed ORACLE-11 weapon/projectile/resource contract controls."""
import copy, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'data/oracle11_predator_weapon_projectile_resource.json'

def validate(d):
    assert d['status']=='SOURCE_CLOSED'
    assert d['determinism']['byte_identical'] is True
    assert d['mutation_controls']=={'all_downstream_effects_asserted':True,'count':12,'no_fixed_frame_result':True,'no_visible_weapon_inference_from_0xad':True}
    p=d['authority_separation']['projectile_lifecycle']
    assert p['class']=='0x05' and p['volley'].startswith('12 attempts')
    assert p['resource_debit'].startswith('3 per successful')
    e=d['authority_separation']['equipment_resource']
    assert e['capacity']==64 and e['action_latch'].endswith('not ownership')
    assert d['resource_causal_trace']['empty']['damaging_projectile_count']==0
    assert d['resource_causal_trace']['sufficient']['spawn_count']==12
    assert d['special_causal_trace']['zero_health'].startswith('special rejected')
    assert len(d['counterfactuals'])==12
    assert d['physical_saturn']=='UNRUN' and d['saturn_emulator']=='UNRUN'

def reject(mut,label):
    try:validate(mut)
    except AssertionError:return
    raise AssertionError('accepted mutation: '+label)

d=json.loads(ART.read_text(encoding='ascii'));validate(d)
for path,value,label in [
 (('mutation_controls','count'),11,'counterfactual removed'),
 (('authority_separation','projectile_lifecycle','class'),'0x00','wrong projectile class'),
 (('authority_separation','equipment_resource','capacity'),63,'fitted resource capacity'),
 (('resource_causal_trace','empty','damaging_projectile_count'),1,'empty fallback damage'),
 (('special_causal_trace','zero_health'),'special accepted','zero-health guard removed'),
 (('mutation_controls','no_visible_weapon_inference_from_0xad'),False,'action latch treated as equipment')]:
    m=copy.deepcopy(d);x=m
    for k in path[:-1]:x=x[k]
    x[path[-1]]=value;reject(m,label)
print('ORACLE-11 weapon/projectile/resource tests: PASS (6 invariant mutations rejected)')
