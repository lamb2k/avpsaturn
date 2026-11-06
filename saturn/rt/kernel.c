/* Master SH-2 kernel for the lifted 68000 game: the board's cooperative task scheduler, traps and level 2 IRQ, natively.
   Task records stay in game RAM at their original offsets, big-endian, because the game reads them. As on the board a task
   keeps only SR, PC and USP: d0-d7/a0-a6 stay global, so a switch swaps only the C stack. Source: kernel at 0xd86, traps from 0xf00. */
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
typedef signed char s8; typedef short s16; typedef int s32;
typedef struct { u32 d[8]; u32 a[8]; u32 ccz, ccn, ccc, ccv, ccx; } Cpu;
#include "lift_target.h"
#include "sat_rt.h"

Cpu sat_cpu;
u8 *PAGE[256];
u8 RAMB[0x10000] __attribute__((aligned(4)));
SatDebug sat_dbg;
volatile unsigned long sat_readout[3];   /* FRT ticks, game and drawing, for the SAT_READOUT bars */

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
#define r32(a) w2_rd32(RAMB + O(a))
#define w8(a, v) (RAM8(O(a)) = (u8)(v))
#define w16(a, v) (RAM16(O(a)) = (u16)(v))
#define w32(a, v) w2_wr32(RAMB + O(a), (v))
#define cpu (*R)

extern void sat_switch(void **save_sp, void *load_sp);
extern void sat_vblank_entry(void);
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

void sat_fatal(u32 code, u32 detail)
{
    __asm__ volatile ("ldc %0,sr" : : "r"(0xf0));
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
static void free_push(u32 r) { u32 p = r32(G_FREEP) - 4; w32(p, r); w32(G_FREEP, p); w16(G_FREEN, r16(G_FREEN) + 1); }
#define LOWW(reg, v) ((reg) = ((reg) & 0xffff0000u) | ((v) & 0xffff))

void f_trap0(void) { u32 r = 0xff0058u + (cpu.d[0] & 0xffff); cpu.a[1] = 0xff0058u; if (r8(r) == 0) { w16(r, 0xc00); w32(r + 4, cpu.a[0]); w16(r + 0x10, cpu.d[1]); w16(r + 0x12, cpu.d[2]); } }
void f_trap10(void) { u32 r = 0xff0058u + (cpu.d[0] & 0xffff); cpu.a[1] = 0xff0058u; w16(r, 0xc00); w32(r + 4, cpu.a[0]); w16(r + 0x10, cpu.d[1]); w16(r + 0x12, cpu.d[2]); }
void f_trap7(void)
{
    if (r16(G_FREEN)) {
        u32 p = r32(G_FREEP), r = r32(p);
        cpu.a[6] = p + 4; cpu.a[1] = r; w32(G_FREEP, p + 4); w16(G_FREEN, r16(G_FREEN) - 1);
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
    u32 tag = r8(0xff81b3); int i;
    w8(0xff81b3, 0);
    for (i = 8; i < 16; i++) { u32 r = REC(i); if (r8(r) && r8(r + 0x16) == tag) { clear_rec(r); free_push(r); } }
}
void f_trap11(void) { } void f_trap12(void) { } void f_trap13(void) { } void f_trap14(void) { } void f_trap15(void) { }

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
        LOWW(cpu.d[1], 8);
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
    { u32 v = 0x06000000; __asm__ volatile ("ldc %0,vbr" : : "r"(v)); }
    *(volatile u32 *)0x25fe00a4 = 0;            /* clear pending */
    *(volatile u32 *)0x25fe00a0 = 0xfffffffeu;  /* only vblank-in */
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
static u32 gfx_handed, gfx_done;
u32 sat_slave_stack[256] __attribute__((section(".lwgfx")));

void sat_slave_main(void)
{
    CCR = 0x10; CCR = 0x01;
    FTCR = 2;
    for (;;) {
        u32 t, seen;
        while (!(FTCSR & 0x80)) ;
        FTCSR = (u8)(FTCSR & 0x7f);
        CCR = 0x11;
        seen = UNCACHED(gfx_handed);
        if (seen == UNCACHED(gfx_done)) continue;
        FRTH = 0; FRTL = 0;
        sat_gfx_draw();
        t = frt();
        sat_dbg.gfx_ticks = t; *(volatile unsigned long *)((unsigned long)&sat_readout[1] | 0x20000000UL) = t;
        if (t > sat_dbg.gfx_peak) sat_dbg.gfx_peak = t;
#ifdef SAT_PROF
        if (IN_WINDOW) prof_add(sat_prof.gfx, t);
#endif
        UNCACHED(gfx_done) = seen;
    }
}

static void slave_start(void)
{
    while (SMPC(0x63) & 1) ;
    SMPC(0x63) = 1; SMPC(0x1f) = 0x03;   /* SSHOFF */
    while (SMPC(0x63) & 1) ;
    *(void (**)(void))0x06000250u = sat_slave_entry;
    *(u32 *)0x060002acu = (u32)(sat_slave_stack + 256);
    SMPC(0x63) = 1; SMPC(0x1f) = 0x02;   /* SSHON */
    while (SMPC(0x63) & 1) ;
}

/* Dispatcher 0xd86. A vblank sets the game's flag at 0xff0266 through f_e0e, which restarts the walk from task 0. */
void f_d86(void)
{
    if (!irq_on) irq_enable();
    sat_dbg.stage = 2;
#ifdef SAT_PROF_PC
    pc_start();
#endif
    for (;;) {
        int i;
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
#ifdef SAT_PROF
                if (IN_WINDOW) { prof_add(sat_prof.frame, frame_carry + sat_dbg.game_ticks); sat_prof.done++; }
                frame_carry = 0;
#endif
            }
            cpu.a[0] = REC(15) + 0x20; cpu.d[0] |= 0xffff; f_11ec(); sat_dbg.idle_calls++;
        }
    }
}

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
    *(volatile u32 *)0x25fe00a4 = ~1u;
    sat_dbg.vblanks++;
    if (!game_done) sat_dbg.overruns++;
#ifdef SAT_PROF
    sat_prof.from = PROF_FROM; sat_prof.to = PROF_TO;
    if (IN_WINDOW) { sat_prof.ticks++; if (!game_done) sat_prof.over++; }
    if (!game_done) frame_carry += frt();
#endif
    game_done = 0;
    FRTH = 0; FRTL = 0;
#ifdef SAT_PROF_PC
    pc_arm(200 + (sat_dbg.vblanks * 37) % PC_STEP);
#endif
    sat_pad_tick();
    t0 = frt();
    /* Before the IRQ body, which moves the next frame's scroll words into place. A slave still drawing skips this frame's picture, never the game. */
    if (UNCACHED(gfx_done) == UNCACHED(gfx_handed)) {
        sat_gfx_snapshot();
        UNCACHED(gfx_handed) = UNCACHED(gfx_handed) + 1;
        SLAVE_WAKE = 0xffff;
    } else
        sat_dbg.gfx_skips++;
    t1 = frt();
    save = cpu;
    cur = -1; cpu.a[5] = 0xff8000; cpu.a[7] = 0xff8000;
    f_e0e();
    cpu = save; cur = sc;
    sat_audio_frame();
    t2 = frt();
    sat_dbg.snap_ticks = t1 - t0; sat_dbg.irq_ticks = t2;
    if (t1 - t0 > sat_dbg.snap_peak) sat_dbg.snap_peak = t1 - t0;
#ifdef SAT_PROF
    if (IN_WINDOW) { prof_add(sat_prof.snap, t1 - t0); sat_prof.skipped = sat_dbg.gfx_skips; }
#endif
    if (t2 > sat_dbg.irq_peak) sat_dbg.irq_peak = t2;
    sat_dbg.ff8018 = RAM16(0x8018);
    if ((sat_dbg.vblanks & 63) == 0) stack_scan();
}

void sat_map_page(u32 page, u8 *base) { PAGE[page & 0xff] = base; }

static const u8 hw_test_seed[16] = {
#include "seed.inc"
};

static const u8 sat_audio_tables[] __attribute__((aligned(4))) = {
#include "audio_tables.inc"
};
extern int sat_audio_clips_loaded;
extern u32 sat_bss_start[], sat_bss_end[], sat_lw_bss_start[], sat_lw_bss_end[];
void sat_main(void)
{
    u32 *p; int i;
    __asm__ volatile ("ldc %0,sr" : : "r"(0xf0));
    for (p = sat_bss_start; p < sat_bss_end; p++) { if (p >= sat_boot_stack && p < sat_boot_stack + 2048) continue; *p = 0; }
    for (p = sat_lw_bss_start; p < sat_lw_bss_end; p++) *p = 0;
    sat_dbg.magic = 0x53415452;
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
    if (!sat_gfx_init(SAT_PACK)) sat_fatal(0xeb, 0);
    sat_audio_clips_loaded = 1;   /* the loader put them in SCSP RAM */
    if (!sat_audio_init(sat_audio_tables)) sat_fatal(0xec, 0);
    slave_start();
    sat_dbg.stage = 1;
    f_800();
    sat_fatal(0xe8, 0);
}
