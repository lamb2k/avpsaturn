# Capcom Saturn porting training exercises

These exercises train evidence discipline before implementation. Each exercise
must produce a reproducible command, derived artifact, falsification attempt,
confidence, and explicit remaining uncertainty. Raw ROM and disc payloads stay
private and ignored.

## 1. Reproduce the deterministic pair

Objective: prove the research environment before interpreting the game.

- Re-run the MAME audit and CPS-2 Ryu capture from a cold state.
- Rebuild the Saturn play record and run two cold replays with the pinned disc,
  backup, cartridge, and emulator.
- Compare all declared hashes and confirm P2 is neutral during gameplay.

Pass: the CPS-2 report hash and every Saturn anchor hash reproduce. Fail: any
input, actor, stage, or hash differs without a documented cause.

Current pilot evidence: complete for the normal-hit first pass. The Saturn
Hadouken path remains outside this exercise's current route.

## 2. Locate CPS-2 player coordinates

Objective: turn a visual movement observation into a labeled actor field.

- Use the captured work-RAM interval around frames 1640-1720.
- Find candidate values that change with Ryu movement and jump but remain stable
  for the neutral target.
- Prove ownership with at least two different distances and a reversed facing.
- Locate the writer PC and test signed/wrapped coordinate behavior.

Pass: one address and writer path predict Ryu's normalized position in an
unseen replay. Fail: the candidate follows camera, animation, or another actor.

Current pilot evidence: open. Per-frame RAM exists; no coordinate field is
labeled.

## 3. Recover the Saturn actor structure

Objective: identify semantic state without comparing SH-2 and 68000 code
literally.

- Capture high and low work RAM at idle, walk, jump, normal, impact, and recovery.
- Identify repeated actor records and prove the stride with Ryu, Spider-Man, and
  at least one reserve teammate.
- Map only the fields needed by the slice: position, velocity, action state,
  animation pointer/index, health, and reaction state.
- Trace the writer functions and reject fields that only correlate visually.

Pass: the mapped fields predict all declared transitions in a fresh replay.
Fail: ownership, writer path, or another actor breaks the model.

Current pilot evidence: open. External behavior is deterministic, but no Saturn
RAM trace is captured.

## 4. Trace a normal attack end to end

Objective: connect input, state, animation, collision, damage, and reaction.

- On both systems, record input acceptance, attack-state entry, animation
  transition, first collision-active interval, impact, health write, hitstop,
  reaction-state entry, and recovery.
- Repeat once in range and once out of range.
- Keep gameplay state timing separate from rendered pose timing.

Pass: the in-range route predicts one hit and the out-of-range route falsifies
the collision path without changing attack startup. Fail: a visual pose is used
as a hitbox or health is inferred only from the HUD.

Current pilot evidence: partial. External Saturn impact is proven; internal
collision, health, damage, and hitstop are open.

## 5. Map one animation table

Objective: distinguish mechanical state from presentation conversion.

- Decode one CPS-2 Ryu animation script including duration, flip, assembly
  pointer, offsets, loop, and termination.
- Locate the corresponding Saturn table or runtime schedule.
- Reconstruct both pose timelines and normalize pivots and resolution.
- Test whether any missing Saturn pose changes collision or only presentation.

Pass: the decoder reproduces known anchor poses and predicts an unseen frame.
Fail: the mapping is based only on screenshot resemblance or inferred record
size without control-flow proof.

Current pilot evidence: open. CPS-2 object lists and Saturn screenshots exist;
neither animation table is decoded for this title.

## 6. Identify a VDP1 command path

Objective: prove how one foreground composite reaches Saturn rendering.

- Capture the VDP1 command table and VRAM at idle and normal-active anchors.
- Walk command links, texture addresses, palette/color mode, clipping, priority,
  and local coordinates.
- Trace the SH-2 writer for at least one command or command block.
- Compare per-tile and composed-cel explanations against the actual table.

Pass: the traced commands account for the selected Ryu pose and disappear or
change as predicted on the next pose. Fail: responsibility is assigned from the
visible framebuffer alone.

Current pilot evidence: open.

## 7. Reconstruct expansion-RAM residency

Objective: replace the phrase "uses the 4 MB cart" with a measured allocation
timeline.

- Compare no-cart and 32 Mbit-cart cold boots.
- Trace writes during frontend, team selection, stage load, gameplay, tag, and
  results transitions.
- Record address range, source disc member, compressed and resident bytes,
  owner, load phase, and retirement event.
- Run a worst-case team/effect route and calculate peak simultaneous occupancy.

Pass: every occupied range has an owner and lifetime and the peak fits with
measured headroom. Fail: on-disc package bytes are treated as resident bytes.

Current pilot evidence: open. Cartridge configuration and platform capacity are
known; runtime layout is not.

## 8. Separate ADP, SCSP, and CDDA audio

Objective: map transport, event semantics, and audible timing independently.

- Isolate normal, Hadouken, hit, voice, and stage-music events.
- Trace ADP file reads, SCSP RAM transfers and slots, and CDDA commands.
- Record command frame, decoded-data availability, voice allocation, audible
  onset, duration, retrigger behavior, and channel reuse.
- Attempt transitions while CDDA is active and record any data-read stall.

Pass: each event has a reproducible source and voice/track path. Fail: file names
or track layout are treated as event mapping.

Current pilot evidence: open. CPS-2 QSound windows and Saturn media topology are
only leads.

## 9. Measure a worst-case super and tag sequence

Objective: test the full hardware budget before accepting reductions.

- Choose a route with maximum simultaneous actors, assist/tag activity, large
  effects, scrolling background work, voices, and music.
- Measure master/slave cycles, VDP1 command count and draw completion, VDP1/VDP2
  VRAM peaks, work/expansion RAM peaks, DMA, SCSP slots/RAM, and CD activity.
- Repeat on the official port and any candidate implementation.

Pass: the route meets its frame deadline and every budget has measured
headroom. Fail: a quiet two-character diagnostic is used as full-game proof.

Current pilot evidence: open.

## 10. Classify one apparent reduction

Objective: apply the historical-fidelity vocabulary without overclaiming.

- Find one visual difference and measure animation coverage and gameplay state
  separately.
- Test collision, damage, hitstop, movement, and recovery.
- Attempt to falsify `REDUCTION` with a different character, palette, route, and
  stress condition.
- Record `MATCH`, `EQUIVALENT`, `PLATFORM ADAPTATION`, `OPTIMIZATION`,
  `REDUCTION`, `ALTERATION`, `ADDITION`, `BUG`, or `UNRESOLVED`.

Pass: the classification has evidence on both systems and a failed falsification
attempt. Fail: a missing rendered pose is called a gameplay reduction.

Current pilot evidence: open; no reduction is currently claimed.
