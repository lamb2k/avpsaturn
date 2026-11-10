# Stage select background, 2026-11-10 (lane stage-menu-bg; EMULATOR Yaba VideoCore 1, own copy port 9727, cache off; hardware UNRUN)

Branch `lane/stage-menu-bg-20261110` on avp/integration 4c3dc09. Evidence `E:\AvP\learning\lane-stage-menu` (ev\bg*, logs bg1.log, fit_bg.log, unittest_bg.log, host_bg.log, disc\bg1.cue/.iso/.elf).

## What drew the grey

Not a panel in the picture: STAGE SELECT ran in `sat_home_mode = 2` (the held game, picture black, layers off). `sub()` fills every text cell with glyph 1. In modes 3 and 4 the menu layer draws glyph 1 as a clear cell (sat_gfx.c draw_home: `ch == 1 ? snap.home >= 3 ? 0 : panel`), but in mode 2 it draws the pause menu's translucent panel (cell 14, colour calculation at ratio 11 of 31 against the black picture). That is the flat grey: pixel (13,13,13) over the picture area in the 3a capture, pure black in the letterbox bars above and below (`ev\bgbefore_01.png`). So the screen was black picture plus the pause panel, not a layer left up.

## What it does now

Stage select runs in mode 4 like the other option screens (clear cells, 1 px halo, logo "vs." sprite off) with the title picture behind it.

The held game's own picture cannot be used (it is the character select's), and the title's VDP state is gone by then (the live select has redrawn it), so the title's snapshot is kept. All of it is cold code (cart, with home_cold.c); the resident part is one call:
- kernel.c, the held-game branch of the vblank: `held = sat_home_snap_frame(); if (!held) sat_gfx_snapshot_begin(); ...hand-off...; if (!held) sat_gfx_snapshot_layers();`. This is the only high RAM change besides making sat_gfx.c's `snap` global (no cost) and moving the `home` field into the header words of the Snapshot (no cost).
- home_cold.c `sat_home_snap_frame()`: state in `sat_home_snap[2]` (a `.data` section in the cart, so no work RAM): [1] 1 saves the whole snapshot (22,752 B, the size comes from `nm -S` of the gfx object, build.py passes -DSAT_SNAP_BYTES) to the cart's pack room at 0x02760000 (the front file's tile pack ends at 0x0274b000, measured over the 287 round files of 3a: 1,011,712 bytes from 0x02654000; cold code starts at 0x027e0000), 2 puts it back; [0] holds: it returns 1 after setting header words 9 (menu mode) and 6 (sprites 0), and the vblank then hands the slave the snapshot it already has instead of taking one, so layers, palettes, scroll and row table stay as the title left them.
- The title menu asks for the save when STAGE SELECT MODE is picked and waits until the held vblank has done it (the save is of the snapshot before that vblank's); `stage_select()` asks for the restore and the hold on entry and clears the hold before it returns. After that the next normal snapshot sees different sums and redraws everything.
- In Yaba the cart code is recompiled on every entry (known), so held vblanks cost more there; hardware cost is one call and two byte tests per held vblank.
- The stage load and the held game are as before: nothing writes game RAM or the CPS video RAM; game RAM ff8000-ff9fff md5 was identical at the select and 3 s later (`ev\bgarea1.log`, `bgend.log`), stage 1-1 loaded and ran (`bgarea1_sheet.png`: NOW LOADING, then the street, no title remnants), ENDING still plays through to the title (`bgend.log`, 327 s, no fatal).
- Rows: the logo covers rows 0 to 18, so the stage rows moved to 20 and 22 (the game's own start lines at rows 19 and down are hidden in the title modes); footer stays at row 25. The second row now exists for every entry: AREA m OF k for ordinary areas (1-1 shows "AREA 1 OF 2"), BOSS name, BONUS SPECIAL STAGE; ENDING shows its line on row 22.

Captures (paused, `ev\bg_before_after.png`; before = avp_integration_3a, after = bg1): entries 1-1, 1-2, 6-2, 7-5, ENDING; `bgbefore_*.png`, `bgafter_*.png` per entry.

Readability: stage rows sit on black under the logo, no overlap; the header sits over the ALIEN letters as on OPTION MODE and the other option screens (halo, same legibility as those).

## Memory, gates

| | hw_free | lw_free | cart_free |
| --- | --- | --- | --- |
| avp/integration 4c3dc09 (link only: scratch work dir, killed after the placement line, `base2.log`) | 436 | 60 | 7908 |
| this branch (bg1.log) | 164 | 60 | 7808 |

+272 B high work RAM (the save/restore loops and the freeze tests in sat_gfx.c, three words of state in home.c), 0 low, -100 cart. hw_free 164 is thin; the loops could go to cold code if the next lane needs the room.

- Build rc 0 (3,521 s: the pack is rebuilt for the new head, `round files rebuilt: stage-pack inputs or layout changed`).
- fit.py D11 (POSE_KEYS=0, KEEP_ROUND_FILES=1; assets copied to scratch): 76 of 76 stage files and the front file pass, gate True, fail [] (`fit_bg.log`).
- check_round_pages 0 of 323, check_screen_keys 0 of 323, check_caption_keys 323 files short 0.
- WSL unittest: 131 run, 30 errors, 1 skipped, same error set as 4c3dc09 (`unittest_bgbase.log`).
- tests/home_stage_menu_test.c (updated for the AREA row) and home_lives_test.c pass.
- HOST goldens clean, missed IRQ 0: r1s 15618, full 317908, c1 272171, c2 369051, c3 333669, 2p 329918 (`host_bg.log`).
- Input: PostMessage to my own window only; Yaba launched SW_SHOWMINNOACTIVE (no focus) from this run on.

Note for the reveal lane: its SAVE_SCRATCH is 0x02754000 (menu and ending); this lane's stash is 0x02760000 to about 0x02763c00, in the title and stage select only, so they do not overlap in use.
