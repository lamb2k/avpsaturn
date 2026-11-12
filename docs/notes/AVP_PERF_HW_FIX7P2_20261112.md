# fix7p2: placement coverage, data-move exactness settled, Wolverine / versus / restart checks (lane perf-hw, 2026-11-12)

Disc `avp_3h_A_fix7p2`, source commit `bda411e` (readout id `F2 BDA411`), branch `lane/perf-hw-20261112`. It replaces `avp_3h_A_fix7p1` (kept as it was). Same five switches as fix7p1 (`SAT_PLACE_FN`, `SAT_HOT_STACK_HW`, `SAT_HOT_GFXRAM_HW`, `SAT_HOT_GFX_HW`, `SAT_PROF_LINE`), all ON in the recipe, all off in the tree. Read `AVP_PERF_HW_20261112.md` first for the cost model and the hot paths. Labels as there: EMULATED = strict Ymir (my copy), MODELLED = the same Ymir with the board's memory costs, CONSOLE = owner photos only (none for this disc).

## 1. What changed from fix7p1
1. **More scenes decide the placement.** `saturn/rt/place_fn.json` now sums 18 profiled runs: the stage select entries 0 to 13 (stage 1-1 twice, the stage 1 and 2 bosses, stages 2 to 6, the boss stages, the bonus stage) and the scripted route from boot (title, attract, round card, stage 1, stage 2). 2,216 functions have heat, 1,882 ran, 738 KB of code ran somewhere.
2. **Rule: code that ran in fix7n4's high RAM stays in high RAM.** `plan_functions` first keeps every function that ran in any scene and sat in high RAM before (about 310 KB), then fills the rest of the 487 KB (1,214 functions; 323 functions, 155 KB, moved in) by cost per byte. Nothing that ran in fix7n4's high RAM is demoted.
3. **A bug in the heat keys.** Split-off bodies shared by two functions (`f_aa8ea.part.0` and `f_aa886.part.0` are one body, kept in the section named after the other) were credited to one name; the linker section carries the other, so the hottest function in the Wolverine fight (30 M instructions) stayed in low RAM. `fn_heat.py` now credits every name at that address.
4. **The compiler's helper routines go to high RAM.** `__sdivsi3`, the shift and block-move routines (libgcc, 1.3 KB) sat in low RAM and were 3.5 % of the master's instructions in a Wolverine fight. `*libgcc.a:*` is now in the `.hw` section.
5. **Test flag `SAT_INPUT_SCRIPT_TICK`** (section 4) and `SAT_BOOT_CLEAR_EQ`, `SAT_FSEC_ONLY`, `.cartcode` for the script: test builds only.

## 2. Placement coverage (item 2)
Share of the master's instructions (game tick and vblank handler) that run from high RAM, low RAM and the cart, in fix7p2, from the PCs my Ymir saw:

| scene | build | high RAM | low RAM | cart |
|---|---|---|---|---|
| stage 1-1 Coffee Shop crowd, Predator Warrior | fix7n4 | 41.8 % | 53.0 % | 5.2 % |
| same | fix7p1 | 97.0 % | 2.8 % | 0.2 % |
| same | **fix7p2** | **99.6 %** | 0.2 % | 0.3 % |
| stage 1-1, Wolverine | fix7p1 (before the fixes of section 1) | 95.2 % | 4.4 % | 0.5 % |
| same | **fix7p2** | **99.2 %** | 0.35 % | 0.5 % |
| versus round (Warrior against Wolverine) | **fix7p2** | **98.8 %** | 0.5 % | 0.6 % |

**High RAM free after the rebuild: 56 bytes** (fix7n4 924, fix7p1 72). Low RAM free 2,440 (fix7n4 96); cart tail free 2,444 (fix7n4 5,008; `cold1_at` unchanged, the 4 KB step is not crossed). The planner relinks until both RAMs fit, so a change that grows high RAM makes it demote cold code instead of failing.

Not profiled and therefore still decided by the other scenes: the ending and the post-credits reveal (not reachable without clearing the game), ranking after a game over (the continue screens were reached, the ranking was not), Mega Man (section 5), the boss rush mode.

## 3. MODELLED before and after, with the new disc (stage 1-1 crowd as in the first note; windows with a load catch-up left out)
| run | build | TICK | MISS | DONE | PIC |
|---|---|---|---|---|---|
| model | fix7n4 | 56.0 | 32.9 | 27.1 | 31.9 |
| model | fix7p1 | 60.0 | 0 | 60 | 39.0 |
| model | **fix7p2** | **60.0** | **0** | **60** | **43.9** |
| stock Ymir (EMULATED) | fix7n4 / fix7p1 / **fix7p2** | 60 | 0 | 60 | 52.3 / 57.8 / **57.7** |
| model, stage 1-2 boss, MISS / PIC | fix7n4 / fix7p1 / **fix7p2** | | 4.7 / 0 / **0** | | 43.1 / 54.2 / **57.7** |
| model, stage 2-1, MISS / PIC | fix7n4 / fix7p1 / **fix7p2** | | 3.2 / 0 / **0** | | 44.7 / 56.5 / **57.3** |
The libgcc routines and the alias fix are worth about 3 to 5 PIC points in the model. PIC in the crowd is still limited by the slave (note 1, section 11).

## 4. Data-move exactness (item 3)
**The first-field offset is explained, and it was in the test, not in the build.** My vblank-indexed pad script gives the game its inputs by vblank. The data moves change the work between the CD finishing and the game's dispatcher starting, so the game starts at another phase of the video frame, one game tick lands on the other side of the first vblank, and from then on a tick sees the pad word of another vblank. The game's state depends on that (controls: a master 1 % slower diverges after 4,000 ticks). It was never a difference in what the game does.

**Re-test with inputs indexed by game ticks** (`SAT_INPUT_SCRIPT_TICK`, pad.c): inside a stage the script advances by the game's own tick counter (ff8019 summed), counted from the stage's entry; outside a stage it is the vblank as before. The probe dumps all 64 KB of game RAM (the 68000's work RAM, including the random number state) at stage-relative ticks 300, 600, 1000, 1500, 2000, 3000 and 3500. Reference build `B0T` = fix7n4 layout with the same PROF line, script and boot-clear test flag (so the instructions are the same); builds under test `P3T` and `P4T` = the placement build.
- **Flat memory cost (`HW_FLAT=1`, placement cannot move time): the RAM is identical at all 7 marks for both P3T and P4T.** All 65,536 bytes, every mark.
- **Stock timing (cache on, the regions cost differently): 3 to 4 bytes differ at each mark, all in the 68000 stack scratch (ff7fc6 to ff7fe7), none in game state.** That is the interrupt landing at another instruction.
- Same tick, stage 2 starts in both builds: stage 1 lasts 3,982 ticks in each; the vblank of that moment differs by 16 (the load takes longer in the new layout in the flat model, not a game difference).
So the data switches (and PLACE_FN with them) are exact over a tick-aligned route: same game state, same kills, same stage progress, no desync. The data switches stay ON. Not covered: the state after the stage change (the script restarts its tick base only at the next stage word of zero) and after a load.

## 5. Ymir checks on the fix7p2 source with Wolverine on (item 1)
Test build `W4` = the shipped recipe with `GUEST_DEFAULT=1` (his panel on the character select, his talk boxes), same placement (the cart is the same as the release disc's), fresh backup RAM, my own Ymir, pad file only. Misalignment log checked per run with `tools/ymir_misalign_gate.py --check`.

| check | result | misalignment gate |
|---|---|---|
| Wolverine's first talk box | "They keep coming, bub. We gotta fall back!" drew with his face, play went on (W3 and W4) | 0 data accesses |
| two continues | KO, CONTINUE 27, character select, play; KO again, CONTINUE 26, play; the stage 2 file loaded (`LD2 F214`) with his later talk boxes ("More than we can handle right now!", "Lucky break. We lost 'em for now.") | 0 |
| quit to title and start again | **plays as Predator Hunter or Warrior: works. As Wolverine: crashes on the second start** (below) | 1 data access, the crash |
| one versus round | duel setup, character select, ROUND I, the fight loaded and ran for 4 minutes with both fighters active (moves, attack effects, HUD); no KO reached | 0 |
| shipped route (boot, title, stage 1, KO, continue with another character) | passes | 0 (5,978 instruction fetch artefacts filtered) |
| Mega Man | **not in the recipe**: it needs `SAT_GUEST_DATA` assets from the Mega Man lane and a different disc; not built, not run | |

**A crash that is not new.** Wolverine, quit to title from the pause menu, start the arcade again: black screen with a garbled readout, one misaligned 16-bit read (`PC` in `f_a9cb6`/`f_a9d18`, address 0x0263B1E7, the opcode view), on every fix7p2 and fix7p1 build I tried (W3, W4, timing varied by 2 % and 15 %), and **also on the baseline: a build of the fix7n4 source with Wolverine on (`W0`) reads the same address from the same function and ends at the Sega logo.** It happens with Wolverine in play when quitting; it did not happen when I quit as Predator Hunter after continuing, nor as Predator Warrior on fix7n4 or fix7p2. I did not find the cause (a state that the restart does not clear; the read goes through a garbage 68000 pointer). It is outside this lane's change, but the owner's "quit to title" test with Wolverine will hit it on every disc. Repro: arcade, choose Wolverine, play 25 s, Start, QUIT TO TITLE, Start, ARCADE, wait.

## 6. Gates on fix7p2
- Build (the build fails on them): `vdp2_cycle_check` PASS; alignment gate 325 data symbols (0 of unknown type), 46 reviewed cast sites, 197 accessor calls, 287 round files and `REVEAL.BIN`, 0 hits; boot data addresses ok; Wolverine block canary ok; budgets as in section 2.
- Tests: `align_gate_test` (13 checks), `lat_protocol_test`, `vdp2_cycle_check_test`: pass (run on the tree of fix7p1; no tested file changed in fix7p2).
- Strict Ymir stock timing, stage 1-1: TICK 60, MISS 0, PIC 57.7.
- Ymir misalignment gate, default route on the release disc: 0 data accesses.

## 7. Risks
- The restart crash with Wolverine (section 5) is old, not new, and unexplained.
- Only 18 scenes decided the placement; the ending, the ranking screens and Mega Man were not profiled. A function none of them ran sits in low RAM or the cart (a few hundred KB of never-run code). The tool and `place_fn.json` take more scenes; a rebuild takes about 13 minutes.
- High RAM free is 56 bytes.
- The model's cart figure is assumed and master/slave bus contention is not modelled (first note, section 10).
- The tick-aligned test covers stage 1 (3,500 ticks); the stage change and the load are not tick-aligned.
