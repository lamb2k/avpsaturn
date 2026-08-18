# Capcom Saturn port acceptance checklist

This is a release gate, not a progress summary. Mark an item complete only with
a linked report, capture, manifest, trace, or physical test record. A focused
profile cannot satisfy a full-route or normal-release item.

## Provenance and build

- [ ] Authorized source and reference revisions are identified and hashed.
- [ ] Arcade ROM audit passes in the pinned emulator.
- [ ] Source media remains unchanged; loader repairs use disposable overlays.
- [ ] Generated data is deterministic and raw copyrighted inputs are excluded
  from Git.
- [ ] Toolchain, emulator, BIOS behavior, region, cartridge, controller, and
  backup state are pinned.
- [ ] Clean focused, full-route, and normal-release builds have manifests with
  byte counts and SHA-256 hashes for every required disc member.

## Gameplay parity

- [ ] Title/menu-to-route state order matches the declared contract.
- [ ] Input latency and buffering meet explicit tolerances.
- [ ] Movement, coordinates, camera, collision, damage, hitstop, reactions, and
  recovery pass deterministic same-input tests.
- [ ] Projectiles, meter, supers, tags/assists, character mechanics, AI, RNG,
  KO, round, continue, and results paths pass.
- [ ] In-range, out-of-range, blocked, whiff, trade, and simultaneous-hit
  falsification routes pass.

## Animation and graphics

- [ ] Animation scripts, pose order, duration, pivots, flip, loops, and
  termination are mapped for required content.
- [ ] Gameplay timing and rendered-pose timing are reported separately.
- [ ] Resolution, aspect, crop, coordinates, and palette comparisons are
  normalized.
- [ ] Actors, projectiles, effects, shadows, HUD, backgrounds, priority,
  clipping, blending/mesh, fades, and transitions pass representative routes.
- [ ] Full-roster and worst-case effect scenes fit VDP1 commands/VRAM and VDP2
  VRAM/color RAM without draw-over or unclassified loss.

## Content

- [ ] Roster, moves, stages, modes, endings, options, regions/revisions, home
  additions, and known bugs are inventoried.
- [ ] Every absent or changed item has a classification, evidence, rationale,
  owner, and acceptance decision.
- [ ] No low-confidence hypothesis is treated as a content decision.

## Audio

- [ ] Every required event maps to source asset, Saturn transport, voice/slot or
  CDDA track, command frame, audible onset, duration, and mix behavior.
- [ ] Rapid retrigger, channel reuse, simultaneous voices, music transitions,
  pause, KO, results, and rematch routes pass.
- [ ] SCSP RAM peaks and CDDA/data-read interaction are measured.

## Performance, memory, and loading

- [ ] Master and slave SH-2 responsibilities and worst-case cycle peaks are
  measured against the frame deadline.
- [ ] Work RAM, expansion RAM, VDP1 VRAM, VDP2 VRAM/color RAM, and SCSP RAM have
  measured focused and full-route peaks, owners, lifetimes, and headroom.
- [ ] DMA transfers and contention are measured.
- [ ] Every CD read has source, destination, size, timing, seek, and CDDA-overlap
  evidence.
- [ ] Worst-case team/super/tag/background/audio routes pass sustained frame
  pacing without asset, allocation, rendering, or audio failure.
- [ ] Loading screens, retries, disc errors, transitions, and rapid rematches
  pass on physical-media timing.

## Validation ladder

- [ ] Host semantic and capability tests pass.
- [ ] Deterministic soak test passes.
- [ ] Focused Saturn profile boots and passes its exact route.
- [ ] Full encounter/full-route profile boots and passes with all concurrent
  assets.
- [ ] Clean normal release is rebuilt last, reports `profile=normal-release`,
  and boots from title/menu.
- [ ] Portable cue/ISO passes on physical NTSC Saturn with digital pad and
  required 32 Mbit RAM cartridge.
- [ ] Sustained performance, audible audio, loading, reset, and soak behavior are
  recorded on hardware.

## Documentation and decision

- [ ] Correspondence database, difference ledger, architecture map, hardware
  budget, fidelity scorecard, and pattern library match current evidence.
- [ ] Every important claim includes both-system evidence, test, falsification,
  confidence, uncertainty, and reusable lesson.
- [ ] Every unresolved deviation is visible and has an owner or accepted waiver.
- [ ] Only patterns confirmed by runtime evidence and the required number of
  official precedents are promoted to standards.
- [ ] The release decision names what is capture-exact, functionally equivalent,
  intentionally adapted, reduced, altered, added, buggy, and unresolved.

Release status remains `OPEN` until every mandatory item is checked or has a
documented, explicitly accepted waiver. A passing emulator slice is never a
substitute for the full checklist.
