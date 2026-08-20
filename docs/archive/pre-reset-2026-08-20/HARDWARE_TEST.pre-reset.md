# Real Saturn hardware test

Physical testing is Capability Gate 1 condition 7 and full-game condition 9,
not a separate gate. This document describes acceptance; it does not imply the
current dirty build is ready.

The present candidate is **not hardware-ready** because the scene-complete
frontend/Round 1 route, parallax renderer, stage CDDA, final memory ledgers, and
clean emulator verification remain open.

## Required setup

- NTSC Sega Saturn in known-good condition;
- digital Saturn controller;
- compatible 32 Mbit / 4 MB expansion RAM cartridge;
- verified optical media or an ODE configuration that preserves the exact cue
  and data/audio track layout;
- capture path capable of showing complete 352x224 geometry and audible output;
- frame-time or high-speed capture method sufficient to establish sustained
  60 Hz rather than visual impression;
- final clean `release-normal-release` cue and recorded SHA-256 values.

Do not test a diagnostic/focused image as the release candidate. Do not infer
physical success from Yaba or another emulator.

## Candidate prerequisites

Before burning/loading the image:

- full `test.ps1` passes;
- clean focused presentation profile passes and its ISO members match manifests;
- normal digital-pad no-skip emulator route reaches Round 2 title;
- `-EncounterTest` reaches `COMPLETE` without regression;
- clean normal-release title boot passes;
- `game.map` and sprite-table bounds are below `0x060c0000`;
- all work RAM, cartridge, VDP1, VDP2, CRAM, SCSP, and allocation peaks are
  recorded with headroom;
- stage CDDA is enabled, audible, source-timed, and has no late data reads;
- all required Round 1 presentation data is resident before the CDDA lock;
- no required scene uses the 13 legacy capture-derived RLE holds;
- emulator/MAME processes are stopped and the exact final cue/hash is recorded.

If any prerequisite is open, report hardware testing as deferred rather than a
failure or pass.

## Capability Gate 1 hardware route

Use a digital pad and the default Predator Warrior route. Do not use a focused
auto-input profile.

1. Cold boot from power-off.
2. Confirm legal/QSound/Capcom/opening and every story panel appear in source
   order with source timing/input behavior. No automated skip.
3. Leave the title waiting for at least 60 seconds. It must remain stable until
   Start; attract is explicitly deferred for Gate 1.
4. Press Start and verify the full Start transition.
5. At character select, visit all four positions with the D-pad. Confirm the
   non-wrapping boundaries, held-direction response, release behavior, live
   cursor, and absence of a baked/stale marker.
6. Return to Predator Warrior and confirm once with each supported button over
   separate boots as needed. A/B/C must confirm; held input must not
   double-trigger; unsupported cancel remains absent.
7. Verify the confirmation shutter and selected character propagation.
8. Verify the ROM-derived Round 1 title appears over the native scene.
9. Play every Round 1 room and presentation transition through results,
   intermission, and Round 2 title. No missing scene, frozen keyframe, new RLE
   playback, crop, black bar, vertical stretch, layer seam, or priority error.
10. During street movement, verify independent foreground/rear parallax and any
    source-required row scroll. Door, interior, boss, and interstitial layer
    ordering must remain correct.
11. Verify controller movement, attacks, jump, lane movement, pause/Start
    behavior, collision, damage, KO, and progression for the currently accepted
    route. Adapted combat differences remain disqualifying for conditions they
    affect; presentation success does not close behavior/collision conditions.
12. Listen through the complete route. CDDA and PCM cues must be audible,
    correctly timed, free of freezes, repeats, cutoffs, and ownership conflicts.
13. Reach the Round 2 title without reset, hang, asset miss, or late disc read.
14. Continue for a ten-minute soak using a diagnostic-equivalent build only if
    its executable/content hashes are tied to the release candidate and the
    diagnostics do not alter resource behavior.

## Required observations

Record:

- console model/region, cartridge, media/ODE, controller, and capture setup;
- cue/ISO/member hashes and build profile;
- video mode and observed full-frame geometry;
- scene-by-scene pass/fail with photographs or capture timestamps;
- parallax, row-scroll, and priority observations at named anchors;
- audible CDDA/PCM observations and transition timing;
- minimum/maximum frame time or equivalent sustained-60-Hz evidence;
- any sprite/texture pop, palette corruption, tearing, seam, missing tile,
  dropped object, audio dropout, seek pause, or input anomaly;
- soak duration and endpoint;
- exact difference between release and any instrumented build.

## Failure handling

- Reproduce first in the clean normal emulator route with the same cue.
- If hardware-only, reduce to one bounded diagnostic build without changing
  lifetime or representation decisions.
- A release-only pass after disabling Jo checks is invalid.
- If sprite high-water reaches 128 or BSS/resource headroom fails, use structural
  relocation/lifetime redesign; do not shrink the allocator blindly.
- If parallax/priority fails, return to layer/register evidence; do not flatten
  the scene.
- If CDDA/data ownership fails, redesign residency or use only a source-proven
  silent boundary; do not accept mid-track seeks.
- Update `docs/AGENT_HANDOFF.md` with exact evidence and keep the relevant Gate
  condition open.

Only a clean candidate that completes this route at sustained 60 Hz with the
required audio, geometry, memory safety, and ten-minute soak may satisfy
Capability Gate 1 condition 7.
