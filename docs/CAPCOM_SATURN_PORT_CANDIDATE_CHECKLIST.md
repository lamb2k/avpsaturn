# Capcom Saturn port candidate checklist

Use this before committing to a historical Saturn-compatible port. A title is
not suitable merely because it boots in MAME or has a related Saturn release.
Complete the machine-readable candidate template in
`templates/capcom_saturn_porting/candidate_assessment.template.json`.

## Hard gates

- Authorized source material and official-port references are available.
- Every source revision is identified and hashed.
- The arcade set audits and cold-boots in a pinned emulator.
- The official Saturn precedent cold-boots with fixed region, BIOS behavior,
  cartridge, controller, and backup state.
- A deterministic route can hold a target neutral and cross movement, attack,
  collision, damage, reaction, rendering, and audio.
- Raw assets and captures can remain private while derived evidence is tracked.
- The new lane has an independent branch and does not rewrite the production
  port's history.

Any failed hard gate means `NO-GO` or a documented research-only exception.

## Engine and behavioral fit

- Identify the arcade board, CPU, graphics, audio, coordinate, and timing model.
- List related official Saturn engines or ports and distinguish title-specific
  evidence from cross-title evidence.
- Count game states, actor classes, animation-script variants, collision types,
  projectiles, meter/super systems, tags/assists, and random sources.
- Prove that state and data can be captured or extracted. Visual capture alone
  is insufficient for behavior, AI, or full-roster work.

## Working-set and rendering fit

Measure focused and worst-case routes separately:

- internal low/high work RAM;
- 4 MB expansion RAM residency and lifetime;
- VDP1 texture/command use and draw completion;
- VDP2 maps, character data, line scroll, rotation, and color RAM;
- simultaneous actors, objects, projectiles, effects, HUD, and shadows;
- palette count, blending, mesh, clipping, priority, and framebuffer mode;
- decompressed asset peaks rather than disc-file sizes.

Required stress routes include the largest characters, maximum assist/tag
activity, effect-heavy supers, busy backgrounds, KO/results transitions, and
rapid rematches or team changes.

## CPU, DMA, and CD fit

- Measure master and slave SH-2 ownership and frame-cycle peaks.
- Identify interrupt, synchronization, and shared-memory costs.
- Record DMA channels, sources, destinations, overlap, and contention.
- Record every gameplay-time CD read, seek distance, transfer time, destination,
  and whether CDDA is active.
- Prove loading windows and retry/error behavior on physical media timing.

## Audio fit

- Inventory music, voices, effects, sample rates, and simultaneous voices.
- Decide which events use CDDA, file-loaded audio, or SCSP-resident samples only
  after tracing the official precedent.
- Measure SCSP RAM, slot reuse, retrigger behavior, onset, duration, and mix.
- Test loading transitions while music is active.

## Fidelity and content fit

- Define functional versus frame-exact parity before estimating effort.
- Inventory roster, stages, moves, frames, effects, modes, endings, options,
  regional differences, home additions, and known bugs.
- Keep gameplay, animation, graphics, content, audio, and performance scorecards
  separate.
- List every expected compromise and the evidence that makes it necessary.
- Do not accept reductions until the full hardware budget and alternatives have
  been tested.

## Decision

Use only these outcomes:

- `GO`: hard gates pass and worst-case budgets have measured headroom.
- `CONDITIONAL`: a bounded research question remains, with a test, owner, and
  deadline; no production promise depends on it.
- `RESEARCH_ONLY`: useful as a precedent but not proven feasible as a port.
- `NO-GO`: authorization, evidence access, deterministic testing, or measured
  hardware fit is absent.

MSHvSF is currently `RESEARCH_ONLY` for this lane: it is an official reference
augmenting AvP, not a second production Saturn build. Its deterministic external
slice passes, while internal state, full hardware peaks, performance, audio,
full-roster coverage, and physical hardware remain open.
