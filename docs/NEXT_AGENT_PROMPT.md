# Tranche 2B / V2A: close the class 0x1F HIT/KO writer set

## Role and immutable base

Act as the write-enabled implementation owner for one bounded V2 investigation
and tooling tranche. Use the exact immutable supervisor selection SHA supplied
by `docs/IMPLEMENTOR_INVOCATION.md`. Create the named implementation branch in
the named separate worktree; do not implement in the supervisor worktree.

Read `AGENTS.md`, all three active
`docs/research/CPS2_TO_SATURN_*.md` files, `docs/AGENT_HANDOFF.md`,
`docs/PARITY_PLAN.md`, `docs/TEST_PLAN.md`, this file, and
`docs/CODEX_REVIEW_TEMPLATE.md` completely. Historical pre-reset files and the
MSHvSF lane are evidence only.

## Objective and plan position

Produce a deterministic, provenance-rich executable writer/routine manifest
for the class `0x1F`, type `0x0C` enemy HIT-to-KO interval in the accepted
`avspu` vertical slice. Identify the exact executed PCs and call/data/event
dependencies that own enemy state/substate/action/animation/timer/health/hit
changes, including the currently documented `GAP_EXTERNAL_REPOINT` HIT and KO
animation-pointer writers.

This is the first V2 body. It closes the lift contract before production code
is emitted. Do not generate, hand-write, or integrate lifted gameplay C; do not
modify `capability_model.*`, `main.c`, Saturn build/runtime/package paths, the
accepted oracle, or the accepted translation-boundary artifact.

## Settled inputs

- Target: only `avspu`, USA 940520, MAME 0.289.
- Accepted Tranche 2A HEAD:
  `eef350a3de6e44d1648a861ab98215c3d61ce20c`.
- Contract Git-blob SHA-256:
  `74016fb2e73c2ae00144fa062662b37e0f575a3ee3ff3b7a420b1ed0f55a4638`.
- Oracle manifest Git-blob SHA-256:
  `106fffb92cc5a14acf5fdae7eb14d33b7d9206b9f9ecffcbac67a6fc326696d2`.
- Cold-run semantic ledger SHA-256:
  `f6e813169a05388ce265d6406382efaa1801fe8c838beb0fdab03bda7725d1a1`.
- Translation-boundary Git-blob SHA-256:
  `95e002b7f6d48e8aafbe5e201a370b6dc7c3c5559e7d2253901d0473c0c7b0f4`.
- Private opcode-trace SHA-256:
  `9bbbc28715668348aeb4d206b7381073123c5b22ec9e2f2557bda1622e142f5f`.
- Opcode image SHA-256:
  `e423127bc04889161657032fcb40a8a8f871f4d4f08bd99726e3babdf6e81501`.
- Program/data image SHA-256:
  `0c14f4094d25787401aa949657620ff495ae8606c1cfd8ae2d059b94c3d478e9`.
- Source window: frames 4080-5469 inclusive, 1,390 semantic frames and
  1,389 interrupt boundaries. HIT begins at 5191; KO begins at 5330 and the
  accepted window ends at 5469.
- Accepted boundary: 7,314 executed PCs, 8,222 executed edges, 126/126
  computed sites resolved, 275 observed computed targets, zero unresolved
  targets, zero instruction-space violations, and opcode/program separation
  over all 7,314 PCs.

Git text checkout may use CRLF. Validate canonical committed JSON through Git
blobs or a LF-normalized isolated copy; never rewrite accepted artifacts merely
to remove an autocrlf status flag.

## Authoritative mapping architecture

Create `tools/map_avsp_hit_ko_writer_set.py`, its focused production validator,
and a committed `data/avsp_hit_ko_writer_set.json` manifest. Reuse parsing and
validation concepts from `tools/map_avsp_translation_boundary.py`, but do not
weaken or mutate that accepted tool/artifact.

The new tool must:

1. Verify every settled input identity before analysis.
2. Segment the private trace into exactly 1,390 ordered source-frame epochs
   using the 1,389 accepted interrupt boundaries. Reject off-by-one alignment.
3. Parse instruction operands only in memory. Determine reads versus writes
   conservatively from the actual 68000 destination effective address and
   width; a mere actor-field reference is not a writer.
4. Correlate the class `0x1F`, type `0x0C` enemy semantic changes in frames
   5191-5469 to executed writer sites in the same source-frame epoch. Record
   field names and before/after semantic values, never raw trace lines,
   disassembly text, or opcode bytes.
5. Group selected PCs into deterministic call-rooted routine units using the
   accepted dynamic edges. Preserve entry PC, member-PC count/hash, observed
   callers/callees, actor-field reads/writes, ROM-data reads, work-RAM
   references, and typed hardware/event exits.
6. Close transitively from every correlated HIT/KO writer through executed
   calls and computed targets until each dependency is one of: a selected
   routine, a declared immutable program/data span, a typed semantic event
   replacement, or an explicitly excluded out-of-window route. An exclusion
   cannot contain an in-window actor-field writer.
7. Prove every selected PC and edge exists in the accepted boundary; every
   code target uses the opcode image; every ROM-data operand uses the program
   image; all selected computed targets are resolved; and selected
   dependencies have zero `unresolved` and zero `unattributed` entries.
8. Identify at least one exact executed `anim_record` writer for the HIT
   interval and at least one for the KO interval, or stop at the declared
   falsification boundary. The manifest must say whether these close
   `GAP_EXTERNAL_REPOINT`; prose alone cannot close it.
9. Generate byte-identical JSON twice from identical inputs and provide a
   production `validate_committed` path that revalidates the real committed
   artifact without private raw bytes.

The manifest may contain hashes, counts, PCs/ranges, routine entry addresses,
field names, semantic values, address-space classifications, event classes,
and exclusions. It must not contain ROM bytes, opcode words, disassembly,
trace text, screenshots, state dumps, or copyrighted asset data.

## Bounded investigation decision table

Follow this table in order. Do not choose a broader body merely because it is
easier to map.

| Candidate | Required evidence | Decision |
|---|---|---|
| A. Class `0x1F` enemy HIT/KO repoints, frames 5191-5469 | Both HIT and KO `anim_record` changes correlate to exact writer PCs; state/action/health dependencies close; zero unresolved/unattributed selected dependencies | **Selected and preferred. Complete this tranche.** |
| B. Enemy HIT only | HIT writer closes but KO cannot be disambiguated after three materially different in-scope correlation/closure approaches | Stop with falsification evidence; do not silently downgrade acceptance or select B as success. |
| C. Player input/attack writers | Candidate A is falsified because the accepted trace lacks a closed enemy repoint path, while player writers remain bounded | Report only as a supervisor decision option. Do not implement C in this tranche. |
| D. Camera/stage or broad 7,314-PC lift | Any pressure to widen beyond the HIT/KO writer closure | Reject as out of scope. |

Three materially different in-scope disambiguation approaches are: same-epoch
destination-writer correlation, dynamic call-context closure, and semantic
before/after plus program-data pointer validation. Exhaust all three before
declaring the selected premise falsified.

## Owned paths

- `tools/map_avsp_hit_ko_writer_set.py` (new)
- `tests/test_avsp_hit_ko_writer_set.py` (new)
- `data/avsp_hit_ko_writer_set.json` (new, bounded metadata only)
- `docs/AGENT_HANDOFF.md` (final evidence only)
- `docs/research/CPS2_TO_SATURN_EVIDENCE_LEDGER.md` (final evidence only)

Everything else is shared or forbidden. In particular, do not modify
`tools/map_avsp_translation_boundary.py`, any accepted contract/oracle/boundary
JSON, production C/H, build scripts, generated runtime headers, `.deps`, ROM
directories, package manifests, or archived plans.

## Chapter 1 - RED contract and real artifact test

Add `tests/test_avsp_hit_ko_writer_set.py` first and commit it separately. The
test must invoke the production validator and require, at minimum:

- all settled identities and exact source-frame anchors;
- 1,390 epochs / 1,389 interrupt boundaries;
- non-empty selected routines, PCs, and edges;
- both HIT and KO exact `anim_record` writer ownership;
- coverage of enemy state/action/animation/timer/health/hit dependencies that
  actually change in the accepted semantic interval;
- every selected PC/edge contained in the accepted translation boundary;
- zero unresolved computed targets and zero unattributed dependencies;
- explicit opcode versus program/data attribution;
- no forbidden raw fields or text.

RED must fail because the production mapper/committed artifact does not yet
exist or lacks the required closure. Record the exact command and exit. A test
that only checks literal JSON values is not acceptable.

## Chapter 2 - GREEN mapper and closure

Implement the smallest mapper/validator that satisfies the authoritative
mapping architecture. Prefer reusable pure parsing/closure functions and a
streaming trace pass; do not retain the raw trace in memory or output.

Required commands:

```powershell
python tools/map_avsp_hit_ko_writer_set.py --self-test
python tools/map_avsp_hit_ko_writer_set.py --generate
python tests/test_avsp_hit_ko_writer_set.py
```

GREEN requires all commands to exit 0 and the generated manifest to pass its
own production validator. Record selected routine/PC/edge counts, exact HIT
and KO writer PCs, field coverage, computed-target count, event exits, and the
output Git-blob SHA-256.

REFACTOR only to remove duplicated parsing or make closure auditable. Do not
generalize into a 68000 recompiler or a multi-title framework.

## Chapter 3 - genuine mutation controls

Both the self-test and the focused committed-artifact test must deep-copy a
valid report and call the production validator. At minimum, each of these
independent mutations must fail for its intended invariant:

1. remove one correlated HIT `anim_record` writer PC;
2. remove one correlated KO `anim_record` writer PC;
3. remove one selected dynamic call/control edge;
4. insert an unresolved selected computed target;
5. change one selected PC to a PC absent from the accepted boundary;
6. relabel one ROM-data dependency as opcode/instruction data;
7. remove one required actor-field attribution;
8. shift HIT or KO source-frame alignment by one;
9. add a forbidden raw/disassembly/trace-text field.

Also run one end-to-end scratch mutation against private input correlation:
alter one semantic HIT/KO before/after value or remove one same-epoch writer in
an isolated copy and require generation/validation to fail. Never mutate the
canonical raw evidence.

## Chapter 4 - determinism and cumulative regression

Generate the new manifest twice from identical inputs and require identical
bytes and SHA-256. Then run, in order:

```powershell
python tests/test_avsp_hit_ko_writer_set.py
python tests/test_avsp_vertical_slice_oracle.py
python tests/test_avsp_translation_boundary.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\test.ps1
git diff --check
```

Run `test.ps1` only in the assigned clean worktree after provisioning its known
git-ignored private/generated prerequisites, or in an isolated copy. Inspect
every regenerated tracked diff. The accepted contract, oracle, boundary, and
all pre-existing data artifacts must remain byte-identical; environment-path
or capture-snapshot drift is evidence to report, not material to commit.

## Evidence limits

This tranche may produce `MAME_TRACE`, `STATIC_ANALYSIS`, and `MEASURED` host
evidence only. It cannot close host behavioral zero-diff, Saturn target,
emulator, release, audio, physical timing, memory, VDP1/VDP2/CRAM/SCSP/CDDA, or
Capability Gate conditions. `GAP_EXTERNAL_REPOINT` closes only as writer
ownership/mapping; behavioral equivalence remains open until the later host
lift passes frame-by-frame differential tests.

## Commit sequence

1. RED focused contract test.
2. GREEN mapper, validator, and deterministic committed manifest.
3. Evidence/handoff after all allowed checks.

Stage explicit paths only. Do not amend, rebase, merge, cherry-pick,
broad-stage, clean, reset, or commit private/generated material.

## Hard stops

Stop and return exact evidence when:

- any settled input identity differs;
- trace epoch segmentation is not exactly 1,390/1,389 or cannot be aligned to
  the accepted source frames;
- either HIT or KO `anim_record` writer cannot be identified after all three
  bounded disambiguation approaches;
- a selected computed target remains unresolved;
- an in-window actor writer can only be hidden in an exclusion;
- selected closure requires more than 50% behavior re-authoring/manual
  semantics or expands materially beyond the class `0x1F` HIT/KO path;
- accepted artifacts would need to change;
- private evidence is absent, new authority is required, or worktree safety
  cannot be preserved.

Do not convert a hard stop into a partial pass or a broader implementation.

## Required final report

Return branch, immutable base, final SHA, commits oldest first, exact files,
RED/GREEN/refactor commands and exits, all nine committed-artifact controls,
the end-to-end scratch mutation, manifest hash/counts/entry PCs, deterministic
two-generation result, cumulative regression, evidence tiers, exclusions,
remaining gaps, and final worktree status.

End with the complete filled `CODEX_REVIEW_INVOCATION` copied from
`docs/CODEX_REVIEW_TEMPLATE.md`. Request the supervisor disposition and the
corresponding next `IMPLEMENTOR_INVOCATION`. Do not self-accept, emit production
lifted C, rotate the plan, or select the next tranche.
