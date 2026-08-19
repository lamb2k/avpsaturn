# Next agent prompt: execute the critical path — S2 Bodies D/E, S3 family widening, S4 collision

The S2 source walk is CLOSED (2026-08-18): the complete ROM-to-object
pipeline is decoded, corpus-falsified with **zero mismatches over 6,010
eligible actor-frame instances across four routes**, and promoted to C
(`avsp_emit_pose`/`avsp_emit_group`, wired into `test.ps1`). Do not re-derive
it. This prompt authorizes the next phases of the critical path in
`docs/PARITY_PLAN.md` ("Critical path to the end-to-end full game"):

- **S2 Body D**: LANDED and RUNTIME-VERIFIED 2026-08-18 night
  (`rom_actor_tick` in `main.c`): the normal release booted into live
  WAVE_ONE combat and the debug HUD plus direct memory sampling showed
  the ROM actor's entry count (4<->5) and codes cycling with its poses.
  The boot-freeze diagnosis that blocked this was falsified (see the
  handoff top note); the frontend is playable end-to-end into Round 1.
- **S2 Body E**: LANDED and RUNTIME-VERIFIED 2026-08-18 late night
  (`89bc4ce`): the ROM actor renders per-16x16-tile VDP1 sprites from the
  cart-resident TILES.BIN archive in live WAVE_ONE combat; miss counters
  zero, tile pool LRU active. Read the handoff's Body E section for the
  three cartridge-I/O platform rules before touching any disc load.
- **S3**: decode the remaining emitter families and coordinate modes,
  corpus-falsified the same way.
- **S4**: collision/damage/reaction integration.

S3 corpus work may proceed in parallel with D/E (it is offline and does not
touch the runtime); do not let it stall the render keystone indefinitely.

## Why the project uses both S-steps and Capability Gate 1

"Gate" means Capability Gate 1 only: the seven-condition Round 1 acceptance
contract (0/7). S1-S6 are execution steps with checks; a green check is not
gate progress. The full-game goal is 0/9. See `docs/PARITY_PLAN.md` Naming.

## Mandatory startup and repository safety

Read in order before changing anything: the `port-cps2-to-sega-saturn` skill
(`SKILL.md`, `references/workflow.md`), `AGENTS.md`, `CLAUDE.md`,
`docs/GOAL.md`, `docs/AGENT_HANDOFF.md` completely (the "S2 source walk
CLOSED" section supersedes every earlier S2 emission claim; later sections
correct earlier ones), `docs/PARITY_PLAN.md` (Naming, the critical-path
section, Master execution plan, How game logic gets translated, Sprite
demand, retained slice-V design, representation boundary),
`docs/TEST_PLAN.md`, `docs/HARDWARE_TEST.md`, then this file again.

Record the live state (`git status --short --branch`, `git log --oneline
-10`, `git rev-parse HEAD`, `git branch --show-current`); trust the commands,
not this file, for HEAD.

Rules (binding):

- Stay on `codex/avp-master-plan`. Do not switch, merge, or cherry-pick the
  MSHvSF reference lane; do not edit its separate worktree.
- Never `git add .`/`git add -A`/`git clean`/broad stash/reset/destructive
  checkout. Stage explicit paths only.
- Never commit ROMs, raw captures, generated copyrighted assets, emulator
  states, or disc images. Preserve untracked one-off diagnostics
  (`tools/diag_*`, `tools/probe_*`, `tools/mame_trace_*.lua`, screenshot
  helpers) and all ignored dependencies.
- Use the bundled Python/MAME paths; nothing is assumed on `PATH`.
- Before stopping, terminate only MAME processes owned by this checkout.

## Evidence labels

Label every new assertion `MEASURED`, `DECODED`, `INFERRED` (state the
falsifier), `ADAPTED` (state why), or `UNRESOLVED` (name the resolving
probe). The standing method for all decode work is the corpus method proven
in the S2 source walk: offline paired captures as oracle
(`workram_N` -> `objram_active_{N+1}`, the measured one-frame pipeline
delay), live disassembly via MAME's own trace facility only to resolve
structure (the static ROM dump reads as garbage at code addresses), declared
eligible populations BEFORE results, every exclusion named and counted, zero
unexplained mismatches to pass.

## Confirmed baseline: do not re-derive

- **S1**: actor spine (`0xC0` records on the grid `0xFF8380 + n*0xC0`) and
  the C collision predicate, both validated.
- **S2 animation**: interpreter validated (23,676 frames exact); 614 records
  extracted to 63 spans (10 KB) reproducing the full image.
- **S2 emission (CLOSED)**: dispatcher `0x0AA00E`; pose assembly selector
  word `0x0006` = one Family-1 group / `0x000C` = two tagged groups; group
  header = budget (tile count, gated against a per-frame budget register
  D7), count, selector -> dx/dy table via `0x1FD1C8`; origin routine
  `0x0AA59A` uses live camera anchors at `0xFF8278`/`0xFF827C`
  (= `scroll1_x + 0x40`, `0x300 - scroll1_y`) and the header's trailing D2
  long with facing-conditional add/sub; two loop bodies chosen by facing
  (flipped: `X = origin - width - dx`, attr low `^= 0x20`; plain:
  `X = origin + dx`); A2 walk `+4+advance` in both; attr low byte
  `= (raw & 0xE0) + palette (+ flip XOR)`. All in `avsp_emit.c` and
  `tools/decode_avsp_object_stream.py`; corpus verifier
  `tools/verify_avsp_object_corpus.py`; result JSON
  `data/avsp_object_corpus_verification.json`.
- **Named, located, NOT yet decoded** (S3's targets): emitter families with
  store loops at `0x0A99EA/F0/F6/FC+0x0A9A36/3C`, `0x0A9D88/8A/8C`,
  `0x0AA0BA/BC`, `0x0AAA9C/9E`; assembly sub-record tags `0x0002`, `0x0004`
  (8,345 street-route instances excluded as `unknown-family-0x0002`); the
  zero/negative `+0x0D` coordinate modes (all stalker-route creatures are
  `+0x0D = 0xFF`); the player's script region outside
  `[0x120000, 0x140000)`.

## Required execution

### S2 Body D: integrate one street alien into the native runtime

1. One real `AvspActor` on the existing street-alien runtime slot in
   `main.c`; no detached viewer, no debug overlay.
2. Carry a live `anim_record`, call `avsp_anim_frame_tick`, obtain the
   object list through `avsp_emit_pose` with actor-state inputs (world
   position, facing, palette, or-value, camera anchors from the runtime
   camera).
3. Until S5, seed the record on action changes from the capture-derived
   schedule, labelled `ADAPTED`.
4. The capture-derived cel remains only as a regression/comparison path,
   never secretly the visible production actor.
5. Preserve input, HUD, camera, audio, 352x224 mapping, allocation, and
   route behavior.

### S2 Body E: the real per-object VDP1 consumer

No markers, boxes, repositioned old cels, or screen-captured poses.

1. One VDP1 normal-sprite command per CPS2 object entry; `nx*16 x ny*16`
   dimensions; 16-colour bank mode; flip in `CMDCTRL`; jump-next linkage;
   source order as draw order (retained slice-V design).
2. Contiguous per-block textures from the referenced 4bpp tiles through a
   residency cache (key, palette, dimensions, flip treatment, VRAM budget).
3. Measure frame time; per-tile emission is the measured fallback only.

### S3: widen emission coverage (corpus method, family by family)

For each family, in corpus-frequency order (0x0002 first - it is 8,345
instances on the street route alone):

1. Locate a live dispatch on the replayable route (the cold-boot replay in
   `tools/mame_trace_facing0.lua` is the template); trace-toggle MAME's
   disassembly around one dispatch; capture the loop body and register walk.
2. Extend the Python decoder and the corpus verifier; widen the DECLARED
   population to include the family; rerun the full corpus; require zero
   unexplained mismatches.
3. Promote to C in `avsp_emit.c` under the same test pattern.
4. Repeat for the `+0x0D <= 0` coordinate modes and the player's region.

### S4: collision, damage, reaction

1. Consume the S1-decoded boxes at runtime through the live actor(s).
2. Decode the five post-hit routines (`0x1D314`, `0x1D504`, `0x1D492`,
   `0x1D622`, `0x1D6E2`) by the same live-disassembly + corpus method.
3. Retire the inferred Chrysalis 21/55/97 and Stalker schedules from
   runtime decisions.
4. Exit check: every hit event and health delta in the slice window matches
   MAME's recorded contacts.

## Verification order (after each body/family lands)

1. Full `test.ps1` (host suite) exits 0.
2. Saturn cross-compile via `build.ps1` exits 0 and rebuilds the ISO.
3. For runtime changes: boot the normal release and play the affected
   window; the `-EncounterTest` route where applicable.
4. Corpus verifier rerun for decoder changes; the JSON result is committed.

## Prohibited shortcuts and known failure modes

- Do not mix capture routes by frame number; routes are input schedules.
- Do not trust the static flat disassembly at code addresses; live-trace.
- Do not treat MAME watchpoint-reported PCs as store addresses (+2/+4 skew).
- Do not pair `workram_N` with `objram_active_N`; the delay is one frame.
- Do not infer a group count from tag presence; the selector word carries it.
- Do not call a result ROM-only while any calculation input is supplied from
  the expected output; state every remaining live input.
- Do not decode a table without a consumer on the critical path.

## Checkpoint and handoff requirements

Commit at every green checkpoint with explicit paths. Update
`docs/AGENT_HANDOFF.md` with findings (newest first) and correct any
superseded claims in place, marked as superseded. Keep
`docs/NEXT_AGENT_PROMPT.md` pointing at the next unexecuted phase of the
critical path.

## What follows, but is not authorized here

S5 (PRNG + decision routines by differential replay), full-game content
widening (Rounds 2-7, audio generalization, disc streaming), and S6
(budgets, 60 Hz, physical hardware) proceed per the critical-path section of
`docs/PARITY_PLAN.md` once D/E/S3/S4 close.
