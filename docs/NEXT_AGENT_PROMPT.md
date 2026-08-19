# Qwen next-turn prompt: finish `table_set` provenance from the retained writer trace

Work in `C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest`, an independent
private Git repository nested in an unrelated workspace. Stay on
`codex/avp-master-plan`; do not switch, merge, rebase, cherry-pick, add a remote,
or touch the separate Marvel worktree.

## Read and verify before acting

Read these completely, in order:

1. `C:\Users\lambd\.codex\skills\port-cps2-to-sega-saturn\SKILL.md`
2. That skill's `references/workflow.md`
3. `AGENTS.md`
4. `CLAUDE.md` only as a cross-harness pointer; `AGENTS.md` remains canonical
5. `docs/GOAL.md`
6. `docs/AGENT_HANDOFF.md` completely, newest sections first when reconciling
   corrections
7. `docs/PARITY_PLAN.md`, especially terminology, S1-S6, static translation,
   and the collision sections
8. `docs/TEST_PLAN.md` and `docs/HARDWARE_TEST.md`
9. This file again

Then run, from this repository:

```powershell
git status --short --branch
git log --oneline -12
git rev-parse HEAD
git branch --show-current
Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match 'mame|yaba|mednafen|retroarch'
} | Select-Object ProcessId,Name,CommandLine
```

The evidence/instrument baseline is `b8bcf48`; this prompt is in its docs-only
successor, whose exact self-referential hash must be read with
`git rev-parse HEAD`. Preserve every untracked diagnostic. Never use
`git add .`, `git add -A`, `git clean`, a broad stash, reset, or destructive
checkout. Stage explicit files only. Never commit ROMs, raw captures, MAME
logs, emulator states, generated copyrighted assets, disc images, or the raw
trace sidecar.

## Project status you must preserve

- The target is a native SH-2 port at functional parity, not a CPS2 emulator.
- Capability Gate 1 remains `0/7`; full-game completion remains `0/9`.
- S1's actor spine and collision predicate are already proven.
- The ROM animation interpreter and enemy object-emission families are already
  decoded and host-tested. Do not re-derive them.
- Every active street alien in WALK/ATTACK now has independent ROM-driven
  animation state. Hit/KO/spawn actions, the player, Stalkers and some boss
  paths still fall back to capture-derived production data.
- The visible Body E path currently expands decoded CPS2 objects into 16x16
  VDP1 tile sprites. It is a working native diagnostic path, not yet the final
  one-command-per-CPS2-object renderer.
- The deterministic tile-archive build contract is green. Normal builds
  explicitly request `--scope street`; `--scope round1` correctly fails before
  writing because 612,720 bytes exceeds the current 262,144-byte carve.
- The clean normal release boot passed. The Saturn `-EncounterTest` route was
  not rerun after the multi-actor change and remains pending; do not confuse
  the 12,000-frame host soak with that emulator run.

## The correction already landed; do not undo it

Commit `b8bcf48` repaired `tools/gen_avsp_table_set_evidence.py`:

- stride 1 over every captured frame;
- inactive-to-active and type-change generation segmentation;
- all candidate bytes retained;
- a perturbation negative control;
- honest correlation wording.

`data/avsp_table_set_evidence.json` schema 2 records 33 target-type-12
generations, each holding one `table_set` for its observed lifetime. Three
informative candidate bytes remain perfectly correlated in this corpus:
`+0x0E`, `+0x5E`, and `+0x64`. Fourteen other perfect candidates, including
`+0x02`, are marked vacuous because their mappings survive the negative
control. None of these correlations may enter runtime code. Only the game's
writer/source path may determine provenance.

## Retained writer-trace inputs: do not rerun first

The headless stock-MAME run completed all 6,260 Lua frames and exited normally.
No MAME process was running when this prompt was written. These are raw/private
diagnostic inputs; preserve but do not commit them:

| File | Bytes | SHA-256 |
|---|---:|---|
| `error.log` | 66,310 | `c1c34eb427a1130a5121982af2000059d1240edcff1b0ae18620f37da0d85c08` |
| `tools_tsw_frames.tsv` | 66,434 | `f5ac294c4854809b2f145735a3cf0c187a3e438352b9cd183a887a410050604e` |
| `tools/mame_trace_table_set_writer.lua` | 4,963 | `a34a5a9edd1164e7ab7e2c418f86d5445a34b338d70a842065eb00ad86a83127` |

The Lua file is an untracked one-off probe and the two outputs are raw evidence.
The run recorded:

- 3,810 `AVP_TSW_FRAME` markers;
- 14 `AVP_TSW_STATE` lines;
- 58 `AVP_TSW_CAND` lines;
- 14 `AVP_TSW_TSET` lines.

The 4-byte watchpoint emits **two lines per logical 32-bit store**. Pair
consecutive same-frame/same-PC/same-register-context lines and reconstruct the
big-endian pointer. There are seven logical `table_set` stores:

- four nonzero stores of `0x00130AC8`, writer report PC `0x060578`;
- two zeroing stores, writer report PC `0x0172BA`;
- one nonzero store of `0x0013E97A`, writer report PC `0x049604`.

Do not treat raw `wpdata` as a complete byte/long without accounting for bus
lane and mem-mask behavior. One candidate line is printed as `data=600`, which
is itself a warning that the byte watchpoint's display is lane-positioned. Use
memory readback or the traced instruction/source operand to establish values.

## Sole objective for this turn

Determine where the game gets actor `table_set` (`actor +0x50`) during spawn
initialization and reproduce that source for all three observed type-12
families (`0x00130AC8`, `0x0013E97A`, `0x0012CE5C`) without using correlation.
Produce a deterministic tracked analyzer/report and a precise continuation.
Do **not** wire collision into Saturn gameplay in this turn.

## Required work, in order

### 1. Parse the retained run deterministically

Create a reusable tracked analyzer, preferably
`tools/analyze_avsp_table_set_writer.py`, that:

1. Validates the three retained input hashes before analysis, with optional
   explicit path/hash overrides if needed for regeneration.
2. Scans `error.log` in order and counts `AVP_TSW_FRAME` markers.
3. Uses `tools_tsw_frames.tsv` to map cumulative bank-write marker counts to
   Lua/source frames. State the exact mapping rule and handle the initial
   nonzero marker count explicitly.
4. Parses state, candidate, and table-set events.
5. Pairs the split table-set lines only when frame, PC, registers, actor slot,
   and event adjacency agree; rejects an orphan or ambiguous half instead of
   guessing.
6. Emits logical stores with frame, reported PC, reconstructed pointer,
   registers, source-address candidates and surrounding candidate writes.
7. Separates nonzero initialization from the `0x0172BA` zero/teardown path.
8. Includes negative parser fixtures: orphan half, mismatched PC/context, and
   lane-positioned byte data must be rejected or explicitly unresolved.

Write a tracked coordinate/control-flow-only report such as
`data/avsp_table_set_writer.json`. It may contain ROM addresses, PCs, register
values, counts, mappings and hashes, but no ROM bytes or raw log excerpts.

### 2. Establish the exact store instructions from the live/decrypted path

Watchpoint PCs can be skewed +2/+4. Do not name the instruction from the
reported PC alone, and do not trust the flat opcode dump at code addresses.

Using stock MAME 0.289 and a bounded Lua-driven trace:

1. Trace a small window around the normal initializer near `0x060578`.
2. Trace a small window around the replacement initializer near `0x049604`.
3. Capture enough preceding instructions to identify the register or memory
   operand that supplies the long written to `actor +0x50`.
4. Record the exact source address calculation, not merely the final register
   value.
5. Capture the nearby candidate writes so their relationship is explicit:
   - normal path: `+0x64` near `0x06056A`, `table_set` near `0x060578`, then
     `+0x57`/`+0x45`/`+0x0E`/`+0x5E` near
     `0x06059E/0x0605B2/0x0605CC/0x0605DC`;
   - replacement path: `+0x64` near `0x0495F6`, `table_set` near `0x049604`,
     then `+0x57`/`+0x5E`/`+0x0E` near
     `0x049620/0x049626/0x049636`; `+0x45` was observed separately at
     `0x04BDAA`.
6. Label the `0x0172BA` writer as teardown only after the instruction trace
   confirms the clear/copy behavior.

Use the existing headless Lua breakpoint/trace-toggle patterns. A custom MAME
build is not authorized or necessary. If a second run is needed, write to new
output filenames so the retained first run remains unchanged.

### 3. Cover the third type-12 family

The slot-43 street run covered `0x00130AC8` and `0x0013E97A`, not
`0x0012CE5C`. After understanding the first two writers:

1. Use `data/avsp_table_set_evidence.json` to select a route and physical slot
   whose generation holds `0x0012CE5C`—the Stalker action route contains such
   generations.
2. Replay that route's exact input/state schedule; do not mix frame numbers or
   schedules from `enemy_actions`.
3. Trace the nonzero `table_set` initialization and its source operand.
4. Determine whether all three values come from one descriptor/table shape,
   parallel type-specific initializers, or distinct structures.

### 4. Decode and falsify the source rule

Promote a source rule only when the live traces prove it. Then:

1. Implement the smallest decoder needed to reproduce the three pointers from
   the proven spawn/template inputs.
2. Run it over every stride-one target-type generation in the repaired corpus.
3. Require zero unexplained mismatches.
4. Add a negative control that perturbs the proven selector/source and fails.
5. If the rule does not generalize, keep the result `UNRESOLVED`, name the exact
   missing path, and do not create a majority/default mapping.

### 5. Correct project documentation

Update the newest sections of `docs/AGENT_HANDOFF.md` with:

- exact HEAD and dirty files;
- input/output hashes;
- writer PCs versus confirmed store instruction PCs;
- source operand/table and all three covered pointer values;
- analyzer population, exclusions, mismatch count and negative control;
- exact MAME commands and output locations;
- whether any MAME process remains;
- ordered next work.

Update this file so it points to the next unexecuted body. Correct stale text
you encounter rather than adding another contradictory layer. In particular,
do not say only one street alien is ROM-driven, and do not describe the current
per-16x16-tile renderer as the final one-command-per-object implementation.

## Acceptance checks for this turn

All of these are required before claiming provenance is resolved:

- retained trace parser passes its positive and negative fixtures;
- all split long writes are paired unambiguously;
- MAME's live/decrypted trace identifies the actual store and source read for
  both already captured nonzero paths;
- the `0x0012CE5C` route is captured and decoded;
- one source rule reproduces all declared stride-one target generations with
  zero unexplained mismatches;
- a perturbed-source negative control fails;
- `test.ps1` exits 0 after tracked analyzer/report changes;
- no runtime collision code, `CapActor.variant` mapping, inferred default, or
  majority mapping was introduced;
- all emulator processes owned by this checkout are stopped before handoff.

This is evidence/analyzer work, so a Saturn rebuild is not required unless you
change SH-2/runtime/build inputs. The previously skipped `-EncounterTest`
remains pending and must stay named; do not claim it as run.

## Commit discipline

Commit coherent green checkpoints with explicit paths only. A suitable split
is:

1. retained-trace analyzer, tests and coordinate-only report;
2. live-proven source decoder/falsification plus handoff/prompt updates.

Do not commit `error.log`, `tools_tsw_frames.tsv`, raw trace files, ROMs,
captures, disc images, emulator state, or unrelated diagnostics. Capability
Gate 1 remains `0/7` regardless of a successful provenance check.
