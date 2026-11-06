# AvP Saturn backlog

Owner, 2026-11-06: "we can discard the legacy avp claude and codex md files and make a new backlog based on the agent skill and learnings here: https://github.com/freefrank/LostOdysseyRecomp/tree/main/docs/notes".

Sources: the decomp skill (E:\AvP\tools\decomp-skill) and the Lost Odyssey recomp notes (copies in E:\AvP\tools\lo-notes; read recomp.md, recompiler-width-audit.md, critical-section-endian.md and cpu-performance-optimization-guide.md sections 5-8). That repo is GPL-3.0: take methods, not code. The AvP sources and our own lane findings come first where they differ, because that project is a PPC-to-PC recomp and this is 68000 to SH-2 with far less room.

The current state of each item belongs in docs/STATUS.md, not here. Order is priority. Each item ends when its check passes.

## P0: reset the repo

1. **Discard legacy agent files** on `decomp/main`: replace CLAUDE.md and AGENTS.md with short new ones from the skill's template (project profile, the rules below). History keeps the old text. Check: no live doc mentions CLAUDE_ALLOWED, Astra or the card chain.
2. **Doc layout, from the LO notes:** docs/STATUS.md (only source of current state), docs/BACKLOG.md (this file), docs/notes/ with each note marked Reference, Historical, Investigation or Draft, and docs/archive/ for old cards, PARITY_PLAN and handoffs. Evidence grades: Fact, Historical evidence, Assumption, Pre-implementation gate; old numbers never count as today's baseline.
3. **Merge the learning lanes:** learn/source, learn/actor, learn/audio, then re-run all gates once. Fix learn_unit.py first: per-lane work directory, audio hooks, wrong bytes for pc-relative word tables in merged.bin, and FAIL rows from mutation runs polluting gate_runs.tsv. Settle the 2 surviving spawn_table_step mutations.

## P1: first gate (go or no-go)

4. **Measure reachable code:** size, function count, computed jumps, for all rounds and for Round 1 alone. Known lower bound: 407,232 bytes, 104,301 instructions, 4,656 call targets.
5. **Measure the lifted cost:** SH-2 GCC -O2 bytes per 68000 byte on 100+ real lifted functions, projected to 2 MB work RAM + 4 MB cart, with and without per-round CD overlays. Modelled cycles for one busy tick, labelled MODELLED. Report go or no-go to the coordinator.

## P2: the translator

6. **68000-to-C lifter**, generating one C function per recovered function against flat big-endian RAM at original offsets. No interpreter fallback.
7. **Boundary convergence loop** (LO recomp.md): iterate until 0 unresolved targets and 0 unresolved jump tables. Auto-detected tables plus a manual list that survives regeneration; pointer-only functions; addresses built in code; data between functions; the 564 call targets entered by fall-through from the code above. A bad split must never pollute the accumulated target list.
8. **Semantics audit suite** (LO recompiler-width-audit.md): generated-code checks per opcode and form, running the real generator's output against the 68000 in Unicorn or Musashi, with a frozen-bad generator proving the checks can fail. Cover X/N/Z/V/C flags, byte and word writes preserving upper bits, predecrement and postincrement aliasing, movem, dbcc, shifts by large counts, BCD, and sign extension of address words. This is the biggest risk in the lane: LO found 9 translator defect classes only after shipping.
9. **Generation guard:** a single wrapper generates output and writes a receipt with hashes of the generator, inputs and output. Builds refuse stale output.
10. **Tasks and interrupts:** the cooperative kernel and traps on real per-task stacks or state machines; the level 2 IRQ logic run from vblank in a fixed order. Use the proven tick contract from source_recon (one rendered tick per video frame, fast-forward rule, both fade waits).
11. **Guest-visible structures:** assume the game reads what it "shouldn't" (LO critical section lesson). Anything the native layer writes into game RAM stays big-endian at its original offset, with a test.

## P3: whole-game check on host

12. **Host runner:** lifted game on PC with a stub hardware layer. Check: boots and reaches Round 1 with no emulator core.
13. **Differential against MAME:** same inputs, compare work RAM and object list per vblank; report the first divergent frame and the writer. Goal: through Round 1 and its boss.
14. **State fixtures** (LO debug teleport): jump to any route point from saved RAM, with a real pad-driven input script, so checks stay under 1 minute and never need a replay from boot.

## P4: Saturn layer (concepts, no fake hardware)

15. **Sprites:** object list to VDP1, using the tile and AVT2 work. Check: stills against MAME for a scene set.
16. **Backgrounds:** scroll layers to VDP2, plus palette to CRAM with up to 32 banks and a capacity refusal; run the path above 16 banks, which has never run.
17. **Memory map:** decide with real numbers: DRAM0 tile carve, code overlays, no mid-round reads. Owner decides if the numbers don't settle it.
18. **Input:** real pad through the game's own input latch.
19. **Audio:** the game's command ring (63 entries, silent drop when full) to a native sender with pan, mode and rates; music to CDDA, SFX in SCSP RAM; per-channel priority rule; the 11 kHz budget. Correct the wrong pointers in oracle11_global_audio_load_release.json. Decode the Z80 sequencer only if needed.
20. **Slave SH-2:** drawing work on the slave, game logic on the master. Single owner per structure, explicit handoff, no splitting game functions across CPUs (LO anti-pattern).

## P5: make it fast and readable

21. **Profile first:** frame cost by function on the real image; old figures (39 ms master, compose 34%, tile find 13%) are Historical evidence until re-measured. Emulator speed isn't Saturn timing, so get cycle-accurate or hardware numbers before trusting any gain.
22. **Experiment rules** (LO section 8): fixed build and scene, one variable, mean and tail, whole frame not just the target. Stop and roll back if p95 rises or the gain moves elsewhere.
23. **Readable C campaign** (orchestrator): disjoint lanes, hottest first, each function behaviour-gated, then replacing the lifted one. Report both numbers. Order: kernel, pools and spawn, damage, player, enemy AI per class, class 0x0c and 0x0e, hit effects, route, boss. Reuse wall-identifier when stuck.
24. **Shrink:** after hot functions, drop lifted flag work proven dead, shared helpers (helper-recovery), and overlay anything cold.

## P6: playable and on hardware

25. **First playable:** Predator Warrior, Round 1 start to boss clear, including KO and continue, with real pad on the emulator, and the whole-game check green to the same frame.
26. **Hardware package:** ISO, cue, hashes, HARDWARE_TEST steps for the owner's Saturn with a 4 MB cart. Physical stays UNRUN until the owner runs it. Physical frame-cost readout included.
27. **Rest of the game:** other rounds, other characters, front end, co-op. Sized after item 25. Round 2 handoff first.

## Open questions for the owner, when numbers exist

- Fast-forward rate: fixed 3 ticks or the arcade's 3 to 5.
- Whether a lower frame rate on the busiest scenes is acceptable if 60 can't hold.

Not carried over: the REIMPLEMENT-13 counters, containment of uncovered enemies (retired once the lifted game runs), captured schedules, the Oracle-to-SPEC firewall, the old run budget.
