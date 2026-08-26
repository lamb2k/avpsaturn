#!/usr/bin/env python3
"""Validate the sole ORACLE-11 Round 1 closure matrix and SPEC-02 gate."""
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('matrix',ROOT/'tools/generate_round1_authority_matrix.py')
assert spec and spec.loader
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
c=json.loads((ROOT/'data/round1_system_coverage.yaml').read_text())
r=json.loads((ROOT/'data/oracle10_round1_route.json').read_text())
derived=m.build(c,r); committed=c['route_segment_authority_matrix']
assert derived==committed,'route-segment x authority-family matrix drift'
assert committed['segment_count']==len(r['segments'])
assert committed['cell_count']==len(r['segments'])*len(committed['authority_families'])
assert set(committed['coverage_universe']['routes'])==set(m.ROUTES)
assert all(len(row['cells'])==len(m.FAMILIES) for row in committed['rows'])
gate=committed['closure_gate'];assert gate==c['spec02_closure_gate']
required=('required_observed','required_partial','required_unknown',
 'unmapped_actor_class_type_pairs','unmapped_route_edges','unowned_events',
 'orphan_authoritative_writers','spec02_eligible')
assert all(x in gate for x in required)
zeros=(gate['required_observed']==0 and gate['required_partial']==0 and
 gate['required_unknown']==0 and gate['unmapped_actor_class_type_pairs']==0 and
 gate['unmapped_route_edges']==0 and not any(gate['unowned_events'].values()) and
 gate['orphan_authoritative_writers']==0)
assert gate['spec02_eligible']==zeros
assert gate['spec02_eligible'] is True,'zero-gap ORACLE-11 gate did not open SPEC-02'
assert c['next_card']=='REIMPLEMENT-13-SOURCE-CLOSED-ROUND1'
print('Round 1 authority matrix: PASS; accepted SPEC-02 routes to REIMPLEMENT-13')
