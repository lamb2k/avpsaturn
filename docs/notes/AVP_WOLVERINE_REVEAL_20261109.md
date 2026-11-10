# Wolverine post-credits reveal and unlock (lane wolverine-reveal, 2026-11-09)

Branch `lane/wolverine-reveal-20261109`, off `lane/wolverine-merge-20261109`. Tiers: art and tools HOST, runtime EMULATOR (Yaba, HLE BIOS, VideoCore 1), nothing on hardware.
Owner decisions: the artist's three frames play after the ending in place of the GAME OVER card, in Wolverine's in-play colours (blue costume to his sprite reds, yellows kept; first asked
as red/yellow, then briefly the 80s brown/gold of revision 3, then back to the sprite reds on 11-09). Unlock model: first locked until the reveal (11-09), then (11-10) a toggle in OPTION MODE from the first power-on that the reveal also turns on by itself the first time.
Owner addition: the "Berserker Barrage!" voice from MSHvSF plays with frame 3.

## What the port saved before this lane: nothing

`kernel.c` keeps the arcade's 128 byte settings block (`save_block`, the EEPROM image) and the home options in work RAM only, and the ranking is the arcade's own table in game RAM:
nothing is written to backup RAM ("backup saves held for the owner", docs/STATUS.md). There was no existing save to extend. This lane adds the first one, one 64 byte file `AVPSAT_SAVE`
in the Saturn's internal backup RAM through the BIOS backup library (`boot.c unlock_io`), holding the unlock flag, with room kept for later settings and ranking (below).

## Recolour (tools/wolverine/reveal_recolour.py)

The artist's frames share an 80 colour palette (indices 0 to 80, 0 transparent, 1 black). The costume's blue ramp, found by following the blue pixels from the two entries that only the costume uses
(50 #445599 and 53 #5566aa, 1000 pixels in six patches of frame 3):

| step | his sprite red | entries (palette index) |
| --- | --- | --- |
| light | #ee3300 | 53 #5566aa, 54 #667799, 55 #7788aa, 57 #8899bb, 58 #aabbdd |
| mid | #cc0000 | 50 #445599, 51 #556677, 52 #556688, 49 #555577 |
| dark | #880000 | 47 #445577, 46 #445566, 45 #444466 |
| darkest | #550000 | 43 #333344, 42 #222233 |

50 and 53 are costume only and change colour in place. Every other entry is shared with the scenery (the pipes, walls, the aliens' shading, the floor; frames 1 and 2 use them too), so only the
costume's pixels of them are recoloured (1892 pixels, a chain of at most 4 blue-ramp pixels from 50 or 53) and move to 50 or 53 or to two new entries (81 #880000, 82 #550000). The yellows,
skin, belt, aliens and scenery keep their entries; frames 1 and 2 are copied unchanged. Eighteen tiles that the split pushed past 15 colours lost 115 pixels of scenery blue/navy next to the figure
to the nearest colour in the tile (one ramp step; list in `recolour.json`). Every 16 x 16 tile still has at most 15 opaque colours. Pictures: evidence `before_after_crop.png`.
Originals are never written; the recoloured PNGs are `art/wolverine-reveal/*_red.png`, the disc file `reveal.bin` is made from them (`reveal_pack.py`) and reproduces byte for byte (tests).

## Display (saturn/rt/reveal.c, run from the cart tail with the other cold code)

The reveal replaces the GAME OVER card, and the card is the game's own: stage word 0x26 with ff8005 = 8 (EMULATOR: ff8005 is 10 through the ending, 8 for the card's 432 vblanks, 14 once the
stage word is 0 and the ranking is up; the arcade log has the same 426 frame card). The game is not held: its own card timer is the reveal's hold, so the front end follows at the arcade's moment.
Losing the game (the continue countdown and GAME OVER at stage 0x24) also shows ff8005 = 8 but never stage 0x26: no reveal, no unlock (checked on Yaba).

- Trigger: `sat_reveal_poll`, once per game walk. It loads `REVEAL.BIN` (168 KB: palette and the three picture bands) and `RVVOICE.BIN` with the loader (`boot.c load_file`, through
  `kernel.c sat_reveal_call`, which stops the game and the slave as a round load does), into the cart's pack room one megabyte into the stage's pack (0x02754000; stage 26's pack is under 600 KB).
- Picture: VDP2 NBG0 as a 512 x 256 8 bit bitmap, frame 1 in bank A1, 2 in B0, 3 in B1, palette in CRAM 0; the picture band is copied in (frames 1 and 2 rows 48 to 175, frame 3 rows 24 to 199),
  the rest of each bank is clear, so the back screen (set to black) shows outside the picture rows. SAT_GFX_FIT 1 zoom (1 + 23/256, 384 pixels on 352) or the 16 pixel crop of 0/2, screen adjust honoured.
  Sprites are off (priority 0) and the slave draws nothing: `sat_vblank` hands it no picture while the takeover flag (LOADER_DIAG[5]) is set.
- No permanent RAM: the art is copied into VRAM and the voice into SCSP RAM and the pack room is free again; resident cost is `sat_reveal_takeover`, `sat_reveal_call` and one hook in the vblank,
  see the gates. At the end `sat_gfx_init` gives the chips back (every cache empty, each tile reloads), then the front end loads as it always does.
- Timing: frame 1 for 90 vblanks, frame 2 for 90, frame 3 until the card ends (about 250): 1.5 s, 1.5 s and about 4.2 s of the card's 7.2 s. Proposed values; constants `T_FRAME2`, `T_FRAME3` in reveal.c.
  The disc read happens at the start of the card with the game stopped (about 1 s on a real drive; not measured: Yaba reads at once).

## Toggle and automatic turn-on (owner 11-10: "make him a toggle in the options since people don't look there, but if they don't toggle it unlocks by itself when they beat the game")

This replaces the first design (locked until the reveal). There is no LOCKED state any more.
- OPTION MODE > GAME OPTION > BONUS CHARACTERS (OFF / WOLVERINE / MEGA MAN / BOTH) works from the first power-on. A change is written to backup RAM at once (`guests.c sat_guest_save`).
- The first time the reveal plays (the stage 0x26 card; losing never plays it) Wolverine is switched on if he is off, and that is saved with the "reveal has played" flag in the same write
  (`sat_guest_reveal_done`). Later endings play the reveal again but leave the setting alone: the player's own choice in OPTION MODE always wins and is what is saved. A player who turned him off
  and beats the game again keeps him off.
- Boot (`boot.c unlock_io`, after the loads): the record is read into the loader's flags word (`LOADER_API[3]`: bit 31 read, bit 0 reveal has played, bit 8 a setting is saved, bits 9 and 10 that setting).
  A saved setting replaces the build default at the first use (`guests.c saved_apply`). No record, a bad sum or a record from before the setting existed means the build default (`SAT_GUEST_DEFAULT`).
  A build with `-DSAT_GUEST_DEFAULT=1` starts with him on until the player saves otherwise.
- Record (`saturn/rt/unlock_save.h`, 64 bytes, AVPS v1 as before): `AVPS`, version 1, header length, flags (bit 0 reveal has played; the first reveal lane's "unlocked" bit, same meaning for such a record),
  byte 7 = saved BONUS CHARACTERS setting (bit 7 = saved, bits 0 and 1 the guest bits; 0 in every record written before, so it reads "none saved"), bytes 8 to 61 free and kept as found, 16 bit sum.
  Writing is read-modify-write: only the flags byte, byte 7, the version (raised to 1) and the sum change; a record with no setting byte, a bad sum or a foreign file is handled as the host test
  `tests/unlock_save_test.c` shows (old record keeps its bytes, a failed sum brings no stale setting back, a foreign file starts from zero). Only our own file is touched; the device is formatted only when unformatted.
- Switches: `-DSAT_WOLVERINE_UNLOCKED` is retired (nothing is locked; it no longer appears in the code). `-DSAT_UNLOCK_DEBUG` stays and still means something for QA: it adds OPTION MODE > GAME OPTION > REVEAL SEEN
  (NO / YES) that writes the flag at once, so a tester can clear it and let the next ending switch Wolverine on again. `REVEAL=0` builds without the reveal and the save altogether.
- Flag-off identity (`REVEAL=0`, no `-DSAT_WV_REVEAL`): every part of the reveal is behind that define, boot.c included. Compiling the same sources at the base (7f26a1f) and now with the same command
  lines gives byte-identical objects for kernel, guests, home_cold, home, sat_gfx and boot (md5, evidence idc/run.sh).

## Voice: his round-entrance line (owner 11-10: "lets use his intro as the reveal sound")

The reveal plays Wolverine's MSHvSF round-entrance line, "Let's go, bub." (arcade sound command 0x207), with frame 3. It replaces the "Berserker Barrage!" idea (no such clip was found; see below).
- Source: the wv-sounds lane renders the line through the real Z80 driver and QSound in MAME (`tools/wolverine/wv_sound.py`, its branch lane/wv-sounds-20261109), after sending 0x484 to load his voice set. The same
  command number plays different samples depending on the voice set loaded, and the whole 0.9 s line spans more than one QSound clip: the first one alone (0x207 with no voice set loaded, bank 0x28, 0.21 s)
  is not it. That is also why my first search for a "Berserker Barrage" clip (commands sent without the voice set) found nothing.
- `tools/wolverine/reveal_voice.py intro SOUND_ASSETS OUT.bin` takes the INTRO clip from that lane's asset directory (wv_sound.json and wv_sound.bin: 8 bit signed mono PCM, 11025 Hz, level in the SCSP total level)
  and writes `RVVOICE.BIN`: 'RVV1', u32 samples, u8 total level, u8 octave nibble, 6 reserved, the samples. Build with `REVEAL_VOICE=OUT.bin` (build.py copies it to the disc; ROM-derived, never in git; without it the
  reveal is silent). Result: command 0x207, 9,924 samples, 0.900 s, tl 42, **9,940 bytes** on the disc.
- Playback (reveal.c): with frame 3 the clip, loaded with the art into the pack room and copied out, sits in SCSP RAM at 0x70000 (stage 26's clips end near 0x55000) and plays on slot 18 (0 to 15 are the game's
  channels, 16 and 17 the CD) with its own level and octave (0xe = 11025 Hz). Nothing stays in work RAM.
- Earlier work (kept in the history): the "Berserker Barrage!" search. `mame_voicescan.lua` sent every command 0 to 0x7ff, 301 distinct clips were run through offline speech recognition and none said it; the
  tools remain (`reveal_voice.py cut`, `REVEAL_VOICE_CLIP`).

## Native Wolverine merge and gates (11-10)

Merged `lane/wv-native-gfx-20261109` (7f26a1f) into the lane (486c982; only docs/STATUS.md conflicted, both sections kept). Build `w11`: commit e40987d, D11, recipe flags
`-DSAT_HOME -DSAT_DUEL_MENU -DSAT_GUESTS -DSAT_GUEST_DEFAULT=0 -DSAT_WV_JUMP=1 -DSAT_GUEST_FAST_LIST=1 -DSAT_GUEST_NAMES_LAZY=1 -DSAT_GUEST_PAL_KEEP=1 -DSAT_WV_NATIVE_GFX` (default OFF so a first power-on shows the
toggle at OFF and the first ending switches him on), stand-in voice, no SAT_UNLOCK_DEBUG. rc 0, 1586 s.
- Memory: hw_free 808, lw_free 48, cart_free 7292. The reveal costs 1425 B of cold code (reveal.o 1196, guests.c +213, home_cold.c +16) and 264 B of work RAM that the lane's kernel hooks need; work-RAM is the
  resident part, nothing of the art or voice stays. The cold code crosses ONE 4 KB step of the cart tail (cold code without it ends 525 B under the step): cold1 starts at 0x27e1000 instead of 0x27e2000,
  cart_pack_room 1,626,112 instead of 1,630,208, that is 32 tiles (4096 B) of pack room.
- fit.py on a copy of D11: gate True, 76 of 76, 0 own dropped, 0 missing; stage24_ma wolverine 16,473 tiles vs Schaefer 16,457, drops 2,866 vs 2,910 (44 tiles of margin).
- check_screen_keys: every stage file passes (the guest front file `front_wv` is a front file and exempt; the tool needs the file names from round_stats.json on a guest build). check_caption_keys: 287 files, 0 short.
  check_round_pages (tool from the stage-sprites lane, not in this base): PASS over the 210 base files (its keep list in rounds.json has no guest files).
- unittest (WSL): 111 ran, 30 errors (the known private-dependency load errors), 1 skipped; all test_wolverine_* OK. Host test unlock_save_test: pass.
- Flag-off identity: kernel, guests, home_cold, home, sat_gfx and boot objects compile byte-identical to 7f26a1f without -DSAT_WV_REVEAL (md5, evidence idc/run.sh).

## Yaba (EMULATOR, own copy, port 9726) so far
Options toggle verified on w11 with a fresh backup file: BONUS CHARACTERS shows OFF at first power-on; right gives WOLVERINE and the loader's flags word went 0x80000000 to 0x80000300 (saved setting 1) at once;
left back to OFF gave 0x80000100 (saved setting 0). Captures: look/e2e/e1_option_off.png, e1_option_wolverine.png. The ending run (assist: Queen set to 1 hit point, health held, Start to continue) was started three
times and had not reached the card when paused; Yaba froze mid-run each time (see report).

## Update 11-10 (late): native 035d44c, restart check, scope

- Build with native 035d44c merged (local WIP branch `wip/reveal-with-native-035d44c`, not pushed: lanes no longer merge each other, the integration lane does): rc 0 (2343 s), hw_free 808, lw_free 80, cart_free 4396;
  the native lane's smaller cold code means the reveal no longer crosses the 4 KB step there (cart_pack_room 1,630,208, unchanged). fit.py D11: gate True, 76/76, 0 own dropped, 0 missing, stage24_ma 16,504 tiles vs 16,488.
  check_screen_keys all stage files pass (front_wv is exempt), check_caption_keys 287 files 0 short, check_round_pages PASS (210 base files). unittest 111 ran, 30 known errors, 1 skipped; flag-off objects identical to 035d44c.
- Queen death with NO memory writes (Yaba, cache off, assist = Start to continue only): no fatal; the game cleared and ran the ending. The coordinator's fatal 0xf4 at f_b2672 (a one-instruction
  tile-address routine, code intact in the cart) came after pokes of her health block: +0x40 health, +0x42 the displayed health that chases +0x40, +0x44 a HUD value (0x138 at the start, 0x108 after hits, 0x138 again
  near the end: it is not a constant maximum), so writing 1 to all three changes what the death path reads. The player's three words are all 0x65 (101) at full health; a write of 0x65 is the true full value.
- End to end on Yaba (EMULATOR, cache off, fresh backup file, Warrior, Wolverine OFF, stage warp 0x24 and the fight with no pokes): at the card ff8005 = 8 the reveal loaded, Wolverine went on and was saved (flags word
  0x80000000 to 0x80000301, `sat_guest_sel` 0 to 1), frame 1 at vblank 29,271, frame 2 at 29,356 (+85), frame 3 at 29,444 (+88), then the front end at 29,692 with the ranking scroll and the title. SCSP slot 18 at frame 3:
  key on, PCM8, start 0x70000, 9,924 samples (stand-in clip of that build), total level 0x2a, octave 0xe. Captures (paused): look/e2e/e4_1_reveal_frame1_m8.png, frame2, frame3, e4_1_front_end.png.
  Restart: same backup file, flags 0x80000301, sel 1; OPTION MODE shows WOLVERINE; turned OFF it saved (0x80000101) and the next power-on stayed OFF (player's choice wins); ON again (0x80000301).
  The select screen after the restart loaded the front file with his art (round file 286, front_wv); a clean capture of it is still to take (the integration lane's STAGE SELECT > ENDING run covers the rest).
- The "stray figure" on the Queen's body in the P.Warrior run is the game's own roast food pickup (platter with tomatoes), not Wolverine: look/e2e/bleed_a_zoom.png. That investigation belongs to the native lane.
- Scope now: reveal frames and display, the save and auto-on, the Options toggle, the voice. The branch is pushed without the native merge; merge avp/integration (with native and stage-menu) when it has them.

## Update 11-10 (evening): reveal only when not seen and Wolverine OFF, uncut voice, merged with avp/integration

Owner: "The shared ending is fine for now, just the reveal shouldn't occur if he's already unlocked."
- Rule (`reveal.c sat_reveal_poll`): at the stage 0x26 card the reveal plays only if the reveal-seen flag (bit 0 of the loader flags word) is clear AND Wolverine is currently OFF (`sat_guest_sel & 1` clear).
  Otherwise nothing is written and the stock GAME OVER card follows. The seen flag is set whenever the reveal plays (with Wolverine switched on, one write); a skipped ending leaves the flag as found.
  `-DSAT_UNLOCK_DEBUG`'s REVEAL SEEN row still clears it.
- Voice: the sounds lane's uncut "Let's go, bub." (`wv_sound.py reveal`, RVV1, 22,050 Hz 8 bit mono, 28,202 samples = 1.279 s, file 28,218 bytes) is the build-time `RVVOICE.BIN` source (`REVEAL_VOICE=...reveal_voice_intro.bin`).
  That file stores octave nibble 0, so reveal.c reads 0 as 0xf (22,050 Hz); total level 0. SCSP RAM 0x70000 to 0x76e2a: clear of stage 26's clips (end 0x6c420) and the 512 KB limit.
- Yaba checks (EMULATOR, own copy port 9726, UseSh2Cache=false, SoundCore 1, Volume 100, build w11 = avp/integration d13fd4b merged + this lane, STAGE SELECT MODE > ENDING, Warrior, fresh backup file each unless noted):
  - (a) first ending, Wolverine OFF, flags 0x80000000: card reached at vblank 8468, reveal frame 1 at 8494, frame 2 at 8579 (+85), frame 3 at 8672 (+93), front end at 8910; flags 0x80000301, `sat_guest_sel` 1.
    At frame 3 slot 18: key on, PCM8, start 0x70000, LEA 0x6e2a (28,202), no loop, TL 0, octave 0xf; SCSP RAM 0x70000 for 28,202 bytes equals the file's samples byte for byte; frame 3 stays up about 240 vblanks, longer than the 1.28 s clip.
  - (b) second ending on the same backup file (flags 0x80000301): no reveal (frames seen none), the stock GAME OVER card shows (look/e2e/sb_card_after_120.png), then the front end; flags stay 0x80000301.
  - (c) fresh backup file, Wolverine turned ON in OPTION MODE first (flags 0x80000300, saved setting): no reveal, stock card, flag UNCHANGED (0x80000300, bit 0 still clear), so a later ending with him turned OFF would still play the reveal once.
  Captures: look/e2e/sa_reveal_frame1..3.png, sa_front_end.png, sb_card_after_120.png, sc_card_after_120.png, sc_options_on.png.
