#!/usr/bin/env python3
"""Reduce official-runner scanout metadata into a bounded equivalence report.

The tool never writes guest memory.  It rejects a superficially advancing
fixture when every post-ready scanout hash is identical: that is the simple
``write the diagnostic counter`` forgery this check is intended to catch.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REQUIRED = ("runtime_ready", "street_frame", "street_objects",
            "frame_counter", "street_frames", "street_ready")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def field(sample: dict, name: str) -> int:
    probes = sample.get("probes", {})
    aliases = sample.get("fields", {})
    key = aliases.get(name, name)
    value = probes.get(key, sample.get(name))
    if not isinstance(value, int):
        raise ValueError(f"missing integer field: {name}")
    return value


def assess(samples: list[dict]) -> dict:
    if not samples:
        raise ValueError("empty scanout metadata")
    missing = [name for name in REQUIRED if all(name not in item.get("fields", {})
               and name not in item.get("probes", {}) and name not in item for item in samples)]
    if missing:
        raise ValueError("schema has no mapping for: " + ", ".join(missing))
    ready = [sample for sample in samples if field(sample, "runtime_ready") == 1]
    if not ready:
        return {"status": "FAIL", "reason": "runtime_ready never asserted", "samples": len(samples)}
    last = ready[-1]
    values = {name: [field(sample, name) for sample in ready] for name in REQUIRED}
    report = {
        "samples": len(samples),
        "ready_samples": len(ready),
        "last": {name: values[name][-1] for name in REQUIRED},
        "distinct": {name: len(set(values[name])) for name in REQUIRED},
        "scanout_dimensions": [last.get("width"), last.get("height")],
        "scanout_hashes_after_ready": len({item.get("fnv1a64") for item in ready}),
    }
    if report["scanout_dimensions"] != [352, 224]:
        report.update(status="FAIL", reason="not native 352x224 scanout")
    elif values["street_frame"][-1] == 0 and values["frame_counter"][-1] <= 1:
        report.update(status="FAIL", reason="fixture callback stalled at initial frame")
    elif len(set(values["street_frame"])) > 1 and report["scanout_hashes_after_ready"] <= 1:
        report.update(status="FAIL", reason="rejected forged fixture advance: invariant scanout")
    else:
        report.update(status="PENDING", reason="requires pinned-release command/shadow/canary comparison")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--field", action="append", default=[], metavar="NAME=PROBEKEY")
    args = parser.parse_args()
    mapping = dict(item.split("=", 1) for item in args.field)
    try:
        rows = []
        for raw in args.log.read_text(encoding="utf-8").splitlines():
            row = json.loads(raw)
            row["fields"] = mapping
            rows.append(row)
        report = assess(rows)
        report.update(schema="official-runner-equivalence-v1",
                      input_sha256=sha256(args.log),
                      source="post-TitanRender callback metadata; no guest writes")
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"equivalence probe: FAIL: {exc}", file=sys.stderr)
        return 1
    print("equivalence probe: " + report["status"] + ": " + report["reason"])
    return 0 if report["status"] != "FAIL" else 3


if __name__ == "__main__":
    raise SystemExit(main())
