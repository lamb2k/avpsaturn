#!/usr/bin/env python3
"""Failing-first checks for the bounded RP4 Saturn-capture provenance."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from verify_rp4_saturn_controls import capture_provenance  # noqa: E402


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "capture.json"
        payload = {"schema": "rp4-street-command-order-capture-v0",
                   "commands": [], "requested_rel": 0}
        path.write_text(json.dumps(payload, sort_keys=True) + "\n",
                        encoding="ascii", newline="\n")
        actual = capture_provenance(path)
        expected = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == {
            "path": str(path.resolve()),
            "sha256": expected,
            "schema": "rp4-street-command-order-capture-v0",
            "requested_rel": 0,
        }, actual

    print("rp4 Saturn capture provenance: exact path, hash and identity hold")


if __name__ == "__main__":
    main()
