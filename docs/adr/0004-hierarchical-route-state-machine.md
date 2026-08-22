# ADR 0004: Hierarchical route state machine

## Status

Accepted for staged implementation.

## Context

Title-to-credits progression combines frontend, loading, stages, bosses,
continues, endings, audio ownership, and transitions. Scattered timers and
`encounter_state` checks cannot express or audit the complete route safely.

## Decision

Represent `GameSession` as explicit hierarchical states and substates from
Boot through Credits. Every transition declares an event/guard, next state,
source-evidence anchor, and load/release, audio, and scene effects. Keep route,
disc/load ownership, audio ownership, and credit/continue machines separate and
coordinated.

## Alternatives considered

- Continue timer-driven switches in `main.c`.
- Encode the entire route in scene bytecode.
- Adopt a general statechart framework.

## Consequences

Transitions become inspectable and testable. Additional tables and coordination
guards are required, without introducing a general framework.

## Migration impact

Measured route bodies move into tables segment by segment. Unknown guards remain
explicitly `UNKNOWN`; no timer is invented to fill a capture gap.

## Evidence still required

Complete ORACLE-01 route capture, continue/game-over branches, ending/credits
transitions, load/audio ownership traces, and Saturn transition timing.
