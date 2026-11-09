# Wolverine post-credits reveal and unlock (lane wolverine-reveal, 2026-11-09)

Branch `lane/wolverine-reveal-20261109`, off `lane/wolverine-merge-20261109`. Tiers: art and tools HOST, runtime EMULATOR (Yaba, HLE BIOS, VideoCore 1), nothing on hardware.
Owner decisions: the artist's three frames play after the ending in place of the GAME OVER card, in Wolverine's in-play colours (blue costume to his sprite reds, yellows kept; first asked
as red/yellow, then briefly the 80s brown/gold of revision 3, then back to the sprite reds on 11-09), and playing it unlocks him (locked until the player beats the game once).
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

## Unlock

- Flag: bit 0 of the loader's flags word (`LOADER_API[3]`, bit 31 = read). `boot.c` reads the record once at power-on (after the loads: the BIOS backup library hangs the next GFS call when it runs before them on Yaba's HLE BIOS).
  The record is "locked" for anything unreadable (no backup RAM, wrong magic, bad checksum, version 0).
- Record (`saturn/rt/unlock_save.h`, 64 bytes): `AVPS`, version 1, header length, flags, reserved, bytes 8 to 61 free (kept as found on every rewrite), 16 bit sum. Writing is read-modify-write: only the flags byte,
  the version (raised to 1) and the sum change, so a record from an older layout (version 0, no flags byte) reads locked and loses nothing; a foreign file under the same name starts from zero.
  Only our own file is touched; the device is formatted only when the library reports it unformatted.
- Locked: `sat_guest_sel` bit 0 is cleared at the first use (`guests.c sat_guest_file`), so the select screen is Schaefer's; OPTION MODE > GAME OPTION > BONUS CHARACTERS shows "WOLVERINE LOCKED" for OFF and skips
  the locked values when cycling.
- After the reveal has started, the flag is set (in RAM first, then written to backup RAM), the setting takes its build default (`sat_guest_unlocked`), and from then on the setting works as before.
  A build with `-DSAT_GUEST_DEFAULT=1` therefore means "Wolverine on once unlocked" (it starts on at every power-on once the flag is saved, and turns on at the unlock in the session that earned it).
- `-DSAT_WOLVERINE_UNLOCKED`: tester and QA builds start unlocked (nothing is read or written for the lock). `-DSAT_UNLOCK_DEBUG`: OPTION MODE > GAME OPTION gets a WOLVERINE row, LOCKED or UNLOCKED, that writes the flag
  and the record at once (clear and set). A build without the art (`REVEAL=0`) is never locked.

## Voice

See the end of this note for the extraction and the result.
