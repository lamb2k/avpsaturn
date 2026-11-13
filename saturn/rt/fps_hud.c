/* Performance readout, -DSAT_FPS_HUD (lane perf-reconcile, 2026-11-10). Default off; the owner reads it off a real Saturn.
   Three short text lines on the menu layer (NBG3, the home font) at rows 24 to 26, refreshed about once a second:
     PIC n   new pictures that reached the screen in the last second (VDP1 frame-buffer swaps, 60 is the most)
     DONE n  game frames COMPLETED in the last second, normalised to 60 vblanks (60 is full speed): vblanks minus the ones where the game's task walk had not reached its end. Until fix6 this
             field was called GAME and counted writes to the object bank select (one per walk START), which stays 60 while the walk is cut off: it overstated the speed
     FLIP n VBL n  that raw count (object bank selects) and the vblanks of the window, third line
     MISS n  game frames that were not finished when the next vblank came (the game fell behind)
     SKIP n  vblanks where the slave was still drawing, so no new snapshot was taken
     HELD n  swaps put off one vblank because VDP1 had not finished the plot
     TICK n  GAME SPEED (lane gamespeed, 2026-11-12): gameplay ticks the game ran in the window, per 60 vblanks. 60 is the arcade's rate and full speed; 45 means the game ran at 75 % speed.
             It is the game's own clock, the byte at ff8019 that the gameplay loop adds one to for every tick, read next to the IRQ count at ff8018 in the one word kept in sat_dbg.ff8018, so both are
             from the same instant. It reads 0 outside play (menus, fades, loads: the loop is held) and can read over 60 for a moment in the scripted scenes (a held button fast-forwards them in the
             arcade); the byte wraps at 256, so a window of more than 250 vblanks is not shown.
     CUT n   runnable tasks a vblank cut off per 60 vblanks (kernel f_d86); not a speed number. (TASK RUN, which sat at its display cap of 9999, is gone.)
   TR n ffff>tttt Ts.t [L]  (lane loading, 2026-11-12, -DSAT_TR_LINE, row 20 above PROF): the last transition that left the screen without a new picture for at least 12 vblanks (about 0.2 s), numbered from boot.
             From and to are the scene codes at the start and the end of it: the first two hex digits are the game's mode byte ff8001 (bit 7 set while ff81b0 is nonzero: attract, title, ranking), the last two the stage
             word's low byte ff81e9 (00 = front end). Time is seconds and tenths with no new picture from the slave (its picture counter stands still). L: a file load was inside it; then the time is the load's whole-second clock
             (D of the LD line, +-1 s) plus the vblanks that followed it, because the vblank count stands still while GFS runs. Without L the time is counted in vblanks (1/60 s). The slave draws a picture every vblank
             in menus, story, select, continue and play, so a transition without a file read does not show here: that is the finding (loading lane note), not a gap in the readout.
   All of it runs from the cart tail with the cold home code: the hot side (sat_gfx_draw) keeps two words and a call once a second. State lives in the
   cart (writable). Nothing here touches work RAM. The font cells and the panel cell are written by the home menus at boot (draw_home), as for the hardware
   test readout (SAT_PERF_HUD in sat_gfx.c, which needs 2.7 KB of high RAM and does not fit the current builds). */
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
#include "sat_rt.h"
#include "../gfx/sat_vdp2_cfg.h"
extern unsigned long sat_tk_run, sat_tk_skip;
extern u32 sat_ld_log[4][4], sat_ld_n, sat_ld_t0;
extern volatile u32 sat_audio_status, sat_gfx_selftest;
extern u8 RAMB[];
#ifdef SAT_PROF_LINE
extern volatile u32 sat_pf[8];            /* kernel.c: the master's field time split (lane perf-hw): n, field, idle, irq, snapshot, sound, tick */
#endif
#ifdef SAT_TR_LINE
#define NROWS 8                           /* rows 0 to 5 as before, 6 PROF (row 21), 7 TR (row 20) */
#elif defined(SAT_PROF_LINE)
#define NROWS 7
#else
#define NROWS 6
#endif
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
#ifndef SAT_BUILD_REV
#define SAT_BUILD_REV 000000
#endif
#define SAT_STR2(x) #x
#define SAT_STR(x) SAT_STR2(x)
#define SAT_BUILD_REV_STR SAT_STR(SAT_BUILD_REV)
extern void sat_gfx_vdp2_latch(unsigned off, unsigned val);
#define VDP2_VRAM ((volatile u16 *)0x25E00000UL)
#define CRAM ((volatile u16 *)0x25F00000UL)
#define MAP_HOME 0x1e000UL
#define FONT 880u                        /* SAT_GFX_HOME_FONT */
#define COLS 24
static u32 st[12] = { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1 };   /* 10, 11: last task run and skip counts */   /* nonzero so they stay in .data */
/* 0 inited, 1 last vblank, 2 last shown, 3 last overruns, 4 last flips, 5 last skips, 6 last waits, 7 pics, 8 last ff8018 word (TICK), 9 (unused) */
#ifdef SAT_TR_LINE
#define NTEXT 8
#else
#define NTEXT 7
#endif
static u16 shadow[NTEXT][COLS] = { { 0xffff } };
static u32 pfs[7] = { 1, 1, 1, 1, 1, 1, 1 };   /* sat_pf at the last readout (nonzero so it stays in .data) */
static char text[NTEXT][COLS + 16] = { { 'P' }, { 'M' }, { 'F' }, { 'T' }, { 'L' }, { 'H' }, { 'R' }
#ifdef SAT_TR_LINE
    , { 'X' }
#endif
};   /* 6: the PROF line, drawn on the row above the others */   /* painted: COLS columns; the rest is slack so no line can overrun */   /* initialised: the cold image has no .bss */

#ifdef SAT_TR_LINE
/* Transition state (cart data, writable: initialised nonzero so it stays in .data; the first call clears it). */
static u32 tr_s[14] = { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1 };   /* 0 last picture counter, 1 vblanks without a new picture, 2 scene code at the last vblank, 3 file loads seen, 4 first call pending,
                                                                       5 load seconds in vblanks (+1), 6 scene before the load, 7 scene at the start of a stillness, 8 transitions n, 9 from, 10 to, 11 length in vblanks, 12 a load was inside it, 13 the scene code before the last change of it */
#define tr_n tr_s[8]
#define tr_from tr_s[9]
#define tr_to tr_s[10]
#define tr_len tr_s[11]
#define tr_ld tr_s[12]
static u32 scene_code(void) { return ((u32)((RAMB[0x81b0] ? 0x80 : 0) | (RAMB[0x8001] & 0x7f)) << 8) | RAMB[0x81e9]; }
#endif
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
#ifdef SAT_TR_LINE
static char *put_hex4(char *p, u32 v) { int i; for (i = 12; i >= 0; i -= 4) { u32 d = (v >> i) & 15; *p++ = (char)(d < 10 ? '0' + d : 'A' + d - 10); } return p; }
/* Called by the master's vblank handler once per vblank with the slave's picture counter (kernel.c, beside the watchdog). The slave draws a picture every vblank while the screen lives; a file load
   stops it (and the vblank handler with it: GFS runs with interrupts masked), so a load shows as the counter standing still across a gap in the vblank count, the log's load count having moved. */
void sat_fps_vb(u32 pics)
{
    u32 code = scene_code();
    if (tr_s[4]) { u32 k; for (k = 0; k < 14; k++) tr_s[k] = 0; tr_s[0] = pics; tr_s[2] = code; tr_s[13] = code; tr_s[3] = sat_ld_n; return; }
    if (code != tr_s[2]) tr_s[13] = tr_s[2];   /* the game moves its stage word a few vblanks before round_check starts the load (it waits for the word to hold): the scene to report as the one left is the one before that change */
    if (sat_ld_n != tr_s[3]) {   /* a file load ran since the last vblank: its whole seconds (kernel.c sat_ld_log, SMPC clock) plus the stillness that follows */
        const u32 *e = sat_ld_log[(sat_ld_n - 1) & 3];
        tr_s[3] = sat_ld_n; tr_s[5] = ((e[3] - e[2]) % 3600u) * 60u + 1u;   /* 5: seconds of load in vblanks, +1 so a load of under a second still counts */
        tr_s[6] = tr_s[13];    /* 6: the scene before the last change of the scene code */
    }
    if (pics != tr_s[0]) {
        u32 len = tr_s[1] + (tr_s[5] ? tr_s[5] - 1 : 0);
        if (tr_s[5] || tr_s[1] >= 12) {
            tr_n++; tr_from = tr_s[5] ? tr_s[6] : tr_s[7]; tr_to = code; tr_len = len; tr_ld = tr_s[5] != 0;
        }
        tr_s[0] = pics; tr_s[1] = 0; tr_s[5] = 0;
    } else {
        if (!tr_s[1]) tr_s[7] = tr_s[2];   /* 7: the scene at the start of this stillness */
        tr_s[1]++;
    }
    tr_s[2] = code;
}
#endif
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
    sat_gfx_vdp2_latch(0x36, SAT_V2_PNC3); sat_gfx_vdp2_latch(0x4c, SAT_V2_MPAB3); sat_gfx_vdp2_latch(0x4e, SAT_V2_MPCD3); sat_gfx_vdp2_latch(0x94, 0); sat_gfx_vdp2_latch(0x96, 0);
    sat_gfx_vdp2_latch(0x24, 0); sat_gfx_vdp2_latch(0x26, 0); sat_gfx_vdp2_latch(0xee, 0); sat_gfx_vdp2_latch(0x10a, 0); sat_gfx_vdp2_latch(0xec, 0);
    for (e = 0; e < 32; e++)                     /* banks 62 and 63: the home font's white and yellow, plain (no translucent dot). Pen p sits at entry p + 1 of its bank, pen 15 has none. */
        if ((e & 15) != 15) CRAM[62 * 16 + e + 1] = sat_gfx_colour((u16)(((u32)home_pal[e * 2] << 8) | home_pal[e * 2 + 1]));
    for (e = 0; e < 28 * 64; e++) VDP2_VRAM[(MAP_HOME >> 1) + e] = 0;
    shadow[0][0] = 0xffff; shadow[1][0] = 0xffff;
    { u32 r, c; for (r = 0; r < NTEXT; r++) for (c = 0; c < COLS; c++) shadow[r][c] = 0xffff; }
}
static void format(u32 dv)
{
    u32 shown = st[2], over, flips, skips, waits, d;
    char *p;
    (void)shown;
    over = sat_dbg.overruns - st[3]; flips = sat_dbg.obj_flips - st[4]; skips = sat_dbg.gfx_skips - st[5]; waits = sat_gfx_plot_waits - st[6];
    d = shown;   /* new swaps in the window, set by the caller */
    p = put_str(text[0], "PIC "); p = put_num(p, udiv(d * 60 + (dv >> 1), dv)); p = put_str(p, " DONE "); p = put_num(p, udiv((over >= dv ? 0 : dv - over) * 60 + (dv >> 1), dv)); *p = 0;
    p = put_str(text[2], "F"); *p++ = (char)('0' + SAT_GFX_FIT); *p++ = ' '; p = put_str(p, SAT_BUILD_REV_STR); *p++ = ' ';   /* build id: presentation mode (1 scaled, 2 native crop) and the first 6 hex digits of the source commit */
    p = put_str(p, "FLIP "); p = put_num(p, udiv(flips * 60 + (dv >> 1), dv)); p = put_str(p, " VBL "); p = put_num(p, dv); *p = 0;
    {   /* game speed: ticks and IRQs from one word, ff8018 (IRQ count, high byte) and ff8019 (tick count, low byte), per 60 IRQs */
        u32 w = sat_dbg.ff8018, di = ((w >> 8) - (st[8] >> 8)) & 255u, dt = (w - st[8]) & 255u;
        st[8] = w; if (dv > 250) di = 0;
        p = put_str(text[3], "TICK "); p = put_num(p, di ? udiv(dt * 60 + (di >> 1), di) : 0);
    }
    p = put_str(p, " CUT "); p = put_num(p, udiv((sat_tk_skip - st[11]) * 60 + (dv >> 1), dv)); *p = 0;   /* CUT: runnable tasks a vblank cut off, per 60 vblanks */
    if (sat_ld_n) {   /* last round-file load: how many so far, file, sectors, seconds it took, seconds since boot at its end (kernel.c sat_ld_log, real-time clock, +-1 s) */
        const u32 *e = sat_ld_log[(sat_ld_n - 1) & 3];
        u32 len = (e[3] - e[2]) % 3600u, since = (e[3] - (sat_ld_t0 - 1)) % 3600u;
        p = put_str(text[4], "LD"); p = put_num(p, sat_ld_n); p = put_str(p, " F"); p = put_num(p, e[0]); p = put_str(p, " S"); p = put_num(p, e[1]); p = put_str(p, " D"); p = put_num(p, len); p = put_str(p, " B"); p = put_num(p, since); *p = 0;
    }
    {   /* power-up report: SND = SCSP start attempts, OK = SCSP RAM read back and no SMPC wait ran out, TMO = an SMPC wait ran out, RB = the master volume register read back; TEST bits 1 CRAM, 2 VDP2 VRAM, 4 VDP1 VRAM read back as written at init (7 = all) */
        u32 a = sat_audio_status;
        p = put_str(text[5], "HW SND "); p = put_num(p, a & 0xff); p = put_str(p, (a & 0x100) ? " OK" : " NO"); if (a & 0x200) p = put_str(p, " TMO"); if (a & 0x400) p = put_str(p, " RB"); p = put_str(p, " TEST "); p = put_num(p, sat_gfx_selftest); *p = 0;
    }
#ifdef SAT_PROF_LINE
    {   /* PROF: the master's time over the window, percent of the fields' length: T game tick, G graphics (the vblank snapshot), S sound, O the rest of the work (other game tasks, the game's vblank body), I idle (the task walk was done, the master spun) */
        u32 f = sat_pf[1] - pfs[1], t = sat_pf[6] - pfs[6], g = sat_pf[4] - pfs[4], so = sat_pf[5] - pfs[5], id = sat_pf[2] - pfs[2], o, tp, gp, sp, ip, op;
        if (f) {
            o = f > id + t + g + so ? f - id - t - g - so : 0;
            tp = udiv(t * 100 + (f >> 1), f); gp = udiv(g * 100 + (f >> 1), f); sp = udiv(so * 100 + (f >> 1), f); ip = udiv(id * 100 + (f >> 1), f); op = udiv(o * 100 + (f >> 1), f);
            p = put_str(text[6], "PROF T"); p = put_num(p, tp); p = put_str(p, " G"); p = put_num(p, gp); p = put_str(p, " S"); p = put_num(p, sp); p = put_str(p, " O"); p = put_num(p, op); p = put_str(p, " I"); p = put_num(p, ip); *p = 0;
        }
        { u32 k; for (k = 1; k < 7; k++) pfs[k] = sat_pf[k]; }
    }
#endif
#ifdef SAT_TR_LINE
    if (tr_n) {   /* the last transition: number, scene codes from > to, time (the gap is in vblanks; seconds and tenths), L when a file load was inside it */
        u32 t10 = udiv(tr_len * 10 + 30, 60);
        p = put_str(text[7], "TR"); p = put_num(p, tr_n); *p++ = ' '; p = put_hex4(p, tr_from); *p++ = '>'; p = put_hex4(p, tr_to);
        p = put_str(p, " T"); p = put_num(p, udiv(t10, 10)); *p++ = '.'; *p++ = (char)('0' + (t10 - udiv(t10, 10) * 10)); if (tr_ld) p = put_str(p, " L"); *p = 0;
    }
#endif
    p = put_str(text[1], "MISS "); p = put_num(p, over); p = put_str(p, " SKIP "); p = put_num(p, skips); p = put_str(p, " HELD "); p = put_num(p, waits); *p = 0;
}
static void paint(void)
{
    u32 r, c;
    for (r = 0; r < NROWS; r++)
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
                VDP2_VRAM[(MAP_HOME >> 1) + (r == 6 ? 21 : r == 7 ? 20 : 22 + r) * 64 + c] = name;
            }
        }
    }
}
/* Called by the master's vblank handler when the slave has drawn no picture for two seconds: "SLAVE STOP" and the picture count (4 hex digits) on the readout's row 27, written straight into the menu layer's map (the slave
   that normally writes the readout is the one that has stopped). Repeats every 64 vblanks while the stall lasts. */
void sat_fps_stall(u32 still, u32 frames)
{
    static const char msg[] = "SLAVE STOP ";
    u32 c, v = frames;
    (void)still;
    for (c = 0; c < 11; c++) VDP2_VRAM[(MAP_HOME >> 1) + 27 * 64 + c] = name_of(msg[c], 1);
    for (c = 0; c < 4; c++) { u32 d = (v >> (12 - 4 * c)) & 15; VDP2_VRAM[(MAP_HOME >> 1) + 27 * 64 + 11 + c] = name_of((char)(d < 10 ? '0' + d : 'A' + d - 10), 1); }
}
/* Called by sat_gfx_draw about once a second, and once when the menus have just gone. shown: the VDP1 frame-buffer swap count (plot_shown). Returns 1: layer on. */
int sat_fps_hud(u32 shown, int fresh)
{
    u32 v = sat_dbg.vblanks, dv = v - st[1];
#ifdef SAT_ALIGN_CONTROL
    { static volatile u32 mis = 2; volatile u32 sink = *(volatile u32 *)((u8 *)st + mis); (void)sink; }   /* positive control for tools/ymir_misalign_gate.py: a data long read at 2 mod 4 (NEVER in a release build) */
#endif
    if (fresh || st[0])
    {
        
#ifdef SAT_PROF_LINE
        { u32 k; for (k = 1; k < 7; k++) pfs[k] = sat_pf[k]; }
#endif
        st[8] = sat_dbg.ff8018; setup(); st[0] = 0; st[1] = v; st[2] = shown; st[3] = sat_dbg.overruns; st[4] = sat_dbg.obj_flips; st[5] = sat_dbg.gfx_skips; st[6] = sat_gfx_plot_waits; st[10] = sat_tk_run; st[11] = sat_tk_skip;
        text[0][0] = 'P'; text[0][1] = 'I'; text[0][2] = 'C'; text[0][3] = 0; text[1][0] = 0; text[2][0] = 0; text[3][0] = 0; text[4][0] = 0; text[5][0] = 0; text[6][0] = 0;
#ifdef SAT_TR_LINE
        text[7][0] = 0;
#endif
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
    st[1] = v; st[2] = shown; st[3] = sat_dbg.overruns; st[4] = sat_dbg.obj_flips; st[5] = sat_dbg.gfx_skips; st[6] = sat_gfx_plot_waits; st[10] = sat_tk_run; st[11] = sat_tk_skip;
    paint();
    return 1;
}
