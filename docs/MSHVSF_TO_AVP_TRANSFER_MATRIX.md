# MSHvSF-to-AvP evidence transfer matrix

This document is the insertion-ready boundary between the isolated MSHvSF
research lane and the AvP production line. It does not authorize merging the
research branch into AvP. A finding may enter the AvP handoff or parity plan
only after the listed AvP probe passes.

## Handoff insertion

Add a compact `Official Saturn reference-port findings` section to
`docs/AGENT_HANDOFF.md` on the AvP branch. That section should contain only:

1. the immutable MSHvSF research checkpoint commit;
2. findings that have passed their AvP-specific validation probe;
3. the exact AvP artifacts or measurements produced by those probes;
4. remaining uncertainty and the next command or test;
5. an explicit statement that no MSHvSF timing, gameplay constants, code, or
   assets were imported.

Do not copy the research lane's full training material into the handoff. The
handoff is an operational resume point, not the evidence archive.

## Parity-plan insertion

Do not add a new AvP goal condition and do not reorder the seven existing goal
conditions. Attach each accepted finding to the existing condition it helps
close. A reference-port finding can change the method or add a validation
probe; it cannot close an AvP condition without AvP evidence.

| Reference evidence | AvP question it reduces | AvP validation probe | Parity-plan destination | Prohibited inference |
|---|---|---|---|---|
| Official port uses a 4 MiB expansion cartridge and exposes separate disc package families | Which Round 1 data should persist in cartridge RAM and which should be phase-loaded from CD? | Instrument AvP allocation by phase; record cartridge high-water mark, allocation lifetimes, reload count, and CD stalls during the deterministic Round 1 route | Conditions 6 and 7; Phase 3 cartridge-budget paragraph and physical-hardware gate | MSHvSF package sizes or lifetimes are AvP budgets |
| Official disc contains multiple executable/module-like members | Can AvP's native runtime be separated into boot, common, room, and actor modules without forcing one monolith? | Produce an AvP ownership table for boot/common/room/actor data, then verify deterministic unload/reload across street, interior, boss room, and Round 2 transition | Conditions 4, 6, and 7; Phase 3 platform infrastructure | Similar filenames prove identical Capcom loaders or module formats |
| Deterministic Saturn replay separates external gameplay anchors from internal implementation | Can AvP validate state trajectory independently from rendering and animation storage? | Reuse one existing player-to-enemy normal hit; compare input, movement, collision event, damage, hit reaction, and recovery over two cold runs | Conditions 2 and 5; Phase 4 event-level parity harness | Similar-looking attacks have identical timing or damage |
| Capacity evidence identifies work RAM, VDP1/VDP2 memory, SCSP RAM, and expansion RAM as separate resources | What must be measured before choosing precomposed cels versus per-tile VDP1 commands? | Add per-resource AvP high-water measurements and VDP1 command counts for one street wave and Chrysalis; compare both rendering strategies with the same route | Conditions 1, 5, and 7; Phase 3 tile-pipeline decision | Platform capacity proves actual official-port residency or bandwidth |
| Exact Marvel normal-hit dumps show stable cartridge/VDP2 residency while VDP1, both work RAMs, and sound RAM change | Should AvP keep combat assets resident and confine per-frame mutation to actor state, VDP1 commands, and audio control? | At AvP renderer integration, capture the same regions at idle, attack-active, impact, and recovery; require AvP-specific residency, command-count, and high-water evidence before choosing an architecture | Conditions 1, 5, 6, and 7; Saturn renderer and cartridge-lifetime decision | Marvel addresses, 3,549,571 nonzero cartridge bytes, page counts, or command counts are AvP budgets |
| Official Saturn output can be captured at fixed frames with fixed controller input and backup state | Can AvP make hardware-facing regressions reproducible instead of relying on subjective playthroughs? | Run two cold AvP routes with the same input record and compare event logs, stable per-member build hashes, screenshots at semantic anchors, and completion frame | Conditions 5, 6, and 7; Phase 4 validation | Emulator agreement closes physical Saturn timing or audio gates |
| Mixed data-track and CD-audio media topology is verified | Which AvP sounds belong in CDDA, SCSP PCM, or streamed/loading phases? | Record an AvP audio ownership table, SCSP RAM high-water mark, CDDA transitions, and any data-read/audio overlap through Round 1 | Conditions 6 and 7; Phase 3 audio path and final audible route | Track layout proves which individual effects were SCSP or CDDA-driven |
| MSHvSF CPS-2 and Saturn behavior can be classified independently as match, adaptation, reduction, or unresolved | How should AvP document intentional Saturn differences without weakening parity? | Apply the difference-ledger schema to every accepted AvP deviation, including evidence, reason, falsification test, confidence, and acceptance owner | Conditions 5 through 7; Phase 4 and final release review | An official Capcom compromise automatically authorizes the same AvP compromise |

## Initial action-plan effects

The reference lane adds these tasks without displacing current ROM-translation
work:

1. Add resource high-water logging to the AvP host model and Saturn diagnostic
   build before deciding whether phase overlays can be removed.
2. Add media and runtime ownership columns to the existing Round 1 data plan.
3. Define one semantic normal-hit event trace as the first event-parity fixture.
4. Record VDP1 command count and VDP1/VDP2/SCSP/cartridge use at the same route
   anchors already used by AvP regression captures.
5. Use the difference ledger for any proposed platform adaptation; leave it
   `UNRESOLVED` until the AvP test passes.

These tasks support the existing critical path. They do not supersede decoding
AvP animation scripts, hitboxes, actor routines, or stage tables.

## Promotion gate

A research result is eligible for the AvP branch only when all are true:

- the research-lane source and checkpoint are immutable and named;
- the claim identifies whether its evidence is static, behavioral, traced, or
  measured on hardware;
- an AvP-specific probe has passed and produced a tracked, copyright-safe
  derivative artifact;
- the claim states what would falsify it;
- the transfer contains no ROM, disc image, raw extracted member, decoded
  copyrighted asset, or copied gameplay constant;
- the AvP handoff and parity-plan status remain truthful after insertion.
