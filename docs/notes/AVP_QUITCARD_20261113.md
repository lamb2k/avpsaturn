# fix7p6: NOW LOADING on quit to title, boot diagnostics off (lane quitcard, 2026-11-13)

Branch `lane/quitcard-20261113` (from `69ec3f3e`, fix7p5's source; commit `ea2c0da5`, readout id `F2 EA2C0D`), worktree `E:\AvP\worktrees\quitcard`, evidence `E:\AvP\learning\lane-quitcard`, disc `E:\AvP\package-integration\fenrir\avp_3h_A_fix7p6`. Recipe: fix7p5's (fix7q2's with `BOOT_CFLAGS=-DSAT_LOAD_LZ -DSAT_LOAD_COALESCE -DSAT_BOOT_DISC_ORDER`) plus `-DSAT_QUIT_CARD`, and without `-DSAT_BOOT_SELFTEST`. Labels: EMULATED = my own copy of the lane-loading Ymir (real BIOS, flat bus costs, stock timing; strict copy `ymir2-mis.exe` for the misalignment gate); CONSOLE = none.

## 1. Quit card (SAT_QUIT_CARD, default ON in the recipe)

`pause_menu` (`saturn/rt/home_cold.c`, cart code) now calls `sat_home_loading(1)` (home.c, the call every stage load already uses via `round_check`) before `sat_home_restart()`. Nothing else moved: `sat_home_restart` (kernel.c) is untouched, so `sat_guest_wolverine_reset()` still runs first inside it, after `ldc sr,0xf0`, in the order of fix7p3. The card is drawn at normal interrupt level, before the restart masks interrupts, because `sat_home_frame` waits on a vblank. The restart's boot clears `sat_home_hold` / `sat_home_mode` (bss), so nothing is left held; if the restart is refused (stuck VDP1 erase, `sat_home_restart` returns) the card is switched off again and the game resumes. About 20 bytes of cart code (cart tail free 2,372 to 2,352 with the card alone, build `Q1`).

Before, the paused picture stayed frozen with the pause list on it for the whole front end reload.

## 2. Boot diagnostics (SAT_BOOT_SELFTEST, default OFF in the recipe; code kept)

Owner, 2026-11-13: remove the boot diagnostics. Behind `SAT_BOOT_SELFTEST` now: the CRAM / VDP2 VRAM / VDP1 VRAM read-back at the end of `sat_gfx_init` (`sat_gfx.c`), the SCSP master volume read-back (`sat_audio.c`, bit 10 "RB") and readout line 6 `HW SND n OK [TMO] [RB] TEST b` (`fps_hud.c`). Always on: the SCSP sound-start retry (up to 3 starts, SMPC waits of 400,000 spins, INTBACK break), which uses status bits 8 and 9 and is a fix. `SAT_BOOT_DIAG` (the loader's step-by-step boot display) and `AVP_CYC_DIAG` were already off; I found no other boot-only diagnostic compiled in. The readout (PROF, PIC/DONE, MISS, id/FLIP/VBL, TICK/CUT, LD) stays; it is 5 lines now.

| build | cart tail free | low RAM free | high RAM free |
|---|---|---|---|
| fix7p5 recipe (`Q0`) | 2,372 | 500 | 72 |
| card only (`Q1`) | 2,352 | 500 | 72 |
| card, selftest on (`Q2S`) | 2,352 | 512 | 72 |
| **fix7p6** (`Q2`, `Q3`) | **2,516** | **612** | **56** |

Freed against the checks-on build `Q2S`: 164 bytes of cart tail and 100 bytes of low RAM. High RAM free reads 16 bytes lower: the profile placement (`place_fn`) refilled it differently, no new code lives there. Bytes, from the build log. Against fix7p5: cart +144, low +112, high -16.

Boot time saved (EMULATED, frame resolution): power-on to the title logo 31.16 s (`Q1`, checks on) to 31.14 s (`Q2`, three boots all 31.14 s), one frame. The checks are about ten bus accesses; the real saving is tens of microseconds (MODELLED by counting, not measured), far below a frame.

## 3. Checks (strict Ymir, own copy; pad file only, windows labelled and shown no-activate)

- **Quit to title as Predator Warrior, twice in a run** (`qP3`, final disc `Q3`; earlier `qP1`, `qP2`): the card shows 4 frames (0.067 s) after the press (the pause screen, then one frame of the hold, then the card), stays for the whole load (5.33 s, 655 sectors in 4 bursts), the arcade copyright screen, title and ARCADE start again, stage 1 plays. Sheet `ymr\runs\qP3\` (`sheet_qP2.png` of the same route on `Q2`).
- **As Wolverine, quit twice** (`qW3`, `GUEST_DEFAULT=1` build `QW2`, same source, build id of the working tree): card each time (`c1a`, `c2a`), then stage 1 with Wolverine and the talk box with his face ("They keep coming, bub. We gotta fall back!") after each restart (`u6..u9`, `v6..v9`, sheet `sheet_qW3.png`). The Wolverine reset order is unchanged.
- **0 misaligned data accesses** (`tools/ymir_misalign_gate.py`, `ymir2-mis.exe`): `qP3` 0 (5,273 instruction fetch artefacts filtered), `qW3` 0, `qP1` 0, `qW1` 0, `qW2` 0, `qP2` 0, three cold boots 0, and the default route (boot, title, ARCADE, stage 1, KO, continue) on `Q3`: 0 (`gate_misalign_Q3.txt`).
- **Build gates** (the build fails on them), `Q3`: `vdp2_cycle_check` PASS; alignment gate 347 data symbols (0 unknown), 49 cast sites, 199 accessor calls, 287 round files, 0 hits; boot data addresses ok; Wolverine canary ok; loader bss end `0x06013ae0` as fix7p5. **Tests:** `align_gate_test.py` 13 ok, `lat_protocol_test.py` PASS, `vdp2_cycle_check_test.py` PASS.
- **Speed, stage 1 (`aQ3`, stock Ymir):** `TICK 60 CUT 38`, `PIC 60 DONE 60 MISS 0 SKIP 0 HELD 0`, readout id `F2 EA2C0D`.
- **Loads, same route on `Q0` (fix7p5 recipe) and `Q3`** (`aQ0`, `aQ3`): quit to title, press to the last disc sector 4.88 s then 4.93 s (+0.05 s: the card's 3 frames before the restart starts reading, first read 0.11 s then 0.16 s after the press); the card was not there before. Stage 1 load 6.39 s of card (797 sectors) and game over load 5.27 s (655 sectors) are identical on both: the other loads show their card as before.
- **Sound starts, 3 cold boots:** on `Q2S` (same source, `SAT_BOOT_SELFTEST` on) the readout reads `HW SND 1 OK TEST 7` on each of three boots (`runs\sd1..sd3`, `sd_sheet.png`): one start, RAM word read back, no SMPC timeout, chips read back. On the shipped `Q2` three boots log exactly one SNDOFF/SNDON pair from `sat_audio_init` each (`regs_cb1..3.log`), so the retry did not fire.

## 4. Known, not done

- Console: nothing measured. Sound start on a console is no longer reported on screen; to see it again build with `-DSAT_BOOT_SELFTEST`.
- The Wolverine checks ran on the `GUEST_DEFAULT=1` build of the same source (`QW2`), not a rebuild at the final commit; the only difference is the build id.
- Quit to title still reboots through `sat_main`; the card goes off when the front end file has loaded (the copyright screen follows), as for every load.
- Under heavy machine load (other lanes' Ymirs) the route's frame waits drift; the runs above were redone alone where they diverged (`sb*` discarded, `sd*`, `sc*` kept).

Tools: `tools/quitcard/` (`qbuild.sh` private build, `stage_q.sh`, `qroute.sh`, `quittime.py`, `cardruns.py`, the route files). Intermediate discs deleted, manifest `E:\AvP\learning\lane-quitcard\DELETED-20261113.txt`.
