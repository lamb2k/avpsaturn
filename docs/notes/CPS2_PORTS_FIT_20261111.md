# CPS2 384 wide on a 352 wide Saturn: what we do, what MSHvSF does (2026-11-11)

Read-only research for the owner's question. Nothing built into the game, nothing pushed, no SD card, no focus stealing.
Labels used below: **MEASURED** = taken from a log or screenshot made in this session. **SOURCE** = read from our code. **MEMORY** = general knowledge, not verified here.

## Answers first

1. **Does our game have black bars? No, not in the picture.** In strict Ymir (native framebuffer screenshots) every gameplay frame fills all 352 x 224 pixels, edge to edge. The only black areas are the ones the arcade art itself has (continue screen bands, the black field behind character select and the game over text). The console photo of the CRT (c8dc9bde) also shows the picture filling the tube with only the monitor's own thin margin.
2. **What we show:** TVMD 0x8101, i.e. HRESO 1 = 352 wide, 224 lines, no interlace. The 384 wide picture is **scaled, not cropped, on the playfield layers**: NBG0 and NBG1 take all 384 source columns and squeeze them onto 352 dots (increment 1 + 0x17/256 = 1.0898, ZMCTL 0x0101 = half-reduction mode). VDP1 sprites are scaled by 11/12. The 8x8 text layer (NBG2) is **not** scaled: it is a 16 px centre crop (44 of 48 columns), except the HUD rows in play, which drop the 4 middle columns instead so the HUD stays flush at both edges.
3. **What retail Marvel Super Heroes vs. Street Fighter (Saturn) does (MEASURED, strict Ymir, real BIOS, 4 MB cart):** 352 x 224, **no scaling at all** (ZMCTL 0, zoom 1.0 on both zoomable layers in every state seen), all four NBG layers on, 1 name read + 1 character read per layer per dot, RAMCTL 0x1300 (same bank split as ours), CPU slots left open in every bank. The picture is full frame, no bars. The HUD is re-laid out for 352 (it is not a pixel crop of the arcade HUD). MSHvSF never uses the reduction mode, so it tells us nothing about how to schedule reduction.
4. **Could we drop the reduction?** Yes. The MSHvSF register sets prove the no-reduction, 1:1, 352 wide, four-NBG layout works on retail hardware (retail disc, so known good on a console by MEMORY; this session only saw it in an emulator). It would cost 16 px of arcade picture per side (352 crop, 8.3 percent of the width) or 32 px per side (320 crop, 16.7 percent). 320 is not recommended; see the cost table.

## Recommendation

- **Run the existing crop build (SAT_GFX_FIT=2, "the crop, HUD flush", already in the tree) on the console next, same disc recipe otherwise.** It is the single most informative test: its VDP2 setup (no reduction) is the same class as MSHvSF's. If the stripes vanish, the half-reduction schedule was the cause (fix7's schedule would then be the thing to prove or drop). If stripes remain, the cause is elsewhere (active-display VRAM writes, bank/slot rules for CPU access) and reduction is not to blame.
- **Product decision after that:** my lean is the 352 crop for AvP. It removes the scaled VDP1 commands and the NBG0/1 reduction (two extra name and cell reads per layer), puts all four layers on one pixel grid so NBG2 text registers with the art (the crop audit's defects 8, 9, 12), and costs 16 px per side, which is mostly background and the corner of the HUD. Its open cost is the handful of full-width text lines that touch the edges (listed below), which need the per-screen remap list the crop audit described. This is a judgement; the scaled build keeps the full playfield width and is acceptable only if the console proves fix7's schedule stripe-free.
- Do not go to 320: MSHvSF itself does not, and AvP's HUD portraits and the character select panels start at x = 4 to 8.
- Hi-res (640/704) is not used by MSHvSF (HRESO stays 1, interlace off in every state; MEASURED). Nothing to copy there.

## 1. Our game, today (MEASURED + SOURCE)

Disc G7 (lane hwboot, branch lane/hwboot-20261110 head 32616ad, fix7 cycle patterns), run in my own strict Ymir copy, scripted pad, native F12 screenshots (704 x 448 = 352 x 224 doubled) and a log of every CPU write to VDP2/VDP1 registers. Log: `ymir_cps2\out\avp_g7_a\vdp_regs.log`, decoded in `out\regs_avp_g7_a_a_150.txt` (gameplay, stage 1).

| Item | Value | Source |
|---|---|---|
| TV mode | TVMD 0x8101: DISP on, BDCLMD 1, LSMD 0 (no interlace), VRESO 0 (224 lines), HRESO 1 (**352 wide**) | MEASURED; matches `TVMD_352_ON` in sat_gfx.c L3107 |
| Zoom | ZMCTL 0x0101 (NBG0 and NBG1 half-reduction on). Horizontal increment ZMXIN 0x0001, ZMXDN 0x1700 = 1.0898 on both. Vertical 1.0 | MEASURED; sat_gfx.c L3176-3180 |
| Source columns shown on NBG0/NBG1 | 352 x 1.0898 = **383.6 of 384** (all of them, 0.4 px lost), vertical 224 of 224 | computed from the measured increment |
| Sprites (VDP1) | scaled sprites: screen x = source x * 11/12 (`fit_x`); heights 1:1 | SOURCE sat_gfx.c L1945-1956 |
| NBG2 (scroll 1: HUD, text) | 8x8 cells, 1:1, **not scaled**. In play, non-HUD rows: source cells 2..45 = source px 16..367 (16 px lost each side). HUD rows (top 5 rows, rows 26-27 when `hud_flush`): cells 0..21 and 26..47, the middle 4 cells (32 px) dropped, nothing lost at the edges. Home menu: per-row blank-column squeeze (44 of 48) | SOURCE sat_gfx.c L1591-1597 and L1249-1260 |
| NBG3 | port's own menu/readout layer, native 44 columns | SOURCE |
| Layers on | NBG0, NBG1, NBG2, NBG3 (BGON 0x000F), no RBG | MEASURED |
| Character sizes, colours | NBG0, NBG1: 2x2 cells (16x16), 16 colours. NBG2, NBG3: 1 cell (8x8), 16 colours. PNC 0 / 0 / 0 two-word names, NBG3 one word | MEASURED |
| RAMCTL | 0x1300 (CRAM mode 1, A and B both split in two banks) | MEASURED |
| Cycle patterns (T0..T7) | A0 `2 3 1 1 6 7 F E`, A1 `0 0 4 F F 4 F E`, B0 `5 5 F F E E E E`, B1 `5 5 F F E E E E` (CYCA0 2311 67FE, CYCA1 004F F4FE, CYCB0 55FF EEEE, CYCB1 55FF EEEE) | MEASURED; equals `sat_vdp2_cfg.h` fit=1 values |
| Black bars | none in 352 x 224 gameplay frames: columns 0 and 351 are non-black in 100 percent of playfield rows; first and last 6 columns checked in 5 gameplay frames | MEASURED |

Reading it: the visible 352 columns are the full 384 arcade width, squeezed 8.3 percent horizontally, on NBG0, NBG1 and sprites. Only NBG2 is cropped, which is why text and art drift apart by up to 15 px (crop audit defect 8).

## 2. MSHvSF, Saturn disc (MEASURED)

Disc: `C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest-MSHvSF\...\Saturn\Marvel Super Heroes vs. Street Fighter.bin` (product T-1238G, Japanese). Run in my own patched strict Ymir (`ymir_cps2\run`, real JP 1.01 BIOS copy in my own profile, 4 MB DRAM cart), pad scripted from a file, native F12 screenshots, register-write log. The arcade ROM set exists at `...\Mame\mshvsf.zip` in the same folder; it was not run (existing MAME captures `art-brief-wolverine\refs\mshvsf\*_384x224.png` confirm the arcade picture is 384 x 224, as for every CPS2 game).

Reached: SEGA logo, legal text, attract loop, title, mode select, character select, VS screen, a fight (Ryu/Ken vs Sakura/Dan, READY, combo, pause menu). Logs: `out\mshvsf_{p3,q,r,s}\vdp_regs.log`, decoded in `out\regs_mshvsf_s_s_56.txt` (character select), `..._s_84.txt` (READY), `..._s_88.txt` (fight).

| Item | Value |
|---|---|
| TV mode | TVMD 0x8001 = **352 x 224**, no interlace, in every title/select/fight state. (0x8000 = 320 wide appears only in the BIOS boot phase.) No hi-res anywhere. |
| Bars / crop / scale | Native frames use all 352 x 224 (columns 0 and 351, rows 0 and 223 non-black in 100 percent of pixels on select, READY and fight). **No scaling:** ZMCTL 0 and zoom increments 1.0 in every state of four sessions (about 1.1 million register writes). Sprites are normal 16x16 VDP1 sprites (earlier Yaba measurement, `research-capcom\CAPCOM-SATURN-STRATEGIES.md` row 3, not redone here). |
| Crop or relayout? | Inference from stills (arcade 384 versus Saturn 352, side by side in `out\fight_compare_rulers.png`, `out\select_compare_rulers.png`): centre items (timer) sit 16 px left of the arcade position (arcade centre 192, Saturn 176), edge items (LEVEL text, portraits) stay flush to the screen edges, life bars are about the same length as the arcade's. That looks like a centre crop of the playfield plus a HUD re-placed for 352, not a squeeze. Moderate confidence (read off images, plus or minus 4 px). |
| Layers | All four NBG on during fights and select (BGON 0x000F), no RBG. Sizes: NBG0 8x8, NBG1 2x2 cells, NBG2 8x8, NBG3 2x2 cells in fights (NBG2 2x2, NBG3 8x8 in some scenes). All 16 colours. One-word names off (PNC 0), plane sizes vary per scene. |
| RAMCTL | 0x1300 in all play states (same as ours); 0x1000 and 0x0300 / 0x2000 in the early loading screens. |
| Zoom registers | ZMCTL 0, ZMXIN/ZMYIN 1, ZMXDN/ZMYDN 0. |
| Sprite control | SPCTL 0x1025 / 0x0025 (type 5, mixed colour mode) in play. Ours: 0x0001 (type 1). Not examined further. |
| Line scroll | SCRCTL 0x0200 in fights. Vertical cell scroll reads (`C D` slots) appear in B1 in several states. |

Cycle patterns in the steady play states (T0..T7, E = CPU, F = none, 0..3 = names NBG0..3, 4..7 = characters NBG0..3, C/D = vertical cell scroll NBG0/1):

| Scene | A0 | A1 | B0 | B1 |
|---|---|---|---|---|
| Character select, READY, fight (state in s_56, s_84, s_88) | `6 7 4 5 F F F E` | `6 7 4 5 F F F E` | `6 7 4 5 F F F E` | `C D 0 1 2 3 F E` |
| Many other play states | `4 5 6 7 F E E E` | `4 5 6 7 F E E E` | `4 5 6 7 F E E E` or `4 5 6 7 F F F E` | `0 1 2 3 6 7 F E` |
| Title / early scenes | `4 4 4 4 4 4 4 4` | `F ...` | `4 4 4 4 4 4 4 4` | `F ...` (one layer, RAMCTL 0x1000) |

What this shows: Capcom gives **every bank all four layers' character reads in T0..T3** (so a layer's cells can sit in any bank), puts **all four pattern-name reads in one bank (B1)**, and leaves the **CPU slots wide open: T5 to T7 on A0/A1/B0, T7 on B1** (T7 only in the first row). Nothing is scheduled twice, because nothing is reduced. Caveat: these are the registers the game programs, read in an emulator that does not enforce slot shortage. They are the retail game's own values, so they work on a console (MEMORY: retail disc), but this session did not see them on hardware. The game changes the cycle registers one write at a time during scene changes (transient mixed states appear in the log), then settles.

## 3. Other CPS2 Saturn discs

Not present on this PC. Searched `C:\Game Dev`, `E:\` and `D:\` for cue/mds/ccd/chd, `*x-men*`, `*street fighter*`, `*vampire*`, `*darkstalker*`, `*alpha*`: only MSHvSF has a Saturn image. Arcade zips of other CPS2 titles exist (sfa3.zip, xmen.zip in open-arcade folders), which are not Saturn data. Absent: X-Men vs. Street Fighter, Street Fighter Alpha 2 / Zero 2, Alpha 3 / Zero 3, Vampire Savior, X-Men: Children of the Atom.

MEMORY, unverified: Capcom's Saturn fighters are native re-implementations on VDP1 sprites and VDP2 NBG layers rather than scaled arcade captures, X-Men vs. Street Fighter and MSHvSF need the 4 MB RAM cart. I do not remember their exact resolution or cycle tables and have not checked them. Treat only the MSHvSF numbers above as evidence.

## 4. Comparison

| | Our game (G7) | MSHvSF Saturn | Others |
|---|---|---|---|
| Resolution | 352 x 224 (TVMD 8101) | 352 x 224 (TVMD 8001) | not available |
| Black bars | none in picture | none | not available |
| 384 source handling | scale 384 to 352 on NBG0/1 and VDP1 sprites; NBG2 crop 16 px or HUD middle-drop | 1:1, no scaling; HUD re-laid for 352 | not available |
| Zoom registers | ZMCTL 0x0101, increment 1.0898 | ZMCTL 0, increment 1.0 | |
| Layers | NBG0 2x2, NBG1 2x2, NBG2 8x8, NBG3 8x8, 16 colours | NBG0..3 all on, mixed 8x8 / 2x2, 16 colours | |
| RAMCTL | 0x1300 | 0x1300 (play), other values in loading | |
| Cycle pattern | A0 `2311 67FE`, A1 `004F F4FE`, B0/B1 `55FF EEEE` (2 names for NBG0/1) | A0/A1/B0 `6745 FFFE`, B1 `CD01 23FE` (or `4567 FEEE`, `0123 67FE`) | |
| Names in one bank? | spread (A0, A1) | all in B1 | |
| CPU slots | A0 T7, A1 T7, B0/B1 T4..T7 | T5..T7 (or T7) in A0/A1/B0, T7 in B1 | |

## 5. What a crop would cost AvP (arcade stills, MEASURED by pixel read and by eye)

Source: arcade MAME captures `crop-audit\arc\*.png` (384 x 224), overlay `out\avp_arcade_edge_strips.png` (red = outer 16 px each side = 352 crop, yellow = next 16 px = 320 crop). Positions are read off the stills, plus or minus 4 px.

- **Playfield:** in gameplay frames the outer 16 px strips are 99 to 100 percent filled with picture (background and sprites), so a crop loses real picture, but only 4.2 percent of the width per side. Enemies enter from the edges; with a crop they appear 16 px later in view. No HUD sits in the playfield.
- **1P HUD (top left):** "1P" tag x 0..12, portrait x 4..24, name text "P-Warrior" starts x 26, health bar ends about x 172. The 352 crop cuts the tag and the left 12 px of the portrait; the 320 crop cuts the whole portrait and the name's first letter. Today's `hud_flush` map already keeps these (HUD rows are placed flush at the edges).
- **2P HUD / right side:** score and bar of the right player end near x 380; the 2P "PRESS START" runs to x 375. A 352 crop loses the last 12 px of the bar and the last letters ("STAR").
- **Boss portrait and bottom bar (rows 25 to 27):** start at x 0..8; split by the current row limits (audit defect 5), fixed by flush mapping.
- **Full-width screens:** character select panels start x 8 and end x 375 (352 crop clips both borders and edge text; 320 crop loses panel frames and the left portrait); the continue line "CONTINUE AND GET 1UP! CAN START WITH 2PLAYERS!" spans the full 48 columns (loses "CO" and "S!", audit defect 1); ranking RANK column starts x 12 and ROUND column ends x 380; title "CREDITS:9" ends x 375. These are the per-screen remaps the audit called an open-ended list (about 6 screens).
- **Screens that need nothing:** game over (content x 64..319), round title (x 136..375), title (x 35..375 except the CREDITS line), story box, story captions in the middle.
- **Scaled build's own costs, for comparison:** 8.3 percent horizontal squash of every character; NBG2 text out of register with scaled art by up to 15 px (defects 8, 9); VDP1 scaled-sprite setup; two extra VDP2 reads per reduced layer; and it is the layout whose stripes we are chasing.

| Option | Picture lost | Registration | VDP2 reads | Verdict |
|---|---|---|---|---|
| Scale 384 to 352 (today) | none (0.4 px) | NBG2 off by up to 15 px | 2 names + 2 chars on NBG0/1 | keep only if console proves a stripe-free schedule |
| Crop 352 (FIT=2) | 16 px per side (8.3 percent total) | exact, all layers 1:1 | 1 + 1 per layer, MSHvSF class | **lean**, needs the edge-text remap list |
| Crop 320 | 32 px per side (16.7 percent total) | exact | same | no: loses HUD portraits and panels, MSHvSF does not use it |

## Capture validity: positive controls (added after the coordinator's warning about earlier MSHvSF VDP2 claims)

Earlier repo captures of the MSHvSF VDP2 block read as zeros and a watchpoint attempt failed its controls, so nothing earlier is used for VDP2 here. This session's method is different: a patched strict Ymir that logs every SH-2 **write** to VDP2 (0x25F80000..0x11F) and VDP1 registers, replayed into a register image. It did not fail:

| Control (same logger, same decoder) | Known words | Logged |
|---|---|---|
| Jo/SGL reference disc, `slInitSystem(TV_352x224)` (`lane-hwboot\sgl_ref\sglref352`) | TVMD 0x8101, RAMCTL 0x1327 (REGDIFF doc) | TVMD 8101, RAMCTL 1327, 305,238 writes (`out\ctl_sgl352`) |
| Brooklyn Bangout rc.47 | TVMD 0x8110, RAMCTL 0x1327 (REGDIFF doc) | TVMD 8110, RAMCTL 1327, 347,052 writes (`out\ctl_brooklyn`) |
| Our G7 disc | `sat_vdp2_cfg.h` fit=1 words: ZMCTL 0101, CYCA0 2311 67FE, CYCA1 004F F4FE, CYCB0/B1 55FF EEEE, RAMCTL 1300 | identical values logged |
| Independent check of MSHvSF's TVMD | Ymir's own native screenshot size | 704 x 448 = 352 x 224 doubled, matching the logged HRESO 1 / 224 lines |

So the MSHvSF VDP2 values in section 2 (TVMD, RAMCTL, CYCA0/A1/B0/B1, ZMCTL, ZMXIN/ZMXDN/ZMYIN/ZMYDN, CHCTL, BGON, PNC, PLSZ, MP, SCRCTL, SPCTL) are **obtained and trusted** as the values the CPU wrote, in an emulator. **Not obtainable here:** hardware behaviour, DMA-written VDP2 registers (the logger sees CPU writes only; none were expected), VDP1 command contents (not captured; the "normal 16x16 sprites, CMDPMOD 0x0880" fact is the earlier Yaba measurement the coordinator cites, not redone), and what a console shows. No "measured rule" attribution in `tools/select_rp4_interval.py` was used; the old AvP prescale-offline design is an AvP workaround, not an MSHvSF finding.

## Measured versus remembered

- **Measured here:** every register value, bar check and screenshot in sections 1 and 2; the edge-fill numbers in section 5; the absence of other Saturn discs.
- **Read from code, not re-measured:** scroll 1 column mapping, 11/12 sprite table, FIT definitions.
- **From earlier work, not redone:** MSHvSF draws normal sprites (Yaba, workspace doc); crop audit defect list.
- **Remembered/unverified:** anything about other CPS2 Saturn ports, and that retail discs are known good on a console.
- **Not tested on hardware:** the claim that fix7's reduction schedule is stripe-free, the claim that the crop build is stripe-free, and all console pixel-aspect effects.

## Files

- Tool: `E:\AvP\learning\hwboot-review\ymir_cps2\` (`run\ymir-sdl3.exe` my patched copy logging VDP1/VDP2 CPU writes to `run\vdp_regs.log`; `build\sh2.cpp` the patch; `drv.py` the driver; `vdp2dec.py` decoder; `uniq.py`; `prof\` own profile). The lane's `ymir_strict`, `ymir_prof` and logs were not touched.
- Evidence (local only, game screenshots): `out\mshvsf_s\native_*.png`, `out\avp_g7_a\native_*.png`, `out\cps2_fit_compare_native.png`, `out\fight_compare_rulers.png`, `out\select_compare_rulers.png`, `out\avp_arcade_edge_strips.png`, per-run `vdp_regs.log` and `marks.txt`, decoded `out\regs_*.txt`.
- Disc copies used by Ymir (`disc\mshvsf.bin`, `disc\avp_G7.iso`) were deleted afterwards (the cue files stay). Ymir resolves a cue's FILE name against the cue's folder, which is why the copies were needed.
