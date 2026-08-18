# Next agent prompt: slice V — the VDP1 shape proof

Continue the private native Alien vs Predator Saturn port using the
`port-cps2-to-sega-saturn` skill.

Repository:

```text
C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest
```

Expected branch: `codex/avp-master-plan`.

**This prompt authorizes slice V only.** Not the actor spine, not collision
integration, not AI, not stage work.

## Read and verify first

1. The skill's `SKILL.md` and `references/workflow.md`.
2. `AGENTS.md` and `CLAUDE.md`.
3. `docs/GOAL.md`.
4. `docs/AGENT_HANDOFF.md` — "Phase A: AvP sprite demand measured", "Plan
   re-sequenced around the actor spine", "Official Saturn reference-port
   findings".
5. `docs/PARITY_PLAN.md` — the phase table, the demand measurement, and
   "Slice V — the VDP1 shape proof".
6. `docs/TEST_PLAN.md` and `docs/HARDWARE_TEST.md`.

Record branch, HEAD, recent commits and `git status`. Preserve every existing
untracked/private ROM, MAME state, raw capture, `nvram/`, `snap/`,
`check_tail.py`, `tools/diag_*`, `tools/probe_*`, screenshot and helper file.
Stage explicit paths only. Never `git add -A`, `git add .`, reset, clean or a
broad stash. Do not switch, merge or cherry-pick the Marvel lane; do not edit
the separate MSHvSF worktree.

## Why this slice exists

Everything downstream — the actor spine, ROM-driven animation, collision
integration, AI translation — assumes AvP can render its own worst frame from
its own object list, natively, at 60 Hz. If that is false the runtime's shape
changes, and it is much cheaper to learn now than after the actor model is
built around it.

Already measured and not to be re-derived (`data/avsp_sprite_demand.json`,
5,302 captured frames):

- peak 86 objects / **909 16x16 tiles** per frame (peak frame **5776**);
- **83.6% of objects are blocked sprites**, mean 8.51 tiles, largest 55 tiles;
- **13 live 16-colour palettes** at peak, against 128 CRAM banks available;
- texture: 68 KB peak per frame, ~309 KB one-second working set, 665 KB for the
  whole street-wave window;
- per-frame new tiles: 5.7 KB mean, 15.2 KB p95, **29.5 KB peak**.

## Sole objective

Prove, by measurement on real hardware, that AvP's peak frame renders at 60 Hz
as **one VDP1 normal-sprite command per CPS2 object**.

- **Producer for this slice is a replay harness, never shipped:** feed the
  captured CPS2 object lists for a window containing frame 5776. Phase B
  replaces the producer with the ROM-driven actor spine; the consumer built here
  does not change.
- **Consumer is real and permanent:** one VDP1 normal sprite per object,
  `nx*16 x ny*16`, 16-colour bank mode, flip in `CMDCTRL`, jump-next linked,
  source list order preserved as draw order.
- **Textures:** a per-block cache (a blocked object needs its tiles contiguous as
  an `nx*16`-wide texture), cartridge-resident, with the per-frame delta DMA'd.
- **Palettes:** the live 16-colour banks into VDP2 CRAM.

## Honest scoping of the offline work

An earlier framing claimed the 5,302-frame object-list oracle gates this slice.
It does not, and do not build the slice around that idea: when the producer is a
replay of MAME's own object list, comparing the emitted list back to it is close
to vacuous. That oracle belongs to **phase B**, where the ROM-driven producer
must generate the list itself.

The meaningful offline gate here is narrower: **coverage**. Every object shape
and flag combination that appears in the captures must map to a legal VDP1
command. That is worth testing across all 215,646 captured objects because an
unhandled block shape, size limit, palette-bank range or flip combination would
otherwise surface as a rendering bug much later.

Keep the offline work to what is needed to boot. The value of this slice is the
hardware number.

## Deliverables

- `tools/build_avsp_block_textures.py` — from the private ROM tiles plus the
  window's captured object lists, emit the per-block texture set and a **tracked
  manifest** carrying counts, sizes and hashes only. Never commit tile data.
- `tools/test_avsp_object_to_vdp1.py` — the coverage gate above, over every
  captured object; report any shape/flag that has no legal mapping.
- a focused Saturn build that replays the window and emits per-object commands;
- a frame-time measurement at the peak frame, recorded with its method.

Every asserted field carries an evidence label (`MEASURED`, `DECODED`,
`INFERRED` with its falsifier, `ADAPTED` with its reason, `UNRESOLVED` with its
probe). Generated reports must be deterministic — run twice, identical hash.

## Gates

1. **Coverage:** every captured object maps to a legal VDP1 command; unhandled
   cases are enumerated, not silently skipped.
2. **Frame time at peak:** the peak frame (86 objects / 909 tiles) holds 60 Hz.
   Record measured frame time, not a pass/fail impression.
3. **DMA:** the 29.5 KB peak texture delta completes inside vblank.

**Emulator frame time is indicative only.** Yaba Sanshiro will not tell you
truthfully whether VDP1 holds 60 Hz. Gate 2 is binding only on physical NTSC
Saturn per `docs/HARDWARE_TEST.md`, or on an FPGA core as a closer proxy that is
still not the hardware gate. Say which instrument produced each number.

If gate 2 fails at per-object, **fall back to one command per 16x16 tile and
re-measure** before changing anything upstream. Both granularities draw the same
~233k pixels; only command count and per-command SH-2 build cost differ. Report
both numbers either way — that comparison is the durable result of this slice.

## Boundaries

- The replay harness is a test instrument. Do not let it become a rendering path,
  and do not present a replayed frame as ROM-driven rendering.
- Do not modify `capability_model.c` or the existing cel path yet; slice V runs
  beside them.
- Do not start the actor spine, collision integration, AI or stage work.
- Do not decode further ROM tables — the standing rule from milestone 2.
- Never commit ROM bytes, tile data, raw screenshots, RAM dumps or disc members.
- Restore `normal-release` after any diagnostic build.

## Acceptance

Slice V passes when gates 1 and 3 pass and gate 2 has a measured frame time from
a named instrument, with the per-object and per-tile command counts both
reported. A passing slice does **not** close any Gate 1 condition: Gate 1 stays
0/7 and the full-game goal stays 0/9, because nothing here is ROM-driven yet.

## Handoff discipline

Update `docs/AGENT_HANDOFF.md` and `docs/PARITY_PLAN.md` with the measurement and
honest status; record branch, HEAD, dirty files, raw paths, hashes and exact
commands; stop MAME and emulator processes or record their ownership; stage
explicit files only; commit one coherent checkpoint if the gates pass.

## What comes after (do not start it here)

S1 actor spine — mirror the ROM's `0xC0` actor record in a native struct, gated
by loading captured work-RAM frames and reading back identical fields. It is
independent of this slice and unblocks both collision and AI, so it may run in
parallel in a separate body if you have a second agent.
