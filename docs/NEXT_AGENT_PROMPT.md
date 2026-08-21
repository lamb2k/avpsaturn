# Tranche 2A: restore the strict host-suite baseline before V2

## Role and immutable base

Act as the write-enabled implementation owner for one bounded runtime-
maintenance tranche. Use the exact immutable supervisor selection SHA supplied
by the launch invocation. Create branch `codex/avp-host-baseline-tranche-2a` in
the separate worktree named by that invocation.

Read `AGENTS.md`, the three active `docs/research/CPS2_TO_SATURN_*.md` files,
`docs/AGENT_HANDOFF.md`, `docs/PARITY_PLAN.md`, `docs/TEST_PLAN.md`, this file,
and `docs/CODEX_REVIEW_TEMPLATE.md` completely. Historical pre-reset files are
evidence only.

## Objective and plan position

Restore the strict C90 host-suite baseline by adding the two declarations that
the existing frontend state machine already consumes, prove the exact 30-frame
boundary with non-vacuous tests, and run the complete host/generator regression.

This is the authorized maintenance gate between accepted Tranche 1 and V2. It
does not lift 68000 behavior, alter the oracle/boundary, build a general
translator, or advance Capability Gate 0/12.

## Settled facts

- Accepted Tranche 1 HEAD is
  `a11527a18c6ec02d3bc3f3421674755a3102c6c5`.
- `capability_model.c` already enters `CAP_ENCOUNTER_START_TRANSITION`, advances
  its timer, and leaves it at `CAP_START_TRANSITION_FRAMES`.
- `main.c` and the generated frontend contract already consume the same state
  and duration.
- The clean accepted line fails strict compilation only because
  `capability_model.h` lacks the enum member and duration macro.
- Source frames 1689-1718 establish a 30-frame transition.
- Historical sibling commit
  `c7e8f80a54725977a5e61486bb9960f37f1680b7` contains the intended declarations
  and boundary test, but also unrelated loader/build/generator work. It is
  read-only evidence. Do not cherry-pick it or copy its unrelated changes.
- Tranche 1 oracle ledger
  `f6e813169a05388ce265d6406382efaa1801fe8c838beb0fdab03bda7725d1a1`
  and boundary artifact
  `95e002b7f6d48e8aafbe5e201a370b6dc7c3c5559e7d2253901d0473c0c7b0f4`
  must not change.

## Preferred repair

1. Insert `CAP_ENCOUNTER_START_TRANSITION` immediately after
   `CAP_ENCOUNTER_MAIN_MENU` in `CapEncounterState`.
2. Define `CAP_START_TRANSITION_FRAMES` as exactly `30` beside the frontend
   selection timing constants, with the measured source-frame provenance.
3. Strengthen `tests/capability_model_test.c` so the literal value `30` and the
   actual state/timer boundary are independently pinned. Do not derive all
   expected timing only from the macro under test.
4. Update the shared `start_encounter` test helper to traverse the transition
   before character selection.

Do not modify `capability_model.c`; the existing state-machine behavior is the
contract being made compilable and testable.

## Owned paths

- `capability_model.h`
- `tests/capability_model_test.c`
- `docs/AGENT_HANDOFF.md` for final evidence only
- `docs/research/CPS2_TO_SATURN_EVIDENCE_LEDGER.md` for final evidence only

Everything else is shared or forbidden. `test.ps1` is a runner, not an owned
implementation path. Generated outputs may be regenerated for verification but
must remain byte-identical unless the tranche stops and reports the exact drift.

## Chapter 1 — failing-first compile and exact-boundary contract

RED:

```powershell
$linuxRoot = (& wsl.exe wslpath '-a' $PWD.Path).Trim()
wsl.exe sh -lc "cd '$linuxRoot' && gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 -fsyntax-only capability_model.c tests/capability_model_test.c"
```

Expected base failure: undefined `CAP_ENCOUNTER_START_TRANSITION` and
`CAP_START_TRANSITION_FRAMES` at `capability_model.c:961,967`.

Before fixing the header, add failing-first assertions that require:

- Start input changes MAIN_MENU to START_TRANSITION with timer zero.
- The constant equals literal `30`.
- After 29 no-input steps the state is still START_TRANSITION and timer is 29.
- The next step changes to CHARACTER_SELECT and resets the timer to zero.
- The common test helper traverses this same boundary before confirming a
  character.

Commit the RED test separately. If the compile failure differs from the two
settled missing declarations, stop and report it.

## Chapter 2 — minimal declaration repair

GREEN: make only the two preferred header declarations. Then run:

```powershell
$linuxRoot = (& wsl.exe wslpath '-a' $PWD.Path).Trim()
wsl.exe sh -lc "cd '$linuxRoot' && mkdir -p build && gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 capability_model.c tests/capability_model_test.c -o build/capability_model_test && ./build/capability_model_test"
```

Required result: exit 0 under strict C90 warnings-as-errors.

REFACTOR: none unless required for test readability. Do not rename encounter
states, reorder any other state, or touch production state-machine logic.

## Chapter 3 — genuine negative controls

In isolated scratch copies, run both perturbations against the production test:

1. Change only the duration declaration from 30 to 29. The literal timing/value
   assertions must fail.
2. Change only the MAIN_MENU start assignment in the scratch
   `capability_model.c` from START_TRANSITION to CHARACTER_SELECT. The first-state
   assertion must fail.

Record commands, exit codes, and assertion/failure text. The perturbations must
occur only in scratch copies. A source-text grep is not a negative control.

## Chapter 4 — cumulative regression

Run in order:

```powershell
python tests/test_avsp_vertical_slice_oracle.py
python tests/test_avsp_translation_boundary.py
python tools/verify_avsp_vertical_slice_oracle.py --generate
python tools/map_avsp_translation_boundary.py --generate
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\test.ps1
git diff --check
```

Requirements:

- Focused oracle/boundary checks exit 0.
- Oracle ledger and boundary artifact hashes remain unchanged.
- `test.ps1` reaches and passes the formerly blocked gameplay-model compile and
  exits 0 through the complete suite.
- Every regenerated tracked output is byte-identical; inspect `git status` and
  every diff explicitly.

If `test.ps1` exposes a later failure, fix it only when it is directly caused by
the restored start-transition timing and the repair remains inside the owned
paths. Otherwise stop and report the new exact downstream blocker; do not widen
the tranche.

## Evidence limits and Saturn constraints

This tranche may produce `MEASURED` host evidence only. Saturn target build,
emulator, normal release, audio, physical timing, memory/BSS, VDP1, VDP2, CRAM,
SCSP, CDDA, disc-read, and cartridge claims remain `UNRUN` and unchanged. No
resource layout or runtime package may change.

## Commit sequence

1. RED test commit.
2. GREEN minimal header repair commit.
3. Evidence/handoff commit after all allowed checks.

Stage explicit paths only. Do not amend, rebase, merge, cherry-pick, broad-stage,
clean, reset, or commit generated/private material.

## Hard stops

Stop and return evidence when:

- the base RED differs from the two declared missing symbols;
- the measured duration cannot be held at exactly 30;
- a production file other than `capability_model.h` must change;
- the oracle or boundary artifact changes;
- full-suite repair requires a path outside the owned set;
- target/emulator/hardware work or new user authority is required;
- private/untracked material cannot be preserved.

## Required final report

Return branch, immutable base, final SHA, commits oldest first, exact files,
RED/GREEN commands and exits, both scratch mutation results, complete `test.ps1`
result, regenerated hashes/diffs, evidence tiers, UNRUN lanes, remaining gaps,
and final worktree status.

End with the complete filled `CODEX_REVIEW_INVOCATION` from
`docs/CODEX_REVIEW_TEMPLATE.md`. Request both the supervisor disposition and
the corresponding next `IMPLEMENTOR_INVOCATION`. Do not self-accept or choose
V2.
