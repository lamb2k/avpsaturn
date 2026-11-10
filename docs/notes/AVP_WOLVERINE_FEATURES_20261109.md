# Wolverine features: healing factor and Berserker flash (lane wv-features, 2026-11-09)

Branch `lane/wv-features-20261109`, from `lane/wv-native-gfx-20261109` b368017. Code: `saturn/guests/wolverine/wv_features.c` (new). Edits elsewhere: `saturn/rt/build.py` (compile the file and rename two hooks when a switch is on), `tools/lift_runner/build_native_host.py` (`--wvf 1`, plus `24060` in its GUEST_WRAP, which the target build has and the host script lacked). Nothing in `wolverine.c` or `game_bind.c`.

Evidence tiers as in the native notes: **MAME** (MSHvSF reference), **HOST** (lifted game on a PC, WSL), **BUILD** (SH-2 link), **EMULATOR** (Yaba, own copy, port 9724). No hardware.

## 1. Switches (all default off; flag off the kernel binaries are byte identical to the base)

| Switch | Meaning | Default |
| --- | --- | --- |
| `-DSAT_WV_HEAL` | healing factor | off |
| `-DSAT_WV_HEAL_DELAY=n` | ticks without a health drop before it starts | 180 (3 s) |
| `-DSAT_WV_HEAL_STEP=n` | ticks between points once it runs | 30 |
| `-DSAT_WV_HEAL_AMT=n` | points per step | 1 |
| `-DSAT_WV_FLASH[=1\|2]` | Berserker moment (needs `SAT_WV_NATIVE_GFX`): 1 at the move's start, 2 at its first contact | 1 |
| `-DSAT_WV_FLASH_FREEZE=n` | ticks the enemy pool stands still (the game's hitstop byte +0x2c); 0 = flash only | 12 |
| `-DSAT_WV_FLASH_HOLD=1` | also skip his own player update for those ticks | 0 |
| `-DSAT_WV_FLASH_FRAMES="a, b, ..."` | VDP2 colour offset per vblank, 9 bit signed, all layers | `-24, -24, +144, +64` |
| `-DWV_SFX_BERSERKER=id` | with the sounds lane's `wv_sfx(id)`: called once at the moment (the hook point) | unset |

Hook mechanism: `build.py` compiles `wolverine.c` with `-Dsat_guest_wolverine_tick=wv_tick_inner` (with `SAT_WV_HEAL` or `FLASH_HOLD=1`) and `-Dsat_guest_wolverine_pad=wv_pad_inner` (with `SAT_WV_FLASH`); `wv_features.c` defines the original names, calls his code first and then ours. The Berserker events are the native lane's weak `wv_on_berserker_start/connect/end`; `wv_features.c` holds the strong definitions.

## 2. Healing factor

Rule: on each of his player updates, in the running stage (route byte ff8001 = 2, not attract ff81b0, not after the stage or boss clear ff81f3/ff822a), while his state is 02 00 xx (stand, walk, jump, the attacks, Berserker, special; substate 0) and his health is 0..100, a counter counts up; at DELAY it adds AMT (both +0x40 and the HUD's latched +0x42, as `pickup_heal` does, so the bar just rises) and drops back to DELAY-STEP. A drop of his health of any cause resets it (hits, grab damage, the Berserker cost charged on connect), as does any other state: hit (02 02), grab (02 04), getting up (02 08), dying and continue (04, 08). The pause menu holds the game, so no update runs. State: `hl_t[2]`, `hl_hp[2]` = 4 bytes.

Cutscenes and talk boxes: the game has no flag that says "talk box"; the gates above (stage clear, boss down, state 02 00) cover the scripted walks of a stage change. Gameplay runs under the talk boxes of the stage, so the heal does too (it is 2 points a second at most). Not separately detected.

Net effect (MODELLED from the defaults, 60 ticks a second): idle, 2 points a second after 3 s (full from 50 in 28 s). Berserker costs 6 on connect and the cost restarts the delay, so a use is repaid only if the next one is more than 6 s away (6 + 3 s dead time, 2 points a second): net per use = 2T - 12 points for T seconds between uses (T <= 3: -6 as stock; T = 4.5: -3; T = 6: 0; T = 10: +8). Per minute at one use every 3 s: -120 (stock -120); every 4.5 s: -40 (stock -80); every 6 s: 0 (stock -60). Berserker is never free while it is used more often than every 6 s.

## 3. Berserker flash

MSHvSF's own hyper (QCF + two punches, level poked to 3) in MAME 0.289: gauge level consumed at frame 2216; 2217-2218 the picture is dimmed to 78 % brightness; 2219 the cut-in (purple streak background, his face, white pulses) replaces the stage; **both fighters' blocks do not change from 2217 to 2255 (39 frames, 0.65 s)**; the action resumes at 2256 and the burst starts with white full-screen flashes. `mshvsf_super_frames.csv`, `mshvsf_super_strip.png` in the evidence folder (ROM-derived pictures stay local).

Ours (EMULATOR/HOST, see sections 5 and 6): at the move's start the enemy pool (20 slots of 0xc0 bytes from ff9580, the game's tag 0x0c pool) gets the game's hitstop byte +0x2c = FREEZE on every slot where it is zero (a hit enemy's own count is not touched), and the VDP2 colour offset runs the 4 vblank table (two dim frames, a bright pop, a fade). The game's box test refuses a defender with +0x2c set, so contacts wait for the thaw; with `FLASH_HOLD=1` his own update is skipped for the same ticks, so the move's clock waits too.

**Found on the way (for the native lane):** `wolverine.c wv_enemy_hp` and the census/harness scans walk ff9a00 in steps of 0x100. The tag 0x0c pool is `ff9580 + k * 0xc0`, 20 slots (`source_recon/avsrc_actor.c` POOLS); the 0x100 grid lands on a real block for one slot in three, so `wv_on_berserker_connect` misses most contacts. `wv_features.c` uses the right grid for its own scans.

## 4. Memory (BUILD)

Owner recipe + `-DSAT_WV_NATIVE_GFX`, workdir = copy of integration/w1, assets D11, `KEEP_ROUND_FILES=1`. Numbers below are from the build on b368017 (before the native Berserker action merged); the merged numbers are in section 7.

| | flag off (base b368017) | HEAL | FLASH | HEAL + FLASH |
| --- | ---: | ---: | ---: | ---: |
| hw_free | 964 | 964 | 964 | 964 |
| lw_free | 32 | 32 | 32 | 32 |
| cart_free | 6,168 | 5,844 (-324) | 5,956 (-212) | 5,632 (-536) |
| cold1_at | 0x27db000 | same | same | same (no new 4 KB step, no tiles lost) |

State, all in the cart (`.data` of the cart tail; the linker script sends every `.bss` to low work RAM, so the state is declared `section(".data")`): HEAL 4 bytes (`hl_t[2]`, `hl_hp[2]`), FLASH 2 bytes (`fl_left`, `fl_done`), +1 with `FLASH_HOLD`. Code: HEAL 316 bytes, FLASH 204 bytes + an 8 byte table, both 524 bytes plus alignment; `SAT_WV_FLASH_HOLD=1` adds about 80 bytes. Nothing in high or low work RAM, nothing in game_bind.c. A first build kept the state in `.bss` and cost lw_free 8 bytes (32 to 24, HEAL) and 4 (FLASH): the reason for `CARTVAR`.

Gates: no NO-GO in any build log; `fit.py` 76/76 gate True (D11 copy, the HEAL+FLASH build's layout; the layout is the same in every variant); WSL unittest 106 run, 30 errors (the known private-dependency set), 1 skipped, same as the base.

Flag-off identity (base b368017 build against this branch with no switch): HW.BIN, LW.BIN, COLD1.BIN, 0.BIN, ROM.BIN, OPX.BIN and STORE.BIN md5 equal; `sat.elf` identical; the ISOs differ in 47 bytes in the first sectors (the volume dates). With a switch only COLD1.BIN and HW.BIN change (HW.BIN holds the cart addresses the lifted hooks jump to; same size, hw_free unchanged).

## 5. HOST (lifted game on a PC, WSL, golden_c1 start, FREERUN, pad script)

Runner: `tools/lift_runner/build_native_host.py ... --guests 1 --wvf 1 --defs "-DSAT_WV_HEAL ..."`, Wolverine selected (`WV_SEL=1`), his skin (the host build is not the native build), 32,000 vblanks a run, health set to 101 at 1250, pad script of random attacks, gun presses, walking, jumps. 6 seeds x 7 variants, all reach the end (no hang). `tools/wolverine/wvf_heal_check.py` on the traces:

- **Healing never fires in the listed states: 36 runs with HEAL, 560,558 player updates, 2,318 heal events, 0 violations.** Every heal event is in a state 02 00 xx (stand, walk, jump, attacks, Berserker); the timer is 0 on every update whose state is a hit (02 02), grab (02 04), getting up (02 08), dying or continue (04, 08), or whose health is outside 0..100; it is 0 on the update after any health drop.
- Health over time, same start, no input (`hp_host_idle.png`, `hp_host_idle_zoom.png`): the runs are identical until the first heal (vblank 7192); after that the green line (heal on) climbs 1 point per 30 ticks after each 180 quiet ticks (7192; 7780, 7810, 7840, 7870, 7900) and stops at the next hit.
- Berserker damage with the freeze (the HOST skin Berserker; damage = drops of the 20 enemy slots' health during the move and 12 ticks after, 6 seeds, 183 to 293 Berserker uses a variant):

| variant | uses | ticks/use | damage/use | uses with damage |
| --- | ---: | ---: | ---: | ---: |
| no heal, no freeze (control) | 211 | 39.0 | 30.8 | 85 |
| heal only | 280 | 45.5 | 26.6 | 104 |
| flash, freeze 12 (default) | 250 | 44.0 | 38.3 | 100 |
| flash, freeze 12 + hold | 183 | 44.8 | 26.8 | 54 |
| flash, freeze 6 | 230 | 37.7 | 33.3 | 78 |
| flash, freeze 39 (MSHvSF length) | 293 | 48.6 | 25.7 | 110 |
| flash at first contact | 221 | 40.5 | 33.0 | 80 |

The runs diverge after the first change of timing (heal alone moves the control from 30.8 to 26.6), so the spread between rows is the timeline noise: **no measurable damage lost to a 12 tick freeze**; 39 ticks is the lowest row. Only the contact-triggered variant fires on 92 of 221 uses (42 %): the others never reach an enemy.

## 6. Yaba (own copy, port 9724, VideoCore 1, SH-2 cache on; paused or polled; stage 02)

Heal (`yaba_health_trace.png`, `.csv`; stage enemies removed by the harness so only the factor shows, health set to 40; `heal_on` = 180/30/1, `heal_slow` = 180/60/1):
- off: health stays 40 for the whole leg.
- 180/30/1: first +1 at vblank 190 (poke at 5), then +1 every 29.9 ticks on average (median 30, 60 steps), 101 at about vblank 1985.
- 180/60/1: first +1 at 181, then +1 every 60.0 ticks (60 steps).
- HUD (`yaba_heal/hud_bar_rises.png`): the bar's yellow part grows and the red part shrinks as the health passes 50, 60, 70, 80, 90, 100; nothing else on the screen changes.

Flash (`flash_compare_mshvsf_vs_saturn.png`, `strip_flash_on.png`, `strip_flash_off.png`; paused, one emulated frame a picture): the Berserker starts at frame 24 (motion QCF + attack). Frame 25 and 26 are dim (mean brightness 76 % of the previous frame, MSHvSF's hyper: 76 %), frame 27 is a near-white pop, frame 28 a fade, frame 29 normal. The enemy pool's hitstop byte reads 11 at frame 25 and counts down to 0 at frame 35: the three enemies in view do not move from frame 25 to frame 35 and move again at 36 (trace.jsonl, `x`); he animates through it. In the build without the switch the same input gives no change of brightness and the enemies keep moving.

## 7. Merge of the native Berserker action (d436009)

(filled after the merged builds)

## 8. For the native lane

1. `wolverine.c wv_enemy_hp` (and any scan with the 0x100 stride from ff9a00) reads the wrong grid: the enemy pool (tag 0x0c) is 20 slots of 0xc0 bytes from ff9580. `wv_on_berserker_connect` therefore sees about one enemy in three. Use `for (b = 0xff9580; b < 0xff9580 + 20 * 0xc0; b += 0xc0)`.
2. `tools/lift_runner/build_native_host.py`: GUEST_WRAP lacked `24060` (the target build has it), so the guest runner did not link; added here.
3. The native Berserker is entered through `sat_guest_wolverine_pad`; with `SAT_WV_FLASH` that function is renamed to `wv_pad_inner` and wrapped. No other change is needed on your side.
