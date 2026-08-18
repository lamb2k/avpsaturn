# MSHvSF Saturn reference-lane handoff

Updated: 2026-08-18 EDT

## Repository boundary

- Worktree: `C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest-MSHvSF`
- Branch: `codex/mshvsf-reference-lane`
- Starting checkpoint: `43e88acaf3db002a3aa86c1d636cf1e926d04326`
- AvP remains in the separate
  `C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest` worktree on
  `codex/avp-master-plan`.
- Never switch, merge, or bulk cherry-pick between the lanes. Marvel findings
  are candidate Saturn patterns until an AvP-specific probe validates them.

The authorized Marvel CPS2/Saturn inputs and Marvel-only ignored evidence were
moved into this worktree. Shared MAME 0.289, emulator, and Capstone directories
are local junctions to the AvP checkout's read-only dependency copies. Do not
move them back merely to make the AvP checkout self-contained.

## Baseline verification

- MAME 0.289: `romset mshvsf is good`; `1 romsets found, 1 were OK`.
- CPS2 vertical slice: 401 frames validated; 30 low-confidence step-decrease
  leads retained.
- Training package: 19 JSON artifacts, ten documents, six correspondence
  records, and six patterns after this checkpoint.
- No MAME, Yaba Sanshiro, Mednafen, or RetroArch process remained after the
  synchronized capture.

The audit now records `<reference-root>/Mame` and `<mame-executable>` instead
of checkout-specific absolute paths, so a valid worktree relocation does not
dirty the tracked report.

## Stock Yaba MCP capability

Installed Yaba Sanshiro 2 v1.20.37 includes a Debug menu with Master/Slave SH-2,
VDP1, VDP2, SCSP, memory-editor, trace-logging, and MCP debug-server controls.
The MCP server listens on localhost port 9640 and supports pause/resume,
registers, memory reads/writes, disassembly, breakpoints, execution history,
and interpreter/dynarec switching. No custom emulator build was required.

Emulator executable:

- bytes: `27,637,248`
- SHA-256: `016112708FC77EC53B8A36C4EF52E300A78B3FB079E815F60B1A51FA1661999C`

The older local source checkpoint `71c973f92966d33de464c1ba4dac1953af6ec462`
documents the memory model but does not contain this newer MCP frontend. Do not
claim that source checkpoint as the MCP implementation provenance.

## Exact-frame normal-hit memory capture

Run from this worktree:

```powershell
.\capture_mshvsf_saturn_memory.ps1
```

The wrapper enables the stock MCP server, runs the proven play record, captures
exact frames 3540, 3828, 3840, and 3900, resumes after the final anchor, and
generates `data/mshvsf_saturn_runtime_memory.json`. It refuses to overwrite an
existing raw capture.

Raw evidence: `.deps\mshvsf_saturn_state` (49 files, 31,517,948 bytes).

- `session.json` SHA-256:
  `D0A92B7866629106E2472880437C26375E90416B608099184C5BFABD5A547031`
- frame 3540 manifest:
  `1AD8287A0C1AB477D004EC54D31427BCA91E2FFD58B4D9E876677ECEF65FB626`
- frame 3828 manifest:
  `E1AD044D9A5FB99402ADFE6BF3F8301975439E7DBEB989600A628D5BB04CFFC4`
- frame 3840 manifest:
  `D5EC8CB098F395A98B6CE13624C095BFA5834B0EB1C37BA03E92A31B3AA4E4CD`
- frame 3900 manifest:
  `7269E80B1CEC826D0D54BEE228939298FE9D377F670472B71BBEB802647E2842`
- tracked report SHA-256 before any later regeneration:
  `1C2DAE62E7AC8E288C9DC7A71C0ADD62FE3DCC0EE14BF531FF2749D1D289B15A`

An earlier incomplete but valid frame-3540 attempt is preserved at
`.deps\mshvsf_saturn_state_incomplete_frame3540`; it is not part of the tracked
report and may be removed after the coherent session is independently
reproduced.

## Evidence boundary

Measured on Marvel:

- Cartridge DRAM has 3,549,571 nonzero bytes across 909 4 KiB pages and remains
  byte-identical from idle through recovery.
- VDP2 VRAM and the sampled VDP2 registers remain byte-identical through the
  same short combat window.
- VDP1's sequential list contains 296 commands at idle, 334 at normal-active,
  308 at impact, and 307 at recovery.
- Normal-active to impact changes 10,295 high-work-RAM bytes across 39 pages,
  92 low-work-RAM bytes across two pages, 5,443 VDP1 bytes across five pages,
  and 16,193 sound-RAM bytes across five pages.

Not proven:

- Nonzero bytes are not allocator occupancy or a high-water mark.
- The VDP1 parser does not yet follow jump/call control flow.
- Stable cartridge or VDP2 bytes in this window do not prove boot/load
  ownership or full-match residency.
- Player structs, health fields, collision state, hitstop, SH-2 ownership,
  CD/DMA activity, and SCSP slot ownership remain unresolved.
- None of the Marvel addresses, sizes, page counts, or command counts is an AvP
  implementation constant.

## Ordered next work

1. Use the changed high/low work-RAM pages plus MCP memory breakpoints to locate
   the Saturn player, health, attack, collision, and hit-reaction writers. Add
   an out-of-range/whiff replay as the falsification control.
2. Extend the VDP1 analyzer to follow command jump/call/return flow and map
   referenced texture spans at the four anchors.
3. Capture team and stage loading to locate cartridge writes, VDP2 changes,
   CD reads, and DMA activity. The stable combat window cannot answer those
   ownership questions.
4. Isolate normal and impact audio events through SCSP slot/register traces.
5. Add Hadouken only after the normal-hit structures are proven. Use a tag or
   super route later for peak hardware pressure.

Every result must finish the sentence, "This will decide whether AvP should
___." If it cannot name a near-term AvP Saturn design decision and an AvP-side
validation probe, keep it out of the AvP action plan.
