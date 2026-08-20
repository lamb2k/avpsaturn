#!/usr/bin/env python3
"""Synthetic controls for the bounded official-runner equivalence reducer."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from probe_yabasanshiro_1_20_37_equivalence import assess

FIELDS = {"runtime_ready": "r", "street_frame": "f", "street_objects": "o",
          "frame_counter": "c", "street_frames": "n", "street_ready": "s"}


def row(frame: int, counter: int, picture: str) -> dict:
    return {"width": 352, "height": 224, "fnv1a64": picture, "fields": FIELDS,
            "probes": {"r": 1, "f": frame, "o": 464, "c": counter, "n": 201, "s": 1}}


def main() -> int:
    try:
        assess([])
    except ValueError as exc:
        assert "empty" in str(exc)
    else:
        raise AssertionError("empty log was accepted")
    try:
        assess([{"width": 352, "height": 224, "fnv1a64": "x"}])
    except ValueError as exc:
        assert "mapping" in str(exc)
    else:
        raise AssertionError("missing field map was accepted")
    non_native = row(1, 2, "a")
    non_native["width"] = 320
    assert assess([non_native])["status"] == "FAIL"
    never_ready = row(1, 2, "a")
    never_ready["probes"] = {**never_ready["probes"], "r": 0}
    assert assess([never_ready])["status"] == "FAIL"
    stalled = assess([row(0, 1, "same"), row(0, 1, "same")])
    assert stalled["status"] == "FAIL" and "stalled" in stalled["reason"]
    forged = assess([row(1, 2, "same"), row(2, 3, "same")])
    assert forged["status"] == "FAIL" and "forged" in forged["reason"]
    plausible = assess([row(1, 2, "a"), row(2, 3, "b")])
    assert plausible["status"] == "PENDING"
    print("official runner equivalence controls: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
