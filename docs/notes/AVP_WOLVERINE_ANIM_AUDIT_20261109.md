# Wolverine animation audit and first pass, 2026-11-09

Lane `lane/wolverine-anim-20261109`, from `3e62e47` (Wolverine v4.1 + default-off FPS experiments). Tiers: HOST (tools, tests, fit), MODELLED (none),
EMULATOR (Yaba: see the end for what was and was not run). Hardware UNRUN. Reference = MAME mshvsf captures (`tools/wolverine/run_mame.sh`,
deterministic: two runs of the full.txt schedule give identical object lists). No ROM data, captures or generated assets are in the repository.

## What the audit found

1. **The shipped "full" move data is thinned.** `remap.json["moves"]` of v4.1 came from the THIN pipeline: a dropped pose's frames were already merged
   into its neighbour before the tile budget was applied. `timeline.py CAPTURE ASSETS FROM TO` matches every capture frame to the poses of a remap and
   shows the real sequence. The reference walk loop is 16 poses in 41 frames (5 6 7 8 ?0 9 10 ?1 11 12 13 14 ?2 15 ?3 16, three to five poses a
   2-3 frame step); v4.1 resident: 8 of them (5 6 7 9 11 13 15 16). Four more of the loop (?0 ?1 ?2 ?3) are in no remap at all.
2. **Idle is a different loop.** MSHvSF's standing loop (capture frames 1843-1901, repeating every 59 frames) is 17 poses:
   17 18 19 20 21 22 23 24 0 1 2 3 4 35 46 47 48. v4.1 played a 4-pose, 10-tick loop (118 1 2 3), the fragment the one-frame-pose capture window held.
   That is the pose the player sees most of the time, six times too fast.
3. **Anchors.** The feet-tile anchor of assets.py is within 2 px of MSHvSF's origin for the stance loop except pose 0 (7-8 px off: the idle jump v4.1
   fixed with pose 118). Walk poses are anchored by feet on purpose (the origin hops 3-6 px a frame, the feet tile 3 px; the walk is distance driven).
4. **Chain.** Schaefer's attack state 020006 does not leave while the attack button is tapped (MAME states.tsv: 56 ticks for about four 15-tick
   attacks), so v4.1's LP/HP alternation, keyed on a fresh entry to the state, played ONE move for a whole mashed chain and then held its last pose.
   The first attack of a fresh chain was HP (chain_ started at 0, incremented before use). 02000e (HK) came up only after a hit in the measured walk.
5. **Dash** (WV_DASH) is never selected by move_for (Schaefer's dash is the walk state); its 53 unique tiles were resident for nothing.

## Move table (reference frames, v4.1 resident steps, this pass)

| Move | Reference (MSHvSF) | v4.1 resident | This pass | Visibility in play |
| --- | --- | --- | --- | --- |
| idle | 17 poses, 59 frames, loops | 4 poses, 10 frames | 12 poses, 59 frames (resident poses only, 0 new tiles) | highest |
| walk | 16-pose loop, 41 frames per 119 px; start 2 poses | 8 loop poses | 10 loop poses (+8, +14, 53 tiles) | highest |
| lp | 8 frames start, 5 active, recovery in the stance loop | 14 steps, 12 poses | unchanged; chain fixed, see below | high |
| hp | 6 attack poses over 38 frames | 9 steps, 3 attack poses (35 37 39) | unchanged | high |
| hk | 40 41 42 43 44 45 ...: 28 steps | 18 steps; state 02000e rarely reached | reachable as the chain finisher | medium |
| hit_etc / hit_m / hit_h | 9 / 11 / 15 steps | all resident | unchanged | high |
| jump | 33 steps (mostly stance loop + landing) | 15 steps | unchanged | medium |
| knockdown / crouch(getup) | 29 / 6 steps | 16 / 4 | unchanged | medium |
| berserker / tornado | 32 / 15 | 21 / 10 | unchanged (rare) | low |
| throw | 29 (walk-in grab) | 17 | unchanged; walk poses 8 and 14 now in it | low |
| dash | 19 | 14 (unused) | removed | none |

## Changes in this pass

- `tools/wolverine/timeline.py`: capture-to-remap pose timeline (the audit instrument).
- `tools/wolverine/retime.py`: idle loop, walk additions, dash removal, re-trim, residency; boxes.py takes the idle loop (window hurt box on every
  step, no hit box). Result `D5`: 64 poses, 1,493 tiles (unchanged total; v4.1 stage 24 passes at this count, limit about 1,514).
- Runtime (`saturn/guests/wolverine/wolverine.c`): attack chain light, light, heavy, kick, new attack told by 15 native ticks of the state
  (`pre` flag so the post-hook cannot fire it a tick early), restart on the same move, chain resets after `WV_CHAIN_GAP` (30) idle ticks, the chain kick
  holds with the state's 15 ticks. Per-move numbers (native ticks, chain) come from one generated table (`wv_nat_tab`, `wv_chain_tab`, gen_c.py).
- Tests: the clock fixture covers the new chain order, the reset gap and a continuous (never-leaving) 020006 run. Python tests pass; the C fixture
  runs only where gcc exists (WSL).

## Where Schaefer's logic limits the feel

- Attack state 020006 has a fixed 15-tick native length and no hit-confirm: the chain advances on the button, not on a hit; no cancel windows.
- Walk and dash are one state (020002) at constant speed: no acceleration, no braking, instant turn (+0f). A dash can only be seen as speed.
- Jump arc and air attack come from state 04; Wolverine's air poses are time-stretched over it, no air normals of his own.
- Hit stun length (28 ticks, 107 for a knockdown) and its size (health delta) are Schaefer's; MSHvSF's reactions are 20-23 frames.
- Damage and knockback of every attack are Schaefer's attack records (the hook only borrows reach); LP and HP differ in reach and timing, not damage.
- Grab/throw is walking into an enemy (state 0204xx); there is no throw button.
- A native fighter (step 4) would own all six; steps 2 and 3 (speed, native timing) stay switchable on top of the tables.

## Results

| Check | Result | Tier |
| --- | --- | --- |
| Python tests | 91 run in WSL: 61 pass, 30 error loading private MAME deps (the known set); `test_wolverine_*` 22 of 22 pass with the C fixture running (gcc in WSL) | HOST |
| fit.py, all 76 stage files, assets D5 | gate True, 0 own tiles dropped, no missing guest keys, 1,493 Wolverine tiles (same as v4.1; stage 24 limit about 1,514) | HOST |
| Build (POSE_KEYS=0 KEEP_ROUND_FILES=1, flags as v4.1) | rc 0, 1,792 s (packs rebuilt), hw_free 4,624, lw_free 92 (v4.1 left 104), iso 377,784,320 bytes | HOST |
| Idle, Yaba stage 02, 240 frames | published step changes 86 (v4.1, 4-pose 10-tick loop) vs 54 (59-tick loop); contact sheet shows a smooth breathing loop, no side pops | EMULATOR |
| Chain, Yaba, mashed attack (state 020006 throughout) | v4.1: one HP held 58 ticks; now LP 32, HP 51, HK 17 (cut by a hit) in one 020006 run: the chain advances and the kick is reached for the first time | EMULATOR |
| Save/load, pick-ups, scripts, Round 1 to boss run | not run | - |

Disc: `E:\AvP\learning\lane-wolverine-anim\w1\sat.iso`. Clips (before = v4.1, after = this build, same harness `v4rec.py`):
`E:\AvP\learning\lane-wolverine-anim\clips\{idle,walk,chain}_{before_v41,after_anim}.gif`, `idle_after_sheet.png`.

## Not done in this pass

Step 2 (his walk speed, jump arc, dash for his slot only) and step 3 (`SAT_WV_NATIVE_TIMING`: his own timing, damage and pushback) were not started, and
the Round 1 to boss gameplay-equivalence run was not made; the chain change touches only which move is shown and the hold lengths, but it is not gated.
One number for step 2: Schaefer's walk is about 2 px a tick (x 944 to 1182 in 120 ticks incl. start-up, MAME states.tsv); MSHvSF's is about 2.8 px a frame.
The invisible-Wolverine case is untouched. Walk poses 10 and 12 (and ?0..?3 of the loop) need 117 + about 120 more tiles; the lossy near-duplicate tile
merge (idea: merge tiles within a few pixels) was not measured because numpy is missing in the lane python.

# Second pass (steps 2 and 3), same day

## Finds
- **Jump was broken, not thin.** The v4.1 jump move was a window that held the standing loop for 40 of its 117 ticks; the airborne poses were not
  resident and poses are anchored by their own bottom row, so a jump showed him standing and sliding sideways. AvP keeps no height in the player block
  (probe: +14 stays 320 through the jump; the jump is 33 ticks of 020004, 23 with a forward key held), the arc was in Schaefer's sprites.
- **Walk speed:** AvP 1.8-2.2 px a tick (Yaba, 290 held frames, 1.78 mean over the held stretch incl. start); MSHvSF about 2.8 px a frame. Dash is the walk state: tap,
  release, hold gives no faster travel than a held walk (x steps every 4-5 ticks, 2.2 px mean), so there is no dash speed to scale.
- **MSHvSF jump** (capture frames 2103-2157): 41 frames airborne, apex 83 px (origin), 55 frames with crouch and landing; rise 14 frames, fall 26.

## Changes
- `retime.py` (RETIME_CAPTURE): jump rebuilt per tick over 33 ticks, resident air poses 27 28 29 (+25 30 31 32), per-step `lift`; `gen_c.py` emits
  `wv_lift` (from/to a step, interpolated across it by the runtime), `wv_speed_tab` (walk 22/16 = 1.375, x and depth, his slot only) and keeps `wv_nat_tab`,
  `wv_chain_tab`; JUMP is a once-move now.
- `tilemerge.py` (numpy): merges resident tiles that differ in at most K weighted pixels (colour change 1, opaque against transparent 3), mirrors included.
  K 8 takes the 1,593 tiles of the jump set to 1,511, the count v4.1 passed at; contact sheet comparison shows shading-level differences only (K 6 with an
  unweighted count left specks, hence the alpha weight).
- Runtime: the walk speed scale runs in the post-update hook (the native step dx, dz is scaled with the remainder kept; jumps of position over 24 px are left
  alone). The collision hook now reports landed hits (target health or hit-flag byte changed across the call); with `-DSAT_WV_NATIVE_TIMING` the chain goes
  on only from a landed hit and a whiff starts it over with the light punch (host test covers it).
