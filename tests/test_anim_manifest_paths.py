#!/usr/bin/env python3
"""Manifest paths must stay lexical repository-relative paths.

The animation-record manifest previously serialized absolute junction
TARGET paths because manifest_path() used Path.resolve(), which follows
NTFS junctions (the private .deps/avspu directories are junctioned into
correction worktrees). This test creates a real junction inside build/,
routes the same file through it and through the ordinary relative path,
and requires:

1. both serializations are repository-relative forward-slash paths;
2. the junctioned route keeps its lexical spelling (never rewritten to
   the junction target, never absolute);
3. a path outside the repository is rejected.

No private inputs are needed; the junction targets tracked data/.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from gen_avsp_anim_records import manifest_path  # noqa: E402

JUNCTION = ROOT / "build" / "manifest_path_junction"


def main() -> None:
    (ROOT / "build").mkdir(exist_ok=True)
    if JUNCTION.exists():
        subprocess.run(["cmd", "/c", "rmdir", str(JUNCTION)], check=True)
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(JUNCTION), str(ROOT / "data")],
        check=True, stdout=subprocess.DEVNULL)
    try:
        direct = manifest_path(ROOT / "data" / "avsp_anim_records.json")
        assert direct == "data/avsp_anim_records.json", direct

        through = manifest_path(JUNCTION / "avsp_anim_records.json")
        assert through == \
            "build/manifest_path_junction/avsp_anim_records.json", through
        assert ":" not in through and not through.startswith("/"), through

        # Same file, junctioned parent directory in the middle of the
        # path: the serialization must stay lexical, not follow the
        # junction to data/'s absolute location.
        assert (JUNCTION / "avsp_anim_records.json").read_bytes() == \
            (ROOT / "data" / "avsp_anim_records.json").read_bytes()

        try:
            manifest_path(ROOT.parent / "outside.json")
        except SystemExit:
            pass
        else:
            raise AssertionError("path escaping the repository accepted")
    finally:
        subprocess.run(["cmd", "/c", "rmdir", str(JUNCTION)], check=True)
    print("manifest paths: lexical repo-relative through junctions, "
          "escapes rejected")


if __name__ == "__main__":
    main()
