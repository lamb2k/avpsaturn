# Next agent prompt: Capability Gate 1, milestone 2

Continue the private native Alien vs Predator Saturn port using the
`port-cps2-to-sega-saturn` skill.

Repository:

```text
C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest
```

Expected branch: `codex/avp-master-plan`.

Milestone 1 is complete at `40e7f76`, with the actor-attribution correction
at `4695dee`. Do not rerun the street-alien object-emission gate. This prompt
authorizes milestone 2 only: replace inferred collision with collision data
decoded from the game.

## Read and verify first

Read completely, in this order:

1. The skill's `SKILL.md` and `references/workflow.md`.
2. `AGENTS.md` and `CLAUDE.md`.
3. `docs/GOAL.md`.
4. `docs/AGENT_HANDOFF.md`.
5. `docs/PARITY_PLAN.md`.
6. `docs/TEST_PLAN.md`.

Then record the branch, HEAD, recent commits and `git status`. Preserve every
existing untracked/private ROM, MAME state, raw capture, `nvram/`, `snap/`,
`check_tail.py`, `tools/diag_*`, `tools/probe_*`, screenshot and helper file.
Stage explicit paths only. Never use `git add -A`, `git add .`, reset, clean or
a broad stash.

Remain on `codex/avp-master-plan` or an explicitly authorized descendant. Do
not switch, merge or cherry-pick the Marvel lane. Do not edit the separate
MSHvSF worktree. Marvel cannot identify AvP's collision tables.

The final destination remains the complete `avspu` game at functional parity.
Round 1 through the Round 2 title is Capability Gate 1. This assignment is one
Gate 1 milestone and does not authorize animation milestone 3, stage work, AI
translation, full-game expansion or a CPS2 emulator.

## Sole objective

Close milestone 2: decode actor-local hurtboxes, attack boxes and required
interaction records for every Round 1 player, street-alien, Stalker and
Chrysalis pose, then make the native collision path consume those game-derived
records.

The exit gate is:

- inferred Chrysalis contact frames 21/55/97 are no longer runtime collision
  rules;
- the inferred Stalker contact schedule is no longer a runtime collision rule;
- scalar range/lane checks are replaced by game-derived box overlap for the
  covered actors and actions;
- controlled hit and whiff fixtures pass;
- existing captures remain regression oracles rather than shipped collision
  data;
- Capability Gate 1 and the full-game goal remain open unless their complete
  acceptance conditions independently pass.

## Evidence already available

Do not start by recapturing the full route. Validate and reuse the existing
ignored raw evidence first:

- `.deps/mame/round1_debug_hitboxes/`: frames 4201..15000 at cadence 1,
  synchronized overlay screenshots and actor-state samples;
- `.deps/mame/round1_debug_collision/`: stage-collision evidence, not a
  substitute for actor boxes;
- `data/round1_debug_overlays.json`: tracked capture manifest;
- `data/round1_hitbox_brackets.json`: selected screen-space bracket evidence;
- `data/round1_hitbox_geometry.json`: four pivot-relative candidates;
- `data/avsp_animation_scripts.json`: animation records with byte `+8` and
  byte `+9` identified as interaction-table selectors;
- `.deps/mame/actorprobe/disasm_full.txt`: existing static disassembly;
- `tools/decode_avsp_animation_scripts.py`: current record decoder;
- `capability_model.c` and `tests/capability_model_test.c`: current inferred
  collision implementation and regression tests.

The four rows in `round1_hitbox_geometry.json` are leads, not authoritative
actor-local tables. Re-derive the raw sample layout and actor attribution
before expanding them. Actor records are `0xC0` bytes apart. Do not repeat the
earlier `0x180` scan, and do not assume a hard-coded actor address identifies
the box owner. Tie each box to live actor context, script/record pointer,
facing, pivot and source frame.

The animation-record consumers at `0x1CF94` and `0x1CF88` are high-value
starting points for bytes `+8` and `+9`. Their table format, role, coordinate
system and lifetime are not proven merely because the selector readers are
known.

## Required investigation

### 1. Revalidate actor and overlay attribution

- Validate the tracked overlay manifest against the ignored raw files and
  record the exact hashes used.
- Document the actor-state sample layout and the `0xC0` actor grid.
- Pair overlay rectangles and pivots with the correct actor slot, complete
  32-bit animation-record pointer, action/state, facing and source frame.
- Separate hurtboxes, attack boxes, throw/special boxes, inactive records and
  stage collision. Do not infer box role from color or overlap alone.
- Reject HUD/text/debug-glyph false positives deterministically.

If the current raw route cannot distinguish a role, add only the smallest
targeted deterministic capture needed. Write fresh raw evidence to a new
ignored directory unless replacement is deliberate and recorded.

### 2. Locate the game tables and readers

- Disassemble `0x1CF88`, `0x1CF94`, their callers and the complete paths from
  animation-record selectors to collision data.
- Identify the ROM table bases, entry widths, terminators/control flow,
  signedness, coordinate convention, facing transform, actor-local origin and
  box-role encoding.
- Identify the runtime routines that test overlap and write damage, hit state
  or reaction state.
- Use stock MAME 0.289 debugger watchpoints before considering a custom MAME
  build. Record `(frame, pc, address, width, data)` and relevant registers for
  bounded hit and whiff windows.
- Map only actor fields consumed by collision. Do not exhaustively label all
  96 words of every actor structure.

Every decoded field must name its source address/routine, evidence class,
confidence and falsification test. Do not promote a format inferred only from
screen rectangles.

### 3. Build a deterministic collision decoder

Prefer extending a proven extractor when its abstractions fit. Otherwise add
a focused decoder and tracked copyright-safe report, using names such as:

- `tools/decode_avsp_collision.py`
- `data/avsp_collision.json`
- a generated native header produced by the decoder
- focused host tests for the decoded format

The tracked report should contain, at minimum:

- ROM/table provenance and input hashes;
- actor family and action/pose or animation-record linkage;
- interaction selector values;
- box role and active/inactive lifetime;
- signed actor-local left/top/right/bottom coordinates;
- facing transformation;
- damage or reaction linkage where proven;
- matching overlay frames and controlled-event evidence;
- unresolved fields and prohibited inferences;
- coverage totals for player, street alien, Stalker and Chrysalis.

Generated data must be deterministic. Run the decoder twice and require an
identical report hash. Never commit ROM bytes, raw screenshots, raw RAM dumps,
disc members or generated copyrighted graphics.

### 4. Prove hit and whiff behavior

Create controlled source fixtures that hold actor/action/pose and input route
constant while changing only whether the relevant boxes overlap. At least one
fixture must prove a hit and one must prove a whiff for the same attack family.

Validate semantic events, not only pictures:

- attack box becomes active;
- overlap is or is not present;
- health changes only on the hit route;
- hit reaction/state transition occurs only on the hit route;
- repeated contact obeys the game's latch/retrigger behavior;
- facing and lane/depth behavior agree with the decoded records.

Use existing natural contacts as regression evidence, including the Chrysalis
and Stalker routes, but do not define the tables from their damage timing.

### 5. Replace the native inferred collision path

Only after the source decoder and controls pass:

- make `capability_model.c` consume generated game-derived collision records;
- remove the boss 21/55/97 contact schedule from runtime collision decisions;
- remove the inferred Stalker contact schedule from runtime collision
  decisions;
- replace applicable scalar reach/lane tests with actor-local box overlap;
- preserve old timing captures as explicitly named regression oracles;
- keep gameplay logic independent from rendering archives and screen-space
  debug geometry.

Do not add pose-specific replacement constants by hand. Do not treat overlay
pixels as the shipped collision source. Do not begin milestone 3 animation
integration while this collision gate is open.

## Validation order

Run the narrowest checks first, then broaden only after they pass:

1. Raw-evidence and manifest validation.
2. Decoder tests and deterministic report-hash reproduction.
3. Hit/whiff and facing negative controls.
4. Focused native collision tests.
5. `test.ps1`, including the controller route and 12,000-frame soak.
6. Relevant focused Saturn profile and ISO-member verification.
7. Full `-EncounterTest` route through the Round 2 boundary.
8. Restore and build `normal-release`, then boot its exact cue.

A host pass does not prove the Saturn build. An emulator pass does not close
physical-hardware validation. If no native code changes are justified because
the source format remains unresolved, do not perform the later build gates.

## Acceptance gate

Milestone 2 passes only when all of the following are true:

1. Collision records are derived from identified game ROM tables and reader
   routines, not inferred from damage frames or overlay pixels.
2. Every required Round 1 pose for the player, street aliens, Stalkers and
   Chrysalis has a resolved box set or an explicitly proven inactive record.
3. Actor attribution, facing, coordinate conversion and box roles are proven.
4. Controlled hit and whiff fixtures pass from decoded source data.
5. Native collision consumes the generated records and the inferred boss and
   Stalker schedules are absent from runtime decisions.
6. Host, soak, focused, full-route and restored normal-release checks pass in
   that order.
7. No private/raw/copyrighted source material is staged.

Partial table discovery is useful evidence but does not pass the milestone.
If blocked, leave the native collision implementation unchanged, document the
exact blocker and the next bounded command, and commit only a coherent
copyright-safe discovery checkpoint when tests permit.

## Deferred work

Do not detour into the milestone-1 fixture metadata cleanup. Its bystander
`0xFFA000` signature versus emitting actor `0xFF9DC0`, and dynamic object-list
watchpoint-window improvement, are explicitly carried into milestone 3 before
the street-alien animation decoder is promoted.

Do not activate Marvel research during this body. Do not begin Hadouken,
renderer selection, stage extraction, AI translation or full-game content
expansion.

## Handoff discipline

Before stopping:

- update `docs/AGENT_HANDOFF.md` and `docs/PARITY_PLAN.md` with proven evidence
  and honest Gate 1/full-game status;
- record branch, HEAD, dirty files, raw paths, hashes, exact commands, writer
  PCs/table addresses, coverage, controls and remaining uncertainty;
- distinguish decoded ROM data, capture evidence, inference and native
  integration;
- stop MAME and Saturn emulator processes or record their exact ownership and
  command lines;
- stage explicit files only;
- commit one coherent AvP checkpoint if the applicable gates pass.

Begin with raw-evidence validation and a focused disassembly of the two known
interaction-selector readers. Do not edit native collision until the source
record format survives a controlled hit/whiff falsification test.
