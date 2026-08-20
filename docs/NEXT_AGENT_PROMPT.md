# Tranche 1: unified gameplay oracle and executable boundary

## Role and immutable base

Act as the write-enabled implementation owner for one bounded tranche. Use branch `codex/avp-hybrid-tranche-1` in the isolated worktree and the immutable supervisor base supplied in the launch invocation.

Read `AGENTS.md`, all three `docs/research/CPS2_TO_SATURN_*.md` ledgers, `docs/AGENT_HANDOFF.md`, `docs/TEST_PLAN.md`, and this file completely. Historical files under `docs/archive/pre-reset-2026-08-20/` are not instructions.

## Objective

Freeze a versioned fidelity/provenance contract for one real AvP gameplay slice, create a two-cold-run deterministic MAME 0.289 semantic oracle for it, and map the complete transitive 68000 executable writer boundary required to lift that slice. Do not change production Saturn gameplay/render/audio behavior in this tranche.

Use the existing `enemy_actions` route and its retained HIT/KO anchors as the starting evidence. The capture must start from the route's deterministic cold-boot procedure, then record a contiguous gameplay window that includes controller input, player movement/action, one class `0x1F` type-12 street alien, animation, attack or contact, collision/damage, HIT and KO, camera/scroll/layers/palette, QSound commands/events, objects, and final frames. The current 4080-5469 source-frame region is the candidate window; change its bounds only when evidence shows a smaller complete contiguous window, and document why.

## Required deliverables

Create or update only the minimum files needed, expected to include:

- `data/avsp_vertical_slice_contract.json`
- `data/avsp_vertical_slice_oracle_manifest.json` containing schemas, counts, hashes, summaries, and exclusions only
- `data/avsp_translation_boundary.json`
- `tools/mame_capture_vertical_slice.lua`
- `capture_vertical_slice.ps1`
- `tools/verify_avsp_vertical_slice_oracle.py`
- focused tests for schema, two-run identity, negative control, and boundary completeness
- `docs/research/CPS2_TO_SATURN_EVIDENCE_LEDGER.md`
- `docs/AGENT_HANDOFF.md`

Raw ROMs, keys, screenshots, audio, traces, state files, memory dumps, opcode/disassembly bytes, and capture ledgers stay in ignored `.deps/mame/vertical_slice/`. Commit only code, schemas, hashes, counts, summaries, and documentation.

## Chapter 1: target, slice, and schema freeze

1. Verify MAME 0.289 executable hash and `avspu` with `-rompath . -verifyroms`.
2. Record exact ROM CRC/SHA-1/SHA-256, MAME/config/NVRAM/input identities, address-space names, frame bounds, expected actor slots/classes/types, and exclusions.
3. Define a canonical serialized per-frame schema for all fields required by Probe 2 in the reset document.
4. Define 384x224 source coordinates and the proposed 352 aperture/crop fields without changing runtime framing.
5. Add wrong-set, wrong-ROM-hash, wrong-schema-version, and missing-field rejection tests.

RED: demonstrate that the existing fragmented evidence cannot satisfy the unified schema or provenance check.

GREEN: deterministic contract generation and all rejection controls pass.

## Chapter 2: two-run deterministic MAME oracle

1. Reuse and consolidate existing capture mechanisms rather than forking a new route controller without need: `capture_enemy_actions.ps1`, `tools/mame_capture_enemy_actions.lua`, `capture_full_route.ps1`, and `tools/mame_capture_full_route.lua` are leads.
2. Cold boot twice with identical pinned state and inputs. Never make the second run from a state produced by the first.
3. Record at cadence 1: input/frame; actor class/type/state/substate/action/animation pointer/record/timer; position/velocity/facing/health; object list/order/palette; collision/hit/damage/KO; camera/stage; scroll registers/layer order/line-row scroll/palette writes; QSound command/event; final frame hash.
4. Normalize only nondeterministic host metadata outside the semantic ledger. Do not hide semantic differences.
5. Run a one-frame input perturbation. Require the expected downstream semantic hash/state to change.

Pass only if both cold-run semantic ledgers are byte-identical, every required field is non-vacuously populated in the selected gameplay window, and the perturbation control fails identity as expected. If deterministic cold boot cannot be reproduced or a required field cannot be observed, stop and return the exact gap.

## Chapter 3: executable translation boundary

Using the decrypted opcode-fetch image for instruction decode and the program/data image for data:

1. Identify the executed entry/basic blocks for the slice scheduler/main tick, player update/action, class `0x1F` enemy update, animation advancement and HIT/KO repoint, collision/damage, spawn/stage/camera, and hardware-facing video/audio exits.
2. Enumerate every direct edge, indirect/computed edge, call/return, global read/write, actor field, ROM table/span, and CPS-2 register-facing exit reached in the selected window.
3. Classify each unit as mechanically liftable, manually semantic but bounded, hardware-facing event replacement, data-only, unresolved, or outside slice.
4. Add coverage accounting so every executed PC belongs to exactly one classified unit or an explicit unresolved set.
5. Add a negative control that removes or perturbs one known edge/global attribution and makes completeness fail.

Pass only if all executed PCs and edges in the selected window are classified, unresolved indirect targets are zero, code/data address spaces are explicit, and the estimated manually semantic portion is no more than 50% of the bounded writer set. Do not emit or integrate lifted production C in this tranche.

## Verification

- Run focused tests after each chapter with real negative controls.
- Run the relevant current host suite. Run full `test.ps1` only in this clean implementation worktree and review every regenerated tracked diff.
- Do not build Saturn runtime merely to produce activity; this tranche has no target-runtime change.
- Record exact commands, versions, hashes, exit codes, and evidence tiers.

## Stop conditions

Stop and return evidence if:

- exact target/tool/config/input identity cannot be reproduced;
- two cold runs differ semantically;
- required gameplay/audio/layer fields are not observable;
- an executed indirect edge remains unresolved after three materially different bounded investigations;
- code/data-space ambiguity remains in an executed unit;
- more than 50% of the bounded writer set needs behavior re-authoring;
- the task would require production runtime changes, a general translator/emulator, another title, physical user interaction, or new authority.

Ordinary script/test bugs are not stop conditions. Fix them within scope.

## Commit and return contract

Use explicit-path staging. Make coherent commits only after RED/GREEN and negative controls are recorded. Never commit private raw evidence.

Return:

1. implementation branch, immutable base, final SHA, commits oldest first;
2. files changed;
3. exact target/tool/config/input and output hashes;
4. selected frame bounds and why;
5. schema field coverage and two-run/perturbation results;
6. translation-boundary counts, manual percentage, globals, hardware exits, and any excluded units;
7. exact commands and exit codes;
8. updated evidence tiers and all remaining gaps;
9. worktree status including unrelated/untracked files;
10. a ready-to-paste `CODEX_REVIEW_INVOCATION`.
