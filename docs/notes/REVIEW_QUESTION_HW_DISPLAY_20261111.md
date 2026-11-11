# Question for the super agent: why does disc F5 show vertical stripes, a doubled HUD and only ~24 pictures/s on a real Saturn?

## Situation (2026-11-11)
- **Disc:** `avp_3h_A_fix5`, branch lane/hwboot-20261110 at b7b463f (standard SGL-style startup: slInitSystem TV_352x224, SMPC clock change, A-bus restore). Staged at E:\AvP\package-integration\fenrir\avp_3h_A_fix5.
- **Console:** Japanese Saturn, region-unlocked, Fenrir ODE, 4 MB RAM cart, CRT. First AvP disc ever to boot on hardware. It reaches the title, character select and gameplay.
- **Port:** Capcom's AvP CPS2 lifted to the Saturn. Master SH-2 runs the game, slave builds VDP1 sprites, VDP2 draws the scroll layers. Code in saturn/rt (boot.c, kernel.c) and saturn/gfx/sat_gfx.c.

## What the owner sees on the console (photos in C:\Users\lambd\.claude-account2\uploads\c57b0534-34fb-4355-bed4-ba0840eb8369\: a98ec4dc, 1ecb9e05, c8dc9bde, b677c290, a6bb1bfa)
1. **Vertical column stripes** over every VDP2 layer (title logos, character select, in-game background). Columns of tiles drop out. VDP1 sprites (characters, aliens) are clean. Menu text is clean on the title.
2. **Doubled HUD:** the scroll-1 text layer (name, health bar, score, PRESS START) is drawn twice in one picture, once at the top and again about two-thirds down. Also seen on character select.
3. **Speed (console readings, SAT_FPS_HUD):** `PIC 25 GAME 60 MISS 39 SKIP 35 HELD 25` and `PIC 23 GAME 60 MISS 38 SKIP 38 HELD 11`. Game logic holds 60, but only 23-25 new pictures/s reach the screen. Yaba showed 58-60. Characters move fast and inputs are responsive.
4. **A crash screen** (the boot.c exception display: colour band plus black/white 16-row stripes) appeared at some point; undecoded. The hardware-boot lane is decoding it.
5. Sound: none, but the owner found it was their audio cables. Ignore.

## What emulators show
- Strict Ymir (real JP BIOS) reproduces the **doubled HUD and the skips**, but **not the vertical stripes**.
- Yaba does not show any of these.

## Hypotheses to confirm or kill
- **Stripes:** VDP2 VRAM cycle patterns (CYCA0/A1/B0/B1) or RAMCTL bank split give a layer's pattern-name or character reads no slot in 352-wide mode, so columns are missed on hardware. Emulators don't enforce this. Also consider colour RAM mode, reduction, VDP1 framebuffer erase/swap, or a mid-display VRAM write.
- **Doubled HUD:** scroll-1 plane or map size, vertical scroll value, line or vertical cell scroll tables, screen height or interlace mismatch.
- **Speed:** whether wrong cycle patterns or CPU VRAM waits also stall the master or slave, versus real VDP1 draw time, cart or low-RAM cost, or clock mode.

## Questions
1. Which of the VDP2 register writes in our startup and in sat_gfx.c differ from the SGL defaults for TV_352x224 with our layer set (see docs/notes/AVP_HWBOOT_REGDIFF_20261111.md)? Give the exact CYCA0/A1/B0/B1 and RAMCTL values to use for each layer and VRAM bank assignment, and show which layer is short of slots.
2. What exactly doubles the scroll-1 layer, and why does Ymir show it but not the stripes?
3. Can the stripe cause be proven off-hardware (a cycle-pattern checker, Ymir settings, a different emulator), or only on the Saturn? What single diagnostic disc view would settle it?
4. Given PIC 23-25 on the console, what are the ranked causes of the picture rate and what extra console readings are needed? Cover VDP2 VRAM contention, VDP1 draw time, slave build, cart reads, tile uploads. Label modelled figures separately from console measurements.
5. What is the minimal standard-practice fix (no tactical one-off patches), and what should the owner look at on the next disc?

## Constraints
Read-only: no builds, pushes, SD card access or focus-stealing. No ROM or BIOS data off the PC. Measure first; label emulated versus console figures.

Write the answer to E:\AvP\learning\hwboot-review\SUPER_ANSWER_HW_DISPLAY.md.
