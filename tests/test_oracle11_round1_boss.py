#!/usr/bin/env python3
import copy
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import analyze_oracle11_round1_boss as analyzer

report=json.loads((ROOT/'data/oracle11_round1_boss_orchestration.json').read_text(encoding='ascii'))
analyzer.validate(report)

def reject(mutant,label):
    try: analyzer.validate(mutant)
    except ValueError: return
    raise AssertionError(label)

mutant=copy.deepcopy(report);mutant['status']='OBSERVED';reject(mutant,'open boss status accepted')
mutant=copy.deepcopy(report);mutant['capture_identity']['byte_identical']=False;reject(mutant,'nonidentical completions accepted')
mutant=copy.deepcopy(report);mutant['coverage']['orphan_controller_phases']=1;reject(mutant,'orphan controller phase accepted')
mutant=copy.deepcopy(report);mutant['coverage']['orphan_boss_spawns']=1;reject(mutant,'orphan boss spawn accepted')
mutant=copy.deepcopy(report);mutant['coverage']['orphan_boss_rng_calls']=1;reject(mutant,'orphan boss RNG accepted')
mutant=copy.deepcopy(report);mutant['coverage']['orphan_clear_writers']=1;reject(mutant,'orphan clear writer accepted')
mutant=copy.deepcopy(report);mutant['controller_contract']['appearance_used_for_authority']=True;reject(mutant,'appearance authority accepted')
mutant=copy.deepcopy(report);mutant['counterfactuals']['suppress_exact_clear_writer']['completed_round1']=True;reject(mutant,'fabricated clear accepted')
mutant=copy.deepcopy(report);mutant['scope_boundary']['stage_clear_and_round2_handoff']='SOURCE_CLOSED';reject(mutant,'handoff silently absorbed')
mutant=copy.deepcopy(report);mutant['protected_boundaries']['physical_saturn']='PASS';reject(mutant,'emulator evidence promoted to hardware')
print('ORACLE-11 Round 1 boss tests: PASS (10 mutations rejected)')
