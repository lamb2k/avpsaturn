# Capability Gate 1 and full-game test plan

These are checks, not separate gates. Only the seven Capability Gate 1
conditions and nine full-game conditions in `docs/PARITY_PLAN.md` affect the
reported `0/7` and `0/9` counts.

Run the narrowest relevant checks first, then broaden. A host/focused success
never substitutes for the normal route or physical hardware.

The active presentation body's granular checks, RP0-RP12 dependencies,
content batches, and ownership are in `docs/ROUND1_EXECUTION_PLAN.md`. Package
checks and its shared-primitives check are scheduling evidence only; they do not
change Capability Gate 1 or full-game counts.

## Test-driven development evidence

Behavioral implementation follows the `RED -> GREEN -> REFACTOR` contract in
`AGENTS.md`. A package or autonomous-book chapter is reviewable only when its
report identifies:

- the exact base SHA, fixture/oracle, test file, RED command, and real failure;
- the test-first commit or an unchanged pre-existing test that fails at base;
- the GREEN commit, command, exact result, and broader regression tier;
- real mutation/perturbation controls that fail for the intended reason;
- every unavailable Saturn, emulator, audio, or hardware check as `UNRUN`.

If a new test already passes at the base, it has not isolated the requested
change. If a claimed negative control does not execute a mutation and compare
its result, it is not evidence. Documentation-only and mechanical changes may
use regression-first validation with an explicit `RED: N/A` reason.

Long coding-agent assignments use
`docs/AUTONOMOUS_EXECUTION_BOOK.md`. Their chapter results are candidate
evidence until Codex independently reproduces the relevant RED/GREEN chain and
accepts the complete book.

## Check A: deterministic source evidence

- Canonical ROM revision is US `avspu`; required private files and hashes are
  checked before decode.
- Stock MAME 0.289 route starts from a declared cold boot or exact state and
  records its full input schedule.
- Required evidence includes source registers/RAM/tables, not screenshots alone.
- Raw captures remain ignored; tracked manifests include semantic values,
  source addresses, counts, dimensions, and hashes but no copyrighted payload.
- Analyzer negative controls alter one source field/constant/frame and fail.
- Two independent generations produce byte-identical tracked manifests and
  generated-member hashes.

Current status: source graphics equality and several actor/collision manifests
pass; the complete no-skip presentation route and row-scroll table are open.

## Check B: native build, staged boot, and memory bounds

- Build with the bundled toolchain; do not assume Python or MAME is on PATH.
- Clean build after makefile/profile changes.
- `/0.bin` and `/GAME.BIN` match their ISO members exactly.
- `game.map` proves `__bend <= 0x060c0000`; checked sprite-array one-past ends
  also remain below the boundary.
- Debug and release builds obey the same memory bounds. Release-only success is
  failure.
- Live sprite registration high-water stays below 128. Expected static maximum
  from current lifetimes is 113; re-measure in focused and full routes.
- Visible pinned Yaba reaches loader status 5, `runtime_ready=1`, and an
  advancing world frame. A moving emulator frame or MSH2 in `slSynch` alone is
  not proof.
- Asset, allocator, palette, tile, sprite, RLE/decode, and missing-file counters
  remain zero unless a check explicitly expects a negative control.

Current status: staged boot reached `WAVE_ONE`; current dirty source and map need
the full clean rerun after presentation work.

## Check C: complete frontend and presentation

Accepted route:

`cold boot -> legal/QSound/Capcom/opening -> every story panel -> title wait ->
Start transition -> character select -> confirmation shutter -> Round 1 title
-> every Round 1 presentation scene -> results/intermission -> Round 2 title`.

### Evidence and conversion

- Capture every source-changed frame at cadence 1 with no story/test skip.
- Semantic manifest separates layer page/map, scroll/line scroll, priority,
  palette/fade, object, procedural mask, input/state, and audio changes.
- Runtime payload contains ROM-derived tiles/cells/maps/palettes/objects/timed
  operations; it contains no new captured framebuffer animation.
- Legacy `MENUFIT.BIN`, `CHARFIT.BIN`, `R1TITLE.RLE`, and the 13 route RLE holds
  leave runtime decisions only after replacements pass.

### Frontend provenance and colour

At exact held title, select, and Round 1 title frames:

- converter member equals ISO member;
- decoded RAM equals expected payload;
- NBG1 VRAM equals decoded surface;
- palette payload equals CRAM under the active registers;
- active bitmap size/colour mode, priority, palette offset, scroll, zoom, and
  CRAM mode match the manifest;
- unique RGB555 count fits the chosen representation;
- deliberate one-bank palette corruption fails.

Surface indices must be one-based `1..255` under Jo's palette contract; index
zero is reserved. Canary checks must prove that loading a surface or 4bpp
subpalette writes neither adjacent 256-entry CRAM block boundary. The rejected
zero-based/block-base workaround is a required negative control.

The active frontend path is indexed 8bpp. Do not test it as direct colour.

### Objects, geometry, and input

- System/user clip is exactly 352x224 with no crop, bars, vertical stretch, or
  stale border content.
- Title objects, Start plates/mask rows, three-frame cursor intro, all four
  cursor positions, confirmation blink/shutter, and Round 1 title match source
  geometry, order, palette, and timing independently.
- VDP1 explicit quads use inclusive bounds and read back exact source-fitted
  rectangles.
- Character select is non-wrapping 2x2; D-pad hold/release/boundary behavior and
  three-frame acceptance match source evidence.
- Saturn A/B/C confirm exactly once; unsupported cancel remains absent.
- Selected ID persists through gameplay initialization. Non-Warrior Warrior
  fallback is visibly and diagnostically `ADAPTED`.
- Title waits indefinitely for Start; attract remains deferred and must not
  accidentally run.

### Scene timing

- Host scene player reconstructs every changed source frame after RGB555
  conversion with zero unexplained difference.
- One-frame timing, palette, object, map, and input perturbations each fail.
- Confirmation shutter retains start 1885, four rows per edge per frame, centre
  131.5, and content rows 40-223 unless newer source evidence falsifies it.
- Normal route has no automated scene skip or static hold where source animates.

Current status: the safe one-based palette correction passes 25 held
CRAM/register observations with 22 exact surface comparisons, zero boundary
writes, and both palette controls failing as required. Twenty-five VDP1
schedules containing 44 objects pass geometry/colour/order/timing checks and
four negative controls. The complete 111-frame confirmation-shutter interval
and ROM-derived Round 1 title pass; `R1TITLE.RLE` is retired from that runtime
decision. Complete story/Round 1 scenes and the remaining legacy holds stay
open.

### Presentation package verification lanes

- **Fast lane:** deterministic generation/schema checks, targeted host
  reconstruction, negative controls, bounds, and `git diff --check`.
- **Batch lane:** full `test.ps1`, focused clean Saturn build, member hashes,
  controller route to the batch endpoint, live diagnostics, and resource
  high-water report.
- **Continuous-route lane:** clean normal route through the Round 2 title with
  every scene visited, no RLE fallback or late read, and every known mismatch
  classified in the variance ledger.
- **Presentation-parity lane:** zero unclassified cadence-1 intervals, exact
  timing/scroll/priority/palette/audio, full negative controls, and physical
  NTSC Saturn presentation evidence.

A shared-primitive failure invalidates all dependent batch results. Each
variance records a stable scene ID, source interval, category, source/native
behavior, measured delta, dependency, owner, closing check, and evidence label.

## Check D: parallax, layer priority, and 352x224 mapping

- Source capture records scroll2/scroll3 registers and the 1,024-word row-scroll
  window during static and moving-camera street spans.
- Layer-only street, door, interior, boss, results, intermission, and Round 2
  anchors record maps/tiles, colours, transparency, mutations, scroll, and
  object insertion priority.
- Saturn mapping uses scroll3/NBG1, scroll2/NBG0, VDP1 objects, and only
  source-proven NBG2/bounded VDP1 foreground.
- Production/RP4 profiles give NBG0 exclusively to the presentation manager;
  Jo printf is absent from NBG0 ownership in those profiles.
- Both planes use the common endpoint-aligned 384-to-352 transform with
  independent scroll. Source tiles are never fitted individually.
- Every generated PNT page maps to its own VDP2 page address and a camera
  boundary crossing proves the second page. Aliasing page 2 to page 1 must fail.
- Nonconstant source row scroll matches every affected Saturn scanline.
- VDP1 object priority uses the selected `SPCTL` sprite-priority encoding and
  `PRISA`-`PRISD` mapping relative to NBG0/NBG1. VDP1 Z or global screen order
  alone is not acceptable priority evidence.
- Deliberate zoom, one-row, palette-bank, and priority perturbations fail.
- Offline and live composites have no crop, bars, seams, stretch, or lost
  tilemap-above-object pixels.
- VRAM/CRAM/register readback matches the phase manifest.
- The captured RP4 object schedule is linked only by the focused StreetTest;
  normal builds prove that fixture absent and continue to use translated
  ROM-derived actor/object state.
- Bundle magic/version/offset/count/frame/page/object bounds reject corrupt
  controls safely. Runtime uses checked frame offsets or a monotonic cursor,
  performs immutable uploads only on activation/change, and records VDP1
  command and memory peaks.

Live readback records at least `CHCTLA`, pattern/map/plane controls, `PLSZ`,
`MPOFN`, scroll/zoom, `CYCA/B`, plane priorities, CRAM mode/offsets, `SPCTL`,
`PRISA`-`PRISD`, representative VDP1 command words, and resource/counter peaks.

Current status: RP4 frames 3474-3674 are measured and bundled through
`8fd75b3`. Scroll2 span is 176 and scroll3 span is 154. NBG0 has 1,596 cells
and 197 colours; NBG1 has 879 cells and 15 colours. The selected interval's
visible normalized row offsets are constant zero, so line scroll is unnecessary
for this fixture only. The dirty prototype contains candidate StreetTest-only
fixture staging, O(1) frame indexing, and sprite-priority class encoding. The
live mapping remains `ADAPTED`: NBG0/Jo ownership, second-page mapping, real
priority-1/priority-4 interleave, production-member exclusion, complete bundle
bounds, safe BSS/arena placement, and live resource/readback checks remain open.

## Check E: actor animation, rendering, and collision

- ROM program walk reproduces required animation-record pointer on every source
  frame. External pointer writers are translated when a program walk alone
  cannot reproduce transitions.
- Every promoted assembly passes the zero-difference pose check against an
  oracle; no-oracle assemblies remain excluded.
- Placement is derived independently from actor/source fields and passes the
  position check; captured coordinates are not runtime inputs.
- VDP1 command count/order, palette, flip, size, and texture residency match the
  semantic assembly.
- Collision uses the same current animation record as rendering.
- Player/enemy attack and hurt records, selector-zero behavior, damage, hit,
  reaction, KO, projectile/broadcast ownership, and stage collision pass
  controlled hit/whiff/edge tests.
- Unknown class/family/record/selector increments a `GAP` counter and is not
  treated as invulnerability.
- Frame ordering resolves collision, steps world, renders, and advances once.

Current status: street actor and defender subsets pass; complete player,
Stalker, boss, effects, attack/reaction/projectile, and stage coverage are open.

## Check F: translated behavior and stage systems

- Each translated 68000 routine has source entry/callers, fields, tables,
  deterministic fixture, static C translation, and semantic differential test.
- Arithmetic width/sign, control flow, side effects, animation-pointer writes,
  and PRNG algorithm/call ordering match or carry a named `ADAPTED` decision.
- Room 1 compares state/action/record transitions, decisions, movement,
  separation, attacks, reactions, spawns, hits, health, score, and audio.
- Stage scripts drive spawn schedule, camera, triggers, collision, doors, exits,
  items, scoring, results, and Round 2 transition.
- Hardcoded 5+3 lifecycle and inferred contact schedules retire only after their
  replacements pass.

Current status: open. Existing native model is adapted and remains a regression
route, not behavior parity.

## Check G: audio, residency, and performance

- F0/F1/G0 bundle manifests give exact bytes and lifetimes in work RAM, both
  cartridge banks, VDP1, VDP2, CRAM, and SCSP RAM.
- Jo whole-block allocation and fragmentation are accounted for.
- All data required during a CDDA interval is resident before playback; late
  data-read counter remains zero.
- Stage CDDA actually starts and is audible. PCM cues/voices use explicit SCSP
  ownership and do not freeze transitions or corrupt music.
- VDP1 command/texture peaks, VDP2 upload/line-scroll cost, DMA, CD seeks, and
  master/slave SH-2 frame time stay within measured 60 Hz budgets.
- Focused presentation and encounter profiles do not hide a normal-route peak.

Current status: incomplete. The current dirty runtime has stage CDDA disabled;
the final G0 and per-resource high-water ledgers do not yet exist.

## Check H: regression routes and physical hardware

Run in this order:

1. analyzer/converter self-tests and negative controls;
2. host unit/integration tests and deterministic soak;
3. full `test.ps1` and deterministic regeneration;
4. clean focused Saturn presentation profile, ISO member hashes, and live
   register/VRAM/CRAM readback;
5. normal digital-pad no-skip route through Round 2 title;
6. `-EncounterTest` through `COMPLETE`;
7. clean normal-release title boot;
8. physical NTSC Saturn route per `docs/HARDWARE_TEST.md`.

For Gate 1, retain the historical 4,485-model-frame and 12,000-frame soak as
regressions, but validate the new real frontend/presentation route separately.
Physical acceptance requires sustained 60 Hz and a ten-minute soak with an NTSC
Saturn, digital controller, and 32 Mbit expansion cartridge.

## Full-game continuation checks

After Capability Gate 1:

- add each round cumulatively and re-run title-to-current-endpoint;
- validate every selectable character through final boss, ending, and credits;
- validate all items, score, lives, continues, game-over, attract, options, and
  transition paths;
- validate original-player-count joins, HUD/score ownership, camera, spawn,
  collision, and worst-case rendering/audio/memory;
- run final clean single-player and multiplayer physical-hardware routes;
- complete the rights/licensing review before any distribution or promotion.
