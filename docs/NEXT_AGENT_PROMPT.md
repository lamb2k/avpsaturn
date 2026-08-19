# Next agent prompt: unblock the Round 1 route (BOSSCLR.PCM phase-load), then decode the state dispatch

## Where the project is

The "connect decoded collision to gameplay (defender side first)" body is
complete AND confirmed live. Its review turn corrected two defects and ran
both verifications that had been carried as pending. Read the handoff's newest
section, "Review of the collision body: two defects corrected (2026-08-19)",
before anything else.

What is now MEASURED, not inferred:

- `runtime_ready = 1` read literally over the Yaba Sanshiro MCP debug server.
- ROM street aliens carry REAL decoded hurt boxes in WAVE_ONE (58 px wide,
  facing-mirrored, tracking model x).
- Player hits resolve through those boxes: the `-EncounterTest` route cleared
  both street waves with `HITS rom=8 approx=0` — 8 kills, every one decided by
  the measured hurt box, none by the ADAPTED point approximation.
- Frames with no ROM measurement (a pose outside the walk/attack loops) keep
  the ADAPTED approximation and are counted in `GAP`. They are NOT treated as
  invulnerable; that earlier behaviour was an invented rule and is gone.
- `NH` (the game's own zero-`sel_hurt` cannot-be-hit rule) is wired but stayed
  0 all session — UNEXERCISED live. Do not claim it works.

**The rig is available on this host.** The MCP debug server answers at
`http://127.0.0.1:9640/mcp`. Re-derive symbol addresses EVERY build with
`.deps/joengine/Compiler/WINDOWS/sh-elf/bin/nm.exe --target=coff-sh game.elf`
(coff-sh symbols carry a leading underscore), and get struct offsets from a
host `offsetof` program rather than reusing absolute addresses from an older
build. A previous turn recorded this readback as impossible; it is not.

## The body of work, part 1: the route blocker (do this first)

**Measured symptom.** The `-EncounterTest` ISO auto-drives MAIN_MENU →
WAVE_ONE → WAVE_TWO → CLEAR, then HALTS at `INTERIOR_TRANSITION` with
`world.frame` frozen (the emulator keeps running; only the model stops).
Cause, read from the runtime's own diagnostics: `avsp_fs_last_error` =
`FS ALLOC`, `boss_clear_sound.data` = 0. The phase-load in `main.c` calls
`jo_malloc_with_behaviour(637084, JO_MALLOC_TRY_REUSE_BLOCK)` for
`/AUDIO/BOSSCLR.PCM`, gets null, sets `runtime_ready = 0`, and returns early
from that function on every subsequent frame.

**Why it outranks the dispatch decode:** the phase-load site is common code,
not gated by the test profile, so the NORMAL RELEASE hits the same wall. Round
1 cannot currently reach BOSS. No amount of further ROM decoding matters while
the route cannot finish.

Ordered:

1. **Measure the real allocation state at the failure point** before changing
   any budget. At `INTERIOR_TRANSITION`, report what is actually free and in
   how many blocks (cartridge bank 0, bank 1, and work RAM separately), and
   what holds the space — the `AVSP_TILE_REGION_BYTES` carve (0x40000 at the
   head of cart bank 1), the earlier PCM loads, the RLE archives. Declare the
   numbers before proposing a fix. The skill's rule applies: treat the reuse
   allocator as a WHOLE-BLOCK allocator until proven otherwise — a small
   earlier load can consume the only block large enough for this one.
2. **Choose the fix from those numbers, not from a guess.** Candidates, in
   rough order of how little they invent: pack the phase assets into one
   aligned allocation so the 637 KB request is not competing for a fragmented
   remainder; retire an allocation that is provably dead by the interior
   transition (the street tile archive is a candidate ONLY if nothing still
   renders from it — prove it, do not assume); move the load to a boundary
   where a large block demonstrably exists. Whichever is chosen, the
   allocation must be proven to fit in the FULL route, not in a focused
   diagnostic.
3. **Verify by running the route to completion**, not by reasoning: the
   `-EncounterTest` ISO must reach BOSS, BOSS_DEFEAT, and the end of the
   route with `runtime_ready` staying 1 and `avsp_fs_last_error` unset. Report
   the states it passed through and the frame at each.

## The body of work, part 2: the state-dispatch index (type_promotion)

Only after the route runs end to end. `table_set` provenance is RESOLVED for
three families as literal immediates in three per-state initializer routines,
reached by an INDEXED JUMP (not `bsr`/`jsr`):

```text
0x060570:   move.l #$130ac8,($50,A6)  ; "normal"
0x0495FC:   move.l #$13e97a,($50,A6)  ; "replace"
0x0003F0F0: move.l #$12ce5c,($50,A6)  ; "type_promotion"
```

The UNRESOLVED item is the dispatch itself: what index selects which
initializer runs, and how it is computed. It is the prerequisite for
hit/KO/spawn actions joining the ROM path with correct per-state `table_set`
— today the runtime holds the WALK/ATTACK-gated constant `0x00130AC8` and
frames outside those loops fall back to the ADAPTED approximation.

1. **Locate the indexed jump** from a live WALK/ATTACK frame; capture, per
   state, the exact source of the index (register, memory field, or constant)
   and the jump targets. Confirm each target reaches one of the three store
   PCs above.
2. **Falsify the index→family map offline** across the stride-1 type-12
   corpus (`data/avsp_table_set_evidence.json`) with zero unexplained
   mismatches plus a perturbation control that must break.
3. **Reconcile hit/KO/spawn.** Determine which initializer those states run.
   If their store is a different immediate, that is the per-state value the
   runtime must adopt when they join. Do not assume `0x00130AC8`.
4. **Wiring is a SEPARATE, gated turn** — keep provenance and wiring apart,
   as the `table_set` and collision bodies did.

Provenance rule (binding): only a live, decrypted 68000 instruction trace is
trusted provenance. Correlation is never provenance. `spawn_type()` in
`tools/decode_avsp_table_set.py` is a hand-authored capture-context
classifier, NOT the game's dispatch, and must never appear in runtime code.

Headless MAME tracing needs `-debug` plus the script's
`debugger.execution_state = "run"`; `-debugger windows` is optional and
harmless as two tokens. Cold-boot replay is reliable; `machine:load()` is not,
in this environment.

## Explicitly deferred (do not start here)

- Widening ROM action coverage to hit/KO/spawn (needs part 2, step 3 first).
- Player ROM animation (blocks full two-sided ROM collision and the
  attack-box side of the predicate).
- Stage collision beyond room/lane clamps; actor separation; projectile path.
- The `round1` tile archive (its budget question is downstream of part 1's
  allocation measurements).

## Prohibited shortcuts

- No `table_set` constant in runtime code without its offline gate passing
  first, in the same turn.
- Do not treat correlation output as provenance, ever.
- Do not turn a missing measurement into a gameplay rule. A pose the ROM path
  does not cover keeps the ADAPTED approximation and is COUNTED; it never
  becomes silent invulnerability. (This is exactly the defect the review turn
  removed.)
- Do not claim a verification that was not run. If the emulator readback or
  the route is not executed, say so plainly — but note that this host CAN run
  both, so "impossible here" is not an available excuse.
- Do not describe the per-tile renderer as final, or the build as a faithful
  playable level (see the handoff's gap table).

## Mandatory startup and repository safety

Read in order before changing anything: the `port-cps2-to-sega-saturn` skill
(`SKILL.md`, `references/workflow.md`), `AGENTS.md`, `CLAUDE.md`,
`docs/GOAL.md`, `docs/AGENT_HANDOFF.md` completely (newest sections supersede
older), `docs/PARITY_PLAN.md`, `docs/TEST_PLAN.md`, `docs/HARDWARE_TEST.md`,
then this file again.

Record the live state (`git status --short --branch`, `git log --oneline -10`,
`git rev-parse HEAD`, `git branch --show-current`); trust the commands for
HEAD. Check `tasklist //FI "IMAGENAME eq mame.exe"` (not a `ps -W | grep
mame.exe` loop — that grep is silently vacuous here) and stop any stray
emulator before starting. An emulator holding `game.iso` open can break a
build's ISO step; stop it before rebuilding.

Rules (binding, unchanged): stay on `codex/avp-master-plan`; never `git add
.`/`-A`/`clean`/broad stash/reset/destructive checkout — stage explicit paths
only; never commit ROMs, raw captures, MAME logs, emulator states, generated
copyrighted assets, or disc images; preserve every untracked
`tools/diag_*`/`tools/mame_trace_*.lua`/instruction-log one-off.

## Checkpoint and handoff requirements

Commit at every green checkpoint with explicit paths. Keep
`docs/AGENT_HANDOFF.md` newest-first with: HEAD, dirty files, the exact code
or trace paths changed, live readbacks with the values actually read, which
verifications ran, and ordered next work. Keep this file pointing at the next
unexecuted body. Capability Gate 1 stays `0/7` regardless of outcome.
