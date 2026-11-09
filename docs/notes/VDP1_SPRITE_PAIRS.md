# Optional vertical sprite pairs

Evidence: **HOST**. Target link, MAME, Yaba and Saturn hardware: **UNRUN**.
Based on the renderer at `37c5b4a3a6f9276bbcad79530f539b3c61cada3b`.

## Purpose and scope

The first recommended experiment is `SAT_GFX_PAIR_REUSE=1`. It uses the
ordinary tile cache and joins an eligible two-tile column only when its
two source textures occupy adjacent slots. It keeps both ordinary texture
lookups and emits one VDP1 command instead of two. It reserves no VRAM,
creates no extra texture copies, and changes no pack data. The default is
zero, pending representative target measurements.

The alternative `SAT_GFX_SPRITE_PAIRS=16` or `32` enables a fixed cache of
that many 16-by-32 textures. Its hot pairs use one texture lookup and one
VDP1 command, but it reserves ordinary texture slots and can increase
uploads. This is a comparison experiment, not the first choice. Both
options cannot be enabled together. Both draw the same pixels and source
texels; neither establishes a frame-rate gain or fivefold command reduction.

The renderer already uses packed four-bit textures and removes empty and
offscreen tiles. This experiment joins vertical neighbours inside a CPS
object, for arbitrary object widths. The current Wolverine guest emits
individual one-by-one objects with canonical tile IDs, so it does not gain
pair batching from this path. Grouping those poses is separate work.

Only two complete, visible, vertically adjacent rows are joined. The pair
must not wrap through the ten-bit coordinate boundary. Missing or blank
members fall back to the individual-tile path. The reserved-cache variant
also falls back on protected collisions and its cold-upload limit. Partial vertical edges
use individual tiles. Horizontal clipping remains the existing path.
Object ordering, palette/priority bits, mirrors and transparent pens are
preserved. Builds combining either experiment with `SAT_KEYLOG`,
`SAT_READOUT`, or `SAT_ABL` are rejected: those coverage/fill/ablation
captures must use the original tile path. In particular, reserved pair
uploads must not bypass the key-coverage logger and underfill future packs.

Vertical pairing deliberately keeps the original horizontal endpoints of
each 16-pixel tile at FIT=1. Its X sampling is unchanged, and Y stays 1:1.
A horizontal strip would introduce a different sampling sequence across
the joined width; it is not enabled by this experiment.

## Storage and ownership

### Ordinary cache reuse

`SAT_GFX_PAIR_REUSE` requests both members in canonical source order. Cold
ordinary allocations can therefore be adjacent; warm nonadjacent entries
remain two commands. A 16-entry `unsigned short` array retains upper-row
answers until that row is processed, so a failed adjacency check does not
add a third lookup. Its declared array storage is 32 stack bytes, plus 16
bytes for saved diagnostic causes with `SAT_VLOG`. There is no additional
persistent metadata. Actual SH-2 stack/code size remains unmeasured.

All allocation, stamps and uploads stay in the existing cache machinery.
The first lookup is protected before the second can allocate. Prefetched
missing/refused answers retain their own cause and are not counted twice.
At extreme cache pressure, changed lookup order can change which tile
survives a refusal. Target acceptance requires no added texture refusals
and no missing art; preserving capacity does not prove identical eviction
behaviour in every scene. No extra copy is introduced specifically for
pairing, but ordinary uploads can still differ if cache order changes.

For integration with previous-list slot hints, both source-order lookups
must consume a hint position. A retained or merged upper-row tile has
already consumed its lookup and must not consume another. Every hint must
still validate its current key and the ordinary cache's first valid slot.

### Reserved comparison cache

The source pack format and asset bytes are unchanged. A cold miss copies
the existing payload for key K and then key K+16 into contiguous texture
slots. Concatenating these two row-major tiles already forms a 16-by-32
texture; no temporary image, transpose, or per-frame pixel composition is
needed. Main and spilled payloads follow the same pack addressing rules.

| Setting | Reserved VDP1 bytes | Ordinary slots remaining | Added persistent metadata |
| --- | ---: | ---: | ---: |
| 0 | 0 | 3584 | 0 |
| Reuse | 0 | 3584 | 0 |
| 16 | 4096 | 3552 | 0 |
| 32 | 8192 | 3520 | 0 |

The reservation uses the existing VDP1 texture allocation. The records
for those reserved slots already exist in `spr_slots`; the ordinary
cache's first usable slot moves past the reservation. The even record
holds the pair key, ownership stamp and valid/negative state. Both
records retain the ownership stamp. The unused `next` field in reserved
slot 1 holds the current build's cold-admission count.

`SAT_GFX_PAIR_UPLOAD_BUDGET` defaults to two pairs per build, bounding pair
creation to 512 bytes of copies. Hot pair hits do not consume the budget.
This is a bound on pair creation, not on total uploads: ordinary cache
misses still occur, and reserving ordinary slots can affect their churn.
Increasing the budget requires measurement.

Neither a current build nor the previous submitted plot's pair can be
evicted. The existing abandoned-build stamp restoration covers both
records, including a cache hit shared with the preceding plot. Negative
pair entries are invalidated when stage packs change; valid entries keep
the renderer's existing contract that a tile key retains its pixels.

The runtime code itself occupies space. A target linker map is still
required before enabling this on a disc. Optional
`SAT_GFX_PAIR_STATS` adds four target `unsigned long` counters (16 bytes):
`sat_gfx_pair_hits`, `sat_gfx_pair_uploads`, `sat_gfx_pair_fallbacks`, and
`sat_gfx_pair_saved`. They accumulate until graphics initialization.
Pair uploads count pairs; the existing `sat_gfx_stats.uploads` continues
to count 128-byte tile payloads, including both halves of each pair.
In reuse mode `sat_gfx_pair_hits` counts successful adjacent pairs,
`sat_gfx_pair_fallbacks` counts failed adjacency checks, and
`sat_gfx_pair_uploads` stays zero.

## Host verification

Run:

```sh
python -m unittest discover -s tests -p test_vdp1_sprite_pairs.py -v
```

The harness compiles the actual production renderer with strict C90
warnings and synthetic, asymmetric pixel data. Its pixel oracle checks
8,044 frames per configuration against pair count zero: FIT 0, 1, 2, and
both runtime settings of FIT 3, each with reuse, 16 and 32 pairs. The corpus
covers every horizontal scale phase, both mirrors and their combination,
odd/even source codes, dimensions through 16-by-16 tiles, screen edges,
ten-bit wrap, origin offsets, transparency, missing tiles, and overlapping
objects. It includes cache-hot repeats and changing poses.

Separate tests cover admission limits, both command-table boundaries,
current/previous ownership, abandoned shared hits, stamp wrap, reinit,
pack-swap negative invalidation, split main/spill addressing, and a full
draw that must not touch a still-active plot's textures. Reuse has direct
tests for noncontiguous slots and either missing, blank or refused member
under both vertical mirrors, including diagnostic cause accounting.
Deliberately wrong second-tile data, a removed previous-plot guard and an
unsafe noncontiguous merge fail their gates.

The pixel oracle runs below command capacity. Above capacity, batching
can allow additional objects to be drawn, so equality to the truncated
reference is not the desired result. That case instead checks the hard
command-table limit and refusal accounting. A refused pair is one
refused command representing two tiles.

On the synthetic FIT=1 corpus with the default two-pair admission budget:

| Configuration | Commands over 8,044 frames | Tile uploads |
| --- | ---: | ---: |
| Individual tiles | 375,947 | 796 |
| Ordinary cache reuse | 265,676 | 796 |
| 16 pairs | 334,139 | 23,134 |
| 32 pairs | 323,412 | 22,280 |

These are coverage-test totals, not gameplay samples. Reuse removes
29.3% of commands with equal uploads in this corpus. The reserved variants
remove 11.1% and 14.0%, with more texture traffic. Before the admission cap, the 16-pair run uploaded
45,650 tile payloads. The option remains off until a representative
scene proves a net benefit. The disabled HOST `-O2` `.text` section was
also compared byte-for-byte with the unmodified base renderer; it was
identical. This is not an SH-2 binary-size claim.

## Target decision

Compare the same scene, input sequence and seed with both flags zero,
then `SAT_GFX_PAIR_REUSE=1`, alongside the existing frame-chain profiler.
The reserved variants are optional later comparisons. Record commands,
pair hits/fallbacks, pair and total uploads, sprite-build time, whole
slave time, vblank cadence and actual new pictures. Keep the feature
only if saved command work outweighs any lookup-order/cache effects and
there are no added texture refusals or missing art. A hardware run must confirm
the scaled 16-by-32 commands and overall timing before claiming a
Saturn frame-rate improvement.
