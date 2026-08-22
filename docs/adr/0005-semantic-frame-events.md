# ADR 0005: Semantic frame events

## Status

Accepted for staged implementation.

## Context

Direct VDP, audio, disc, or emulator actions inside gameplay would make
presentation own behavior and prevent the same core from running under host
recorders and Saturn adapters.

## Decision

`AvspFrameOutput` contains fixed-capacity semantic render, audio, load/release,
route-transition, and telemetry event arrays. Events describe game meaning and
stable source identities, not Saturn command addresses or presentation-specific
sprite IDs.

## Alternatives considered

- Direct platform calls from actors.
- One untyped event stream.
- Presentation polling all game state with no ordered events.

## Consequences

Adapters can record, compare, budget, and submit identical intent. Capacity,
overflow behavior, event order, and identity schemas must be explicit.

## Migration impact

Each promoted subsystem gains only the event types required by measured AvP
behavior. Existing diagnostic readback remains a consumer, not gameplay logic.

## Evidence still required

Capacity high-water across route workloads, deterministic ordering, overflow
negative controls, and physical submission/timing proof.
