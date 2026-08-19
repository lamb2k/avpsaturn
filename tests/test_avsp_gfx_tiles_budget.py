"""Negative test: the tile generator must refuse an over-budget archive.

Proves tools/gen_avsp_gfx_tiles.py's budget guard actually guards: a
--scope round1 archive (612,720 bytes, MEASURED) must be REFUSED against
the runtime's real AVSP_TILE_REGION_BYTES carve (262,144 bytes, parsed
live from main.c, never hardcoded here so this test cannot drift out of
sync with the runtime). Also proves the on-disk archive and manifest are
left untouched by a refused run, and that --scope street still succeeds
and fits.

Requires the private captures and program image; skips cleanly without
them (matching every other test in this suite that depends on private
inputs).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools" / "gen_avsp_gfx_tiles.py"
ARCHIVE = ROOT / "build" / "avsp_cd" / "SPR4" / "TILES.BIN"
MANIFEST = ROOT / "data" / "avsp_gfx_tiles.json"
CAPTURE_ROOT = ROOT / ".deps" / "mame" / "enemy_actions"


def run(args):
    return subprocess.run([sys.executable, str(GENERATOR)] + args,
                          cwd=str(ROOT), capture_output=True, text=True)


def main() -> int:
    if not CAPTURE_ROOT.is_dir():
        print("test_avsp_gfx_tiles_budget: SKIP (private captures absent)")
        return 0

    # Establish a known-good baseline so the refused run's "untouched"
    # claim is checked against something, not against build/ debris.
    baseline = run(["--scope", "street"])
    if baseline.returncode != 0:
        print("FAIL: baseline --scope street run failed:\n" +
              baseline.stdout + baseline.stderr)
        return 1
    before_bytes = ARCHIVE.read_bytes()
    before_manifest = json.loads(MANIFEST.read_text())
    if before_manifest["scope"] != "street":
        print("FAIL: baseline manifest scope is not 'street'")
        return 1

    refused = run(["--scope", "round1"])
    if refused.returncode == 0:
        print("FAIL: --scope round1 was accepted; it must be refused "
              "against the current AVSP_TILE_REGION_BYTES carve")
        return 1
    if "REFUSING to write" not in refused.stdout + refused.stderr:
        print("FAIL: round1 run failed for the wrong reason:\n" +
              refused.stdout + refused.stderr)
        return 1

    after_bytes = ARCHIVE.read_bytes()
    after_manifest = json.loads(MANIFEST.read_text())
    if after_bytes != before_bytes:
        print("FAIL: the refused round1 run modified the archive on disk")
        return 1
    if after_manifest != before_manifest:
        print("FAIL: the refused round1 run modified the manifest")
        return 1

    print("test_avsp_gfx_tiles_budget: PASS (round1 refused at %d bytes "
         "vs a %d-byte carve; street archive and manifest untouched)"
         % (612720, before_manifest["tile_region_budget_bytes"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
