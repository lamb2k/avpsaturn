# Next agent prompt: Capability Gate 1, phase A — decide the renderer

Continue the private native Alien vs Predator Saturn port using the
`port-cps2-to-sega-saturn` skill.

Repository:

```text
C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest
```

Expected branch: `codex/avp-master-plan`.

The execution order was re-sequenced on 2026-08-18. Phases A–E are in
`docs/PARITY_PLAN.md`. **This prompt authorizes phase A only.**

## Read and verify first

Read completely, in this order:

1. The skill's `SKILL.md` and `references/workflow.md`.
2. `AGENTS.md` and `CLAUDE.md`.
3. `docs/GOAL.md`.
4. `docs/AGENT_HANDOFF.md` — especially "Plan re-sequenced around the actor
   spine" and "Official Saturn reference-port findings".
5. `docs/PARITY_PLAN.md` — the phase A–E table and the re-sequence rationale.
6. `docs/TEST_PLAN.md`.

Record branch, HEAD, recent commits and `git status`. Preserve every existing
untracked/private ROM, MAME state, raw capture, `nvram/`, `snap/`,
`check_tail.py`, `tools/diag_*`, `tools/probe_*`, screenshot and helper file.
Stage explicit paths only. Never use `git add -A`, `git add .`, reset, clean or
a broad stash. Do not switch, merge or cherry-pick the Marvel lane, and do not
edit the separate MSHvSF worktree.

## Two facts that shape this body

1. **There is no Saturn Alien vs Predator.** Capcom never shipped one; this port
   is the first. Do not look for an AvP Saturn reference, disc or memory dump.
   Fidelity is always judged against MAME's CPS2 `avspu` under identical input.
2. **The only official CPS2-to-Saturn port available is a different game**
   (MSHvSF, research lane, immutable checkpoint `dc5d3ea`). Its per-tile VDP1
   finding is an `INFERRED` hypothesis recorded in the handoff, not a
   specification. Its numbers are not AvP budgets. This phase exists to get
   AvP's own answer, which may legitimately differ.

## Sole objective

Decide, by measurement, which of **our two candidate sprite pipelines** AvP
should use, before any actor is moved onto the ROM-record spine in phase B.

Pipeline 1 (current): precomposed per-palette 288x192 pose cels, built by
`compose_boss_rom_pose` in `main.c` and streamed through
`jo_sprite_add_4bits_image`.

Pipeline 2 (candidate): one 16x16 VDP1 command per source tile, in source
assembly order, colour-bank mode, with flip in `CMDCTRL` — the shape in which a
decoded ROM assembly *is* the command list.

## What to measure

On one deterministic route, for **one street wave plus Chrysalis**, at matched
anchors (idle, attack-active, impact, recovery), for **both** pipelines:

- reachable VDP1 command count — walk the command list's control flow; do not
  count stored non-zero slots, the two numbers differ substantially;
- **live colour banks per frame** — this is the resource a per-tile pipeline
  actually spends, and AvP's current allocation was sized for precomposed
  per-palette cels. If this number does not fit, pipeline 2 is dead regardless
  of command count;
- per-resource high-water marks: VDP1 VRAM, colour RAM, work RAM, cartridge;
- texture working set: distinct referenced tiles per anchor and across the wave.

Pipeline 2 does not need a finished renderer to be measured. A host-side model
driven by the already-decoded assemblies (`data/avsp_animation_scripts.json`,
`generated/avsp_boss_rom.h`) that emits the command list it *would* build is
sufficient, provided the model's output is validated against the pixels
pipeline 1 already produces for the same pose.

## Deliverables

- a focused measurement tool and a tracked, copyright-safe report
  (suggested: `tools/measure_avsp_sprite_pipelines.py`,
  `data/avsp_sprite_pipeline_budget.json`);
- every asserted field carries an evidence label — `MEASURED`, `DECODED`,
  `INFERRED` (with its falsifier), `ADAPTED` (with its reason), or `UNRESOLVED`
  (with the probe that resolves it), per the parity plan;
- determinism: run the tool twice, require an identical report hash;
- a written recommendation naming the **losing pipeline's specific failure**
  (which budget it exceeds, by how much, at which anchor). "Pipeline 2 looks
  cleaner" is not a result.

## Boundaries

- **Do not change the native rendering path in this phase.** Phase A decides;
  phase B implements. If the measurement is ambiguous, say so and name the
  further probe rather than picking.
- Do not start phase B, stage extraction, AI translation or full-game work.
- Do not decode further ROM tables in isolation — the standing rule from
  milestone 2, whose correct-but-inert collision records are the reason.
- Do not commit ROM bytes, raw screenshots, raw RAM dumps or disc members.
- Leave the milestone-1 fixture-signature cleanup (bystander `0xFFA000` versus
  emitting `0xFF9DC0`) deferred; it belongs with phase B/C actor work.

## Acceptance

Phase A passes when the tracked report shows, from AvP's own route, which
pipeline fits AvP's colour RAM and VDP1 budget, with the loser's failure named
and every field labelled. A host measurement does not close any Gate 1
condition and does not prove Saturn behaviour; say so in the handoff.

## Handoff discipline

Before stopping: update `docs/AGENT_HANDOFF.md` and `docs/PARITY_PLAN.md` with
the measurement and an honest Gate 1 / full-game status (both currently 0/7 and
0/9); record branch, HEAD, dirty files, raw paths, hashes and exact commands;
stop MAME and emulator processes or record their ownership; stage explicit files
only; commit one coherent checkpoint if the gates pass.
