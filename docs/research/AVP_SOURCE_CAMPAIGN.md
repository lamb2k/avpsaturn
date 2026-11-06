# AvP source campaign

Lead lane: avp-source, branch `learn/source`. Method taken from github.com/lemiur/Game-Decompilation-Skill-For-Claude
(kept at E:\AvP\tools\decomp-skill, outside this repo; it has no licence file, so its text is not copied here).
Project rules in AGENTS.md outrank it. This is research: it moves no card, gate or candidate.

## Target decision: hand assembly, no compiler

Measured over 104,301 reachable instructions (407,232 bytes, 4,656 call targets; `tools/learn_cfg68k.py style`):

| Signal | Compiled C would show | Measured |
| --- | --- | --- |
| `link`/`unlk` frames | common | 0 / 0 |
| stack cleanup right after a call | on most calls with arguments | 0 of 8,431 calls |
| single pushes (`move x,-(a7)`, `pea`) | common | 6 |
| `tst d0` straight after a call | common | 0 |
| result in condition codes (branch right after call) | none | 1,334 |
| call targets entered by falling in from code above | none | 564 of 4,656 |
| `jsr pc-rel` followed by `nop` | none | 37 of 37: an assembler relaxing `jsr abs.l` and padding |
| Sharing a global base register a5 | possible | 8,641 operands |
| Sampled: 0x161de/0x1620a tail sharing, 0x1840e fall-through loops, 16 unrolled `add.w d2,(a0)+` | none | seen |

Candidate options listed as the skill asks: Capcom's in-house 68000 assembler (fits everything above);
a 1990s C compiler such as Microtec, Sierra or GCC (rejected for the whole measured program: no frames, no stack
arguments). No region looked compiled, but the census is global; a lane that finds one reports it.

Consequences:
- Every function is `ORIGINAL-ASM`. There is no compiler, so no byte match, no permuter, no fakematch class.
- Kept from the method: ledgers, disjoint lanes, reader test, helper recovery, wall classes (restated below), one gate at merge.
- The output is readable C and specs for the SH-2 port. It is never reported as "matched".

## The gate

1. **Unit differential (tier: unicorn-differential).** `tools/learn_unit.py`: ROM routine under Unicorn (image merges decrypted
   opcode bytes and data bytes, as the board fetches them) versus the C on the same random inputs. Compares every changed
   RAM/palette byte and the ordered stubbed calls. Needs at least one case that changes memory.
2. **MAME differential (tier: MAME).** For routines with timing or scheduler effects: a bounded probe through the retained
   route (`tools/learn_run_probe.py`, about 70 s), then a test replaying measured values (`source_recon/tests/`).
3. A sensitivity check on any new unit: a deliberate wrong constant must fail the gate.

Emulator tiers only. Nothing here is a Saturn or a CPS2 board result.

## Numbers, reported every time

`python tools/learn_ledger.py report`: **understood under rules** and **gate-passed**, byte-weighted over reachable code and over
the code the Coffee Shop route actually executed.

A function counts as understood when: it has a ledger row with an evidence-based name and a purpose note; its inputs, outputs
and globals are stated; and it passes the reader test (below). It counts as gate-passed when its C also passes a recorded gate run.

## Project profile

- **Dialect:** C90, `gcc -std=c90 -pedantic -Wall -Wextra -Werror` as test.ps1 does. No floats. Fixed widths from avsrc.h; `u32` is
  `unsigned int`, since hosts are LP64 and SH-2 is ILP32.
- **Layout:** `source_recon/avsrc_<module>.c/.h`, one module per lane; gates in `source_recon/gates/<module>.c/.py`; replays in `source_recon/tests/`.
  Style matches the repo's `avsp_*.c`: 4 spaces, snake_case functions, `G_UPPER` for source globals, `CamelCase` types.
- **Names:** from evidence: behaviour, retained labels, the existing SPEC field names. `sub_<addr>` is the placeholder for a callee not yet understood.
  A name you cannot defend is a placeholder. Comments cite source addresses.
- **Reader test:** would someone write this to express the behaviour, without opening the disassembly? So no register-shaped variables (`d0`), no 68000 flag modelling, no gotos that only mirror branches. Registers appear only in the gate adapter.
- **Source quirks** are kept and labelled `/* QUIRK: */` with the evidence (overflow, order dependence).
- **Rule check:** `learn_ledger.py check`, plus gcc flags. Rule changes are the owner's.
- **Parking:** an unfinished function stays out of the ledger or at UNDERSTOOD, with its open point in the note. Nothing is marked done without its gate run.
- **Ledger:** `docs/research/avp_source_ledger.tsv`: addr, size, status, name, unit, gate, note. Short addresses only. Rows merge per row at merge time.
- **No ROM data in commits:** no bytes, no tables, no disassembly listings. Cited addresses and our own constants as needed to implement behaviour; large tables stay extracted at build time. Dumps go under E:\AvP\learning.

## Walls (restated for this target)

| Wall | Signal | Lever |
| --- | --- | --- |
| Call set | stubbed call order differs | callee not understood, or a tail shared across entries: split or reconstruct the callee |
| Control flow | changed bytes differ on some input class | restate the branches; check unstated entry points and fall-ins |
| Hidden input | differs only with unseeded state | a global or register input is missing from the generator: widen seeds |
| Kernel | routine sleeps or yields | stub 0x1060/0x1092 as calls, then write a frame-stepped continuation; MAME tier for timing |

## Coverage denominator

Coffee Shop route to frame 5400 executes 62,042 bytes, 15.24% of reachable code (`cover_a`, fetch tap, prefetch overcounts slightly). Round-1-wide cover is the next denominator.

## Lanes

| Lane | Module | Owns |
| --- | --- | --- |
| 1 lead | route kernel, command ring, fades, tick loop, fast-forward, output | `avsrc_fade`, `avsrc_kernel` |
| 2 | object lifecycle, spawn tables, health and damage, hitstop | `avsrc_actor` |
| 3 | audio command path, Z80 and QSound | `avsrc_audio` |
