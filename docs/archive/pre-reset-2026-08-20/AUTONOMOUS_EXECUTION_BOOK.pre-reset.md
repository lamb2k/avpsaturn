# Autonomous execution-book protocol

This document defines how Codex can assign a long, prescriptive body of work to
Claude without a planning/review turn after every package. `AGENTS.md` remains
canonical. An execution book applies only when the invocation says
`MODE: AUTONOMOUS_BOOK_IMPLEMENTATION` or uses its deprecated
`AUTONOMOUS_IMPLEMENTATION` alias.

## Ownership

Codex owns the architecture, chapter order, interfaces, test contracts,
acceptance decision, canonical plans, and next work. Claude owns continuous
implementation and self-evaluation inside the written book.

Claude may:

- implement every ordered chapter on the named branch/worktree;
- create tests, source, tools, generated-data producers, and candidate evidence
  within the book's owned paths;
- repair normal RED tests and regressions without asking for another turn;
- commit coherent candidate checkpoints and update the candidate run ledger;
- continue immediately when a chapter's checks pass.

Claude may not:

- invent a new chapter, architectural substitute, or acceptance tradeoff;
- edit `docs/PARITY_PLAN.md`, accepted package status, Capability Gate counts,
  or `docs/NEXT_AGENT_PROMPT.md` unless the book explicitly carries a separate
  user authorization for plan ownership;
- call a candidate chapter accepted or completed;
- publish, create a remote, commit private/copyrighted inputs, or perform an
  unsafe/destructive action;
- replace missing evidence with an approximate implementation.

## Required book header

Every execution book names:

```text
MODE: AUTONOMOUS_BOOK_IMPLEMENTATION
BOOK_ID: <stable name>
REPOSITORY: <absolute path>
BASE_SHA: <full SHA>
IMPLEMENTATION_BRANCH: <suggested branch>
IMPLEMENTATION_WORKTREE: <separate clean worktree>
RUN_LEDGER: <candidate ledger path; default docs/AUTONOMOUS_RUN_STATUS.md>
OBJECTIVE: <one overall outcome>
OWNED_PATHS: <explicit files/directories>
FORBIDDEN_PATHS: <canonical/shared files not owned>
CHAPTERS: <ordered list>
FINAL_VERIFICATION: <ordered commands>
```

It also records settled facts not to re-derive, private-input assumptions,
actions that require user authority, and the conditions that stop the whole
book.

## Required chapter contract

Each chapter is executable without drafting another plan:

```text
CHAPTER: <number and name>

OUTCOME
<Observable result.>

PREFERRED_IMPLEMENTATION
<Exact files, interface, data representation, algorithm, and ordering.>

FIXTURE_OR_ORACLE
<Source capture/table/manifest/hash or bounded synthetic fixture.>

RED_TEST
File: <test path>
Command: <exact command>
Expected failure: <assertion, mismatch, counter, or exit code>

GREEN_REQUIREMENT
<Exact values and exit code.>

NEGATIVE_CONTROLS
<Concrete mutations and their expected nonzero mismatch/rejection.>

REGRESSION_TIER
<Targeted host, full host, focused Saturn, full route, release, hardware.>

COMMIT
<Checkpoint subject and required evidence.>

CONTINUE_RULE
When GREEN and the assigned regression tier pass, update the candidate ledger,
commit, and begin the next chapter without asking Codex.

FALSIFICATION_OR_HARD_STOP
<Evidence that invalidates the prescribed design or needs new authority.>
```

The preferred implementation is authoritative unless its falsification
condition fires. Claude does not replace it merely because another design looks
cleaner or more general.

## Internal TDD cycle

For behavioral work, Claude performs this cycle inside each chapter:

1. Add or identify the smallest test that observes the required behavior.
2. Run it at the chapter base and record the real RED output.
3. Prefer a `test(red):` commit before the production implementation.
4. Implement only the prescribed behavior needed for GREEN.
5. Run the targeted test and record exact GREEN output.
6. Run every real perturb-and-compare negative control.
7. Refactor while targeted tests remain green.
8. Run the assigned broader regression tier.
9. Commit the candidate checkpoint, update the ledger, and continue.

If a new test passes before the implementation, it does not prove the missing
behavior. Strengthen it or record a hard stop. A hardcoded `failed=true`, a
check that a population exists, or prose saying a mutation would differ is not
a negative control.

Documentation-only and purely mechanical changes may use regression-first
validation without manufacturing a RED commit. The ledger must state why RED
was not applicable.

## Tiered verification cost

Do not run the most expensive route after every edit:

1. During a code loop: targeted host test.
2. At chapter GREEN: targeted tests and negative controls.
3. At a related chapter group boundary: full `test.ps1` and deterministic
   regeneration.
4. At a runtime integration boundary: focused Saturn build, ISO-member hashes,
   and pinned-emulator readback.
5. At book completion: full encounter route, normal-release boot, applicable
   audio checks, process cleanup, and every other final check named by Codex.
6. Physical Saturn stays `UNRUN` unless the book explicitly has hardware
   access and requires it.

## Candidate run ledger

The ledger is implementation evidence, not canonical status. Update it after
every chapter using this structure:

```text
BOOK_ID: <id>
BASE_SHA: <sha>
CURRENT_HEAD: <sha>
CHAPTER: <number/name>
STATUS: CANDIDATE PASS | IN PROGRESS | HARD STOP
RED_COMMIT: <sha or N/A with reason>
RED_COMMAND: <command>
RED_RESULT: <exact failure>
GREEN_COMMIT: <sha>
GREEN_COMMAND: <command>
GREEN_RESULT: <exact result>
NEGATIVE_CONTROLS: <names and results>
REGRESSIONS: <commands and results>
HASHES_AND_MEASUREMENTS: <values>
MEASURED: <items>
ADAPTED: <items>
GAP: <items>
UNRUN: <items and reason>
NEXT_CHAPTER: <number/name or BOOK COMPLETE>
```

Never write `ACCEPTED`, `COMPLETED`, or Capability Gate progress in this
candidate ledger.

## Continue and stop rules

A failing test, compile error, bounds failure, hash mismatch, or emulator bug
is normally work to diagnose and repair inside the current chapter. Claude does
not return merely because implementation is difficult or takes several loops.

Stop the book only when:

- measured evidence falsifies a settled architecture or the chapter's preferred
  implementation;
- required private evidence/tooling cannot be obtained or regenerated;
- continuing needs publication, destructive action, new rights, or another
  authority the user did not grant;
- user-owned changes cannot be isolated safely;
- a material choice between architectures lies outside the book;
- a required check cannot be made meaningful without changing the contract.

On a hard stop, preserve all work, update the ledger with the exact command,
error, evidence and first unresolved decision, stop emulator/MAME processes,
and return one consolidated review payload. Do not draft a replacement plan.

## Final relay to Codex

At book completion or hard stop, update `docs/AGENT_HANDOFF.md` with one
implementation report plus a clearly advisory **Suggested next body**, then
finish with one `CODEX_REVIEW_INVOCATION` containing:

- book ID, repository/worktree, branch, base SHA, and every candidate commit;
- per-chapter RED/GREEN/negative-control evidence;
- changed and overlapping files;
- deterministic hashes and resource measurements;
- focused Saturn, ISO, emulator, full-route, release, audio, and hardware
  results, including `UNRUN` checks;
- remaining `ADAPTED` and `GAP` items;
- any hard stop or deviation from the prescribed implementation;
- exact local/private checks requested from Codex.

Codex reviews the complete book once, makes the sole acceptance decision,
updates canonical status, and writes the next execution book.
