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

## Voice ("Berserker Barrage!", owner addition)

Pipeline, built and run (EMULATOR for playback, see Verification): `tools/wolverine/reveal_voice.py` runs MAME 0.289 on the owner's mshvsf set (`mame_voice.lua`, no sound, no video), dumps the 8 MB QSound sample ROM,
cuts one clip (bank/start/end in the ROM, 8 bit signed, 24038 Hz at rate 0x1000), resamples it to 22050 Hz, scales it to peak 120 and writes `reveal_voice.bin` (`RVV1`, u32 samples, 8 reserved, the samples).
build.py puts it on the disc as `RVVOICE.BIN` (REVEAL_VOICE or GUEST_ASSETS/reveal_voice.bin; ROM-derived, never in git; without it the reveal plays silent). At frame 3 `reveal.c` loads it with the art, copies it
to SCSP RAM at 0x70000 (stage 26's clips end near 0x55000) and plays it on SCSP slot 18 (0 to 15 are the game's channels, 16 and 17 the CD) at octave -1 (22050 Hz). It lives in the pack room only while the reveal starts
and is copied out at once; nothing stays in work RAM. A 0.55 s clip is 12.2 KB.

NOT DONE: the clip itself is not identified. `mame_voicescan.lua` sent every sound command 0 to 0x7ff through the 68000 mailbox and logged the QSound voice starts: 301 distinct samples of 0.3 to 2.5 s. They were run
through offline speech recognition (faster-whisper small.en, installed in a venv on this PC; Windows SAPI first). None came out as "Berserker Barrage" (with a prompt naming the phrase it hallucinated it into noise, so those hits
are worthless). The commands Wolverine's own moves send in a MAME run (0x120 to 0x127, 0x203 to 0x20d) are 0.1 to 0.3 s grunts. Either the shout is not a separate QSound clip in MSHvSF (its hyper combo name may be text only),
or it is played in pieces. For playback testing a stand-in clip (20:b400:e7ff, command 0x91, 0.55 s; recognised once as "Barrage!" with the prompt, so not evidence) was cut. The owner should pick the clip by ear:
`REVEAL_VOICE_CLIP=BANK:START:END reveal_voice.py cut WORKDIR out.bin`, the candidates are in the scan evidence (E:\AvP\learning\lane-wolverine-reveal\scan1\w, one WAV per clip named bank_start_end).
