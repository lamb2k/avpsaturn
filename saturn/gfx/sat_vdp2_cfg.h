/* VDP2 display set-up, the one place its numbers live (hwboot lane fix7, 2026-11-11). Included by sat_gfx.c / sat_gfx.h (kernel) and saturn/rt/boot.c (loader).
   tools/vdp2_cycle_check.py reads this file (plain #define lines, integer expressions) and checks the VRAM access cycle pattern against Sega's VDP2 manual, chapter 3 (Tables 3.2 to 3.4,
   the CPU access rule for split banks); the build fails if it does not pass. Any other write of the registers it covers (CYC*, RAMCTL, CHCTL*, PNC*, PLSZ, MP*, ZMCTL) must use these
   macros or be listed with its reason in tools/vdp2_writers_allow.txt. Layout of VRAM (512 KB, four 128 KB banks A0 0x00000, A1 0x20000, B0 0x40000, B1 0x60000, split by RAMCTL):
     A0  NBG1 maps 0x08000-0x17fff, NBG2 map 0x04000-0x07fff, NBG2 + NBG3 cells 0x18000-0x1dfff, NBG3 map + font 0x1e000-0x1ffff
     A1  NBG0 cells 0x20000-0x3bf7f, NBG0 blank character 0x3bf80-0x3bfff, NBG0 map (one 2 x 2 page plane, 16 KB) 0x3c000-0x3ffff
     B0, B1  NBG1 cells 0x40000-0x7fbff, NBG1 blank character 0x7fc00-0x7fdff   (0x7fe00-0x7ffff: the boot display's line table)
   NBG0 = scroll 2 (the playfield), NBG1 = scroll 3 (foreground), NBG2 = scroll 1 (HUD, banners), NBG3 = menus and readout. */
#ifndef SAT_VDP2_CFG_H
#define SAT_VDP2_CFG_H
#ifndef SAT_GFX_FIT
#define SAT_GFX_FIT 1   /* the same default as sat_gfx.h: 1 scales 384 pixels onto 352 with the VDP2 half-reduction mode */
#endif
#if SAT_GFX_FIT == 3
#error SAT_GFX_FIT 3 switches the zoom at run time; the access cycles would have to switch with it. Not supported since fix7.
#endif

/* ---- VRAM layout (byte addresses) ---- */
#define SAT_V2_MAP_S1 0x04000
#define SAT_V2_MAP_S3 0x08000
#define SAT_V2_MAP_S2 0x3c000
#define SAT_V2_MAP_HOME 0x1e000
#define SAT_V2_CELL_S1 0x18000
#define SAT_V2_CELL_S2 0x20000
#define SAT_V2_CELL_S3 0x40000
#define SAT_V2_S2_SLOTS 895
#define SAT_V2_S3_SLOTS 510
#define SAT_V2_CLEAR_S1 0x18000
#define SAT_V2_CLEAR_S2 0x3bf80
#define SAT_V2_CLEAR_S3 0x7fc00

/* ---- registers the cycle rules depend on ---- */
#define SAT_V2_RAMCTL 0x1300   /* VRAM-A and VRAM-B each split in two banks, CRAM mode 1, no rotation data banks */
#define SAT_V2_CHCTLA 0x0101   /* NBG0 and NBG1: 2 x 2 cell characters, 16 colours, not bitmaps */
#define SAT_V2_CHCTLB 0x0000   /* NBG2 and NBG3: 1 x 1 cell characters, 16 colours */
#define SAT_V2_PNC0 0x0000     /* two word names */
#define SAT_V2_PNC1 0x0000
#define SAT_V2_PNC2 0x0000
#define SAT_V2_PNC3 0x8063     /* one word names, supplements 3 */
#define SAT_V2_PLSZ 0x000f     /* NBG0, NBG1 planes of 2 x 2 pages; NBG2, NBG3 one page */
#define SAT_V2_MPAB0 0x3c3c    /* NBG0 planes A to D: the same 2 x 2 page plane at 0x3c000 (page units of 4 KB) */
#define SAT_V2_MPCD0 0x3c3c
#define SAT_V2_MPAB1 0x0c08    /* NBG1 planes at 0x8000, 0xc000, 0x10000, 0x14000 */
#define SAT_V2_MPCD1 0x1410
#define SAT_V2_MPAB2 0x0101    /* NBG2: one page at 0x4000 (16 KB units) */
#define SAT_V2_MPCD2 0x0101
#define SAT_V2_MPAB3 0x0f0f    /* NBG3: one page at 0x1e000 (8 KB units) */
#define SAT_V2_MPCD3 0x0f0f

#if SAT_GFX_FIT == 1
/* Half reduction on NBG0 and NBG1 (ZMCTL bit 0 and 8): Sega manual Table 3.2 asks 2 name reads for each of them, Table 3.3 two 16 colour cell reads; NBG2 and NBG3 one and one.
   Timing words, T0 to T3 in the low word and T4 to T7 in the high word, one nibble each: 0 to 3 names of NBG0..3, 4 to 7 cells of NBG0..3, e CPU, f no access.
     A0  2 3 1 1 | 6 7 f e   NBG2 names T0, NBG3 names T1, NBG1 names T2 T3, NBG2 cells T4, NBG3 cells T5, CPU T7
     A1  0 0 4 f | f 4 f e   NBG0 names T0 T1, NBG0 cells T2 T5, CPU T7        (A0 and A1 share the CPU slot T7 with no access at T6, the manual's pair rule)
     B0  5 5 f f | e e e e   NBG1 cells T0 T1, CPU T4 to T7 after no access at T3;  B1 the same */
#define SAT_V2_ZMCTL 0x0101
#define SAT_CYC_A0L 0x2311
#define SAT_CYC_A0U 0x67fe
#define SAT_CYC_A1L 0x004f
#define SAT_CYC_A1U 0xf4fe
#define SAT_CYC_B0L 0x55ff
#define SAT_CYC_B0U 0xeeee
#else
/* No reduction: one name read and one cell read for every layer.
     A0  2 3 1 f | 6 7 f e   A1  0 f 4 f | f f f e   B0 and B1  5 f f f | e e e e */
#define SAT_V2_ZMCTL 0x0000
#define SAT_CYC_A0L 0x231f
#define SAT_CYC_A0U 0x67fe
#define SAT_CYC_A1L 0x0f4f
#define SAT_CYC_A1U 0xfffe
#define SAT_CYC_B0L 0x5fff
#define SAT_CYC_B0U 0xeeee
#endif
#define SAT_CYC_B1L SAT_CYC_B0L
#define SAT_CYC_B1U SAT_CYC_B0U
#endif
