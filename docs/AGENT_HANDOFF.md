# Agent handoff

Current-only restart state. Historical investigations belong in Git history and
archived diagnostics, not in this file. Verify this document before relying on
it with:

```powershell
git status --short --branch
git log --oneline -10
Get-Process mame,yabasanshiro* -ErrorAction SilentlyContinue
```

## RP4 direct-order supervisor checkpoint, 2026-08-20 (newest first)

Branch `claude/rp4-priority-architecture` was clean at `1cd021b` before this
supervisor documentation checkpoint. The accepted evidence remains:

- CPS2 source order and object identity are measured;
- final VDP1 command memory is readable;
- the old reverse/forward equal-Z `slDispSprite` experiment emitted 528
  commands in the same final order (510 comparable sprite commands and
  129,795/129,795 order-preserving pairs), so that mechanism is refuted;
- object-versus-plane composite controls remain blocked and may not be
  promoted from command-table evidence;
- RP4 v1 remains `FALSIFIED`; Capability Gate 1 remains `0/7`.

Codex inspected Jo/SGL and selected the lowest-risk first candidate:
`jo_sprite_draw(..., billboard=true, screen_doors=true)` reaches
`slPutSprite`, whereas `jo_sprite_draw3D` reaches the measured sorted
`slDispSprite` path. A three-file candidate (`build.ps1`, `makefile`, `main.c`)
was compiled successfully with an old-sorted feature control, but it was not
accepted or committed. The edits were reverted exactly after the bounded run.
The candidate artifacts remain ignored at
`private-evidence/rp4-owned-order/owned-reverse/`:

```text
game.iso sha256 bd874666def117a4583533c68b3a68fcba381dadfb3256cb52b60c57ce19c104
game.elf sha256 cbdbc236708c92def6f505d0d25e6935309b3a2162a3dca347e74624dadb3ee1
```

The candidate was **UNRUN**, not failed. Two hidden pinned-release launches
never reached the StreetTest readiness predicate within 600 seconds:
`avsp_diag_runtime_ready=0`, `avsp_diag_street_objects=0`,
`avsp_diag_street_frame=0`, empty print buffer. The second command line was
verified as:

```text
yabasanshiro.exe -nb -a -i "C:\Users\lambd\AppData\Local\Temp\AvPSaturnCapabilityTest\game.yaba.cue"
```

The master SH-2 was executing at `PC=0x06002E00` (`bra 0x06002E20`), with
`SP=0x06002000` and `VBR=0x06000000`; the slave SH-2 remained all zero. The
first launch also exposed a real PowerShell defect: an unquoted cue path was
flattened by `Start-Process`. Quoting fixed the command line but not the guest
readiness failure. Because the candidate draw call cannot execute before the
street renderer is live, this does not distinguish a candidate defect from a
stale disc/config/boot-harness failure. No command capture was produced. All
Yaba/MAME processes were stopped.

The next body must begin with a known-good unchanged `1cd021b` StreetTest boot
and an intentional invalid-disc negative control before rebuilding the
`slPutSprite` candidate. Do not spend another 600 seconds on a candidate until
the base control reaches `runtime_ready=1`, `street_objects>0`, and an advancing
fixture frame with the exact ISO/ELF hashes recorded. The complete decision
book is `docs/NEXT_AGENT_PROMPT.md`.

Work is now governed by the sequential Codex-supervisor/Claude-implementor
protocol in `AGENTS.md`. Codex owns the architecture and disposition; Claude
executes the bounded book and may stop only at its named architectural hard
stop.

## Official 1.20.37 source: reference instrument only, 2026-08-20 (newest first)

This supersedes the **scope**, not the factual record, of the prior
`be24dbf` scanout-equivalence note. Branch
`claude/rp4-priority-architecture` began this repair at `be24dbf`; the
official archive/source/release hashes, wrong-base and corruption controls,
fresh patch, apply script, build script, and standalone tests now form a
reproducible **REFERENCE_INSTRUMENT_ONLY** checkpoint. Its ignored inputs are
`.deps/source-archives/yabasanshiro-src-1.20.37.zip` and fresh extractions
under `.deps/yb-official-*-20260820`; no source tree, build, executable,
scanout, or raw guest data is tracked. Run its narrow checks with:

```powershell
$py = "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $py tests\test_yabasanshiro_1_20_37_scanout.py
& $py tests\test_yabasanshiro_1_20_37_equivalence.py
```

The recorded RED was
`& $py tests\test_yabasanshiro_1_20_37_scanout.py`, exit 1:
`official scanout verifier: FAIL: official patch hash mismatch`. The repaired
GREEN reran that command twice from unchanged clean inputs, exit 0 both times,
with corrupt archive, wrong-version, dirty/already-patched preimage, mutated
patch, and historical Tico-source controls all rejected. The official archive
is `102568341` bytes, SHA-256
`c12a68e90d8f03001eff8c75790e0a221cb9b79c676cf5f3daf6c08ac9795557`;
the clean generated patch is SHA-256
`7751693a0e129521ed0ac265a545e0bdd093d5709c1dffa67a4ab7fb41ecd843`.
The current RP4 generated manifest was also run twice, byte-identical,
SHA-256 `1ecc95407ccdc4dec807a497c5d412db1bbfcad7ea2b00e77b7b279fb0691278`.

The source provenance is `SOURCE_CORRESPONDENCE_PROVEN`. The existing
software-Titan runner boot/callback and its AvP fixture stall are retained as
historical diagnostics only; **AvP guest equivalence is no longer a
prerequisite for this architecture study**. These tests are deliberately not
part of `test.ps1`, cannot promote RP4, and do not provide an AvP final
composite result.

The next implementation body is the direct AvP mechanism: bypass equal-Z SGL
sorting for the RP4 object schedule, emit an explicitly owned sequential VDP1
command list, and prove from command memory that the earlier CPS2 object-RAM
entry appears later in the final list. MSHvSF remains corroborating reference
evidence only. A separate minimal Saturn fixture may measure object-versus-plane
priority; neither route makes the optional Yaba source instrument an AvP
acceptance dependency. MAME/ROM captures remain authoritative for AvP CPS2
semantics.

Independent correction verification passed the two official-source tests, the
Saturn-control/provenance/rejected-diagnostic tests, RP4 v1 status mutations,
priority-decode tests, a fresh apply-script run, and two byte-identical RP4
manifest generations. Full `test.ps1` passed every earlier check and stopped at
the expected intentional RP4 v1 `FALSIFIED` result after the 201-frame composite
check; it is not a green suite. No emulator process remained.

Do not delete the historical 71c973f/Tico rejection or use its patch as an
official-source patch. Do not alter `saturn_vdp2_scanout_status`, RP4 status,
or Capability Gate counts in this repository from this checkpoint.

## RP4 exact-source scanout recovery: defined equivalence stop, 2026-08-20 (newest first)

The old statement that corresponding source was unavailable is
**SUPERSEDED_BY_OFFICIAL_1_20_37_SOURCE**.  The official Yaba Sanshiro download
page publishes the corresponding-source archive for the pinned release:

```text
source URL: https://d1t36rsydvwkyk.cloudfront.net/yabasanshiro-src-1.20.37.zip
archive bytes: 102568341
archive SHA-256: c12a68e90d8f03001eff8c75790e0a221cb9b79c676cf5f3daf6c08ac9795557
extracted version.json: version 1.20.37, code 354
release URL: https://d1t36rsydvwkyk.cloudfront.net/yabasanshiro-1.20.37-2986eb.zip
pinned installed exe SHA-256: 016112708fc77ec53b8a36c4ef52e300a78b3fb079e815f60b1a51fa1661999c
```

This establishes **SOURCE_CORRESPONDENCE_PROVEN**. It does *not* establish a
guest-equivalent diagnostic build. The prior 71c973f/Tico patch and manifests
remain historical **REJECTED** evidence and must not be deleted or repurposed.

### Route results

1. **Official-source software-Titan runner: BUILT, guest equivalence FAIL.**
   A short-root MSVC/CMake runner was built from the official archive with a
   copied scanout callback directly after `TitanRender(dispbuffer)` and before
   VDP1 swap, OSD, upload, and present. `game.cue` boots with HLE, 32-Mbit DRAM
   cart, and a 352x224 callback. Two real runner corrections were made while
   diagnosing it: `PERDummyHandleEvents()` already invokes `YabauseExec()`
   (the extra runner call was removed), and the runner now uses C68K plus the
   Qt default unthrottled setting rather than an unregistered Musashi id.
   Neither fixes the semantic failure. After 4,500 scanout frames the current
   StreetTest reports `runtime_ready=1`, `street_ready=1`, 464 objects and
   201 loaded fixture frames, but `frame_counter=1` and exported
   `street_frame=0` remain fixed. The prior pinned-release corpus advanced
   fixture frames. Thus command/VRAM/CRAM equivalence and calibration are
   blocked; do not use this runner's scanout as evidence.

2. **Official-source Qt/SDL real-context routes: not buildable from the
   published archive in this environment.** The Qt build reached the UI after
   a Windows CMake defect (`/MP` was sent to `rc.exe`) and absent updater
   support were isolated, but then stopped on independent omitted/unguarded
   components: `VIDCORE_VULKAN` is referenced when Vulkan headers are absent,
   and the bundled Firebase 6.11 API returns `User*` while the UI source
   expects a value with `is_valid()`. The fallback SDL route was tried with
   the pinned SDL 2.30.10 VC package; CMake then requires additional
   pkg-config/GLFW/OpenGLES dependencies. No arbitrary UI/cloud rewrite was
   accepted merely to obtain a measurement tool.

3. **MCP/Vulkan readback: rejected as an authority substitute.** The exact
   source MCP service exposes memory/debug operations only. Vulkan
   `FbReadback` is explicitly a paused VDP1-offscreen buffer, not the final
   VDP1+VDP2 composite. `VulkanScene::getScreenshot` reads the host swapchain
   at host surface dimensions after presentation. None is a deterministic,
   pre-OSD, native 352x224 final-composite witness.

### Current ruling and superseded runner direction

`saturn_vdp2_scanout_status` remains **UNREADABLE**;
`saturn_output_order_status` and `saturn_vdp1_command_status` remain
**ADAPTED/GAP**, all three visual controls are blocked, `rp4_v1_status`
remains **FALSIFIED**, and Capability Gate 1 remains **0/7**. Calibration and
RP4 promotion are not authorised.

The former executable instruction to pursue official-runner guest-equivalence
archaeology is **SUPERSEDED**. The reference-only package is complete and must
not be extended, wired into `test.ps1`, or used to change any AvP acceptance
status. MSHvSF owns generic Saturn priority/order measurement; later AvP
runtime work consumes that transfer contract and validates the AvP final
composite separately. Preserve the ignored official archive, extracted source,
runner builds, Qt/SDL attempts, logs and scanouts. Do not model a composite or
treat VDP1-only/host-swapchain output as VDP2 scanout.

## RP4 correction: reproducible rejected scanout diagnostic, 2026-08-20 (newest first)

Read the actual current commit with `git rev-parse HEAD`; this document must
not be used as a self-referential HEAD assertion. The starting base for the
Saturn-control evidence body was `bb06c0c6b595170d7ff2178f0538a7b4365d0d29`.
The prior hard-stop evidence commit is `9cb3ccb`. The correction commits after
that preserve the experiment, but do **not** reopen RP4 Chapters 3-6 or alter
Saturn runtime code.

### Chapter 0 provenance check: PASS, equal-Z result unchanged

The ignored raw inputs are stable repository-local private evidence:

```text
private-evidence/rp4-saturn-controls/cap_baseline.json
  791b22ecb5c7904cc9acc084536fb2776d0d83b4e86ea55e4bc5b542b2a19077
private-evidence/rp4-saturn-controls/cap_forward.json
  df56fd35f25a7bf816b430440511d5232ee1fccf29af21845de1a5ab583cf4fa
```

`tools/verify_rp4_saturn_controls.py` requires the stable private-evidence
root and records portable repository-relative paths, SHA-256 values, schema
and requested fixture frame under `input_captures`; it does not track raw
object lists or refer to the old Temp location. Reproduction command:

```powershell
$py = "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$evidence = Join-Path (Get-Location) 'private-evidence\rp4-saturn-controls'
& $py tools\verify_rp4_saturn_controls.py --baseline-capture (Join-Path $evidence cap_baseline.json) --forward-capture (Join-Path $evidence cap_forward.json) --baseline-build-sha256 3F5F2DB9D504FBC77BF26A3B3A12D74CD90237D42B9369F6B08150BFB568EF18 --forward-build-sha256 AD7651A8412EBA832561C1C44F16D8B06DCB3A17BA7DCE6E3FC3B683AEDAE320
```

Two stable-evidence regenerations produced SHA-256
`5ac9e83ec56fa4c78dccef5f4a7c39c20556417cc3c583a70387beab0f7245d5`
both times. The manifest remains `FAIL` (one executed/refuted equal-Z control,
two blocked visual controls), exactly as before. `tests/test_rp4_saturn_capture_provenance.py`
was written failing-first and passes after the provenance implementation.

### Rejected custom diagnostic build: reproducible, not acceptance

`emulator-patches/yabasanshiro-vdp2-scanout.patch` is the actual dirty-source
diff against source `71c973f92966d33de464c1ba4dac1953af6ec462`, SHA-256
`29905bf77e2ee4c29cb4d71111da66e40d52fe35c1a4be6fc972ae1dac989120`.
`data/yabasanshiro_scanout_diagnostic_manifest.json` pins every pre-patch
Git-blob SHA-256, the release SHA-256, CMake/MSVC/dependency versions and the
previous custom runner SHA-256. It is explicitly classified
`REPRODUCES_A_REJECTED_CUSTOM_DIAGNOSTIC_BUILD`.

The clean-base verifier uses `git apply --ignore-space-change` solely because
the upstream checkout has `core.autocrlf=true`; it separately validates
byte-exact Git blobs before allowing that EOL-tolerant patch application.
It proves all of the following: exact base + patch applies; `HEAD~1` is
rejected; an appended byte in `vidsoft.c` is rejected. Run:

```powershell
$py = "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $py tests\test_yabasanshiro_scanout_diagnostic.py
```

The full manual apply/build/smoke recipe is in the manifest and the tracked
`tools/apply_yabasanshiro_scanout_patch.ps1` and
`tools/build_yabasanshiro_scanout.ps1` scripts. Their output roots are ignored.
The known smoke result remains exit `0xC0000005` with zero scanout bytes; it
therefore remains a hard stop, not a usable visual witness.

Correction validation: `tests/test_rp4_saturn_capture_provenance.py` exit 0;
`tests/test_saturn_control_status.py` exit 0;
`tests/test_yabasanshiro_scanout_diagnostic.py` exit 0; and a separate clean
clone passed `apply_yabasanshiro_scanout_patch.ps1` plus `git diff --check`.
`test.ps1` was started and passed its normal host checks through fixture
separation, but its pre-existing private `verify_street_planes.py` stage did
not complete within the bounded run and was terminated; it did not reach a
new correction failure or the intentionally red RP4 result. It must be rerun
to completion in a persistent environment before this is called a full-suite
pass. No MAME, Yaba Sanshiro, compiler, linker, CMake, or correction-owned
Python process remains running.

### Prescriptive next agent prompt

```text
CODEX_REVIEW_INVOCATION
REPOSITORY: C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest-ClaudePriorityArchitecture
Read AGENTS.md, then this newest handoff section. Run git rev-parse HEAD,
git status --short --branch, git diff --check, the two RP4 provenance/patch
tests, and inspect data/yabasanshiro_scanout_diagnostic_manifest.json.
Confirm that the rejected custom diagnostic workflow is labelled correctly,
that no Saturn runtime file changed, and that the raw captures, source, build,
runner, logs and scanouts remain ignored. Do not resume RP4 Chapters 3-6.
Return whether the correction is accepted and a separately authorised proposal
for obtaining a guest-equivalent post-composite visual instrument.
```

### Dirty/ignored inventory at the correction boundary

The Git worktree must be clean after the correction commit. Ignored local
inputs remain: the two capture JSON files above; `.deps/yabasanshiro-source`
(patched/untracked `runner/lodepng`); the disposable patched
`.deps/yb-apply-check` validation clone; `.deps` build logs and scanout smoke
files; and `C:\yb5` diagnostic output. None is staged or tracked.

## RP4 Saturn visual-control body, 2026-08-20 (historical evidence)

## RP4 native-scanout diagnostic emulator: defined hard stop, 2026-08-20 (newest first)

Branch `claude/rp4-priority-architecture`, starting evidence base
`bb06c0c6b595170d7ff2178f0538a7b4365d0d29` (not current HEAD). This checkpoint does **not**
promote RP4 and does not alter the refuted equal-Z result.

### Result

The exact source corresponding to the pinned Windows release could not be
located. The release binary is
`.deps/emulators/yabasanshiro-1.20.37-2986eb/yabasanshiro-1.20.37-2986eb/yabasanshiro.exe`,
SHA-256 `016112708fc77ec53b8a36c4ef52e300a78b3fb079e815f60b1a51fa1661999c`.

The only available source was fetched fully at
`.deps/yabasanshiro-source`, commit
`71c973f92966d33de464c1ba4dac1953af6ec462` from
`https://github.com/ticohq/tico-yabasanshiro.git`. It is a
**CUSTOM_DIAGNOSTIC_EMULATOR**, never a patched copy of the pinned release.

Three bounded setup/build paths were attempted:

1. NMake output under the long worktree path: libchdr/zstd failed at Windows
   generated-object path limits.
2. Clean short output root with OpenGL disabled: the source's VDP2 code does
   not compile with `VIDCORE_OGL` removed.
3. Clean short output root (`C:\\yb5`) with OpenGL enabled: after repairing
   stale runner API calls, port-owned stubs, and NMake libchdr link paths, the
   headless software-Titan runner built successfully. Portable CMake was
   `3.30.5` SHA-256
   `5ab6e1faf20256ee4f04886597e8b6c3b1bd1297b58a68a58511af013710004b`;
   MSVC reported `19.44.35228.0` via the existing Build Tools install.

The third path includes the required hook immediately after `TitanRender` and
before VDP1 swap, OSD, GL upload, and presentation. Its callback API carries
pixels, width, height, interlace, monotonic renderer frame, and user data.
It compiled into `C:\\yb5\\src\\runner\\yabasanshiro.exe`, but is not evidence:

```powershell
& C:\yb5\src\runner\yabasanshiro.exe scanout `
  C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest-ClaudePriorityArchitecture\game.cue `
  5 C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest-ClaudePriorityArchitecture\.deps\scanout-smoke.txt
```

exited `-1073741819` (`0xC0000005`) before producing any scanout record. The
pinned release reaches `runtime_ready=1` for this disc. The custom source
therefore fails the book's required guest-equivalence check before calibration:
command order, command count, VDP/CRAM canaries, and fixture state cannot be
compared. This is the explicit stop condition **custom source diverges from
required guest behavior**.

### Consequences

- `saturn_vdp2_scanout_status` remains **UNREADABLE**, not MEASURED.
- All three Saturn controls remain unexecuted/blocked; `rp4_v1_status` stays
  **FALSIFIED** and Capability Gate 1 stays **0/7**.
- Do not use the custom executable, its hook, or a modelled composite as an
  acceptance substitute.
- No emulator binary, patched source, raw scanout, build output, or log is
  tracked. The source-tree experiment remains under ignored `.deps` only.

### Historical next work (superseded)

These instructions record the original stop condition only. Do not resume the
custom/pinned equivalence comparison, scanout calibration, or UI/runner build
archaeology on this branch. The official reference instrument is optional and
complete; generic Saturn priority/order evidence belongs to MSHvSF, while a
later AvP runtime validation must consume its transfer contract.

### Process state

No MAME, Yaba Sanshiro, NMake, compiler, linker, or CMake process is running.
At the original hard-stop evidence commit, the only tracked modification was
the handoff update; all source and build experiment files were ignored under
`.deps` or `C:\\yb5`. The current correction adds only the tracked patch,
manifest, reproducibility tools/tests and revised documentation named above.

Historical evidence sub-body: starting HEAD `2e0d36e`, ending evidence HEAD
`d330a92`. Commits: `fd80e38` Saturn-control evidence schema
(failing-first), `d330a92` StreetTest command-order measurement.

### Outcome: the primary objective is ANSWERED, and the answer is no

Option 1 of the ruling ("prove that the current reversed equal-Z SGL
submissions become the required final VDP1 order") is **REFUTED BY
MEASUREMENT**. Option 2, replacing the mechanism, is now the required
work and has NOT been done.

Evidence, from two real builds captured at the same StreetTest fixture
frame:

| | baseline (reverse emission) | forward-order control |
|---|---|---|
| ISO sha256 | `3F5F2DB9...B568EF18` | `AD7651A8...AEDAE320` |
| command count | 528 | 528 |
| command table sha256 | `0273ca8dda048a47...` | `51bf42ba5d013e73...` |
| street objects drawn | 464 | 464 |

- 510 of the 528 commands are sprite commands, ALL with jump mode 0, so
  the table is sequential and its index order IS the VDP1 draw order.
  The traversal was verified before the conclusion was drawn.
- Every one of the 510 comparable commands sits at the SAME index in
  both builds: 129,795 of 129,795 order-preserving pairs, 100%.
- The command multiset is identical once texture address is excluded.
  Only `srca` differs, because tile upload order follows emission order.

So SGL does not preserve submission order for equal-Z sprites, and
reversing the emission loop does not decide what VDP1 draws on top. The
main.c comment that claimed it did now states the measurement instead.
The loop is left reversed (it matches the source's intent and is inert
for ordering), but it must NOT be read as the fix.

### Stop condition reached: no observable witness pixel

The other two controls are BLOCKED, not failed and not assumed:

- VDP1 framebuffer at 0x05C80000 / 0x25C80000 reads all zeros under the
  OpenGL core (VideoCore=4) and is UNMAPPED under the software core
  (VideoCore=2, memory_read returns 0 bytes). The ini was restored to
  VideoCore=4 afterwards.
- `yabasanshiro.exe` contains no "screenshot" string at all; this build
  has no screenshot facility.
- VDP1 command table, VDP1/VDP2 VRAM and CRAM all read fine, so this is
  specific to the framebuffer, not a broken reader.

`sprite_priority_register_effect` in particular can NEVER be executed
this way: the ruling itself requires its VDP1 command table to stay
byte-identical, so the composite is the only possible observable.

### Result labels

- `saturn_output_order_status` = **FAIL** (1 executed, 0 passed, 2
  blocked). Not MEASURED.
- `saturn_vdp1_command_status` = MEASURED (the table is readable and was
  compared between builds).
- `saturn_vdp2_register_readback` = UNREADABLE.
- `mshvsf_priority_architecture` = ADAPTED.
- `animation_jump_record_coverage` = GAP.
- `rp4_v1_status` stays FALSIFIED; `rp4_v0_status` stays
  FALSIFIED_BY_SOURCE_PREMISE. Nothing was promoted to PASS.

### Commands run and exit codes

- `git status --short --branch`, `git log --oneline -12`,
  `git diff --check`: clean, HEAD confirmed `2e0d36e` at start.
- `py tests/test_saturn_control_status.py`: 0. Mutating the verifier to
  promote blocked controls, ignore the observed winner, ignore
  negative-control leakage, ignore the command table, or allow a build
  compared against itself fails 4, 2, 1, 1 and 1 controls respectively.
- `py tests/test_priority_decode.py`: 0 (8 tests).
- `py tests/test_rp4_v1_status.py`: 0.
- `py tools/pin_street_object_order.py`: 0. Nineteen witnesses, nine
  pair types, zero counterexamples, fourteen StreetTest-mappable.
- `build.ps1 -StreetTest -SkipHostTests` (baseline): 0.
- `build.ps1 -StreetTest -Rp4ForwardOrder -SkipHostTests`: 0.
- `py tools/capture_street_command_order.py` (both builds): 0.
- `py tools/verify_rp4_saturn_controls.py`: 3 (FAIL, as it must be).
  Manifest regenerated twice, byte-identical
  (`300571bfbdc72b67...`).
- Full `test.ps1`: **UNRUN to completion**, and it must stay red.
- Visible boot verification, EncounterTest, title boot, ISO member
  hashes, CDDA/PCM regression: **UNRUN**.
- Emulator processes: stopped and verified none running.

### Exact next ordered work

1. Decide the deterministic emission mechanism. The measurement rules
   out submission order; the remaining candidates are an explicitly
   owned VDP1 command path, or an SGL sort key that is proven to order
   equal-Z sprites deterministically. Arbitrary Z separation stays
   barred until a 352x224 geometry comparison proves it changes neither
   scale nor position.
2. Prove the replacement with the command table alone, which IS
   readable: the earlier CPS entry must end up LATER in the final VDP1
   list. This does not need a framebuffer.
3. Rule on the two pixel-blocked controls. They cannot be executed in
   this emulator. Either a different instrument is authorised (a Saturn
   emulator that exposes the framebuffer or a screenshot), or the
   controls are respecified against observables that exist here.
4. Only then: manifest promotion, full `test.ps1`, and the live ladder.

### Repository state

`git status --short --branch` reports the AvP worktree clean at
`d330a92`. The MSHvSF probe worktree is clean apart from the untracked
`history.txt`, which was preserved and never staged.

## Priority-architecture book, 2026-08-20 (newest first)

Worktree `AvPSaturnCapabilityTest-ClaudePriorityArchitecture`, branch
`claude/rp4-priority-architecture`, base `a57f368`.
Companion lane: `AvPSaturnCapabilityTest-MSHvSF-PriorityProbe`, branch
`claude/mshvsf-vdp2-priority-probe`, base `dc5d3ea`.

### Implementation report

Commits (AvP): `413b4ab` Chapter 0 test bootstrap, `b3835a5` fixture
tile coverage, `a6cd6d1` per-scene priority semantics, `6a24c8e`
object-versus-tile priority, `981c7e7` within-priority ordering,
`0b9c15e` identity join, `e8c32bf` v1 contract and source controls,
`1292368` port onto the v1 model. That is eight commits against the
book's suggested five; the extra separation was to keep each falsifiable
claim independently reviewable. Commit (MSHvSF): `b3df75c`.

**Chapter 0 (done).** `tools/preflight_generated_inputs.py` gains
`--ensure`; `test.ps1` ensures `generated/avsp_collision.h` before the
first host compile and regenerates the RP4 fixture archives instead of
skipping. Proven: a clean worktree now fails for the explicit RP4 reason
rather than on a missing header.

**Chapter 1 (done).** Four results, each with executed controls:

- Per-scene sweep of all 122 scenes: visible objects carry ONLY code 4
  (406,858) and code 7 (16,324); code 7 appears solely in
  character-select, its unlabeled transition and the two continue
  countdowns. `data/source_priority_semantics.json`.
- Object-versus-tile priority decoded from the registers that program
  it (OBJ_PRI nibbles, CPS-B layer-control draw order, tile-pen masks
  read and measured ZERO, hence inert). Four street witnesses agree with
  MAME's framebuffer, each with three executed controls including a
  negative one. `data/rp4_object_layer_witnesses.json`.
- Within-priority ordering: the EARLIER object-RAM entry wins. 11
  witnesses over 11 frames, four semantic pair types, ZERO
  counterexamples, every reversed-entry control detected. Witnesses are
  taken only where the composite already agrees with the capture, so
  they are validated pixels rather than selected agreements.
  `data/rp4_object_order_witnesses.json`.
- Identity join by EXACT RE-EMISSION: 12,736 of 15,074 eligible entities
  (84.49%) matched verbatim, joining 32,829 of 68,020 objects (48.26%),
  against a 2.95% shuffled-frame control.
  `data/rp4_object_identity_join.json`.

**A HARD STOP was nearly invoked here and would have been WRONG.** The
first join reached 19.6% and the actor grid looked empty apart from the
player, which reads exactly like the contract's "actor identity cannot
be joined" stop condition. The cause was a defect in the new tool: the
capture's `workram` region is based at **0xFF0000**
(`tools/mame_capture_full_route.lua`), not 0xFF8000, so it scanned the
wrong half of RAM. At the correct base one street frame carries 43 live
records including 8 class-0x1F street aliens, and every one of the 3,469
street frames carries 6 to 11 of them. Nearest-X proximity was then
falsified properly (its shuffled control stayed within ~15 points) and
replaced by exact re-emission. `decode_actor_entries` gained optional
state and pose-region parameters that default to its original gates.

**Chapter 2 (done, negative).** Both paths to the official port's VDP2
priority programming are closed, each with its own control:

- Reads: the register block is all zeros through the cached view
  `0x05F80000` AND the uncached mirror `0x25F80000` at all four anchors,
  while a colour-RAM positive control reads nonzero every time.
- Writes: watchpoints on SPCTL/PRISA-D/PRINA-B/PRIR on both CPUs with
  the debug interpreter core give zero hits, but so do BOTH controls: a
  write watchpoint on a work-RAM long observed changing across a frame,
  and a code breakpoint at the master CPU's own PC. **The breakpoint
  mechanism is inert in this Yaba build**, so the run is reported as
  proving nothing rather than as a measurement.
- "List order is the only priority" therefore stays **ADAPTED**.

**Chapter 3 (source half done, Saturn half BLOCKED).** `rp4_status.py`
gains the v1 contract: eight controls split five source / three Saturn,
with `rp4_v0_status` preserved as the constant
`FALSIFIED_BY_SOURCE_PREMISE`. All five source controls agree with the
model, including the mask-bit control which PREDICTS no change and
observes none, confirming the masks inert. `test.ps1` now keeps the v0
verifier as a regression assertion that must report exactly FALSIFIED
and takes acceptance from v1, so the suite is green only when v1 passes.

`main.c` is ported onto the v1 model: the actor/foreground class split
is gone (no priority-1 object is ever visible), every street object
takes one sprite class above NBG0/NBG1, and the emission loop now walks
the object schedule IN REVERSE, because CPS2 draws the earlier entry on
top while VDP1 draws the later command on top. Front-to-back emission
had been inverting every overlap inside the class. StreetTest builds
clean.

### Blocking obstacle for the remaining work

The three Saturn-side v1 controls and the Chapter 4 acceptance step
"visible StreetTest boot with SPCTL/PRIS/PRIN readback matching the v1
manifest" both require reading Saturn VDP2 registers from a running
build. Chapter 2 measured, with controls, that this instrument CANNOT
read those registers and CANNOT set breakpoints. The acceptance
requirement as written is therefore not satisfiable on this rig.

The available substitute, not yet executed and NOT self-accepted: run
the Saturn controls as VISUAL DIFFERENTIALS. Rebuild StreetTest with
exactly one perturbation (reversed command order; a changed CMDCOLR
priority-class bit; a perturbed `slPriority` class value), capture the
same frame, and require the framebuffer to differ in the direction the
model predicts. That tests the same programming through the only output
this instrument can observe. **Codex should rule on whether that
substitution is acceptable before it is treated as satisfying the
contract.**

### Resume point

1. Rule on the visual-differential substitution above.
2. Execute the three Saturn controls, feed them into `build_v1_status`,
   and confirm `rp4_v1_status` reaches PASS.
3. Then the Chapter 4 ladder: full `test.ps1` exit 0, manifests twice
   byte-identical (the three Chapter 1 manifests already rerun
   byte-identical), clean StreetTest build with host tests, ISO member
   hashes, visible boot, EncounterTest (shared code changed:
   `main.c` street path only), normal-release title boot, emulators
   stopped.

### Checks and results

- `tests/test_priority_decode.py`: 8 tests, PASS.
- `tests/test_rp4_v1_status.py`: PASS; mutation-checked (ignoring
  blocked controls, the witness floor, or counterexamples fails 16, 2
  and 1 controls respectively).
- `tests/test_rp4_status.py`: PASS (v0 instrument unchanged).
- `tests/reference_engine/test_vdp2_priority_decode.py`: 8 tests, PASS.
- `build.ps1 -StreetTest -SkipHostTests`: PASS (clean build attempted
  first and also reached the compile stage; the full-suite build is
  expected to fail while v1 is FALSIFIED).
- Full `test.ps1`: **UNRUN to completion.** It fails by design at the
  v1 gate while the Saturn controls are blocked.
- Live AvP boots, ISO member hashes, EncounterTest, title boot: **UNRUN.**
- All three Chapter 1 manifest reruns: byte-identical.

### Remaining ADAPTED / GAP

- `ADAPTED`: MSHvSF "list order is the only priority" (instrument cannot
  decide it).
- `GAP`: animation-script jump-record decode, which bounds the identity
  join at 48.26% of objects (45,725 jump-record exclusions). Named and
  counted, not hidden.
- `GAP`: Saturn-side v1 controls and all live validation.

Capability Gate 1 remains 0/7. Nothing here is self-accepted.

## Implementation report: RP4 overlap-proof corrections - HARD STOP (2026-08-20)

- Worktree: `C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest-ClaudeOverlapCorrections`,
  branch `claude/rp4-overlap-proof-corrections`, base
  `6bee037031d5416dd47719b75421cd725ce34b74`. Primary worktree untouched.
- Commits: `c6751a9` (Chapter 1: acceptance instrument), `c66f7a8`
  (Chapter 2: full-street + route scans, hard-stop evidence), plus this
  handoff commit. Chapters 3-4 were NOT started: the book's hard-stop
  condition fired.

### Baseline (recorded before changes)

- `verify_street_planes.py` exit 0 (201/201 frames, 0 mismatches,
  after regenerating STRIPS.BIN `7c286173...` and TILES.BIN in the
  fresh worktree); `verify_street_composite.py` exit 3 (6 executed,
  2 blocked); `test.ps1` previously exited 0 despite the FALSIFIED
  tracked result - confirmed and fixed.

### Chapter 1 - acceptance instrument (commit c6751a9)

- `tools/rp4_status.py`: required_controls_total/executed/passed/
  blocked, `rp4_contract_status` PASS|FALSIFIED|FAIL,
  `actor_foreground_overlap_status` separated from the independently
  MEASURED `generic_object_plane_order_status`, live-register readback
  explicitly not a substitute, stale-evidence rejection, exit map
  0/1/3.
- `tests/test_rp4_status.py` written failing-first; all behaviours now
  hold (blocked/missing controls can never pass, null overlap =>
  FALSIFIED, synthetic 8/8 fixture passes, corrupt hashes rejected,
  tracked evidence recomputes).
- `test.ps1` runs `verify_street_composite.py` under the same
  private-input gate as the plane verifier; exit 3 FAILS the suite.
  The suite is intentionally red on this branch.

### Chapter 2 - full-street and route scans (commit c66f7a8) - HARD STOP

- `tools/scan_street_overlaps.py` swept the complete street range
  2074-5542 (bounds from the scene manifest): 3469/3469 frames reject
  as `actors_offscreen`. The street scene carries exactly TWO
  priority-1 objram entries, both parked at (-64,240) on every frame -
  sentinels, never content.
- `tools/scan_route_object_priorities.py` extended the falsification to
  the whole 18000-frame route: priority 1 NEVER draws a visible object
  anywhere. Visible content: priority 4 (406,858 onscreen objects,
  15,282 frames) and priority 7 (16,324 objects, 1,045 frames) - a
  third class the current model does not map.
- Conclusion: the RP4 contract's actor-class-is-priority-1 premise is
  falsified route-wide. There is no actor/foreground priority-class
  overlap to measure in this game's street scene; visible actors and
  foreground both live in priority 4, ordered by objram slot, and the
  Saturn STREET_SPR_CLASS_ACTOR (class 1) design maps a class the
  source never uses for content (live class counts {1: 2} are the two
  parked sentinels).
- Evidence: `data/rp4_overlap_candidates.json`,
  `data/route_object_priority_sweep.json`,
  `data/rp4_street_readback.json` (composite.status FALSIFIED, 6/8
  executed, 2 blocked).

### Status

- rp4_contract_status: **FALSIFIED** (intentionally red suite).
- No substitute fixture manufactured; RP8/S5 not started; Capability
  Gate 1 unchanged (0/7); NEXT_AGENT_PROMPT untouched.
- Independently valid work at 6bee037 retained unchanged.

### Architectural ruling requested from Codex

The contract requirement "actor-class (priority 1) object overlapped by
foreground-class (priority 4) content" cannot be satisfied by this
title's data. Options for the ruling:

1. Redefine the RP4 overlap proof in terms the source actually uses:
   object-vs-object ordering WITHIN priority 4 (objram slot order,
   player/enemy sprites vs foreground props - candidates exist wherever
   two pri-4 objects overlap), plus the already-MEASURED object-over-
   plane ordering; retire the class-1 actor lane or repurpose it after
   measuring what priority 7 carries.
2. Investigate priority 7 (1,045 frames) and the cps_b priority masks
   before ruling, in case the actor/foreground split is expressed
   there.
3. Keep the FALSIFIED verdict as the permanent RP4 record and move the
   ordering obligation into RP8 gameplay rendering with a new
   contract-level definition.

## Implementation report: RP4-RP7 acceptance corrections (2026-08-20)

- Worktree: `C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest-ClaudeCorrections`,
  branch `claude/rp4-rp7-acceptance-corrections`, BASE_SHA
  `e79f666c865b096192aa102137db1cfdfad6c321`. The dirty primary worktree was
  not edited. `.deps`/`avspu` are NTFS junctions into the primary (never
  committed).
- Correction commits (oldest first): `c7e8f80` (clean-checkout
  reproducibility: loader sources, START_TRANSITION interface + exact
  30-frame test, generated-input preflight, Invoke-Generator harness,
  lexical manifest paths + junction test), `a12165f` (STRIPS parser
  extracted to `avsp_street_bundle.c/h`, 23 ASan corrupt/truncated
  controls), `a1c7ef0` (signature_id/runtime_scene_id policy,
  `generated/avsp_scene_ids.h`, row-scroll runtime-ID join, 9+4 ID
  controls), `23566a7` (RP4 201/201 pixel frames, full host composite,
  6 executed controls, overlap falsification), `41f4c21` (stateless
  residency: `tools/measure_avsp_profile.ps1`, four explicit profile
  measurements, byte-identical ledger; street-bundle scoped to the
  street profile after it pushed encounter-test 704 bytes over the
  0x060C0000 bound), `9589294`, `875f69f`, `72cb9e2` (verifier/wiring
  fixes and the live readback record).

### Checks and exact results

1. Narrow host tests: street-bundle (24 cases incl. view-unusable
   assertion, ASan exact-size buffers), scene manifest (9 controls),
   row-scroll (4 controls), residency (v1 schema, 3 controls), manifest
   junction-path test - all PASS.
2. RP4 reconstruction: `verify_street_planes.py` - 201/201 pixel frames,
   mismatches nbg0=0 nbg1=0, objects 12118, missing tiles 0, executed
   controls PASS. `verify_street_composite.py` - 201 frames composited
   (NBG1 < NBG0 < actor < foreground < scroll1); six executed one-input
   perturbation controls all detect (wrong_transform 17095 px,
   scroll_shift 25249, row_entry 127, palette_cycle 6, patch_dropped
   4045, register_order 18920).
3. **RP4 interval falsified: no deliberate overlap.** The interval's 402
   actor-class (CPS priority 1) schedule entries are all parked
   offscreen (raw-geometry scan, zero opaque actor pixels in all 201
   frames), so no actor/foreground overlap exists to measure. Recorded
   verbatim in `data/rp4_street_readback.json` (`composite` section);
   the two overlap-object controls are BLOCKED, not fabricated. Per the
   contract stop condition this path stops without substituting another
   design; actor-class ordering remains ADAPTED (live registers only).
   Composite-vs-PNG residue (total 2181334 px over 201 frames, max
   21066/frame) is offline object-decoder + scroll1 imprecision, GAP.
4. Determinism: STRIPS.BIN
   `7c28617351ec2bb2099d10e28de561f0ef64feb2fbb1784c5dae11d29c7f1c22`
   (269654 bytes) twice; scene manifest, `avsp_scene_ids.h`, row-scroll
   classification and residency ledger each regenerated twice
   byte-identical (ledger sha256 `c329c380fc81...`).
5. Full `.\test.ps1`: exit 0 (includes the deterministic capability
   soak and every RP gate above).
6. `git diff --check`: clean.
7. `.\build.ps1 -Clean -StreetTest` WITH host tests: exit 0. Hashes:
   TILES.BIN `43d9707f2bcd...` (297764), game.iso (street)
   `f59449e82995...` (6141952), game.cue `bfc58c7020d9...`, loader
   IP.BIN `a442bd5a5fda...` (4860), 0.BIN `1f55dae40281...` (29036),
   game.elf `c487105e472f...`.
8. Visible pinned StreetTest boot: `yabasanshiro.exe -nb -a -i
   %TEMP%\AvPSaturnCapabilityTest\game.yaba.cue` (staged cue sha256
   `f8a1b410b96a...`), Yaba Sanshiro 1.20.37. Live readback
   (`data/rp4_street_live_readback.json`): runtime_ready=1, street
   frames advancing (109 -> 184 -> 194), PRINA 0x0203 / PRINB 0x0102 /
   PRISA 0x0406, SPCTL 0x0023, VDP1 classes {0:1, 1:2, 2:308}, CRAOFA
   0x0032, all VRAM canaries match the staged STRIPS.BIN, print buffer
   clean.
9. EncounterTest: exit 0 build, self-driving route reached
   CAP_ENCOUNTER_COMPLETE (state 18) at frame 3532, live over MCP.
10. Normal-release: build exit 0 (ISO `5d7112e6f603...`), title boot
    healthy - runtime_ready=1, frames advancing 596 -> 658,
    encounter_state 0 (MAIN_MENU title).
11. All MAME/Yaba/Kronos/Mednafen processes stopped and verified gone.
12. Work-RAM residency (all four profiles, measured):
    normal-release __bend 0x060bf6c0 (headroom 2368), frontend-test
    0x060bf820 (2016), encounter-test 0x060bfec0 (320), street-test
    0x0608a3a0 (220256); limit 0x060C0000.

### Remaining ADAPTED / GAP / UNRUN

- ADAPTED: actor-class (priority-1) VDP1 ordering above NBG0 - no
  visible in-interval evidence exists (falsified above); rests on the
  live register programming. CDDA ownership/rejection path - CD track
  start still disabled. Character fallback rendering per capability
  model.
- GAP: route-wide VDP1 command high-water; allocator/SCSP high-water;
  offline object pixel-decoder residue in the full composite.
- UNRUN: physical Saturn hardware boot; audible CDDA on hardware.
- RP4, RP5, RP6, RP7, SP7, SP8 are NOT represented as passed; Codex
  owns acceptance. Capability Gate 1 remains 0/7.

### Suggested next body (for Codex only)

The RP4 overlap contract cannot be satisfied inside frames 3474-3674:
actor-class content never enters the visible window there. Two
evidence-preserving options: (a) re-select the RP4 proof interval to a
street window that provably contains onscreen priority-1 objects (a
census scan over the street group can locate candidates before any
generator work), keeping the current 201-frame reconstruction as-is; or
(b) accept the falsification record and carry actor-class ordering as a
live-register ADAPTED item into the RP8 gameplay renderer, where actors
are guaranteed onscreen and the same composite census applies. Option
(a) costs one re-capture-free re-selection pass; option (b) defers the
pixel proof to a package that needs it anyway.

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
