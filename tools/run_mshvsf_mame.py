#!/usr/bin/env python3
"""Run the authorized MSHvSF reference through a disposable MAME ROM layout."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from audit_mshvsf_reference import mame_rompath_overlay


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mame",
        type=Path,
        default=Path(".deps/mame/mame0289/mame.exe"),
    )
    parser.add_argument(
        "--reference-root",
        type=Path,
        default=Path("Marvel Super Heroes vs. Street Fighter"),
    )
    parser.add_argument(
        "mame_args",
        nargs=argparse.REMAINDER,
        help="MAME arguments after --; defaults to a five-second headless boot.",
    )
    args = parser.parse_args()

    mame_args = args.mame_args
    if mame_args and mame_args[0] == "--":
        mame_args = mame_args[1:]
    if not mame_args:
        mame_args = [
            "mshvsf",
            "-video",
            "none",
            "-sound",
            "none",
            "-nothrottle",
            "-skip_gameinfo",
            "-seconds_to_run",
            "5",
        ]

    rom_source = args.reference_root.resolve() / "Mame"
    with mame_rompath_overlay(rom_source) as overlay:
        command = [str(args.mame.resolve()), *mame_args, "-rompath", str(overlay)]
        display = [*command]
        display[-1] = "<temporary-mame-rompath>"
        print("Command:", subprocess.list2cmdline(display))
        result = subprocess.run(command, check=False)
        return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
