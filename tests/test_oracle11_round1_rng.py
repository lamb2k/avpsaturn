#!/usr/bin/env python3
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import analyze_oracle11_round1_rng as analyzer

report = json.loads((ROOT / "data/oracle11_round1_rng.json").read_text(encoding="ascii"))
analyzer.validate(report)


def reject(mutant, label):
    try:
        analyzer.validate(mutant)
    except ValueError:
        return
    raise AssertionError(label)


mutant = copy.deepcopy(report); mutant["status"] = "PARTIAL"; reject(mutant, "open RNG accepted")
mutant = copy.deepcopy(report); mutant["capture_identity"]["byte_identical"] = False; reject(mutant, "nonidentical RNG accepted")
mutant = copy.deepcopy(report); mutant["algorithm"]["entry"] = "0x017c60"; reject(mutant, "wrong algorithm accepted")
mutant = copy.deepcopy(report); mutant["consumption"]["calls"] -= 1; reject(mutant, "missing call accepted")
mutant = copy.deepcopy(report); mutant["consumption"]["distinct_seed_change_frames"] -= 1; reject(mutant, "missing frame accepted")
mutant = copy.deepcopy(report); mutant["consumption"]["recurrence_gaps"] = 1; reject(mutant, "recurrence gap accepted")
mutant = copy.deepcopy(report); mutant["owner_partition"]["enemy_type12"]["calls"] -= 1; reject(mutant, "owner gap accepted")
mutant = copy.deepcopy(report); mutant["owner_partition"]["orphan_calls"] = 1; reject(mutant, "orphan call accepted")
mutant = copy.deepcopy(report); mutant["owner_partition"]["global_route_and_controller"]["groups"].pop(); reject(mutant, "global group gap accepted")
mutant = copy.deepcopy(report); mutant["counterfactuals"]["freeze_rng"]["completed_round1"] = True; reject(mutant, "frozen RNG completion accepted")
mutant = copy.deepcopy(report); mutant["coverage"]["unowned_seed_writers"] = 1; reject(mutant, "unowned seed writer accepted")
mutant = copy.deepcopy(report); mutant["protected_boundaries"]["physical_saturn"] = "PASS"; reject(mutant, "emulator promoted to hardware")
print("ORACLE-11 Round 1 RNG tests: PASS (12 mutations rejected)")
