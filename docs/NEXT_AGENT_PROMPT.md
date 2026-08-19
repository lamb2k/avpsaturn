# Next agent prompt: connect decoded collision to gameplay (defender side first)

`table_set` provenance is RESOLVED and decoded (2026-08-19, commits
`720e2a5` + `dc91061`): a literal immediate constant in one of three
per-state initializer routines, proven by live instruction trace, with a
stride-1 corpus decoder (`tools/decode_avsp_table_set.py`) falsifying the
constants map at zero unexplained mismatches. Read the handoff's
"table_set source rule: RESOLVED" section (and its "Re-verified and
completed" follow-up) before anything else; do not re-open provenance.

Two review caveats from the checkpoint-2 audit, binding on this turn:

1. `spawn_type(route, slot, first_frame)` in the stride-1 decoder is a
   hand-authored CAPTURE-CONTEXT classifier, adequate for falsifying the
   constants map offline. It is NOT the game's own spawn/state dispatch
   logic and must NEVER be wired into runtime code as if it were. The
   real dispatch index is the still-UNRESOLVED type_promotion item
   (S5-adjacent).
2. Headless MAME tracing needs `-debug` plus the script's
   `debugger.execution_state = "run"`; `-debugger windows` is optional
   and harmless as two tokens (an earlier exit-6 claim was a quoting
   artifact — see the corrected handoff note). Cold-boot replay is
   reliable; `machine:load()` is not, in this environment.

## Mandatory startup and repository safety

Read in order before changing anything: the `port-cps2-to-sega-saturn`
skill (`SKILL.md`, `references/workflow.md`), `AGENTS.md`, `CLAUDE.md`,
`docs/GOAL.md`, `docs/AGENT_HANDOFF.md` completely (newest sections
supersede older), `docs/PARITY_PLAN.md`, `docs/TEST_PLAN.md`,
`docs/HARDWARE_TEST.md`, then this file again.

Record the live state (`git status --short --branch`, `git log --oneline
-10`, `git rev-parse HEAD`, `git branch --show-current`); trust the
commands for HEAD. Check `tasklist //FI "IMAGENAME eq mame.exe"` (not a
`ps -W | grep mame.exe` loop — that grep is silently vacuous here) and
stop any stray emulator before starting.

Rules (binding, unchanged): stay on `codex/avp-master-plan`; never
`git add .`/`-A`/`clean`/broad stash/reset/destructive checkout — stage
explicit paths only; never commit ROMs, raw captures, MAME logs, emulator
states, generated copyrighted assets, or disc images; preserve every
untracked `tools/diag_*`/`tools/mame_trace_*.lua`/instruction-log one-off.

## Project status to preserve

- Native SH-2 port at functional parity, not a CPS2 emulator. Capability
  Gate 1 remains `0/7`; the full-game goal remains `0/9`.
- S1's actor spine and collision predicate (`avsp_collision.c/h`,
  `avsp_actor.c/h`) are proven on the host; nothing calls them from
  gameplay.
- Every active street alien in WALK/ATTACK carries independent ROM-driven
  animation state (`1350cf8`, live-validated). Hit/KO/spawn actions, the
  player, stalkers, and boss paths still use capture-derived production
  data.
- Body E renders ROM-driven actors as per-16x16-tile VDP1 sprites — a
  working native diagnostic path, NOT the final one-command-per-object
  renderer of `docs/PARITY_PLAN.md`.
- Tile-archive builds are deterministic (`--scope street` explicit;
  `round1` refuses over-budget before writing).
- The clean normal-release boot passed (`runtime_ready=1`, zero failed
  assets). The Saturn `-EncounterTest` route remains PENDING since the
  multi-actor change; the 12,000-frame host soak is not a substitute.

## The body of work: ROM hurt-boxes live in gameplay

Ordered. Each step gates the next; stop and record honestly if a gate
fails.

### Step 1 — offline gate: WALK/ATTACK actors always carry 0x00130AC8

Before any runtime constant is wired, prove the specific claim the
runtime needs, not the corpus aggregate: for every stride-1 street-route
frame in which a type-12 actor's live animation-record pointer (`+0x1C`)
lies inside the walk loop (seed `0x12EB4C`) or attack loop (seed
`0x12D8A0`) record spans, that actor's `+0x50` must equal `0x00130AC8` —
zero exceptions, population declared before counting, every exclusion
named. This is cheap (existing captures, no emulator) and is the same
discipline that caught the `+0x02` false lead. Write it as a small
tracked checker wired into `test.ps1`; a tracked manifest records the
population and result. If ANY exception appears, stop wiring and record
the finding instead.

### Step 2 — runtime plumbing: give ROM-driven actors their AvspActor view

For each ROM-driven street alien slot (the `rom_actor_*` arrays in
`main.c`):

- `table_set` = `0x00130AC8` under Step 1's gate, with a comment naming
  the gate artifact and the live-trace provenance
  (`data/avsp_table_set_source.json`). MEASURED constant, not ADAPTED —
  but ONLY while the ROM path is WALK/ATTACK-gated; the comment must say
  the constant must be revisited when hit/KO/spawn actions join the ROM
  path (their state-entry may run a different initializer).
- `sel_hurt`/`sel_attack` read from the live record's bytes +8/+9 via the
  existing anim-script span view each frame (the record pointer is
  already in `rom_actor_frames[slot]`).
- `facing`, `world_x/y/z` from the same ADAPTED model-space bridge the
  emitter already uses (label consistently).

### Step 3 — defender-side wiring, honestly scoped

Full `avsp_collision_overlap` needs BOTH parties' selectors. The player
has no ROM animation record yet, so player-attack-vs-alien contact cannot
run the full ROM predicate this turn. The honest increment:

- Replace the DEFENDER geometry in `cap_resolve_player_hit` for
  ROM-driven aliens only: instead of the X-distance/lane-delta check, test
  the player's existing ADAPTED attack reach against the alien's REAL
  decoded hurt box (via `avsp_collision_hurt_box` with Step 2's
  `table_set` and `sel_hurt`), resolved to world space with the existing
  ADAPTED coordinate bridge. Label the attacker side ADAPTED and the
  defender side MEASURED-geometry in the code comment.
- Capture-cel actors keep the existing approximation untouched.
- A sel_hurt of 0 means "cannot be hit" (the game's own rule) — honor it
  rather than falling back to the approximation for that frame, and count
  occurrences in a debug counter (visible on the debug HUD like the tile
  MISS counters) so silent no-hit windows are observable, not mysterious.

### Step 4 — host falsification against recorded contacts

The `enemy_contact` captures hold the game's own recorded contacts. Add a
host test that replays the S1-proven predicate over those captures using
EXACTLY the runtime's new inputs-path (record-derived selectors +
constant table_set) and requires the known contact set to reproduce —
this is the same check `tests/avsp_actor_test.c` family already performs;
the new assertion is that the RUNTIME's input-assembly path (not just the
library) produces identical results. Zero unexplained mismatches.

### Step 5 — verification order

1. Full `test.ps1` exits 0 (existing checks + Step 1's gate + Step 4's
   test).
2. `build.ps1 -Release -SkipHostTests` green; ISO members verified.
3. Boot the normal release; over MCP verify `runtime_ready=1`, no failed
   asset, and observe hit behavior in WAVE_ONE: ROM-driven aliens take
   hits with plausible reach differences from the cel actors; the
   sel_hurt=0 counter behaves (nonzero only in expected windows).
4. Re-run the Saturn `-EncounterTest` route this turn if time permits —
   it is still pending from the multi-actor change and this turn touches
   combat resolution, which is exactly what it soaks. If not run, keep it
   named as pending; do not claim it.
5. Clean `build.ps1 -Clean -Release -SkipHostTests` last; stop all
   emulators.

## Explicitly deferred (do not start here)

- The state-dispatch index / `type_promotion` decode (S5-adjacent) — the
  UNRESOLVED item in the handoff. Needed before hit/KO/spawn actions can
  join the ROM path with per-state `table_set` correctness.
- Player ROM animation (blocks full two-sided ROM collision and the
  attack-box side of the predicate).
- Stage collision beyond room/lane clamps; actor separation; projectile
  path (S4 items after this body).
- The PCM phase-load refactor that affords the `round1` tile archive.

## Prohibited shortcuts

- No `table_set` constant in runtime code without Step 1's gate passing
  first, in the same turn.
- `spawn_type()` from the stride-1 decoder must not appear in runtime
  code (capture-context classifier, not game logic).
- Do not treat correlation output as provenance, ever.
- Do not widen the ROM action coverage (hit/KO/spawn) in this turn just
  to make collision uniform — that requires the dispatch decode first.
- Do not describe the per-tile renderer as final, or the build as a
  faithful playable level (see the handoff's gap table).

## Checkpoint and handoff requirements

Commit at every green checkpoint with explicit paths. A suitable split:

1. Step 1 gate checker + manifest;
2. runtime plumbing + defender-side wiring + debug counter;
3. host falsification + docs.

Update `docs/AGENT_HANDOFF.md` newest-first with: HEAD, dirty files, the
gate's declared population and result, exact code paths changed, MCP
readbacks, whether `-EncounterTest` ran, and ordered next work. Keep this
file pointing at the next unexecuted body. Capability Gate 1 stays `0/7`
regardless of this body's outcome.
