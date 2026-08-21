# AvP operational roadmap and parity gates

This is the project's single active roadmap and backlog. `project_state.yaml`
is the machine-readable source of truth for current hashes, dispositions,
blockers, capability-condition status, and the active task card. Evidence history belongs in
`docs/AGENT_HANDOFF.md` and the evidence ledger, not in a second roadmap.

## 1. Goal

Deliver a native, capture-faithful Sega Saturn port of *Alien vs. Predator*
whose gameplay, presentation, audio, responsiveness, and stability are proven
against title-specific evidence. The shortest acceptable proof is a normal
release image that cold-boots and completes the bounded physical capability
slice without authored fallback.

The project has enough foundational evidence. The critical path is now:

1. Accept the current HIT/KO writer closure.
2. Implement native HIT/KO host parity.
3. Complete the bounded host gameplay loop.
4. Build the slice assets and Saturn diagnostic runner.
5. Run AvP's representative and 909-tile physical performance test.
6. Optimize only if AvP fails its own performance contract.

After the completed AvP slice passes, compare it with MSHvSF only as a
non-blocking quality calibration.

## 2. AvP performance contract

AvP passes or fails on its own measured workload. MSHvSF is not a prerequisite
or a source-layout template. A later same-chain comparison may calibrate the
quality result, but it cannot replace any AvP measurement below.

| Dimension | Hard target |
|---|---|
| Frame pacing | One deterministic simulation tick per displayed field, with no sustained skipped, repeated, or late fields. |
| Display cadence | Stable NTSC output at the target Saturn cadence throughout gameplay. |
| VDP1 | Representative schedules and the measured 909-tile peak complete before the draw deadline with at least **15% measured draw-end margin**. |
| CPU and transfer | Simulation, command preparation, transfers, and submission finish with at least **15% frame-time margin** in the worst accepted scene. |
| Cartridge | Every gameplay phase fits with at least **15% usable headroom** and an instrumented lifetime map. |
| Work RAM, VRAM, and SCSP | At least **15% mutable-arena headroom**, no canary damage, and no unmeasured allocator growth. |
| Input | No additional queued simulation frame; record input-to-photon latency on the exact console, controller, display, and capture chain. |
| Loading | No invisible mid-combat stalls and no data-track read while CDDA owns the drive. |
| Audio | Timed PCM and continuous CDDA without dropout, starvation, or false ownership state. |
| Stability | Zero missed fields, corruption, fallback activation, hangs, or audio loss during the ten-minute worst-case slice soak; longer soak is required for release. |
| Visual quality | No sprite breakup, missing tiles, palette corruption, priority instability, or crop behavior that changes gameplay visibility. |

The representative replay, 909-tile peak, overload negative control, and
ten-minute alternating soak are central architecture gates. Optimize the flat
per-tile VDP1 path only after an AvP measurement fails this contract.

## 3. Accepted baseline and current checkpoint

CURRENT_TASK: V2-2B

`project_state.yaml` owns the authoritative SHAs, disposition, checkpoint,
active-card status, blockers, and capability count. `CURRENT_TASK` is the only
mutable routing value repeated here, and the Fast lane rejects disagreement
between it and the active task card.

The accepted foundation provides exact `avspu` identity, a deterministic
1,390-frame MAME gameplay oracle and perturbation control, the complete
7,314-PC translation boundary, and the restored strict host suite. The
The candidate writer closure reports 301 PCs, 302 edges, 12 routines, nine computed
targets, seven semantic fields, and no unresolved or unattributed selected
dependencies. Those recorded counts are not accepted closure until the
corrections on the active task card pass bounded Tier 2 re-review.

## 4. Active backlog

Only the next eight dependency-ready outcomes belong here.

| Priority | Work | Dependency |
|---:|---|---|
| 1 | Final consolidated Tier 2 review and acceptance disposition for the Tranche 2B HIT/KO writer closure | None |
| 2 | Implement the accepted HIT/KO writer set in the isolated native host differential core | #1 |
| 3 | Define stable native actor-state and semantic event interfaces shared by host and Saturn | #2 |
| 4 | Build exact before/after and multi-frame HIT/KO differential fixtures | #2 |
| 5 | Extend the native core through the bounded host gameplay loop | #2 |
| 6 | Build the exact slice asset inventory/package and close missing palette coverage | #5 |
| 7 | Integrate the host-proven core and available assets into a thin Saturn diagnostic runner | #5 and #6 |
| 8 | Build and run the representative, 909-tile, and overload physical replay proof | #6 and #7 |

## 5. Delivery roadmap

### R0 — Accept and freeze the HIT/KO closure

Conduct one final consolidated Tier 2 review of the Tranche 2B validator
correction. On `ACCEPTED`, pin the candidate SHA, freeze its writer-set
manifest, activate `V2-B1`, and stop validator work unless a later behavioral
differential exposes a concrete missing dependency.

**Exit:** an accepted HIT/KO lift contract; no mapping-only tranche remains
active.

### R1 — Native HIT/KO host parity

Translate the bounded writer set into `src/port_v2/` with tests in
`tests/port_v2/`. Preserve explicit signed and unsigned 8/16/32-bit semantics,
condition-code dependencies, exact actor-state transitions, animation-record
repoints, health/hit writes, and action/state/substate/timer changes. Do not
place this implementation in the legacy `main.c` or authored
`capability_model.c` path.

**Exit:** zero semantic differences across the accepted HIT-to-KO interval;
deterministic repeats; instruction/input mutations fail as expected; no
authored fallback.

### R2 — Bounded host gameplay loop

Extend the native core through digital input, player movement and attack, class
`0x1F` enemy walk/attack, collision selectors, contact, damage, HIT, KO,
animation advancement, camera movement, one stage checkpoint, and semantic
render/audio events. Add mapping only when a failing differential names a
specific unsupported dependency.

**Exit:** zero required semantic mismatches across the accepted 1,390-frame
window and no unclassified or authored fallback.

### R3 — Complete slice asset package

Create one deterministic phase-contained package for the player, class `0x1F`
enemy, emitted tiles, all referenced object palettes, stage scroll2/scroll3
cell maps, HUD, priorities, PCM cues, one CDDA track, source-proven load
transitions, and lifetime/provenance metadata. Close the known gap between the
ten shipped object-palette banks and the fifteen measured route banks through
package content, not a CRAM redesign.

**Exit:** every required asset resolves to an exact source identity, all
simultaneous palettes fit, no screenshot-derived gameplay content is required,
and planned static arenas retain 15% headroom.

### R4 — Saturn diagnostic gameplay runner

Wrap the host-proven core in a thin diagnostic ISO with one master-SH-2 loop,
one input sample per tick, typed actor/collision/stage state, semantic
VDP1/VDP2/audio queues, stable readback, mismatch/fallback counters, and cycle
and high-water telemetry. Direct checkpoint entry is allowed for diagnostic
iteration only.

**Exit:** the pinned emulator matches the host/MAME state trajectory, HIT and
KO occur on expected frames, counters stay at zero, repeats are deterministic,
and the diagnostic ISO boots consistently.

### R5 — AvP physical performance proof

On physical Saturn, replay representative gameplay frames, the measured
909-tile peak, and an overload negative control using the flat per-tile 4bpp
command model first.

- **Pass:** lock the flat per-tile model and continue.
- **Fail:** add only the minimum measured remedy, such as bounded preassembled
  composites, a threshold hybrid, or load-time composition, then repeat the
  exact failed test.

Do not build a general dynamic composite cache, linked-command framework, or
slave-SH-2 scheduler without an AvP profile identifying that bottleneck.

**Exit:** zero missed fields/corruption, at least 15% VDP1 draw-end margin at
909 tiles, and at least 15% total-frame margin for the diagnostic runner's
measured render/transfer workload. This is the renderer baseline; R8 must prove
the integrated stage, gameplay, loading, and audio frame budget.

### R6 — Production VDP2 stage and final scanout

Replace RP4 fixtures with source-derived scroll3 and scroll2 planes, HUD or
foreground only where evidenced, exact palette/priority ownership,
source-proven scroll changes, explicit 384-to-352 framing, and final VDP2
scanout. Captured strips remain regression fixtures. Frontend line scroll does
not block the gameplay slice unless the selected gameplay route requires it.

**Exit:** exact cell-map, scroll, priority, palette, object, crop, and final
scanout semantics in emulator readback and physical output.

### R7 — Audio and residency ownership

Replace the disabled/represented-only CDDA path with timed SCSP PCM, audible
CDDA, real drive ownership, zero data-track reads while CDDA owns the drive,
phase loading before music, arena canaries, live high-water, and underrun
diagnostics.

**Exit:** correct event timing, audible PCM/CDDA, no illegal overlap or
combat-time asset load, at least 15% live headroom, and no physical-soak audio
loss.

### R8 — Integrated physical capability slice

Build a normal `release-normal-release` image that cold-boots through the
declared route and plays the bounded encounter with controller input, one
player, class `0x1F` enemy, movement, attacks, collision/damage/HIT/KO, camera
and progression, final VDP1/VDP2 output, source palettes, PCM, CDDA, real
memory/load ownership, timing, latency, and the ten-minute soak.

**Exit:** all 12 capability conditions pass on the exact normal image with no
fallback. This proves the selected architecture for a quality playable port.

#### Non-gating post-slice quality calibration

After R8 passes, the completed slice may be compared with the isolated,
rights-owned MSHvSF reference using the same controller, console, display, and
capture chain where practical. Record the result as quality context only. It
does not block R9 or alter AvP's architecture or acceptance.

### R9 — Round 1 with one character

Expand encounter by encounter: freeze the next bounded MAME route, identify
only new writer dependencies, translate them into the same core, generate
phase assets, and repeat host/emulator/physical checks for new workload
classes. Complete all Round 1 enemies, interactions, boss, stage clear,
continues, and failure paths reached by the route.

**Exit:** Round 1 is fully playable on a normal release with no authored
gameplay fallback.

### R10 — Single-player game with one character

Apply the production pipeline across all stages. Physical coverage is required
for each new workload class: sprite peak, VDP2/line-scroll effect, phase load,
audio ownership pattern, boss/large actor, or worst-case collision/AI load.

**Exit:** cold boot to ending with stable pacing, complete audio, continues,
game over, all transitions, no diagnostic assets, and no authored fallback on
the supported route.

### R11 — Roster and multiplayer

The planned release scope is all three original playable characters and three
simultaneous local players through a documented Saturn multitap/controller
topology. Add that scope only after the one-character game is complete:
character routines/assets, multiple input devices, multi-actor camera/stage
behavior, join/continue/game-over behavior, worst-case resource loads, and
physical multiplayer soak. Any reduced scope requires an explicit user decision
and roadmap revision before R11 acceptance.

**Exit:** complete character and player-count parity for the selected release
scope.

### R12 — Release-candidate hardening

Produce repeated deterministic clean builds and the final manifest; remove
diagnostic profiles/fixtures; run multiple cold boots, full-route and
worst-encounter loops, audio soak, controller topology checks, and all
available loader/console combinations. Reconcile the source/evidence ledger.

**Exit:** candidate telemetry shows zero crash, fallback, canary, draw-end,
late-read, missed-field, and audio-loss failures over the declared soak.

### R13 — Release acceptance

Repeat the full acceptance matrix on the exact release image and archive its
hashes, commands, environment, captures, and provenance.

**Exit:** the release scope is reproducible, evidence-complete, physically
stable, and all declared release conditions are closed.

## 6. Capability slice conditions

| # | Condition |
|---:|---|
| 1 | Exact `avspu` identity and deterministic package provenance |
| 2 | Two identical cold-boot MAME gameplay oracle runs plus perturbation control |
| 3 | Controller input and one playable actor match semantic oracle |
| 4 | One class `0x1F` enemy update/animation matches, including HIT/KO repoints |
| 5 | Source collision, damage, hit response, and KO match |
| 6 | Camera/stage progression and 352 crop/framing contract match |
| 7 | VDP1 objects and VDP2 layers/priority/palette/final scanout match |
| 8 | SCSP PCM event path is audible and correctly timed |
| 9 | CDDA music is audible with no illegal data-read overlap |
| 10 | Live work-RAM/cart/VDP1/VDP2/SCSP high-water and canaries pass |
| 11 | Physical VDP1 draw-end, CPU/transfer timing, and input latency pass |
| 12 | Normal-release cold boot and ten-minute physical soak pass with no missed frame, corruption, or fallback |

No partial condition advances the count. Close a condition only when the exact
binary/profile hash, command, environment, tier, and evidence artifact are
recorded in `docs/research/CPS2_TO_SATURN_EVIDENCE_LEDGER.md`.

## 7. Full-port completion conditions

The port is complete only when all of these hold for the planned three-character,
three-simultaneous-player release scope:

- Cold boot reaches the complete game and ending through normal release flow.
- All selected characters and player counts have native gameplay parity with
  no authored or diagnostic fallback.
- Every stage, transition, continue, game-over, audio, and ownership path is
  present and source-proven.
- The AvP performance contract passes for every introduced workload class and
  on the final exact release image.
- Long full-route, worst-case, audio, and multiplayer soaks show zero declared
  failures.
- Clean builds are deterministic and the release manifest, provenance ledger,
  commands, environment, and physical evidence are archived together.

## 8. Parked work

Do not schedule these without a concrete AvP differential or profile that
requires them:

- More frontend presentation work before the gameplay slice.
- A general CPS-2 engine or broad static recompiler.
- Another whole-boundary mapping pass.
- A large legacy `main.c` cleanup.
- A dynamic composite cache or generalized linked VDP1 commands.
- Slave-SH-2 distribution.
- Full-route content expansion before the capability slice.
- More validator hardening without a concrete falsification.
- MSHvSF measurement as a prerequisite or acceptance gate.

## 9. Update rules

1. `project_state.yaml` is the machine-readable truth for accepted/candidate
   SHAs, disposition, hashes, blockers, condition statuses, gate count, accepted
   dependencies, and active task card.
2. This file is the only active roadmap. Do not create another plan of record.
3. The task card named by `project_state.yaml` contains only the first
   executable backlog body. Its status controls launch.
4. `docs/AGENT_HANDOFF.md` records the concise evidence checkpoint and current
   disposition; it does not accumulate future planning.
5. An accepted review advances the backlog and state together. Corrections stay
   on the same branch and worktree.
6. New mapping is demand-driven by a failing behavioral differential.
7. Verification and review depth follow the risk tier in `AGENTS.md`.
8. No roadmap status or gate advances without an exact artifact/hash, command,
   environment, evidence tier, and falsification result.
9. Structural, emulator, diagnostic-image, and physical-hardware evidence must
   remain labeled separately.
10. MSHvSF is an isolated, later quality calibration only; AvP's own contract
    decides architecture and acceptance.
