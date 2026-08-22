# ADR 0002: Legacy displacement by abstraction

## Status

Accepted for staged implementation.

## Context

Accepted player, enemy, camera/stage, HUD, and PCM results must survive while
authored-controller coupling is removed. A wholesale cutover would discard
working evidence and enlarge the correction surface.

## Decision

Use branch-by-abstraction: define one narrow production interface, wrap the
working implementation, move its caller to the interface, implement and compare
the replacement, switch composition, then delete the adapter. Each adapter
records its wrapped implementation, interface, locks, coupling, and exact
deletion condition. See [Branch by Abstraction](https://martinfowler.com/bliki/BranchByAbstraction.html).

## Alternatives considered

- Rewrite the runtime in one cutover.
- Preserve legacy adapters indefinitely.
- Maintain a separate long-lived rewrite branch.

## Consequences

Migration remains runnable and reviewable. Temporary duplication is accepted,
but unbounded compatibility layers are prohibited.

## Migration impact

Player, enemy, stage, HUD, PCM, and frontend receive explicitly temporary
adapters. Goal Mode removes each only after its deletion condition is proven.

## Evidence still required

Per-adapter old/new differential results, approved-lock regression evidence,
and clean deletion proof with no remaining caller.
