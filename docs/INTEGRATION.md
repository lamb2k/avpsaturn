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

| Item | Branch | State |
| --- | --- | --- |
| Sprite dropout and half speed (blocker) | lane/sprite-dropout | bisecting |
| Select-screen column-drop regression from the talk-box fix 95b1167 | lane/menu-dropfix | on hold until the dropout lane is done |
| Wolverine still fires Schaefer's gun (owner rule: claws only) | lane/wv-noguns-20261109 | built and gated (fit 76/76, hw_free 1,948, lw_free 60); no Yaba check yet |
| Post-credits reveal + unlock | lane/wolverine-reveal 850fc42 (pushed) | built; end-to-end Yaba check not done (paused); voice clip not identified |
| Guest group loop out of the snapshot (about 44 ticks per snapshot), precomputed in the game frame | lane/fps-group | starting |
| Menu mode flow, transparent option screens, title list lower; talk-box face/text 8 px offset | lane/wolverine-menu | merge done; building and checking |
| Wolverine takes far more hits than Schaefer (Round 1 gate: 36-37 vs 2), and a wrong pose while an enemy holds him (0204xx shows throw poses) | lane/wolverine-defense | PAUSED until the owner has played the integrated disc |
| Native Wolverine (fork of Schaefer, plan aae2e10) | lane/wolverine-native | Stage 0 identity |
| HURRY UP missing U (stage timer banner) | lane/hurryup | PAUSED until the owner has played the integrated disc |
| Saturn hardware FPS test discs | E:\AvP\package-hwtest-20261109 (built from lane/hwtest, pre-integration) | to be rebuilt from avp/integration with the owner disc |
| Talk-box face for Wolverine (crop of recoloured portrait) | not started | after the menu lane |
| Stage font glyph gaps (packs keep only census-seen font glyphs) | not started | found by the hurryup lane |

## Owner discs
| Disc | Commit | Package | State |
| --- | --- | --- | --- |
| avp_integration_1 | a6e58aa | **WITHDRAWN 11-09**: owner saw sprites vanish on most frames and half speed in Yaba. The regression predates the menu/slowdown merges (anim-branch base also bad); lane/sprite-dropout is bisecting. |
| (was) avp_integration_1 | a6e58aa | E:\AvP\package-integration\avp_integration_1 (27 tracks, README.txt) | current; Yaba boot/menu/fight check passed, fit 76/76 (stage24_ma 38 tiles of margin), hw_free 2,028, lw_free 64 |

wolverine-v4, package-fps and package-home-combined are superseded.
