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
| `-DSAT_WV_FLASH_FRAMES="a, b, ..."` | VDP2 colour offset per vblank, 9 bit signed, all layers | `-56, -56, +192, +96` |
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

(filled from the builds)

## 5. HOST

(filled)

## 6. Yaba

(filled)
