# Wolverine talk box face and story box wording, 2026-11-10 (lane wv-talkbox)

Branch `lane/wv-talkbox-20261109`. Evidence tiers: HOST (unit tests, builds), EMULATOR (Yaba soft core, own copy, port 9723). No hardware.
The arcade's own dialogue is ROM data, so this note lists Wolverine's new wording (ours) and the ROM offset of every record it replaces;
the old lines are printed locally by `python tools/wolverine/dialog.py table <rom>` and stay out of git.

## 1. Talk box face (always on with the guest, build time)

The story box's speaker picture is 5x3 scroll 1 cells (40x24 px) at codes `0xfbd-c + 16r`, palette bank 0x13, drawn x-flipped; both halves of every
code block hold the same cell, so the column parity does not matter. Bank 0x13 is the palette `hud_art.py` already rewrites for the HUD portrait,
which is why the box showed Schaefer's face in Wolverine's colours. The 2P HUD portrait draws the same cells unflipped.

`tools/wolverine/hud_art.py` now builds a `talk_face` piece: the head and shoulders of the approved select portrait (crop x 20, y 8, 88 x 50.9)
shrunk to 38x22 by area average, each pixel to the nearest of the portrait's own 15 colours, inside the arcade's 1 px white frame (pen 1, which
every arcade face has in its tiles). Stored mirrored in both halves of each block, stage files only. A `wolverine_talk_face_40x24.png` in the art
directory (same 15 colours) replaces the crop if the artist wants to paint it. The approved portrait faces left; mirroring is one constant if
the owner wants him to face the text like Schaefer. Memory: none (same payload slots; the ELF is byte-identical).

## 2. Story box wording, SAT_WV_DIALOG (default off)

Owner 2026-11-10: "modify the dialog slightly to be more Wolverine without changing the story".

How the arcade stores it: the program ROM holds story box text as 16 bit font cell codes. A record is 64 words (0x80 bytes): `0xffff`, four zero
words, the display time, a speaker word, line 1 (28 cells), a zero word, line 2 (28 cells). The speaker word picks the face: 0 Warrior,
0x100 Schaefer's slot, 0x200 Hunter, 0x300 Linn; the soldiers' calls use 0x900 and up. Every story beat has one record per character and the
game shows the one for the player's character, so Schaefer's slot, which Wolverine takes, is every record with speaker word 0x100, plus the
soldier's call that names him. Two English blocks exist (0xbec02 to 0xc1382 and 0xcf842 to 0xd7fc2); the other languages sit in ROM stretches
the Saturn image gives to tiles, so the English text is the only text the Saturn game has.

How it is switched: `tools/wolverine/dialog.py` (from `saturn/rt/build.py` when `-DSAT_WV_DIALOG=1`) checks every record against a truncated
hash of its original bytes (`dialog_hashes.py`, not reversible) and writes `gen/guest_dialog.inc`: his lines and the originals, packed one byte
a character. `saturn/rt/guest_dialog.h` (plain C, host tested) writes his lines over the records while his stage files are the loaded ones and
the originals back otherwise, from `sat_guest_loaded()` in `guests.c`, the same hook as his palettes. Only differing bytes are written; with
the flag off nothing is compiled and the image is unchanged; with it on and the guest off no byte of the ROM image changes
(`tests/test_wolverine_dialog.py`, HOST). No ROM data is in git: the wording is `tools/wolverine/dialog_lines.py`, the originals come from
the user's ROM at build time.

The stage clear banner's name: the ROM has Schaefer's name three times in the banner script at 0x11a65e: a 20-byte field of a four name table
(0x11a75f), a single centred name message (0x11a7d3), and the "DATA OF FILE" listing (0x11a837, attract profile pages, left alone because it
sits beside Dutch's picture). The first two read WOLVERINE while his files are loaded.

Memory (flag on): data 3,985 bytes in the cart tail with `guests.c`, which comes out of the sprite pack room (`cart_pack_room`), not hw_free or
lw_free; code about 200 bytes in the same place. See section 4 for the build's own numbers.

## 3. Where the wording appears

Stage numbers are the arcade's stage words, from the MAME cutscene sheet (E:\AvP\learning\cutscene-sheet) where the line was seen there;
"by sequence" where the record sits between seen lines. The owner's table (old line, new line, capture) is in the lane report; the modelled
sheets with every old and new line in the game's own font are `E:\AvP\learning\lane-wv-talkbox\work\model_sheet_{0,1,2}.png` (MODELLED, not captures).

Names that were checked and need nothing in text: the continue screen (CONTINUE? and the countdown, no names), the ending subtitles and the
staff roll (no character names), the "BEST 50 HUNTERS" table (icon done by hud_art.py). Art, not text, still showing Schaefer or the four
characters: the continue screen's per-character picture (the arcade draws the character's weapon; Schaefer's smartgun arm for his slot), the
intro cast panel, the ending and staff roll group panels, and the attract profile pages. These need new art; none is a direct swap.
