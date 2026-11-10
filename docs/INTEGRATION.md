# AvP Saturn integration line

`avp/integration` collects all finished work. Lanes start from its latest commit and merge back after their gates.
The owner's test disc is built only from this branch, and each disc lists the commit it came from.
An item leaves "In progress" only when it is merged here; a paused or parked lane keeps its row.

## Merge note 2026-11-10 (integration lane, evening)

avp/integration holds, merged in this order: stage-sprites 7ba526c (text-glyphs inside), native Wolverine 035d44c, stage-menu 6b005e9, versus 2ada807, stage-sprites final 9298450 (SAT_TILE_ROWTRIM=2), talk box 7b02556, sounds 0246dd1, native e0a0f1c (heal, flash, unhittable Berserker, +0xd2 test in every build). The reveal (b2c0abf) is merged on branch `wip/integration-with-reveal-20261110` only: with it hw_free is 248, so it waits until the reveal lane moves its 272 B of resident code into cold or cart code. Lanes: merge avp/integration into your branch.

Memory, owner recipe, assets D11 (hw_free / lw_free / cart_free; Yaba-built, measured on the build of each step):

| Step (build) | hw_free | lw_free | cart_free |
| --- | --- | --- | --- |
| disc 2 (70af5ed) | 964 | 60 | 4,340 |
| + sprites 7ba526c (rowtrim 1, lane figure 708) + native 035d44c + stage-menu (lane figure -272) + versus = disc 3a (4c3dc09) | 520 | 84 | 5,344 |
| + final sprites 9298450 (rowtrim 2) + talk box (7bcd7ab) | 520 | 84 | 5,172 |
| + sounds (57e7d43) | 520 | 84 | 4,988 |
| + native e0a0f1c: heal, flash, unhittable (45c867c) = disc 3e | 520 | 84 | 4,556 |
| + reveal b2c0abf (a4b9757, not on avp/integration) | 248 | 80 | 7,132 (crosses a 4 KB cart step; the reveal alone costs hw -272) |

## Merged (in avp/integration)

| Item | Source | Switch / default | Gate evidence |
| --- | --- | --- | --- |
| Wolverine v4.1 (idle anchor, standing hitstun, food/score pickups only) | lane/wolverine-v4 a83ba1a | on (guest) | v4.1 notes |
| Frame chain + Codex FPS experiments (pairing, hints, slack, HW erase, pairs16) | c4489a4 | all off | AVP_FPS_COMPARE_20261109.md |
| draw_home waits for the menu copy | 3e62e47 | on | AVP_FPS_COMPARE_20261109.md |
| VDP1 profile rings in high RAM | 1665742 | measurement builds only | same |
| Wolverine animation steps 1-3 (chain mapping, walk/jump, native timing switch) | lane/wolverine-anim 9728e4e | walk/jump on; SAT_WV_NATIVE_TIMING off | anim notes |
| Wolverine select/HUD/rank art | lane/wolverine-art f518e5c | on with guest | art check 11-09 |
| Wolverine KO invisibility fix; Round 1 gate notes | lane/wolverine-gate d5f2dda, 43f9c7d | on | host test wolverine_clock_test; AVP_WOLVERINE_GATE_20261109.md (boss clear and section 3 off/on/Schaefer, harness assists) |
| Wolverine slowdown fix (FAST_LIST, NAMES_LAZY, PAL_KEEP; FOLD measured, no gain) | lane/fps-held 457508b, 82cf075 | ON in the owner recipe (Yaba: held 11.4% -> 2.3-2.9%, snapshot 644 -> 486 ticks) | AVP_FPS_HELD_20261109.md |
| Saturn on-screen perf readout (SAT_PERF_HUD) + PAL_KEEP page-0-only fix | lane/hwtest 8a75ccb | readout off; used for console A/B discs | AVP_HWTEST_20261109.md |
| Wolverine ground contact, jump height, size comparison (SAT_WV_GROUND=1/2, SAT_WV_JUMP=1/2, SAT_WV_SCALE=14) | lane/wolverine-ground 9745da7 | all off; owner comparison discs in E:\AvP\learning\lane-wolverine-ground\discs | AVP_WOLVERINE_GROUND_20261109.md; ground.py data must be regenerated for D11 before a switch is turned on |
| Main-game text glyphs, HURRY UP!, stage 14 caption; stage-file sprite keys, fuzz keys, tail fill, row-masked tiles (rowtrim 2) | lane/stage-sprites-20261109 9298450 (text-glyphs f62d289 inside) | CHAR_FUZZ_PAGES on; CHAR_FUZZ_KEYS=1 CHAR_FUZZ_KEY_STAGES= PACK_TAIL_FILL=1 -DSAT_TILE_ROWTRIM=2 in the recipe | fit 76/76, round/screen/caption checks 0 of 287, goldens clean (lane) and re-run here |
| Native Wolverine (no skin), chain B, Berserker attack+jump unhittable, heal, flash, +0xd2 character test | lane/wv-native-gfx-20261109 e0a0f1c | -DSAT_WV_NATIVE_GFX -DSAT_WV_HEAL -DSAT_WV_FLASH=1 -DSAT_WV_FLASH_FREEZE=12 | native notes; gates below |
| Stage select names, ENDING entry, PRESS START boot line | lane/stage-menu-20261110 6b005e9 | on | AVP_STAGE_MENU_20261110.md |
| Versus mode fixes | lane/versus-20261109 2ada807 | on; DUEL_FILES=0 in the recipe (owner) | AVP_VERSUS_20261109.md |
| Talk-box face and his story-box wording | lane/wv-talkbox-20261109 7b02556 | -DSAT_WV_DIALOG=1 | AVP_WOLVERINE_DIALOG_20261110.md |
| Wolverine sounds | lane/wv-sounds-20261109 0246dd1 | -DSAT_WV_SOUND, WV_SOUND=E:/AvP/learning/lane-wv-sounds/assets3, -DWV_SFX_BERSERKER=13 | AVP_WOLVERINE_SOUNDS_20261109.md |

Asset set for builds from this line: `E:\AvP\learning\lane-wolverine-merge\D11`. It holds the K12 tile-merged Wolverine set (1,474 tiles; stage24_ma has 38 tiles of
margin with D9/D10) and the artist's revision 3 HUD art (80s red-brown/gold, crimson backdrop, no claws), exactly as delivered. remap.json gains a
colour entry `eighties`, his sprite in the 80s red-brown/gold to match the art; WV_COLOUR=eighties builds it. Owner decision 11-09: his sprite keeps the default `kick` (red/yellow), so the owner disc does not set WV_COLOUR.

## Owner disc recipe (avp/integration, disc 3e)
```
DUEL_FILES=0 CHAR_FUZZ_KEYS=1 PACK_TAIL_FILL=1 CHAR_FUZZ_KEY_STAGES= WV_SOUND=/e/AvP/learning/lane-wv-sounds/assets3 POSE_KEYS=0 KEEP_ROUND_FILES=1 GUEST_ASSETS=/e/AvP/learning/lane-wolverine-merge/D11 KERNEL_CFLAGS="-DSAT_HOME -DSAT_DUEL_MENU -DSAT_GUESTS -DSAT_GUEST_DEFAULT=1 -DSAT_WV_JUMP=1 -DSAT_GUEST_FAST_LIST=1 -DSAT_GUEST_NAMES_LAZY=1 -DSAT_GUEST_PAL_KEEP=1   -DSAT_TILE_ROWTRIM=2 -DSAT_WV_NATIVE_GFX -DSAT_WV_DIALOG=1 -DSAT_WV_SOUND -DSAT_WV_HEAL -DSAT_WV_FLASH=1 -DSAT_WV_FLASH_FREEZE=12 -DWV_SFX_BERSERKER=13" python saturn/rt/build.py <workdir>      # also: copy WORK/char_fuzz.json from E:\AvP\learning\lane-stage-sprites (private, not in git)
```
Owner decisions in the recipe: SAT_WV_JUMP=1 (jump apex 88 px); his size unchanged (SAT_WV_SCALE off); native only, no skin; DUEL_FILES=0; Berserker unhittable (WV_BZ_HURT default 0 in the native code now, no env override needed).
**When the reveal goes in, owner discs use `-DSAT_GUEST_DEFAULT=0`** (owner model: Wolverine off by default, OPTION toggle, auto-on at the first ending; the reveal is on by default in every SAT_GUESTS build after its merge, `REVEAL=0` builds without it, `REVEAL_VOICE=E:/AvP/learning/lane-wv-sounds/wav/reveal_voice_intro.bin`, keep SAT_UNLOCK_DEBUG out). With SAT_GUEST_DEFAULT=1 the reveal never plays.
Do not set SAT_WV_SOUND_HOOKS with SAT_WV_HEAL/FLASH (the features hooks own the Berserker events; build.py skips the test hooks then).
Asset sets: D11 as above; sprite fuzz data `char_fuzz.json` is private and goes in the work dir.

## In progress (not merged yet)

Updated 2026-11-10 evening.

| Item | Branch | State |
| --- | --- | --- |
| Post-credits reveal + Options toggle + auto-on | lane/wolverine-reveal-20261109 b2c0abf | merged only on `wip/integration-with-reveal-20261110` (a4b9757): hw_free 248 with it (reveal costs 272 B of resident code, one 4 KB cart step). The reveal lane moves that code into cold/cart code; then merge and rebuild with SAT_GUEST_DEFAULT=0. Ending test on 3f (reveal build) in this file's discs section. |
| Opening cutscene is missing Schaefer and some sprites; Wolverine shows jump poses when hit; the automatic grab uses placeholder poses | native / sprites lanes | being fixed (owner known issues for disc 3e) |
| Saturn hardware FPS test discs | E:\AvP\package-hwtest-20261109 (pre-integration) | rebuild from avp/integration with an owner disc (owner to confirm) |

Dropped (owner 2026-11-09: no more work on the sprite-replacement Wolverine): claws-only follow-up, guest group loop (lane/fps-group), Wolverine defense gate, feet-on-floor ground/ground2 switches. Native Wolverine covers each of them. Closed lanes (merged here): stage-menu, versus.

## Owner discs

| Disc | Commit | Package | State |
| --- | --- | --- | --- |
| avp_integration_3e | 45c867c | E:\AvP\package-integrationvp_integration_3e | current: everything above except the reveal; SAT_GUEST_DEFAULT=1 |
| avp_integration_3a | 4c3dc09 | E:\AvP\package-integrationvp_integration_3a | first native disc (sprites 7ba526c rowtrim 1, native 035d44c, stage menu, versus); Berserker hittable on it; superseded by 3e |
| avp_integration_2 | 70af5ed | E:\AvP\package-integrationvp_integration_2 | skin Wolverine; superseded |

Gates for 3e: see the report of 2026-11-10 (build rc 0, hw_free 520 / lw_free 84 / cart_free 4,556, STORE 162,336 of 262,144, fit.py D11 77/77 with the dialog keys, check_round_pages / check_screen_keys / check_caption_keys 0 of 287, six HOST goldens clean, WSL unittest 145 run / 30 known errors / 0 failures, Yaba cache off and cache ON smoke, Berserker unhittable, heal Wolverine-only).
avp_integration_1 was WITHDRAWN 11-09 (sprites vanished, half speed). wolverine-v4, package-fps and package-home-combined are superseded.
