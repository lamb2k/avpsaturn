#!/usr/bin/env python3
import copy,importlib.util,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];S=importlib.util.spec_from_file_location('aux',R/'tools/analyze_oracle11_round1_auxiliary.py');assert S and S.loader
m=importlib.util.module_from_spec(S);S.loader.exec_module(m);report=json.loads((R/'data/oracle11_round1_auxiliary_authority.json').read_text(encoding='ascii'));m.validate(report)
def reject(x,label):
 try:m.validate(x)
 except ValueError:return
 raise AssertionError('accepted auxiliary mutation: '+label)
for label,mutate in [('status',lambda x:x.__setitem__('status','PARTIAL')),('determinism',lambda x:x['capture_identity'].__setitem__('byte_identical',False)),('pair',lambda x:x['archetypes'].pop()),('dispatch',lambda x:x['archetypes'][0].__setitem__('dispatch_entry','fixed frame')),('writer',lambda x:x['archetypes'][0].__setitem__('orphan_write_rows',1)),('rng',lambda x:x['archetypes'][0]['rng'].__setitem__('orphan_calls',1)),('record',lambda x:x['archetypes'][0]['presentation_and_collision'].__setitem__('record_count',0)),('suppression',lambda x:x['archetypes'][0]['counterfactual'].__setitem__('suppression_count',0)),('alias',lambda x:x['phantom_census_aliases'][0].__setitem__('classification','SOURCE_CLOSED')),('bad-control',lambda x:x['coverage'].__setitem__('invalid_zero_removal_controls_accepted',1)),('names',lambda x:x['archetypes'][0].__setitem__('semantic_name_inferred',True)),('spec',lambda x:x['protected_boundaries'].__setitem__('spec02_active',True))]:
 x=copy.deepcopy(report);mutate(x);reject(x,label)
print('ORACLE-11 auxiliary authority tests: PASS (12 mutations rejected)')
