# Goal

Pursue this until every completion condition holds. This file does not change
as the method or phase changes; `docs/PARITY_PLAN.md` holds the route, this
holds the destination.

## Objective

A private, native Sega Saturn build that plays Alien vs Predator Round 1,
"City of Despair", from character-select confirmation through the Round 2
title at **functional parity** with the CPS2 original, on real NTSC Saturn
hardware.

Functional parity: given the same initial state and inputs, the build
reproduces the arcade's actor state trajectory, real hitboxes, and real
animation sequences and durations. It does not require identical framebuffers,
PRNG streams, or sub-pixel rounding.

## Complete when all of these hold

1. **Animation** plays from ROM-derived script tables interpreted at runtime,
   not from captured pose archives.
2. **Collision** uses hitboxes read from the game, not contact offsets inferred
   from health deltas.
3. **Enemy behaviour** comes from translated 68000 routines, not hand-authored
   approximations. Any PRNG dependence is identified and its handling recorded.
4. **Spawns, camera and triggers** come from extracted stage tables.
5. **Validation**: a ROM-decoded sprite assembly reproduces an already-captured
   pose pixel for pixel, and an event-level parity comparison against MAME on
   the deterministic route shows no unexplained divergence.
6. **Regression**: the existing capture-derived clips, the controller-only route
   to Round 2, and the deterministic soak all still pass.
7. **Hardware**: the `normal-release` disc runs the full route on a physical
   NTSC Saturn with a digital pad and 32 Mbit RAM cartridge, at sustained 60 Hz,
   with audio, no partial cels, no palette corruption, and no allocation or
   asset failure.

## Non-negotiable

- Native SH-2 gameplay. Never a CPS2 emulator, video player, host-only
  simulation, or animation viewer.
- Never commit ROM data, raw captures, generated assets, or disc images.
- Never report the goal met while any condition above is open. Label work
  honestly as verified, approximate, or missing.
- Private capability test only. Distribution, public demonstration or promotion
  requires an explicit rights-holder and licensing review; see `NOTICE.md`.

## If blocked

Record the blocker, the exact failure text, and the next reproducible command
in `docs/AGENT_HANDOFF.md`, then continue on the next independent condition.
Do not silently substitute an easier target for a blocked one.
