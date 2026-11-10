# Wolverine's own sounds from Marvel Super Heroes vs. Street Fighter (lane wv-sounds, 2026-11-09)

Branch `lane/wv-sounds-20261109`, worktree from `lane/wv-native-gfx-20261109` b368017. Owner brief: "lets get the sounds": claw swing, claw hit, Berserker Barrage voice and its hits, select / entrance voice, KO voice, and the
"Berserker Barrage" voice for the post-credits reveal. Before this lane he played Schaefer's sounds and Berserker was silent.

Evidence labels: **MAME** = MAME 0.289 on the owner's mshvsf set (tools/run_mshvsf_mame.py of the MSHvSF repo), sound off, `-wavwrite` for the audio; **ROM** = decoded from the QSound sample ROM / Z80 driver
tables; **EMULATOR** = Yaba (own copy, port 9722, `AVP_SCSP_RAW` dump of the SCSP output); **HOST** = unit tests / build tools. Nothing here is hardware. No ROM bytes, samples or renders are in git: everything below
is generated at build time from the user's local files (`tools/wolverine/wv_sound.py`, like `gen_c.py`); evidence lives in `E:\AvP\learning\lane-wv-sounds`.

## 1. How MSHvSF makes a sound, and how a move finds its sound (MAME)

CPS2 sound is a Z80 driver and QSound. The 68000 writes a 16 byte entry to the mailbox at 0x618001.. (command high, command low, parameter, pan mode, pan, span, rates; same layout as AvP's: Z80 0xc000..),
and the Z80 turns the command number into QSound voice starts (bank, address, pitch, envelope). Facts found on the way (`tools/wolverine/mame_wvsound.lua`):

- The sender is a vblank ring at 0xff2be0..0xff2fff (16 byte entries, enqueue at 0xabd96). At the enqueue a6 is the *owner*: 0xff3800 player 1's point character, 0xff3c00 player 2's, 0xff4000 / 0xff4400 the partners, other
  values effect objects. This gives clean attribution of every command to a move.
- The Z80 uses `command mod 0x400` (583 of 826 commands from 0x38d to 0x8ff play the sample of command minus 0x400): player 2 adds 0x400 to the numbers a left player sends.
- A command number renders the same sample whatever character is loaded (checked: command 0x124 is bank 0x6f, 0xb270 to 0xcb94 in a fresh boot, after the VS screen's 0x484 and in a real fight).
  The ranges are per character where it matters: Wolverine's own shouts and effects are 0x200..0x20e (+ 0x21a select, 0x21c), the shared swing/impact set is 0x120..0x13f (his claws use 0x124..0x126), Ryu uses 0x2a2..0x2aa.
  Wolverine-only = used by player 1 as Wolverine and never by player 1 as Ryu (same scripted input, `ryu_far` run).
- The audio of each command is rendered through the real driver (`tools/wolverine/mame_wvrender.lua`: after saturn/audio/render_mame.lua; the 68000 handshake is blocked after boot, this script sends the
  command to the Z80 mailbox, waits 110 frames, sends the stop control), so a clip is what the arcade plays, envelope and pitch included. A catalogue of every command 0x001..0x8ff is in `E:\AvP\learning\lane-wv-sounds\cat`, cat2.

## 2. What each Wolverine move sends (MAME, player 1 = Wolverine, player 2 pinned out of reach and held at full health, clean runs `far`, `far2`; player 2 pinned in reach `near`, `near2`)

| Move (input) | Sound commands sent by him, frames after the press | What they are (ASR with faster-whisper small.en on the render, voicing/centroid measure of the render) |
| --- | --- | --- |
| LP | 0x124 (+1) | noise sweep, centroid 3.2 kHz: claw swing, light |
| MP | 0x125 (+1), 0x20d (+3) | swing, medium + shout "ha" |
| HP | 0x126 (+1), 0x209 (+8) | swing, heavy + shout "HAAAAA" |
| LK / MK / HK | 0x120 / 0x121 / 0x122 (+1), MK 0x20a (+3), HK 0x20b (+5) | shared low kick thumps (Ryu's punches use 0x120..0x122 too), + shouts "huh", "yeah" |
| crouching / jumping versions | the same numbers | |
| DP + P (Tornado Claw) | 0x204 (+11) | "Tornado Claw!" (ASR: "Tornado Claw!") |
| QCF + P | 0x206 (+10), then 0x125 per slash, player 2's hurt voices and 0x642 hits | 1.3 s shout (ASR: "PIZZA KIPARAGE!", i.e. "Berserker Barrage!") then the slash flurry |
| QCB + K in the air | 0x205 | "Drill Claw!" |
| hyper QCF QCF + P+P (gauge poked full) | 0x140 (+27), 0x13c (effect object, +42), 0x20e (+43), then every slash 0x124/0x125/0x120/0x121/0x126 + shout 0x20a/0x20c + hurt voice and 0x643 on the target | 0x140 metallic ring (claws out), 0x20e "Let's go." |
| round entrance | 0x207 (frame 1771) | "Let's go, bub." |
| picked on the select screen | 0x21a | "HAAAAA!" (Ryu: 0x2ba) |
| he is hit | 0x50c (generic impact), 0x202 / 0x203 voices, 0x130 / 0x12c thump | |
| he is knocked out | 0x88 x2 (announcer), 0x130, then 0x200 (+7..+34) | 1.2 s scream: KO voice |
| a claw lands on the enemy | no Wolverine-specific command: the *victim* sends 0x642 / 0x643 / 0x50e by hit strength (same for Ryu) and its own hurt voice | 0x10e, 0x242, 0x243 are the generic slash/hit impacts |

Berserker Barrage (the port's gun slot, QCF + A) is the QCF + P special: the voice 0x206 at the start, then per contact a swing (0x125) and a shout (0x20c) with the generic hit (0x643).
The shout is a real recording in the sample ROM: the previous reveal lane's scan failed because it sent commands through a fresh driver and ran speech recognition with a prompt
(hallucinated), and the move list it tried did not include QCF + P. **Candidates for the reveal are in `E:\AvP\learning\lane-wv-sounds\wav\berserker_candidates`; 0x206 is the one the arcade plays for the move.**
No sound was heard by a person in this lane: roles come from timing in the move runs, the ASR text and voicing measures above. The owner picks by ear.

## 3. The sound set (`tools/wolverine/wv_sound.py` SOUNDS, `saturn/guests/wolverine/wv_sound.h`)

Clips are MAME's audio of the command, cut onset to last sound (tail threshold 250 of 32767), mixed to mono, lowered to 11025 Hz with the same filter as `saturn/audio/build_pack.py` and stored as 8 bit signed with the
level in the SCSP total level `tl` exactly as the AvP clips, so they are as loud against the game's own clips as MAME played them. IDs are AvP sound commands 0x2c0 + id (the driver's table has null entries 0x276..0x2ff).

| id | name | MSHvSF cmd | file | priority | clip bytes | seconds | where it belongs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | SELECT | 0x21a | front end | 6 | 8,980 | 0.81 | automatic: Schaefer's select shout (0x264, only in the front end file) plays this instead |
| 1 | INTRO | 0x207 | stages | 6 | 9,923 | 0.90 | his entrance at stage start (call from the native lane's entrance record) |
| 2 | CLAW_L | 0x124 | stages | 5 | 4,779 | 0.43 | first active record of a light attack (chain stage 1 and 2) |
| 3 | CLAW_M | 0x125 | stages | 5 | 5,682 | 0.52 | jump attack; each Berserker slash |
| 4 | CLAW_H | 0x126 | stages | 5 | 6,327 | 0.57 | the chain finisher (02000e) |
| 5 | ATK_A | 0x20a | stages | 6 | 2,737 | 0.25 | shout on a light swing |
| 6 | ATK_B | 0x20b | stages | 6 | 4,554 | 0.41 | shout, second chain hit |
| 7 | ATK_D | 0x20d | stages | 6 | 4,749 | 0.43 | shout, medium swing |
| 8 | ATK_H | 0x209 | stages | 6 | 5,513 | 0.50 | shout on the finisher |
| 9 | HURT_A | 0x203 | stages | 6 | 5,256 | 0.48 | hurt voice: automatic through Schaefer's 0x213 |
| 10 | HURT_B | 0x202 | stages | 6 | 2,462 | 0.22 | second hurt voice, available |
| 11 | KO | 0x200 | stages | 7 | 9,923 | 0.90 | KO scream: automatic through Schaefer's 0x214 |
| 12 | TORNADO | 0x204 | stages | 7 | 9,691 | 0.88 | special start: automatic through Schaefer's 0x21c |
| 13 | BERSERKER | 0x206 | stages | 7 | 14,339 | 1.30 | `wv_on_berserker_start` |
| 14 | CLAW_HIT_L | 0x10e | stages | 5 | 2,109 | 0.19 | `wv_on_berserker_connect`; a landed hit of a light attack |
| 15 | CLAW_HIT_H | 0x243 | stages | 5 | 4,219 | 0.38 | a landed hit of the finisher |
| 16 | BERSERKER_GRUNT | 0x20c | stages | 6 | 2,726 | 0.25 | `wv_on_berserker_connect` |

Total 103,980 bytes (stage files 94,989, front end file 8,980).

## 4. How the game plays them

**Automatic (no change to wolverine.c): the stage pack remap.** The game's own code sends Schaefer's sound numbers; the Wolverine stage files get a sound pack in which those rows hold his clip
(`tools/wolverine/wv_audio.py REMAP`, same command, priority and channel): 0x213 (the voice the player routine sends when a hit lands on him, f_1a96e, table 0x1b7b4) to HURT_A, 0x214 (his KO scream, f_1b16e,
table 0x1b7c4) to KO, 0x264 (stage 0 only, the select shout) to SELECT, 0x21c (the special's voice, sent with 0x97 by f_24f04) to TORNADO, 0x97 to CLAW_H, 0x250 (the weapon sound, table 0x1b814) to CLAW_M.
Schaefer's other own sounds (0x215, 0x219, 0x21d..0x221, 0x268, 0x218, 0x21a, 0x61: roles not identified, mostly 1 to 7 plays in the whole route) stay as they were.

**Explicit: `wv_sfx(id)`** (`saturn/guests/wolverine/wv_sound.c`, built with `-DSAT_WV_SOUND`): sends the command through the same mailbox the game's sender fills (interrupts masked for the 16 byte write, caller's mask restored),
so the stock player applies its channel and priority rules; no state, **0 bytes of low work RAM**, about 140 bytes of cart code. `wv_sfx_pan(id, pan)` for a pan on the game's own 0..0x20 scale.
`-DSAT_WV_SOUND_HOOKS` adds `wv_sound_hooks.c`: test-only bodies of `wv_on_berserker_start/connect/end` (BERSERKER, CLAW_HIT_L + BERSERKER_GRUNT); the features lane owns the real ones, never build both.

**Calls for the other lanes** (the frame records' +12..15 event bytes are move-progress triggers read by the state routines, not sound triggers: Schaefer's own attacks have no per-record sound at all, so the call has to come
from native code):

| Where | Call |
| --- | --- |
| `wv_on_berserker_start(i)` (features lane) | `wv_sfx(WV_SFX_BERSERKER)` |
| `wv_on_berserker_connect(i, damage)` | `wv_sfx(WV_SFX_CLAW_HIT_L)`; every other contact also `wv_sfx(WV_SFX_BERSERKER_GRUNT)` and `wv_sfx(WV_SFX_CLAW_M)`; at most 3 sounds a frame |
| tick the native lane sees a record whose attack index (+9) becomes non-zero for the first time in a move (the same place `+0x90` hit hold is set) | LP: `WV_SFX_CLAW_L`; second LP: `WV_SFX_CLAW_L` + `WV_SFX_ATK_B`; HP finisher: `WV_SFX_CLAW_H` + `WV_SFX_ATK_H`; jump attack: `WV_SFX_CLAW_M` + `WV_SFX_ATK_D` (MSHvSF: light swing has no shout, medium and heavy do) |
| landed hit (the collision answer d0 = 1 that wolverine.c already reads) | `WV_SFX_CLAW_HIT_L` (light), `WV_SFX_CLAW_HIT_H` (finisher) |
| entrance (native lane's T0 entrance set) | `WV_SFX_INTRO` |

## 5. Budget

(filled in section 6 with the build numbers)

## 6. Verification

(see below)
