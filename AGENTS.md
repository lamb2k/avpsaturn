# AvP Saturn port agent policy

## Authority and target

The authoritative architecture is the title-specific hybrid native port in
`docs/research/CPS2_TO_SATURN_RESET.md`. The only implementation target is MAME
set `avspu`, `Alien vs. Predator (USA 940520)`, clone of `avsp`.

Do not reopen that architecture without a bounded falsification result and an
evidence-led impact analysis. MSHvSF is an isolated research lane, never an AvP
specification, and cannot establish a general Capcom rule by itself.

## Start of work

For every task, read completely:

1. `AGENTS.md`;
2. `project_state.yaml`;
3. the task card named by `project_state.yaml` or supplied at launch.

Read `docs/research/CPS2_TO_SATURN_RESET.md` for behavioral, runtime, device, or
architecture work. Read the source/evidence ledgers when changing an evidence
claim or generated artifact. Read `docs/TEST_PLAN.md` for verification and
`docs/HARDWARE_TEST.md` for physical work. Files under
`docs/archive/pre-reset-2026-08-20/` are historical evidence only.

The task card owns the current objective, base, branch, paths, acceptance
criteria, exclusions, and stop condition. `project_state.yaml` owns volatile
project status. Do not duplicate either in durable policy files.

## Selected architecture

- Offline extraction and normalization from the exact authorized ROM set.
- Address-traceable sparse spans for retained original data.
- Selective lifting of bounded 68000 behavior into native C; no runtime
  interpreter or whole-program recompiler.
- Native SH-2 input, simulation, collision, stage, render, audio, loading, and
  telemetry.
- MAME 0.289 as the deterministic semantic oracle.
- A flat VDP1 command list with one 16x16 4bpp tile per command as the first
  hardware baseline.
- VDP2 scroll3/scroll2/HUD composition, with line scroll only where measured.
- Fixed phase arenas in the 32 Mbit cartridge; G0 resident before CDDA.
- SCSP PCM for short events and CDDA for long music.
- One master-SH-2 loop until profiling justifies more.

Do not build a generalized CPS-2 emulator, Capcom engine, streamer, dynamic
composite cache, or presentation-first roadmap.

## Implementation contract

For behavioral work:

1. Pin the exact base, inputs, and expected failing evidence.
2. Add or preserve a failing-first test or differential fixture.
3. Implement the smallest change inside the selected architecture.
4. Run the focused check and a real mutation or negative control.
5. Run the broader lane required by the task risk.
6. Record precisely what is host-, MAME-, emulator-, or hardware-proven.

Keep all corrections for one substantive checkpoint on its existing branch and
worktree. A review creates one consolidated blocking list; one re-review is the
default. Start a fresh branch only for a genuinely new checkpoint. Do not
commit launch prompts or reviewer invocations. Use
`tools/start-agent-task.ps1` to create ignored launch metadata and
`tools/New-ReviewBundle.ps1` to create the ignored review bundle.

Codex Goal Mode is the only reasoning and orchestration layer. Repository
scripts do not interpret review findings, select roadmap work, make
architecture decisions, or run autonomous retry loops. Use
`tools/Invoke-TaskExecutor.ps1` for exactly one explicitly active
implementation, correction, or evidence-repair invocation. It may invoke the
card-authorized Codex or Claude provider, run every required lane, and generate
a candidate-bound bundle; Goal Mode decides whether any further invocation is
warranted.

To start the explicitly active task, first inspect a no-execution plan, then
run the same command without `-PlanOnly`:

```powershell
.\tools\Invoke-TaskExecutor.ps1 -Task <active-card-id> -Executor Auto -PlanOnly
.\tools\Invoke-TaskExecutor.ps1 -Task <active-card-id> -Executor Auto
```

`Auto` follows the active card's `PREFERRED_EXECUTOR`. A card declaring
`PREFERRED_EXECUTOR: CLAUDE` and `CLAUDE_MODEL: fable` therefore launches one
local Fable implementation turn. Codex Goal Mode still owns review,
acceptance, state promotion, and selection of any later task.

After Goal Mode obtains independent external review results, use
`tools/Apply-ReviewDisposition.ps1` to validate their hashes, candidate binding,
three required roles, and conservative verdict. The script may apply only the
predeclared mechanical transition. It never launches reviewers, chooses an
unlisted next card, commits, pushes, or begins the next task. An accepted
candidate must already be integrated into the controller HEAD before promotion.

## Evidence rules

Use the existing vocabulary exactly: `PHYSICAL_SATURN`, `MULTI_EMULATOR`,
`ONE_EMULATOR`, `MAME_TRACE`, `STATIC_ANALYSIS`, `VISUALLY_PLAUSIBLE`,
`PLANNED`, `IMPLEMENTED_UNEXERCISED`, `CONTRADICTED`, `UNKNOWN`, plus
`MEASURED`, `ADAPTED`, `GAP`, `UNRUN`, and `MISSING` where already used.

Never promote evidence tiers. A screenshot is not semantic parity, an emulator
pass is not hardware timing, and a static budget is not live high-water.
Generated evidence must carry target/revision, contributing ROM hashes, address
space and offsets, tool/extractor identity, command parameters, schema, output
hash, consumer lifetime, evidence tier, and exclusions.

## Verification lanes

Use `verify.ps1`:

- `Fast`: direct unit tests, focused differential fixtures, strict portable C,
  and no private capture regeneration.
- `Oracle`: MAME provenance, deterministic artifacts, boundary/writer-map
  validators, and mutation controls.
- `Target`: explicit build-only iteration, or an exact
  `release-normal-release` build plus profile-specific emulator semantic,
  resource, render, and final-scanout checks for Saturn-facing acceptance.
- `Full`: the complete legacy and generated regression in `test.ps1`.

Run `Fast` during iteration. Add `Oracle` for evidence or lifted-behavior work,
the release `Target` with emulator readback when Saturn-facing code changes,
and `Full` at acceptance, before merge, or after foundational tooling changes.
A Target launch or build alone is not an acceptance pass. Physical validation
remains a separate gate under `docs/HARDWARE_TEST.md`.

## Review tiers

- **Tier 0 - mechanical:** documentation, a settled declaration, formatting,
  or a deterministic hash refresh with no semantic change. Automated checks
  and path-scope review are sufficient unless an evidence claim changes.
- **Tier 1 - translated behavior:** native routines, state transitions,
  collision, animation, or bounded SH-2 features. One high-reasoning read-only
  review blocks only on semantic mismatch, missing dependency, nondeterminism,
  unsafe scope, unsupported behavior, or an unproved evidence claim.
- **Tier 2 - trust boundary:** oracle, translation/writer boundary, evidence
  schema/validator, memory architecture, VDP ownership, audio residency,
  physical timing, or material architecture change. Review semantic closure,
  validator/provenance integrity, and Saturn constraints independently, then
  consolidate all blockers once.

The first Tier 2 pass must exercise, where applicable: provenance mutation
with recomputed integrity; missing/reordered/promoted evidence tiers;
opcode/program reversal; unknown or raw-like schema fields; reduced PC, edge,
routine, caller/callee, or computed-target closure; changed event frame/writer
PC; missing actor field/observation; boundary completeness reduction; and the
declared Saturn resource/timing claim.

Every review returns only:

```text
VERDICT: ACCEPTED | CORRECTIONS REQUIRED | NOT REVIEWABLE
BLOCKING:
NONBLOCKING:
EVIDENCE:
NEXT ACTION:
```

The reviewer does not author the next implementation architecture. The current
task card stays active for corrections; after acceptance, update
`project_state.yaml` and activate the next dependency-ready card.

## Repository and content safety

The repository may contain unrelated private and untracked evidence. Never use
reset, clean, stash, rebase, broad checkout/restore, force operations,
`git add -A`, or diagnostics that overwrite captures. Stage explicit paths.

Never commit ROMs, keys, original disc data, generated copyrighted
graphics/audio, raw captures, memory dumps, screenshots, ISO/cue files,
disassembly bytes, or logs containing them. Preserve legacy fallbacks and
fixtures until their replacements pass retained regression plus the semantic
oracle; do not delete recoverability for cosmetic cleanup.

The first accepted capability slice still requires deterministic gameplay,
input, one player, one class `0x1F` enemy, movement, animation, contact/HIT/KO,
camera/stage, layers/palettes, PCM, CDDA, residency/transfer, final scanout, and
physical timing. No host, mapping, presentation, or emulator result substitutes
for that integrated physical gate.
