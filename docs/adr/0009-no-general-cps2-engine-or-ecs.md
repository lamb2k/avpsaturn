# ADR 0009: No general CPS-2 engine or ECS

## Status

Accepted.

## Context

The objective is one faithful AvP port. A general CPS-2 emulator, generalized
Capcom engine, whole-program recompiler, general ECS, or speculative scene
language would consume effort before the title's measured route and character
differences are known.

## Decision

Implement only title-specific Port V2 state, definitions, adapters, and tools
required by measured `avspu` behavior and Saturn constraints. Selective source
lifting remains bounded to demanded transitive behavior.

## Alternatives considered

- General CPS-2 runtime emulation.
- Static recompilation of the full source program.
- General-purpose Capcom beat-em-up framework or ECS.

## Consequences

Interfaces may be less reusable across titles, but scope, provenance, and
performance remain reviewable. Shared code is extracted only after repeated
measured need.

## Migration impact

Validators and reviews reject speculative framework work. Existing bounded
fixtures remain evidence tools, not a new engine.

## Evidence still required

No behavioral evidence can prove this scope choice; ongoing card review must
show each new abstraction is required by an accepted AvP experiment.
