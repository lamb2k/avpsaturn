/* Master SH-2 kernel for the lifted 68000 game: the board's cooperative task scheduler, traps and level 2 IRQ, natively.
   Task records stay in game RAM at their original offsets, big-endian, because the game reads them. As on the board a task
   keeps only SR, PC and USP: d0-d7/a0-a6 stay global, so a switch swaps only the C stack. Source: kernel at 0xd86, traps from 0xf00. */
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
typedef signed char s8; typedef short s16; typedef int s32;
typedef struct { u32 d[8]; u32 a[8]; u32 ccz, ccn, ccc, ccv, ccx; } Cpu;
#include "lift_target.h"
#include "sat_rt.h"
#include "../gfx/vdp1_profile.h"

Cpu sat_cpu;
u8 *PAGE[256];
u8 RAMB[0x10000] __attribute__((aligned(4)));
SatDebug sat_dbg;
volatile unsigned long sat_readout[3];
#ifdef SAT_VLOG
/* Lane avp-vanish diagnostic: per frame, VDP1 end-of-draw state at the vblank and at the slave's list write. Read by MCP. */
volatile unsigned long sat_vlog[16 * 4];
#endif   /* FRT ticks, game and drawing, for the SAT_READOUT bars */

#define TASKS 16
#define TASK_STACK 2048   /* high water 308 bytes on the route; stack_scan stops the game if one fills */
#define REC(i) (0xff0058u + (u32)(i) * 0x20u)
#define G_CUR 0xff025cu
#define G_FREEP 0xff0260u
#define G_FREEN 0xff0264u
#define G_VFLAG 0xff0266u
#define O(a) ((a) - 0xff0000u)
#define r8(a) RAM8(O(a))
#define r16(a) RAM16(O(a))
/* The 68000 takes an IRQ between longs, never inside one (seen at 0xf66 in the task record clear). A vblank here can land anywhere, so a long on a 4-byte boundary is one bus write; the split form is only for the boundaries the SH-2 cannot do. */
#define r32(a) RAM32(O(a))
#define w8(a, v) (RAM8(O(a)) = (u8)(v))
#define w16(a, v) (RAM16(O(a)) = (u16)(v))
#define w32(a, v) RAMW32(O(a), (v))
#define cpu (*R)

extern void sat_switch(void **save_sp, void *load_sp);
extern void sat_vblank_entry(void);
void sat_gfx_vblank(void);
#if SAT_VDP1_HW_ERASE
extern void sat_gfx_vblank_out_entry(void);
extern int sat_gfx_erase_suspend(void);
#endif
extern void f_dispatch(u32);
extern void f_e0e(void);
extern void f_800(void);
extern void f_11ec(void);
extern u8 SAT_SINK[], SAT_OBJ[], SAT_PACK[];
u8 sat_gfxram[0x20000] __attribute__((section(".lwgfx"), aligned(4)));

static u32 task_stacks[TASKS][TASK_STACK / 4];
u32 sat_boot_stack[2048];
u32 sat_irq_stack[2048];   /* drawing left this stack with the move to the slave */

static void *task_sp[TASKS];
static void *sched_sp;
static volatile int cur = -1;
static int irq_on;

/* The loader's boot display (boot.c) stays ours until the first picture: a stop before then shows its code instead of the BIOS logo. */
#define DIAG_API ((volatile u32 *)0x06013fa0u)
static void diag_call(int i, u32 a, u32 b) { u32 f = DIAG_API[i]; if (f && DIAG_API[3]) ((void (*)(u32, u32))f)(a, b); }
void sat_fatal(u32 code, u32 detail)
{
    __asm__ volatile ("ldc %0,sr" : : "r"(0xf0));
    diag_call(1, code, detail);
    sat_dbg.fatal = code; sat_dbg.fatal_detail = detail; sat_dbg.fatal_task = (u32)cur;
    sat_dbg.fatal_a[0] = cpu.a[0]; sat_dbg.fatal_a[1] = cpu.a[1]; sat_dbg.fatal_a[2] = cpu.a[7];
    for (;;) ;
}

void *memcpy(void *d, const void *s, unsigned long n) { u8 *a = d; const u8 *b = s; while (n--) *a++ = *b++; return d; }
void *memset(void *d, int v, unsigned long n) { u8 *a = d; while (n--) *a++ = (u8)v; return d; }

/* The board's input latch comes from the pad (pad.c); the other ports read idle. */
extern u32 sat_pad_in0(void), sat_pad_in2(void);
extern void sat_pad_tick(void);
u32 sat_vblanks_now(void) { return sat_dbg.vblanks; }
static u32 io_read(u32 a)
{
    a &= 0xfffffe;
    if (a == 0x804030) return 0xe021;
    if (a == 0x804000) return sat_pad_in0();
    if (a == 0x804020) return sat_pad_in2();
    return 0xffff;   /* 0x804010 players 3 and 4 */
}
u32 IOR8(u32 a) { u32 v = io_read(a); return (a & 1) ? (v & 0xff) : (v >> 8); }
u32 IOR16(u32 a) { return io_read(a) & 0xffff; }
u32 IOR32(u32 a) { return (io_read(a) << 16) | io_read(a + 2); }
extern void sat_audio_io_write8(unsigned long addr, unsigned long value);
void IOW8(u32 a, u32 v) { if (a >= 0x618000 && a <= 0x619fff) sat_audio_io_write8(a, v); }
/* Two object banks: 0x8040e0 bit 0 picks the one the game sees at 0x708000. Only those 8 KB exist; the page below them aliases the sink. */
void IOW16(u32 a, u32 v) { if (a == 0x8040e0) { PAGE[0x70] = SAT_OBJ + (v & 1) * 0x2000 - 0x8000; sat_dbg.obj_flips++; } }
void IOW32(u32 a, u32 v) { (void)a; (void)v; }

u32 f_divu(u32 n, u32 d, int *ov) { u32 q; d &= 0xffff; if (!d) return n; q = n / d; if (q > 0xffff) { *ov = 1; return n; } return ((n % d) << 16) | q; }
u32 f_divs(u32 n, u32 d, int *ov)
{
    s32 dv = (s16)d, nn = (s32)n, q;
    if (!dv) return n;
    if (dv == -1 && n == 0x80000000u) { *ov = 1; return n; }
    q = nn / dv;
    if (q > 32767 || q < -32768) { *ov = 1; return n; }
    return (((u32)(nn % dv) & 0xffff) << 16) | ((u32)q & 0xffff);
}
u32 f_roxl(u32 o, int n, int w, int *x)
{
    int left = w > 0; u32 m;
    if (!left) w = -w;
    m = w == 32 ? 0xffffffffu : (1u << w) - 1;
    n %= (w + 1);
    for (; n > 0; n--) {
        if (left) { int c = (o >> (w - 1)) & 1; o = ((o << 1) | (u32)*x) & m; *x = c; }
        else { int c = o & 1; o = (o >> 1) | ((u32)*x << (w - 1)); *x = c; }
    }
    return o & m;
}
u32 f_abcd(u32 d, u32 s, int *x) { u32 r = (s & 15) + (d & 15) + (u32)*x; if (r > 9) r += 6; r += (s & 0xf0) + (d & 0xf0); *x = r > 0x99; if (*x) r -= 0xa0; return r & 0xff; }
u32 f_sbcd(u32 d, u32 s, int *x) { u32 r = (d & 15) - (s & 15) - (u32)*x; if (r > 9) r -= 6; r += (d & 0xf0) - (s & 0xf0); *x = r > 0x99; if (*x) r += 0xa0; return r & 0xff; }
void f_badjump(u32 a) { sat_fatal(0xe2, a); }
void f_unhandled(u32 a) { sat_fatal(0xe3, a); }
void f_sysreg(void) { }

/* Settings block: the game's EEPROM read (0x41ca) and write (0x42e4) as plain copies against a 128-byte block in RAM. Backup RAM
   comes later. Arguments are the game's own: pointer at ff0ffc, last word index at ff1000, first word at ff1002. */
static u8 save_block[128] __attribute__((aligned(2))) = {
#include "save_seed.inc"
};
#ifdef SAT_HOME
int sat_home_get(int off) { return save_block[off]; }
void sat_home_set(int off, int v) { save_block[off] = (u8)v; save_block[off + 0x30] = (u8)v; }
extern volatile int sat_home_hold;
extern int sat_home_snap_frame(void);   /* home_cold.c */
extern void sat_home_loading(int);
extern void sat_home_poll(void);
extern void sat_duel_step(void);
#endif
void f_41ca(void)
{
    u32 p = r32(0xff0ffc), n = r16(0xff1000) + 1u, w = r16(0xff1002);
    for (; n && w < 64; n--, w++, p += 2) WR16(p, ((const u16 *)save_block)[w]);
}
void f_42e4(void)
{
    u32 p = r32(0xff0ffc), n = r16(0xff1000) + 1u, w = r16(0xff1002);
    for (; n && w < 64; n--, w++, p += 2) ((u16 *)save_block)[w] = RD16(p);
}

/* Start stock, 0x212f8 (a6 = player object; +0xf1 is the stock the HUD shows after "x"): the game's own routine, then in home builds the
   LIVES option when one was chosen. The game calls it at a game start, a join and a continue, so a chosen value is the stock per credit, as the
   game's own lives byte (ff81d1) already is. Left at its default the option writes nothing and play is the arcade's. */
void f_212f8(void)
{
    extern void lifted_212f8(void);
    lifted_212f8();
#ifdef SAT_HOME
    {
        extern int sat_home_start_stock(void);
        int s = sat_home_start_stock();
        if (s >= 0) WR8(cpu.a[6] + 0xf1u, (u8)s);
    }
#endif
}

#ifdef SAT_HOME
/* Home text (lane avp-home-5). Owner 11-08: no credit or coin text anywhere at home; the credit and continue logic is untouched, only text.
   Every arcade line that mentions coins or credits comes from three text writers, each drawing message N of its own table (ROM strings at
   0x119790, 0x11a65e and 0x11a870, searched for COIN, CREDIT, INSERT and FREE: no other copies in the ROM), plus the credit task 0xab438,
   which draws "CREDITS:" and writes the count beside it. HOME_COIN_TEXT is the one list: each entry hides that message (0xff) or draws the
   game's own PRESS START message in its place. Messages not listed draw as the arcade's, but moved in as one block so every non-space
   character lies in columns 3 to 44 of 48: the 16 pixel crop of scroll 1 would cut column 0, 1 and 46, 47 (P1's PRESS at column 1, P2's
   START to 47, the title's TM to 45). */
#define TXT_SMALL 0x119790u   /* writer 0xaba96, 8 px font */
#define TXT_MID 0x11a65eu     /* writer 0xabb0a */
#define TXT_BIG 0x11a870u     /* writer 0xabbae, 16 px font */
typedef struct { u8 table, idx, to; } HomeText;   /* table: 0 small, 1 mid, 2 big */
static const HomeText HOME_COIN_TEXT[] = {
    { 0, 6, 0xff }, { 0, 7, 0xff },                            /* "CREDITS:" "COINS:" (bottom right, one player) */
    { 0, 8, 0xff }, { 0, 9, 0xff }, { 0, 10, 0xff },   /* "CREDITS:" "  COINS:" per player */
    { 0, 11, 0xff }, { 0, 12, 0xff }, { 0, 13, 0xff },
    { 1, 0, 0xff },                                                      /* continue: "CONTINUE REQUIRES ONLY 1 (COIN)" */
    { 2, 0, 3 }, { 2, 1, 3 },                                      /* title: "INSERT COIN", "FREE PLAY" -> PRESS START BUTTON */
    { 2, 17, 3 }, { 2, 18, 3 }, { 2, 19, 3 }, { 2, 20, 3 }, { 2, 21, 3 }, { 2, 22, 3 },   /* "INSERT n (MORE) COIN(S)" */
    { 2, 23, 3 }, { 2, 24, 3 }, { 2, 55, 3 },                /* "PRESS 1P START OR ..", "INSERT 2 COINS" */
    { 2, 25, 0xff }, { 2, 26, 0xff }, { 2, 27, 0xff },      /* "n MORE COIN(S) FOR" "2P" "3P" */
    { 2, 28, 0xff }, { 2, 29, 0xff }, { 2, 30, 0xff }, { 2, 31, 0xff },
    /* each player's slot: "INSERT COIN", "1 MORE COIN", "FREE PLAY", "INSERT n COINS", "n MORE COINS" -> that player's PRESS START (8, 9, 10) */
    { 2, 5, 8 }, { 2, 6, 9 }, { 2, 7, 10 }, { 2, 11, 8 }, { 2, 12, 9 }, { 2, 13, 10 },
    { 2, 14, 8 }, { 2, 15, 9 }, { 2, 16, 10 },
    { 2, 32, 8 }, { 2, 33, 9 }, { 2, 34, 10 }, { 2, 35, 8 }, { 2, 36, 9 }, { 2, 37, 10 },
    { 2, 38, 8 }, { 2, 39, 9 }, { 2, 40, 10 }, { 2, 41, 8 }, { 2, 42, 9 }, { 2, 43, 10 },
    { 2, 44, 8 }, { 2, 45, 9 }, { 2, 46, 10 },
};
#ifdef SAT_HOME_TEXT_LOW   /* the menu base had no high work RAM left; the Wolverine build has about 3 KB high and no low, so the text writers stay high by default */
#define HOME_OS __attribute__((optimize("Os"), section(".lwcode")))   /* low work RAM (.lw) */
#else
#define HOME_OS __attribute__((optimize("Os")))
#endif
static HOME_OS u32 home_text(u32 table, u32 idx)
{
    u32 i;
    for (i = 0; i < sizeof HOME_COIN_TEXT / sizeof HOME_COIN_TEXT[0]; i++)
        if (HOME_COIN_TEXT[i].table == table && HOME_COIN_TEXT[i].idx == idx) return HOME_COIN_TEXT[i].to;
    return idx;
}
extern void f_f7a(void);
extern void lifted_aba96(void), lifted_abb0a(void), lifted_abbae(void);
void f_ab438(void) { f_f7a(); }   /* the credit task's frame: draws nothing at home (its tail, the frame wait, as the arcade's) */
HOME_OS static u32 txt_msg(u32 table, u32 idx) { return table + (u32)(s32)(s16)RD16(table + idx * 2); }
HOME_OS static u32 txt_cell(u32 col, u32 rowb) { u32 o = (col << 7) & 0xffffu; return 0x900000u + ((o & 0xff00u) | ((o + rowb) & 0xffu)); }
/* Columns to move the whole message so that every non-space character sits in columns 3 to 44 (8 pixels inside each edge, as on the arcade). */
HOME_OS static int txt_shift(u32 p, int w)
{
    int lo = 99, hi = -1;
    for (;;)
    {
        int col = RD8(p), i = 0, c;
        p += 3;
        while ((c = RD8(p)) != 0 && c != '/')
        {
            if (c != ' ') { if (col + i * w < lo) lo = col + i * w; if (col + (i + 1) * w > hi) hi = col + (i + 1) * w; }
            i++; p++;
        }
        if (!c) break;
        p++;
    }
    if (hi < 0) return 0;
    if (lo < 3 && hi - (lo - 3) <= 45) return 3 - lo;
    if (hi > 45 && lo - (hi - 45) >= 3) return 45 - hi;
    return 0;
}
/* The writers 0xaba96 (small) and 0xabbae (big) with a column shift, same cells and attributes. */
HOME_OS static void txt_draw(u32 p, int big, int erase, int sh, int lim)   /* lim: draw only the first record, at most lim letters; 0 all */
{
    int n = 0;
    for (;;)
    {
        u32 a = txt_cell((u32)((int)RD8(p) + sh), RD8(p + 1));
        u32 pal = (u16)(s16)(s8)RD8(p + 2), c;
        p += 3;
        while ((c = RD8(p)) != 0 && c != '/' && (!lim || n++ < lim))
        {
            p++;
            if (erase) { WR32(a, 0x200000u | (pal & 0xff)); if (big) { WR32(a + 4, 0x200000u | (pal & 0xff)); WR32(a + 128, 0x200000u | (pal & 0xff)); WR32(a + 132, 0x200000u | (pal & 0xff)); a += 256; } else a += 128; continue; }
            if (!big) { WR16(a, (u16)c); WR16(a + 2, (u16)pal); a += 128; continue; }
            {
                u32 v = (u8)(c - 0x20);
                u16 code = (v & 0x80) ? 0 : RD16(0xab8b4u + v * 2);
                if (!code) { WR32(a, 0x20000000u); WR32(a + 4, 0x20000000u); WR32(a + 128, 0x20000000u); WR32(a + 132, 0x20000000u); }
                else
                {
                    WR16(a, code); WR16(a + 2, (u16)pal); WR16(a + 4, (u16)(code + 0x10)); WR16(a + 6, (u16)pal);
                    WR16(a + 128, (u16)(code + 1)); WR16(a + 130, (u16)pal); WR16(a + 132, (u16)(code + 0x11)); WR16(a + 134, (u16)pal);
                }
                a += 256;
            }
        }
        if (!c || lim) break;
        p++;
    }
}
HOME_OS void f_aba96(void)
{
    u32 idx = home_text(0, cpu.d[0] & 0x7f), erase = cpu.d[0] & 0x80;
    int sh;
    if (idx == 0xff) return;
    sh = txt_shift(txt_msg(TXT_SMALL, idx), 1);
    if (!sh) { lifted_aba96(); return; }
    txt_draw(txt_msg(TXT_SMALL, idx), 0, erase != 0, sh, 0);
}
HOME_OS void f_abb0a(void)
{
    if (home_text(1, cpu.d[0] & 0x7f) == 0xff) return;
    lifted_abb0a();
}
HOME_OS void f_abbae(void)
{
    u32 idx = home_text(2, cpu.d[0] & 0x7f), erase = cpu.d[0] & 0x80;
    int sh;
    if (idx == 0xff) return;
    cpu.d[0] = (cpu.d[0] & ~0xffu) | idx | erase;
    if (idx >= 2 && idx <= 4)   /* the title's "PRESS START BUTTON" with "ONLY ONE PLAYER" or "UP TO TWO / THREE PLAYERS" under it (the game picks by credits; owner 11-10: just PRESS START):
                                   the first 11 letters of message 2's PRESS START BUTTON record, same row, palette and font, moved from column 6 to 13 = centred on the screen's middle, nothing else */
    {
        txt_draw(txt_msg(TXT_BIG, 2) + 5, 1, erase != 0, 7, 11);
        return;
    }
    sh = txt_shift(txt_msg(TXT_BIG, idx), 2);
    if (!sh) { lifted_abbae(); return; }
    txt_draw(txt_msg(TXT_BIG, idx), 1, erase != 0, sh, 0);
}
#endif

/* Scheduler */
static void to_sched(void)
{
    int me = cur;
    u32 usp = cpu.a[7];
    if (me < 0 || !sched_sp) sat_fatal(0xea, (u32)me);
    sat_switch(&task_sp[me], sched_sp);
    cpu.a[7] = usp; cpu.a[1] = usp; cpu.a[0] = REC(me);
}
static void task_tramp(void)
{
    f_dispatch(r32(REC(cur) + 4));
    sat_fatal(0xe4, (u32)cur);
}
static void clear_rec(u32 r) { w32(r + 0x10, 0); w32(r + 0x14, 0); w32(r + 0x18, 0); w32(r + 0x1c, 0); w8(r, 0); }
static void task_end(void)
{
    void *dead;
    if (cur < 0 || !sched_sp) sat_fatal(0xe5, (u32)cur);
    sat_switch(&dead, sched_sp);
}
/* addq.w and subq.w on the free count are one instruction on the board; the vblank body may start tasks (not checked), so it stays one step here. Pointer steps stay interruptible, as on the board. */
static void free_count_add(int d)
{
    u32 sr;
    __asm__ volatile ("stc sr,%0" : "=r"(sr));
    __asm__ volatile ("ldc %0,sr" : : "r"(sr | 0xf0));
    w16(G_FREEN, r16(G_FREEN) + d);
    __asm__ volatile ("ldc %0,sr" : : "r"(sr));
}
static void free_push(u32 r) { u32 p = r32(G_FREEP) - 4; w32(p, r); w32(G_FREEP, p); free_count_add(1); }
#define LOWW(reg, v) ((reg) = ((reg) & 0xffff0000u) | ((v) & 0xffff))

void f_trap0(void) { u32 r = 0xff0058u + (cpu.d[0] & 0xffff); cpu.a[1] = 0xff0058u; if (r8(r) == 0) { w16(r, 0xc00); w32(r + 4, cpu.a[0]); w16(r + 0x10, cpu.d[1]); w16(r + 0x12, cpu.d[2]); } }
void f_trap10(void) { u32 r = 0xff0058u + (cpu.d[0] & 0xffff); cpu.a[1] = 0xff0058u; w16(r, 0xc00); w32(r + 4, cpu.a[0]); w16(r + 0x10, cpu.d[1]); w16(r + 0x12, cpu.d[2]); }
void f_trap7(void)
{
    if (r16(G_FREEN)) {
        u32 p = r32(G_FREEP), r = r32(p);
        cpu.a[6] = p + 4; cpu.a[1] = r; w32(G_FREEP, p + 4); free_count_add(-1);
        w16(r, 0xc00); w32(r + 4, cpu.a[0]); w16(r + 0x10, cpu.d[0]); w16(r + 0x12, cpu.d[1]);
    }
}
void f_trap1(void) { clear_rec(REC(cur)); task_end(); }
void f_trap9(void) { u32 r = REC(cur); clear_rec(r); free_push(r); task_end(); }
void f_trap2(void) { u32 off = cpu.d[0] & 0xffff, r = 0xff0058u + off; cpu.a[4] = 0xff0058u; if (r8(r)) { cpu.d[1] = 0; clear_rec(r); } }
void f_trap3(void)
{
    u32 r = REC(cur), bit = (cpu.d[0] & 0xff) ? 0x100 : 0x200, v = (cpu.d[0] & 0xffff) | bit;
    LOWW(cpu.d[1], bit); LOWW(cpu.d[0], v); w16(r, v); w32(r + 8, cpu.a[7]); to_sched();
}
void f_trap4(void) { u32 r = REC(cur); w8(r, 4); w32(r + 8, cpu.a[7]); to_sched(); }
void f_trap5(void) { u32 r = 0xff0058u + (cpu.d[0] & 0xffff); w8(r, 2); w8(r + 1, 0); cpu.a[4] = 0xff0058u; }
void f_trap6(void) { u32 r = 0xff0058u + (cpu.d[0] & 0xffff); w8(r, 4); w8(r + 1, cpu.d[1]); cpu.a[4] = 0xff0058u; }
void f_trap8(void)
{
    /* Board 0xfde: the first live record of the eight with tag d1 only. a4, d7, d0 and a6 stay as it leaves them. */
    u32 r = REC(8); int n = 7;
    w8(0xff81b3, 0);
    LOWW(cpu.d[7], 7);
    for (;;)
    {
        if (r8(r) && r8(r + 0x16) == (cpu.d[1] & 0xff)) { cpu.d[0] = 0; clear_rec(r); free_push(r); cpu.a[6] = r32(G_FREEP); break; }
        r += 0x20;
        if (--n < 0) { LOWW(cpu.d[7], 0xffff); break; }
        LOWW(cpu.d[7], n);
    }
    cpu.a[4] = r;
}
/* Board 0x1026: end every live record of the eight. */
void f_trap11(void)
{
    u32 r = REC(8); int i;
    for (i = 8; i < 16; i++, r += 0x20) if (r8(r)) { cpu.d[0] = 0; clear_rec(r); free_push(r); cpu.a[6] = r32(G_FREEP); }
    cpu.a[4] = r; LOWW(cpu.d[7], 0xffff);
}
void f_trap12(void) { } void f_trap13(void) { } void f_trap14(void) { } void f_trap15(void) { }

static void run_task(int i)
{
    u32 r = REC(i), st = r8(r);
    cur = i; w32(G_CUR, r);
    if (st == 0xc) {
        u32 *sp = task_stacks[i] + TASK_STACK / 4;
        int k;
        w8(r, 8);
        cpu.a[7] = r32(r + 0xc); cpu.a[4] = cpu.a[7]; cpu.a[1] = r32(r + 4); cpu.a[0] = r;
        LOWW(cpu.d[1], 0xc); cpu.a[5] = 0xff8000;
        *--sp = (u32)task_tramp;
        for (k = 0; k < 6; k++) *--sp = 0;
        sat_switch(&sched_sp, sp);
    } else {
        w8(r, 8);
        LOWW(cpu.d[1], st); cpu.a[1] = r32(r + 8); cpu.a[0] = r;   /* board 0xdc8, 0xdea: lifted code can read these */
        if (!task_sp[i]) sat_fatal(0xe6, (u32)i);
        sat_switch(&sched_sp, task_sp[i]);
    }
}

extern void sat_exc_illegal(void), sat_exc_slot(void), sat_exc_addr(void);
void sat_exception(u32 vec, u32 pc, u32 pr)
{
    sat_dbg.exc_pc = pc; sat_dbg.exc_pr = pr;
    sat_fatal(0xf0 + vec, pc);
}
static void exceptions_install(void)
{
    void (**vt)(void) = (void (**)(void))0x06000000;
    u32 v = 0x06000000;
    vt[4] = sat_exc_illegal; vt[6] = sat_exc_slot; vt[9] = sat_exc_addr; vt[10] = sat_exc_addr;
    __asm__ volatile ("ldc %0,vbr" : : "r"(v));
}

static void irq_enable(void)
{
    __asm__ volatile ("ldc %0,sr" : : "r"(0xf0));
    ((void (**)(void))0x06000000)[0x40] = sat_vblank_entry;
#if SAT_VDP1_HW_ERASE
    ((void (**)(void))0x06000000)[0x41] = sat_gfx_vblank_out_entry;
#endif
    { u32 v = 0x06000000; __asm__ volatile ("ldc %0,vbr" : : "r"(v)); }
    *(volatile u32 *)0x25fe00a4 = 0;            /* clear pending */
#if SAT_VDP1_HW_ERASE
    *(volatile u32 *)0x25fe00a0 = 0xfffffffcu;  /* vblank-in and erase cleanup at vblank-out */
#else
    *(volatile u32 *)0x25fe00a0 = 0xfffffffeu;  /* only vblank-in */
#endif
    irq_on = 1;
    __asm__ volatile ("ldc %0,sr" : : "r"(0x00));
}

/* Free running timer at clock / 128 (about 4.5 us a tick), restarted at each vblank. Readings are emulator-only until run on a console. */
#define FRTH (*(volatile u8 *)0xfffffe12u)
#define FRTL (*(volatile u8 *)0xfffffe13u)
#define FTCR (*(volatile u8 *)0xfffffe16u)
static inline u32 frt(void) { u32 h = FRTH; return (h << 8) | FRTL; }
static volatile int game_done;

#ifdef SAT_PROF
/* Test flag: per-frame histograms over a fixed vblank window, 128 FRT ticks a bucket (about 0.61 ms). MODELLED until run on a console.
   frame: master busy from the vblank that started a game frame until its idle, across overruns. gfx: drawing. snap: snapshot on the master. */
#define PROF_FROM 1000
#define PROF_TO 1650
typedef struct { u32 from, to, ticks, done, over, skipped; u16 frame[128], gfx[128], snap[128]; } SatProf;
SatProf sat_prof __attribute__((section(".lwgfx")));
static u32 frame_carry;
static void prof_add(u16 *h, u32 t) { t >>= 7; h[t > 127 ? 127 : t]++; }
#define IN_WINDOW (sat_dbg.vblanks >= PROF_FROM && sat_dbg.vblanks < PROF_TO)
#endif

#ifdef SAT_PROF_PC
/* Test flag: PC and PR sampled by the master's FRT compare interrupt, level 15, about every 5 ms with a per-vblank phase, over the window, in unused cart space. Read by run_yaba.py, ranked by tools/sat_pc_rank.py. MODELLED. */
#define PC_STEP 1100
#define PC_MAX 2500
#define FTIER (*(volatile u8 *)0xfffffe10u)
#define FTCSR_M (*(volatile u8 *)0xfffffe11u)
#define OCRAH (*(volatile u8 *)0xfffffe14u)
#define OCRAL (*(volatile u8 *)0xfffffe15u)
#define TOCR (*(volatile u8 *)0xfffffe17u)
#define sat_pcs ((u32 *)0x02557000u)
u32 sat_pcn;
extern void sat_pc_entry(void);
static u32 pc_next;
static void pc_arm(u32 at) { pc_next = at; TOCR = 0; OCRAH = (u8)(at >> 8); OCRAL = (u8)at; }
void sat_pc_sample(u32 pc, u32 pr)
{
    FTCSR_M = (u8)(FTCSR_M & ~0x08);
    if (IN_WINDOW && sat_pcn < PC_MAX) { sat_pcs[sat_pcn * 2] = pc; sat_pcs[sat_pcn * 2 + 1] = pr; sat_pcn++; }
    pc_arm(pc_next + PC_STEP);
}
static void pc_start(void)
{
    ((void (**)(void))0x06000000)[0x70] = sat_pc_entry;
    *(volatile u16 *)0xfffffe66u = 0x0070;   /* VCRC: compare vector */
    *(volatile u16 *)0xfffffe60u = (u16)(*(volatile u16 *)0xfffffe60u | 0x0f00); /* IPRB: FRT level 15 */
    pc_arm(PC_STEP);
    FTIER = 0x09;
}
#endif

/* Slave SH-2: draws, nothing else. Interface is one handoff: while gfx_handed != gfx_done the slave owns the snapshot, otherwise the master does.
   Each counter has one writer and is read through the cache-through alias. The slave waits on its own FRT input-capture flag, set by a master
   write to 0x21000000, so its idle loop stays off the bus. The whole cache is purged per frame: the snapshot changed under it, nothing else it caches does. */
#define UNCACHED(v) (*(volatile u32 *)((u32)&(v) | 0x20000000u))
#define CCR (*(volatile u8 *)0xfffffe92u)
#define FTCSR (*(volatile u8 *)0xfffffe11u)
#define SLAVE_WAKE (*(volatile u16 *)0x21000000u)
#define SMPC(o) (*(volatile u8 *)(0x20100000u + (o)))
extern void sat_slave_entry(void);
#if defined(SAT_GUESTS) && defined(SAT_WV_REVEAL) && !SAT_VDP1_HW_ERASE
u32 gfx_handed, gfx_done;   /* the reveal (cart code) waits for the slave and takes the picture over through these */
#else
static u32 gfx_handed, gfx_done;
#endif
#ifdef SAT_CPU_SLACK_PROFILE
#define CPU_SLACK_ROW(i) ((volatile unsigned int *)((u32)&sat_cpu_slack[(i)] | 0x20000000u))
#include "cpu_slack_profile.h"
/* The vblank can interrupt this sample or its publication. A changed epoch or
   cleared game_done rejects the sample; a partial mailbox has tag zero. */
static void cpu_slack_mark_idle(void)
{
    u32 vblank = *(volatile u32 *)&sat_dbg.vblanks;
    u32 tick = frt(), flags = (FTCSR & 2) ? CS_TIMER_WRAP : 0;
    if (UNCACHED(gfx_handed) != UNCACHED(gfx_done)) flags |= CS_BUSY_DONE;
    if (game_done && vblank == *(volatile u32 *)&sat_dbg.vblanks)
        cpu_slack_publish_done(vblank, tick, flags);
}
#endif
#if defined(SAT_VDP1_PROFILE) || defined(SAT_PERF_HUD)
int sat_gfx_profile_busy(void)
{
    return UNCACHED(gfx_done) != UNCACHED(gfx_handed);
}
#endif
u32 sat_slave_stack[256] __attribute__((section(".lwgfx")));

#ifdef SAT_PERF_HUD
extern u32 sat_gfx_hud_pre;
extern void sat_gfx_hud_idle(void);
#endif
void sat_slave_main(void)
{
    CCR = 0x10; CCR = 0x01;
    FTCR = 2;
    diag_call(5, 1, 0);   /* the loader's display: the slave runs */
    for (;;) {
        u32 t, seen;
#ifdef SAT_PERF_HUD
        while (!(FTCSR & 0x80)) sat_gfx_hud_idle();   /* readout build: notes the moment VDP1 ends a plot while the slave would only wait */
#else
#ifdef AVP_DIAG_SLAVEPOLL   /* analysis builds only: marks (line 120-121) whether the SCU ever shows a pending vblank-in after the first handler */
        while (!(FTCSR & 0x80)) { if (UNCACHED(sat_dbg.vblanks) && (*(volatile u32 *)0x25fe00a4 & 1)) diag_call(5, 15, 0); }
#else
        while (!(FTCSR & 0x80)) ;
#endif
#endif
        FTCSR = (u8)(FTCSR & 0x7f);
        CCR = 0x11;
        diag_call(5, 2, 0);   /* the master woke the slave */
        seen = UNCACHED(gfx_handed);
        if (seen == UNCACHED(gfx_done)) continue;
#ifdef SAT_PERF_HUD
        sat_gfx_hud_pre = frt();   /* the slave's timer at the wake, before the per-draw reset: the readout's plot-end bound */
#endif
        FRTH = 0; FRTL = 0;
        diag_call(5, 13, 0);
        sat_gfx_draw();
        diag_call(5, 14, 0);
        t = frt();
        sat_dbg.gfx_ticks = t; *(volatile unsigned long *)((unsigned long)&sat_readout[1] | 0x20000000UL) = t;
        if (t > sat_dbg.gfx_peak) sat_dbg.gfx_peak = t;
#ifdef SAT_PROF
        if (IN_WINDOW) prof_add(sat_prof.gfx, t);
#endif
        UNCACHED(gfx_done) = seen;
    }
}

static void smpc_idle(void)   /* the SMPC is busy while SF is set (the BIOS polls it every frame); a bounded wait, never a spin */
{
    u32 n;
    for (n = 0; n < 4000000u && (SMPC(0x63) & 1); n++) ;
}
static void slave_start(void)
{
    smpc_idle();
    SMPC(0x63) = 1; SMPC(0x1f) = 0x03;   /* SSHOFF */
    smpc_idle();
    *(void (**)(void))0x06000250u = sat_slave_entry;
    *(u32 *)0x060002acu = (u32)(sat_slave_stack + 256);
    SMPC(0x63) = 1; SMPC(0x1f) = 0x02;   /* SSHON */
    smpc_idle();
}

/* Rounds: each round's tile pack and sound set come from CD between rounds (RNN.BIN, tools/rounds_pack.py), on the master, with the game stopped and the slave idle.
   The game's stage word, ff81e8, says which: 0 in attract and on the front end. rounds.inc maps a stage word and the characters in play to a file; the same path for every round.
   ff81cc holds a bit per character in play. It drops bits around a KO and follows the cursor on the select screen, so bits are gathered while in a stage and cleared at the front end's load. A character who joins mid-stage gets their file at the next stage word. */
#define LOADER_API ((volatile u32 *)0x06013fd0u)
#define CCR_M (*(volatile u8 *)0xfffffe92u)
#include "rounds.inc"
#ifdef SAT_GUESTS
#include "guests.h"
#endif
u8 sat_aud_tables[0x2000] __attribute__((section(".lwgfx"), aligned(4)));
static int round_loaded = -1;
struct sat_rounds_s { u32 current, loads, sectors, last_vblank; } sat_rounds;
/* The sound part of a round file lands at SAT_PACK first and goes to SCSP RAM here; the tile part then overwrites it. */
static void round_sound_ready(void)
{
    extern int sat_audio_clips_loaded;
    u32 keep = 12u + 16u * ((u32)(SAT_PACK[4] << 8 | SAT_PACK[5]) + (u32)(SAT_PACK[6] << 8 | SAT_PACK[7]));
    if (keep > sizeof sat_aud_tables) sat_fatal(0xee, keep);
    memcpy(sat_aud_tables, SAT_PACK, keep);
    if (round_loaded < 0) {
        sat_audio_clips_loaded = 1;
        if (!sat_audio_init(sat_aud_tables)) sat_fatal(0xec, 0);
    }
    if (!sat_audio_swap(sat_aud_tables, SAT_PACK + keep)) sat_fatal(0xec, 1);
}
static void load_round(int file)
{
    char name[] = "R000.BIN";
    long got;
    name[1] = (char)('0' + file / 100); name[2] = (char)('0' + file / 10 % 10); name[3] = (char)('0' + file % 10);
    diag_call(5, 17, 0);
    got = ((long (*)(const char *, void (*)(void)))LOADER_API[0])(name, round_sound_ready);
    diag_call(5, 18, 0);
    CCR_M = 0x11;
    if (got < 0) sat_fatal(0xed, (u32)-got);
    sat_rounds.sectors = (u32)got;
}
#ifdef SAT_DUEL_MENU
extern volatile u32 sat_duel_on;
volatile u8 sat_duel_plain;   /* test hook (play_versus.py PLAIN=1), 0 in play: 1 = a duel runs the stage's plain file, for a before and after on one disc */
#endif
static void round_check(void)
{
    int row = stage_row[(r8(0xff81b0) || r8(0xff8001) != 2) ? 0 : r16(0xff81e8) & 0xff], want, want0;
    static u32 settled;
    static int row_loaded;
    static u8 chars;
#if SAT_VDP1_HW_ERASE
    int erase_old_row = row_loaded;
#endif
    int stale = 0;
    if (row) chars |= r8(0xff81cc) & 15;
#ifdef SAT_GUESTS
    /* The front end's file follows the bonus characters setting (guests with select screen art have a front file of their own): the
       word is steady here, so no wait, and the load runs at once when the title menu hands back to the game. */
    stale = !row && !row_loaded && round_loaded != sat_guest_file(0, 0, 0, row_file[0][0]);
#endif
    if (row == row_loaded && !stale) { settled = 0; return; }
    /* The word flickers for a few frames as a scene closes; go only when it has held. */
    if (!stale && !settled) settled = sat_dbg.vblanks;
    if (!stale && sat_dbg.vblanks - settled < 12) return;
    settled = 0;
    if (!row) chars = 0;
    want = row_file[row][mask_variant[chars]];
#ifdef SAT_GUESTS
    want = sat_guest_file(row, chars, mask_variant[chars], want);   /* bonus characters: guests.c */
#endif
    want0 = want;
#ifdef SAT_DUEL_MENU
    /* A duel on an arena stage runs the file's duel copy (build.py duel_plan): it also keeps the ROM pages stage 02's walk reads, which the duel reads and the stage's own file spills tiles into. */
    if (sat_duel_on && row && !sat_duel_plain) {
        int d;
        for (d = 0; d < DUEL_PAIRS; d++)
            if (duel_pairs[d][0] == want) { want = duel_pairs[d][1]; break; }
    }
#endif
    row_loaded = row;
    diag_call(5, 16, 0);
#ifdef SAT_HOME
    sat_home_loading(1);   /* NOW LOADING stays on screen through the load */
#endif
    while (UNCACHED(gfx_done) != UNCACHED(gfx_handed)) ;   /* the slave finishes the picture in hand and stays off the pack */
    __asm__ volatile ("ldc %0,sr" : : "r"(0xf0));
#if SAT_VDP1_HW_ERASE
    if (!sat_gfx_erase_suspend())   /* GFS masks/replaces the OUT cleanup interrupt */
    {
        row_loaded = erase_old_row;
        __asm__ volatile ("ldc %0,sr" : : "r"(0x00));
#ifdef SAT_HOME
        sat_home_loading(0);
#endif
        return;   /* a stuck blank flag must not cause a long masked erase */
    }
#endif
#ifndef SAT_HOME
    sat_gfx_display(0);
#endif
    load_round(want);
    if (!sat_gfx_swap_pack(SAT_PACK)) sat_fatal(0xeb, 1);
    sat_audio_resume_music();
#ifdef SAT_HOME
    sat_home_loading(0);
#else
    sat_gfx_display(1);
#endif
    round_loaded = want;
#ifdef SAT_GUESTS
    sat_guest_loaded(row, chars, mask_variant[chars], want0);   /* guest colours follow the art this file holds */
#endif
    sat_rounds.current = (u32)want;
    sat_rounds.loads++;
    sat_rounds.last_vblank = sat_dbg.vblanks;
    /* GFS takes the SCU mask and vectors for itself: without this the vblank never comes back after a load. */
    exceptions_install();
    irq_enable();
}

#if defined(SAT_GUESTS) && defined(SAT_WV_REVEAL) && !SAT_VDP1_HW_ERASE
/* The post-credits reveal owns the picture while LOADER_DIAG[5] is set: the vblank hands nothing to the slave, so the chips are the reveal's. This test is all of the reveal that stays in
   resident code (owner 11-10: the high RAM cost near zero); the takeover, the loader calls and the poll are in cart code (guests.c sat_reveal_call and sat_reveal_poll, the overlay reveal.c
   loaded from REVCODE.BIN at the ending). The poll is called from sat_home_flow (home_cold.c), after round_check as before. */
#define REVEAL_ON (((volatile u32 *)0x06013fe0u)[5])
#else
#define REVEAL_ON 0
#endif

/* Dispatcher 0xd86. A vblank sets the game's flag at 0xff0266 through f_e0e, which restarts the walk from task 0. */
void f_d86(void)
{
    diag_call(0, 0, 0);   /* the game's dispatcher is reached */
    if (!irq_on) irq_enable();
    diag_call(0, 0, 0);   /* the vblank interrupt is enabled */
    sat_dbg.stage = 2;
#ifdef SAT_PROF_PC
    pc_start();
#endif
    for (;;) {
        int i;
        round_check();
#ifdef SAT_HOME
        sat_home_poll();
        sat_duel_step();
#endif
        w8(G_VFLAG, 0);
        for (i = 0; i < TASKS; i++) {
            u32 st;
            if (r8(G_VFLAG)) break;
            st = r8(REC(i));
            cpu.a[0] = REC(i); LOWW(cpu.d[0], 15 - i);
            cpu.d[1] = (cpu.d[1] & 0xffffff00u) | st;
            if (st >= 4) {
                run_task(i);
                sat_dbg.task_runs++;
                cpu.a[0] = REC(i); LOWW(cpu.d[0], 15 - i);
            }
            cur = -1;
        }
        if (i == TASKS) {
            if (!game_done) {
                game_done = 1; sat_dbg.game_ticks = frt(); *(volatile unsigned long *)((unsigned long)sat_readout | 0x20000000UL) = sat_dbg.game_ticks; if (sat_dbg.game_ticks > sat_dbg.game_peak) sat_dbg.game_peak = sat_dbg.game_ticks;
#ifdef SAT_CPU_SLACK_PROFILE
                cpu_slack_mark_idle();
#endif
#ifdef SAT_PROF
                if (IN_WINDOW) { prof_add(sat_prof.frame, frame_carry + sat_dbg.game_ticks); sat_prof.done++; }
                frame_carry = 0;
#endif
            }
            cpu.a[0] = REC(15) + 0x20; cpu.d[0] |= 0xffff; f_11ec(); sat_dbg.idle_calls++;
        }
    }
}

#ifdef SAT_HOME
#include "duel.inc"
#endif
static void stack_scan(void)
{
    int i;
    u32 hi = 0;
    for (i = 0; i < TASKS; i++) {
        u32 *p = task_stacks[i], n = 0;
        while (n < TASK_STACK / 4 && p[n] == 0xa5a5a5a5u) n++;
        n = TASK_STACK - n * 4;
        if (n > hi) hi = n;
        if (n == TASK_STACK) sat_fatal(0xe7, (u32)i);
    }
    sat_dbg.task_stack_high = hi;
}

/* C body of the vblank IRQ, on its own stack. Runs the game's level 2 handler, as the board does, then the hook. */
void sat_vblank(void)
{
    static Cpu save;
    int sc = cur;
    u32 t0, t1, t2;
#ifdef SAT_CPU_SLACK_PROFILE
    u32 slack_end = frt(), slack_wrap = (FTCSR & 2) ? CS_TIMER_WRAP : 0;
#endif
    u32 first = !sat_dbg.vblanks;
#define DIAG_AT(n) do { if (first) diag_call(5, (n), 0); } while (0)
    *(volatile u32 *)0x25fe00a4 = ~1u;
    /* The SCU sets its whole interrupt mask when the CPU accepts an interrupt (so handlers do not nest); the handler must put its mask back or no further
       interrupt arrives: the game stopped after the first picture on hardware-accurate cores (Ymir) while Yaba, which does not do this, kept going. */
#if SAT_VDP1_HW_ERASE
    *(volatile u32 *)0x25fe00a0 = 0xfffffffcu;
#else
    *(volatile u32 *)0x25fe00a0 = 0xfffffffeu;
#endif
    DIAG_AT(3);
    if (sat_dbg.vblanks == 1) diag_call(5, 11, 0);   /* the second vblank is entered */
#ifndef SAT_VDP1_RACE_OLD
    sat_gfx_vblank();   /* first: the frame change for a finished plot belongs early in vblank-in */
#endif
    DIAG_AT(4);
    if (sat_dbg.vblanks == 1) diag_call(5, 12, 0);
    sat_dbg.vblanks++;
    if (DIAG_API[3]) { if (sat_dbg.vblanks <= 3) diag_call(0, 0, 0); else if (sat_dbg.vblanks == 4) diag_call(2, 1, 0); }   /* the loader's display ends on the 4th vblank */
#ifdef SAT_VLOG
    { volatile unsigned long *e = (volatile unsigned long *)((unsigned long)&sat_vlog[(sat_dbg.vblanks & 15) * 4] | 0x20000000UL);
      e[0] = sat_dbg.vblanks << 16 | *(volatile unsigned short *)0x25D00010UL; e[1] = 0; e[2] = 0; e[3] = (UNCACHED(gfx_done) != UNCACHED(gfx_handed)); }
#endif
    if (!game_done) sat_dbg.overruns++;
#ifdef SAT_PROF
    sat_prof.from = PROF_FROM; sat_prof.to = PROF_TO;
    if (IN_WINDOW) { sat_prof.ticks++; if (!game_done) sat_prof.over++; }
    if (!game_done) frame_carry += frt();
#endif
#ifdef SAT_CPU_SLACK_PROFILE
    cpu_slack_close(slack_end, game_done, slack_wrap, UNCACHED(gfx_handed), UNCACHED(gfx_done));
    cpu_slack_begin(sat_dbg.vblanks,
        (game_done ? 0 : CS_PREVIOUS_OVERRUN) |
        (UNCACHED(gfx_handed) != UNCACHED(gfx_done) ? CS_BUSY_BEGIN : 0),
        (u32)RAM16(0x81e8) | (u32)(RAMB[0x8380] ? RAMB[0x8381] : 255) << 16 |
        (u32)(RAMB[0x8480] ? RAMB[0x8481] : 255) << 24);
    /* SH7604 FTCSR bit 1 is read-then-write-zero OVF. Clear only this flag
       alongside the existing counter reset; do not enable another interrupt. */
    FTCSR = (u8)(FTCSR & ~2u);
#endif
    game_done = 0;
    FRTH = 0; FRTL = 0;
#ifdef SAT_PROF_PC
    pc_arm(200 + (sat_dbg.vblanks * 37) % PC_STEP);
#endif
    sat_pad_tick();
    t0 = frt();
    DIAG_AT(5);
#ifdef SAT_HOME
    if (sat_home_hold) {   /* the game is held: picture and sound only */
        if (UNCACHED(gfx_done) == UNCACHED(gfx_handed)) {
            u32 held = (u32)sat_home_snap_frame();   /* stage select's held title picture (home_cold.c): 1 = hand the slave the snapshot it has */
            if (!held) sat_gfx_snapshot_begin();
            UNCACHED(gfx_handed) = UNCACHED(gfx_handed) + 1;
            SLAVE_WAKE = 0xffff;
#ifdef SAT_CPU_SLACK_PROFILE
            cpu_slack_handoff(UNCACHED(gfx_handed), frt());
#endif
            if (!held) sat_gfx_snapshot_layers();
#ifdef SAT_CPU_SLACK_PROFILE
            cpu_slack_layers(frt());
#endif
        }
        sat_audio_frame();
        game_done = 1;
#ifdef SAT_CPU_SLACK_PROFILE
        cpu_slack_irq(frt(), 1);
#endif
        return;
    }
#endif
    /* Before the IRQ body, which moves the next frame's scroll words into place. A slave still drawing skips this frame's picture, never the game. */
#if defined(SAT_GUESTS) && defined(SAT_WV_REVEAL) && !SAT_VDP1_HW_ERASE
    if (REVEAL_ON) {
        /* the reveal's picture: nothing for the slave to draw */
    } else
#endif
    if (UNCACHED(gfx_done) == UNCACHED(gfx_handed)) {
        sat_gfx_snapshot_begin();
        UNCACHED(gfx_handed) = UNCACHED(gfx_handed) + 1;
        SLAVE_WAKE = 0xffff;
        DIAG_AT(6);
#ifdef SAT_CPU_SLACK_PROFILE
        cpu_slack_handoff(UNCACHED(gfx_handed), frt());
#endif
        sat_gfx_snapshot_layers();   /* the slave builds the sprite commands meanwhile and waits for this before it reads a layer cell */
        DIAG_AT(7);
#ifdef SAT_CPU_SLACK_PROFILE
        cpu_slack_layers(frt());
#endif
    } else
        sat_dbg.gfx_skips++;
    t1 = frt();
    save = cpu;
    cur = -1; cpu.a[5] = 0xff8000; cpu.a[7] = 0xff8000;
    DIAG_AT(8);
    f_e0e();
    cpu = save; cur = sc;
    DIAG_AT(9);
    sat_audio_frame();
    DIAG_AT(10);
    t2 = frt();
    sat_dbg.snap_ticks = t1 - t0; sat_dbg.irq_ticks = t2;
    if (t1 - t0 > sat_dbg.snap_peak) sat_dbg.snap_peak = t1 - t0;
#ifdef SAT_PROF
    if (IN_WINDOW) { prof_add(sat_prof.snap, t1 - t0); sat_prof.skipped = sat_dbg.gfx_skips; }
#endif
    if (t2 > sat_dbg.irq_peak) sat_dbg.irq_peak = t2;
    sat_dbg.ff8018 = RAM16(0x8018);
    if ((sat_dbg.vblanks & 63) == 0) stack_scan();
#ifdef SAT_CPU_SLACK_PROFILE
    cpu_slack_irq(frt(), 0);
#endif
}

void sat_map_page(u32 page, u8 *base) { PAGE[page & 0xff] = base; }

static const u8 hw_test_seed[16] = {
#include "seed.inc"
};

extern u32 sat_bss_start[], sat_bss_end[], sat_lw_bss_start[], sat_lw_bss_end[];
#ifdef SAT_HOME
static int home_slave_on __attribute__((section(".data")));
void sat_main(void);
/* Quit to title: the game starts over from its boot, front end file included; settings in save_block (initialised data) stay. */
void sat_home_restart(void)
{
    __asm__ volatile ("ldc %0,sr" : : "r"(0xf0));
#if SAT_VDP1_HW_ERASE
    /* sat_main clears the erase bookkeeping before its initial CD load. */
    if (!sat_gfx_erase_suspend())
    {
        __asm__ volatile ("ldc %0,sr" : : "r"(0x00));
        return;
    }
#endif
    while (UNCACHED(gfx_done) != UNCACHED(gfx_handed)) ;
    *(volatile u32 *)0x25fe00a4 = 0;
    cur = -1; round_loaded = -1;
    __asm__ volatile ("mov %0,r15\n jmp @%1\n nop" : : "r"(sat_boot_stack + 2048), "r"(sat_main));
    for (;;) ;
}
#endif
void sat_main(void)
{
    u32 *p; int i;
    __asm__ volatile ("ldc %0,sr" : : "r"(0xf0));
    for (p = sat_bss_start; p < sat_bss_end; p++) { if (p >= sat_boot_stack && p < sat_boot_stack + 2048) continue; *p = 0; }
#ifdef SAT_HOME   /* a restart runs this with the slave already up, on this stack */
    for (p = sat_lw_bss_start; p < sat_lw_bss_end; p++) { if (p >= sat_slave_stack && p < sat_slave_stack + 256) continue; *p = 0; }
#else
    for (p = sat_lw_bss_start; p < sat_lw_bss_end; p++) *p = 0;
#endif
    sat_dbg.magic = 0x53415452;
    diag_call(0, 0, 0);   /* the loader's band: the runtime is entered */
    exceptions_install();
    for (i = 0; i < TASKS; i++) { u32 k; for (k = 0; k < TASK_STACK / 4; k++) task_stacks[i][k] = 0xa5a5a5a5u; }
    for (i = 0; i < 256; i++) PAGE[i] = SAT_SINK;
    PAGE[0x90] = sat_gfxram; PAGE[0x91] = sat_gfxram + 0x10000;   /* the game uses only these two of the three pages */
    for (i = 0; i < 0x20; i++) PAGE[i] = ROMB + ((u32)i << 16);
    PAGE[0xff] = RAMB; PAGE[0x70] = SAT_OBJ - 0x8000;
    { u32 n; for (n = 0; n < 0x4000; n++) SAT_OBJ[n] = 0xff; }
    { u32 n; for (n = 0; n < 0x10000; n++) SAT_SINK[n] = 0; }
    for (i = 0; i < 16; i++) RAMB[0xe90 + i] = hw_test_seed[i];
    /* Registers the skipped hardware test left, seen through f_1a36. */
    cpu.d[3] = 4; cpu.a[4] = 0x800; cpu.a[7] = 0xff8000; cpu.a[5] = 0xff8000;
    FTCR = 2;
    game_done = 1;
#ifdef SAT_FREEPLAY_ONLY   /* test flag: the game's free play coinage; its paths are outside the census, 0xe2 fatal on stage 02 */
    save_block[0] = 9; save_block[0x30] = 9;
#endif
#ifdef SAT_GUESTS
    i = sat_guest_file(0, 0, 0, 0);   /* the front end's file for the bonus characters setting */
    load_round(i);
    round_loaded = i;
    sat_guest_loaded(0, 0, 0, i);
#else
    load_round(0);
    round_loaded = 0;
#endif
    diag_call(0, 0, 0);   /* first round file and sound set done */
    if (!sat_gfx_init(SAT_PACK)) sat_fatal(0xeb, 0);
    diag_call(4, 0, 0);   /* graphics init cleared VRAM and the registers: the loader's display comes back */
    diag_call(0, 0, 0);
#ifdef SAT_HOME
    if (!home_slave_on) { home_slave_on = 1; slave_start(); }
#else
    slave_start();
#endif
    diag_call(0, 0, 0);   /* slave started */
    sat_dbg.stage = 1;
    f_800();
    sat_fatal(0xe8, 0);
}
