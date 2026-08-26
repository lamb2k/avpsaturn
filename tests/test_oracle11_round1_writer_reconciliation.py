#!/usr/bin/env python3
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import analyze_oracle11_round1_writer_reconciliation as analyzer

report = json.loads((ROOT / "data/oracle11_round1_writer_reconciliation.json")
                    .read_text(encoding="ascii"))
analyzer.validate(report)
derived = analyzer.build_report()
assert derived == report, "writer reconciliation derivation drift"


def reject(mutant, label):
    try:
        analyzer.validate(mutant)
    except ValueError:
        return
    raise AssertionError(label)


mutant = copy.deepcopy(report); mutant["status"] = "PARTIAL"; reject(mutant, "open status accepted")
mutant = copy.deepcopy(report); mutant["entries"].pop(); reject(mutant, "missing PC accepted")
mutant = copy.deepcopy(report); mutant["entries"][1]["pc"] = mutant["entries"][0]["pc"]; reject(mutant, "duplicate PC accepted")
mutant = copy.deepcopy(report); mutant["entries"][0]["owner"] = "unmapped"; reject(mutant, "unproven owner accepted")
mutant = copy.deepcopy(report); mutant["entries"][0]["evidence"] = "data/guess.json"; reject(mutant, "wrong evidence accepted")
mutant = copy.deepcopy(report); mutant["coverage"]["orphan_writer_pcs"] = 1; reject(mutant, "orphan accepted")
mutant = copy.deepcopy(report); mutant["coverage"]["duplicate_owner_pcs"] = 1; reject(mutant, "duplicate owner accepted")
mutant = copy.deepcopy(report); mutant["method"]["broad_family_subtraction"] = True; reject(mutant, "broad subtraction accepted")
mutant = copy.deepcopy(report); mutant["method"]["post_handoff_behavior_claimed_source_closed"] = True; reject(mutant, "post-handoff scope inflated")
mutant = copy.deepcopy(report); mutant["coverage"]["baseline_writer_pcs"] = 1516; reject(mutant, "baseline universe gap accepted")
mutant = copy.deepcopy(report); mutant["protected_boundaries"]["physical_saturn"] = "PASS"; reject(mutant, "emulator promoted to hardware")
print("ORACLE-11 writer reconciliation tests: PASS (11 mutations rejected)")
