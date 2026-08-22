# ADR 0003: Deterministic fixed-tick kernel

## Status

Accepted for staged implementation.

## Context

Source comparison, replay, negative controls, and Saturn timing require one
repeatable simulation clock. Wall-clock and platform calls inside game rules
would make host/Saturn comparison ambiguous.

## Decision

The production kernel advances exactly one source-frame tick through conceptual
entry point `avsp_game_step(game_state, input_frames, frame_output)`. Results
depend only on prior state, fixed-tick inputs, and content data. Gameplay makes
no wall-clock calls or dynamic allocations during an active phase.

## Alternatives considered

- Variable-delta simulation.
- Platform-specific frame callbacks containing game rules.
- Replay correction layered over nondeterministic state.

## Consequences

Input ledgers and state/event hashes can repeat across host and Saturn. Fixed
capacity and deterministic ordering impose explicit budgets.

## Migration impact

Future gameplay bodies move behind the step boundary one bounded behavior at a
time. Accepted benches remain adapters until their state is kernel-owned.

## Evidence still required

Two-run determinism for each migrated body, real perturbation controls,
host/Saturn event equivalence, and physical frame-pacing proof.
