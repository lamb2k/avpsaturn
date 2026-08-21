# Canonical Codex review and continuation template

Use this envelope for every implementor return. Fill every bracketed field;
do not replace it with a bare `CODEX_REVIEW_INVOCATION` heading.

```text
CODEX_REVIEW_INVOCATION

SUPERVISOR_REPOSITORY: C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest
IMPLEMENTATION_WORKTREE: [absolute path]
IMPLEMENTATION_BRANCH: [branch]
IMMUTABLE_BASE_SHA: [40 hex]
CANDIDATE_HEAD_SHA: [40 hex]
COMMITS_OLDEST_FIRST: [ordered full SHAs]
OBJECTIVE: [bounded tranche objective]
OWNED_PATHS: [explicit paths]
IMPLEMENTATION_SUMMARY: [behavior and evidence summary]
CHECKS_PASSED: [commands and exits]
CHECKS_FAILED: [commands, exits, and attribution]
CHECKS_UNRUN: [exact checks and reason]
EVIDENCE_TIERS: [claim=tier list]
REMAINING_GAPS: [explicit gaps]
STOP_CONDITION: [NONE or exact declared stop]

REVIEW_SCOPE:
- Review the complete immutable-base-to-candidate range and claimed evidence.
- Preserve both worktrees and all private/untracked material.
- Return exactly ACCEPTED, CORRECTIONS REQUIRED, or NOT REVIEWABLE.
- Do not implement production changes during review.

SUPERVISOR_CONTINUATION_REQUIRED: true
AUTOMATIC_SUPERVISOR_LAUNCH: After the candidate is committed, clean, and pushed to the verified private remote, create a new Codex task using model gpt-5.6-sol with medium reasoning. Pass this complete CODEX_REVIEW_INVOCATION verbatim, direct it to the supervisor repository and selection branch, and request exactly ACCEPTED, CORRECTIONS REQUIRED, or NOT REVIEWABLE plus the corresponding next IMPLEMENTOR_INVOCATION. Return the created task identifier to the user; do not self-accept in the implementor task.
ON_ACCEPTED: reconcile accepted evidence with the active ledgers and plan, update canonical status, select the next dependency-ready tranche, and issue a complete IMPLEMENTOR_INVOCATION
ON_CORRECTIONS_REQUIRED: issue one consolidated correction IMPLEMENTOR_INVOCATION against the reviewed candidate HEAD
ON_NOT_REVIEWABLE: issue the minimum evidence/isolation IMPLEMENTOR_INVOCATION needed to make the candidate reviewable

NEXT_ASSIGNMENT_REQUIREMENTS:
- exact 40-character base SHA and separate branch/worktree;
- Codex-authored architecture and bounded investigation decision table;
- ordered RED/GREEN/refactor chapters and real negative controls;
- explicit owned paths, constraints, exclusions, verification, stop, commit,
  and return contracts;
- require the next implementor to return through this same template.
```
