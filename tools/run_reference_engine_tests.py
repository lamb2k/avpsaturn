#!/usr/bin/env python3
"""Run the reference-engine test suite.

Kept as a script because the repository's bundled Python is not on PATH and
``tests/`` also holds C sources, so it is not an importable package.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE_DIR = ROOT / "tests" / "reference_engine"


def main() -> int:
    for path in (str(ROOT), str(SUITE_DIR)):
        if path not in sys.path:
            sys.path.insert(0, path)
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(SUITE_DIR), top_level_dir=str(SUITE_DIR))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
