#!/usr/bin/env python3
import copy
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location(
    'encounters',ROOT/'tools/analyze_oracle11_round1_encounters.py')
assert spec and spec.loader
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
report=json.loads((ROOT/'data/oracle11_round1_encounter_route_authority.json').read_text(encoding='ascii'))
m.validate(report)

def reject(mutant,label):
    try:m.validate(mutant)
    except ValueError:return
    raise AssertionError('accepted encounter mutation: '+label)

mutations=[]
for label,change in (
    ('status',lambda x:x.__setitem__('status','PARTIAL')),
    ('determinism',lambda x:x['capture_identity'].__setitem__('byte_identical',False)),
    ('segment',lambda x:x['segment_bindings'].pop()),
    ('edge',lambda x:x['route_state_edges'].pop()),
    ('spawn',lambda x:x['enemy_spawns'].pop()),
    ('timer',lambda x:x['coverage'].__setitem__('fixed_frame_substitutes',1)),
    ('actor-count',lambda x:x['coverage'].__setitem__('actor_count_clear_substitutes',1)),
    ('presentation',lambda x:x['negative_controls'].__setitem__('presentation_signature_can_advance_gameplay',True)),
    ('spec',lambda x:x['protected_boundaries'].__setitem__('spec02_active',True)),
):
    mutant=copy.deepcopy(report);change(mutant);reject(mutant,label)
print('ORACLE-11 encounter/route authority tests: PASS (9 mutations rejected)')
