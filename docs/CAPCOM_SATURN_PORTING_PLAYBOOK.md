# Capcom Saturn porting playbook

This is the reusable research method being trained with the official Marvel
Super Heroes vs. Street Fighter Saturn port while Alien vs Predator remains the
production target. It governs evidence quality; it does not import MSHvSF code,
assets, or unproven assumptions into AvP.

## Fidelity vocabulary

Every comparison uses exactly one classification:

- `MATCH`: same observed behavior and presentation within declared tolerance.
- `EQUIVALENT`: different implementation with the same observed result.
- `PLATFORM ADAPTATION`: a change required by Saturn media or hardware form.
- `OPTIMIZATION`: a measurable resource-saving change without accepted loss.
- `REDUCTION`: a documented loss of behavior or presentation.
- `ALTERATION`: an intentional observable change not explained by reduction.
- `ADDITION`: behavior or presentation absent from the CPS-2 reference.
- `BUG`: unintended behavior supported by reproduction evidence.
- `UNRESOLVED`: evidence is incomplete or competing explanations remain.

Confidence is separate: `HIGH` means deterministic reproduction, `MEDIUM`
means repeatable but incompletely mapped evidence, and `LOW` means a lead that
must not drive implementation.

## Evidence record

Each claim must contain:

1. Claim and semantic concept.
2. CPS-2 evidence with frame, address, table, trace, or hash.
3. Saturn evidence with frame, address, disc member, trace, or hash.
4. Deterministic test and expected result.
5. Observation that would falsify the claim.
6. Classification and confidence.
7. Explicit uncertainty.
8. Reusable AvP lesson and title-specific boundary.

A filename, screenshot resemblance, or unexplained RAM delta is never enough
to identify a subsystem.

## Workflow

### 1. Audit immutable inputs

Hash source media, validate manifests, record tool versions, and repair loader
packaging only in disposable overlays. Never rewrite the research inputs.

Acceptance: source hashes remain unchanged and a cold audit passes.

### 2. Define one semantic slice

Choose a short route that crosses multiple systems. The pilot slice is:

```text
idle -> walk -> jump -> normal -> Hadouken -> projectile collision
-> damage -> hit reaction -> recovery
```

Use a neutral human-controlled target to remove AI variance.

Acceptance: exact input edges, action order, and anchor-frame hashes reproduce.

### 3. Capture synchronized source evidence

Capture cadence-1 screenshots plus input edges, work RAM, object RAM, palette,
video registers, and audio writes. Analyze only derived reports in Git; keep raw
captures private and ignored.

Acceptance: every required stream covers the same frame interval without gaps.

### 4. Capture the official Saturn counterpart

Reproduce the same characters, spacing, controls, and action order. Capture
gameplay timing separately from rendered animation timing. Add SH-2, VDP1,
VDP2, SCSP, CD, DMA, work-RAM, and expansion-RAM evidence as instrumentation
allows.

Acceptance: cold replay is deterministic and all paired measurements have
declared tolerances.

### 5. Build correspondence before interpretation

Populate the correspondence database with evidence from both sides. Mark a row
`UNRESOLVED` until the pair exists. Record mechanical and presentation changes
independently in the difference ledger.

Acceptance: each non-UNRESOLVED classification has a passing falsification
replay and no unsupported hardware-responsibility claim.

### 6. Extract a reusable pattern

For each pattern record the problem, observed Capcom solution, hardware reason,
constraints, failure cases, and candidate AvP validation test. A pattern may
guide AvP only after the AvP test passes.

Acceptance: the lesson survives both the MSHvSF evidence and an AvP-specific
probe without weakening AvP route parity.

## Training exercises

1. Reproduce the CPS-2 report hash from a cold boot and explain every input
   edge without viewing the Lua route.
2. Identify the Ryu actor structure by proving ownership, writer path, and
   behavior under controlled movement; reject coincidental RAM deltas.
3. Map projectile creation through collision and damage, then falsify the map
   with a whiffed Hadouken.
4. Isolate normal, special, hit, and music audio paths on both systems.
5. Establish deterministic Saturn pad injection and capture the paired slice.
6. Classify each paired difference, keeping mechanics and presentation apart.
7. Produce one AvP validation probe from a confirmed pattern and demonstrate
   that it does not alter the AvP route contract.

## Candidate-title checklist

- Authorized, complete CPS source and official Saturn reference are available.
- Both versions can cold boot repeatably with pinned tools.
- A deterministic neutral-target route can be constructed.
- Source and Saturn state can be captured at useful cadence.
- Loading, memory, rendering, and audio stress cases are observable.
- Region, revision, expansion hardware, and controller configuration are fixed.
- Raw copyrighted inputs remain private and excluded from Git.

## Fidelity acceptance checklist

- Route and state-transition order match.
- Input latency, movement, collision, damage, hitstop, and reactions meet
  explicit tolerances.
- Animation coverage and timing are reported separately from mechanics.
- Sprite count, priority, clipping, background layers, effects, and palette
  behavior pass representative and stress scenes.
- Audio event, onset, source, voice behavior, and music transitions pass.
- Loading boundaries and worst-case stalls are recorded.
- Memory and hardware budgets have measured peaks and ownership.
- Every deviation is classified, evidenced, and either accepted or open.
- No unresolved MSHvSF inference is silently promoted into AvP.

## Current pilot result

The CPS-2 slice, Saturn package/boot, and Saturn controller route are
reproducible. Yaba Sanshiro's native play-record path now drives both controller
ports from a fixed backup state. Two cold replays produced byte-identical hashes
for all 25 anchors through Ryu idle, walk, jump, normal collision, visible
health response, Spider-Man hit reaction, and recovery.

That closes the deterministic-input exercise but not the full pilot slice.
Hadouken command acceptance and projectile lifecycle are intentionally deferred
to a second pass, and exact mechanics stay `UNRESOLVED` until RAM/state traces
produce paired measurements. The high-confidence reusable lesson remains the
method: immutable inputs, deterministic routes, synchronized evidence, explicit
uncertainty, and falsification before reuse.
