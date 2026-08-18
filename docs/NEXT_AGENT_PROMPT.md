# Next agent prompt: Capability Gate 1, body 1

> **STATUS 2026-08-18: this body is COMPLETE. Do not re-execute it.** Both gated
> frames (4214 and 4253) reproduce 20/20 from a fresh deterministic run; the
> exit gate in `docs/PARITY_PLAN.md` milestone 1 is met. The next executable
> body is **milestone 2 (replace inferred collision)**. Two corrections to the
> assignment text below, kept for the record: the state named here
> (`avspu_stage1_debug_hitboxes`) is **not** the oracle's route — the oracle came
> from the cold-boot route in `tools/mame_capture_enemy_actions.lua`, replayed
> from the `avspu_stage1_replay4200` anchor plus its post-anchor tail; and the
> actor base named here (`0xFFA000`) is **not** an actor base — type-12 actors
> sit on a `0x180` grid and the emitting actor is `0xFF9DC0`. See the handoff
> section "Capability Gate 1 — street-alien emission (2026-08-18 execution)".

Continue the native Alien vs Predator Saturn port using the
`port-cps2-to-sega-saturn` skill.

Repository:

```text
C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest
```

## Read and verify first

Read completely, in this order:

1. The skill's `SKILL.md` and `references/workflow.md`.
2. `AGENTS.md`.
3. `docs/GOAL.md`.
4. `docs/AGENT_HANDOFF.md`.
5. `docs/PARITY_PLAN.md`.

Then record the current branch, HEAD, recent commits and `git status`. The work
must remain on `codex/avp-master-plan` or an explicitly authorized descendant;
`prototype/private-capability-test` remains the production baseline. Preserve
all existing untracked/private ROM, MAME, `nvram/`, `snap/`, `check_tail.py`,
diagnostic and screenshot files. Stage explicit paths only. Never use
`git add -A`, `git add .`, reset, clean or a broad stash.

Do not switch to, merge or cherry-pick `codex/mshvsf-reference-lane`. Marvel is
an isolated Saturn reference lane and has no role in locating this AvP CPS2
writer.

The final project destination is the complete `avspu` game. Round 1 through the
Round 2 title is Capability Gate 1. This assignment is only the first body of
Gate 1 and does not authorize later milestones.

## Sole objective

Close the street-alien five-slot object-emission gate.

Use stock MAME 0.289 and state `avspu_stage1_debug_hitboxes`. Adapt the existing
actor-writer capture pattern into:

- `capture_street_alien_object_emission.ps1`
- `tools/mame_watch_street_alien_object_emission.lua`
- `tools/analyze_street_alien_object_emission.py`
- `data/street_alien_object_emission_oracles.json`
- `data/street_alien_object_emission.json`
- ignored raw evidence under `.deps/mame/object_emission/`

The wrapper, watcher and analyzer must accept scenario parameters for state,
post-load frame count, actor base, object base, first word, word count, bank-
select register and raw-output directory. Street-alien defaults are allowed;
the derivation must remain reusable for another AvP actor. Expected object
values belong only in the oracle fixture and validation path, never in the
derivation logic.

## Capture contract

- Install exactly 20 word-write watchpoints at `0x7080A0..0x7080C6`.
- Do not add simultaneous `0x7000A0..0x7000C6` watchpoints. Static disassembly
  proves `0xA99DC` initializes the logical writer pointer `A1=0x708000`.
- Remain below the empirical 34-watchpoint ceiling.
- Capture bank-select register `0x8040E0` once per frame to prove the logical
  write-buffer versus active/display-bank relationship.
- In one bounded run from the frame-4200 state, capture frames 4214 and 4253.
  Prove source-frame mapping from synchronized actor/work-RAM evidence; never
  assume Lua notifier count equals the source frame.
- Log mapped source frame, writer PC, address, width and data. Include A0/A4/A6
  when debugger expressions support them. Otherwise combine synchronized RAM
  evidence with static PC, caller and jump-table attribution.

Useful actor signatures:

- actor base `0xFFA000`
- actor type at `+0x08` = `12`
- facing flag at `+0x0F` = `1`
- frame 4214 animation pointer at `+0x1C` = `0x0012EC04`
- frame 4253 animation pointer at `+0x1C` = `0x0012E8EC`
- actor `+0x50` pointer on both frames = `0x00130AC8`

## Independent derivation and oracles

Reconstruct each ordered five-slot list from the new run before consulting the
validation fixture.

Frame 4214, different-pose anti-hardcoding control:

```text
[8113,0099,4efe,0131]
[80e3,00a9,4ef6,0431]
[80f3,00b9,4fc8,0131]
[8121,007b,473a,2431]
[8111,00ab,479c,1331]
```

Frame 4253 target:

```text
[814f,009e,4df8,0131]
[810f,00ae,4ef0,0531]
[815b,007b,4b04,2531]
[814b,00ab,4a88,1431]
[816b,006b,4958,0131]
```

Trace the street alien through:

```text
0xA99DC list builder
  -> exact group emitter
  -> 0xA9B48 common actor loop
  -> 0xA9B80 actor-type jump table
  -> exact per-type handler
  -> exact Family-1 variant in 0xAA4A4..0xAA598
```

Establish the per-part source layout and relationship among actor `+0x1C`,
actor `+0x50` and ROM data around `0x12FE06..0x12FEEE`. Derive every X, Y,
code, attribute, flag, palette/type transformation, preceding-entry offset,
slot order and bank/frame relationship.

## Gate and stopping point

The gate passes only when all 20 words for both frames are independently
derived and traced to their actual writer and source data, and frame 4214
demonstrates that frame-4253 values are not hard-coded.

Do not promote selector 12, implement Saturn rendering, begin collision work,
activate Marvel research or start full-game content expansion before this gate
passes. The existing actor-writer summary's `0x1665E`/`0x16636` reporting issue
is a separate non-gating cleanup; do not detour into it during this body.

At completion:

- Update `docs/AGENT_HANDOFF.md` and `docs/PARITY_PLAN.md` with proven evidence
  and honest Gate 1/full-game status.
- Record exact commands, MAME/save-state provenance, raw paths and SHA-256
  hashes, tracked-report hash, frame-mapping proof, writer/source attribution,
  bank relationship and per-frame pass/fail.
- Commit one coherent AvP technical checkpoint only if the gate passes. If it
  remains blocked, retain reproducible evidence, document the precise blocker
  and next command, and do not claim completion.
- Confirm no MAME process remains running.
