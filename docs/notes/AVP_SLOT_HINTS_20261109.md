# Previous-list sprite-slot hints

Date: 2026-11-09, America/New_York. Evidence: **HOST, synthetic**.
Base: frame-chain `37c5b4a3a6f9276bbcad79530f539b3c61cada3b`.
SH-2 link, private assets, emulator timing and Saturn qualification: **UNRUN**.

## Why this experiment

The current frame-chain lane attributes about 54% of command-build cost to the
slot lookup/upload path in a Yaba ablation. Its 64/256-entry tile-key memo did
not produce a clear gain. This experiment uses a different source of locality:
the slot used by the same visible tile position in the preceding list build.

Enable one build with `-DSAT_GFX_SLOT_HINTS=512` in `KERNEL_CFLAGS`. The option
defaults to zero. At 512 entries it adds exactly 1,024 bytes of declared 16-bit
hint storage in ordinary high work RAM, before linker alignment/code growth.
There is no added low work RAM or VDP1 texture allocation. Values 1..1024 are
supported; the actual target link must approve the chosen size.

Each in-range hint stores only a slot number. The fast path checks that the
slot is valid and its live tile key matches the requested key. On a mismatch,
blank/missing tile, eviction, object-list reorder or animation change, normal
lookup remains authoritative. The first configured number of visible tile
queries receive hints; further queries follow the original lookup.

A hit performs the original current-frame stamp/used-count work, updates the
existing two-entry memo and preserves diagnostic causes. Texture ownership is
unchanged: the existing aborted-submission scan also protects hinted hits.
Initialization resets every hint. Stage swaps retain the existing contract
that a tile key always names the same pixels, and continue validating live keys.
Only the slave accesses hint and cache state.

With the option disabled, the array, lookup helper, counters and loop bookkeeping
are removed at preprocessing. Do not combine lookup ablations with a performance
claim for hints: an ablation that removes lookup is not a valid picture.

## Measurement

Optionally add `-DSAT_GFX_SLOT_HINT_STATS` for four cumulative 32-bit target
counters (16 additional declared bytes): `queries`, `hits`, `fallbacks` and
`beyond_limit`, in `sat_gfx_slot_hint_stats`. They reset at graphics init.
Capture counter deltas for one fixed route. Hits + fallbacks + beyond_limit
must equal queries. The counters measure avoided hash traversals, not saved
milliseconds. Use a separate counters-off build for release timing.

Compare the same stage-02 fight inputs and emulator/core settings at 0, 512 and,
only if the target fits, 1024 entries. Record whole-frame mean/p95/max and missed
presentation deadlines as well as command-build time. Animated/reordered lists
can turn hints into extra work; retain the feature only with a repeatable net
gain and unchanged pictures. The existing frame-chain measurements have several
percentage points of seed noise, so one short successful run is insufficient.

## Host verification

Run:

```sh
python -m unittest discover -s tests -p test_sprite_slot_hints.py -v
```

The actual production driver is compiled under strict C90 at hint sizes 1, 64,
512 and 1024, with crop/fit, readout, VLOG and profiling combinations. Cases cover
warm hits, re-used counts, wrong-key eviction, out-of-range hints, blank/missing
tiles, stage swap, reinitialization, stamp rollover and abandoned texture hits.
The existing presentation fixture also runs with hints enabled.

The existing randomized all-layer harness runs 600 frames at each of FIT=0 and
FIT=1 with hints off/on. Every VDP1/VDP2/CRAM/register hash, command count and
upload count must match. On this candidate these checks pass. They establish
output identity on synthetic input, not a new fps result.

The source-function/behaviour-match ledger is unchanged: this is graphics-adapter
work. Current MAME golden counts remain those of the pinned base; this candidate
has no new private whole-game comparison.
