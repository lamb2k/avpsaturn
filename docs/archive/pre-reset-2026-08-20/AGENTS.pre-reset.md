# AvP Saturn Port Agent Instructions

These instructions apply to the entire repository.

## Mission

- Build a private, capture-faithful, native Sega Saturn port of the complete US
  `avspu` revision of CPS2 Alien vs Predator.
- Round 1 from the frontend through the Round 2 title is Capability Gate 1. It
  proves the reusable engine and extraction method; it is not project
  completion.
- Complete and validate the entire single-player game before the final
  original-player-count multiplayer and physical-hardware conditions.
- Keep gameplay native SH-2 code. Do not replace the goal with a CPS2 emulator,
  approximate demo, video player, host-only simulation, or focused animation
  viewer.
- Keep the project private. Do not commit, publish, or redistribute ROM data or
  other private source material.

The standing objective and its completion conditions are in `docs/GOAL.md`.
It is independent of the current work package: pursue it until every condition
holds. `docs/PARITY_PLAN.md` holds the overall route, and
`docs/ROUND1_EXECUTION_PLAN.md` decomposes the active Round 1 presentation
body without replacing that route.

## Start every session

1. Use the `port-cps2-to-sega-saturn` skill and read its linked workflow.
2. Run `git status --short --branch` and inspect recent commits. Preserve all
   existing changes; never assume an uncommitted file is disposable.
3. Read `docs/AGENT_HANDOFF.md` completely. It is the authoritative volatile
   checkpoint for hashes, active profile, dirty files, failures, processes, and
   ordered next work.
4. Read `docs/PARITY_PLAN.md`. It is the current direction and S1-S6/full-game
   order.
5. Read `docs/ROUND1_EXECUTION_PLAN.md`. It holds the granular work packages,
   dependencies, ownership, and internal checks for the active presentation
   body. It never supersedes the parity plan.
6. Verify important handoff claims against the current worktree before relying
   on them.
7. Stay on the current task branch. `prototype/private-capability-test` is the
   production baseline, while `codex/avp-master-plan` is the current isolated
   planning/discovery branch. Do not switch, merge or cherry-pick between AvP
   and Marvel lanes unless the user explicitly authorizes that operation.
8. When present, read `docs/NEXT_AGENT_PROMPT.md`; it contains only the first
   executable body and never supersedes `GOAL.md`, `PARITY_PLAN.md` or the
   Round 1 execution plan.

## Reasoning effort and delegation policy

Optimize for total successful-work cost, not per-turn depth. Codex owns planning,
review, and final local verification; Claude Cloud owns implementation. Internal
Codex supervisor agents are read-only technical consultants, not a replacement
for the Codex/Claude ownership boundary below. Escalation is for unresolved
uncertainty, not a reward for difficulty.

### Normal effort: planning, implementation, and verification

Codex uses normal effort to define contracts, inspect diffs, run checks, and
make acceptance decisions. Claude uses normal effort for:

- implementing an already-decided design;
- translating an already-understood routine;
- extending a proven table or decoder pattern;
- writing tools, analyzers, and deterministic checks;
- localized debugging with a known reproduction;
- running the verification order and reporting results;
- integrating decoded data with an existing consumer.

Do not escalate merely because a task is technical or the ROM is involved.

### High: Codex's read-only technical consultant

Codex may use the read-only `supervisor` custom agent at high effort when the work
requires:

- reverse engineering or disassembly interpretation;
- tracing an unknown writer or reader;
- reconstructing control flow;
- determining an unknown table format or field semantics;
- forming or falsifying a hypothesis;
- explaining a MAME/native divergence;
- a bounded architectural decision;
- substantive review of a completed implementation.

This consultant does not own the plan, edit the implementation branch, or
accept Claude's work. Once it resolves the uncertainty, Codex turns the result
into a concrete contract or review finding for Claude.

### xhigh: escalation only

Spawn the read-only `deep_supervisor` custom agent at xhigh only for a single
unresolved question that survived a focused `supervisor` pass:

- several plausible readings still fit the same evidence;
- evidence contradicts an established interpretation;
- indirect or computed control flow is still unresolved;
- writer attribution is still ambiguous;
- PRNG generator identity or call ordering is still unresolved;
- a differential replay failure survived focused high investigation;
- a CPS2-to-Saturn architectural fork carries expensive downstream cost;
- high can only reach `ADAPTED` where the step needs `MEASURED`;
- two bounded attempts at the same root problem have failed.

`deep_supervisor` investigates only the handed-over question. It does not
re-plan the project, edit implementation, or accept a checkpoint. Return:

1. conclusion;
2. evidence, in the terms of the evidence chain;
3. alternatives rejected and why;
4. confidence, labelled `MEASURED`, `ADAPTED`, or `GAP`;
5. a falsification test;
6. an implementation contract if resolved.

### Plan of record

Consult `docs/GOAL.md`, `docs/PARITY_PLAN.md`,
`docs/ROUND1_EXECUTION_PLAN.md`, and `docs/AGENT_HANDOFF.md` before writing a
new plan. Do not reinterpret settled project decisions unless new evidence
falsifies them. Plan only far enough to resolve the active work package or the
immediate technical question.

### Review

Codex reviews every substantive Claude implementation against the written
contract and available local/private evidence. Codex may add one fresh internal
`supervisor` review for reverse engineering, architecture, or a material
correctness question; escalate to `deep_supervisor` only if that question
survives. Claude fixes one bounded confirmed list. One review-and-fix cycle is
the default; do not run repeated review loops.

### Test-driven implementation contract

Behavioral source, converter, parser, runtime, allocation, and build changes
use a recorded `RED -> GREEN -> REFACTOR` loop. Tests are part of the design
contract, not evidence added after implementation.

- Codex defines each chapter's observable behavior, fixture or oracle, exact
  RED command and expected failure, permitted implementation boundary, GREEN
  values, negative control, and regression tier. For long assignments, these
  contracts live in the execution book described below.
- Claude adds or identifies the test before changing production behavior and
  records the failure against the exact base. Prefer a distinct `test(red):`
  commit followed by `fix(green):`; a pre-existing failing test may substitute
  when its unchanged command and failure are recorded at the base SHA.
- If a proposed new test already passes at the base, stop that chapter and
  strengthen the test or report that the contract does not isolate missing
  behavior. Do not implement against a test that cannot detect the defect.
- Every promoted decoder or renderer needs a real perturb-and-compare negative
  control. A hardcoded boolean, population-presence check, or assertion that a
  mutation *would* differ is not a falsification test.
- After GREEN, refactor only while the targeted test stays green, then run the
  chapter's broader regression tier. A focused host pass never substitutes for
  required Saturn, full-route, audio, or hardware evidence.
- Documentation-only edits and purely mechanical changes do not require an
  artificial RED commit. They still require the narrowest meaningful lint,
  link, schema, or regression check.

Claude reports `RED_COMMIT`, `RED_COMMAND`, `RED_RESULT`, `GREEN_COMMIT`,
`GREEN_COMMAND`, `GREEN_RESULT`, negative-control results, and broader
regressions for every behavioral chapter. Codex independently verifies that
the RED test detects the missing behavior and the final commit passes it; a
missing or non-falsifying RED record is a review correction.

## Codex supervisor and Claude implementor workflow

The default cross-agent operating model is sequential and evidence-based:

- **Codex is the supervisor and plan owner.** Codex inspects the repository,
  writes the bounded implementation contract in `docs/NEXT_AGENT_PROMPT.md`,
  defines its checks and exclusions, reviews Claude's diff and report, runs or
  witnesses private local/emulator checks, decides acceptance, updates
  `docs/PARITY_PLAN.md`, and rotates the canonical next prompt.
- **Claude Cloud is the implementor.** Claude implements only the current
  contract on a separate implementation branch/worktree, adds or updates the
  required checks, runs every check available in its environment, records what
  it could not run, and updates `docs/AGENT_HANDOFF.md` with an implementation
  report plus a **Suggested next body**. Claude does not declare Capability
  Gate progress or replace the canonical next prompt.
- **The user remains the authority** for scope changes, remote publication,
  destructive operations, rights/licensing changes, and material acceptance
  tradeoffs.

### Optional self-contained Codex supervisor loop

The Claude Cloud boundary above remains the default. The user may explicitly
invoke `CODEX_SELF_CONTAINED_SUPERVISOR_LOOP` to keep a complete
supervisor/implementor loop inside one Codex task. That invocation is the
required authority for this mode; do not infer it from ordinary requests such
as "continue" or "keep going".

In this opt-in mode:

- the primary `gpt-5.6-sol` task owns architecture, execution books, review,
  acceptance, plan rotation, and final local/private verification;
- one `avp_implementer` subagent using `gpt-5.6-terra` owns the complete
  write-enabled implementation tranche;
- no second write-enabled agent runs concurrently, and the primary does not
  edit the implementation worktree while the implementor is active;
- the implementor works through all dependency-ready chapters, internal
  RED/GREEN/refactor cycles, coherent commits, and the tranche verification
  ladder before returning once at completion or a defined hard stop;
- normal failed tests, fixable build errors, falsified local hypotheses, and
  completed intermediate chapters are work inside the tranche, not reasons for
  a planning handback;
- the primary independently reviews the exact commit range and returns one
  consolidated correction book when required, rather than micro-corrections;
- the same underlying blocker receives at most three consolidated correction
  cycles before it is recorded as `BLOCKED` with the attempted alternatives;
- after acceptance the primary alone updates canonical status and
  `docs/NEXT_AGENT_PROMPT.md`, then may automatically assign the next ordered
  tranche without asking the user between tranches.

The durable invocation is `docs/CODEX_SELF_CONTAINED_SUPERVISOR.md`. Repository
safety, evidence, TDD, ownership, private-input, and physical-hardware rules in
this file apply unchanged. This mode does not authorize publication,
destructive operations, rights/licensing changes, material scope changes, or
fabricated hardware evidence.

Do not let Codex and Claude edit the same dirty branch/worktree concurrently.
At each iteration:

1. Codex finishes a clean, committed planning baseline and records its exact
   SHA. If the current tree is dirty, reconcile and land it before delegation.
2. Claude starts from that exact SHA on a separate implementation branch or
   cloud worktree. The branch name may follow the cloud environment's prefix,
   but the base SHA must be explicit.
3. Claude commits coherent implementation checkpoints and reports commit SHA,
   changed files, checks, failures, hashes, remaining `ADAPTED`/`GAP` items,
   and private validations it could not perform.
4. Codex reviews the commits rather than an unbounded dirty directory, reruns
   the applicable local/private evidence chain, and returns one bounded fix
   list when necessary.
5. After acceptance, Codex lands the implementation, records completed work,
   updates evidence-supported plan status, and replaces
   `docs/NEXT_AGENT_PROMPT.md` with the next bounded contract.

This repository currently has no remote. Do not create or publish one without
the user's explicit authorization. A cloud handoff therefore requires either a
user-provided private repository/worktree integration or an explicit patch/
bundle transfer. ROMs, raw captures, generated copyrighted assets, opcode
dumps, logs, disc images, and emulator state never travel with that handoff.
When Claude cannot access private inputs or Saturn tooling, it must leave those
checks `UNRUN`; Codex performs them locally before acceptance.

### Persistent behavior, current state, and relay payload

Keep these three layers separate so prompts stay short and do not drift:

1. **Persistent behavior:** this `AGENTS.md` section defines how Codex reviews
   Claude and how Claude reports to Codex. Do not paste the full policy into
   every invocation.
2. **Current state:** `docs/AGENT_HANDOFF.md`, `docs/PARITY_PLAN.md`,
   `docs/ROUND1_EXECUTION_PLAN.md`, and `docs/NEXT_AGENT_PROMPT.md` hold
   evidence, accepted status, package status, and the current contract.
3. **Relay payload:** an invocation contains only the exact base/commit SHAs,
   result summary, failed/`UNRUN` checks, gaps, and the action requested from
   the receiving agent.

A Claude implementation response must end with a copy-paste
`CODEX_REVIEW_INVOCATION` containing:

- repository/worktree, branch, Codex base SHA, and Claude commit SHA(s);
- objective and concise implementation summary;
- owned files and any overlapping/uncertain files;
- checks passed, failed, and `UNRUN`;
- known `ADAPTED`/`GAP` items;
- exact local/private validation requested from Codex.

When Codex receives that payload, it reads this behavior and the current state,
reviews the actual commits, and returns exactly one disposition:

- `ACCEPTED`;
- `CORRECTIONS REQUIRED` with one bounded fix list; or
- `NOT REVIEWABLE` with only the missing evidence/isolation request.

Codex must end every review response with a copy-paste `CLAUDE_INVOCATION`. For
`ACCEPTED`, it contains the next tranche from the newly rotated canonical
prompt. For `CORRECTIONS REQUIRED`, it contains only the correction body. For
`NOT REVIEWABLE`, it requests only the evidence/isolation work. The invocation
names exact BASE_SHA, branch suggestion, objective, first task, checks,
exclusions, `UNRUN` expectations, and report/commit requirements; it references
the repository behavior and current-state files instead of duplicating them.

Invocation mode is explicit:

- `MODE: SUPERVISED_IMPLEMENTATION` uses the Codex/Claude review boundary above
  and stops after the assigned package candidate is reported.
- `MODE: AUTONOMOUS_BOOK_IMPLEMENTATION` assigns Claude one prescriptive,
  Codex-authored execution book containing multiple ordered chapters. Claude
  runs each chapter's internal RED/GREEN/refactor loop, commits candidate
  checkpoints, updates the book's candidate run ledger, and immediately
  continues to the next dependency-ready chapter without requesting another
  plan or review turn. It returns once at book completion or at a defined hard
  stop. It does not edit canonical acceptance status, `docs/PARITY_PLAN.md`,
  the accepted package table, or `docs/NEXT_AGENT_PROMPT.md`.
- `MODE: AUTONOMOUS_IMPLEMENTATION` is a deprecated alias for
  `AUTONOMOUS_BOOK_IMPLEMENTATION`; it no longer grants plan-rotation or
  self-acceptance authority.
- Plan-rotating integration ownership is not a normal coding-agent mode. It
  requires a separate, explicit user instruction naming that authority; do not
  infer it from "continue", "autonomous", or a lengthy execution book.
- A delegated package worker receives `PACKAGE: RP<n>` and an exact `BASE_SHA`.
  It owns only that package/path set and returns a package report; it never
  integrates or advances shared status itself.

If no mode is stated, use `SUPERVISED_IMPLEMENTATION`.

### Autonomous execution books

The protocol and reusable chapter template are in
`docs/AUTONOMOUS_EXECUTION_BOOK.md`. An invocation using book mode must name:

- exact `BASE_SHA`, separate branch/worktree, book objective, owned files, and
  ordered chapter list;
- settled decisions not to re-derive;
- per-chapter preferred implementation, RED/GREEN contract, negative controls,
  regression tier, commit requirement, and falsification conditions;
- a candidate run-ledger path and final verification sequence;
- hard-stop conditions and actions that remain unauthorized.

Book chapters are internal implementation checkpoints, not new planning turns
or acceptance decisions. A normal failed test is work to repair, not a reason
to return to Codex. Claude stops early only when evidence falsifies the book's
architecture, required private evidence cannot be obtained, an unsafe or
unauthorized action is required, user-owned work cannot be isolated, or a
material design choice falls outside the book. On completion or hard stop,
Claude emits one consolidated `CODEX_REVIEW_INVOCATION` covering every chapter.

## Current direction: functional parity by ROM translation

The target is a **functionally parity-accurate complete game**. Round 1 is the
active Capability Gate 1, and the method is **translating game logic and data
out of the ROM**, not inferring it from screen captures. `docs/PARITY_PLAN.md`
holds the Gate 1 steps, full-game continuation, established memory/ROM
addresses, and evidence checks.

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

## Immediate execution body: Round 1 scene-complete presentation

Before resuming S5 enemy AI, complete the player-controlled presentation route
from cold boot through the Round 2 title. This is a bounded work body inside
Capability Gate 1; it is not a new milestone, phase, slice, or acceptance gate.

- Required route: legal/QSound/Capcom/opening, title wait, every story panel,
  Start transition, character select, confirmation shutter, Round 1 title, all
  Round 1 presentation scenes, results/intermission, and Round 2 title.
- Do not automate past, omit, or replace required scenes with new captured
  framebuffer/RLE playback. Existing captures and the 13 legacy keyframes are
  regression oracles only. New runtime scene content comes from ROM-derived
  tilemaps, object lists, palettes, scroll/priority data, and timed programs.
- The current frontend bitmap is indexed 8bpp NBG1, not RGB555 direct colour.
  RP0's palette, held-object, confirmation-shutter, and ROM-derived Round 1
  title checks now pass. RP1-RP3 provide the scene contracts, full-route census,
  and minimal scene runtime. The immediate package is RP4's representative
  two-plane stage renderer.
- The gameplay presentation target is hybrid: CPS scroll3 on NBG1, CPS scroll2
  on NBG0, VDP1 for actors/transient objects, and NBG2 or a bounded VDP1
  foreground only where measured CPS priority requires it. The selected RP4
  interval has a measured constant-zero row table, so it needs no line scroll;
  wider route coverage remains open. This architecture remains `ADAPTED` until
  the two-plane Saturn prototype proves NBG0 ownership, page mapping,
  per-object priority, live register state, and resource bounds.
- All four character-select cursor positions and source-measured input behavior
  are required. Predator Warrior is the only accepted gameplay route in this
  body; selecting another character may use an explicitly counted `ADAPTED`
  Warrior fallback.
- Attract/demo, service mode, continue/game-over, S5 AI, remaining cast parity,
  and physical-hardware acceptance are outside this body. Capability Gate 1
  remains `0/7` until its actual conditions pass.
- Restore and validate CDDA only after every Round 1 presentation asset needed
  during playback is resident. No unmeasured data-track read may occur after
  the CDDA lock.

The work-package graph and parallel ownership rules are in
`docs/ROUND1_EXECUTION_PLAN.md`; the first executable sequence and
falsification checks are in `docs/NEXT_AGENT_PROMPT.md`; volatile measurements
and dirty-worktree ownership are in `docs/AGENT_HANDOFF.md`.

## Terminology

Two vocabularies, and only two. Everything else is a retired name kept for
history; the map is at the top of `docs/PARITY_PLAN.md`.

- **Acceptance:** `Capability Gate 1` and its seven conditions, plus the nine
  full-game conditions. Only these move the 0/7 and 0/9 counts.
- **Work:** steps **S1-S6**, each with its own **checks**. The active
  presentation body may be decomposed into **work packages RP0-RP12** and
  **content batches A-C** in `docs/ROUND1_EXECUTION_PLAN.md`; those names are
  scheduling units, not acceptance claims.
- Do not plan new work as a "milestone", a "phase", or a "slice"; those name
  earlier orderings that were superseded on 2026-08-18.

- **"Gate" means Capability Gate 1**, the seven-condition acceptance contract in
  `docs/PARITY_PLAN.md`, and nothing else. Never call anything else a gate - not
  a pose comparison, a format check, a coverage run, a step's exit criteria, or
  the physical-hardware requirement.
- A step's own pass criteria are **checks**: "S1 check 2", "check C".
- A presentation work package may have a package check, and shared presentation
  mechanisms use the **shared-primitives check**. Neither affects `0/7` unless
  a whole Capability Gate 1 condition independently passes.
- Physical-hardware validation is **Capability Gate 1 condition 7** and
  full-game condition 9, not a gate of its own.
- A step passing every check it has does **not** move Capability Gate 1. Report
  the two separately and never let a green check read as gate progress.
- A few legacy tool filenames and serialized JSON keys contain `gate` for
  compatibility. Treat their results as checks; do not copy that wording into
  plans, status reports, comments, or new schemas.

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
  proves otherwise. Combine related lifetime assets and four-byte-align embedded
  archive offsets.
- Prove phase overlays in the full route, not only a focused build.
- Avoid unmeasured data-track seeks after CDDA begins.
- The target hardware configuration requires an NTSC Saturn, digital controller,
  and 32 Mbit expansion RAM cartridge.

## Verification order

For a changed work body, run the narrowest applicable checks, then broaden them:

1. Deterministic analyzer or converter validation.
2. Host capability tests and deterministic soak.
3. Focused Saturn profile and ISO-member byte/hash verification.
4. Full `-EncounterTest` Capability Gate 1 route through the Round 2 boundary.
5. Clean `normal-release` build and boot from the title/menu using the exact cue.
6. Real-time audible route validation.
7. Capability Gate 1 condition 7 physical Saturn validation.
8. After Capability Gate 1, cumulative title-to-current-endpoint tests for every added
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
- Other agents may work independently only under the ownership rules in
  `docs/ROUND1_EXECUTION_PLAN.md`: exact committed base SHA, separate clean
  worktree, one claimed package, explicit owned files, and no concurrent edits
  to shared integration surfaces. Evidence-only capture may proceed once its
  starting state is preserved; runtime lanes begin after the shared interface
  baseline is committed.
- Only the assigned integration owner updates the execution-plan status table,
  shared scene IDs, `main.c`, `capability_model.*`, build scripts, and common
  generated headers. Other agents report commit SHAs and checks for review.
- Before stopping or risking a restart, update `docs/AGENT_HANDOFF.md` with the
  branch, HEAD relationship, dirty files, profile, hashes, exact errors,
  running processes, reproducible commands, verified evidence, and ordered
  remaining work.
- When Claude believes an executable work body is complete, it adds a concise
  **Implementation report** and **Suggested next body** to
  `docs/AGENT_HANDOFF.md`, with exact commits, checks, hashes, available live
  results, confidence labels, and every `UNRUN` private/local check. It does not
  advance acceptance status or replace the canonical prompt.
- After Codex accepts the body, Codex:
  1. converts the implementation report into a dated **Completed work** entry;
  2. updates S-step and acceptance-condition status in `docs/PARITY_PLAN.md`
     only where accepted evidence actually changed;
  3. **replaces**, rather than appends to, `docs/NEXT_AGENT_PROMPT.md` with the
     next bounded executable contract, including settled facts, first task,
     falsification criteria, verification order, and explicit exclusions;
  4. re-reads the new prompt against current HEAD/worktree so it does not ask
     Claude to repeat completed work or rely on stale hashes.
- Do not advance `docs/NEXT_AGENT_PROMPT.md` merely because time is ending. If
  the current body is incomplete, keep its prompt current and record the exact
  resume point. If the next body is not yet defensible, say so explicitly in
  the handoff instead of inventing one.
- In `AUTONOMOUS_BOOK_IMPLEMENTATION`, completing a candidate chapter does not
  require a planning pause. Record its RED/GREEN evidence in the candidate
  ledger, commit, and continue within the book. Do not convert candidate work
  into accepted/completed status or rotate the canonical prompt; Codex performs
  those actions once after reviewing the complete book.
- Leave the normal-release disc clearly distinguishable from diagnostic discs.
- Do not declare the port hardware-ready or complete while any required route,
  fidelity, audio, crop, allocation, or physical-hardware condition remains
  open.
