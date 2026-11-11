/* Performance readout, -DSAT_FPS_HUD (lane perf-reconcile, 2026-11-10). Default off; the owner reads it off a real Saturn.
   Two short text lines on the menu layer (NBG3, the home font) at rows 24 and 25, refreshed about once a second:
     PIC n   new pictures that reached the screen in the last second (VDP1 frame-buffer swaps, 60 is the most)
     GAME n  game frames run in the last second (60 is full speed)
     MISS n  game frames that were not finished when the next vblank came (the game fell behind)
     SKIP n  vblanks where the slave was still drawing, so no new snapshot was taken
     HELD n  swaps put off one vblank because VDP1 had not finished the plot
   All of it runs from the cart tail with the cold home code: the hot side (sat_gfx_draw) keeps two words and a call once a second. State lives in the
   cart (writable). Nothing here touches work RAM. The font cells and the panel cell are written by the home menus at boot (draw_home), as for the hardware
   test readout (SAT_PERF_HUD in sat_gfx.c, which needs 2.7 KB of high RAM and does not fit the current builds). */
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
#include "sat_rt.h"
extern u32 sat_gfx_plot_waits;           /* swaps put off for an unfinished plot, since boot */
extern unsigned short sat_gfx_colour(unsigned short cps);
#ifdef SAT_HOME_FONT_COLD
extern const u8 sat_home_pal[64];
#define home_pal sat_home_pal
#else
static const u8 home_pal[64] __attribute__((aligned(2))) = {
#include "home_pal.inc"
};
#endif
extern void sat_gfx_vdp2_latch(unsigned off, unsigned val);
#define VDP2_VRAM ((volatile u16 *)0x25E00000UL)
#define CRAM ((volatile u16 *)0x25F00000UL)
#define MAP_HOME 0x1e000UL
#define FONT 880u                        /* SAT_GFX_HOME_FONT */
#define COLS 24
static u32 st[10] = { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1 };   /* nonzero so they stay in .data */
/* 0 inited, 1 last vblank, 2 last shown, 3 last overruns, 4 last flips, 5 last skips, 6 last waits, 7 pics, 8 (unused), 9 (unused) */
static u16 shadow[2][COLS] = { { 0xffff } };
static char text[2][COLS + 1] = { { 'P' }, { 'M' } };   /* initialised: the cold image has no .bss */

static u32 udiv(u32 n, u32 d) { u32 q = 0; if (!d) return 0; while (n >= d) { n -= d; q++; } return q; }
static char *put_str(char *p, const char *s) { while (*s) *p++ = *s++; return p; }
static char *put_num(char *p, u32 v)
{
    char t[8]; int n = 0;
    if (v > 9999) v = 9999;
    do { u32 q = udiv(v, 10); t[n++] = (char)('0' + (v - q * 10)); v = q; } while (v);
    while (n) *p++ = t[--n];
    return p;
}
/* name table word: palette 14 white (labels), 15 yellow (numbers); a space is the panel cell, the black block every line sits on */
static u16 name_of(char c, int yellow)
{
    if (c == ' ' || c == 0) return (u16)(14u << 12 | ((FONT + 58) & 0x3ff));
    return (u16)((yellow ? 15u : 14u) << 12 | ((FONT + (u32)(u8)c - 33) & 0x3ff));
}
static void setup(void)
{
    u32 e;
    /* The access cycles already carry NBG3's slots (sat_gfx_init). The registers go through the draw's latch (applied at V-blank IN), never mid-frame. */
    sat_gfx_vdp2_latch(0x36, 0x8063); sat_gfx_vdp2_latch(0x4c, 0x0f0f); sat_gfx_vdp2_latch(0x4e, 0x0f0f); sat_gfx_vdp2_latch(0x94, 0); sat_gfx_vdp2_latch(0x96, 0);
    sat_gfx_vdp2_latch(0x24, 0); sat_gfx_vdp2_latch(0x26, 0); sat_gfx_vdp2_latch(0xee, 0); sat_gfx_vdp2_latch(0x10a, 0); sat_gfx_vdp2_latch(0xec, 0);
    for (e = 0; e < 32; e++)                     /* banks 62 and 63: the home font's white and yellow, plain (no translucent dot). Pen p sits at entry p + 1 of its bank, pen 15 has none. */
        if ((e & 15) != 15) CRAM[62 * 16 + e + 1] = sat_gfx_colour((u16)(((u32)home_pal[e * 2] << 8) | home_pal[e * 2 + 1]));
    for (e = 0; e < 28 * 64; e++) VDP2_VRAM[(MAP_HOME >> 1) + e] = 0;
    shadow[0][0] = 0xffff; shadow[1][0] = 0xffff;
    { u32 r, c; for (r = 0; r < 2; r++) for (c = 0; c < COLS; c++) shadow[r][c] = 0xffff; }
}
static void format(u32 dv)
{
    u32 shown = st[2], over, flips, skips, waits, d;
    char *p;
    (void)shown;
    over = sat_dbg.overruns - st[3]; flips = sat_dbg.obj_flips - st[4]; skips = sat_dbg.gfx_skips - st[5]; waits = sat_gfx_plot_waits - st[6];
    d = shown;   /* new swaps in the window, set by the caller */
    p = put_str(text[0], "PIC "); p = put_num(p, udiv(d * 60 + (dv >> 1), dv)); p = put_str(p, " GAME "); p = put_num(p, udiv(flips * 60 + (dv >> 1), dv)); *p = 0;
    p = put_str(text[1], "MISS "); p = put_num(p, over); p = put_str(p, " SKIP "); p = put_num(p, skips); p = put_str(p, " HELD "); p = put_num(p, waits); *p = 0;
}
static void paint(void)
{
    u32 r, c;
    for (r = 0; r < 2; r++)
    {
        int num = 0;
        for (c = 0; c < COLS; c++)
        {
            char ch = text[r][c];
            u16 name;
            if (ch == 0 || ch == ' ') { name = name_of(' ', 0); num = 0; }
            else
            {
                /* a run of digits is yellow */
                num = (ch >= '0' && ch <= '9');
                name = name_of(ch, num);
            }
            if (shadow[r][c] != name)
            {
                shadow[r][c] = name;
                VDP2_VRAM[(MAP_HOME >> 1) + (24 + r) * 64 + c] = name;
            }
        }
    }
}
/* Called by sat_gfx_draw about once a second, and once when the menus have just gone. shown: the VDP1 frame-buffer swap count (plot_shown). Returns 1: layer on. */
int sat_fps_hud(u32 shown, int fresh)
{
    u32 v = sat_dbg.vblanks, dv = v - st[1];
    if (fresh || st[0])
    {
        setup(); st[0] = 0; st[1] = v; st[2] = shown; st[3] = sat_dbg.overruns; st[4] = sat_dbg.obj_flips; st[5] = sat_dbg.gfx_skips; st[6] = sat_gfx_plot_waits;
        text[0][0] = 'P'; text[0][1] = 'I'; text[0][2] = 'C'; text[0][3] = 0; text[1][0] = 0;
        paint();
        return 1;
    }
    if (dv < 30) return 1;
    {
        u32 saved = st[2];
        st[2] = shown - saved;   /* format() reads the window's swaps here */
        format(dv);
        st[2] = saved;
    }
    st[1] = v; st[2] = shown; st[3] = sat_dbg.overruns; st[4] = sat_dbg.obj_flips; st[5] = sat_dbg.gfx_skips; st[6] = sat_gfx_plot_waits;
    paint();
    return 1;
}
