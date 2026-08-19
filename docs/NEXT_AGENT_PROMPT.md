# Next agent prompt: wire collision, or decode the state-dispatch mechanism

`table_set` provenance is RESOLVED (2026-08-19) — read
`docs/AGENT_HANDOFF.md` "table_set source rule: RESOLVED via live
instruction trace" completely before doing anything else. Do not re-open
that question or re-attempt correlation; the answer came from a live
instruction trace, not correlation, and correlation could not have found
it (the value is a literal immediate constant, not a data-dependent
field read). See the handoff's "Re-verified and completed this session"
note: all three families' store instructions are now backed by surviving
instruction logs in the checkout, the stride-1 corpus decoder
(`tools/decode_avsp_table_set.py`) is the reproducible zero-mismatch
check, and the full-attribution hit counts are transcribed (their raw log
is not retained).

## Mandatory startup and repository safety

Read in order before changing anything: the `port-cps2-to-sega-saturn`
skill (`SKILL.md`, `references/workflow.md`), `AGENTS.md`, `CLAUDE.md`,
`docs/GOAL.md`, `docs/AGENT_HANDOFF.md` completely (newest sections first
supersede older ones — the table_set source-rule section supersedes
every earlier table_set section), `docs/PARITY_PLAN.md`, `docs/TEST_PLAN.md`,
`docs/HARDWARE_TEST.md`, then this file again.

Record the live state (`git status --short --branch`, `git log --oneline
-10`, `git rev-parse HEAD`, `git branch --show-current`); trust the
commands, not this file, for HEAD. Check for stray `mame.exe` processes
(`tasklist //FI "IMAGENAME eq mame.exe"` — `ps -W`'s process name column
omits the `.exe` suffix in this shell, so a `grep mame.exe` check is
silently vacuous) and stop any before starting new work.

Rules (binding, unchanged): stay on `codex/avp-master-plan`; never
`git add .`/`-A`/`clean`/broad stash/reset/destructive checkout — stage
explicit paths only; never commit ROMs, raw captures, MAME logs,
emulator states, generated copyrighted assets, or disc images; preserve
every untracked `tools/diag_*`/`tools/mame_trace_*.lua` one-off.

## Project status to preserve

- Native SH-2 port at functional parity, not a CPS2 emulator. Capability
  Gate 1 remains `0/7`; the full-game goal remains `0/9`.
- S1's actor spine and collision predicate (`avsp_collision.c/h`) are
  proven but not yet connected to gameplay.
- Every active street alien in WALK/ATTACK carries independent ROM-driven
  animation state (`1350cf8`, live-validated over MCP). Hit/KO/spawn
  actions, the player, stalkers, and boss paths still use capture-derived
  production data.
- Body E's per-object renderer expands CPS2 objects into 16x16 VDP1 tile
  sprites — a working native diagnostic path, not the final one-command-
  per-object renderer described in `docs/PARITY_PLAN.md`.
- The tile-archive build contract is deterministic: normal builds pass
  `--scope street` explicitly; `--scope round1` correctly refuses before
  writing (612,720 bytes exceeds the 262,144-byte carve).
- The clean normal-release boot passed (`runtime_ready=1`, zero failed
  assets). The Saturn `-EncounterTest` route was not rerun after the
  multi-actor change and remains pending — do not confuse the 12,000-
  frame host soak with that emulator run.
- `sel_hurt`/`sel_attack` (animation record +8/+9) are already readable
  for ROM-driven street aliens. `table_set` provenance is now proven (see
  above) but the state-dispatch INDEX (which of the three routines a
  given actor state selects) is not decoded — that's the "type_promotion"
  UNRESOLVED item in the handoff, real S5-adjacent AI work.

## Two legitimate directions from here — pick one, state which

### Option A: wire collision now

Both fields `avsp_collision_overlap` needs for a ROM-driven street alien
are now provably obtainable:

- `sel_hurt`/`sel_attack`: already read from the live animation record's
  bytes +8/+9 (no new work).
- `table_set`: now known to be one of three fixed constants
  (`data/avsp_table_set_source.json`), written whenever an actor enters
  one of three state classes. For street aliens currently ROM-driven
  (WALK/ATTACK only), the evidence strongly suggests `table_set =
  0x00130AC8` ("normal") is the state they are in — the "normal" writer
  fired 35 times in the corpus window against 1 for "replace" and 2 for
  "type_promotion", i.e. it is the default/common state family. **Before
  hardcoding `0x00130AC8` for the runtime's WALK/ATTACK actors, verify
  this holds during those two SPECIFIC actions** (a targeted watchpoint
  during WALK/ATTACK only, not the whole corpus) — do not assume the
  aggregate corpus dominance transfers cleanly to the specific action
  subset without checking, the same discipline that caught the +0x02
  false lead.
- Then: read the S1-decoded hurt/attack boxes for the live ROM actor,
  call `avsp_collision_overlap`/`avsp_collision_guarded` from
  `capability_model.c`'s hit-resolution path for ROM-driven actors only
  (capture-cel actors keep the existing X-distance/lane approximation
  until they too are ROM-driven), and retire the approximation
  incrementally, actor-class by actor-class.

### Option B: decode the state-dispatch mechanism

Answers "which index selects `normal` vs `replace` vs `type_promotion`,
and what does `type_promotion` actually do" — the UNRESOLVED item in the
handoff. This is AI/state-machine decode work (S5-adjacent), not
table_set provenance; do not conflate the two. Use the same live-trace
method: find the jump-table read that selects among the three routine
addresses (a backward trace from the entry points, or a broader
breakpoint on the state-dispatch loop itself), then decode
`type_promotion`'s ROM table lookup at `0x117FAE` and its `jsr $17020`
callee.

## Verification order (either option)

1. Full `test.ps1` exits 0 (includes the
   `tools/gen_avsp_table_set_source.py` full-attribution falsification,
   the `tools/decode_avsp_table_set.py` stride-1 target-type-12 corpus
   decoder falsification, and the existing
   `tools/analyze_avsp_table_set_writer.py --self-test`).
2. Saturn cross-compile via `build.ps1` exits 0 and rebuilds the ISO, IF
   runtime code changed (Option A). Option B is pure evidence/analysis
   work; no rebuild required unless runtime code changes.
3. For runtime changes: boot the normal release and verify over MCP
   (`runtime_ready=1`, no failed asset, live entry counts / new collision
   behavior as applicable).
4. Stop any MAME process this session started before handoff.

## Prohibited shortcuts (unchanged, restated)

- Do not wire a `table_set` value into runtime code without live-trace
  confirmation for the SPECIFIC action/state it will be used under (see
  Option A's caveat above).
- Do not treat "perfectly correlated in this corpus" (any correlation
  result) as provenance — only a live instruction trace proves a source.
- Do not describe the per-tile Body E renderer as the final one-command-
  per-object implementation.
- Do not claim the `-EncounterTest` soak ran without actually running it.

## Checkpoint and handoff requirements

Commit at every green checkpoint with explicit paths. Update
`docs/AGENT_HANDOFF.md` newest-first, correcting superseded claims in
place rather than layering contradictions. Keep this file pointing at
the next unexecuted body.
