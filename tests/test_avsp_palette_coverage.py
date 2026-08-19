"""Pin the tile-archive palette gap open so it cannot widen silently.

data/avsp_palette_coverage.json records that the shipped archive carries a
single-frame ADAPTED palette while the captured routes reference more banks
than it holds. That is correctly harmless today - the ROM tile path renders
street aliens only, and their banks are shipped - and it is deliberately NOT
fixed now, because the consumer that needs full coverage is the S3 full-cast
tile path, and regenerating ahead of a consumer is how this project has
previously produced correct-but-unusable data.

The risk that creates is silent drift: someone widens the archive scope, the
palette stays a single-frame snapshot, and actors render with resolved-to-wrong
or unresolvable banks. These checks make that failure loud.

Checks:
  A  every shipped bank is one the routes actually reference (catches a bogus
     or stale bank in the manifest);
  B  while uncovered banks exist, the archive scope must still be `street` -
     widening scope without widening the palette fails here;
  C  the coverage artifact is non-vacuous (it sampled frames and found banks).

Skips cleanly (exit 0) when the coverage artifact or the tile manifest is
absent, matching tests/test_avsp_gfx_tiles_budget.py's contract.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COVERAGE = ROOT / "data" / "avsp_palette_coverage.json"
TILES = ROOT / "data" / "avsp_gfx_tiles.json"

FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    if condition:
        return
    FAILURES.append(message)
    print("  FAIL:", message)


def main() -> int:
    if not COVERAGE.is_file() or not TILES.is_file():
        print("palette coverage test: SKIPPED - artifact or tile manifest "
              "absent; regenerate with tools/analyze_avsp_palette_coverage.py")
        return 0

    coverage = json.loads(COVERAGE.read_text())
    tiles = json.loads(TILES.read_text())

    shipped = {int(b, 16) for b in coverage.get("shipped_banks", [])}
    routes = coverage.get("routes", [])
    check(bool(shipped), "coverage artifact records no shipped banks")
    check(bool(routes), "coverage artifact records no routes")
    if not routes or not shipped:
        print("\n%d check(s) failed" % len(FAILURES))
        return 1

    referenced: set[int] = set()
    uncovered: set[int] = set()
    sampled = 0
    for route in routes:
        referenced |= {int(b, 16) for b in route.get("banks_referenced", [])}
        uncovered |= {int(b, 16) for b in route.get("uncovered_banks", [])}
        sampled += route.get("frames_sampled", 0)

    # C - non-vacuous
    check(sampled > 0, "no frames were sampled; the artifact proves nothing")
    check(bool(referenced), "no colour banks were referenced in any route")

    # A - shipped banks must be real
    stale = sorted(shipped - referenced)
    check(not stale,
          "shipped bank(s) %s are referenced by no captured route - the "
          "archive palette may be stale or wrong"
          % ["0x%02X" % b for b in stale])

    # B - the gap is pinned to the street scope
    scope = tiles.get("scope")
    if uncovered:
        check(scope == "street",
              "the archive palette still misses %d bank(s) %s, so its scope "
              "must remain 'street'; scope is '%s'. Widening the tile archive "
              "requires widening the palette in the same change."
              % (len(uncovered),
                 ["0x%02X" % b for b in sorted(uncovered)][:8], scope))

    if FAILURES:
        print("\n%d check(s) failed" % len(FAILURES))
        return 1
    print("palette coverage test: PASS - shipped %d banks, routes reference "
          "%d, %d uncovered, scope='%s' (gap pinned)"
          % (len(shipped), len(referenced), len(uncovered), scope))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
