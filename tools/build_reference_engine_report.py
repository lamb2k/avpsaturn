#!/usr/bin/env python3
"""Run a CPS2-to-Saturn reference-engine scenario and write its report.

The engine consumes tracked, copyright-safe JSON only. It writes a canonical
report whose bytes are a function of its inputs, so running it twice produces
the same SHA-256. ``--check`` re-runs the model and compares against the file
already on disc without rewriting it.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference_engine import report as report_module  # noqa: E402
from reference_engine.scenario import NormalHitModel  # noqa: E402

DEFAULT_SCENARIO = ROOT / "reference_engine" / "scenarios" / "normal_hit.json"
DEFAULT_OUTPUT = ROOT / "data" / "reference_engine_normal_hit_report.json"


def generate(scenario: Path) -> tuple[dict, str, str]:
    model = NormalHitModel.load(ROOT, scenario)
    result = model.run()
    document = report_module.build_report(result, model)
    text = report_module.serialise(document)
    return document, text, report_module.digest(document)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", type=Path, default=DEFAULT_SCENARIO)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify the tracked report matches a fresh run instead of writing it",
    )
    args = parser.parse_args()

    document, text, digest = generate(args.scenario)
    _, repeat_text, repeat_digest = generate(args.scenario)
    if repeat_digest != digest:
        print("NON-DETERMINISTIC: two runs of the same scenario disagree", file=sys.stderr)
        return 2

    if args.check:
        if not args.output.is_file():
            print("Missing report: %s" % args.output, file=sys.stderr)
            return 1
        if args.output.read_bytes() != text.encode("ascii"):
            print("Tracked report differs from a fresh run: %s" % args.output, file=sys.stderr)
            return 1
        print("Report matches a fresh deterministic run. sha256=%s" % digest)
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Explicit LF so the recorded SHA-256 matches the bytes on disc on any host.
    args.output.write_bytes(text.encode("ascii"))

    counts = document["evidence_label_counts"]
    run = document["run"]
    print(
        "Wrote %s\n  frames=%d events=%d\n  evidence: %s\n  sha256=%s"
        % (
            args.output.relative_to(ROOT),
            run["frame_count"],
            len(document["semantic_events"]),
            ", ".join("%s=%d" % (key, counts[key]) for key in sorted(counts)),
            digest,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
