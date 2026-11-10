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
| hyper QCF QCF + LP+MP (gauge poked full) | 0x140 (+27), 0x13c (effect object, +42), 0x20e (+43), then every slash 0x124/0x125/0x120/0x121/0x126 + shout 0x20a/0x20c + hurt voice and 0x643 on the target | 0x140 metallic ring (claws out), 0x20e "Let's go." |
| hyper QCF QCF + HP+HK | 0x21c (+27) | ASR "RUCKY" (second hyper's shout) |
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
| 0 | SELECT | 0x21a | none | 6 | 8,987 | 0.81 | kept in the assets and the wav folder, in no pack: the select screen plays INTRO (owner 11-10) |
| 1 | INTRO | 0x207 | front end and stages | 6 | 14,101 | 1.28 | the character select (automatic: Schaefer's select shout 0x264, only in the front end file, plays this instead, owner 11-10) and his entrance at stage start (call from the native lane's entrance record); also the post-credits reveal voice (owner 11-10) |
| 2 | CLAW_L | 0x124 | stages | 5 | 4,908 | 0.45 | first active record of a light attack (chain stage 1 and 2) |
| 3 | CLAW_M | 0x125 | stages | 5 | 6,503 | 0.59 | jump attack; each Berserker slash |
| 4 | CLAW_H | 0x126 | stages | 5 | 7,078 | 0.64 | the chain finisher (02000e) |
| 5 | ATK_A | 0x20a | stages | 6 | 2,767 | 0.25 | shout on a light swing |
| 6 | ATK_B | 0x20b | stages | 6 | 4,578 | 0.41 | shout, second chain hit |
| 7 | ATK_D | 0x20d | stages | 6 | 4,755 | 0.43 | shout, medium swing |
| 8 | ATK_H | 0x209 | stages | 6 | 8,973 | 0.81 | shout on the finisher |
| 9 | HURT_A | 0x203 | stages | 6 | 5,458 | 0.49 | hurt voice: automatic through Schaefer's 0x213 |
| 10 | HURT_B | 0x202 | stages | 6 | 2,633 | 0.24 | second hurt voice, available |
| 11 | KO | 0x200 | stages | 7 | 13,570 | 1.23 | KO scream: automatic through Schaefer's 0x214 |
| 12 | TORNADO | 0x204 | stages | 7 | 9,695 | 0.88 | special start: automatic through Schaefer's 0x21c |
| 13 | BERSERKER | 0x206 | stages | 7 | 14,453 | 1.31 | **owner-confirmed 11-10 as his Berserker Barrage voice**, full length, once at the start of the move: `wv_on_berserker_start` (WV_SFX_BERSERKER) |
| 14 | CLAW_HIT_L | 0x10e | stages | 5 | 2,113 | 0.19 | `wv_on_berserker_connect`; a landed hit of a light attack |
| 15 | CLAW_HIT_H | 0x243 | stages | 5 | 4,222 | 0.38 | a landed hit of the finisher |
| 16 | BERSERKER_GRUNT | 0x20c | stages | 6 | 2,873 | 0.26 | `wv_on_berserker_connect` |

Total 117,677 bytes in the assets (stage files 108,680 including INTRO; front end file 14,101: INTRO only; SELECT's 8,987 are in no pack). Every clip runs to the arcade's own end (cut where the render last passes 40 of 32767, as the AvP clips; a 3 ms fade at the end): an earlier build capped INTRO, ATK_H and KO at 0.9 / 0.5 / 0.9 s and cut words (owner 11-10); there is no length cap now.

## 4. How the game plays them

**Automatic (no change to wolverine.c): the stage pack remap.** The game's own code sends Schaefer's sound numbers; the Wolverine stage files get a sound pack in which those rows hold his clip
(`tools/wolverine/wv_audio.py REMAP`, same command, priority and channel): 0x213 (the voice the player routine sends when a hit lands on him, f_1a96e, table 0x1b7b4) to HURT_A, 0x214 (his KO scream, f_1b16e,
table 0x1b7c4) to KO, 0x264 (stage 0 only, the select shout) to INTRO ("Let's go, bub." when he is picked, owner 11-10), 0x21c (the special's voice, sent with 0x97 by f_24f04) to TORNADO, 0x97 to CLAW_H, 0x250 (the weapon sound, table 0x1b814) to CLAW_M.
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

## 5. Budget (final build, native base 7f26a1f: owner recipe + `-DSAT_WV_NATIVE_GFX -DSAT_WV_SOUND -DSAT_WV_SOUND_HOOKS`, assets D11 copy)

Full-length clips (owner 11-10: "the saturn voices seem cut off"; the first build capped INTRO at 0.9 s, ATK_H at 0.5 s, KO at 0.9 s and cut the tail of every clip below 250 of 32767; now every clip runs to the arcade's own end, 40 of 32767 as the AvP clips, 3 ms fade):

| clip | before | now | extra bytes | arcade |
| --- | --- | --- | --- | --- |
| INTRO | 0.900 s 9,923 | 1.279 s 14,101 | +4,178 | 1.250 s |
| ATK_H | 0.500 s 5,513 | 0.814 s 8,973 | +3,460 | 0.804 s |
| KO | 0.900 s 9,923 | 1.231 s 13,570 | +3,647 | 1.229 s |
| CLAW_M | 0.515 s | 0.590 s 6,503 | +821 | 0.583 s |
| CLAW_H | 0.574 s | 0.642 s 7,078 | +751 | 0.630 s |
| the other twelve (SELECT included) | | | +841 together (HURT_A +202, HURT_B +171, BERSERKER_GRUNT +147, CLAW_L +129, BERSERKER +114, the rest under 31 each) | |
| total | | | **+13,698** (stage clips 94,989 to 108,680; all assets 103,980 to 117,677) | |

Tail of the last 30 ms (RMS of 32767): INTRO 43, KO 95, CLAW_M 39, CLAW_H 48, ATK_H 186, BERSERKER 132; CLAW_HIT_L 966 and TORNADO 156 are sounds the arcade itself cuts (3 ms fade only). Still no voice is cut by a cap.

- **Select screen = INTRO** (owner 11-10): the front end file's row for Schaefer's select shout (0x264) plays INTRO ("Let's go, bub.", 14,101 bytes) instead of SELECT, which stays in the assets and wav folder but is in no pack. Front end pack 344,118 to 344,312 bytes (+194: INTRO against Schaefer's 13,924), 171,784 bytes of room left. INTRO is in the stage files too (the round entrance), where it is part of the 108,680.
- **Program memory** (build.py report, no NO-GO) on the merged head: hw_free 1,080, lw_free 52, cart_free 4,436. My own cost, measured on the earlier base: **0 bytes of low work RAM** and 184 bytes of cart (about 140 `wv_sfx`, the rest the test hook bodies). Without `-DSAT_WV_SOUND` nothing is compiled or changed.
- **Sound RAM** (SCSP, 504 KB of clip room per stage file): a stage pack gains 108,680 bytes of Wolverine clips; Schaefer's clips that the remaps replace leave the pack (0x213 3.1 KB, 0x214 12.9 KB, 0x21c 14.4 KB, 0x97 9.0 KB, 0x250 7.2 KB = 46 KB); the other ~63 KB comes from clips the rounds' routes never played, then the fewest used
  (`wv_audio.py`, same ranking as rounds_config.py). Over the 76 Wolverine stage files (`fitstat.py`): 572 never-used rows dropped (4.07 MB in all, 54 KB a file), and **route plays lost: 19 in the 19 solo files, 181 / 477 / 574 in the pair variants (masks 10 / 6 / 3), 1,251 in all, 50 files touched**
  (the uncut set costs 443 more plays than the capped one: 808 before). **Stage 26 fits easily**: its Wolverine pack is 444,924 bytes, room left 71,172, nothing dropped, clips end at SCSP 0x6c420; the reveal's voice at 0x70000 (28,202 bytes, 22,050 Hz) ends at 0x76f4a, inside the 512 KB with 14 KB between.
  The tight files are the pair variants of the other stages (stages 24, 10, 20, 1c: room left 2 to 9 KB after dropping 15 to 25 rows).
  **If those plays matter, what I would trade, in this order, without cutting a word:** (1) store the long voices (INTRO, KO, BERSERKER, TORNADO, ATK_H, 5 clips, 60 KB) at 8 kHz instead of 11,025 Hz: 27 percent less, about 16 KB a stage, needs a per-clip octave in `sat_audio.c start_sfx`
  (everything above 4 kHz is lost on those clips; I have not listened to the difference); (2) drop the sound rows a stage does not use (ATK_A and BERSERKER_GRUNT, 5.6 KB); 16 bit would double everything. I found no ADPCM mode in the SCSP slot setup the player uses (PCM8 and PCM16 only), so 8-bit against ADPCM is not an option on this player; a lower rate is the trade.
- **Disc**: every stage and front file keeps its number and its audio field is capped at the same SCSP_ROOM, so the disc grows by nothing but sector rounding; no new file or track (sat.iso 391,321,600 bytes on the new base, against 385,658,880 before the base moved). The sound assets (`wv_sound.bin` 117,677 bytes, `wv_sound.json`) are a build input, not a disc file.

## 6. Reveal lane

The owner chose INTRO as the reveal voice. `wv_sound.py reveal OUT.bin RENDER_DIR [NAME]` writes the reveal lane's `RVVOICE.BIN` (`RVV1`, u32 samples, 8 reserved, 8 bit signed mono at 22,050 Hz, peak 120, 4 ms fades, even length) from the same MAME render, uncut: 28,202 samples, 1.279 s, 28,218 bytes (`E:\AvP\learning\lane-wv-sounds\wav
eveal_voice_intro.bin`; the reveal copies it to SCSP RAM 0x70000 and plays it on slot 18 at octave -1 = 22,050 Hz, as its note describes).
Cut parameters, for anyone who rebuilds from the arcade render of command 0x207 (`mame_wvrender.lua`, command list `207 110`): onset minus 16 samples to the last sample above 40 of 32767 (mono mix of the 48 kHz stereo), lowered with a 63 tap windowed sinc at 0.45 of the target Nyquist, no length cap, mean removed, scaled to peak 120. The uncut 11,025 Hz clip is `wav\saturn_11025_INTRO.wav` (the same path as before, now full length); the arcade's own is `wav\mame_original_INTRO_mshvsf_207.wav`.

## 7. Verification (second round, build of 09:30 on the merged native head)

- **HOST**: `tests/test_wolverine_sound.py` 7 tests (list agreement, the 0x2c0 range is unused by the game, pack rebuild keeps arcade rows and priorities, remaps, front/stage/both/none split, drop by rank never drops a Wolverine row, `wv_sfx` mailbox bytes with a stub player compiled by gcc). WSL unittest after WSL was restarted: 113 run, the same 30 private-dependency errors, 0 failures. `fit.py` on a copy of D11 (this build): gate true, 76 of 76 files, 0 Wolverine-own tiles dropped (stage24_ma 2,872 Schaefer against 2,834 Wolverine, the documented D11 numbers).
- **EMULATOR** (own Yaba copy, port 9722, ini checked before launch: SoundCore 1, Volume 100, UseSh2Cache false; the SCSP dump `AVP_SCSP_RAW` is independent of the sound core): run `t9` in `E:\AvP\learning\lane-wv-sounds\yaba`.
  - **Select screen** (`select_check.py t9 207`): after the pick the line plays **once, in full**: one match with the arcade render (envelope correlation 0.967, onset 0.10 s, 1.29 s long across the two words), level -6 dB in the mono mean of a panned sound, last 30 ms RMS 48 (render 134), then silence for 10 s through the load and nothing matching again when the game moves to the stage (best later match 0.47: other sounds).
  - **In game, from the hook**: his Berserker input (QCF + A, now a native action) reached `wv_on_berserker_start` and the test hook's `wv_sfx(WV_SFX_BERSERKER)` sent 0x2cd to the player, once at the start, as the BERSERKER row (`seen.json`: vblank 1607, command 0x2cd); the other Berserker tries were interrupted by hits. This is the first running-game call of `wv_sfx`.
  - Injection of every stage clip through the game's audio ring (loud fight underneath, so judged where the sound stands alone): level -0.1 to -1.3 dB, envelope correlation 0.86 to 0.99 for CLAW_M, CLAW_H, ATK_A/B/D/H, HURT_A/B, KO, BERSERKER, CLAW_HIT_H; INTRO, TORNADO, CLAW_L, CLAW_HIT_L and BERSERKER_GRUNT were buried or split by the fight in this run (INTRO is judged by the select-screen check above, which is clean). The previous run's measurements of the capped set stand for those.
- **Not done**: nobody has listened; hits of the claws (CLAW_HIT_*), swings and shouts are not called by anything yet (section 4); on hardware nothing was run.

## 8. Select-screen music, avp_integration_3e against disc 2 (owner report 11-10: "music is missing on the select character")

EMULATOR, own Yaba copy (port 9722, ini checked, SW_SHOWNOACTIVATE, below-normal priority), MCP build without SDL, so judged from the player's counters and the SCSP dump (`AVP_SCSP_RAW`, which does carry the CD music: the stage music is continuous in it), not by ear. Tools: `tools/wolverine/wv_music_check.py` (boot, title, select, pick, stage; logs every command the player receives with the vblank and the dump position), `wv_select_check.py`. Runs `m2 / n2` (disc 2 with its own build's symbols), `m3e / n3e` (3e with wd3e's symbols), `w2_24 / w3e_24`, `w2_26 / w3e_26` (stage warps) in `E:\AvP\learning\lane-wv-sounds\yaba`. Disc 3a: its build directory is gone and no sat.elf matches its iso (sha), so its counters could not be read; its cue and CD tracks are byte-identical to 2 and 3e (below).

- **What plays on the select screen** (disc 2 and 3e alike): CD-DA, not SCSP. The game sends music command 0x1a as the screen opens; the pack's music row 0x1a is (intro 0, loop track 23): the cue's track 23, file `t23_001a.raw` (the MAME render of command 0x1a), looping. A second music command, 0x5, starts track 5 (`t05_0005.raw`) when the select countdown begins (cursor moved), then 0x31 (confirm), 0x264 (Schaefer's select shout, which on 3e plays "Let's go, bub."), 0xff07 (music fade) and 0xff00 (stop) as the stage loads. Same command order on both discs.
- **No difference found.** Player counters after the pick on both: music_started 2, cd_sent 8, then 9 / 11 / 12 as the stage loads (disc 2 and 3e: the same numbers at the same points); stage 02 starts music 0x7, stage 24 starts 0x8 (3e vblank 1630, disc 2 1640), stage 26 (the ending) sends only 0xff00 on both; before the select screen no music has started on either (music_started 0 at the title). The SCSP dump of the first 9 s of the select music: RMS 781 against 783, mean spectrum correlation 0.998, 100 ms envelope correlation 0.93 (timing jitter), i.e. the same track at the same level.
- **Not the pack**: all 77 Wolverine packs of 3e (wd3e) carry music tables byte-identical to the arcade packs they came from, no sound row of mine shares a command with a music row (music commands 0x01 to 0x1f, mine 0x2c1 up), the front end pack's music rows equal r000's. Not the CD side: cue files identical (3a, 2, 3e), the CD tracks t23, t05, t07 identical by sha256. Not my INTRO-on-select change: it starts after the music is up (0x264 at the pick, SCSP slot 13; the CD music is on the external input slots 16 and 17, which no clip uses), and the previous run showed no second match of the line when the stage loads.
- So on my Yaba the select music is present on 3e exactly as on disc 2. What I could not reproduce is the owner's silence; it needs the exact moment (the first select after the title, the hover over Wolverine, or after the pick) and his Yaba settings (stock build with SDL: the CD input may be handled differently from the MCP build's). If it is real and specific to 3e, the next step is a bisect build of the same head with `-DSAT_WV_SOUND` off (about 35 minutes), played on his Yaba.
