# Open-risk register before fix7n goes on the console (2026-11-11)

Source commit of the staged discs: `1ca3e82` (fix7n = FIT 2, fix7b = FIT 1; both carry the build id on the readout's third line). "Closed" = shown off-hardware; "reduced" = less likely or bounded, not shown; "console-only" = only the Saturn can tell.

| # | Risk | Status | Evidence |
|---|---|---|---|
| 1 | NBG2 (HUD/text) striped although its F5 schedule met every manual rule | **console-only** (root cause); reduced by the changes in fix7/fix7n | below: ranked hypotheses; the F5 register image rules out colour calc, windows, mosaic and line scroll for NBG2 |
| 2 | Crop screens never looked at | closed for 12 screens, **unchecked** for story captions, CREDITS line, post-credits reveal, Wolverine pick | below |
| 3 | Gameplay hidden by the 16 px crop | measured; the importance is a play judgement (**console / owner**) | 3 scripted Ymir runs, numbers below |
| 4 | Torn read in the register record | **closed** (model) and a real hole in the retry path found and fixed | `tests/lat_protocol_test.py`: new routine 0 mixed records in 26,447 states, previous routine 720 |
| 5 | fix7b never traced | **closed** | 6,364 judged bursts, 0 rule breaks, 6,962 vblanks, one 24 register burst per vblank, 0 slave writes |
| 6 | CPU slot throughput | **reduced** (MODELLED) | below |
| 7 | Owner must diagnose | **closed** | README "WHAT TO PHOTOGRAPH" in both discs; build id on the readout (third line, not the second: line 2 has no room) |

## 1. NBG2: what was re-read and what could explain it
Photos (a98ec4dc title, 1ecb9e05 select, c8dc9bde and b677c290 stage 1), per layer: NBG0/NBG1 backdrop and logo striped (certain); NBG3 menu text and readout panel clean (certain); NBG2: the top "Maj. Schaefer" and "PRESS START" copy in c8dc9bde is washed with vertical cuts, the select labels and both PRESS START copies in 1ecb9e05 are streaked, the lower HUD copy in c8dc9bde reads crisp except where an alien tail crosses it ("PRESS START" there is whole, "Maj.S?aefer" has a gap). So NBG2 is affected at least in some regions; contrast hides it on flat backgrounds.
Register image of NBG2 in F5 stage 1 (strict Ymir register log): CHCTLB 0 (1x1 cells, 16 colours), PNC 0 (two-word names), PLSZ N2 one page, map 0x4000, SCXN2/SCYN2 integer only (NBG2 has no fraction or zoom registers), priority 6 (above sprites 5 and NBG0 4, NBG1 2), CCCTL 0, window registers 0, MZCTL 0, SCRCTL line scroll only on NBG0. Colour calculation, windows, mosaic, line scroll and zoom are therefore not a cause for NBG2.
Ranked hypotheses (none proven):
1. Live CPU writes into banks with no valid CPU slot. F5 had no CPU slot anywhere; fix6's slots were not valid pairs. NBG0/NBG1/NBG2 data are rewritten during display (cell uploads, name writes); NBG3's font and panel are written rarely. If a VDP2 write that finds no slot is lost or garbled, tiles uploaded live would stay damaged (stripes persist in static scenes) while NBG3 and the VDP1 sprites stay clean, which fits all four photos. The manual only says the CPU waits for its slot; it does not say what happens without one, so this is a mechanism candidate, not a fact. fix7/fix7n: valid pairs (A T7, B T4-T7): addresses it.
2. Cross-layer effect inside bank A0: in F5, NBG0 had 1 name read where 2 are required, in the same bank whose name pipeline NBG2 and NBG1 also use. fix7/fix7n: counts correct.
3. Visibility: NBG2 sits over striped layers, so stripes in NBG2 pixels and stripes seen through transparent NBG2 pixels look alike. Not testable from the photos. No change.
4. Mid-frame register writes by the slave (BGON, priorities, scroll): produce horizontal bands, not columns; fixed by the latch in any case.
5. Two-word versus one-word names (NBG0-2 two words, NBG3 one word): the manual's tables do not depend on name size; no rule found. No change.
6. Colour calculation / windows / mosaic / line scroll: rejected by the register image.
fix7n changes 1, 2 and 4. If fix7n is clean on NBG0, NBG1 and NBG2 alike, hypotheses 1 and 2 are both in play; the discs cannot separate them. If NBG2 stays striped on fix7n, hypotheses 3 and 5 are what is left.

## 2. Crop screens checked with fix7n in strict Ymir (screenshots in the lane scratchpad, `sc_s1` to `sc_s7`, `sheet_s*.png`)
Title and mode list; OPTION MODE, GAME OPTION (DIFFICULTY, EXTEND, CONTINUE, LIVES, BONUS CHARACTERS OFF/WOLVERINE), BUTTON CONFIG, SOUND OPTION, SCREEN ADJUST (X/Y, "PAD MOVES A CENTRE", "PRESS START BUTTON TO EXIT"); character select; STAGE SELECT MODE list (STAGE 1-1 AREA 1 OF 2, 1-2 BOSS CHRYSALIS, 2-2 BOSS RAZOR CLAWS); ROUND I title; stage 1 and the 2-2 boss stage in play (health bars, portrait, name, score, 1P/2P PRESS START, boss stage bottom bar); dialogue boxes ("They just keep coming! We have to fall back!", "It's not an ordinary alien. Its speed is incredible..."); continue screen with the 48 column line; GAME OVER (red fade and text); ranking, four pages. Nothing cut and nothing misaligned in those. Not reached: story captions between stages, the CREDITS line (free play shows none), the reveal (needs the ending), selecting Wolverine (with BONUS CHARACTERS set to WOLVERINE the select still showed the four standard panels in Ymir; not pursued).

## 3. Edge gameplay (`SAT_EDGE_STATS` measurement build, FIT 2, never staged; counters kept in VRAM, read by the patched Ymir)
Counts sprite objects (the arcade's object list entries, not the background) whose 384 column box touches the outer 16 columns on either side, over scripted random-pad runs: stage 1 (80 s of play), two stage-select stages (29 s and 38 s before the character died).
| run | objects per picture | touching a strip per picture | entirely in a strip per picture | straddling the 384 edge | pictures with one touching | pictures with one entirely hidden |
|---|---|---|---|---|---|---|
| stage 1 | 82.8 | 24.8 | 4.4 | 17.3 | 96.3 % | 70.1 % |
| stage select 1 | 86.6 | 21.4 | 3.2 | 16.3 | 89.4 % | 59.1 % |
| stage select 2 | 88.7 | 20.9 | 3.1 | 15.8 | 89.7 % | 59.9 % |
Geometry only (no enemy / projectile / pickup classification, no hit or attack boxes: those are game RAM state not captured). It says how often the crop hides sprite pixels (most pictures), not whether any of it matters.

## 4. Record latch protocol
`tests/lat_protocol_test.py` models `lat_publish` (slave: sequence word odd, copy, even) and `lat_apply` (master) step by step and searches every interleaving of three publishes with one apply (MODELLED, no C run: no host gcc). Finding: the apply as staged in fix7 (write registers while reading, verify afterwards) can leave a mixed record on the chip when the slave publishes during the apply and every retry then fails (720 of 904 terminal states in the model). Fixed: `lat_apply` copies the record to a snapshot, checks the sequence word before and after, and writes the chip only from a verified copy (0 of 2,078 terminal states mixed). Both fix7b and fix7n use the fixed routine.

## 6. CPU slot throughput (MODELLED)
Writes measured in strict Ymir (fix7n gameplay and menus): mean about 100 bytes per vblank over all four banks (about 6 KB/s; the readout alone is 1,680 bytes/s in B1), busiest second 44 to 58 KB in bank A1 (stage load, tile refill) and up to 52 KB in B0. Capacity with the new words: bank A has one CPU slot per cycle of 8 timings, a cycle is 8 dots (one timing per dot, 352 dots = 44 cycles per line), so 224 x 44 = 9,856 long-word slots in the active picture = about 39 KB per frame, 2.4 MB/s, plus every timing in the blanking periods; bank B four slots per cycle, about 158 KB per frame. The busiest measured second (58 KB over 60 frames) uses about 2.5 % of bank A's active slots; a whole-layer refill in one frame (16 KB of names) about 40 %, plus the SH-2's own B-bus cost (about 4 ms for 16 KB if a long write is about 1 microsecond: ASSUMED). So the slots keep up with margin; the unknown is the real bus cost per write.
