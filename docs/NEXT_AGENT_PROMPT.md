# Next agent prompt: locate the action-level dispatch, then wire per-state table_set

## Where the project is

The Round 1 route runs end to end (`-EncounterTest`: MAIN_MENU → both street
waves → CLEAR → INTERIOR_TRANSITION → BOSS → BOSS_DEFEAT → RESULTS →
COMPLETE), street aliens animate from ROM scripts and die through the game's
own decoded hurt boxes (`HITS rom=8 approx=0`), and **the state-dispatch
mechanism is now decoded and falsified**. Read the handoff's newest section,
"State dispatch: DECODED (2026-08-19)", before anything else.

What is MEASURED and tracked:

- The actor state machine is a **two-level PC-relative jump-table** system.
  Both levels use the idiom `move.b ($N,A6),D0 / move.w ($6,PC,D0.w),D1 /
  jmp ($2,PC,D1.w)`, table base = dispatcher_pc + 12, `table[0]/2` = entry
  count. Level 2 is keyed on actor byte `+0x04` (sub-state); level 1 on the
  action byte at `+0x06`.
- Sub-state-0 handlers are the per-state initializers; each begins
  `addq.b #2,($4,A6)` so it runs once per state entry — the reason the live
  caller trace saw a recurring state-entry event with a fixed stack pointer.
- `tools/extract_avsp_dispatchers.py` enumerates **250** sub-state
  dispatchers (`data/avsp_substate_dispatchers.json`), self-tested against
  the three live-confirmed `table_set` initializers with a perturbation
  control.
- `tools/verify_avsp_substate_model.py` falsifies the index claim over
  **52,982** active actor-frames (`data/avsp_substate_model.json`): zero odd
  values, zero out-of-range, negative control correctly failing.
- **The opcode-space dump is valid at code addresses** (the data-space dump
  is not). Offline structural decode of game code is available and cheap.
  Provenance rule unchanged: offline LOCATES and STRUCTURES; live trace or
  corpus falsification CONFIRMS anything that enters the runtime.

## The body of work

### Step 1 — locate the action-level dispatch (the one open item)

85 action-level dispatchers exist, but none statically links to the street
alien's routines: scanning every one of them for a table entry landing on
the enclosing routine starts (`~0x060138`, `0x0495CC`, `0x03F0C4`) found
nothing. This corroborates the live caller trace's fixed return address
`0x00FF00D8` — the immediate caller is a **RAM-resident trampoline** the
game builds at run time.

The probe is live and bounded:

1. Cold-boot replay to a street wave using the pinned recipe (`-debug`, the
   script sets `debugger.execution_state = "run"`, byte-for-byte
   `enemy_actions` input schedule — copy it from
   `tools/mame_trace_table_set_writer_insn.lua` or the untracked
   `tools/mame_trace_dispatch_index.lua`). Check `tasklist //FI "IMAGENAME
   eq mame.exe"`, never a `ps -W` grep.
2. Dump and disassemble RAM around `0xFF0080–0xFF0140` (the trampoline
   region implied by `0x00FF00D8`), and breakpoint sub-state dispatcher
   `0x060532` logging the call chain and registers, to see what wrote the
   trampoline and what indexes it.
3. Deliverable: the action-word → action-routine rule, recorded in a tracked
   manifest (addresses/rules only, no ROM bytes), falsified offline against
   the stride-1 corpus with zero unexplained mismatches and a control that
   breaks. Extend `tools/extract_avsp_dispatchers.py` or add a sibling; wire
   into `test.ps1`.

If the trampoline turns out to be data-driven from a per-type table, that
table is the real prize — it is the same structure S5's AI translation will
walk.

### Step 2 — reconcile hit/KO/spawn `table_set` (offline, after step 1)

With the action map, find the street alien's HIT/KO/spawn action routines,
locate their sub-state-0 initializers among the 250 enumerated dispatchers,
and read their `table_set` immediates directly from the opcode image.
Cross-check against corpus frames carrying those action words. This answers
what the collision body left open: today those frames have no measured hurt
box and correctly fall back to the ADAPTED approximation, counted in the
`GAP` HUD diagnostic. **Do not assume `0x00130AC8` applies.**

### Step 3 — wiring (SEPARATE, gated turn — not in the same turn as step 2)

Only once steps 1–2 are green: carry per-state `table_set` and the hit/KO
records into the ROM actor path in `main.c`/`capability_model.c`, retiring
the `GAP` fallback for the states now covered. Keep the discipline the
collision body used: the offline gate passes first, in the same turn as the
constant it authorises; attacker/defender labelling stays honest; a missing
measurement keeps the ADAPTED approximation and stays counted, never
becoming silent invulnerability. Re-run the full chain: `test.ps1`,
`build.ps1 -Release`, `-EncounterTest` route to COMPLETE, MCP readback of
`runtime_ready` and the collision counters, clean `-Clean -Release` last.

## Queue after this body (user priority, do not re-order without the user)

**frontend → AI (S5) → traversal.**

The **real frontend** is next and is fully specified. Key measured facts:
the settled character-select screen is drawn by the three CPS tilemap layers
plus a 2-sprite `1P` cursor; title and select are distinct tilemap pages;
both decoder halves already exist in `tools/extract_avspu_stage1.py`
(`render_background`, `decode_objects`); and **colour RAM is the binding
constraint** — live banks per frame are 17 (select), 19 (title), 32 (round-1
title) against `AVSP_EXACT_PALETTE_BANKS` = 8. Plan CRAM before writing
renderer code. See `data/frontend_rom_composition.json` and the handoff's
frontend sections. The user requires the select screen be built from
ORIGINAL ROM ASSETS, not captured pictures.

**Reference lane:** consult
`C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest-MSHvSF` (measured
official Capcom Saturn port) for menus, loading, and sprite architecture.
Binding rule from its own transfer matrix: findings may change AvP's METHOD
or add a probe; its numbers are NEVER AvP budgets; never import its code,
assets, timing, or constants; never modify that worktree.

## Prohibited shortcuts

- No `table_set` constant in runtime code without its offline gate passing
  first, in the same turn.
- Do not treat correlation output as provenance, ever. `spawn_type()` in
  `tools/decode_avsp_table_set.py` is a capture-context classifier, not game
  logic, and must never appear in runtime code.
- Do not turn a missing measurement into a gameplay rule.
- Do not claim a verification that was not run; this host CAN run the MCP
  readback and the encounter route.
- Do not add a large load without stating its zone and what frees before it
  (allocator rules: no coalescing, whole-block reuse, transients must top
  their zone, `jo_reduce_memory_fragmentation()` after non-LIFO releases,
  never gate a release on `jo_audio_is_channel_playing` alone).
- Do not describe the per-tile renderer as final, or the build as a faithful
  playable level.

## Mandatory startup and repository safety

Read in order: the `port-cps2-to-sega-saturn` skill (`SKILL.md`,
`references/workflow.md`), `AGENTS.md`, `CLAUDE.md`, `docs/GOAL.md`,
`docs/AGENT_HANDOFF.md` completely (newest sections supersede older),
`docs/PARITY_PLAN.md`, `docs/TEST_PLAN.md`, `docs/HARDWARE_TEST.md`, then
this file again.

Record live state (`git status --short --branch`, `git log --oneline -10`,
`git rev-parse HEAD`, `git branch --show-current`). Stop stray emulators
before starting; one holding `game.iso` open can break a build's ISO step.

Rules (binding): stay on `codex/avp-master-plan`; never `git add
.`/`-A`/`clean`/broad stash/reset/destructive checkout — stage explicit
paths only; never commit ROMs, raw captures, MAME logs, emulator states,
generated copyrighted assets, or disc images; preserve every untracked
`tools/diag_*` / `tools/mame_trace_*.lua` / instruction-log one-off.

## Checkpoint and handoff requirements

Commit at every green checkpoint with explicit paths. Keep
`docs/AGENT_HANDOFF.md` newest-first with HEAD, dirty files, exact paths
changed, live readbacks with values actually read, which verifications ran,
and ordered next work. Keep this file pointing at the next unexecuted body.
Capability Gate 1 stays `0/7` regardless of outcome.
