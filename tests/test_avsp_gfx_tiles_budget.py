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
import re
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
    residency = before_manifest["presentation_residency"]
    if (residency["source_peak_unique_tiles"] != 374 or
        residency["source_peak_frame"] != 2357 or
        residency["projectile_simultaneous_bound"] != 12 or
        residency["max_tiles_per_projectile"] != 4 or
        residency["max_tiles_per_impact"] != 2 or
        residency["per_tile_scanout_requirement"] != 446 or
        residency["composite_tile_threshold"] != 35 or
        residency["spec02_composite_unique_entries"] != 5 or
        residency["spec02_composite_texture_bytes"] != 36736 or
        residency["spec02_composite_max_texture_bytes"] != 11648 or
        residency["configured_composite_slots"] != 5 or
        residency["configured_composite_texture_budget"] != 36736 or
        residency["configured_composite_max_texture_bytes"] != 11648 or
        residency["startup_source_frame_range"] != [2074, 2253] or
        residency["startup_peak_noncomposite_tiles"] != 162 or
        residency["startup_peak_noncomposite_frame"] != 2208 or
        residency["retained_tile_sprite_pool"] != 208 or
        residency["mid_frame_lru_replacement_allowed"] is not False):
        print("FAIL: first-segment presentation residency drifted")
        return 1
    makefile = (ROOT / "makefile").read_text(encoding="utf-8")
    jo_max_match = re.search(r"^JO_MAX_SPRITE\s*=\s*(\d+)$", makefile,
                             re.MULTILINE)
    if (jo_max_match is None or int(jo_max_match.group(1)) != 255 or
        int(jo_max_match.group(1)) <
            residency["configured_composite_slots"] +
            residency["retained_tile_sprite_pool"] + 32):
        print("FAIL: Jo sprite-definition bound/headroom drifted")
        return 1
    if ("$(JO_ENGINE_SRC_DIR)/sprites.o "
            "$(JO_ENGINE_SRC_DIR)/3d.o: makefile" not in makefile):
        print("FAIL: JO_MAX_SPRITE-dependent engine objects can become stale")
        return 1
    build_script = (ROOT / "build.ps1").read_text(encoding="utf-8")
    if ("$requiredSpriteArrayBytes = 255 * 8" not in build_script or
            "$spriteArrayDistance -lt $requiredSpriteArrayBytes" not in
            build_script):
        print("FAIL: target link does not reject overlapping Jo sprite arrays")
        return 1
    required_sprite_array_bytes = int(jo_max_match.group(1)) * 8
    if (abs(0x060BE97C - 0x060BED7C) >= required_sprite_array_bytes or
            abs(0x060BE568 - 0x060BED60) < required_sprite_array_bytes):
        print("FAIL: stale-array mutation control is non-discriminating")
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
