#!/usr/bin/env python3
"""Run the shared paired-evidence validator for PcmPromotionBench."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]


def main() -> None:
    subprocess.run([
        sys.executable, "-B",
        str(ROOT / "tests/port_v2/hud_pcm_bench/test_evidence.py"),
        "--suite", "pcm",
    ], check=True)


if __name__ == "__main__":
    main()
