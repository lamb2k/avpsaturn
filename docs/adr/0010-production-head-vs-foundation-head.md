# ADR 0010: Production head versus foundation head

## Status

Accepted.

## Context

The old `accepted_head` identifies the Tranche 2A foundation while later
player/enemy production work is accepted on a sequential continuity line. Using
one field as both base concepts makes future task cards ambiguous.

## Decision

Record `foundation_head`, `production_head`, `candidate_head`, and
`evidence_candidate_head` separately in `project_state.yaml`. Keep legacy
aliases temporarily for existing tooling. Future production cards base from
`production_head`; the active INTEGRATE-01 card and protected V2-2B evidence
retain their current metadata.

## Alternatives considered

- Move `accepted_head` and reinterpret historical cards.
- Merge the divergent master-plan line wholesale.
- Create a new worktree/branch for every card.

## Consequences

Foundation, accepted production, in-progress runtime, and evidence candidates
are unambiguous. Validators must check commit identity and ancestry.

## Migration impact

The existing `codex/avp-user-02-enemy-review` line is designated production
continuity. New isolation is created only for an actual dependency or safety
need.

## Evidence still required

Each approved successor must advance `production_head` only after coherent
commit, normal push to `private-origin`, and verified remote SHA.
