# REIMPLEMENT-13-SOURCE-CLOSED-ROUND1 handoff (2026-11-06, lane avp-native)

RESUMED by owner 2026-11-06; decision recorded in project_state.yaml owner_decision_2026_11_06.
Branch `codex/avp-playable-loop-pivot`, one writer. Do not touch `history.txt` or `data/avsp_anim_records.json`.
Card says CLAUDE_ALLOWED false and AGENTS names Astra; left unedited and reported to the owner as an open conflict.
Not candidate promotion. USER-09/USER-10/HW-01 unchanged; physical Saturn UNRUN.

## What changed

- Normal play runs `avsp_round1_step_interactive_frame` (round1.c): 1 tick per frame; 3 per frame in fast-forward
  (5 polls of held input during the scripted exit; port policy). AUTOTEST keeps the capture adapter.
- Fade waits: teardown phases of the exit display machine hold gameplay ticks. Durations still come from SPEC
  coffee_exit stall constants; `source_recon/avsrc_fade.c` has a palette-driven contract not yet wired.
- Containment: in normal play an actor body that leaves covered source programs is released and logged in
  `avsp_round1_containment`; differential builds still fail closed. This is a counted gap, not a pass.
- Boundary check: tests/port_v2/round1/test_interactive_tick_boundary.py (with a negative control).
- Host sim: tests/port_v2/round1/round1_interactive_tick_sim.c (idle/source/bot/fuzzN).
- Emulator driver: tools/run_interactive_emulator.py; waits for any other yabasanshiro (one MCP port, one ini).
- Scripted input profile: env AVSP_INPUT_SCRIPT=1 at build. Never label it interactive proof.

## Known defects in normal play (emulator frames, E:\AvP\native\script2)

1. Player has no KO or continue: health reaches zero and play goes on (host idle shows -9).
2. Two repair-unit props stay at a fixed screen position while the camera scrolls. Cause not examined.
3. Score and enemy health bar did not change in the frames viewed.
4. After the Coffee Shop exit, live_frame stops at 4718 and no next-room gameplay exists natively.
5. PCM cues are silent by design in live_encounter_audio_step; audio/load gap stays 279/281.
6. Class0e Saturn draw not wired. tag8 no-op is already in avsp_emit.c.

## Scene report (host, differential path, unchanged by this work)

103/747 missing lifetimes; 1/708 unowned; 501/1494 endpoints; 93/149 health events; 279/281 audio/load. RED.

## Not run

Fast and Oracle lanes, test_entry.py (EXPECTED now pins SPEC 836518b1; review of that pin is not independent),
paired cold Emulator runs, real pad input on an emulator, audio output (SoundCore 0), physical.
The Target exhaustion note on the card predates the owner decision; see the state file for the new budget.

## Next, in order

1. Player KO/continue from accepted oracle11 player_hitko_continue evidence (defect 1).
2. Drive containment down: host trace by site, top entries are player-step site 2 and class1f codes 11/15.
3. Props and HUD defects 2 and 3. 4. Wire route_wait from avsrc_fade.c. 5. Class0e draw. 6. Audio commands to PCM.
7. Run Fast and Oracle. Build regenerates data/reimplement13_round1_memory_plan.json: review before staging.
