# fix7n2: the Wolverine talk-box freeze, the continue report, readout lines (2026-11-11)

Disc `avp_3h_A_fix7n2` (source dad1028, FIT 2). Console results of fix7n are in `AVP_HWBOOT_FIX7N_20261111.md`. Labels: EMULATOR = strict Ymir with the JP BIOS and 4 MB cart; CONSOLE = owner photos; INFERRED = reasoning only.

## 1. Freeze in the first Wolverine talk box (owner priority 1)
- CONSOLE: fix7n froze at the first Wolverine dialogue, only with Wolverine, music kept playing, box half drawn.
- Found (source and map): `guest_face_data` (his talk-box face cells) sat at 0x027F6D86, 2 mod 4. `vram_copy` on the slave read the source as 32 bit words. A real SH-2 takes an address error on a misaligned long read; Ymir and Yaba allow it, and strict Ymir did not log it here either, so no emulator run here could show it.
- Fix (560df79): `tools/wolverine/hud_art.py` emits `__attribute__((aligned(4)))` for the face data, and `vram_copy` has a byte-wise path when the source is not 4-aligned.
- INFERRED, not confirmed: the match of address, timing (first box that draws his face) and symptom (slave stops, master and music go on) is strong, but nothing measured it on the console. If the box still freezes, the readout now prints `SLAVE STOP xxxx` after 2 s without a completed picture (xxxx = pictures drawn so far).
- EMULATOR check of the same disc: the data-misalignment log of three strict runs (boot to stage 1, die, continue, next stage) lists instruction-fetch artefacts only (PC = address), 0 data accesses.
- Not done: a Wolverine route in Ymir (the 1P cursor still does not move onto his panel with the keys sent).

## 2. Continue screen, character missing (owner report on fix7n, a Predator)
- EMULATOR: boot, stage 1 as Predator Warrior, died, CONTINUE, picked the same character: player drawn and playing. Died again path: picked Hunter on "SELECT YOUR CHARACTER" (D, D, A): P-Hunter drawn and playing, no extra file load at the continue (readout `LD1` unchanged), the next stage loaded the Hunter solo file (`LD2 F35`). Not reproduced.
- Static check: `round_check` (kernel.c) reloads a file only when the stage word changes; characters picked at a continue only add to `chars` for the NEXT stage load. The per-character stage files do carry the same sprite keys (`wd_hw/round_stats.json`: 0 dropped keys in every variant except stage 0E: 300 to 480), so a wrong variant should not remove a character in stages 1 to 0C. For stage 0E it could (dropped keys); not tested.
- Not compared on fix7b/fix6/F5: nothing reproduces here, so a comparison would show nothing. The `round_check` logic is the same in all of them (INFERRED from the diff: this lane did not touch it).
- Open, needs from the owner: stage, character before, character picked at the continue, and a readout photo after it (the `LD` line says if a file load happened).
- Ideas not acted on (INFERRED, no evidence): the character's sprite tiles come from the spill region on a later stage; a hardware-only effect after the 12-vblank settle; the intermittent boot-1 sprite crush seen on the console (same family: tiles missing after a load).

## 3. New readout lines (priority 3: load state; priority 2: tick counters, first part)
- `TASK RUN n CUT n` (kernel.c `f_d86`): `sat_tk_run` counts task runs, `sat_tk_skip` counts runnable tasks a vblank cut off. Per 60 vblanks. EMULATOR reading in stage 1: RUN at the display cap 9999, CUT 20 to 60. The dispatcher walks the task list repeatedly inside a vblank (the idle call returns and the walk restarts), so RUN is not a frame count, and CUT is not yet tied to lost game time. The "game time vs DONE" question is not settled; see section 4.
- `LDn Fnn Snnnn Dn Bn` (kernel.c `sat_ld_log`, four entries): file number, sectors, load seconds, seconds since the first dispatcher pass. EMULATOR: `LD1 F20 S1090 D9 B34` (stage 1 file), `LD2 F35 S1222 D10 B118`. The vblank count stands still while GFS loads (3 counted vblanks for the 1090 sector file), so the clock is the SMPC real-time clock via the INTBACK status report, to the second. SMPC command 0x0E is CKCHG352, not GETTIM: the first draft used it and reset the machine in Ymir. Boot time before the first dispatcher pass (BIOS, IP, loader) is not in B.
- Only loads are logged. Transitions with no file load (title to menu, menu to select, continue) are not on the readout; this is a gap against the request for a log line per transition.
- RAM: `lw_free` 96 bytes after this change (was larger); the readout is `SAT_FPS_HUD` only.

## 4. Arcade comparison (priority 2): not yet done
- Arcade ROM: MAME `avspu` runs locally (`.deps/mame/mame0289`, rompath `AvPSaturnCapabilityTest`; scripts in `tools/wolverine/*.lua`). Nothing has been measured on it for this question.
- Plan: tap the game's own variables in MAME (task record reads at the last task, flag writes at 0xff0266) over a crowded stage 1 fight, count walk completions per vblank, then the same counters in Ymir and the console. Until then no statement about arcade speed.
