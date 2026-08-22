# ADR 0006: Phase-scoped residency packages

## Status

Accepted for staged implementation.

## Context

The complete four-route content set is not assumed resident at once. Saturn
cart, work RAM, VDP1, VDP2, CRAM, SCSP, and CD ownership must be bounded per
phase, especially while CDDA owns the drive.

## Decision

Every gameplay phase receives a `PortV2PhaseManifest` declaring loaded and
released assets, every memory allocation, CRAM/SCSP ownership, CDDA track,
legal data-read windows, expected high-water, and canaries. No generalized
runtime cache precedes measured need.

## Alternatives considered

- One monolithic archive.
- Opportunistic on-demand loading during combat.
- A general cache/streamer.

## Consequences

Ownership and memory failure become deterministic and testable. Phase planning
must be completed before a body can enter release acceptance.

## Migration impact

SALVAGE/PROMOTE-07 establishes the first production manifest and ownership
machine; later stage templates extend it per measured workload.

## Evidence still required

Complete package inventory, per-phase allocation/high-water, illegal-read
controls, canary coverage, CDDA transitions, and physical load timing.
