# REIMPLEMENT-13-SOURCE-CLOSED-ROUND1 task card

TASK: REIMPLEMENT-13-SOURCE-CLOSED-ROUND1
KIND: INTEGRATE
STATUS: READY
CHECKPOINT: reimplement-source-closed-round1
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 1
DEPENDENCIES: [SPEC-02-ROUND1-EXECUTABLE-CONTRACT]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator]
OPTIONAL_LANES: [Full]
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [QA-13-ROUND1-END-TO-END-DIFFERENTIAL]

## Objective

Translate only SPEC-02 and its generated fixtures into portable native C so
Predator Warrior can play from direct Round 1 entry through boss defeat, stage
clear, and stable Round 2 handoff with no fixed-frame, counter, scene, snapshot,
or authored-fallback gameplay authority.

## Owned paths

- Bounded Round 1 native gameplay and source-derived content data named by
  SPEC-02; focused host/Target/Emulator tests; state and control ledgers

## Existing systems to reuse

- Accepted Port V2 rendering, VDP1/VDP2, camera adapters, HUD, PCM/CDDA,
  loading/residency, collision, HIT/KO, readback, and visual-QA infrastructure.

## Systems deliberately disabled

- Raw trace/disassembly implementation, runtime 68000 interpretation, frontend,
  other characters, multiplayer, later-stage gameplay, and physical status.

## Focused machine checks

- Preserve source actor-pool semantics, scheduler order, signedness,
  state/substate, arithmetic/branch order, RNG call order, and table indexing
  where supported. Build vertically through each segment, encounter, actor,
  event, boss, clear, and handoff; after each body run host differential, real
  mutations, Target, paired Emulator, rendered inspection, correction, commit,
  push, and remote-SHA verification.

## Saturn build profile

Direct diagnostic Round 1 boot plus normal interactive image, built only from
SPEC-02, generated fixtures, accepted interfaces, and approved assets.

## Emulator readback

Paired cold deterministic progression plus rendered inspection after every
added body; require zero fallback, canary failure, unsupported result, or
candidate/spec identity mismatch.

## Human-review requirement

No per-segment review. QA-13 must pass before USER-10.

## Exclusions

- No frontend/title/select, four-character work, multiplayer, full-game engine,
  raw source-note implementation, visual guesses, or physical claim.

## Hard stops

- SPEC-02 violation, required UNKNOWN, guessed behavior, objective discrepancy,
  target/emulator failure, nondeterminism, fallback, or approved-lock regression.

## Active vertical checkpoint

The SPEC-02-bound stable-entry state and exact fixed actor-pool initialization
are implemented in portable C, connected to the direct diagnostic boot, and
visible through target readback. They pass the host differential, nine bounded
mutations/suppressions, Target, paired-emulator evidence, rendered legacy-scene
inspection, Fast, and Oracle. This remains a native diagnostic substrate, not
yet a playable segment. The first source-derived Round 1 title view now renders
through the accepted presentation adapter and passed direct paused-frame
inspection. Implement the first exact route-state guard, title-owned spawn
boundary, and controllable street segment next.
Evidence: `data/reimplement13_round1_stable_entry.json`.

## Next eligible cards

- `QA-13-ROUND1-END-TO-END-DIFFERENTIAL` after the complete stable Round 2
  handoff candidate is committed and frozen.
