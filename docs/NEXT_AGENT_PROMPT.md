# Next agent prompt: finish S2 by proving the part-table walk, then integrate one real actor

Continue the private, native Sega Saturn port of the US CPS2 `avspu` revision
of Alien vs Predator. Use the `port-cps2-to-sega-saturn` skill and its linked
workflow. This is ROM translation into native SH-2 code, not a CPS2 emulator,
video player, capture-and-bind extension, or approximate animation demo.

Repository:

```text
C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest
```

Expected branch: `codex/avp-master-plan`.

This prompt authorizes **S2 only**. Do not begin S3 cast expansion, S4 collision
integration, S5 AI/PRNG translation, S6 hardware completion, stage-table work,
multiplayer, or another research lane.

## Why the project uses both S-steps and Capability Gate 1

Keep both names because they answer different questions. Do not call S1-S6
milestones or gates.

- **S1-S6 are execution steps.** Each step has narrow evidence checks that can
  pass independently. S2 answers: can one real actor select animation records,
  produce CPS2-equivalent semantic objects from ROM data, and render those
  objects through the native Saturn path?
- **Capability Gate 1 is acceptance.** Its seven conditions cover all of Round
  1 through the Round 2 title, including ROM-derived animation, collision,
  behaviour, stage systems, regression, and physical Saturn performance.
- Passing S2 does **not** close a Capability Gate 1 condition. One actor is not
  the complete Round 1 cast or route. Report S2 checks and Gate 1 status
  separately. At the start of this task, S1 is passed, S2 is active,
  Capability Gate 1 is 0/7, and the full-game goal is 0/9.

The word **gate** is reserved for Capability Gate 1. Use **check** for S2 pass
criteria. Older handoff sections mentioning milestones, phases, slice V, pose
gates, or hardware gates are historical records, not current terminology.

## Mandatory startup and repository safety

Read and verify in this order before changing anything:

1. `C:\Users\lambd\.codex\skills\port-cps2-to-sega-saturn\SKILL.md`
2. `C:\Users\lambd\.codex\skills\port-cps2-to-sega-saturn\references\workflow.md`
3. `AGENTS.md`
4. `CLAUDE.md`
5. `docs/GOAL.md`
6. `docs/AGENT_HANDOFF.md` completely. For S2, read these sections in their
   written order because later sections correct earlier claims:
   - `S2 integration - part 1 done, the object emitter decoded`
   - `Correction and live verification of the above`
   - `+0x2E resolved: the contradiction was a route-mixing bug`
   - `The object-entry geometry formula is now C, tested; bsr $0AA59A identified...`
   - `Status across S1-S6`
   - `S2 animation walk - interpreter VALIDATED, integration open`
7. `docs/PARITY_PLAN.md`, especially Naming, Capability Gate 1 progress,
   Master execution plan, How game logic gets translated, Sprite demand,
   retained slice-V design, and the CPS2-to-Saturn representation boundary.
8. `docs/TEST_PLAN.md` and `docs/HARDWARE_TEST.md`.
9. This file again, after the sources of record above.

Then record the live state:

```powershell
git status --short --branch
git log --oneline -10
git rev-parse HEAD
git branch --show-current
```

The verified ancestor immediately before this prompt correction was `1eb14af`.
Do not assume it is still HEAD; trust the commands. The worktree contains
intentional untracked one-off diagnostics such as `check_tail.py`,
`tools/diag_*`, `tools/probe_*`, `tools/mame_probe_emitter_pc.lua`, and
screenshot helpers. Preserve them. Preserve all ignored ROMs, MAME states,
captures, `nvram/`, `snap/`, generated assets, and build output.

Rules:

- Stay on `codex/avp-master-plan` unless the user explicitly authorizes a
  branch operation.
- Do not switch, merge, or cherry-pick the MSHvSF reference lane.
- Do not edit its separate worktree.
- Never run `git add .`, `git add -A`, `git clean`, a broad stash, reset, or a
  destructive checkout. Stage explicit paths only.
- Never commit ROMs, raw captures, generated copyrighted assets, emulator
  states, or disc images.
- Use the bundled Python or repository wrappers; do not assume Python or MAME
  is on `PATH`.
- Before stopping, terminate only MAME/emulator processes owned by this
  checkout. Do not kill another task's emulator.

## Direction of record and external architecture context

The following external findings inform architecture but do not replace AvP
evidence:

- There is no official Saturn Alien vs Predator. The fidelity oracle is always
  MAME 0.289 running CPS2 `avspu` under the same route and inputs.
- The isolated official MSHvSF Saturn-port study supports 16-colour bank mode,
  flip in VDP1 `CMDCTRL`, jump-next command linkage, and source order as draw
  order. It is method evidence from another game, not an AvP budget or a code
  source.
- AvP's own measured demand overrides the reference game's granularity: peak
  demand is 86 CPS2 objects / 909 16x16 tiles, 83.6% of objects are blocked
  sprites, and only 13 palettes are live at peak. Therefore the primary Saturn
  design is one VDP1 normal-sprite command per CPS2 object, with per-tile
  emission retained only as a measured fallback.
- CPS2 schematics and open FPGA cores are useful for priority, masking,
  palette, and video-timing questions. They do not contain AvP animation, AI,
  or stage logic and are not a reason to leave S2 for more research.
- Stock MAME debugger watchpoints have already been sufficient. A custom MAME
  build is a contingency only after a specific stock limitation is proven.

## Evidence labels

Use the repository's labels for every new assertion:

- `MEASURED`: read from an instrument or computed losslessly from it; name it.
- `DECODED`: produced by a validated decoder; name the source and test.
- `INFERRED`: a hypothesis; state exactly what would falsify it.
- `ADAPTED`: an intentional Saturn-port choice; explain why.
- `UNRESOLVED`: required but unknown; name the probe that will resolve it.

Do not promote an inferred field name into a C API or generated schema merely
because one frame looks plausible.

## Confirmed baseline: do not re-derive

### S1 actor and collision spine

- `avsp_actor.h/.c` mirrors the consumed fields of the game's `0xC0` actor
  record.
- The field loader passed 481,566 captured actor-field loads with zero
  mismatches.
- `avsp_collision.h/.c` reproduces the Python collision falsification on all
  eight counters.
- S1 is passed, but native gameplay still does not consume that collision path.

### S2 animation scripts and extracted records

- `avsp_anim_script.c` implements the validated 16-byte pose-record and 4-byte
  backward-jump walk.
- Free-running prediction reached a longest exact run of 732 frames.
- The extracted Saturn subset contains 614 reachable records in 63 sparse spans
  totalling about 10 KB and reproduces the full program-image interpreter on
  every recorded counter.
- `avsp_actor.c`, `avsp_anim_script.c`, and `avsp_emit.c` are in `makefile`
  `SRCS` and cross-compile for SH-2.
- None is yet called by `main.c`; the shipped runtime still selects the relevant
  actor poses through capture-derived schedules.

### Confirmed object-entry geometry

The Family-1 flipped emitter's geometry is coded in `avsp_emit.h/.c`:

```text
width = 16 * (((attr >> 8) & 0xF) + 1)
X = ((origin_x - width - dx) & 0x3FF) | or_value
Y = (origin_y + dy) & 0x3FF
```

The current host test proves expected X/Y for **three observed object entries**
at the route-matched frame-4214 case. It does not yet prove a complete
ROM-to-object conversion:

- `dx/dy` come from ROM at live-confirmed table addresses.
- `origin_x/origin_y` and actor `+0x2E` `or_value` come from route-matched live
  capture.
- `code/attr` are currently supplied by the captured oracle.
- A CPS2 object entry is four words: `[X, Y, code, attr]`. Do not call five
  objects “five object words.”

### Confirmed origin routine

- `bsr $0AA59A` at `0x0AA59A..0x0AA5E6` runs once per actor dispatch.
- It derives the `D1` flip mask from actor facing byte `+0x0F`, shifted into bit
  5.
- It computes the per-actor screen origin from world position minus fixed
  camera/scroll anchors, adjusted by one long read from the part stream, and
  writes the scratch origin at `(A5-0x64F4)`.
- The two camera-anchor values still need route-matched live reads if the native
  origin calculation consumes them rather than an already-normalized semantic
  input.

### Route-mixing lesson

`collision_probe` and `replay4200`/`enemy_actions` are different deterministic
routes. “Frame 4214” is not the same game state across them. Every comparison
must bind route name, state hash, source frame, input tail, actor address, and
sample timing. Never join evidence on frame number alone.

## The exact unresolved problem

S2 is blocked on the **general Family-1 part-stream walk**: where the stream
begins, how its header/count is represented, which entry the origin routine
consumes, how many 6-byte entries are visited, and whether any visited entries
are conditionally non-emitting.

For the frame-4214 alien pose:

- live capture confirms `A0=0x12F73C` for the first observed part and a 6-byte
  source-entry stride;
- observed source addresses include `0x12F73C`, `0x12F742`, `0x12F748`,
  `0x12F75A`, and `0x12F760`;
- the `0x12` jump between the third and fourth observed writes proves that two
  additional 6-byte source entries were consumed;
- the existing narrow watchpoint evidence does **not** prove whether those two
  entries emitted into object slots outside the watched range or were consumed
  without emission. Both explanations remain hypotheses;
- `bsr $0AA59A` consumes one part-stream long before the emitter loop;
- candidate 3-word headers at `extra=0..18` before the observed first part were
  already searched. Plausible-looking triples at extras 10, 12, 14, and 16 do
  not reconcile to the observed writes. Do not repeat that blind offset scan.

The flat `.deps/mame/actorprobe/disasm_full.txt` is a naive linear decode and
has already produced a confirmed instruction-boundary error. Capstone is an
instruction decoder, not an automatic control-flow oracle. If using it, decode
only reachable instructions while constructing a control-flow graph from the
confirmed entry at `0x0AA00E`, following branches, calls, returns, and jump-table
targets. Otherwise use a bounded live MAME step/watchpoint trace.

## Required execution sequence

Complete these bodies in order. Do not start a later body while an earlier
check is red.

### Body A: establish route-matched ground truth for the complete pose

1. Select one deterministic route and write down its state name/hash, anchor
   frame, post-anchor input tail, actor base, object-RAM bank, and frame mapping.
   Prefer the existing `replay4200`/`enemy_actions` route used by the emission
   proof. Do not mix in `collision_probe` data.
2. Widen or relocate the object-RAM watch window so every write produced by the
   target actor's dispatch is observed, including the two source entries hidden
   between the previous third and fourth watched writes.
3. At the handler entry and each source-entry iteration, record at minimum:
   source frame, PC, `A0`, `A1`, `A2`, `A4`, `A5`, `A6`, `D0-D4`, actor
   `+0x0E/+0x0F/+0x2E`, origin scratch, object write address, width, and data.
4. Record object-bank select `0x8040E0` and distinguish write buffer from active
   display bank. Preserve the full 8 KB bank dumps for before/after comparison.
5. Use the validation oracle only after the derivation data has been captured.
   The derivation must not copy expected four-word entry values into its output.
6. Conclude with one of two evidence-backed results:
   - the hidden entries emit elsewhere and the old watch window omitted them; or
   - they are consumed without emission and the precise branch predicate and
     control-flow address are proven.

If MAME cannot expose the required registers at the causing instruction, record
its known forward PC-reporting skew and capture at adjacent instructions. Do not
silently treat the reported watchpoint PC as the store instruction.

### Body B: recover the reachable part-stream algorithm

1. Starting at `0x0AA00E`, build a reachable-path disassembly/CFG. Enumerate the
   source of the loop count, the origin-routine call, each `A0`/`A2` advance,
   every conditional emission path, and loop termination.
2. Name every field only after a live register read or a control-flow read proves
   it. Keep unknown header words raw.
3. Implement a host-side diagnostic walker that accepts an assembly/record
   pointer plus actor/camera inputs and returns normalized semantic entries:
   position, tile code, palette, block width/height, flip, priority, and source
   order. The diagnostic may read private ROM/capture inputs but must not embed
   those bytes in a tracked report.
4. First reproduce all **five previously observed four-word object entries** for
   the frame-4214 pose. Then show the complete actor emission, including any
   additional entries the wider trace reveals.
5. Add an anti-hardcoding control using at least one different pose/part family
   from the same route. The existing frame-4253 evidence is suitable only if
   route, actor, bank, and sample timing are bound explicitly.
6. Run against the 5,302-frame oracle. Define the eligible population before
   computing results: frames and entries whose actor, record, route, and
   supported Family-1 format are attributable. Report total frames, eligible
   frames, eligible entries, exact matches, mismatches, and every exclusion by
   reason. S3 actors/formats may be excluded, but not silently.
7. The S2 source-walk check passes only with **100% exact agreement over the declared eligible
   population and zero unexplained mismatches**. A merely reported percentage,
   a high match rate, or tolerance-based result is not a pass. Expand the trace
   around any mismatch until it is explained or leave the check red.

The object-list comparison is exact because it validates the decoder. This does
not change the overall goal from functional parity to framebuffer-exact parity.

### Body C: promote the proven walk into reusable C

Only after Body B passes:

1. Generalize `avsp_emit.c/.h` or add a tightly named companion module for the
   part-stream walker. Keep source-machine decoding separate from Saturn VDP1
   command emission.
2. Preserve the semantic boundary: do not recreate the CPS2 `0x708000` buffer,
   bank flip, or packed representation as a Saturn runtime requirement.
3. Add bounds for bad pointers, unsupported selector/family, excessive entry
   count, destination capacity, and malformed termination. Return an explicit
   failure rather than clipping or guessing.
4. Keep C90, big-endian assumptions explicit, and SH-2 compatibility intact.
5. Add a focused host test using copyright-safe expected semantic values. It
   must cover:
   - flipped geometry;
   - code/attribute derivation rather than oracle passthrough;
   - palette contribution;
   - priority/size bits;
   - source ordering;
   - the proven hidden-entry behaviour;
   - malformed/bounds negative controls;
   - the second-pose anti-hardcoding case.
6. Wire the new test into `test.ps1` and run the strict host suite.

Do not call a result ROM-only if origin, code, attributes, palette, or priority
are still supplied from the expected output. State every remaining live input.

### Body D: integrate one street alien into the native runtime

Only after the general C walker and its host check pass:

1. Add one real `AvspActor` to the existing street-alien runtime slot in
   `main.c`; do not create a detached viewer actor or debug overlay.
2. Carry a live `anim_record`, call `avsp_anim_frame_tick`, and obtain pose
   assembly/object data through the proven ROM-derived path.
3. Until S5 translates action selection, seed the animation record on each
   existing action change from the current capture-derived schedule. Label this
   source explicitly `ADAPTED`; it is an integration bridge, not original AI.
4. Keep the capture-derived cel available only as a regression oracle or a
   deliberately selectable comparison path. It must not secretly remain the
   visible production actor while the ROM actor merely updates off-screen.
5. Preserve current input, HUD, camera, audio, 352x224 mapping, allocation, and
   route behavior. This task changes one actor's animation/render source, not
   the whole platform pipeline.

### Body E: implement the real per-object VDP1 consumer

Do not substitute a marker, box, repositioned old cel, or screen-captured pose.

1. Emit one VDP1 normal-sprite command per normalized CPS2 object.
2. Use `nx*16` by `ny*16` dimensions, 16-colour bank mode, flip in `CMDCTRL`,
   jump-next linkage, and source order as draw order.
3. Build contiguous per-block textures from referenced 4bpp tiles through a
   cache. Track key, residency, palette, dimensions, flip treatment, VRAM
   address, last use, and upload size.
4. Preserve transparency and palette identity. Do not flatten priority/order
   into a precomposed actor cel.
5. Bound command count, VDP1 VRAM, texture uploads, CRAM banks, work RAM, and
   cartridge residency. Record measured high water rather than estimates alone.
6. If per-object cannot hold 60 Hz on the eventual hardware measurement, retain
   per-tile as the explicit fallback and measure it. Do not redesign the actor
   spine first; producer and consumer are intentionally separate.
7. Obtain an unambiguous paused/frame-stepped visual comparison against the
   route-matched MAME frame. A live autoplay screenshot race is not evidence.

If the session cannot finish this body convincingly, stop after a clean Body B,
C, or D checkpoint. Do not leave a half-confirmed renderer in `main.c`.

## S2 checks

S2 passes only when checks 1-3 are all green:

1. **General source walk:** the header/count/advance/emission mechanism is
   proven; all five previously observed object entries and the complete widened
   target-actor emission derive without expected-output constants; the declared
   eligible subset of the 5,302-frame oracle matches exactly with zero
   unexplained mismatches.
2. **Live actor integration:** one street alien in `main.c` carries and advances
   a real `AvspActor`; its semantic object list comes from the proven source
   walker, with only action selection explicitly labelled `ADAPTED` pending S5.
3. **Real Saturn rendering path:** that list is consumed by the per-object VDP1
   path at an honest basic fidelity level, with route-matched visual evidence;
   no placeholder and no capture-derived actor cel supplies the claimed result.

The following measurement is required work but may be explicitly deferred to a
named follow-up without claiming it happened:

4. **Throughput measurement:** measure the 86-object / 909-tile peak case at
   source frame 5776 on physical Saturn or a named close proxy. Report command
   count, texture-upload bytes, VDP1 VRAM high water, frame time, and missed
   frames. Emulator timing is indicative only. Physical Saturn remains
   Capability Gate 1 condition 7 and cannot be closed by a proxy.

Passing S2 keeps Capability Gate 1 at 0/7 and the full-game goal at 0/9.

## Verification order

Run the narrowest applicable check after each coherent change, then broaden:

1. Python analyzer/CFG tests and deterministic regeneration check.
2. Focused C host test for the part walker/emitter.
3. Full `test.ps1`, including actor, collision, animation walk, emitter, route,
   and 12,000-frame soak.
4. Saturn cross-compile/build for the changed sources.
5. Focused one-actor diagnostic profile, if one is added, with ISO member
   size/hash verification.
6. Full `-EncounterTest` route through the Round 2 title to prove no regression.
7. Rebuild `normal-release` last and boot from title/menu using the exact cue.
8. Record audio status even though S2 should not change audio.
9. Defer or run physical/proxy timing explicitly; never imply hardware proof
   from Yaba Sanshiro.

Inspect the emulator process command line before judging a boot because it may
retain stale disc state. Do not overwrite the normal-release image with a
diagnostic image and leave it mislabeled.

## Prohibited shortcuts and known failure modes

- Do not compare different deterministic routes by frame number.
- Do not treat the flat disassembly as control-flow truth.
- Do not rerun the already-failed header-offset scan at extras 0..18.
- Do not call the current three-entry geometry test a complete ROM-only object
  decoder.
- Do not describe five four-word entries as five object words.
- Do not accept a high match percentage; S2's eligible oracle population must
  be exact or the check remains red.
- Do not hand-code a part count, hidden-entry skip, code, attribute, palette,
  origin, or priority from frame 4214/4253.
- Do not extend capture-and-bind for new actions.
- Do not begin S3/S4/S5 because one pose renders.
- Do not implement or ship a CPS2 emulator.
- Do not revive the custom-MAME build without documenting a concrete stock
  limitation.
- Do not claim physical-hardware success without a real NTSC Saturn run.

## Checkpoint and handoff requirements

Commit only coherent, passing pieces. Suggested boundaries are:

1. tracked, reproducible part-stream analyzer/trace report with Body B exact;
2. generalized C walker plus strict host tests;
3. one live `AvspActor` integrated without visual claims;
4. real per-object VDP1 consumer plus unambiguous visual evidence.

Before every commit, inspect `git status`, stage explicit paths, and ensure no
private/raw/generated content is staged. Before stopping, update
`docs/AGENT_HANDOFF.md` with:

- branch, HEAD and relevant parent checkpoint;
- tracked and untracked dirty files;
- exact route/state/input/actor/bank provenance;
- raw evidence path and SHA-256 values;
- exact commands and outputs;
- match population, exclusions, mismatches and negative controls;
- what is `MEASURED`, `DECODED`, `INFERRED`, `ADAPTED`, or `UNRESOLVED`;
- host/build/focused/full-route/normal-release/hardware status;
- disc profile and stable member hashes where applicable;
- running MAME/emulator processes or confirmation none remain;
- the first ordered command for the next session.

Update `docs/PARITY_PLAN.md` only for durable direction/status changes. Do not
rewrite historical evidence merely to make the narrative shorter.

## What follows S2, but is not authorized here

- S3 widens the same proven spine/renderer to the player, remaining street
  aliens, Stalkers, and Chrysalis and demotes their capture-derived archives to
  regression oracles.
- S4 integrates the already-decoded game hitboxes/damage path and retires the
  inferred Chrysalis 21/55/97 and Stalker contact schedules.
- S5 translates street-alien decisions and PRNG use, replacing S2's explicitly
  `ADAPTED` action-pointer seeding.
- S6 integrates the room slice and validates it on hardware.

Do not advance to those steps during this task.
