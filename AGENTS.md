# AvP Saturn Capability Agent Instructions

These instructions apply to the entire repository.

## Mission

- Build a private, capture-faithful, native Sega Saturn port capability test of
  CPS2 Alien vs Predator.
- The required route begins at the main menu, preserves state through character
  selection, and plays through the complete first level into Round 2.
- Keep gameplay native SH-2 code. Do not replace the goal with a CPS2 emulator,
  approximate demo, video player, host-only simulation, or focused animation
  viewer.
- Keep the project private. Do not commit, publish, or redistribute ROM data or
  other private source material.

The standing objective and its completion conditions are in `docs/GOAL.md`.
It is phase-independent: pursue it until every condition holds. `docs/PARITY_PLAN.md`
holds the route, `docs/GOAL.md` holds the destination.

## Start every session

1. Use the `port-cps2-to-sega-saturn` skill and read its linked workflow.
2. Run `git status --short --branch` and inspect recent commits. Preserve all
   existing changes; never assume an uncommitted file is disposable.
3. Read `docs/AGENT_HANDOFF.md` completely. It is the authoritative volatile
   checkpoint for hashes, active profile, dirty files, failures, processes, and
   ordered next work.
4. Read `docs/PARITY_PLAN.md`. It is the current direction and phase order.
   The handoff says where work stopped; the parity plan says where it is going.
5. Verify important handoff claims against the current worktree before relying
   on them.
6. Stay on `prototype/private-capability-test` unless the user explicitly asks
   for another branch.

## Current direction: functional parity by ROM translation

As of 2026-08-17 the target is a **functionally parity-accurate** Round 1, and
the method is **translating game logic and data out of the ROM**, not inferring
it from screen captures. `docs/PARITY_PLAN.md` holds the phases, the established
memory and ROM addresses, and the gates.

- Do not extend the capture-a-clip-and-bind-it method for new actors or
  actions. It cannot represent unobserved behaviour, does not scale, and cannot
  reach AI. Existing captured clips remain valid as **regression oracles**.
- The graphics are already solved: the 16 MiB CPS2 graphics region is
  reconstructed byte-for-byte. What is missing is assembly instructions, which
  live in ROM tables that are already located.
- The retail ROM still contains Capcom's debug tools, including hitbox and
  stage-collision overlays. Prefer reading real data from them over inferring
  hit windows from health changes.
- Stock MAME 0.289 is the primary observation instrument. The retained debug
  overlays work with Development hardware mode, active-low fields held before
  frame 0, and a one-time post-init software-switch injection because the
  retail ROM removed the DIP-to-RAM copy. Try stock debugger watchpoints before
  treating a custom MAME build as necessary; keep any fallback patch set
  tracked and pinned.
- Functional parity means matching the actor state trajectory, real hitboxes,
  and real animation sequences and durations. It does not mean identical
  framebuffers or RNG streams. If AI consumes a PRNG, record that decision
  explicitly before translating it.
- Do not begin native reimplementation before a ROM-decoded sprite assembly
  reproduces an already-captured pose pixel for pixel. Building on a misread
  table format is the most expensive available mistake.

The repository has independent Git history even if its checkout is nested in a
larger workspace. Relocation is organizational only; never move or delete the
working checkout without first preserving `.git` and all required ignored
private inputs.

## Evidence and fidelity

- Prefer ROM tables and the game's own debug overlays as source truth. Use
  deterministic MAME capture to confirm what those produce, and retain older
  capture-derived clips as regression oracles rather than extending capture
  and bind for new actors or actions.
- Treat verified deterministic MAME capture as source truth for frame timing,
  inputs, objects, palettes, hit events, camera anchors, and QSound timing
  where no ROM-derived equivalent exists yet.
- Preserve the evidence chain:
  `ROM audit -> deterministic capture -> validating analyzer -> generated asset
  -> native state binding -> ISO member hash -> emulator -> physical Saturn`.
- Generate derived data through repository scripts. Do not hand-edit generated
  headers or archives.
- Label results honestly as capture-exact, native-but-approximate, or missing.
  Screenshots alone do not prove timing, interaction, audio, or route fidelity.
- A reduced-cadence capture may size a representation, but shipped exact
  timelines require every source frame.
- Preserve the documented 384-to-352 horizontal mapping and 224-line height.
  Reject accidental crop, stretch, or unverified black bars.

## Saturn constraints

- Prefer VDP2 for full-screen/scrolling surfaces and VDP1 for actor composites.
- Budget VDP1 texture RAM, Saturn work RAM, SCSP RAM, and both 32 Mbit expansion
  RAM banks separately.
- Treat the Jo Engine reuse allocator as whole-block unless current evidence
  proves otherwise. Combine related phase assets and four-byte-align embedded
  archive offsets.
- Prove phase overlays in the full route, not only a focused build.
- Avoid unmeasured data-track seeks after CDDA begins.
- The target hardware configuration requires an NTSC Saturn, digital controller,
  and 32 Mbit expansion RAM cartridge.

## Verification order

For a changed slice, run the narrowest applicable checks, then broaden them:

1. Deterministic analyzer or converter validation.
2. Host capability tests and deterministic soak.
3. Focused Saturn profile and ISO-member byte/hash verification.
4. Full `-EncounterTest` route through the Round 2 boundary.
5. Clean `normal-release` build and boot from the title/menu using the exact cue.
6. Real-time audible route validation.
7. Physical Saturn validation.

Inspect the emulator process command line because Yaba Sanshiro can retain stale
disc state. A focused or host pass never substitutes for full-route or hardware
proof.

## Repository hygiene and handoff

- Keep ROMs, `.deps`, emulator state, generated builds, raw captures, and other
  ignored private artifacts out of Git unless the repository explicitly tracks
  a derived evidence report.
- Use `apply_patch` for source/document edits and preserve unrelated user work.
- Commit coherent checkpoints only after relevant deterministic checks pass.
- Before stopping or risking a restart, update `docs/AGENT_HANDOFF.md` with the
  branch, HEAD relationship, dirty files, profile, hashes, exact errors,
  running processes, reproducible commands, verified evidence, and ordered
  remaining work.
- Leave the normal-release disc clearly distinguishable from diagnostic discs.
- Do not declare the port hardware-ready or complete while any required route,
  fidelity, audio, crop, allocation, or physical-hardware gate remains open.
