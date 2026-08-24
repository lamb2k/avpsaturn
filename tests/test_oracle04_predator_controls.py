"""Committed-artifact and mutation controls for ORACLE-04."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from analyze_oracle04_controls import OUT, self_test, validate  # noqa: E402


report = json.loads(OUT.read_text(encoding="utf-8"))
validate(report)
self_test(report)

mutations = []
changed = copy.deepcopy(report)
changed["determinism"]["control_cold_runs_byte_identical"] = False
mutations.append(changed)
changed = copy.deepcopy(report)
changed["bounded_findings"]["player_side_rng_consumption"] = "MEASURED"
mutations.append(changed)
changed = copy.deepcopy(report)
changed["attacks"][3]["health_after"] = 0
mutations.append(changed)

for index, mutation in enumerate(mutations):
    try:
        validate(mutation)
    except ValueError:
        continue
    raise AssertionError(f"ORACLE-04 committed mutation {index} unexpectedly passed")

print("ORACLE-04 committed artifact and negative controls: PASS")
