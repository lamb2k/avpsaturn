# Next agent prompt: decode the state-dispatch index (type_promotion) that
# selects the per-state table_set initializer

## Where the project is (the collision body is COMPLETE as scoped)

The "connect decoded collision to gameplay (defender side first)" body is
done. All five of its steps ran on `codex/avp-master-plan`:

- **Step 1 — offline gate** (`f56821f`, `data/avsp_table_set_gate.json`):
  over the stride-1 street capture, every active type-12 frame whose record
  pointer (+0x1C) is in the walk (`0x12EB4C`) or attack (`0x12D8A0`) span
  carries `table_set` (+0x50) == `0x00130AC8` — 2186/2186, zero exceptions.
- **Steps 2 + 3 — runtime plumbing + defender-side wiring** (`e9febe6`:
  `makefile`, `capability_model.h`, `capability_model.c`, `main.c`): ROM
  street aliens (active type-12 whose record pointer is in the walk/attack
  street spans) now carry `table_set = 0x00130AC8` (the gated constant),
  `sel_hurt` from the live record +8 via the anim-script span view, and their
  DEFENDER geometry in `cap_resolve_player_hit` is the player's ADAPTED
  attack-reach interval against the alien's REAL decoded hurt box.
  `sel_hurt == 0` means "cannot be hit" (no fallback), counted in the
  `rom_collision_no_hurt` debug-HUD counter.
- **Step 4 — host falsification** (`tests/avsp_runtime_collision_test.c`,
  wired into `test.ps1`): replays the S1 predicate over `collision_probe` +
  `collision_probe_boss` through the RUNTIME's input path — check A 1392
  street frames, 0/0/0 mismatches (non-vacuous); check B the exact S1 known
  contact set (21908/25/2516/24; latches 25/19/8/4). Full `test.ps1` exits 0
  (single-window and sparse-span forms).
- **Step 5 — verification**: full `test.ps1` exit 0; the clean `-Release`
  build + ISO member-hash verification ran green; the normal-release ISO
  booted in Yaba Sanshiro 1.20.37 and was read back by pixel statistics
  (busy, non-black, no `CAPABILITY TEST FAILED` banner).

Read the handoff's newest section, "Defender-side collision wiring + Step 4
host falsification (2026-08-19)", and its "table_set source rule: RESOLVED"
section before anything else. Do not re-open `table_set` provenance.

## Carried forward as NAMED PENDING (do NOT claim; run on a capable host)

1. **Live readback of the literal `runtime_ready=1` and
   `rom_collision_no_hurt` (NH) values, plus WAVE_ONE hit behavior** (ROM
   street aliens take hits with plausible reach differences from the
   capture-cel actors; the NH counter nonzero only in the expected windows).
   Pixel statistics CANNOT read these: this model has no image input, and
   this host has no emulator MCP client. They need a host that can read
   emulator state (the prior "Yaba Sanshiro MCP" path) or a debug HUD
   resolvable at the window's scale.
2. **The full Saturn `-EncounterTest` route** (`build.ps1 -EncounterTest`).
   It was NOT rerun this turn (it soaks combat resolution, which this turn
   touched). The 12,000-frame host soak is not a substitute.

## Project status to preserve

- Native SH-2 port at functional parity, not a CPS2 emulator. Capability
  Gate 1 remains `0/7`; the full-game goal remains `0/9`.
- The S1 actor spine and collision predicate (`avsp_collision.c/h`,
  `avsp_actor.c/h`) are proven on the host AND now called from gameplay
  (defender side) for ROM street aliens.
- Every active street alien in WALK/ATTACK carries independent ROM-driven
  animation state (`1350cf8`, live-validated). Hit/KO/spawn actions, the
  player, stalkers, and boss paths still use capture-derived production
  data; a street alien in `CAP_ACT_HIT` has no measured hurt box until it
  returns to WALK.
- Body E renders ROM-driven actors as per-16x16-tile VDP1 sprites — a
  working native diagnostic path, NOT the final one-command-per-object
  renderer of `docs/PARITY_PLAN.md`.
- Tile-archive builds are deterministic (`--scope street` explicit; `round1`
  refuses over-budget before writing).
- The clean normal-release boot renders (pixel-verified this turn); the
  literal `runtime_ready`/NH readback and the Saturn `-EncounterTest` route
  remain the two named-pending verifications above.

## The body of work: decode the state-dispatch index (type_promotion)

`table_set` provenance is RESOLVED for three families as literal immediates
in three per-state initializer routines, reached by an INDEXED JUMP (not
`bsr`/`jsr`):

```text
0x060570:   move.l #$130ac8,($50,A6)  ; "normal"
0x0495FC:   move.l #$13e97a,($50,A6)  ; "replace"
0x0003F0F0: move.l #$12ce5c,($50,A6)  ; "type_promotion"
```

The UNRESOLVED item is the **dispatch itself**: what index selects which
initializer runs, and how that index is computed from the actor / spawn
context. This is real S5-adjacent state-machine work (not `table_set`
provenance), and it is the prerequisite for hit/KO/spawn actions joining the
ROM path with correct per-state `table_set` — today the runtime holds the
WALK/ATTACK-gated constant `0x00130AC8` and a street alien in `CAP_ACT_HIT`
has no measured hurt box until it returns to WALK.

Provenance rule (binding): only a live, decrypted 68000 instruction trace is
trusted provenance here. Correlation is never provenance. `spawn_type()` in
the stride-1 decoder (`tools/decode_avsp_table_set.py`) is a hand-authored
capture-context classifier used to falsify the constants map offline; it is
NOT the game's dispatch and must never be wired into runtime code.

Ordered — each step gates the next; stop and record honestly if a gate
fails:

1. **Locate the indexed jump.** From a live WALK/ATTACK frame, trace forward
   to the instruction that dispatches among the three initializers. Capture,
   per state, the exact source of the index (register, memory field, or
   constant) and the jump target(s). Confirm each target reaches one of the
   three store PCs above.
2. **Falsify the index→family map offline.** Map the observed index values to
   {normal, replace, type_promotion} and predict each generation's store PC
   (hence its `table_set`) across the stride-1 target-type-12 corpus
   (`data/avsp_table_set_evidence.json`) with ZERO unexplained mismatches,
   plus a perturbation/negative control that must break — the same discipline
   as `tools/decode_avsp_table_set.py`.
3. **Reconcile the hit/KO/spawn states.** Once the dispatch is decoded,
   determine which initializer — hence which `table_set` — the hit/KO/spawn
   states actually run. If their store is a DIFFERENT immediate, that is the
   per-state value the runtime must adopt when those states join; do not
   assume `0x00130AC8`.
4. **Wiring is a SEPARATE, gated turn.** Do not widen ROM action coverage in
   the same turn as the decode (keep provenance and wiring separated, the
   same discipline the `table_set` and collision bodies used).

## Explicitly deferred (do not start here)

- Widening ROM action coverage to hit/KO/spawn (needs step 3's result first).
- Player ROM animation (blocks full two-sided ROM collision and the
  attack-box side of the predicate).
- Stage collision beyond room/lane clamps; actor separation; projectile path
  (S4 items after this body).
- The PCM phase-load refactor that affords the `round1` tile archive.

## Prohibited shortcuts (unchanged)

- No `table_set` constant in runtime code without the offline gate passing
  first, in the same turn.
- `spawn_type()` from the stride-1 decoder must not appear in runtime code
  (capture-context classifier, not game logic).
- Do not treat correlation output as provenance, ever.
- Do not widen ROM action coverage in the same turn as the dispatch decode.
- Do not describe the per-tile renderer as final, or the build as a faithful
  playable level (see the handoff's gap table).

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

## Checkpoint and handoff requirements

Commit at every green checkpoint with explicit paths. Keep
`docs/AGENT_HANDOFF.md` newest-first with: HEAD, dirty files, the exact code
or trace paths changed, MCP/pixel readbacks, whether the named-pending
verifications ran, and ordered next work. Keep this file pointing at the next
unexecuted body. Capability Gate 1 stays `0/7` regardless of this body's
outcome.
