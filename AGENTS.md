# AvP Saturn port agent instructions

## Authority and target

The authoritative architecture is the title-specific hybrid native port selected in `docs/research/CPS2_TO_SATURN_RESET.md`. The implementation target is only MAME set `avspu`, `Alien vs. Predator (USA 940520)`, clone of `avsp`.

Do not reopen the architecture by inertia. A change to the selected approach requires a bounded falsification result, an evidence-led impact analysis, and supervisor approval. MSHvSF is an isolated research lane; it is never an AvP specification and no finding becomes a general Capcom rule until a second official port confirms it.

## Read order for every session

Read these files completely before acting:

1. `AGENTS.md`
2. `docs/research/CPS2_TO_SATURN_RESET.md`
3. `docs/research/CPS2_TO_SATURN_SOURCE_LEDGER.md`
4. `docs/research/CPS2_TO_SATURN_EVIDENCE_LEDGER.md`
5. `docs/AGENT_HANDOFF.md`
6. `docs/NEXT_AGENT_PROMPT.md`
7. `docs/CODEX_REVIEW_TEMPLATE.md` when preparing or consuming a handoff
8. `docs/TEST_PLAN.md` and `docs/HARDWARE_TEST.md` when verification is in scope

Files under `docs/archive/pre-reset-2026-08-20/` are historical evidence only. They must not be treated as instructions or a plan of record.

## Selected architecture

- Offline extraction and normalization from the exact authorized ROM set.
- Original data retained only as address-traceable sparse spans where that reduces risk.
- Selective lifting of bounded 68000 state writers and behavior routines; no whole-program recompiler.
- Native SH-2 simulation, input, collision, rendering, stage, audio, loading, and telemetry.
- MAME 0.289 as the deterministic semantic oracle.
- VDP1 per emitted 16x16 4bpp tile in a flat ordered command list as the first hardware baseline.
- VDP2 scroll3/scroll2/HUD composition, with line-scroll only where traces require it.
- Fixed phase arenas in the 32 Mbit cartridge; all G0 assets resident before CDDA.
- SCSP PCM for short events and CDDA for long music.
- One master-SH-2 loop initially. Slave SH-2 and composite caches require measured need.

Do not build a CPS-2 emulator, runtime 68000 interpreter, generalized Capcom engine, generalized streamer, dynamic composite cache, or presentation-first roadmap.

## Current execution body

Only execute the bounded tranche in `docs/NEXT_AGENT_PROMPT.md`. Tranche 1's
vertical-slice contract, deterministic MAME oracle, and executable boundary are
accepted at `a11527a18c6ec02d3bc3f3421674755a3102c6c5`. Tranche 2A's strict-host
baseline repair is accepted at `eef350a3de6e44d1648a861ab98215c3d61ce20c`;
the complete host/generator suite is reviewable again. The active body is the
first V2 subtranche: correct the candidate class `0x1F` enemy HIT/KO writer-set
proof so actor identity, writer/routine/edge closure, data/event dependencies,
and every committed relationship are derived and falsifiable rather than
hard-coded. It does not yet emit or integrate production lifted C.

The first accepted slice must contain real gameplay: deterministic startup, controller input, one player, one class `0x1F` enemy, movement, animation, attack/contact, collision/hit/KO, camera/stage movement, representative layers and palettes, PCM, CDDA, residency/transfer, final scanout, and physical timing. Title/menu work cannot substitute for any item.

## Evidence rules

Use these exact labels:

- `PHYSICAL_SATURN`
- `MULTI_EMULATOR`
- `ONE_EMULATOR`
- `MAME_TRACE`
- `STATIC_ANALYSIS`
- `VISUALLY_PLAUSIBLE`
- `PLANNED`
- `IMPLEMENTED_UNEXERCISED`
- `CONTRADICTED`
- `UNKNOWN`

Also preserve `MEASURED`, `ADAPTED`, `GAP`, `UNRUN`, and `MISSING` where existing tools use them. Never promote one evidence tier into another. A screenshot is not semantic parity; an emulator pass is not hardware timing; a static budget is not live high-water.

Every generated artifact must identify set/revision, contributing ROM hashes, address space and offsets, MAME/tool/extractor pin, command parameters, schema version, output hash, consumer lifetime, evidence tier, and exclusions.

## Implementation contract

For every behavioral change:

1. Pin the exact base, inputs, and expected failing evidence.
2. Add or preserve a failing-first test or differential check.
3. Implement the smallest change inside the selected architecture.
4. Run focused tests and a real negative control or mutation.
5. Run the broader safe regression set.
6. Record what is host-, MAME-, emulator-, or hardware-proven.
7. Update the handoff and evidence ledger.

Do not weaken tests, replace missing behavior with a capture, or call an adapted fallback faithful. If a premise fails, stop at its declared probe boundary and return evidence rather than expanding scope.

## Repository and content safety

The worktree may contain unrelated private and untracked evidence. Never use reset, clean, stash, rebase, broad checkout/restore, force operations, `git add -A`, or broad diagnostics that overwrite captures. Stage explicit paths only.

Never commit ROMs, keys, original disc data, generated copyrighted graphics/audio, raw captures, memory dumps, screenshots, ISO/cue files, disassembly bytes, or logs containing them. Committed outputs must be code, schemas, hashes, counts, provenance, tests, and documentation.

Legacy authored behavior, capture-derived holds, RP4 fixtures, and the disabled CDDA path are parked. Remove them only after their replacement passes the same retained regression plus the new semantic oracle. Do not delete recoverability to make the tree look clean.

## Build and verification order

1. Target identity and provenance checks.
2. Focused host unit/differential tests.
3. Complete `test.ps1` in an isolated copy when it would rewrite tracked data.
4. Target build in the implementation worktree.
5. Focused emulator semantic/readback checks.
6. Normal-release rebuild and manifest readback.
7. Physical Saturn timing, scanout, audio, input-latency, and soak.

The shared-primitives check, presentation/stage parity check, and capability slice gate are separate. Only the final integrated physical slice advances capability.

## Handoff

Every implementation handoff must include branch, immutable base and final SHA, commits oldest first, explicit files changed, commands and exit codes, RED/GREEN/negative-control results, build/profile/artifact hashes, evidence tiers, remaining gaps, worktree status, and a ready review invocation. If incomplete, state the exact stop condition that fired.

Use `docs/CODEX_REVIEW_TEMPLATE.md` verbatim as the envelope for every review
request. The implementor never self-accepts or rotates the plan. A valid return
requests the supervisor ruling and the corresponding next
`IMPLEMENTOR_INVOCATION` for acceptance, corrections, or missing evidence.

When a separate Codex implementor task is created, explicitly use model
`gpt-5.6-terra` with reasoning/thinking `xhigh`. Supervisor and review reasoning
levels are separate from this implementor launch policy.

Before creating or resuming that implementor task, the supervisor must verify
the configured destination repository is private, push the reviewed candidate
branch, the supervisor selection/invocation branch, and the new implementation
start branch, and confirm their remote SHAs. The implementation task may begin
write work only after its immutable base is recoverable on that private remote.
Record the remote name, URL, branch, and verified SHA in
`docs/IMPLEMENTOR_INVOCATION.md`. Never push ROMs, `.deps`, raw evidence, or
other ignored/private inputs.
