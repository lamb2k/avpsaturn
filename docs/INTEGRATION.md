# AvP Saturn integration line

`avp/integration` collects all finished work. Lanes start from its latest commit and merge back after their gates.
The owner's test disc is built only from this branch, and each disc lists the commit it came from.
An item leaves "In progress" only when it is merged here; a paused or parked lane keeps its row.

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

Asset set for builds from this line: `E:\AvP\learning\lane-wolverine-merge\D11`. It holds the K12 tile-merged Wolverine set (1,474 tiles; stage24_ma has 38 tiles of
margin with D9/D10) and the artist's revision 3 HUD art (80s red-brown/gold, crimson backdrop, no claws), exactly as delivered. remap.json gains a
colour entry `eighties`, his sprite in the 80s red-brown/gold to match the art; WV_COLOUR=eighties builds it. Owner decision 11-09: his sprite keeps the default `kick` (red/yellow), so the owner disc does not set WV_COLOUR.

## Owner disc recipe (avp/integration)
```
POSE_KEYS=0 KEEP_ROUND_FILES=1 GUEST_ASSETS=/e/AvP/learning/lane-wolverine-merge/D11 \
KERNEL_CFLAGS="-DSAT_HOME -DSAT_DUEL_MENU -DSAT_GUESTS -DSAT_GUEST_DEFAULT=1 -DSAT_WV_JUMP=1 -DSAT_GUEST_FAST_LIST=1 -DSAT_GUEST_NAMES_LAZY=1 -DSAT_GUEST_PAL_KEEP=1" \
python saturn/rt/build.py <workdir>
```
Owner decisions in the recipe: SAT_WV_JUMP=1 (jump apex 88 px, owner 11-09). Wolverine keeps his current size: SAT_WV_SCALE stays off (owner 11-09).
D11 carries the ground lane's `jumpair` data; its moves and lift match G1.
Slowdown switches ON (11-09): release link fits (hw_free 4,476 / lw_free 104 on the compare base), fit 76/76; PAL_KEEP exact palette check clean (lane fps-held 82cf075). SAT_GUEST_FOLD stays off (no gain).
Still awaiting the owner's choice: SAT_WV_GROUND (feet on the floor; ground.py data for D11 still to be generated).

## In progress (not merged yet)

Updated 2026-11-09 evening. Merged at 4bfcdf6: sprite-dropout cart guards (13e63b5), menu dropfix first pass (e1e6158), claws-only first pass (62d16f7).

| Item | Branch | State |
| --- | --- | --- |
| Native Wolverine, plan revision 2 (docs/notes/AVP_WOLVERINE_NATIVE_PLAN_V2_20261109.md): no sprite replacement; first milestone one complete native attack | lane/wv-native-gfx-20261109 (5e5d568 pushed) | design and stand prototype done (SAT_WV_NATIVE_GFX, default off; stand drawn natively in Yaba); working on the HOST identity run, then his own data block and one attack |
| Character select: fixed scroll 1 drops so panels never move and stat bars sit inside their boxes | lane/menu-dropfix-20261109 | first pass merged (stops the collapse); second pass (2f2f093, local) building; owner saw bars shifting on the merged pass |
| Main-game text: font glyphs never seen by a census draw blank; HURRY UP! second U (lane/hurryup f36ff31); stage 14 caption garbage | lane/text-glyphs-20261109 (f62d289 pushed) | done and gated (fit 76/76, check_screen_keys 0/287 missing, Yaba HURRY UP and stage 14 caption checked); costs +400-800 dropped sprite keys on 0e/1c/1e/24, so owner 2026-11-09: WAIT and merge together with the stage-sprites fix |
| Main-game sprite pieces dropped on stages 0e, 1c, 1e, 24; fatal 0xe2 at 0xa9cc4 once on 0e | lane/stage-sprites-20261109 (merged with text-glyphs f62d289) | built, offline and host gates passed (docs/notes/AVP_STAGE_SPRITES_20261109.md). Fatal 0xe2 cause found: Linn's script page 0x171400 kept by no stage file; fixed by CHAR_FUZZ_PAGES (default on). CHAR_FUZZ_KEYS=1 PACK_TAIL_FILL=1 (default off) cut fuzz-drawn missing keys in 1c, 1e, 24 solo files from 500-1,600 to 0-346 (held-out run); 0e Schaefer/Linn and the 2P pairs still short. row-trimmed tiles (SAT_TILE_ROWTRIM, default off) built and gated: stages 02-26 drop 0 fuzz-drawn keys with CHAR_FUZZ_KEYS=1 in every stage, hw_free 1,004, lw_free 60 unchanged; Yaba A/B done as a proxy (docs note section 6) |
| Post-credits reveal + unlock | lane/wolverine-reveal 850fc42 (pushed) | built; end-to-end Yaba check not done; owner to pick the voice clip |
| Saturn hardware FPS test discs | E:\AvP\package-hwtest-20261109 (pre-integration) | rebuild from avp/integration with the next owner disc (owner to confirm) |
| Wolverine sounds from MSHvSF (claws, hits, Berserker voice, select/KO voice, reveal clip) | lane/wv-sounds-20261109 (port 9722) | started 2026-11-09 |
| Wolverine talk-box face (crop of approved portrait) and identity leaks | lane/wv-talkbox-20261109 (port 9723) | started 2026-11-09 |
| Wolverine healing factor (SAT_WV_HEAL) and Berserker flash/freeze (SAT_WV_FLASH) | lane/wv-features-20261109 (port 9724) | started 2026-11-09 (owner un-deferred healing) |
| Versus mode (Duel): RANDOM arena garbage, Hunter not drawn, stage enemies entering, full pairing matrix | lane/versus-20261109 (port 9725) | unparked by owner 2026-11-09 |
| Row-trimmed tile encoding (SAT_TILE_ROWTRIM) on top of stage-sprites | lane/stage-sprites-20261109 19f87b0 | implemented, offline numbers done; gates and Yaba A/B running |

Dropped (owner 2026-11-09: no more work on the sprite-replacement Wolverine): claws-only follow-up (lane/wv-noguns-20261109-f2576a, not merged), guest group loop (lane/fps-group), Wolverine defense gate (lane/wolverine-defense), feet-on-floor ground/ground2 switches. Native Wolverine covers each of them.

Versus mode was parked earlier on 2026-11-09 and unparked the same night (lane/versus-20261109).

## Owner discs

- avp_integration_2 (70af5ed), 2026-11-09: E:\AvP\package-integration\avp_integration_2 (27 tracks, 662 MB). Gates: build rc 0 (hw_free 964, lw_free 60), fit.py D11 76/76, WSL unittest 106 run with the 30 known private-dependency errors, Yaba boot + walk to a stage 1 Wolverine fight with sprites drawn. Yaba speed not measured (host busy with other lanes). Replaces avp_integration_1.
| Disc | Commit | Package | State |
| --- | --- | --- | --- |
| avp_integration_1 | a6e58aa | **WITHDRAWN 11-09**: owner saw sprites vanish on most frames and half speed in Yaba. The regression predates the menu/slowdown merges (anim-branch base also bad); lane/sprite-dropout is bisecting. |
| (was) avp_integration_1 | a6e58aa | E:\AvP\package-integration\avp_integration_1 (27 tracks, README.txt) | current; Yaba boot/menu/fight check passed, fit 76/76 (stage24_ma 38 tiles of margin), hw_free 2,028, lw_free 64 |

wolverine-v4, package-fps and package-home-combined are superseded.
