#!/usr/bin/env python3
import copy,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; ART=ROOT/'data/oracle11_global_load_release_boundaries.json'
S=importlib.util.spec_from_file_location('loads',ROOT/'tools/analyze_oracle11_global_load_release_boundaries.py');assert S and S.loader
o=importlib.util.module_from_spec(S);S.loader.exec_module(o)
def reject(m,label):
 try:o.validate(m)
 except ValueError:return
 raise AssertionError('accepted load mutation: '+label)
r=json.loads(ART.read_text(encoding='ascii'));o.validate(r)
m=copy.deepcopy(r);m['status']='PARTIAL';reject(m,'status')
m=copy.deepcopy(r);m['coverage']['boundaries']=3;reject(m,'hidden boundary')
m=copy.deepcopy(r);m['coverage']['orphan_loader_callers']=1;reject(m,'orphan caller')
m=copy.deepcopy(r);m['boundaries'].pop();reject(m,'body removed')
m=copy.deepcopy(r);m['boundaries'][0]['loader_callers']=[];reject(m,'caller removed')
m=copy.deepcopy(r);m['boundaries'][0]['semantic_package_name']='guessed';reject(m,'semantic guess')
m=copy.deepcopy(r);m['boundaries'][0]['failure_control']['package_difference']=False;reject(m,'non-discriminating control')
m=copy.deepcopy(r);m['boundaries'][0]['failure_control']['route_and_gameplay_projection_unchanged']=False;reject(m,'gameplay coupling')
m=copy.deepcopy(r);m['protected_boundaries']['spec02_active']=True;reject(m,'SPEC-02')
print('ORACLE-11 global load/release boundary tests: PASS (9 mutations rejected)')
