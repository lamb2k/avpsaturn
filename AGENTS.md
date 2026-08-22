# AvP Saturn port agent policy

## Authority and control loop

Codex Goal Mode owns interactive implementation, sequencing, acceptance, and
task-card activation. `docs/PARITY_PLAN.md` is the only roadmap,
`project_state.yaml` is the machine-readable state, and files under
`docs/task_cards/` are the bounded work queue. Do not create another
orchestrator, autonomous state machine, master plan, or competing backlog.

Read `AGENTS.md`, `project_state.yaml`, and the active task card completely
before work. Read `docs/TEST_PLAN.md` for verification and
`docs/HARDWARE_TEST.md` before physical work. Read
`docs/research/CPS2_TO_SATURN_RESET.md` for behavioral, runtime, device, or
architecture changes.

Exactly one implementation task owns writes at a time. Direct Codex
implementation is the default for ordinary work; nested Codex executors are
not used for ordinary implementation. Claude is an optional bounded provider
only when the active task card explicitly permits it. The task card fixes the
scope, owned paths, checks, exclusions, hard stops, and next eligible cards.

## Branch and worktree continuity

A new tranche, task card, milestone, or checkpoint does not by itself justify
a new branch or worktree. For each approved card, coherently commit the
completed work, push it to `private-origin`, and verify that the remote branch
SHA equals the local commit. Before activating its successor, inspect the
current repository state and select the existing branch and worktree that best
continue the dependency chain and intended development line. Continue there
sequentially from the approved predecessor, using explicit, clean commits as
meaningful milestone and checkpoint boundaries.

Create a new branch or worktree only when required isolation, parallel
development, incompatible dependencies, an unsafe dirty state, or a genuinely
separate line of development makes reuse inappropriate. Preserve existing
worktrees; do not remove, migrate, reset, or rewrite them merely to conform to
this routing policy.

## Development loop

Use this loop for each existing subsystem:

1. isolate it in a salvage bench;
2. run focused machine validation with a deterministic repeat and a real
   negative control;
3. build its dedicated Saturn diagnostic and self-review it in the pinned
   emulator;
4. obtain human review when appearance or feel is subjective;
5. record `SALVAGE_AS_IS`, `SALVAGE_WITH_ADAPTER`, `REPAIR`, or `REPLACE`;
6. promote it behind a `port_v2` production interface;
7. integrate it with one additional dependency and repeat.

The old mixed runtime is reusable evidence and implementation material, not
the production gameplay authority. Loading, graphics, animation, input, VDP1,
VDP2, palette, HUD, audio, diagnostic, build, and emulator systems must receive
a bounded salvage experiment before replacement. The lab and prototype may
prove reuse or falsify a candidate; they do not advance parity or physical
capability gates.

Within the active card's owned paths, automatically correct ordinary compile,
focused-test, asset, integration, emulator, readback, palette, pivot, and
animation problems. Stop only for a declared hard stop, missing evidence,
unsafe worktree state, required physical interaction, a material architecture
decision, or an exhausted bounded correction cycle.

## Saturn self-review and human checkpoints

Every Saturn-facing bench must use its dedicated diagnostic build, the pinned
emulator, automated runtime-ready and asset-failure readback, relevant actor
position and render-count diagnostics, a bounded stability run, and a
screenshot or short clip. Compare it with the old-build baseline and existing
source evidence before presenting it to the user.

Do not self-approve subjective visual scale, pivot or grounding, animation
cadence, movement feel, camera feel, palette preference, composition, or audio
feel. Every visible or audible checkpoint creates an ignored package at
`build/feedback/<task-id>/` with the practical evidence listed in the task
card and asks: "What should remain unchanged, what looks or feels wrong, and
which issue should be fixed first?"

A `USER_REVIEW` card performs no implementation and never infers approval from
silence. While feedback is pending, activate only a predeclared dependency-safe
card that cannot alter the result under review. Record the user's exact
response in `data/port_v2_migration_map.yaml`, then derive approved components,
requested changes, priority, and the next bounded repair or promotion card.

A user-approved component is locked. Later work may change it only after
identifying the approved behavior at risk and requesting renewed review.

## Evidence and acceptance

Machine validation, fidelity evidence, emulator review, human approval, and
physical Saturn proof are independent. A passing emulator check is not human
visual approval, and neither is physical-hardware proof. Preserve the evidence
vocabulary and never promote a tier.

The only title target is MAME set `avspu`, `Alien vs. Predator (USA 940520)`.
The selected architecture remains offline extraction, address-traceable data,
bounded selective lifting into native C, native SH-2 subsystems, MAME 0.289 as
semantic oracle, VDP1 actors, VDP2 stage layers, fixed cartridge arenas, SCSP
PCM, CDDA music, and one master-SH-2 loop until profiling proves otherwise.
Do not build a CPS-2 emulator, whole-program recompiler, generalized Capcom
engine, or presentation-first substitute.

Use the smallest verification lane justified by the active card. DEV and BENCH
checks are the ordinary inner loop. Oracle, Full, release Target, normal-release
emulator acceptance, and physical lanes are reserved for the risk boundaries
defined in `docs/TEST_PLAN.md` and `docs/HARDWARE_TEST.md`.

## Repository safety

The repository contains dirty implementation worktrees and private evidence.
Never reset, clean, stash, rebase, broadly restore, force, use `git add -A`, or
run diagnostics that overwrite captures. Stage explicit owned paths only.
Preserve prototype, V2-2B, recovery, ROM, `.deps`, capture, and untracked work.
Never commit ROMs, keys, original disc data, generated copyrighted media, raw
captures, memory dumps, screenshots, ISO/cue files, or private logs.

The final acceptance target remains a normal-release, deterministic physical
Saturn capability slice with controller input, player, class `0x1F` enemy,
movement, animation, collision, damage, HIT/KO, camera/stage, palettes, VDP1,
VDP2, PCM, CDDA, residency, timing, final scanout, and soak evidence. No bench,
host, MAME, emulator, or user-review result substitutes for that gate.
