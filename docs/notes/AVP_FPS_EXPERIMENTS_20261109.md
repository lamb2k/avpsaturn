# Next frame-rate experiments, 2026-11-09

## Result and evidence boundary

Two source candidates are supplied:

- `codex/avp-fps-next-20261109`, based on frame-chain `37c5b4a3a6f9276bbcad79530f539b3c61cada3b`.
- `codex/avp-wolverine-fps-next-20261109`, based on Wolverine-disc `dd295f20d43ba7cbd9d42f7d502ff1fc0390491e`, with the current frame-chain runtime brought across while preserving the guest, asset selection and build gates.

The new performance experiments default off. The first target candidate is ordinary-cache vertical pairing: it removes commands without reserving more texture VRAM or creating extra texture copies. Previous-list slot hints, a master availability recorder, a bounded reserved-pair comparison, and a partial hardware erase experiment are also implemented.

**New evidence is HOST only. No new gameplay FPS result, SH-2 linked fit, disc, MAME comparison, Yaba run, or Saturn run is claimed.** The current environment has no SH-2 toolchain, console emulator session or private build inputs. Synthetic packs are used for all new graphics checks. Older target results below belong to their pinned builds and do not qualify these candidates.

## What the current branch already established

The initial 22% held-picture diagnosis is superseded by the frame-chain work. In the profile B configuration, stage 02 Warrior, three seeds of 400 refreshes, its documented Yaba VideoCore 1 results were:

| Measurement | Before | Current frame-chain |
| --- | ---: | ---: |
| New pictures / refreshes | 73.2% | 88.3% |
| Held because the plot was unfinished | 22.4% | 0.4% |
| Late cadence | 2.4% | 11.3% |
| Mean submit time, FRT ticks from IN | 3010 | 2230 |

These are stepped, modelled emulator measurements, not Saturn timings. The remaining slow slave frames reach roughly 3600–3700 ticks against a modelled 3495-tick field. The VLOG A series is a different build and must not be pooled with B. The earlier serial chain submitted too late; its held pictures did not prove that physical VDP1 pixel throughput was the dominant cost.

The current base already overlaps the master layer snapshot with slave command construction, packs cache-node metadata into eight bytes, hoists row arithmetic, skips offscreen rows and uses five long command writes instead of nine word writes. It already uses four-bit bank textures, without half transparency or Gouraud. Repeating those changes is not a new optimization.

Evidence: [pinned frame-chain STATUS](https://github.com/lamb2k/avpsaturn/blob/37c5b4a3a6f9276bbcad79530f539b3c61cada3b/docs/STATUS.md), sections “Frame chain”, “VDP1 held frames”, and the earlier command-shadow comparison.

## Decisions on the six proposals

| Proposal | Decision and implementation |
| --- | --- |
| Split sprite-list building between the CPUs | The master is not established to be idle: it copies layers and runs the game. Added `SAT_CPU_SLACK_PROFILE` plus a decoder that joins master windows to source-frame graphics records. A second command builder is not enabled. Its useful phase, available time and ownership design still need measurement. |
| Previous-list tile-slot hints | Implemented `SAT_GFX_SLOT_HINTS=N`. A two-byte positional hint is accepted only if the current slot is in the ordinary cache and still holds the requested key. Hits retain current/previous-plot ownership and the existing two-entry memo. Invalid hints use the normal lookup. This differs from the earlier direct-mapped key memo that showed no clear gain. |
| Write only changed command values | Deferred on contrary evidence: the earlier command shadow worsened Yaba graphics mean/p95/top from 7.62/18.9/50.6 ms to 8.51/21.95/52.43 ms. The current renderer already has wide writes. Revisit only if hardware establishes a write bottleneck and a specific shadow design has a measured net benefit. |
| Combine tiles into larger sprites | Implemented vertical 16×32 pairing, first using adjacent ordinary texture slots and alternatively a bounded reserved cache. Eligible pairs use one command instead of two. Whole-pose packing and a fivefold whole-frame reduction are not implemented or demonstrated. |
| Hardware screen clear | Implemented a guarded partial erase plus a remainder polygon. A full 352×224 V-blank erase exceeds Sega's stated budget. Hardware timing and interrupt behavior must be checked before enabling it on a normal disc. |
| Measure on a Saturn | Added exact experiment selection, counters, capture guidance and acceptance criteria. Physical execution remains unrun; neither host checks nor Yaba's raster model can replace it. |

## Best new candidate: reuse adjacent texture slots

`SAT_GFX_PAIR_REUSE=1` asks the existing cache for two vertical neighbours in source order. When the slots are physically contiguous it emits one 16×32 sprite. Otherwise it retains the lookup answers and emits the original separate tiles, avoiding a third lookup. It changes no pack format and reserves no VRAM. The two halves keep their palette, priority and mirror behavior. Vertical joining preserves FIT=1's existing horizontal sampling.

On the synthetic FIT=1 pixel corpus, 8,044 frames:

| Mode | Commands | 128-byte tile uploads |
| --- | ---: | ---: |
| Separate tiles | 375,947 | 796 |
| Ordinary-cache reuse | 265,676 | 796 |
| Reserved 16-pair cache, capped | 334,139 | 23,134 |
| Reserved 32-pair cache, capped | 323,412 | 22,280 |

Reuse saved 110,271 commands, **29.3%**, with the same uploads in this corpus. This is a command-count result, not a timing or FPS result. The reserved cache's extra traffic is why it is a secondary comparison. Changed ordinary lookup order can affect refusals at full capacity; no additional missing art or texture refusals is an acceptance condition.

Wolverine currently emits one-tile guest objects. This pairing path helps native multirow CPS objects, including other actors in a Wolverine fight; it does not directly combine Wolverine's individual guest tiles. Whole-pose guest packing remains future work with separate residency and sampling checks.

Details: [VDP1_SPRITE_PAIRS.md](VDP1_SPRITE_PAIRS.md).

## Options and declared storage

Append the selected option to the existing `KERNEL_CFLAGS`; retain the original guest/menu/scene flags. The build script passes these flags to both graphics and kernel. Each row below is a separate experiment first, not an instruction to enable everything together.

| Option | Declared additional storage, before target code/alignment |
| --- | --- |
| All options off | No new experiment storage; renderer HOST `.text` is byte-identical to the pinned base at FIT 0 and 1 |
| `-DSAT_GFX_PAIR_REUSE=1` | No persistent metadata or reserved VRAM; 32-byte retained-answer stack array, plus 16 bytes with VLOG |
| `-DSAT_GFX_SLOT_HINTS=512` | 1024 bytes high-work-RAM BSS; reduce N if the actual link requires it |
| `-DSAT_CPU_SLACK_PROFILE -DSAT_CPU_SLACK_DEPTH=4` | 232 bytes high-work-RAM BSS; depth 2 uses 144, default depth 16 uses 760 |
| `-DSAT_VDP1_HW_ERASE=1` | 28 bytes high-work-RAM BSS; IRQ save space and total target stack are still unmeasured |
| `-DSAT_GFX_SPRITE_PAIRS=16` / `32` | Reserves 4 KB / 8 KB from existing VDP1 texture allocation; reuses existing slot records |
| `-DSAT_GFX_PAIR_STATS` | 16 bytes of counters when a pair mode is enabled |
| `-DSAT_GFX_SLOT_HINT_STATS` | 16 bytes of counters when hints are enabled |

None of these new data structures uses low work RAM. All enabled code still consumes link space. The prior Wolverine image's 1148 high / 140 low bytes free is not this integration's headroom; the new target linker map decides fit. Existing VDP1 profiling has its own memory requirements and may need a smaller ring or a separate build. Pair modes are mutually exclusive and intentionally reject KEYLOG, READOUT and ABL captures; collect key coverage using the ordinary path.

The master recorder measures a scheduler-completion window, an **upper bound on available time**. The sample is before `f_11ec`; subsequent work and the slave's phase must be traced before treating any of the window as idle. Its decoder never subtracts one CPU's timer from the other CPU's timer. Details: [CPU_SLACK_PROFILE.md](CPU_SLACK_PROFILE.md) and [AVP_SLOT_HINTS_20261109.md](AVP_SLOT_HINTS_20261109.md).

## Partial hardware erase

Sega's manual gives a 63,180-pixel V-blank erase budget in NTSC 352×224 mode. The full display is 78,848 pixels. The experiment erases the top 160 rows and retains a polygon for the bottom 64; its conservative erase-area calculation is 57,600, within that budget. The polygon's area falls to 22,528 pixels on eligible submissions. This is not a claim that half the render time disappears.

Reduction requires primed erase bounds, the correct physical-buffer change serial, completed OUT cleanup, a confirmed cleared CEF, and zero local origin. First plots, uncertain latches and load/restart recovery keep full clear. The old active command list is never rewritten during missing-end recovery. A bounded suspension handles long loads while their interrupts are masked. The SH-2 OUT interrupt entry, display deadlines and stack behavior require target validation.

Primary source: Sega [VDP1 User's Manual ST-013-R3-061694](https://antime.kapsi.fi/sega/files/ST-013-R3-061694.pdf), printed pages 35–36, 40 and 47–50. Implementation and capture details: [VDP1_HARDWARE_ERASE.md](VDP1_HARDWARE_ERASE.md).

## Wolverine integration boundary

The Wolverine candidate retains the previous simulation-clock hold fixes, atomic pose publication, guest slot replacement and strict pack/cache/fit gates. It adds the current split snapshot, compact cache representation, wide command writes, bounded stuck-CEF recovery, and the default-off experiments. Guest replacement remains in the first snapshot half before waking the slave.

Its base lane's disc qualification records a full 21-step walk, full LP, HP 11/15 poses, 1511 tiles, and 76/76 stage files fitting. HP reached 51–66 logical ticks, LP 16–24; HK was not reached. Those results qualify the older disc, not this new runtime. See [pinned Wolverine-disc qualification](https://github.com/lamb2k/avpsaturn/blob/dd295f20d43ba7cbd9d42f7d502ff1fc0390491e/docs/notes/AVP_WOLVERINE_DISC_V3_20261108.md).

Rebuild and recheck the actual link, all stage fits and the owner's VideoCore 1 sprite display. HUD portrait, invisible-Wolverine closure and complete HP pose residency remain open. No private sprite/ROM assets, generated disc or function-ledger changes are included here.

## Verification and next target run

The integrated Wolverine candidate passed all **61 Python tests**, including the combined configurations below. Its guest-enabled renderer also passed strict C90 syntax checks with pairing, hints, erase, VLOG and profiling enabled together. Run `python -m unittest discover -s tests -v`. The new tests compile the production renderer and recorder with strict C90 warnings. They cover stale hint validation, eviction and abandoned plots; pixel identity across FIT modes, mirrors, wrap, clipping, transparency and overlapping objects; pair admission, both command-table limits and cache ownership; two-buffer erase coverage with separately programmed and latched registers; recorder publication, overflow and source-vblank joins. Wrong-payload, unsafe-adjacency and lost-ownership mutations fail. Combined pair/hint, erase/pair/hint and presentation configurations are included. The Wolverine suite also retains its clock, fit, extraction and pack-cache regressions.

Target sequence:

1. Build the exact new source with experiments off. Record the SHA, complete flags, map headroom, asset selection, emulator/core and inputs. Verify the Wolverine sprite path on VideoCore 1 before performance comparisons.
2. Compare ordinary-cache reuse alone to that baseline over matched fights, several seeds and repeated windows. Record build and submit distributions, total slave time, command count, uploads/refusals, and actual new-picture/held/skip/late shares. Inspect pixels and cache-pressure scenes. Mean build time alone is insufficient: the slow-frame tail is the problem.
3. Run hints alone at a size that links; collect hit/fallback counts in a diagnostic build and compare cadence with diagnostics disabled. Combine with reuse only if both improve the same target workload.
4. Use the master recorder separately to establish relevant completion windows and trace remaining work. Implement a CPU split only if useful work plus a reserve fits those windows, with one owner for cache residency and VRAM writes.
5. Run partial erase on a physical Saturn against its identical baseline. Check both buffers, trails, origins, stage loads, menus, held refreshes and bounded recovery. Keep it only if cadence or completion margin improves without artifacts.

Accept improvements by displayed-picture cadence and low-tail frame margin, with no gameplay-speed change, added missing tiles, command-table overflow or memory overrun. These source experiments do not yet justify a 60 fps claim.
