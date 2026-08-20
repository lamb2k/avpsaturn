# IMPLEMENTOR_INVOCATION — RP4 deterministic VDP1 command order

Compatible alias: `CLAUDE_INVOCATION`. This exact prompt may be given to
Claude or to a separately invoked Codex model.

## Assignment identity

```text
MODE: DIRECTED_BOOK_IMPLEMENTATION
IMPLEMENTOR: Claude or a separately invoked Codex model
ROLE_LOCK: IMPLEMENTOR_ONLY
SUPERVISOR_AND_ACCEPTANCE_AUTHORITY: Codex
REPOSITORY: C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest
SUPERVISOR_WORKTREE: C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest-ClaudePriorityArchitecture
IMPLEMENTATION_WORKTREE: C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest-Rp4DirectOrder
IMPLEMENTATION_BRANCH: codex/rp4-direct-command-order
BASE_SHA: 3903cc303f51cc0cc5bcaf0889c50f24be061a6b
SCOPE: RP4 deterministic final VDP1 command order only
```

Regardless of model vendor, you are the implementor session, not the
supervisor session. Do not issue `ACCEPTED`, `CORRECTIONS REQUIRED`, or
`NOT REVIEWABLE`; do not select or draft the next tranche; do not rewrite the
master architecture. Execute this bounded book and return its evidence package
to the separate Codex supervisor session. A Codex implementor must not
self-review merely because it is a Codex model.

Create the implementation worktree and branch from exactly `BASE_SHA`. Do not
modify the primary repository or the supervisor worktree. Do not reuse a dirty
worktree. If the named worktree or branch already exists, verify its base and
ownership; stop only if it cannot be isolated without touching user work.

Use the `port-cps2-to-sega-saturn` skill. Read completely, in order:

1. `AGENTS.md`;
2. `docs/GOAL.md`;
3. `docs/AGENT_HANDOFF.md`;
4. `docs/PARITY_PLAN.md`;
5. `docs/ROUND1_EXECUTION_PLAN.md`;
6. `docs/ARCHITECTURE.md`;
7. `docs/TEST_PLAN.md`;
8. `docs/HARDWARE_TEST.md`;
9. this file.

Then run:

```powershell
git status --short --branch
git log --oneline -10
git rev-parse HEAD
Get-Process mame,yabasanshiro* -ErrorAction SilentlyContinue
```

Require a clean worktree at the exact base and no emulator process. Preserve
all ignored private evidence. Never reset, clean, stash, bulk-stage, or commit
ROMs, captures, screenshots, generated graphics/audio, ISO/CUE/ELF files,
emulator state, logs, or raw command tables.

## Architectural question

Can StreetTest bypass SGL's measured equal-Z sorter through the existing
immediate `slPutSprite` path and preserve the required CPS2 object order in the
Saturn's final sequential VDP1 command list without changing sprite geometry,
palette, pixel data, command count or other runtime paths?

If not, can a narrowly owned sequential VDP1 emission seam coexist with Jo/SGL
without corrupting its command table or exceeding the current memory budget?

## Settled evidence — do not re-derive

- AvP's source ordering contract is measured from MAME/ROM. For the relevant
  same-priority street population, the earlier CPS2 object-RAM entry wins.
- VDP1 final command memory is readable and its link-mode-zero sequence is the
  actual VDP1 draw order.
- Existing reverse versus forward equal-Z `slDispSprite` builds emitted 528
  commands with 510 comparable sprites at identical final indices:
  129,795/129,795 order-preserving pairs. Only texture addresses moved.
  Reversing caller submission therefore does not control that output path.
- Nineteen source overlap witnesses exist; fourteen map to StreetTest. Use the
  witness with `streettest_rel=0`, source coordinate `(39,184)` first, then all
  uniquely joinable StreetTest witnesses.
- `jo_sprite_draw3D` reaches sorted `slDispSprite`.
  `jo_sprite_draw(..., billboard=true, screen_doors=true)` reaches immediate
  `slPutSprite`. This call-path inspection selects the first candidate; it is
  not proof that the candidate preserves order.
- The earlier Codex candidate build is ignored evidence only. Its attempted
  emulator runs never reached readiness and produced no command capture, so it
  is `UNRUN`, not a failed candidate. Exact hashes and CPU state are in the
  newest handoff section.
- Object-versus-plane and priority-register composite controls remain blocked.
  This book may pass the final-command-order control only; it may not promote
  those controls, RP4 v1 as a whole, Capability Gate 1 or physical hardware.
- MSHvSF and the optional Yaba source patch are corroborating references only.
  Do not resume emulator-source archaeology or use MSHvSF as AvP acceptance.

## Hypotheses and predetermined decision table

| Result | Required evidence | Continue immediately with |
|---|---|---|
| A — immediate path works | Final VDP1 order follows the reversed CPS2 group order; every usable witness has the earlier CPS entry later in the final list; command count and full content/geometry/palette multiset equal the sorted baseline | Keep a project-owned wrapper around `slPutSprite`, retain a sorted negative-control build flag, integrate it only into the RP4 StreetTest/object schedule, then complete Chapters 3-5 |
| B — immediate path controls order but changes another invariant | Order changes, but command count, texture content, position, size, PMOD, colour, flips or runtime behavior differs | Diagnose the exact invariant. If one bounded setup correction makes every invariant exact, apply it and continue as A. Otherwise implement Chapter 4 |
| C — immediate path does not control final order | Reverse/forward immediate builds still have the same final joined group order | Implement Chapter 4 |
| D — neither seam can coexist safely | The raw seam collides with SGL ownership, requires an unbounded renderer rewrite, crosses a measured memory limit or cannot preserve command/content invariants | Architectural hard stop. Commit only tests, instruments and evidence, and report the exact ownership or memory contradiction |
| E — acceptance instrument unavailable | After the bounded launch recovery, unchanged base cannot reach a readable advancing StreetTest while prior evidence remains intact | `NOT REVIEWABLE` hard stop. Commit only reproducible launch diagnostics; do not judge either candidate |

Do not hand back after proving A, B or C. Continue into its prescribed
implementation and verification chapters. Ordinary compiler, linker, emulator
or runtime failures are debugging work, not hard stops.

## Chapter 0 — prove the unchanged boot/capture control first

Do not rebuild a candidate until this chapter is green.

1. From the clean base, build exactly:

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\build.ps1 `
     -Clean -StreetTest -SkipHostTests
   ```

2. Record SHA-256 for `game.iso`, `game.elf`, `game.cue`,
   `stage1_audio.wav`, `build/rp4_fixture/STRIPS.BIN`, and the pinned
   `yabasanshiro.exe`. Verify the cue points to those exact artifacts.
3. Add or repair one focused launcher/capture helper instead of repeating an
   ad-hoc `Start-Process` line. It must quote space-containing paths, record the
   actual process command line and PID, wait in stages, and kill only its PID.
   It must never rely on Yaba's recent-disc state.
4. Readiness requires all of: `avsp_diag_runtime_ready == 1`,
   `avsp_diag_street_objects > 0`, and an advancing
   `avsp_diag_street_frame`. Distinguish no guest, loaded pre-init guest,
   initialized no-renderer, and live fixture. Record master/slave PC/registers
   on failure.
5. Bounded recovery sequence:
   - attempt 1: exact clean build and absolute-path cue;
   - attempt 2: verify ISO members/hashes, command line, cartridge and current
     Yaba configuration hash; relaunch from a freshly staged cue;
   - attempt 3: compare process/PC/diagnostics with committed known-good
     provenance and correct only a proven launcher/config divergence.
   Each attempt is bounded at 600 seconds. Do not retry unchanged state.
6. Negative control: launch the same emulator through an intentionally invalid
   or absent ignored cue and require it cannot satisfy readiness. Reject a
   stale process, stale ISO hash, wrong ELF symbols, wrong fixture period and a
   capture before the first completed render.

Write failing-first tests for the quoting, stale-artifact and readiness defects
before changing the helper. If unchanged base still cannot boot after the
three bounded attempts, take result E and stop before renderer changes.

## Chapter 1 — strengthen the evidence instrument, RED first

The committed RED is the measured inert sorted path. Preserve it.

1. Extend the ignored command capture so every normal-sprite command records a
   SHA-256 of referenced VDP1 texture bytes. Derive byte count from CMDSIZE and
   4bpp mode; reject unsupported command/mode combinations instead of guessing.
2. Compare command identity with at least command kind, PMOD, CMDCOLR, size,
   XA, YA, flip bits and texture-content hash. Do not use `srca` as identity
   because residency order may move it.
3. Decode emitted object/tile groups from `STRIPS.BIN` and `TILES.BIN`, then
   join them to final commands by complete identity. Report ambiguous counts.
   A witness is usable only when both source entries join uniquely to final
   command ranges.
4. Add failing tests before implementation for:
   - the current sorted reverse/forward pair being inert;
   - a mutated texture byte;
   - one changed coordinate;
   - one changed CMDCOLR/palette selector;
   - one dropped or duplicated command;
   - one swapped source group;
   - stale capture, fixture, ELF or ISO hashes;
   - a build compared against itself;
   - attempted promotion of either composite-only control.
5. The tracked manifest contains hashes, counts, indices, fractions and labels
   only. Raw command and texture data stay ignored.

## Chapter 2 — measure the preferred immediate path

Add a narrowly named diagnostic switch such as `-Rp4SortedSprites`; the normal
candidate uses the immediate path and the switch restores the old sorted path.
Keep the seam within the RP4 StreetTest/object renderer. Preserve current
palette and flip setup/teardown.

Build and capture at the same clean base and fixture frame:

1. old sorted reverse control;
2. old sorted forward control, reproducing the committed inert result;
3. immediate reverse candidate;
4. immediate forward negative control.

For result A, require:

- valid, sequential, terminated final list;
- unchanged command count;
- complete command-identity multiset equal to sorted baseline;
- reverse versus forward changes group order in the predicted direction;
- every uniquely joined StreetTest witness places the earlier CPS2 entry later
  in final VDP1 order;
- sorted reverse/forward remains inert;
- no tile, palette, object, allocator, late-read or command-overflow regression;
- `__bend` and checked sprite arrays remain below `0x060C0000`.

If all hold, continue with A. Otherwise follow B or C without asking the user
or returning an investigation-only report.

## Chapter 3 — integrate result A

Move the passing seam into a small project-owned RP4 emitter interface.
Document it honestly as an **immediate unsorted SGL submission seam**, not a raw
hardware renderer. Own attribute setup, draw and flip cleanup so later code
cannot mix sorted and immediate submissions within one schedule.

Retain sorted mode only as a diagnostic negative control. Do not apply the seam
globally to unrelated Jo sprites. Do not alter frontend, combat, AI, collision,
audio or stage logic.

## Chapter 4 — bounded raw seam for B/C only

Enter only if the immediate path is falsified or cannot preserve an invariant
after one bounded correction.

1. Inspect exact Jo/SGL command-table ownership and frame finalization. Reuse
   existing VDP1 VRAM reservations and system/user-clip/local-coordinate
   commands; do not create an overlapping second table.
2. Add the smallest project-owned sequential normal-sprite emitter into a
   reserved contiguous range with link mode 0 and one valid handoff/terminator.
3. Preserve PMOD, CMDCOLR, size, coordinates, flips and texture content. Do not
   introduce arbitrary Z separation.
4. Prove table bounds, command headroom, no Jo/system overlap and stable
   finalization with canaries and a deliberate overflow negative control.
5. Run the same four-build, identity and witness proof from Chapter 2.

If coexistence needs an unbounded Jo/VDP1 redesign or crosses a measured limit,
take D. Never compensate with `JO_DEBUG=0`, Release-only behavior, reduced
malloc, dropped commands or approximate order.

## Chapter 5 — status, regressions and commits

Allow `command_order` to pass from explicit
`evidence_kind=final_vdp1_command_sequence` only when the full identity,
unique-witness direction and negative-control contract passes. This must not
make zero or unreadable witness pixels pass. Leave
`cmdcolr_priority_selector` and `sprite_priority_register_effect` blocked.
RP4 v1 therefore remains FALSIFIED even if this sub-control becomes MEASURED.

Run, in order:

1. launcher/readiness tests and invalid-disc control;
2. command verifier tests and every mutation control;
3. deterministic regeneration twice with byte-identical tracked manifests;
4. focused StreetTest build/capture for all four variants;
5. full `test.ps1`; it may stop only at the documented remaining RP4 composite
   condition after all earlier checks pass;
6. focused StreetTest build plus map and ISO-member hash checks;
7. EncounterTest through `COMPLETE`, checking allocation, late-read,
   tile/palette/object, collision and audio counters;
8. clean normal-release title boot with exact staged cue;
9. verify no MAME, Yaba or compiler process remains.

Commit coherent checkpoints, at minimum:

1. launch/capture instrument and RED tests;
2. evidence-supported emitter and focused GREEN proof;
3. status/manifest integration, regression results and handoff.

Stage explicit paths only. Do not commit with failing focused tests; the sole
exception is a clean architectural-hard-stop evidence checkpoint with no
half-integrated renderer.

## Scope exclusions

- No RP8 frontend expansion.
- No MSHvSF implementation or AvP acceptance dependency.
- No Yaba source/scanout archaeology.
- No CPS2/MAME recapture unless an evidence hash is corrupt or missing.
- No AI, collision, stage, traversal, audio-content or actor-cast widening.
- No Capability Gate progress, hardware-ready claim or publication.

## Required report to Codex

Return one `CODEX_REVIEW_INVOCATION` containing:

- repository, implementation worktree, branch, exact base and candidate HEAD;
- commits oldest first and owned files;
- decision-table result and distinguishing evidence;
- RED command/result and every negative-control result;
- exact build, fixture, emulator, capture and manifest hashes;
- uniquely joined witness counts and order direction;
- command count, identity multiset, ambiguous/excluded counts and table canaries;
- focused, full-suite, EncounterTest and normal-boot exits;
- memory/map headroom and live diagnostic counters;
- all remaining `ADAPTED`, `GAP`, blocked controls and unrun hardware checks;
- clean/dirty status and process cleanup;
- every divergence from this book, without self-acceptance.

Do not draft the next body. Codex owns disposition, canonical-plan updates and
the next assignment.
