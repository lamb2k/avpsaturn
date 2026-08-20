# AvP Saturn Port Agent Instructions

These instructions apply to the entire repository.

## Mission

- Build a private, capture-faithful, native Sega Saturn port of the complete US
  `avspu` revision of CPS2 Alien vs Predator.
- Round 1 from the frontend through the Round 2 title is Capability Gate 1. It
  proves the reusable engine and extraction method; it is not project
  completion.
- Complete and validate the entire single-player game before the final
  original-player-count multiplayer and physical-hardware gates.
- Keep gameplay native SH-2 code. Do not replace the goal with a CPS2 emulator,
  approximate demo, video player, host-only simulation, or focused animation
  viewer.
- Keep the project private. Do not commit, publish, or redistribute ROM data or
  other private source material.

The standing objective and its completion conditions are in `docs/GOAL.md`.
It is phase-independent: pursue it until every condition holds. `docs/PARITY_PLAN.md`
holds the route, `docs/GOAL.md` holds the destination.

## Start every session

1. Use the `port-cps2-to-sega-saturn` skill and read its linked workflow.
2. Run `git status --short --branch` and inspect recent commits. Preserve all
   existing changes; never assume an uncommitted file is disposable.
3. Read `docs/AGENT_HANDOFF.md` completely. It is the authoritative volatile
   checkpoint for hashes, active profile, dirty files, failures, processes, and
   ordered next work.
4. Read `docs/PARITY_PLAN.md`. It is the current direction and phase order.
   The handoff says where work stopped; the parity plan says where it is going.
5. Verify important handoff claims against the current worktree before relying
   on them.
6. Stay on the current task branch. `prototype/private-capability-test` is the
   production baseline, while `codex/avp-master-plan` is the current isolated
   planning/discovery branch. Do not switch, merge or cherry-pick between AvP
   and Marvel lanes unless the user explicitly authorizes that operation.
7. When present, read `docs/NEXT_AGENT_PROMPT.md`; it contains only the first
   executable body and never supersedes `GOAL.md`, `PARITY_PLAN.md` or the
   handoff.

## Supervisor and implementor protocol

Work is sequential. Only one role owns the repository at a time.

- **Codex is the supervisor, systems architect, reverse-engineering
  strategist, plan owner and acceptance authority.** Codex defines the real
  technical question, leading hypotheses, distinguishing evidence, preferred
  solution, decision branches, TDD contract, negative controls, Saturn
  constraints, ordered chapters and acceptance criteria. Codex does not
  delegate parity definitions, architecture ownership, acceptance thresholds
  or overall sequencing.
- **Claude is the directed investigator and implementor.** Claude runs the
  prescribed traces and experiments, writes the failing tests, implements the
  evidence-supported branch, debugs ordinary build/runtime failures, executes
  the verification ladder and commits coherent checkpoints. Claude may report
  contradicting evidence and recommend a change, but may not silently redesign
  the system, weaken acceptance, replace ROM translation with approximation or
  accept its own recommendation.

Every unknown source fact must receive a bounded contract in
`docs/NEXT_AGENT_PROMPT.md`: exact question, hypotheses, settled evidence,
prescribed instruments, distinguishing evidence, negative controls, decision
table, implementation boundary, tests and regressions. Claude continues into
the matching implementation branch; investigation completion alone is not a
handoff condition.

An architectural hard stop exists only when evidence falsifies every
prescribed branch, materially different designs remain equally supported, a
memory/fidelity/rights/scope boundary would be crossed, required private
evidence or tooling is unavailable after the bounded recovery procedure, or
user-owned work cannot be isolated safely. A failed test, wrong local
hypothesis, compiler/linker error, emulator crash or implementation debugging
problem is not by itself a hard stop.

Codex reviews a committed result and returns exactly one disposition:
`ACCEPTED`, `CORRECTIONS REQUIRED`, or `NOT REVIEWABLE`. Every review verifies
the evidence, falsifying control, failing-first RED, non-weakened GREEN,
prescribed architecture, reported divergences and cumulative Saturn routes,
then ends with a complete `CLAUDE_INVOCATION`. Acceptance also records the
accepted range/evidence in the handoff, updates canonical status only where
evidence changed it, selects the next dependency-ready body, replaces
`docs/NEXT_AGENT_PROMPT.md`, and commits the supervisor documentation
checkpoint when appropriate. Do not ask whether to continue when the plan
already orders the next body.

## Current direction: functional parity by ROM translation

The target is a **functionally parity-accurate complete game**. Round 1 is the
active Capability Gate 1, and the method is **translating game logic and data
out of the ROM**, not inferring it from screen captures. `docs/PARITY_PLAN.md`
holds the Gate 1 phases, full-game continuation, established memory/ROM
addresses and evidence gates.

- Do not extend the capture-a-clip-and-bind-it method for new actors or
  actions. It cannot represent unobserved behaviour, does not scale, and cannot
  reach AI. Existing captured clips remain valid as **regression oracles**.
- The graphics are already solved: the 16 MiB CPS2 graphics region is
  reconstructed byte-for-byte. What is missing is assembly instructions, which
  live in ROM tables that are already located.
- The retail ROM still contains Capcom's debug tools, including hitbox and
  stage-collision overlays. Prefer reading real data from them over inferring
  hit windows from health changes.
- Stock MAME 0.289 is the primary observation instrument. The retained debug
  overlays work with Development hardware mode, active-low fields held before
  frame 0, and a one-time post-init software-switch injection because the
  retail ROM removed the DIP-to-RAM copy. Try stock debugger watchpoints before
  treating a custom MAME build as necessary; keep any fallback patch set
  tracked and pinned.
- Functional parity means matching the actor state trajectory, real hitboxes,
  and real animation sequences and durations. It does not mean identical
  framebuffers or RNG streams. If AI consumes a PRNG, record that decision
  explicitly before translating it.
- Do not begin native reimplementation before a ROM-decoded sprite assembly
  reproduces an already-captured pose pixel for pixel. Building on a misread
  table format is the most expensive available mistake.

The repository has independent Git history even if its checkout is nested in a
larger workspace. Relocation is organizational only; never move or delete the
working checkout without first preserving `.git` and all required ignored
private inputs.

## Terminology

Two vocabularies, and only two. Everything else is a retired name kept for
history; the map is at the top of `docs/PARITY_PLAN.md`.

- **Acceptance:** `Capability Gate 1` and its seven conditions, plus the nine
  full-game conditions. Only these move the 0/7 and 0/9 counts.
- **Work:** slice steps **S1-S6**, each with its own **checks**.
- Do not plan new work as a "milestone", a "phase", or a "slice"; those name
  earlier orderings that were superseded on 2026-08-18.

- **"Gate" means Capability Gate 1**, the seven-condition acceptance contract in
  `docs/PARITY_PLAN.md`, and nothing else. Never call anything else a gate - not
  a pose comparison, a format check, a coverage run, a step's exit criteria, or
  the physical-hardware requirement.
- A step's own pass criteria are **checks**: "S1 check 2", "check C".
- Physical-hardware validation is **Capability Gate 1 condition 7** and
  full-game condition 9, not a gate of its own.
- A step passing every check it has does **not** move Capability Gate 1. Report
  the two separately and never let a green check read as gate progress.

## Evidence and fidelity

- Prefer ROM tables and the game's own debug overlays as source truth. Use
  deterministic MAME capture to confirm what those produce, and retain older
  capture-derived clips as regression oracles rather than extending capture
  and bind for new actors or actions.
- Treat verified deterministic MAME capture as source truth for frame timing,
  inputs, objects, palettes, hit events, camera anchors, and QSound timing
  where no ROM-derived equivalent exists yet.
- Preserve the evidence chain:
  `ROM audit -> ROM table/routine extraction plus deterministic MAME evidence
  -> validating analyzer -> round-specific semantic data and translated C ->
  native SH-2 integration -> ISO member hash -> emulator -> physical Saturn`.
- Generate derived data through repository scripts. Do not hand-edit generated
  headers or archives.
- Label results honestly as capture-exact, native-but-approximate, or missing.
  Screenshots alone do not prove timing, interaction, audio, or route fidelity.
- A reduced-cadence capture may size a representation, but shipped exact
  timelines require every source frame.
- Preserve the documented 384-to-352 horizontal mapping and 224-line height.
  Reject accidental crop, stretch, or unverified black bars.

## Saturn constraints

- Prefer VDP2 for full-screen/scrolling surfaces and VDP1 for actor composites.
- Budget VDP1 texture RAM, Saturn work RAM, SCSP RAM, and both 32 Mbit expansion
  RAM banks separately.
- Treat the Jo Engine reuse allocator as whole-block unless current evidence
  proves otherwise. Combine related phase assets and four-byte-align embedded
  archive offsets.
- Prove phase overlays in the full route, not only a focused build.
- Avoid unmeasured data-track seeks after CDDA begins.
- The target hardware configuration requires an NTSC Saturn, digital controller,
  and 32 Mbit expansion RAM cartridge.

## Verification order

For a changed slice, run the narrowest applicable checks, then broaden them:

1. Deterministic analyzer or converter validation.
2. Host capability tests and deterministic soak.
3. Focused Saturn profile and ISO-member byte/hash verification.
4. Full `-EncounterTest` Gate 1 route through the Round 2 boundary.
5. Clean `normal-release` build and boot from the title/menu using the exact cue.
6. Real-time audible route validation.
7. Gate 1 physical Saturn validation.
8. After Gate 1, cumulative title-to-current-endpoint tests for every added
   round, followed by all-character complete single-player routes.
9. Original-player-count multiplayer stress and complete-route validation.
10. Final clean-release physical Saturn validation for the complete game.

Inspect the emulator process command line because Yaba Sanshiro can retain stale
disc state. A focused or host pass never substitutes for full-route or hardware
proof.

## Repository hygiene and handoff

- Keep ROMs, `.deps`, emulator state, generated builds, raw captures, and other
  ignored private artifacts out of Git unless the repository explicitly tracks
  a derived evidence report.
- Use `apply_patch` for source/document edits and preserve unrelated user work.
- Commit coherent checkpoints only after relevant deterministic checks pass.
- Before stopping or risking a restart, update `docs/AGENT_HANDOFF.md` with the
  branch, HEAD relationship, dirty files, profile, hashes, exact errors,
  running processes, reproducible commands, verified evidence, and ordered
  remaining work.
- Leave the normal-release disc clearly distinguishable from diagnostic discs.
- Do not declare the port hardware-ready or complete while any required route,
  fidelity, audio, crop, allocation, or physical-hardware gate remains open.
