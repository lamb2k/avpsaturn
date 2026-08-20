# Goal

Pursue this until every full-game completion condition holds. This file holds
the destination; `docs/PARITY_PLAN.md` holds the overall work plan;
`docs/ROUND1_EXECUTION_PLAN.md` holds the active granular package graph;
`docs/NEXT_AGENT_PROMPT.md` holds only the first executable package; and
`docs/AGENT_HANDOFF.md` holds the volatile checkpoint.

## Objective

A private, native Sega Saturn port of the complete US `avspu` revision of
Capcom's CPS2 Alien vs Predator at **functional parity** with the arcade game,
running on real NTSC Saturn hardware.

The complete game includes the boot/title and attract flow, character select,
every playable character, every round and stage, enemies and bosses, weapons
and items, HUD/scoring/lives/continues, game over, endings and credits, and the
complete music, voice and sound-event set. Complete and validate the entire
single-player game first; then support the arcade revision's original
simultaneous-player count before final completion.

Functional parity means that the same initial state and inputs reproduce the
arcade's gameplay state trajectory, real hitboxes, real animation sequences and
durations, stage events, progression and audio cues. It does not require
identical framebuffers, cycle timing, PRNG streams or sub-pixel rounding except
where gameplay behavior depends on the same generator and call order.

## Capability Gate 1

Round 1, "City of Despair", from the frontend through the Round 2 title is the
first capability gate. It must prove the reusable extraction, semantic-runtime,
Saturn-rendering, audio and validation approach before broad content expansion.
Passing Gate 1 is a major checkpoint; it is not completion of the full-game
goal.

## Complete when all of these hold

1. **Complete content and flow:** boot/title, attract mode, character select,
   all characters, rounds, enemies, bosses, items, weapons, continues, game
   over, endings and credits are present and traversable in arcade order.
2. **Animation and presentation:** all systematic actor/effect animation plays
   from ROM-derived scripts, assemblies and referenced graphics interpreted or
   translated by the native runtime; captures are regression oracles, not the
   shipped animation source.
3. **Collision:** every required player, enemy, boss, weapon, item and stage
   interaction uses collision data read from the game rather than inferred
   contact windows.
4. **Behavior:** required player, enemy, boss and object behavior comes from
   translated 68000 routines and extracted tables, with PRNG generator and call
   order identified wherever decisions depend on them.
5. **Stage and game systems:** spawns, camera, scrolling, triggers, difficulty,
   scoring, HUD, progression and transitions consume extracted game data rather
   than route-specific authored approximations.
6. **Audio:** the complete music, voice and sound-event set has source timing,
   native SCSP/CDDA ownership and measured CD/DMA behavior without channel
   leaks, late data reads or transition stalls.
7. **Single-player validation:** every selectable character completes the full
   game, including continues, final boss, ending and credits, with no
   unexplained semantic divergence from deterministic MAME evidence.
8. **Multiplayer validation:** the arcade revision's original simultaneous-
   player capability completes the game with correct joins, HUD/score ownership,
   camera, spawns, collisions, items and transitions under worst-case load.
9. **Hardware:** a clean `normal-release` disc completes the required
   single-player and multiplayer routes on a physical NTSC Saturn with digital
   pads, the required multitap and a 32 Mbit RAM cartridge at sustained 60 Hz,
   with audio and no partial cels, palette corruption, allocation failure,
   asset failure or unsafe CD/CDDA overlap.

## Non-negotiable

- Native SH-2 gameplay. Never a CPS2 emulator, video player, host-only
  simulation or animation viewer.
- Preserve functional parity across the complete game; do not close a global
  condition from a Round 1-only or single-actor slice.
- Never commit ROM data, raw captures, generated copyrighted assets or disc
  images.
- Label work honestly as proven, approximate or missing. Never report the goal
  met while any full-game condition remains open.
- Private porting research only. Distribution, public demonstration or
  promotion requires an explicit rights-holder and licensing review; see
  `NOTICE.md`.

## If blocked

Record the blocker, exact failure text and next reproducible command in
`docs/AGENT_HANDOFF.md`, then continue the next independent condition when
safe. Do not silently substitute an easier target for a blocked one.
