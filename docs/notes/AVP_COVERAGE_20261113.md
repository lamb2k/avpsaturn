# Coverage lane, 2026-11-13: what was tested in emulators and what was fixed

Branch `lane/coverage-20261113` on `lane/quitcard-20261113` a978d300 (fix7p6). Evidence `E:\AvP\learning\lane-coverage` (runs\, mame\runs\, REPORT-c34.md). Labels: EMULATED = my own Ymir copy (`ymir\run\cov-sdl3.exe`, strict copy `cov-mis.exe`), MAME = avspu 0.289 (own copy `mame\mame.exe`, scripts `mame\mame_snd.lua`, `mame_calls.lua`). Nothing here is a console measurement. No RAM pokes in any Ymir run (RAM read only); MAME reference runs poke health, stage word and boss flags (arcade reference only).

## Tools built
- `cov.py` / `croute.sh`: frame-exact route driver (pad file per port: port 1 `AVP_PAD`, port 2 `AVP_PAD2`), RAM-read waits, audio capture (`AVP_AUDIO`: raw SCSP output, 44.1 kHz s16 stereo, CD audio included), `AUDPOLL=1` sampler of `sat_audio_stats` (every request and what the library did with it), `AUDRING=1` (the game's own sound ring).
- Ymir patches (copy only): second pad, SCSP output dump, CD block command and CDDA sector trace, EXTS level trace.
- MAME `mame_snd.lua`: logs every 68000 write into the QSound mailbox and decodes commands as `sat_audio.c` does (handshake write of 0 at 0x61801f latches the mailbox); scene automation (coin, start, bot, KO, continue, stage warp, clear flags).
- Pitfalls: a Lua frame notifier or tap must be kept in a global or MAME garbage collects it; `-video none` needs `-seconds_to_run`; the write tap offset is the absolute address.

## Sound (item 6 and the owner's two additions)
### No music at character select: root cause and fix
The game does request the select music (command 0x05, 57 frames after the select starts, as the arcade does: MAME f=1681; Saturn ring entry seen, `runs\sel3\audring.txt`), `sat_audio` starts CD track 5 and Ymir feeds the CDDA sectors to the SCSP, but the audio is silent. The CD input's effect send (SCSP slots 16 and 17, register 0x16, `cd_level()`) is zero. `sat_audio_swap()` clears slots 0..31 registers 0..0x16 (including slots 16 and 17) on every round sound swap, and `cd_level()` only writes when the level changes. After a stage load `sat_audio_resume_music()` forgets the cached level, so it is rewritten. The first round file of a boot (the front end: story, character select) is loaded by the boot path which does not call it. So **every CD track is silent from boot until the first stage load**: story music (0x1a), character select (0x05). Ymir EXTS trace: level 7 written at vb 1249, zeroed in the same frame, 0 until the first fade (`runs\sel6`). Console: same code path, so expected the same (not measured).
Fix `SAT_CD_LEVEL_FIX` (`saturn/audio/sat_audio.c`, 16 bytes: `cd_level_now = 0xff` in the swap). **sat_audio.c is compiled with `AUDIO_CFLAGS`, not `KERNEL_CFLAGS`**: the recipe needs `AUDIO_CFLAGS=-DSAT_CD_LEVEL_FIX` and an object not reused by mtime (build.py `cc()` skips an object newer than its source). Verified on disc S3: level written back at vb 1492, select music audible (RMS 1,500 to 1,700 against 0 before, `runs\sel9`, `runs\sel6` for the before). Budgets: low RAM free 612 to 596, high RAM 56, cart 2,516.
Arcade: the select music is track 5 (80 s loop) in the CD table and loops; the Saturn command is the same; the loop is the CD repeat flag (not re-checked past 80 s).

### Music commands per scene: arcade against Saturn (no wrong tracks)
Per stage (stage select entry, game logic identical): MAME `mame\runs\sw_XX\cmds.txt` against Saturn `runs\ss_L12_NN\audpoll.txt` (`tools\stagetable.py`, `tools\satsum.py`).
| scene | arcade command sequence | Saturn | match |
|---|---|---|---|
| story | 0x1a | 0x1a | yes (silent before the fix) |
| character select | stop, 0x05 | stop, 0x05 | yes (silent before the fix) |
| 1-1 | 0x07 | 0x07 | yes |
| 1-2 boss | 0x1f, 0x0f | 0x1f, 0x0f | yes |
| 2-1 / 2-2 | 0x16 then 0x06 / 0x1f, 0x10 | same | yes |
| 3-1 | 0x15, 0x08, boss 0x0f | same | yes |
| 4-1 / 4-2 / 5-1 | 0x0a / 0x09 / 0x15, 0x08 | same | yes |
| 6-1 .. 6-5 | 0x17,0x0b / 0x1c / 0x0b / 0x06 / 0x1f,0x13 | same | yes |
| 7-1 .. 7-4 | 0x18,0x07 / 0x07 / 0x07 / 0x17,0x08 | same | yes |
| 7-5 Queen stage | 0x08, 0x18 (phase 2) | 0x08 | first part yes |
| continue countdown | stop, 0x01 loop, quiet (no tick sounds), 0x026d at game over | 0x01 | yes; 0x026d not seen in my Saturn run (the idle run reached ranking music 0x03, 0x252) |
| ENDING | 0x08, 0x18, 0x1b, then 0x03 (ranking) | 0x08, 0x18, 0x1b, 0x03 | yes |
Not compared: title and attract (the arcade attract is muted by the saved demo-sound option; the port has no attract loop), versus and Boss Rush (not in the arcade; Boss Rush reuses the five stage files above).

### Missing effects (requests the Saturn cannot play)
Counted from the arcade logs against the tables of every round file (`tools\globalmiss.py`, `unkstatic.py`; runtime confirmation in `audpoll.txt`, UNKNOWN):
| command | where | arcade uses (in my logs) | cause |
|---|---|---|---|
| 0x08e, 0x14e, 0x14f, 0x156 | story and character select, ending epilogue | 34 each | real SFX (priority 5 to 7), in no round file: never rendered into the pack. 0x14e / 0x14f are in the front end's 'uses' list. |
| 0x05b 0x064 0x067 0x07f 0x087 0x094 0x12c 0x134 | stage 3-1, 6-1, 6-5, 7-3, 7-4 (one to eight uses) | 1 to 8 | same, in no table |
| 0x04f | front end only (in 236 of 287 files) | 1 | dropped from the front end file |
| 0x056 | 7-2 (48 uses in a short window) | 48 | in 78 of 287 files, not in the 7-2 file |
| 0x9e, 0x11a, 0x200 .. 0x207, 0x252 | various | few | no entry in the arcade's own table (null): silent on the arcade too |
Fix cost: render the 12 missing commands with `saturn/audio/render_mame.lua` (MAME, one run per command), add them to `command_map.tsv` and rebuild the packs; the front end has room (its `dropped` list is empty), stage files need the budget check (SCSP RAM 524,288 bytes, 8 bit 11 kHz clips). Not done in this landing (cost: render plus pack rebuild, about half a day; owner's call).
Other known differences from the arcade (`sat_audio.c` header): a sound on several channels is one clip on the first channel it wins, so refusals by priority differ (REFUSED in the logs: 0x35, 0x100, 0x7e, 0x148 in the busy stages); music is a CD track so an SFX cannot suppress a note on its channel; pan modes 5..7 do not use their second rate; music renders have seams where no repeat was found.

### Wolverine (intended differences, owner decisions, not bugs)
His MSHvSF sounds (`AVP_WOLVERINE_SOUNDS_20261109.md`): claw swings 0x124..0x126, shouts 0x209..0x20e, Tornado Claw 0x204, Berserker Barrage voice 0x206, Drill Claw 0x205, hyper ring 0x140 and 0x20e "Let's go", entrance "Let's go, bub" 0x207, select shout 0x21a, hurt voices 0x202 / 0x203, reveal voice. The arcade AvP has no Wolverine, so there is nothing to compare.

## Other findings and fixes
- **Wolverine reveal black in Ymir: our bug** (fork F4, commit 764aa8b7, `SAT_REVEAL_UNLATCH`, default on, `-DSAT_REVEAL_NO_UNLATCH` to A/B): the display register latch rewrote the last game picture's BGON/priority every vblank and overwrote the reveal's registers (`bgon=0008 nbg0en=0` logged during the reveal). `begin()` now resets the latch. Verified: `bgon=0001`, the three art frames on screen (`runs\c15_rev4\sheet_reveal.png`), flag 0x80000000 to 0x80000301. The reveal was never silent: the voice plays from 234.2 s (audio captured, `runs\c15_rev3\reveal_audio_231_240s.wav`).
- **Alien Queen fight played to the end, no pokes** (fork F4): Predator Warrior (`runs\c15_q17d`, boss flag at emulated frame 41,498, ending, GAME OVER, ranking, title, TICK 60 PIC 60) and Wolverine (`runs\c15_q17w2`, Queen dead about frame 50,109, IP RESULTS, name entry, ship over the planet, flash, planet, credits, ranking, title). Entry 18 (1-based) is stage word 0x24. Bot: reads player and enemy pool RAM, walks to the nearest enemy and attacks, about 17 lives. The Queen spawns about 7,700 frames into the stage with health 0x138 at ff94c0+0x40; a blind bot only scratches her. Unclear: a name entry row drawn over the ending cutscenes when the score ranks (probably the arcade's own).
- **Character not loaded after a continue or join** (fork F2, commits 228e9475 and 68d7b324, `SAT_CHAR_RELOAD`): `round_check` picks the stage file once per stage word from the characters in play, so a character that continues or joins mid-stage as one the loaded file does not hold has no sprites until the next area (seen with Wolverine on both P1 continue and P2 join; HUD kept "Maj.Schaefer"). Switch watches the live player blocks and triggers the normal reload after 90 frames (about 6 s of NOW LOADING). Verified for the join. Cost on fix7p5: high RAM 72 to 56, low 500 to 416, cart 2,372 to 2,188. Not fixed: HUD name and portrait stay Schaefer's after the reload. Not run: P2 KO then continue, a 2P start with Wolverine, continues for every character.
- **Co-op works** (fork F2, fix7p5): the port 2 pad reaches the game with no change; Warrior + Linn and Warrior + Hunter play stage 1 with both HUDs whole on the crop (TICK 60 PIC 60), the 1-2 boss draws everything, a single KO gets its own CONTINUE? while the other plays, both KO give the full-screen continue, GAME OVER and two-player name entry, nothing cut. Top band says PRESS START where the arcade says JOIN IN (not chased).
- **Stage 0a (3-1) intro story drawn with holes** (fork F3, commits 8bda90a1, bfa1cf15, aada7609, `STORY_KEYS`): 40 sprite keys of the intro cut-in are in no round file (the route censuses skip the story); not caused by the crate fix or `GUEST_SYNC_KEEP`.
- **Boss Rush fights 2..5**: the premise of 659 dropped keys is the stage 0e (4-2) file, not a Boss Rush file; stage 04, 08, 0a, 1a, 24 all have `dropped_keys` 0. Fights 2, 4, 5 equal MAME; fight 3 only had the story holes above. Real Boss Rush mode with kills not reached (no pokes).
- **Screens on the FIT=2 crop**: character select, ranking (BEST 50 HUNTERS), name entry, game over: nothing cut. The 48-column continue line and story captions could not be judged on the HUD discs (the readout covers the bottom left); see REPORT-c34.md.
