#!/usr/bin/env python3
"""Failing-first controls for official 1.20.37 source/patch provenance."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".deps" / "yabasanshiro-src-1.20.37" / "yabasanshiro-1.20.37"
ARCHIVE = ROOT / ".deps" / "source-archives" / "yabasanshiro-src-1.20.37.zip"
VERIFY = ROOT / "tools" / "verify_yabasanshiro_1_20_37_scanout.py"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(VERIFY), *args], text=True,
                          capture_output=True)


def main() -> int:
    if not SOURCE.is_dir() or not ARCHIVE.is_file():
        print("official scanout provenance test: skipped (ignored official source/archive absent)")
        return 0
    passed = run("--source", str(SOURCE), "--archive", str(ARCHIVE),
                 "--negative-controls")
    if passed.returncode:
        print(passed.stdout, end="")
        print(passed.stderr, end="", file=sys.stderr)
        return passed.returncode
    tico = ROOT / ".deps" / "yabasanshiro-source"
    if tico.is_dir():
        rejected = run("--source", str(tico), "--archive", str(ARCHIVE))
        if rejected.returncode == 0:
            print("Tico source was incorrectly accepted", file=sys.stderr)
            return 1
        print("negative control rejected: historical Tico source")
    print(passed.stdout, end="")
    print("official scanout provenance test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
