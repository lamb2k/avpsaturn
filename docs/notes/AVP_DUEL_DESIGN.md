# PvP duel: design

Status: Draft. Nothing built or run. Tiers: READ = 68000 code read in this lane or docs/notes/AVP_NOTES_ACTOR.md; ESTIMATE = my judgement, not measured. Hardware UNRUN.

**Recommendation: build it.** Reuse the game's own hit test from a small duel driver loaded from CD, one arena first. No lifted game function changes, so arcade mode stays out of the path. Effort ESTIMATE: small arena version about 1 to 2 lane sessions, most of it in KO handling and bot runs.

## What the code already gives (READ)

- **Hit test works on any two actors.** 0x1cf54 takes attacker a6 and target a1. It checks live state, the target's +0x70 and the one-hit-per-attack id (+0x67 against +0x2d), then the box test at 0x1d25e. A hit runs knockback direction, 0x1d314, `damage_apply` 0x1d504, 0x1d492, the hit effect 0x1d622, 0x1d6e2.
- **Player targets are handled.** Target tag +8 = 0 means player; 0x1cf6c branches on it, and 0x1cfe6 runs 0x1d73a for it.
- **Player attacker on player target has a path.** At 0x1d606 it does 1 damage, or 0 if the target is at 0. So the arcade has friendly hits at a token level, and the duel needs more damage than that.
- **Enemy hits on players** use a table row from current health, and health 0 to 5 becomes 0 (0x1d5f6).
- **Not read yet:** whether arcade loops ever pair two players, what 0x1d716 rejects for a player target (it can veto the hit), and 0x1d314, 0x1d492, 0x1d6e2. These are the first check of the build.

## Design

| Part | How | Cost (ESTIMATE) |
| --- | --- | --- |
| Hits | Each game tick the driver calls 0x1cf54 for every ordered player pair, after the normal actor pass. Projectiles and weapon children loop over the same target list, keyed by owner. A pair list keeps player 3 open. | Few hundred bytes; a few box tests per tick |
| Health | Driver reads target health before and after the call. If it fell by the token 1, it applies duel damage: the attack's enemy-table value through the health row, clamped. The game's 0-5 rule stays. | Small |
| KO | Player health at 0 enters the game's own KO state (top state 4 at player +4). The driver sees it first and blocks the continue path. | **Main risk:** the KO flow is written to lead to a continue screen |
| Arena | One Round 1 section with spawn table walking stopped and the camera held at a fixed value, using the stage's own floor and bounds. Both players start at fixed spots. | Stopping the table and scroll cleanly needs the actor pass read |
| Win state | First to 2 rounds. Each round is last standing, or more health at a time limit, with equal health a draw and a replay. Result text in the game's font, then return to title through the same load path as attract. | Small |
| Files | DUEL.BIN overlay in low RAM, plus a stage file variant for the pair. No new resident code but one hook and flag. Low RAM has about 4 KB free, so the overlay must stay under about 3 KB, or take a page of free cart space. | Size is a limit to check |

**Arcade safety:** the hook sits in the Saturn kernel behind a mode flag and is off in arcade. Calling 0x1cf54 from native code needs it as a lifted root. A root can change the lift split, so the host check against all goldens is rerun.

**Stage file:** the measured pair is Warrior + Schaefer. The first arena uses that pair's stage file for stage word 02. Other pairs' files lose some keys (STATUS, per-character stage files), so they get a key check before they are offered.

## Random aliens

Same principle: the game's own alloc, class init and AI. The aliens need no duel-specific logic, because enemy AI already targets players.

| Question | Recommendation | Why |
| --- | --- | --- |
| How often | One spawn try every 8 to 15 s at random, none in the first 10 s of a round or while a player is in KO. Skipped if at the cap. | Keeps the duel about the players. Tune by play; ESTIMATE |
| Cap on live aliens | **2 in the first version, 3 at most** until drawing is measured. | Pool room is not the limit: enemy pool 0xff9580 has 20 slots of 0xc0 bytes (the bot's and RNG analyzer's layout). Drawing is: two players peak up to 132 objects against 96 for one, the game already overruns its field in emulator runs, and 60 Hz does not hold. Measure with SAT_PROF on the emulator (MODELLED), then raise |
| Which types | Only alien rows found in **that stage's own spawn table** (16-byte rows, 0x1be5e, selected by ff81e8), whose sprite keys and sound clips are all in the pair's file. Built offline into a short list in DUEL.BIN. No bosses, no scripted or control rows (kinds 0x1c, 0x18). | Guarantees no blank tiles and no silent clips. The list also carries each row's init values, so a spawn is a normal table row. Which rows qualify is not yet worked out |
| Spawn place | Off the arena edge, away from the nearer player, as the table's camera-driven entries appear. | Fair; no pop-in |
| Random seed | Use the game's generator: 16-bit seed at ff81a8, recurrence as in tools/analyze_oracle11_round1_rng.py. At duel start only, mix in the vblank count and pad state from the title. The spawn timing and type draw from a separate duel seed with the same recurrence, stored by the driver. | A separate seed keeps enemy AI consumption from shifting the spawn plan, and a logged seed makes a bot run repeatable. This recurrence's period is not measured; check it stays long from the starting seed, or reseed |
| Do alien hits count | **Yes, as damage and as KOs.** A player KOed by an alien loses that round; no credit tracking. Both down in the same tick is a draw and a replay. | Simplest rule, and it makes the aliens a real hazard |
| Do alien kills count | **No for the result.** Score only, shown at the end; health decides a timeout. | Otherwise hunting aliens beats fighting the opponent |
| Between rounds | All aliens released through the normal release, so no slot leaks. | Pools do not clear on alloc: bodies set what they read, so the normal path is required |

Aliens also get hit by both players through the game's normal loops. A dying alien's drops are the one open point: pick-ups heal, which could swing a duel. First version: leave them as the game does, and review on play.

## Order of work

1. Read 0x1d716, 0x1d314, 0x1d492, 0x1d6e2, the arcade loop callers at 0x1c9e0 to 0x1cc5c, and the KO flow.
2. Hits and health only in stage 02, no arena lock; bot run with stills.
3. Arena lock, KO block, win state and return to title.
4. Aliens at cap 2; drawing measured with and without them.

## What could stop it

- KO flow can't be held without changing lifted code. Fallback: a lifted override used only in duel mode, with host check rerun.
- 0x1d716 or weapon code assumes enemy targets and misbehaves with a player as target.
- Fighting at closer range than the arcade's co-op stresses player state the routes never exercised, so the goldens prove nothing here. Only bot runs cover it.

## First read results (READ, nothing run)

- 0x1c9a8 is the game's own player-pair melee pass, one hit routine 0x1d03e per pair. It runs only with an empty enemy pool (ffee80 = 0x14) and not on stage 14, so live aliens stop it. The driver must call 0x1d03e itself.
- It does token damage: 1, or 0 at health 0. Setting the attacker's tag byte +8 for the call sends `damage_apply` down its enemy path. Whether that table gives sensible numbers for a player's attack needs a run.
- 0x1d716 only checks the recent-attack list used by 0x1cf54. 0x1d03e uses its own one-hit id.
- 0x1d492 sets the KO state when health goes below 0. Blocking the continue is still to read.
