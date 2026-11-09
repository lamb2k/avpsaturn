# AvP frame timing and Wolverine: source correction handover

Date: 2026-11-08, America/New_York. **Candidate source, HOST verified.**
Target link, private asset fit, MAME differential, emulator playback and physical
Saturn qualification are **UNRUN** for this candidate. There is no new measured
fps result and no claim that 60 fps has been achieved.

## Branches and integration

| Candidate | Starting point | Purpose |
| --- | --- | --- |
| `codex/avp-wolverine-frame-fixes-20261108` | `feat/wolverine` at `79c958023082574ba2b844a3de24c118d8ac9773` | Combined Wolverine, presentation and pack/build corrections |
| `codex/avp-vdp1-frame-fixes-20261108` | `fix/vdp1-race` at `3b2810990a9ffd09a7cbea701f5d4c2415c82c95` | VDP1-only correction and profiling lane for a nonguest build |

Both starting tips were rechecked before publication. The common ancestor is
`138bdf1b684347e74f50bcb18b3cf9e2fb43fe46`; `int/play-latest` was
`ce000d81528b30070d155981176a53993e88091a` (the additional commit is backlog-only).
The repository default branch is an older campaign; it is not this baseline.

The combined candidate imports the existing race branch's **runtime graphics,
header and kernel** changes by a clean three-way merge, then adds the reviewed
corrections below. This folds the double command tables, prior-texture protection,
earlier sprite submission and CEF-clear latch into Wolverine. It does not import
that branch's additional pose-census pack policy: extra arcade pose keys require
a fresh guest remap and memory fit. The VDP1-only branch retains its own original
pack policy. The two candidates already share the runtime fixes; select the
appropriate candidate for a trial rather than merging the whole branches twice.

All source is in the private repository. No ROM, extracted graphics, ISO,
capture, savestate or raw trace is included. The source-function census and
behaviour-matched function ledger are unchanged by this adapter work.

## What changed

### Wolverine clock and publication

The existing 15-update/51-tick hold schedule finished on tick 49. It now runs its
first and last native updates on ticks 1 and 51. A post-update hook observes entry
and completion immediately and retains the original player pointer even when
the native routine changes `a6`.

An early native return to idle/walk retains the guest's remaining presentation
and recovery. It leaves the native state completed, with no rollback of game
RAM or repeated damage calls. Hitstun, grab, death and entry changes interrupt
the hold; naturally longer native states remain longer. This establishes the
presentation-duration contract, not exact MSHvSF startup, hitstop or damage.

Opening poses lasting one tick are no longer skipped. Rendering never advances
the clock. A vblank snapshot reads one aligned volatile 16-bit published step,
with bounds checks, instead of combining a newly written move with an old step.
Inactive or deselected players reset their guest clock, attack cache and command
history. `WV_MEASURE` still runs without the duration holds.

`SAT_WOLVERINE_DEBUG` now gates 152 bytes of existing probe arrays. Two bytes of
recovery state are added: **150 bytes less declared fixed state**, before linker
padding. The SH-2 link remains the authority for real free RAM and code size.

### Pose residency and build correctness

The selector budgets every emitted first pose, including poses shared between
moves. Stage keys are derived from the final emitted sequences. Unused
portrait-only tiles are omitted from gameplay residency; portrait data remains
in the private source assets for future HUD/select work. Exact savings require
the private remap. Full `walk` selection retains every captured walk pose and
duration, and a supplied budget cannot be silently exceeded.

Reselection refreshes graphics and marks box data stale. `boxes.py` clears the
marker after regeneration; the generator rejects stale/mismatched boxes,
missing required moves, invalid stance/palette/tile fields, missing resident
pose keys and values that overflow the runtime's 8/16-bit fields.

The stage builder now checks:

- Every mandatory guest key survives packing, before any round file is written.
- Guest remap keys do not overlap current arcade/screen keys.
- A guest row is not configured twice with different asset sources.
- Kept stage files have matching planning/layout, graphics/audio, ranks, screen
  keys, controls and packer-source hashes, plus exact output file hashes.
- Missing receipts, changed assets, corrupt/missing outputs or surplus files
  cause a rebuild. Surplus generated files are parked under the private work
  directory's `stale_rounds`, outside the new disc store.
- The loader directory is one sector for 1..255 round files, two for 256..511;
  the actual file count determines `STORE_HEAD2`, not a guest environment flag.

The first build after adopting the receipt format intentionally rebuilds packs,
even with `KEEP_ROUND_FILES=1`. Later accepted reuse refreshes ROM restore bytes
and records new output hashes. This closes a path where new pose tables could
be shipped with old sprite packs.

The standalone fit command now requires every selected stage and Schaefer
variant, mirrors the production packing controls, and exits 0 only for a real
pass, 1 for fit failure and 2 for missing/invalid input or scope. It checks that
guest additions do not increase the baseline arcade tile loss. Its recorded
layout is from the last completed build; the production post-link gate remains
authoritative after code/table sizes change.

### VDP1 presentation and profiling

Late drawing no longer forces an unconfirmed framebuffer change. Bounded waits
skip that presentation and retry on the next handoff when completion, change
acknowledgement or CEF-clear confirmation is missing. The game continues. An
emulator permanently missing CEF will keep the last picture; this deliberate
correctness tradeoff needs the local emulator check.

The completion wait precedes palette/cache/table writes. Only successful
submission flips command-table ownership. On an abandoned build, a failure-only
stamp scan retains the last submitted plot's texture protection, including
shared cache hits. The first plot bypasses a nonexistent prior-frame latch.

`SAT_VLOG` now reserves its sixteen marker commands inside each 32 KB table:
1,000 sprite commands with that flag, 1,016 otherwise. Both limits include the
existing readout-bar reserve.

`SAT_VDP1_PROFILE` is off by default. Its rings record command construction,
upload work, completion/change/latch waits, submission, layer work, stage and
arcade slots, pixel-area proxies, colour mode and half-transparency. The decoder
keeps master/slave clocks separate and labels raster observations as upper
bounds. See [VDP1_PROFILE.md](VDP1_PROFILE.md) for exact flags, dump sizes and
interpretation. The enabled profile uses 2,116 bytes at depth 16 or 380 bytes at
depth 2, before padding; neither is proven to fit the Wolverine image. Start
with the nonguest diagnostic lane and respect the existing memory limits.

## Verification on the combined source

| Check | Result |
| --- | --- |
| Python regression suite, including actual runtime C compilation | HOST PASS, 37 tests |
| Wolverine clock/adapter | Strict C90 PASS: release, debug, measurement, debug+measurement |
| Actual VDP1 driver fixture | Strict C90 PASS: seven flag combinations |
| Existing graphics fixture | Strict C90 PASS |
| Combined guest/profile/VLOG graphics syntax | HOST PASS |
| Independent review of clock, IRQ publication, pack gate and VDP1 ownership | No remaining blocking finding |
| Deliberate clock and VDP1 behavioural mutations | Rejected by running assertions |
| Real private stage 06/1c/1e fit | UNRUN |
| SH-2 link, disc build, MAME, emulator, Saturn | UNRUN |

Clock fixtures include HP 15 native calls -> 51 guest ticks, an early HP return
at 10 calls -> 51 ticks, early HK at 6 calls -> 28 ticks, and a naturally longer
HK -> 32 ticks. They also cover interruptions, sequential moves, reselect,
unchanged time across repeated snapshots, and an interrupted move/step update.
These are synthetic logical ticks, not measured displayed arcade frames.

Run the new Python checks individually in a full checkout, avoiding unrelated
historic tests that require private data:

```sh
python -m unittest discover -s tests -p test_round_cache.py
python -m unittest discover -s tests -p 'test_wolverine_*.py'
python -m unittest discover -s tests -p test_vdp1_profile.py
```

The VDP1 document contains the two standalone C fixture commands.

## Exact next local assignment

1. Fetch the combined candidate into an isolated worktree using the configured
   private remote. Preserve the existing disc and capture its exact source SHA,
   build flags, asset identities and image hash as the comparison baseline.
2. Re-select from the retained private capture into a new asset directory. Keep
   the established full-move list and replace `walk/2` with `walk`, at the same
   tile budget. If the required set exceeds the budget, retain the safe smaller
   set and report the measured deficit; do not force a larger arena.
3. Regenerate boxes from the matching retained capture, then run the explicit
   stage subset and the complete fit. Placeholder paths below denote existing
   private inputs, not files supplied by this change:

```sh
python tools/wolverine/reselect.py OLD_ASSETS NEW_ASSETS FULL_MOVES TILE_BUDGET
python tools/wolverine/boxes.py CAPTURE_BOXES.txt NEW_ASSETS
python tools/wolverine/fit.py WORK NEW_ASSETS 06,1c,1e
python tools/wolverine/fit.py WORK NEW_ASSETS
```

4. Build with the usual `SAT_HOME`/`SAT_GUESTS` flags and `GUEST_ASSETS` pointing
   to `NEW_ASSETS`. Use `SAT_GUEST_DATA` only for other guests. Let the new receipt
   force the initial full pack rebuild. Record actual high/low RAM, cart and ROM
   stretch headroom. A failed gate is a failed candidate, not a qualified disc.
5. On the exact resulting disc, count guest ticks and visible pose serials for
   heavy slash/kick, walk, hit/grab/death, respawn/reselect and guest OFF. Play
   stages 06, 1c and 1e; check zero required guest-tile loss and no new refusal.
   Retain standard-stage and option-OFF regressions. Exact collision/attack
   timing still needs comparison to the retained source evidence.
6. Profile an identical stage-2 fight route on baseline and candidate, initially
   nonguest. Decode paused ring dumps with `tools/vdp1_profile.py`; use VLOG
   picture serials for displayed cadence. Separate late start/upload/wait causes
   from genuine completed-raster cost. Preserve emulator/version/core settings.
7. Qualify the final image on Saturn. Only that run can support a hardware 60 fps
   or fill-rate conclusion.

Remaining feature work: the actual full-walk fit and disc rebuild above, real
invisible-Wolverine reproduction/closure, and the HUD portrait. The build and
publication fixes close specific missing-pose paths; they do not establish that
every cause of invisibility has been eliminated. Combined-guest residency and
mid-stage guest joins also retain the original runtime limitations.
