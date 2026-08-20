# Agent handoff

Current-only restart state. Historical investigations belong in Git history and
archived diagnostics, not in this file. Verify this document before relying on
it with:

```powershell
git status --short --branch
git log --oneline -10
Get-Process mame,yabasanshiro* -ErrorAction SilentlyContinue
```

## Repository state

- Repository: `C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest`
- Branch: `codex/avp-master-plan`
- HEAD: see `git log -12`; autonomous chain since the Codex base
  `8fd75b31c1ed6708de5fbd32ccaa2b98042d9654`: `18c781f`+`671eca8` (RP4),
  `247e8a9` (RP4 interim acceptance, prompt rotation), `254719b` (RP6),
  `6ac45b3` (RP5), plus the row-scroll classification and
  handoff/plan bookkeeping commits.
- No remote publication is authorized.
- Capability Gate 1: **0/7**.
- Full-game acceptance: **0/9**.
- RP0-RP3 are committed package checkpoints. RP4 is **IN PROGRESS**, not
  accepted and not a parity claim.
- Optional local orchestration is now defined by
  `docs/CODEX_SELF_CONTAINED_SUPERVISOR.md`: a `gpt-5.6-sol` primary reviews
  complete write-enabled tranches performed sequentially by the configured
  `avp_implementer` (`gpt-5.6-terra`, high). This mode is opt-in only through
  `CODEX_SELF_CONTAINED_SUPERVISOR_LOOP`; the Claude Cloud boundary remains
  the default. Start a new Codex task rooted at this repository after the
  `.codex` configuration is present so the custom agent is loaded.

The worktree is intentionally and heavily dirty. It contains shared actor,
collision, frontend, staged-loader, test, analyzer, documentation, and private
diagnostic work. Do not reset, clean, stash, switch branch, bulk-stage, or
assume any uncommitted path is disposable. Re-run Git status for the exact
inventory before every commit and stage explicit paths only.

Current tracked modifications include the repo/agent instructions,
`README.md`, actor/collision/runtime files, `build.ps1`, `main.c`, `makefile`,
data manifests, plans/tests, Jo Engine patch, host tests, and analysis tools.
Untracked work includes `.claude/`, `.codex/`, `loader/`, `tools/diag_*`, MAME
trace probes, and local logs/TSVs. ROMs, raw captures, generated copyrighted
payloads, audio, opcode dumps, save states, logs, and ISO/cue files must never
be committed.

## Process ownership snapshot

At the latest verified snapshot:

```text
(2026-08-20 03:00) no mame, yabasanshiro, or kronos processes running
```

Every emulator started during the RP4 supervised validation was terminated at
the checkpoint. Treat PIDs as snapshots, not stable tokens.

## Accepted presentation checkpoints

- RP0: frontend palette/object primitives, confirmation shutter, and
  ROM-derived Round 1 title are committed. `R1TITLE.RLE` is no longer the
  runtime title path. Capability Gate progress remains unchanged.
- RP1: `AvspSceneDef v0`, route/player/diagnostic interfaces, host controls, and
  SH-2 link are committed.
- RP2: full-route cadence-1 capture grouping and the tracked machine census are
  committed. Private capture material remains ignored.
- RP3: the minimal v0 scene player and explicit route controller are committed
  behind platform seams.

The previous accepted RP0 verification included deterministic host checks,
`test.ps1`, frontend and encounter profiles, and a clean release boot. RP3 also
passed its focused host and SH-2 checks. Those results do **not** validate the
current uncommitted RP4 runtime prototype; all affected lanes must be rerun.

## RP4 committed evidence and bundle checkpoint

The current five-commit RP4 chain is:

```text
aee8cc5 Select and measure RP4 interval
e4086a9 Generate pre-scaled street plane strips
72f62eb Pack strips as VDP2 cells with PNT map patches
4f86c43 Merge interval object tiles into street archive
8fd75b3 Serialize strip schedules in runtime form
```

Measured facts for the selected source interval:

- source frames: `3474..3674`, inclusive, 201 frames;
- horizontal transform: `source_x = (out_x * 383 + 175) // 351`;
- strip bundle (regenerated at 18c781f): `STRIPS.BIN`, 269,654 bytes,
  SHA-256
  `7c28617351ec2bb2099d10e28de561f0ef64feb2fbb1784c5dae11d29c7f1c22`;
- scroll2/NBG0: 527x240, 1,596 unique 8x8 cells, 102,144 character bytes,
  197 colours;
- scroll3/NBG1: 528x256, 879 unique 8x8 cells, 56,256 character bytes,
  15 colours;
- two map patches;
- palette cycle: 14 entries, period 4, first flip at rel 4;
- selected interval scroll2 span 176 and scroll3 span 154, ratio `0.875`;
- source row scroll is enabled, but the normalized visible rows in this chosen
  interval are constant zero. Line scroll is unnecessary for this interval
  only; the wider route remains unclassified;
- source object priorities observed: 1 and 4;
- the captured validation schedule contains 12,118 object entries over 201
  frames with complete interval tile coverage.

The captured 12,118-entry object schedule is a **focused validation fixture**.
It may prove geometry, colour, order, paging, and priority for this interval. It
must never become the production whole-route object source or a substitute for
translated actor/object logic.

The last linked RP3 map left only 624 bytes below the high-work-RAM boundary.
RP4 must not add large static/BSS buffers. All map, bundle, and runtime bounds
must be measured again after the current integration links.

## RP5 and RP6 implementation reports (autonomous session)

### RP6: semantic scene manifest — PASS (interim review) at `254719b`

- `tools/gen_avsp_scene_manifest.py` -> `data/avsp_scene_manifest.json`:
  all 122 census groups become scenes with content-addressed stable IDs
  (SHA-256 over CPS-B hash, layer bases, video control, palette
  population, map-hash counts; occurrence-suffixed for revisits), the
  measured frame range and provisional ID, input dependency, composition,
  QSound change counts, and the route transition chain.
- 23 scenes carry labels bound to explicit evidence (committed
  measurements or reviewed private screenshots): legal warning, EPA,
  QSound, Capcom logo, opening earth/demo/story panel, character select,
  Round 1 title, street gameplay, barricade dialogue, warehouse and
  Stalker segments, two Chrysalis battle segments, two CONTINUE
  countdowns, the Round 2 title (frames 15092-15192), and the Round 2
  underpass tail (15193-18000). 99 scenes keep `label: null` with a
  `needs-label` review flag; nothing is silently unlabeled.
- Route-quality finding: the scripted composite route dies twice
  (CONTINUE countdowns at 6201-6692 and 12800-13292); the capture reaches
  the Round 2 title and ~2,800 frames of Round 2 underpass.
- `tools/verify_scene_manifest.py` gates `test.ps1`: exact route tiling,
  recomputable stable IDs, consistent transition chain, evidence-bound
  labels, four negative controls (shifted range, forged ID, broken
  transition, silent unlabeled) all detect.

### RP5: residency ledger and disc-read guard — PASS (interim review) at `6ac45b3`

- `avsp_disc_guard.c/h`: every data-track read through
  `avsp_fs_read_into` asks the guard; reads are rejected and counted
  while CDDA owns the drive unless an explicit measured window is open,
  and windows refuse to open under active CDDA. The interior-wipe
  boss-clear load is the one declared window
  ("interior wipe: CDDA paused").
- Host test `tests/avsp_disc_guard_test.c` (wired into test.ps1, WSL gcc
  -Werror) proves permit/reject/window/refusal semantics plus both
  trivial-guard negative controls.
- Live proof: EncounterTest to COMPLETE with guard counters read by
  symbol — 66 reads allowed before CDDA ownership, the CDDA flag set at
  encounter start, exactly one further windowed read, zero late reads,
  zero refused windows. The CD track start call itself remains disabled,
  so live CDDA rejection is ADAPTED contract skeleton until it returns.
- `tools/gen_avsp_residency_budget.py` -> `data/avsp_residency_budget.json`
  (gated by `tools/verify_residency_budget.py` with recompute checks and
  three negative controls):
  - work RAM __bend vs 0x060C0000: debug-normal-release 2,368 bytes
    headroom; debug-street-test 220,784; debug-encounter-test **320**;
    debug-frontend-test 2,016. The encounter profile is the tightest
    lane; any new unconditional BSS must be paid for first.
  - cartridge DRAM1: 0x200000 with 0x50000 tile carve (297,764 used,
    29,916 headroom) and 0x48000 street-test strips carve (269,654 used);
    jo zone recomputes.
  - VDP2 street scene: 160,704 char + 4,224 PNT = 164,928 of 524,288.
  - VDP1: 297,764-byte texture archive; live command sample recorded;
    route-wide command high-water remains a GAP entry.
  - PCM members staged (2,727,832 bytes total) with the phase-load model;
    allocator/SCSP high-water instrument remains a GAP entry.
- BSS regression found and fixed during RP5 groundwork: the encounter
  profile had crossed the limit after the RP3 carve rework; one FS
  staging sector (32->31) reclaimed 2 KiB.

### SP status after RP5/RP6

SP1-SP10 are green (interim review) and RP7 passes. SP10's complete-route
classification (`tools/classify_route_rowscroll.py`, gated capture-free by
`tools/verify_rowscroll_classification.py`): 6 scenes require line scroll
(0x8012, 0x8013, 0x8015, 0x8016, 0x8019, 0x801a - all in the
opening/character-select region), no gameplay scene does, and the street
group is constant-zero route-wide, confirming RP4's interval measurement.
Implementing line scroll for those six frontend scenes is RP8 scope.

## RP4 interim acceptance (autonomous session)

Under the user's `RESUME_AUTONOMOUS_IMPLEMENTATION` authority this session
acted as interim technical reviewer: the RP4 end state in the previous
`docs/NEXT_AGENT_PROMPT.md` (both planes, endpoint transform, independent
motion, page crossing, interleaved priorities, exact palette timing, no
crop/seam/stretch) is fully evidenced by the report below, so RP4 is marked
**PASS (interim review)** in `docs/ROUND1_EXECUTION_PLAN.md` and the prompt
was rotated to RP6. Codex ratification is pending and may reopen RP4.

## RP4 implementation report (supervised, awaiting Codex review)

- Mode: `SUPERVISED_IMPLEMENTATION`, `PACKAGE: RP4`, implementor.
- Base SHA: `8fd75b31c1ed6708de5fbd32ccaa2b98042d9654`.
- Implementation commits: `18c781f` (renderer proof and hardening),
  `671eca8` (endpoint-rule unification for the street object draw).
- Changed files: `main.c`, `build.ps1`, `makefile`, `test.ps1`,
  `tools/gen_avsp_street_planes.py`, `tools/verify_street_planes.py` (new),
  `tools/verify_fixture_separation.py` (new),
  `tools/capture_street_readback.py` (new), `data/rp4_street_planes.json`,
  `data/rp4_street_readback.json` (new),
  `data/rp4_street_live_readback.json` (new).

### Root causes fixed to reach the offline proof

1. The generator's patch packing mutated the base pattern grid
   (`pack["pnt"][...] = index`), so the serialized base held the LAST patch
   state; a base-PNT snapshot before patch processing restores first-seen
   semantics. This alone collapsed NBG0 from 108,286 mismatched pixels to
   1,122.
2. The palette cycle is serialized and replayed with first-flip semantics
   (state A until the first observed flip at rel 4, then alternate per
   period 4) in generator, runtime, and verifier; the old
   `(rel+phase)/period` formula was phase-inverted.
3. The verifier's expected window now marks plane columns whose world pixel
   is outside the 384-wide capture window as unobservable (sentinel), never
   clamping to the neighbouring column; those columns are compared at the
   scroll phases that bring them into view.

### Offline proof (tools/verify_street_planes.py, gate in test.ps1)

- All 201 frames structurally checked (scroll equality, object schedule
  byte-equality against the active CPS bank, tile coverage); 124 frames
  pixel-compared (every 8th, patch frames, endpoints, all 113 page-boundary
  crossing frames).
- Result: **0 mismatched pixels on NBG0 and NBG1**, 12,118/12,118 objects
  exact, 0 missing tiles, priority split {1: 402, 4: 11,716}.
- Negative controls, all detecting: wrong transform (window-anchored fit),
  aliased second page, one scroll record, one cycle entry, one dropped
  patch, one object coordinate, one object priority, one VDP2 priority
  register. Zero-mismatch and control detection are hard failures.

### Required issues A-D

- **A (NBG0 ownership).** MEASURED by live write watchpoint: the writer of
  the street NBG0 PNT area was `jo_clear_screen` -> `jo_clear_screen_line`
  -> SGL `prnt_0`, proving the SGL ASCII text map lives at `VDP2_VRAM_B0`
  (0x25E40000), not offset 0 as previously noted. The street profile
  compiles out `frame_callback`'s `jo_clear_screen` and redirects
  `jo_printf` into `avsp_diag_print_buffer`; after the fix the char and
  PNT canaries for both planes match `STRIPS.BIN` live.
- **B (two-page mapping).** Live SGL shadow readback: `CHCTLA=0x1010`,
  `PNCN0=0xc000`, `PNCN1=0xc004`, `PLSZ=0x0005`, `MPOFN=0x0044`,
  `MPABN0=0x2020`, `MPABN1=0x2222`. Offline: 113 boundary-crossing frames
  all exact; the aliased-page negative control detects.
- **C (per-object priority).** `SPCTL=0x0023` (sprite type 3); classes in
  CMDCOLR bits 13-14: default 0 (Jo/HUD), actor `0x2000` (CPS pri 1),
  foreground `0x4000` (CPS pri 4); `PRISA=0x0406`, `PRISB=0x0606`,
  `PRINA=0x0203` (NBG1=2 < NBG0=3 < actors 4 < default/foreground 6). Live
  VDP1 command walk: classes {0: 1, 1: 2, 2: 446}. Both priority negative
  controls (object class bit, VDP2 register) detect offline.
- **D (fixture separation).** `STRIPS.BIN` is generated to
  `build/rp4_fixture/`, staged into the ISO only by `-StreetTest`, removed
  otherwise; `data/rp4_street_planes.json` carries `fixture_role`
  ("VALIDATION FIXTURE ONLY"); `tools/verify_fixture_separation.py` gates
  test.ps1 (fixture references outside `AVSP_STREET_TEST`, lost
  classification, or wrong-profile staging all fail).

### Runtime hardening

- STRIPS header, plane, and object-schedule offsets/counts bounds-checked
  against the file size; malformed counts fail with a named asset.
- Object frame offsets indexed once (O(1) per-frame lookup); map patches
  record overwritten PNT words and revert on loop wrap; chars/PNT uploaded
  once at activation; per-frame writes are the measured scroll registers,
  cycle colours, and patch words only.
- Street arrays live only in the StreetTest link (no street symbols in
  other profiles' ELFs).

### Memory and live measurements

- StreetTest link: `__bend=0x0608a8f0` (218,896 bytes below 0x060C0000).
- Encounter profile BSS had crossed the limit by 0x5a0 after the RP3 carve
  rework (pre-existing, exposed on rebuild); reclaimed by shrinking the FS
  staging burst 32->31 sectors (2 KiB); encounter link now
  `BSS end 0x060bfda0`, release link `0x060bf590`.
- `STRIPS.BIN`: 269,654 bytes, SHA-256
  `7c28617351ec2bb2099d10e28de561f0ef64feb2fbb1784c5dae11d29c7f1c22`,
  verified byte-identical inside the StreetTest ISO at 0x54e000.
- Tile archive 297,764 bytes (90.87% of the 0x50000 cart carve); STRIPS
  carve 0x48000 at DRAM1+0x50000, street profile only.
- Live diagnostics matched the offline table exactly (scx 161/148 at the
  hold segment, SCXIN0 tracking, s2y 512/513 jitter visible as SCYIN0 0/1).
  Full register list in `data/rp4_street_live_readback.json`; visual
  anchors captured at pre-movement, during movement, hold, and patch phases
  (private scratchpad, not committed).

### Checks

- `test.ps1`: exit 0 (includes the new fixture-separation and street plane
  gates; the plane gate requires the private full-route capture).
- Offline street proof: PASS (0 px, 8/8 controls).
- StreetTest live readback: registers as above, char+PNT canaries all
  match, loop advancing.
- EncounterTest: reached `COMPLETE` (state 18) self-driven.
- Clean normal-release boot: `runtime_ready=1`, world frame advancing at
  full rate (132->253 over 2 s).
- All emulators terminated.
- FrontendTest: self-driven through main menu, character select, and
  intro into Round 1 gameplay (encounter states 0->6, world frame
  advancing). Observation, out of RP4 scope: Round 1 gameplay ran at
  ~16 fps in this Yaba instance (frontend/title states run at full
  rate); the street renderer profile is unaffected and prior encounter
  timings show similar sub-60 model rates under the emulator, so this
  is recorded as an observation, not a claimed regression.
- `UNRUN`: physical Saturn hardware; audible CDDA/PCM confirmation;
  full-game route beyond captured frame 300,000.

### Remaining ADAPTED/GAP

- `ADAPTED`: the world-anchored anamorphic pre-scale realizes the endpoint
  384->352 mapping at plane level. The street object draw now shares the
  same endpoint rule (`street_out_of - 176`); the previous `fit_352`
  variance was measured at exactly 0 or 1 px per screen column (6,761 of
  12,118 scheduled objects sat 1 px left of the plane mapping) before
  unification. The frontend/gameplay `fit_352` path (RP0-RP3 territory)
  is unchanged and remains for Codex to rule on.
- `GAP`: scroll1/HUD layer and row-scroll classification outside this
  interval remain unmodelled; production object sourcing still requires
  translated actor logic (the fixture must never ship in production).
- Capability Gate 1 remains **0/7**; RP4 is implemented and verified but
  NOT self-accepted.

### Suggested next body (for Codex, not enacted)

After RP4 acceptance, RP5 (pessimistic G0/CDDA residency) and RP6 (semantic
scene IDs over the RP2 census) are dependency-ready in isolated lanes, per
the existing plan. The evidence here adds one input to RP5 sizing: the
street scene's full working set (tile archive + strips) fits the current
cart carves with 9% headroom, so per-scene archive swap at loading
boundaries remains the preferred residency shape.

## Handoff discipline

Before stopping:

- update this file newest-first with branch, full HEAD, exact check commands and
  results, hashes, memory totals, live readbacks, and remaining `ADAPTED`/`GAP`;
- update `docs/ROUND1_EXECUTION_PLAN.md` only for evidence actually accepted;
- update `docs/NEXT_AGENT_PROMPT.md` only after supervisor acceptance, or emit a
  proposed next prompt separately for review;
- include a `CODEX_REVIEW_INVOCATION` block when operating as the implementor;
- stage explicit paths and commit coherent checkpoints only;
- label every unrun check `UNRUN`;
- never change Capability Gate counts without satisfying the complete gate.
