# MSHvSF Saturn reference-lane handoff

Updated: 2026-08-18 EDT

## VDP2 priority re-read, 2026-08-20 (newest first)

Worktree `AvPSaturnCapabilityTest-MSHvSF-PriorityProbe`, branch
`claude/mshvsf-vdp2-priority-probe`, from `dc5d3ea`.

**Result: the VDP2 priority programming remains undecodable with this
instrument, and the reason is now pinned rather than assumed.** Both the
read path and the write path were attacked, each with its own control.

Reads (`tools/probe_mshvsf_vdp2_priority.py`, replayed on
`saturn_ryu_first_pass_b` at the four tracked anchors idle 3540,
normal_active 3828, impact 3840, recovery 3900):

- the 288-byte register block reads back all zeros through BOTH the
  cached A-bus view `0x05F80000` and the uncached mirror `0x25F80000`,
  at every anchor;
- the colour-RAM positive control at `0x05F00000` reads nonzero in every
  run, so the memory reader itself is proven working and the zeros are a
  property of the register block, not of the tool.

This closes the "a better parser cannot help" question from the previous
session: it is not a parser problem and not an address-view problem.

Writes (`tools/trace_mshvsf_vdp2_writes.py`): the fallback of watching
the writes instead of the state is ALSO closed.

- SH-2 memory write watchpoints were armed on SPCTL, PRISA-PRISD,
  PRINA/PRINB and PRIR on both CPUs, with the debug interpreter core
  selected (`sh2 core: SH2 Debugger Interpreter`). Yaba normalizes the
  uncached mirror onto the cached address, so 16 armed watchpoints cover
  all eight registers on both CPUs.
- Zero hits. But zero hits proves nothing on its own, so the run carries
  two controls, and BOTH fail: a write watchpoint on `0x06001F18`, a
  work-RAM long observed changing across a frame, never fires; and a
  code breakpoint set at the master CPU's own current PC never fires
  either.
- Conclusion: **the breakpoint mechanism as a whole is inert in this Yaba
  build**, not merely memory watchpoints. The tool reports this as
  proving NOTHING about VDP2 rather than as a measurement.

Consequences for the reference lane:

- "list order is the only priority" stays **ADAPTED**. It is not
  confirmed and not refuted; the instrument cannot see the registers
  that would decide it.
- The VDP2 priority decode itself is implemented and unit-tested
  (`tests/reference_engine/test_vdp2_priority_decode.py`, 8 tests),
  including that an all-zero block decodes to all-zero priorities. The
  decode is deliberately naive there; it is the PROBE, not the decode,
  that refuses to treat an all-zero block as a measurement.
- The instrument that would answer this: a Saturn emulator whose
  debugger actually services register reads or breakpoints (a Kronos or
  Mednafen debug build), or a Yaba build with breakpoint support
  compiled in. Adding more anchors or more parsing to the current rig
  cannot help.

## Repository boundary

- Worktree: `C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest-MSHvSF`
- Branch: `codex/mshvsf-reference-lane`
- Starting checkpoint this session: `4b826534c9b2e5da47243c2aeee07cf6c9daa8bc`
- AvP remains in the separate
  `C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest` worktree on
  `codex/avp-master-plan`.
- Never switch, merge, or bulk cherry-pick between the lanes. Marvel findings
  are candidate Saturn patterns until an AvP-specific probe validates them.

The authorized Marvel CPS2/Saturn inputs and Marvel-only ignored evidence were
moved into this worktree. Shared MAME 0.289, emulator, and Capstone directories
are local junctions to the AvP checkout's read-only dependency copies. Do not
move them back merely to make the AvP checkout self-contained.

### AvP checkout was read-only this session

The AvP checkout was consulted, never modified. Its committed HEAD at the time
of reading was `79c313032791e99dd01c3217c4d148e23a36871b` on
`codex/avp-master-plan`, and it had uncommitted work in progress (a modified
`CLAUDE.md` plus roughly two dozen untracked diagnostic tools and one untracked
data file). None of that was read, staged, committed, moved, or depended on.
Every AvP clue was read with `git show 79c3130:<path>` so the investigation is
tied to an immutable commit.

Verified after the work: AvP HEAD unchanged, branch unchanged, no AvP file
written by this lane. Its untracked-file count did move from 33 to 34 during the
session, because **another agent is actively working in that checkout**. Only
`git rev-parse`, `git status` and `git show` were ever run against it, all
read-only. Treat a changed dirty count there as that agent's work, and re-record
the AvP HEAD before the next consultation rather than reusing `79c3130`.

## What this session added

A CPS2-to-Saturn **reference engine**: a host-side, executable model of the
translation boundary, plus two new measured analyses of the existing captures.

- `docs/CPS2_SATURN_REFERENCE_ENGINE.md` — architecture, three layers, evidence
  labelling rules, and the inventory of what was reused rather than duplicated.
- `docs/CPS2_SATURN_REFERENCE_ENGINE_AVP_ADAPTERS.md` — eight mapped concepts
  against the immutable AvP commit, each with the AvP probe it still needs.
- `reference_engine/` — `evidence`, `source_semantic`, `translation`, `vdp1`,
  `saturn_backend`, `trace`, `scenario`, `report`, plus
  `scenarios/normal_hit.json`.
- `tests/reference_engine/` — 121 tests, all passing.
- `tools/analyze_mshvsf_saturn_vdp1.py`,
  `tools/analyze_mshvsf_saturn_video_audio.py`,
  `tools/build_reference_engine_report.py`,
  `tools/run_reference_engine_tests.py`.
- `tools/analyze_mshvsf_saturn_memory.py` now calls the same VDP1 traversal, so
  there is one implementation rather than two.
- `tools/validate_mshvsf_training_package.py` gained gates on the three new
  artifacts; both new gate families were negative-tested and do fail when
  broken.

It is not a Saturn runtime, not a CPS2 emulator, not a 68000 interpreter, and
not an AvP implementation branch.

## Baseline verification

- MAME 0.289: `romset mshvsf is good`; `1 romsets found, 1 were OK` (unchanged;
  not re-run this session, no capture was taken).
- CPS2 vertical slice: 401 frames validated; 30 low-confidence step-decrease
  leads retained.
- Training package: **22 JSON artifacts, 12 documents**, six correspondence
  records, and six patterns.
- Reference-engine suite: **121 tests, OK**.
- Report determinism: two separate process invocations produced byte-identical
  files.
- No MAME, Yaba Sanshiro, Mednafen, or RetroArch process was started or left
  running. All work ran against the existing ignored captures.

## Tracked report hashes

Recorded with explicit LF newlines so the hash matches the bytes on disc.
`.gitattributes` pins `eol=lf` for these three files, otherwise a checkout on a
CRLF host would rewrite them and break both the recorded hash and
`build_reference_engine_report.py --check`:

- `data/mshvsf_saturn_vdp1_control_flow.json`:
  `54E6FECE9020AF8255BEC515FB71034A07E076FE199A535587559C8CDE7D189E`
- `data/mshvsf_saturn_vdp2_scsp.json`:
  `A17F2E9C8D013D10436522CE7749BA624CC0FA3F5BC157A0BCF68049865B375A`
- `data/reference_engine_normal_hit_report.json`:
  `E64E7A27BB761FC7F2680636E565F50AF6B8ECCA2F3E603FD222600028433877`
- `data/mshvsf_saturn_runtime_memory.json` (regenerated with the new VDP1
  fields; supersedes the previously recorded `1C2DAE62...`):
  `28085BC843099CC2EE9D6473D0987E7A5004BB11169B9C4F952ECF07217DFBF8`

The runtime-memory report shrank from 845,841 to 154,022 bytes, which is most of
the diff's deletion count. The previous version embedded **1,245 complete VDP1
command records** across the four anchors, with every coordinate and source
address. Those are now replaced by command-type, jump-mode, sprite-size and flip
histograms plus a pointer to `data/mshvsf_saturn_vdp1_control_flow.json`, which
records merged texture spans rather than per-command contents. That keeps the
tracked artifacts clearly on the derived-report side of the rights boundary. If a
future question needs per-command detail, regenerate it from
`.deps\mshvsf_saturn_state` rather than committing it.

## Raw evidence locations

Unchanged and still ignored:

- `.deps\mshvsf_saturn_state` — 49 files, 31,517,948 bytes. `session.json`
  SHA-256 `D0A92B7866629106E2472880437C26375E90416B608099184C5BFABD5A547031`;
  per-frame manifests 3540 `1AD8287A...`, 3828 `E1AD044D...`, 3840 `D5EC8CB0...`,
  3900 `7269E80B...`. Every region was re-validated against its manifest hash
  before analysis this session.
- `.deps\mshvsf_saturn_state_incomplete_frame3540` — earlier partial attempt,
  not part of any tracked report; may be removed once the coherent session is
  independently reproduced.

No new capture was taken, so nothing was overwritten.

## Exact commands

```powershell
$py = "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $py .\tools\analyze_mshvsf_saturn_vdp1.py
& $py .\tools\analyze_mshvsf_saturn_video_audio.py
& $py .\tools\analyze_mshvsf_saturn_memory.py
& $py .\tools\build_reference_engine_report.py
& $py .\tools\build_reference_engine_report.py --check
& $py .\tools\run_reference_engine_tests.py
& $py .\tools\validate_mshvsf_training_package.py
```

The two capture analyzers need `.deps\mshvsf_saturn_state`. The model, its
tests, and the validator run from tracked JSON alone.

## Evidence boundary

### Newly measured this session

VDP1, from a real command-processor traversal rather than a stored-order scan:

| Anchor | Reachable slots | Stored in order | Stored nonzero slots | Residue | Drawn |
|---|---:|---:|---:|---:|---:|
| idle 3540 | 296 | 296 | 772 | 476 | 293 |
| normal-active 3828 | 334 | 334 | 772 | 438 | 331 |
| impact 3840 | 308 | 308 | 772 | 464 | 305 |
| recovery 3900 | 307 | 307 | 772 | 465 | 304 |

- Every reachable command at all four anchors uses `JUMP_NEXT`. Zero links
  followed, zero control-flow anomalies, all four terminate on a draw-end. The
  earlier sequential reading was therefore correct here — but that agreement is
  now shown rather than assumed.
- All 1,233 drawn commands across the four anchors are **16x16 normal sprites**
  with identical `CMDPMOD` 0x0880: 16-colour bank mode. No other size, and no
  scaled or distorted sprite, appears in any reachable set. The official port
  draws per 16x16 tile, not from precomposed cels.
- Horizontal flip lives in `CMDCTRL`, not in mirrored art: 101-107 `FLIP_X` per
  anchor, plus `FLIP_Y` and `FLIP_XY` at normal-active.
- Referenced texture spans total 19,968 / 23,552 / 21,632 / 21,504 bytes across
  17-26 merged spans.

VDP2 and SCSP:

- The **VDP2 register block reads back as all zeros** (0 of 288 bytes) at every
  anchor. Layer enables, plane maps, priorities and scroll values cannot be
  decoded from this capture at all. This is an instrument limit.
- Every VDP1 sprite colour bank at every anchor resolves into a **populated**
  16-colour VDP2 colour-RAM bank. All 128 banks are populated; 12-14 are
  referenced per anchor. Colour-bank sprites spend a **VDP2 colour-RAM** budget,
  not a VDP1 texture budget.
- Colour RAM changes inside the combat window while VDP2 VRAM does not: 16 bytes
  in one bank at attack start, none at impact, 35 bytes across three banks at
  recovery.
- Only **three of thirty-two SCSP slots** hold register content, and every active
  slot is byte-identical across all four anchors. Exactly one SCSP
  common-register byte changes per transition, the same byte every time, while
  sound RAM moves ~16 KiB across five pages.

From the AvP-decoded assemblies, computed independently here:

- The selector-6 `budget` field equals the summed 16x16 tile count under the
  candidate attribute bit split for **27 of 28** assemblies. `0x13E36E` declares
  59 against an inferred 57. Strong lead, not a decoded field definition, which
  is why VDP1 command pressure is reported as a range.

### Inferred, with falsification recorded

- Gameplay audio reaches the DAC as a **mixed stream** refilled by a sound
  program, not one keyed SCSP slot per event. Falsified by a slot key-on write
  between the sampled anchors, or by an anchor whose sound RAM is unchanged while
  audio is audibly playing. Four sampled frames cannot see a write between them.
- CPS2 attribute bits 8-11 / 12-15 are a tile span, bits 0-4 a palette index,
  bits 5-6 a per-part flip.

### Still not proven

- Nonzero bytes are not allocator occupancy or a high-water mark.
- Stable cartridge or VDP2 bytes in this window do not prove boot/load ownership
  or full-match residency.
- Player structs, health fields, collision state, hitstop, SH-2 work division,
  CD/DMA activity, VDP2 layer assignment, and per-cue audio attribution remain
  unresolved.
- The reference title's own animation tables are **not decoded**; only its Saturn
  output is measured.
- None of the Marvel addresses, sizes, page counts, command counts, colour-bank
  counts or slot counts is an AvP implementation constant.

## Ordered next work

1. **Locate the Saturn player, health, attack, collision and hit-reaction
   writers.** Use the changed high/low work-RAM pages plus MCP memory
   breakpoints. Add an out-of-range/whiff replay as the falsification control
   before calling any changing field collision or damage. This is the top open
   item and the reference engine's `collision_geometry` and `damage_magnitude`
   claims are blocked on it.
2. **Map referenced VDP1 texture spans to cartridge and VDP1 residency**, and
   find the SH-2 code that builds the command list. The list's shape is now
   known; its owner is not.
3. **Capture team and stage loading**, not combat, to resolve cartridge writes,
   VDP2 changes, CD reads and DMA. If a fresh capture would overwrite existing
   evidence, write to a new ignored directory.
4. **Attribute audio cues through sound-RAM write traces**, not slot registers:
   only three slots are active and none of their registers change, so the
   per-event evidence lives in the buffer refills. Use a whiff control.
5. **Establish VDP2 layer responsibility with a register write watchpoint.** A
   better parser cannot help; the register block is not readable.
6. Add Hadouken only after the normal-hit structures are proven. Use a tag or
   super route later for peak hardware pressure.

## Reference-engine limits worth knowing before extending it

- The scenario binds decoded programs to state roles as an **`ADAPTED` modelling
  choice**. `0x13ce70`, `0x13ce4c` and `0x13cec4` are not proven to be attack,
  impact and recovery animations. The available decoded programs are boss walk
  loops and single-pose loops; there is no decoded attack program yet.
- Trigger and contact frames are scenario inputs, not any game's timing.
- `CollisionEvent` carries no box extents and damage crosses as the token
  `UNRESOLVED_DAMAGE_MAGNITUDE`. The type system prevents inventing either.
- Texture placement is a deterministic first-come allocator chosen for
  reproducible byte accounting, not an observed layout.

Every result must finish the sentence, "This will decide whether AvP should
___," and name the AvP-side probe that must pass first. If it cannot do both,
keep it out of the AvP action plan.
