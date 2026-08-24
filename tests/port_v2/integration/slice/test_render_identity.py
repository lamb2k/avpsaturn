#!/usr/bin/env python3
"""Reject candidate-derived fidelity pins and run the MAME-source mutations."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    retired = json.loads(
        (HERE / "render_identity_contract.json").read_text(encoding="utf-8"))
    require(retired == {
        "schema": 2,
        "status": "SUPERSEDED",
        "former_evidence": "Saturn-candidate-derived render sequence hashes",
        "reason": "A candidate output cannot independently prove source fidelity.",
        "replacement": "data/avsp_source_combat_presentation_contract.json",
        "replacement_origin": "MAME_SOURCE_ONLY",
        "active_runtime_check": "Each emitted player and alien object/tile identity is compared with the source event or source timeline identity; any mismatch increments slice_asset_failures.",
    }, "candidate-derived render contract was reactivated or drifted")
    result = subprocess.run(
        [sys.executable, "-B", str(
            ROOT / "tests/port_v2/integration/combat/"
            "test_source_bound_presentation.py")],
        cwd=ROOT, check=True, capture_output=True, text=True)
    require("coherent source-event presentation contract: PASS" in
            result.stdout,
            "independent source contract or its mutations failed")
    print("INTEGRATE-03 MAME-source rendered identity contract: PASS")


if __name__ == "__main__":
    main()
