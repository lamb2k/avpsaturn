#!/usr/bin/env python3
"""Failing-first checks for the bounded RP4 Saturn-capture provenance."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from verify_rp4_saturn_controls import capture_provenance  # noqa: E402


def main() -> None:
    evidence = ROOT / "private-evidence" / "rp4-saturn-controls"
    expected = {
        "cap_baseline.json": "791b22ecb5c7904cc9acc084536fb2776d0d83b4e86ea55e4bc5b542b2a19077",
        "cap_forward.json": "df56fd35f25a7bf816b430440511d5232ee1fccf29af21845de1a5ab583cf4fa",
    }
    for name, digest in expected.items():
        actual = capture_provenance(evidence / name)
        assert actual["path"] == "private-evidence/rp4-saturn-controls/" + name, actual
        assert actual["sha256"] == digest, actual
        assert actual["schema"] == "rp4-street-command-order-capture-v0", actual
        assert actual["requested_rel"] == 0, actual
        assert "Temp" not in actual["path"] and "AppData" not in actual["path"], actual

    manifest = json.loads((ROOT / "data" / "rp4_saturn_controls.json").read_text())
    recorded = manifest["input_captures"]
    assert recorded["baseline"]["path"] == "private-evidence/rp4-saturn-controls/cap_baseline.json"
    assert recorded["forward_order"]["path"] == "private-evidence/rp4-saturn-controls/cap_forward.json"

    print("rp4 Saturn capture provenance: stable private paths, hashes and identity hold")


if __name__ == "__main__":
    main()
