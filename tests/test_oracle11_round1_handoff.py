#!/usr/bin/env python3
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import analyze_oracle11_round1_handoff as analyzer

report = json.loads((ROOT / "data/oracle11_round1_handoff.json").read_text(
    encoding="ascii"))
analyzer.validate(report)


def reject(mutant, label):
    try:
        analyzer.validate(mutant)
    except ValueError:
        return
    raise AssertionError(label)


mutant = copy.deepcopy(report); mutant["status"] = "OBSERVED"; reject(mutant, "open status accepted")
mutant = copy.deepcopy(report); mutant["capture_identity"]["byte_identical"] = False; reject(mutant, "nonidentical captures accepted")
mutant = copy.deepcopy(report); mutant["coverage"]["orphan_stage_clear_phases"] = 1; reject(mutant, "orphan phase accepted")
mutant = copy.deepcopy(report); mutant["coverage"]["orphan_handoff_route_edges"] = 1; reject(mutant, "orphan edge accepted")
mutant = copy.deepcopy(report); mutant["coverage"]["orphan_load_release_events"] = 1; reject(mutant, "orphan load accepted")
mutant = copy.deepcopy(report); mutant["coverage"]["fixed_frame_authorities"] = 1; reject(mutant, "fixed-frame authority accepted")
mutant = copy.deepcopy(report); mutant["coverage"]["presentation_label_authorities"] = 1; reject(mutant, "visual label authority accepted")
mutant = copy.deepcopy(report); mutant["counterfactuals"]["suppress_exact_clear_writer_completes"] = True; reject(mutant, "fabricated clear accepted")
mutant = copy.deepcopy(report); mutant["round2_handoff"]["stable_round2_route_state"] = 2; reject(mutant, "unstable handoff accepted")
mutant = copy.deepcopy(report); mutant["load_release_ownership"]["new_unowned_events"] = 1; reject(mutant, "unowned load accepted")
mutant = copy.deepcopy(report); mutant["scope_boundary"]["global_rng_ownership"] = "SOURCE_CLOSED"; reject(mutant, "RNG silently absorbed")
mutant = copy.deepcopy(report); mutant["protected_boundaries"]["physical_saturn"] = "PASS"; reject(mutant, "emulator promoted to hardware")
print("ORACLE-11 Round 1 handoff tests: PASS (12 mutations rejected)")
