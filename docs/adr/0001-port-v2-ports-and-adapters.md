# ADR 0001: Port V2 ports and adapters

## Status

Accepted for staged implementation.

## Context

The mixed runtime couples game state, Saturn presentation, loading, audio, and
diagnostics. The production game must run under host differential tests, MAME
fixtures, and native Saturn adapters without giving any platform authority over
game rules.

## Decision

Build a title-specific Port V2 kernel behind purposeful input, render, audio,
asset, telemetry, and persistence/credit ports. Host, MAME, Saturn, and
temporary legacy implementations are adapters. This follows the inside/outside
boundary described by [Ports and Adapters](https://alistair.cockburn.us/hexagonal-architecture).

## Alternatives considered

- Continue expanding the mixed `main.c` runtime.
- Bind the game core directly to Jo/SGL.
- Build separate host and Saturn game implementations.

## Consequences

Game-domain behavior becomes independently deterministic and testable. Adapter
contracts and semantic conversions require explicit design and regression
coverage.

## Migration impact

Add ports only through future cards. Existing accepted systems remain runnable
behind temporary adapters until production replacements pass their locks.

## Evidence still required

Host/Saturn differential proof for each port, target compile boundaries,
integrated timing, and physical Saturn acceptance.
