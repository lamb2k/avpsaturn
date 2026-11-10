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
directory (same 15 colours) replaces the crop if the artist wants to paint it. The approved portrait faces left; owner 2026-11-10 asked for the box
face mirrored so he faces the text like Schaefer, so `TALK_FACE_MIRROR = True` (False restores the approved orientation). Memory: none (same
payload slots; the ELF is byte-identical).

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

His stage files also have to hold the tiles the new wording draws: a stage file draws a font cell blank unless its tile pack holds the key
(cell code << 1 | column parity), and the arcade's file holds only the keys its own lines used (a first build showed "They Kee  coming  b b").
`dialog.needed_keys()` lists them (176) and `guest_rounds.extend(..., s1_keys)` adds them to the 76 guest stage files; `fit.py` takes them from
`FIT_DIALOG_KEYS`. The banner's CONGRATULATIONS letters that no stage's census saw are a separate, existing gap (the text-glyphs lane).

## 4. Gates (owner recipe, assets D11; HOST and EMULATOR, no hardware)

Face only, flag off (code 9135ff4; later commits are flag-gated): build rc 0, hw_free 964, lw_free 60, cart_free 4,340, the same as avp_integration_2;
the ELF is byte-identical to the owner build; the 210 arcade round files are byte-identical and 76 of the 77 guest files differ (front_wv is the
same); fit.py on a copy of D11: 77 of 77 (76 stage files and front_wv), gate True; screen keys 0 of 285 stage files missing, caption keys 0 of 287;
WSL unittest 112 run, the 30 known private-dependency errors, 0 failures. check_round_pages is not in this base (it and round_keep.json come with
the stage-sprites lane's fuzz-page fix), so it was not run.

SAT_WV_DIALOG=1 (d35375b): build rc 0, hw_free 964, lw_free 60, cart_free 4,168. The wording and its originals are 3,985 bytes plus about 200
bytes of code in the cart tail, which moves the sprite pack's end by 4,096 bytes (`cart_pack_room` 1,630,208 to 1,626,112), not hw_free or
lw_free. fit.py with the 176 keys: 77 of 77, gate True, no Wolverine tile dropped; 889 more dropped keys in total than the flag-off build, all in
16 files that already drop keys (stages 1c, 1e, 24; the most is 133 in stage1c_ma). The arcade round files differ from the flag-off build (132 of
210: the cold code moved, and kept round files carry the build's bytes), so flag-on is its own disc, not a delta.

HOST: tests/test_wolverine_dialog.py (font round trip, record and hash checks, the C sync over a ROM buffer: off never changes a byte, on writes
exactly the wording and the name fields, off restores, twice on equals once, other speakers untouched). EMULATOR: with the flag on and BONUS
CHARACTERS off, Schaefer shows the arcade's own line and face.

Speed: the owner's rule of 2026-11-10 (UseSh2Cache=false in every Yaba copy) was applied from 08:40; the face captures and the dialog captures
through B2_off ran before it. No speed or timing number is reported.

## 3. Where the wording appears

Stage numbers are the arcade's stage words, from the MAME cutscene sheet (E:\AvP\learning\cutscene-sheet) where the line was seen there;
"by sequence" where the record sits between seen lines. The owner's table (old line, new line, capture) is in the lane report; the modelled
sheets with every old and new line in the game's own font are `E:\AvP\learning\lane-wv-talkbox\work\model_sheet_{0,1,2}.png` (MODELLED, not captures).

Names that were checked and need nothing in text: the continue screen (CONTINUE? and the countdown, no names), the ending subtitles and the
staff roll (no character names), the "BEST 50 HUNTERS" table (icon done by hud_art.py). Art, not text, still showing Schaefer or the four
characters: the continue screen's per-character picture (the arcade draws the character's weapon; Schaefer's smartgun arm for his slot), the
intro cast panel, the ending and staff roll group panels, and the attract profile pages. These need new art; none is a direct swap.

## 5. Capturing a story box in Yaba (the "missing backdrop" of 2026-11-10 was the capture, not the game)

The panel behind the face and text, the fence and barricades, and every sprite looked missing in `framebuffer_burst` captures. Same box, same
disc, three ways (plain integration `integration\w1`, the flag-off and the flag-on builds all behave alike, so the game is not at fault):
- free-running `framebuffer_screenshot`: panel, face, text, fence, barricades, sprites all present (the arcade's picture);
- the first 2 to 3 stepped frames after `pause` (`framebuffer_burst`) have no VDP1 content at all: no panel, no sprites. The panel is a sprite
  object, and the frame chain's command list is empty until the first presented frame after a resume. From the 3rd or 4th stepped frame on, panel
  and sprites are back;
- the camera also moves between the probe that finds the box and the pause (seconds of wall time at Yaba's speed), which is why the fence was
  gone in the later frames of the same box.
So story box evidence is taken as: the running-core screenshot, or a paused `framebuffer_screenshot`, or burst frames after the 4th. Burst frames 1
to 3 are never used. (`E:\AvP\learning\lane-wv-talkbox\scripts\talk_walk.py` keeps all of them: `box*_running.png`, `_paused_shot.png`, 12 stepped frames, `_run0..2.png`.)

Matched-moment evidence (lane report, E:\AvP\learning\lane-wv-talkbox\deliver): `backdrop_trio_mame_integration_flagon.png` (MAME frame 1290,
plain integration, this lane with the flag on and the mirrored face: panel, fence, barricades, sprites, face and text in all three),
`backdrop_stepped_frames_artifact.png` (stepped frame 1, frame 5 and the free-running screenshot of one plain-integration box),
`backdrop_flagoff_C_and_flagon_D_same_box.png`. The camera at the moment of a box differs run to run in every build (fence on screen in 2 of
3 plain integration runs and 1 of 3 flag-on runs; the flag-off captures had the door in view), so the fence is a camera position, not a layer.

## 6. Sprite room

The flag's cart-tail cost (4,268 bytes, one 4 KB page of the sprite pack) and its dropped keys are owned by the stage-sprites lane from
2026-11-10 (it owns the stage-file tile budget). Facts handed over: on the stage-sprites + text-glyphs line all 176 keys the wording draws are
already in FONT_KEYS (0 new keys); on the plain integration base they are 889 more dropped keys (section 4).

## 7. Intended recipe

Owner 2026-11-10: SAT_WV_DIALOG on with Wolverine is the intended default for owner discs. The code default stays 0; the integration recipe adds
`-DSAT_WV_DIALOG=1` (build.py also accepts `-DSAT_WV_DIALOG`). Wording approved by the owner 2026-11-10 ("g2g").
