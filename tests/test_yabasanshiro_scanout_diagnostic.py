#!/usr/bin/env python3
"""Run the portable wrong-base/corruption controls for the rejected hook."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / ".deps" / "yabasanshiro-source"


def main() -> int:
    source = Path(sys.argv[1]) if len(sys.argv) == 2 else DEFAULT_SOURCE
    if not source.is_dir():
        print("scanout diagnostic test: source absent; tracked verifier not executed")
        return 0
    with tempfile.TemporaryDirectory(prefix="yb-scanout-test-") as temporary:
        clean = Path(temporary) / "clean"
        result = subprocess.run(["git", "clone", "--quiet", "--no-hardlinks",
                                 str(source), str(clean)], text=True)
        if result.returncode:
            raise SystemExit("cannot create clean diagnostic source clone")
        result = subprocess.run([
            sys.executable, str(ROOT / "tools" /
                                "verify_yabasanshiro_scanout_diagnostic.py"),
            "--source", str(clean), "--negative-controls"], text=True)
        if result.returncode:
            return result.returncode
    print("scanout diagnostic test: clean apply and negative controls hold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
