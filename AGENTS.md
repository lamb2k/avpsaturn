# AvP Saturn: decompilation campaign guide

Owner, 2026-11-06: "yes pelase write code you can completely rethink the approach since it didn't make much progress ebfore and leverage the apoproach from the decomp / recomp repo", then "I emant the decomp / recomp agent skill iuf there are best practices for that coordinattor that supersese the prvious avp attempt".

This replaces Codex ownership, Astra selection, one-writer rule, `CLAUDE_ALLOWED`, the task-card chain, the old PARITY_PLAN and REIMPLEMENT-13's counters. The old versions are in docs/archive/decomp-reset-20261106.
Method: the skills at E:\AvP\tools\decomp-skill\.claude\skills (not copied here; no licence file). Plan: docs/PARITY_PLAN.md. Campaign detail: docs/research/AVP_SOURCE_CAMPAIGN.md.

## What stays

- Private repo only. No public remote; no ROM, derived assets, listings or dumps outside the private repo and this PC. Raw dumps under E:\AvP.
- Evidence tiers on every result: HOST, MAME, EMULATOR, HARDWARE. Never claim hardware without hardware. Modelled numbers say MODELLED.
- Never touch `history.txt` or `data/avsp_anim_records.json`. Keep NOTICE.md and every licence file. Stage named paths only. No force-push, reset or clean on shared trees.
- Set `avspu` USA 940520, MAME 0.289.

## Objective

The ROM's program is the source. A lifter gives one C function per recovered 68000 function (throwaway scaffold); a hardware layer maps object list, scroll, palette and sound to VDP1, VDP2, CRAM and SCSP/CDDA by concept; workers replace lifted functions with readable C, hottest and most-called first. Target: SH-2. First playable: Predator Warrior, Round 1 start to boss, real pad input in emulator, then a package for a real Saturn with a 4 MB cart.

Anti-emulation boundary: no register interpreter, opcode switch or fake VRAM in the target layer.

## Project adapter

| Verb | Command |
| --- | --- |
| `disasm` / `xref` | `python tools/learn_dis68k.py START END`, `... xref ADDR`; code map `tools/learn_cfg68k.py` |
| `gate` (function) | `python tools/learn_unit.py UNIT|all [CASES]`, behaviour against the ROM routine (test only) |
| `gate` (whole game) | per-vblank work-RAM and object-list comparison with MAME 0.289 from the same inputs |
| `rules` | `python tools/learn_ledger.py check` plus gcc strict flags |
| `report` | `python tools/learn_ledger.py report` |
| `build` | `build.ps1` for the Saturn image; SH-2 gcc is .deps/joengine/Compiler/WINDOWS/bin |

- **Toolchain:** SH-2 GCC -O2 for target; host gcc in WSL, C90, `-Wall -Wextra -Werror`.
- **Match test:** byte matching does not apply (hand assembly, compiled for SH-2). Same inputs must give the same RAM and register effects as the 68000 original. Report as behaviour-matched, never "matched bytes".
- **Annotation:** source address in a comment: `/* source 0x1620a */`.

## Scores, every report

1. **Functions readable and behaviour-matched under the rules.**
2. **Functions lifted and passing.**
Plus the frames the whole-game comparison holds to, and the tier.

## Code rules (project profile)

Dialect, layout, names, placeholders, parking and ledger: docs/research/AVP_SOURCE_CAMPAIGN.md, "Project profile". Reader test: would someone write this to express the behaviour without opening the disassembly? A function that only works by transliterating registers is open work.

## Lanes

Disjoint worktrees under E:\AvP\worktrees, up to 4 workers; the orchestrator merges into `decomp/main` per the skill's merge procedure. Hold new batches under 12 GB free commit; pause if C: is under 16 GB free. Evidence on E:\AvP. Yaba runs take the lock (port 9640, shared yabause.ini; restore VideoCore 4 / SoundCore 1), under 1 minute where possible.
