# fix7n3: alignment gate, Wolverine in Ymir, power-up report, HUD inset (2026-11-12)

Disc `avp_3h_A_fix7n3` (source 2cb8435, FIT 2). Base: fix7n2 (`AVP_HWBOOT_FIX7N2_20261111.md`). Labels: EMULATOR = strict Ymir (real JP BIOS, 4 MB cart); CONSOLE = owner photos; INFERRED = reasoning only.

## 1. Alignment gate (build NO-GO), `tools/align_gate.py`
Why: the SH-2 raises an address error for a 16 bit access at an odd address and a 32 bit access at an address that is not a multiple of 4. Ymir and Yaba accept both. The Wolverine talk-box freeze (fix7n2) was one such read.
What it checks, on the build's own outputs (run by `saturn/rt/build.py` before the image; `align_gate.txt` in the work dir):
- **Data objects** (every nm symbol inside a `.data/.rodata/.bss` input section of the link map, `sat.elf` and `boot.elf`; 318 in the final build): byte-typed objects of 4 bytes or more must be 4 aligned, wide-typed ones aligned to their element width. The type comes from the declaration in the sources or the generated includes. The bases `RAMB`, `ROMB`, `OPX`, `SAT_PACK`, `SAT_OBJ`, `SAT_SINK` must be 4 aligned (`lift_target.h` RAM32/ROM32 and the pack readers assume it).
- **Cast sites**: every non-literal cast to a 16/32 bit pointer in `saturn/**/*.c,h,inc` (46) must be on the reviewed list `tools/align_sites.txt`, keyed by file and a hash of the normalised line, each with the reason it is aligned or why a byte path exists. A new or edited line fails the build until it is reviewed. Casts of literal hardware addresses and of the address of a typed object are skipped.
- **Accessor offsets** (197 calls of be16/be32/get32/put16/put32/put32_ram/put32b/ld32/copy8): a literal byte offset added to the pointer must be a multiple of the width.
- **Disc files** (`tools/align_packs.py`): all 287 round files (region destinations and lengths, section tables, spill table and spill destinations, rowtrim base and offset tables) and `REVEAL.BIN` (record offsets).
- **Strict Ymir data-misalignment log** (`tools/ymir_misalign_gate.py --run CUE`, or `--check LOG`): runs the patched strict Ymir (SW_SHOWNOACTIVATE, keys posted to its own window), then fails on any logged access whose PC differs from the address. Lines with PC equal to the address are the emulator's own 32 bit instruction fetches at a 2 mod 4 PC (about 6,000 to 8,000 distinct per run), not data accesses.
Tests: `tests/align_gate_test.py` (misaligned object, unreviewed and edited cast, odd offsets, misaligned spill, Ymir log with a data line: each caught; the clean forms pass).

**Hits found and fixed**

| hit | what | fix |
|---|---|---|
| `guest_face_data` at 0x027F6D86 | the fix7n2 freeze (already fixed) | aligned in the generator; the gate catches it again (control below) |
| `name_saved` (u8[2][16]) at 3 mod 4, `sat_home_text` (char[28][44]) at 2 mod 4 | byte objects not 4 aligned; no wide access known, flagged by the byte-data rule | `aligned(4)` |
| `vram_copy` SCU DMA experiment (`SAT_TILE_DMA`, off) | the DMA reads longs: an unaligned source or odd length would break | byte copy then |
| round files, offsets, other casts | none | none |

**Positive controls (EMULATOR)**: `SAT_ALIGN_CONTROL` + `HUD_FACE_ALIGN=0` + `ALIGN_CONTROL=1` build the old bug back (face cells at 2 mod 4, long reads). The symbol gate listed `guest_face_data at 0x027f6d86 ... is 2 mod 4`; strict Ymir on that disc, Wolverine talk box, logged `READ SH2-S PC=0601952C addr=027F6D86 32-bit` and the gate failed on it. Normal builds refuse `SAT_ALIGN_CONTROL` unless `ALIGN_CONTROL=1`.
**Results on the normal builds (EMULATOR)**: 0 data accesses in boot, title, stage 1, KO, continue (same and another character) and the next stage; 0 in a 5.5 minute Wolverine play with three continues and a stage 2 load.
**Limits**: the cast scan is a pattern scan (a wide-typed pointer variable assigned without a cast is not seen); the Ymir log only covers what the route runs; the deliberate misaligned read in `fps_hud.c` (a second control) was not logged (the compiler may have split it); only the face read is a proven control; the sound packs are read byte-wise (checked in `sat_audio.c`), other data files are read as bytes or through the checked pack structures.

## 2. Wolverine in Ymir (EMULATOR, `GUEST_DEFAULT=1` test build of the same source; fix7n3 itself ships with BONUS CHARACTERS OFF by default as before)
- Why the 1P cursor "would not move" earlier: key timing, not the game. The earlier scripted keys reached the select screen at a different time from the keys on a slow host, and Start/A confirmed Warrior first. With a pad-file driver and a screenshot state check the cursor moves: from the Warrior panel one `right` puts it on WOLVERINE (top right); a second `right` stays. The panel is shown only when BONUS CHARACTERS includes WOLVERINE (his slot is Schaefer's; OPTION MODE cycles OFF, WOLVERINE, MEGA MAN, BOTH) and the saved setting overrides the build default (backup RAM bit 8), so a fresh backup RAM plus `-DSAT_GUEST_DEFAULT=1` gives a deterministic run.
- Played from the title: select Wolverine, stage 1 (file F210, `LD1 F210 S1030`), his talk boxes drew with his face ("They keep coming, bub. We gotta fall back!", "More than we can handle right now!"), no fault. Three KOs, three CONTINUEs: each continue shows SELECT YOUR CHARACTER, picks him again, play resumes; stage 2 loaded (`LD4 F214`); game over and the ranking (`LD2 F286`, the front file) were also reached once. Strict-Ymir data misalignment log: 0 data accesses. Sound was not checked.
- Not done: a Wolverine route with a sound check, and the console.

## 3. First-boot crushed sprites and no sound (open, instrumented)
Evidence: console photos only. fix7n boot 1: `PIC 31 DONE 15 MISS 45` (photo 658c9beb), the whole picture one cold teal two-tone (backgrounds and sprites alike, not only sprites), no sound; boot 2 normal colours and music. Photo 76e2facf (Wolverine, a later boot) shows a teal region with a diagonal seam at the bottom right.
Looked at, not found:
- Power-up memory contents (EMULATOR): a patched Ymir copy (`sh2r`, `AVP_RANDRAM=seed`, `AVP_RANDRAM_MASK`) fills VDP1 and VDP2 VRAM, CRAM and SCSP RAM (mask f, seed 1) and WRAM low (mask 10, seed 2) with pseudo-random words at the 20th instruction fetch. Boot to stage 1 was normal in both (colours, sprites, readout). Random WRAM high (and everything at once) stops the BIOS from booting in Ymir, so the work RAM high case is untested. One seed each is not a proof.
- The SCSP is driven by the SH-2; the 68000 only spins. A lost SNDON therefore should not silence it by itself (INFERRED from `sat_audio.c`, not confirmed on hardware). `sat_audio_init` runs inside the GFS callback of the first round load (kernel.c `round_sound_ready`); its SMPC waits were bounded at 100,000 spins, and a command written while an INTBACK still had data queued would be ignored.
- CRAM is cleared in `sat_gfx_init` before `RAMCTL` is written, and the clear loop writes 2,048 entries whatever the mode; the colour offset registers are zeroed by the loader. No fault found by reading.

Ranked candidates (INFERRED): (1) palette or colour state wrong on that boot (the whole picture is wrong, not only the sprites: CRAM mode or contents, or the colour calculation set-up applied late); (2) marginal cart (A-bus) timing at the 352 clock, as the fix7n risk note says: sprite textures, the sound samples and cold code all live in the cart, but the layers and palettes do not, which fits it less; (3) a start-up race (an SMPC command lost while the SMPC was busy, slave start against the first snapshot).

Changes (cheap, evidence-producing): `sat_audio_init` now retries up to three times if an SMPC wait ran out or the SCSP RAM word did not read back, waits up to 400,000 spins, and breaks a pending INTBACK first; `sat_gfx_init` reads back a CRAM entry, a VDP2 VRAM word and a VDP1 VRAM word once the display is on. Readout line 6 prints both: `HW SND n OK [TMO] [RB] TEST b` (n start attempts; OK = RAM word read back and no wait ran out; TMO = a wait ran out; RB = the SCSP master volume register read back, information only; TEST 7 = CRAM, VDP2 VRAM and VDP1 VRAM all read back). In Ymir the master volume register did not read back, which is why OK does not depend on it. A photo of the readout on a bad boot shows which of these failed, if any. If everything reads normal on a boot that still shows teal and no sound, the next suspects are (1) and (2).

## 4. 2P PRESS START cut at the right edge (FIT 2)
Cause: play's HUD rows keep the flush map (middle four blank columns dropped, content on cells 0 to 43), so the 1P portrait and the end of the 2P line sit on the last cell of each side, which the console's overscan cuts (photo 76e2facf: the right end of PRESS START).
Fix (`home_row_map`, `SAT_GFX_FIT == 2`, off with `-DSAT_HUD_NO_INSET`): on HUD rows with blank source columns 22 to 25 and two more blank ones among 21, 26, 20, 27, 19, 28, six columns go and the other 42 sit in cells 1 to 42; cells 0 and 43 are blank. A row without the blanks falls back to the old flush map. EMULATOR: stage 1 with 1P and the 2P prompt, the HUD has one empty cell (8 px) each side. Not confirmed on the console (the overscan is not measured; 8 px is an estimate from the photo).

## 5. Earlier corrections
Checked in `AVP_HWBOOT_RISKS_20261111.md` ("Corrections and console results"): `SAT_EDGE_STATS` counts object rows (the code comment is now corrected too); the CPU slot throughput is restated as average modelled utilisation (about 100 bytes per vblank average, busiest measured second 58 KB); "writes lost or garbled" is a candidate only; the per-outcome expectations replace the old percentage; the fix7n3 README repeats the per-outcome list.
