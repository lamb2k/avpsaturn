# Next agent prompt: decode the state-dispatch index (type_promotion)

## Where the project is

The Round 1 route is UNBLOCKED and runs end to end. Read the handoff's newest
section, "Route blocker fixed: opening audio must top its zone (2026-08-19)",
before anything else. In short, all MEASURED live over the Yaba Sanshiro MCP
rig:

- The `-EncounterTest` route completes: MAIN_MENU → both street waves →
  CLEAR → INTERIOR_TRANSITION (BOSSCLR.PCM loads, `runtime_ready` stays 1) →
  BOSS → BOSS_DEFEAT → RESULTS → COMPLETE.
- Street alien kills resolve through the MEASURED decoded hurt boxes
  (`HITS rom=8 approx=0` across both waves); boss/stalker kills use the
  designed ADAPTED point test (`approx=6`) — capture-cel actors, unchanged.
- The former `FS ALLOC` halt was diagnosed from a full heap dump: Jo's
  allocator never coalesces free neighbours, consumes reused blocks whole,
  and rolls the bump pointer back only for a directly-adjacent free. The fix
  (main.c only): the four opening-overlay PCMs load LAST at init via
  `load_opening_audio()` so their phase-end releases roll the bump pointer
  back; BREACH is reclaimed unconditionally at the interior transition
  (slPCMStat stays asserted forever on Yaba — release gated on it never
  fires); `jo_reduce_memory_fragmentation()` runs before both BOSSCLR load
  sites. Post-fix margin at COMPLETE: 161,012 bytes of bank-1 bump spare.

Allocator rules now MEASURED in this codebase (treat as binding design
constraints for any future load): phase-transient allocations must be the
LAST allocations in their zone (LIFO with their lifetime); never rely on a
mid-heap free becoming usable contiguous space; call
`jo_reduce_memory_fragmentation()` after non-LIFO releases before a large
allocation; on Yaba Sanshiro never gate a release on
`jo_audio_is_channel_playing` alone.

**The MCP rig is available on this host** (`http://127.0.0.1:9640/mcp`).
Re-derive symbol addresses EVERY build with
`.deps/joengine/Compiler/WINDOWS/sh-elf/bin/nm.exe --target=coff-sh game.elf`
(leading underscore on symbols) and struct offsets from a host `offsetof`
program. The session scratchpad pattern (readback.py / heapdump.py) is
described in the handoff. A previous turn recorded this readback as
impossible; it is not.

## Named pending (recorded, not claimed)

- NH (the game's zero-`sel_hurt` cannot-be-hit rule) is wired but has never
  fired live — no zero-selector record appears in the walk/attack loops.
- The normal-release ISO's own full route (manual input) has not been driven
  end to end by a human; the encounter-test route is the measured evidence.
- Physical-hardware validation remains pending per `docs/HARDWARE_TEST.md`.

## The body of work: decode the state-dispatch index (type_promotion)

`table_set` provenance is RESOLVED for three families as literal immediates
in three per-state initializer routines, reached by an INDEXED JUMP (not
`bsr`/`jsr`):

```text
0x060570:   move.l #$130ac8,($50,A6)  ; "normal"
0x0495FC:   move.l #$13e97a,($50,A6)  ; "replace"
0x0003F0F0: move.l #$12ce5c,($50,A6)  ; "type_promotion"
```

The UNRESOLVED item is the dispatch itself: what index selects which
initializer runs, and how it is computed from actor/spawn context. It is the
prerequisite for hit/KO/spawn actions joining the ROM path with correct
per-state `table_set` — today the runtime holds the WALK/ATTACK-gated
constant `0x00130AC8` and frames outside those loops fall back to the
ADAPTED approximation (counted in the GAP diagnostic).

Ordered — each step gates the next; stop and record honestly if a gate
fails:

1. **Locate the indexed jump.** From a live WALK/ATTACK frame, trace forward
   to the instruction that dispatches among the three initializers. Capture,
   per state, the exact source of the index (register, memory field, or
   constant) and the jump targets. Confirm each target reaches one of the
   three store PCs above. The caller-side evidence so far: a fixed stack-top
   value `0x00FF00D8` at every entry (an outer dispatch loop's own address).
2. **Falsify the index→family map offline** across the stride-1 type-12
   corpus (`data/avsp_table_set_evidence.json`) with ZERO unexplained
   mismatches, plus a perturbation/negative control that must break — the
   same discipline as `tools/decode_avsp_table_set.py`.
3. **Reconcile hit/KO/spawn.** Determine which initializer — hence which
   `table_set` — those states actually run. If their store is a DIFFERENT
   immediate, that is the per-state value the runtime must adopt when they
   join; do not assume `0x00130AC8`.
4. **Wiring is a SEPARATE, gated turn.** Keep provenance and wiring apart,
   as the `table_set` and collision bodies did.

Provenance rule (binding): only a live, decrypted 68000 instruction trace is
trusted provenance. Correlation is never provenance. `spawn_type()` in
`tools/decode_avsp_table_set.py` is a hand-authored capture-context
classifier, NOT the game's dispatch, and must never appear in runtime code.

Headless MAME tracing needs `-debug` plus the script's
`debugger.execution_state = "run"`; `-debugger windows` is optional and
harmless as two tokens. Cold-boot replay is reliable; `machine:load()` is
not, in this environment. Check `tasklist //FI "IMAGENAME eq mame.exe"`
(never a `ps -W | grep mame.exe` loop — silently vacuous) and stop strays.

## Explicitly deferred (do not start here)

- Widening ROM action coverage to hit/KO/spawn (needs step 3's result
  first).
- Player ROM animation (blocks full two-sided ROM collision and the
  attack-box side of the predicate).
- Stage collision beyond room/lane clamps; actor separation; projectile
  path.
- The `round1` tile archive (any new carve must be re-simulated against the
  measured allocator rules above).

## Prohibited shortcuts

- No `table_set` constant in runtime code without its offline gate passing
  first, in the same turn.
- Do not treat correlation output as provenance, ever.
- Do not turn a missing measurement into a gameplay rule: a pose the ROM
  path does not cover keeps the ADAPTED approximation and is COUNTED; it
  never becomes silent invulnerability.
- Do not claim a verification that was not run; this host CAN run the MCP
  readback and the encounter route, so "impossible here" is not available.
- Do not add a large load without stating which zone it lands in and what
  frees before it, under the measured allocator rules above.
- Do not describe the per-tile renderer as final, or the build as a
  faithful playable level (see the handoff's gap table).

## Mandatory startup and repository safety

Read in order before changing anything: the `port-cps2-to-sega-saturn`
skill (`SKILL.md`, `references/workflow.md`), `AGENTS.md`, `CLAUDE.md`,
`docs/GOAL.md`, `docs/AGENT_HANDOFF.md` completely (newest sections
supersede older), `docs/PARITY_PLAN.md`, `docs/TEST_PLAN.md`,
`docs/HARDWARE_TEST.md`, then this file again.

Record the live state (`git status --short --branch`, `git log --oneline
-10`, `git rev-parse HEAD`, `git branch --show-current`); trust the
commands for HEAD. Stop any stray emulator before starting; an emulator
holding `game.iso` open can break a build's ISO step.

Rules (binding, unchanged): stay on `codex/avp-master-plan`; never
`git add .`/`-A`/`clean`/broad stash/reset/destructive checkout — stage
explicit paths only; never commit ROMs, raw captures, MAME logs, emulator
states, generated copyrighted assets, or disc images; preserve every
untracked `tools/diag_*`/`tools/mame_trace_*.lua`/instruction-log one-off.

## Checkpoint and handoff requirements

Commit at every green checkpoint with explicit paths. Keep
`docs/AGENT_HANDOFF.md` newest-first with: HEAD, dirty files, the exact code
or trace paths changed, live readbacks with the values actually read, which
verifications ran, and ordered next work. Keep this file pointing at the
next unexecuted body. Capability Gate 1 stays `0/7` regardless of outcome.
