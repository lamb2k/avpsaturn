# Wolverine ground contact, jump height and size, 2026-11-09

Lane `lane/wolverine-ground-20261109`, from `lane/wolverine-anim-20261109` (`9728e4e`). Tiers: HOST (tools, tables, offline renders), EMULATOR (MAME arcade
captures of AvP and MSHvSF; Yaba), hardware UNRUN. Everything below is a comparison: the default build is unchanged. Owner rule (11-09): compare first, keep the
current behaviour as the default, alternatives behind default-off defines.

## Switches (all default off; a default build is code-identical to the anim lane's OFF build)

| Define | Effect |
| --- | --- |
| `-DSAT_WV_GROUND=1` | Each step's drawn pose is moved so its lowest opaque row is on the floor line (`wv_gy`, one signed byte a step). MSHvSF's deliberate lifts (heavy-punch hop, flying kick, high-hit pop-up) are kept. The jump uses the sole-exact arc (today's apex), so take-off and landing touch the floor. |
| `-DSAT_WV_GROUND=2` | Strict: every step on the floor line, no lifts at all. |
| `-DSAT_WV_JUMP=1` | Jump apex scaled to the AvP jumpers (88 px of sole height, x0.838). Rise and fall timing is MSHvSF's, unchanged. |
| `-DSAT_WV_JUMP=2` | Half way between that and today (x0.919, 96.5 px). |
| `-DSAT_WV_SCALE=14` | He is drawn at 14/16 of his size (VDP1 scaled sprite, same command as the 11/12 table), boxes scaled with him. Needs `SAT_GFX_FIT 1` (the default). |

Defines combine (`-DSAT_WV_GROUND=1 -DSAT_WV_JUMP=1`). Generated tables: `tools/wolverine/ground.py` (new, asset stage: reads the MSHvSF capture, writes `ground`,
`ground_floor`, `jumpair` into `remap.json`), emitted by `gen_c.py`. `wolverine.c` has three guarded additions (`sy += wv_gy[step]`, the scale of his tiles and
boxes); `sat_gfx.c` has one guarded function. Nothing is compiled without the define.


## A. Jump height

### What AvP does (MAME avspu, arcade sprite lists, `tools/wolverine/ap_measure.lua` + `run_ap_measure.sh`; sole = lowest opaque sprite row, native 384x224 px)

| Character | Neutral jump (state 020004) | Sole lift at apex | Origin lift (`+0x14`) | Length |
| --- | --- | --- | --- | --- |
| Schaefer (Dutch Schaefer, the slot Wolverine rides) | a flat leap: the body stays on the floor line (sole row 194 to 195 against 195 standing; the head pose changes, 7 px) and the player travels sideways (about 120 px back, longer forward). `+0x14` stays 320. | 0 to 1 px | 0 | 42 frames |
| Linn | rises straight up, top of the sprite leaves the screen (row -30) | 128 px | 104 | 50 frames |
| Predator Warrior and Hunter (identical arc) | rises straight up | 88 px | 76 | 39 frames |

Finding: Schaefer does not jump. His 020004 is a long, low leap; the vertical arc Wolverine shows is entirely his own (MSHvSF's). The cast that does jump has a median apex of 88 px
(Predators 88, Linn 128). Wolverine today: MSHvSF's arc over 33 ticks, 105 px of sole height at the apex (99 by pose bottom, the figure in the first notes), so he is inside the AvP
range, above the Predators and below Linn. By body height: Predators jump 1.0 to 1.1 body heights, Linn 1.6, Wolverine 1.25. Plot: `jump_arcs.png`. The AvP arcs hang at the top
(apex held over about 25 percent of the jump); MSHvSF's is a triangle that peaks 30 percent in and lands at 80 percent (the rest is the landing crouch), so it rises faster for the same height.

### Variants (arc shape unchanged, heights scaled; sole height at the apex)

| Variant | Define | Apex |
| --- | --- | --- |
| Current (default) | none | 105 px (legacy `wv_lift`, unchanged bytes) |
| AvP-matched | `-DSAT_WV_JUMP=1` | 88 px, x0.838 (the median of the three jumpers; the Predators' number) |
| Midpoint | `-DSAT_WV_JUMP=2` | 96.5 px, x0.919 |

The variants use the sole-exact lift (`wv_lift` becomes `signed char` for them: lift = scale x the original's sole height + the pose's sole offset), so take-off and landing are on the floor
line in all three; the default table is the old unsigned one.

## B. Ground contact

### Cause
Poses are anchored by the bottom row of their tile grid. The lowest opaque row of a pose (its sole) sits 0 to 16 rows above that, and by a different amount per pose: the stance (pose 17) is 7
rows above it, the heavy-punch lunge pose 1 row. Bottom-anchoring therefore floats or sinks every pose by the difference. Floor line = the stance's sole (Yaba: within 1 px of Schaefer's own feet,
verified in the anim lane). `tools/wolverine/ground.py` measures each pose's sole from its tile pixels, and the original's own placement from the MSHvSF capture (origin screen y from
`origin.txt`/`boxes.txt`, camera scroll included), and decides per step:
- on the floor line (a pose within 4 px of the floor in the original, and always idle, walk, crouch, throw), or
- lifted by what MSHvSF itself lifts it (heavy-punch hop, flying kick, high-hit pop-up, knockdown flight), never below the floor line.
`SAT_WV_GROUND=1` does that; `=2` puts everything on the floor (no lifts).

### Pose offset table (px, down positive; "before" = how far the pose's sole sits below (+) or above (-) the floor line today)
| pose | before: sole vs floor (px, + = sunk) | strict offset | default offset (lifts kept) | moves | ticks |
| --- | --- | --- | --- | --- | --- |
| 5 | +0 | +0 | -6, +0 | knockdown, throw, tornado, walk | 10 |
| 6 | +0 | +0 | -5, +0 | knockdown, throw, tornado, walk | 15 |
| 8 | +1 | -1 | -1 | throw, walk | 20 |
| 13 | -2 | +2 | +2 | throw, walk | 6 |
| 14 | -4 | +4 | +4 | throw, walk | 7 |
| 15 | -9 | +9 | +9 | walk | 5 |
| 16 | -1 | +1 | +1 | walk | 3 |
| 17 | +0 | +0 | -8, -6, +0 | berserker, hk, hp, idle, knockdown, lp, tornado | 30 |
| 18 | +0 | +0 | -6, +0 | berserker, hk, hp, idle, knockdown, lp | 55 |
| 20 | +0 | +0 | -12, +0 | berserker, hk, hp, idle, knockdown, lp | 42 |
| 25 | +2 | -2 | -11, -2 | berserker, crouch, hk, hp, knockdown, throw, tornado | 30 |
| 30 | +2 | -2 | -2 | crouch, hp, knockdown | 56 |
| 31 | +2 | -2 | -12, -2 | berserker, crouch, hp, knockdown, throw | 17 |
| 32 | +6 | -6 | -11, -6 | berserker, hp, knockdown, throw | 13 |
| 37 | +2 | -2 | -2 | hp | 21 |
| 39 | +1 | -1 | -1 | hp | 7 |
| 40 | +0 | +0 | -11, +0 | hk, throw | 9 |
| 41 | +3 | -3 | -15, -3 | hk, throw | 36 |
| 45 | +1 | -1 | -1 | berserker, crouch, hk, knockdown, throw, tornado | 19 |
| 49 | -2 | +2 | +2 | berserker | 18 |
| 50 | +3 | -3 | -3 | berserker | 6 |
| 51 | +2 | -2 | -2 | tornado | 9 |
| 53 | -5 | +5 | -13, +5 | tornado | 28 |
| 56 | -5 | +5 | +5 | tornado | 3 |
| 57 | +3 | -3 | -10 | knockdown | 16 |
| 68 | +2 | -2 | -2 | hit_h, knockdown | 8 |
| 69 | +2 | -2 | -2 | hit_h, knockdown | 57 |
| 71 | +6 | -6 | -6 | hit_etc, hit_m, knockdown | 10 |
| 106 | +1 | -1 | -1 | hit_h | 3 |
| 122 | +1 | -1 | -1 | hit_etc | 2 |
| 123 | +1 | -1 | -1 | hit_etc | 3 |
| 124 | +1 | -1 | -1 | hit_etc | 1 |
| 125 | +1 | -1 | -1 | hit_etc | 6 |
| 126 | +1 | -1 | -1 | hit_etc | 4 |
| 132 | +2 | -2 | -2 | hit_h, hit_m | 5 |
| 134 | +4 | -4 | -16 | hit_h | 3 |
| 135 | +4 | -4 | -16 | hit_h | 3 |
| 136 | +4 | -4 | -16 | hit_h | 2 |
| 137 | +4 | -4 | -16 | hit_h | 1 |
| 138 | -8 | +8 | -16 | hit_h | 2 |
| 139 | +6 | -6 | -32 | hit_h | 1 |

Moves that carry a hop or lift in the default (`=1`) column: heavy punch (-2 on the lunge), flying kick (-11, -15), high-hit pop-up (-16 to -32), knockdown flight (-6 to -12), Tornado
Claw landing (-13). The strict column is the plain "feet on the floor" fix. Biggest corrections of pure floating: walk pose 15 (9 px above the floor), pose 14 (4), 13 (2); biggest sinking: poses
32 and 71 (6 px below; the jump landing and the hit/knockdown recovery), 41 and 50 (3 px). Idle (all 12 steps) and the light punch were already on the floor line.

Sheets: `ground_pose_sheet.png` (HOST, offline render of the pose tiles before and after on the floor line), and the Yaba tour clips (EMULATOR) listed under results.

### Hurt and attack boxes
The boxes are game-space data (`wv_box`, relative to the player, in AvP's collision). `SAT_WV_GROUND` only changes where the art is drawn: the `wv_box`, `wv_steps`, `wv_tiles`, chain and timing
tables of every variant are byte-identical to the default (diffed in the generated `wolverine_data.inc`), and the hook that pokes boxes into the collision pass is not touched. What does change
is the relation between a drawn pose and its box by the step's offset (0 to 2 px on most steps; the table above); the boxes were captured against MSHvSF's origin, so a pose lifted by its
authored hop now sits where its box already was. Nothing moves in the collision.

## C. Size ("should he be smaller?")

Line-up on one floor line, native 384x224 px (AvP: MAME avspu sprite lists, idle; Wolverine: MSHvSF stance pose 17 from the capture; `lineup.png`). The Saturn squeezes every sprite horizontally by
11/12 under `SAT_GFX_FIT 1` (rows are 1:1), Wolverine's included, so the ratios below hold on the console.

| Character | Standing height (px) | Bounding width (px) | Torso ("shoulder") width (px) |
| --- | --- | --- | --- |
| Linn | 80 | 55 | 46 |
| Schaefer (Dutch Schaefer; "Schaefer" and "Dutch" are one character) | 86 | 88 (with the rifle) | 68 |
| Predator Warrior | 88 | 66 | 41 |
| Predator Hunter | 80 | 72 | 43 |
| Wolverine (stance 17) | 84 | 87 (claws out) | 49 |

Ratio: Wolverine is 0.98 of Schaefer, 1.05 of Linn, 0.95 to 1.05 of the Predators, by height. By lore he is 5'3" against Schaefer's about 6'2" (0.85), Linn about 5'6" (0.95) and a Predator
about 7'(0.75). AvP's own cast is not drawn to lore either (the Predators are only 0 to 10 percent taller than Linn and Schaefer; lore says 25 to 40), so the arcade scale is a gameplay scale,
and a 84 px Wolverine sits inside the cast's 80 to 88 px band: nothing looks wrong beside them.

Recommendation: keep the current size. A smaller one is defensible only on the Schaefer ratio: x0.875 (14/16) gives 73 px, the 0.85 lore ratio against Schaefer. It costs: VDP1's scaled
sprite drops 2 of every 16 rows and 3.2 of 16 columns (now 1.3), so thin claws and outlines crawl while he moves; plot cost is unchanged (the same scaled-sprite command, no new tiles, same
command count), code cost 88 B of high RAM (`hw_free` 4,616 to 4,528, `lw_free` 76 unchanged). His boxes scale with him (centre and half sizes x14/16 about his feet): his reach and hurt
box are 12.5 percent smaller, so his hits land shorter and he is a little harder to hit; the AvP depth bytes are unchanged. That changes how fights feel and should be judged by playing it.

## Results (EMULATOR = Yaba, own copy on MCP port 9717; MAME for the arcade measurements; HOST = tables and offline renders)

| Check | Result | Tier |
| --- | --- | --- |
| Default build vs the anim lane's OFF build | same ELF size (2,039,956 B); the ISOs differ in 184 bytes, all in sectors 16, 18 and 23 (volume dates); `wolverine_data.inc` differs only by the added `#if` blocks; hw_free 4,616, lw_free 76 | HOST |
| Variants hw_free / lw_free | ground, ground2, jump_avp, jump_mid, ground_jump_avp: 4,616 / 76 (tables are cart ROM); scale14: 4,528 / 76 | HOST |
| `wv_box`, `wv_steps`, `wv_tiles`, `wv_pose_start`, `wv_move_start`, `wv_nat_tab`, `wv_chain_tab` of every variant | byte-identical to the default's (boxes and timing untouched; `wv_speed_tab` untouched) | HOST |
| WSL tests (tests/, `unittest discover`) | 91 run, 61 pass, 30 private-dep load errors (baseline); `test_wolverine_*` 22 of 22 OK | HOST |
| `fit.py` (76 files) | gate False on `stage24_ma` (wolverine drop 2,873 against Schaefer 2,872): this is the state of the anim lane's final workdir, not of this change. Run against the anim lane's own `w1` and `D6` it gives the identical fail (cart_pack_room 1,630,208; the anim lane's 4:42 gate saw 1,634,304, 4,096 B more, before the later guest-code builds). 0 own dropped, no missing keys, 1,511 tiles. Needs the coordinator: the gate is red at the anim tip. | HOST |
| Jump, 3 variants | each disc: he leaves the floor on the 020004 state (32 to 35 ticks), same timing, same sideways travel (944 to 825); clips below | EMULATOR |
| Ground contact on a tour (idle, walk, taps, a mashed chain, walk, jumps; 600 to 700 frames, enemies present so hit and knockdown poses occur) | step timeline from Yaba against the pose tables: frames within 1 px of the floor line: default 69 and 73 percent (two tours); `SAT_WV_GROUND=1` 80 and 88 percent (the rest are MSHvSF's authored lifts); `=2` 100 percent. Off-floor frames of the default by move (tour 1): hit/getup 80 of 165, knockdown 52 of 133, walk 16 of 132, heavy punch 4 of 14, kick 54 of 84; idle and light punch 0 | EMULATOR timeline + HOST tables |
| Size build | draws smaller, tiles join cleanly in idle, walk and attack (`clips/scale_compare.png`) | EMULATOR |

Not done: the 100 percent pixel measurement of each pose's sole in the screenshots (the stage scrolls and he moves in depth in the tours, so a fixed floor line is not valid per frame; the offline pose sheet draws the line exactly); play-through of the variants beyond the tours; hardware.

## Evidence (E:\AvP\learning\lane-wolverine-ground, never in git)
`clips/jump_current.gif`, `jump_avp_matched.gif`, `jump_midpoint.gif`, `jump_compare.gif` (3 panels, same moment, floor line red), `jump_compare_rows.png`, `jump_arcs.png`;
`ground_pose_sheet.png`; `lineup.png` and `lineup_stats.json`; `clips/scale_compare.png`; `avp_jump_arcs.json`; `ground_report.txt` (every step's offset); AvP captures `ap_c0..c3`, MSHvSF capture `capG`.
Discs to play, each a self-contained cue and iso under `discs\<tag>`: `cur` (default), `ground` (`SAT_WV_GROUND=1`), `ground2` (`=2`), `jump_avp` (`SAT_WV_JUMP=1`), `jump_mid` (`=2`),
`ground_jump_avp` (ground and AvP jump), `scale14` (`SAT_WV_SCALE=14`).

## Table formats (for the native lane's rebase)
Added to `wolverine_data.inc`, all under `#if`: `wv_gy[WV_STEPS]` (signed char, one per step in `wv_steps` order, only with `SAT_WV_GROUND`); under `SAT_WV_JUMP` or `SAT_WV_GROUND` `wv_lift` is a
`signed char` table of the same length (2 per step, from and to) instead of `unsigned char`. Default tables are unchanged byte for byte. `wolverine.c` reads `wv_gy` after the lift block in
`sat_guest_objects`; the scale code is in the tile loop there and in `sat_guest_wolverine_boxes`. New asset-stage keys in `remap.json`: `ground`, `ground_floor`, `jumpair` (from `ground.py`, run after
`retime.py`/`boxes.py`, before `gen_c.py`; needs the capture with `origin.txt`, made by `mame_wolverine.lua` with `WV_BOXES=1`).
