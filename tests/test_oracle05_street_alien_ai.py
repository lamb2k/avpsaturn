"""Committed-artifact and mutation controls for ORACLE-05."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from analyze_oracle05_ai import OUT, self_test, validate  # noqa: E402


report = json.loads(OUT.read_text(encoding="utf-8"))
validate(report)
self_test(report)

mutations = []
changed = copy.deepcopy(report)
changed["determinism"]["cold_runs_byte_identical"] = False
mutations.append(changed)
changed = copy.deepcopy(report)
changed["observed_loop"]["attack"]["contact_frames"] = [4301]
mutations.append(changed)
changed = copy.deepcopy(report)
changed["counterfactuals"]["ai_timer"]["attack_clear_frame"] = 4373
mutations.append(changed)
changed = copy.deepcopy(report)
changed["bounded_findings"]["multiplayer_targeting"] = "MEASURED"
mutations.append(changed)

for index, mutation in enumerate(mutations):
    try:
        validate(mutation)
    except ValueError:
        continue
    raise AssertionError(f"ORACLE-05 committed mutation {index} unexpectedly passed")

print("ORACLE-05 committed artifact and negative controls: PASS")
