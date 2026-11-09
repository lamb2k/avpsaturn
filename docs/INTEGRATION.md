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
| Wolverine KO invisibility fix | lane/wolverine-gate d5f2dda | on | host test wolverine_clock_test |
| Wolverine slowdown fix (FAST_LIST, NAMES_LAZY, PAL_KEEP) | lane/fps-held 457508b | all off (Yaba: held 11.4% -> 2.3% with all on) | AVP_FPS_HELD_20261109.md |
| Saturn on-screen perf readout (SAT_PERF_HUD) + PAL_KEEP page-0-only fix | lane/hwtest 8a75ccb | readout off; used for console A/B discs | AVP_HWTEST_20261109.md |
| Wolverine ground contact, jump height, size comparison (SAT_WV_GROUND=1/2, SAT_WV_JUMP=1/2, SAT_WV_SCALE=14) | lane/wolverine-ground 9745da7 | all off; owner comparison discs in E:\AvP\learning\lane-wolverine-ground\discs | AVP_WOLVERINE_GROUND_20261109.md; ground.py data must be regenerated for D11 before a switch is turned on |

Asset set for builds from this line: `E:\AvP\learning\lane-wolverine-merge\D11`. It holds the K12 tile-merged Wolverine set (1,474 tiles; stage24_ma has 38 tiles of
margin with D9/D10) and the artist's revision 3 HUD art (80s red-brown/gold, crimson backdrop, no claws), exactly as delivered. remap.json gains a
colour entry `eighties`, his sprite in the 80s red-brown/gold to match the art; WV_COLOUR=eighties builds it. Owner decision 11-09: his sprite keeps the default `kick` (red/yellow), so the owner disc does not set WV_COLOUR.

## Owner disc recipe (avp/integration)
```
POSE_KEYS=0 KEEP_ROUND_FILES=1 GUEST_ASSETS=/e/AvP/learning/lane-wolverine-merge/D11 KERNEL_CFLAGS="-DSAT_HOME -DSAT_DUEL_MENU -DSAT_GUESTS -DSAT_GUEST_DEFAULT=1 -DSAT_WV_JUMP=1" python saturn/rt/build.py <workdir>
```
Owner decisions in the recipe: SAT_WV_JUMP=1 (jump apex 88 px, owner 11-09). Wolverine keeps his current size: SAT_WV_SCALE stays off (owner 11-09).
D11 carries the ground lane's `jumpair` data; its moves and lift match G1.
Still awaiting the owner's choice: SAT_WV_GROUND (feet on the floor; ground.py data for D11 still to be generated), and the slowdown switches.
The slowdown switches are waiting on the release fit and the PAL_KEEP look check.

## In progress (not merged yet)

| Item | Branch | State |
| --- | --- | --- |
| Menu mode flow, transparent option screens, title list lower; talk-box face/text 8 px offset | lane/wolverine-menu | merge done; building and checking |
| Round 1 boss gate, throw look | lane/wolverine-gate | running |
| Native Wolverine (fork of Schaefer, plan aae2e10) | lane/wolverine-native | Stage 0 identity |
| Post-credits reveal + unlock + Berserker Barrage voice | lane/wolverine-reveal | running |
| HURRY UP missing U (stage timer banner) | lane/hurryup | finding the banner |
| Saturn hardware FPS test discs | E:\AvP\package-hwtest-20261109 (built from lane/hwtest, pre-integration) | to be rebuilt from avp/integration with the owner disc |
| Slowdown fix follow-ups (release fit, PAL_KEEP look check, fold pass) | lane/fps-held | running |
| Talk-box face for Wolverine (crop of recoloured portrait) | not started | after the menu lane |
| Stage font glyph gaps (packs keep only census-seen font glyphs) | not started | found by the hurryup lane |

## Owner discs
The discs the owner has (wolverine-v4, package-fps, package-home-combined) predate this line and are superseded. The next owner disc is built from
avp/integration once the menu lane merges.
