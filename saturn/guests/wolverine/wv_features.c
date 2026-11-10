/* Wolverine features (lane wv-features, 2026-11-09). Cart code, SAT_GUESTS builds with Wolverine only; every part is its own default-off switch and
   without the switches this file is not compiled and the image is byte-identical.

   Hooks (no edit to wolverine.c or game_bind.c): saturn/rt/build.py compiles wolverine.c with
     -Dsat_guest_wolverine_tick=wv_tick_inner (SAT_WV_HEAL) and -Dsat_guest_wolverine_pad=wv_pad_inner (SAT_WV_FLASH)
   so the game's calls (game_bind.c f_195ec once a player update, pad.c once a vblank) reach the wrappers below, which call his code and then ours.

   -DSAT_WV_HEAL            healing factor. Wolverine regains health slowly while nothing hurts him.
       -DSAT_WV_HEAL_DELAY=180  ticks without any drop of his health before it starts (3 s)
       -DSAT_WV_HEAL_STEP=30    ticks between points once it runs (2 points a second)
       -DSAT_WV_HEAL_AMT=1      points each step
     Any drop of his health restarts the delay, whatever its cause (a hit, a grab's damage, the Berserker cost charged by the game on connect), so
     Berserker is never free. Healing runs only on a tick where his state is 020000..020006 / 02000x with substate 0 (stand, walk, jump, attacks,
     Berserker, special), in the running stage (route byte ff8001 = 2), not attract (ff81b0), not after the stage or boss clear (ff81f3, ff822a),
     with health between 0 and 100. The pause menu holds the game, so no tick runs; a hit (0202), a grab (0204), getting up (0208), the dying and
     continue states (04, 08) reset the delay. State: 4 bytes. Health is written to +0x40 and +0x42 (the HUD's latched value) as pickup_heal does,
     so the bar simply rises.

   -DSAT_WV_FLASH[=1|2]     Berserker super moment (needs SAT_WV_NATIVE_GFX: the events come from wolverine.c's wv_on_berserker_* hooks).
       1 (default): when the move starts; 2: at its first contact.
       -DSAT_WV_FLASH_FREEZE=12 ticks every tag-0c enemy block (ff9a00.., stride 0x100: Ganados, aliens, bosses) stands still: the game's own hitstop byte
                                +0x2c, set only on blocks where it is zero, so a hit enemy's own count is never cut short or lengthened. The game's box test
                                refuses a defender with +0x2c set, so contacts wait for the thaw; he, a partner and everything not in those pools run on.
       -DSAT_WV_FLASH_HOLD=1    also hold his own player update for the same ticks (the game's f_195ec is skipped, as the old attack hold does): the move's clock
                                stops with the world and thaws with it, so no contact is lost to the freeze. Default 0: he runs through the freeze.
       -DSAT_WV_FLASH_FRAMES    vblank table of VDP2 colour offset values (9 bit signed, all colour layers, +255 = white); default 4 frames: -24 -24 +144 +64
   Sound: if the sounds lane provides wv_sfx(id) and -DWV_SFX_BERSERKER=<id> is given, the move's start calls it (one hook point). */
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32; typedef short s16;

extern u8 RAMB[];
extern unsigned char sat_guest_sel;
#define R8(a) (*(volatile u8 *)(RAMB + ((a) - 0xff0000u)))
#if defined(__BYTE_ORDER__) && __BYTE_ORDER__ == __ORDER_BIG_ENDIAN__
#define R16(a) (*(volatile u16 *)(RAMB + ((a) - 0xff0000u)))
#define W16(a, v) (R16(a) = (u16)(v))
#else   /* HOST runner: RAMB holds the 68000's bytes */
#define R16(a) ((u16)(RAMB[(a) - 0xff0000u] << 8 | RAMB[(a) - 0xff0000u + 1]))
#define W16(a, v) (RAMB[(a) - 0xff0000u] = (u8)((v) >> 8), RAMB[(a) - 0xff0000u + 1] = (u8)(v))
#endif
#define PL(i) (0xff8380u + (u32)(i) * 0x100u)
/* The game's enemy pool (tag 0x0c: Ganados, aliens; source_recon/avsrc_actor.c POOLS): 20 slots of 0xc0 bytes from ff9580. (wolverine.c's wv_enemy_hp walks ff9a00 in steps of 0x100, which is not
   this pool's grid: it sees one block in three.) The tag 0x08 pool (ff9280, bosses) is left alone. */
#define EN_FIRST 0xff9580u
#define EN_N 20
#define EN_STRIDE 0xc0u
/* The state lives in the cart (the .data of the cart tail, RAM on the RAM cartridge), not in low work RAM: the linker script puts every .bss there and lw_free is 32 bytes. */
#define CARTVAR __attribute__((section(".data")))

#ifdef WVF_HOST   /* HOST runner only (tools/lift_runner/build_native_host.py --wvf 1): WVFTRACE=file, one line per Wolverine player update */
#include <stdio.h>
#include <stdlib.h>
extern long host_vblank;
static void wvf_log(const char *what, int i, int a, int b)
{
    static FILE *f; static int init;
    if (!init) { const char *e = getenv("WVFTRACE"); init = 1; if (e) f = fopen(e, "w"); }
    if (f) fprintf(f, "%ld %s %d %d %d\n", host_vblank, what, i, a, b);
}
static void wvf_enemies(void)   /* per tick: health of the 20 slots of the enemy pool, -1 for a free slot (damage is read off the drops) */
{
    static FILE *f; static int init, k; u32 b;
    if (!init) { const char *e = getenv("WVFEN"); init = 1; if (e) f = fopen(e, "w"); }
    if (!f) return;
    fprintf(f, "%ld", host_vblank);
    for (k = 0, b = 0xff9580u; k < 20; k++, b += 0xc0u) fprintf(f, " %d", RAMB[b - 0xff0000u] && RAMB[b - 0xff0000u + 8] == 0x0c ? (RAMB[b - 0xff0000u + 0x40] << 8 | RAMB[b - 0xff0000u + 0x41]) : -1);
    fprintf(f, "\n");
}
#else
#define wvf_log(w, i, a, b) ((void)0)
#define wvf_enemies() ((void)0)
#endif
#if defined(SAT_WV_HEAL) || defined(WVF_HOST) || (defined(SAT_WV_FLASH) && SAT_WV_FLASH_HOLD)
extern int wv_tick_inner(unsigned long a6);
#endif
#ifdef SAT_WV_FLASH
extern void wv_pad_inner(u16 *in0);
#endif

#ifdef SAT_WV_HEAL
#ifndef SAT_WV_HEAL_DELAY
#define SAT_WV_HEAL_DELAY 180
#endif
#ifndef SAT_WV_HEAL_STEP
#define SAT_WV_HEAL_STEP 30
#endif
#ifndef SAT_WV_HEAL_AMT
#define SAT_WV_HEAL_AMT 1
#endif
#if SAT_WV_HEAL_DELAY > 255 || SAT_WV_HEAL_STEP > SAT_WV_HEAL_DELAY || SAT_WV_HEAL_STEP < 1 || SAT_WV_HEAL_AMT < 1
#error SAT_WV_HEAL_DELAY 1..255, SAT_WV_HEAL_STEP 1..DELAY, SAT_WV_HEAL_AMT >= 1
#endif
#define WV_HP_FULL 101   /* the game's maximum (0x65, pickup_heal's cap) */
static u8 hl_t[2] CARTVAR, hl_hp[2] CARTVAR;   /* ticks since his health last fell (the delay counts up, then the step); health seen last tick */
static void wv_heal(int i)
{
    u32 b = PL(i);
    int hp = (s16)R16(b + 0x40);
    int ok = R8(b) && R8(b + 4) == 2 && R8(b + 5) == 0 && R8(0xff8001) == 2 && !R8(0xff81b0) && !R8(0xff81f3) && !R8(0xff822a) && hp >= 0 && hp < WV_HP_FULL;
    if (hp < hl_hp[i] || !ok) hl_t[i] = 0;   /* a drop of any kind restarts the delay */
    else if (++hl_t[i] >= SAT_WV_HEAL_DELAY) {
        hl_t[i] = SAT_WV_HEAL_DELAY - SAT_WV_HEAL_STEP;
        hp += SAT_WV_HEAL_AMT;
        if (hp > WV_HP_FULL) hp = WV_HP_FULL;
        W16(b + 0x40, hp);
        W16(b + 0x42, hp);
    }
    hl_hp[i] = (u8)(hp < 0 ? 0 : hp > 255 ? 255 : hp);
    wvf_log("t", i, R8(b + 4) << 16 | R8(b + 5) << 8 | R8(b + 6), hp << 8 | hl_t[i]);
}
#endif

#ifdef SAT_WV_FLASH
#if !defined(SAT_WV_NATIVE_GFX) && !defined(WVF_HOST)
#error SAT_WV_FLASH needs SAT_WV_NATIVE_GFX (the Berserker events)
#endif
#if SAT_WV_FLASH + 0 == 0
#undef SAT_WV_FLASH
#define SAT_WV_FLASH 1
#endif
#ifndef SAT_WV_FLASH_FREEZE
#define SAT_WV_FLASH_FREEZE 12
#endif
#ifndef SAT_WV_FLASH_HOLD
#define SAT_WV_FLASH_HOLD 0
#endif
#ifndef SAT_WV_FLASH_FRAMES
#define SAT_WV_FLASH_FRAMES 0x1e8, 0x1e8, 0x090, 0x040   /* -24 -24 +144 +64: two dim frames, then a bright pop (MSHvSF's hyper: two frames at 78 % brightness, then the cut-in) */
#endif
#define VDP2R(o) (*(volatile u16 *)(0x25F80000UL + (o)))
static const u16 fl_tab[] = { SAT_WV_FLASH_FRAMES };
#define FL_N ((int)(sizeof fl_tab / sizeof fl_tab[0]))
static u8 fl_left CARTVAR, fl_done CARTVAR;   /* vblanks of flash still to show; 1 = this burst has had its moment */
#if SAT_WV_FLASH_HOLD
static u8 fz_left CARTVAR;   /* updates of his own still to skip; bit 7 = player index */
#endif
#ifdef WV_SFX_BERSERKER
extern void wv_sfx(int id) __attribute__((weak));
#endif
static void wv_super(int who)
{
    u32 b;
    if (fl_done) return;
    fl_done = 1;
    fl_left = FL_N;
    wvf_log("super", who, 0, 0);
#if SAT_WV_FLASH_HOLD
    fz_left = (u8)(SAT_WV_FLASH_FREEZE | (who << 7));
#else
    (void)who;
#endif
    if (SAT_WV_FLASH_FREEZE > 0)
        for (b = EN_FIRST; b < EN_FIRST + EN_N * EN_STRIDE; b += EN_STRIDE)
            if (R8(b) && R8(b + 8) == 0x0c && !R8(b + 0x2c)) R8(b + 0x2c) = SAT_WV_FLASH_FREEZE;
#ifdef WV_SFX_BERSERKER
    if (wv_sfx) wv_sfx(WV_SFX_BERSERKER);
#endif
}
void wv_on_berserker_start(int i) { fl_done = 0; if (SAT_WV_FLASH == 1) wv_super(i); else (void)i; }   /* a start is always a new move, whatever became of the last one's end */
void wv_on_berserker_connect(int i, int damage) { (void)i; (void)damage; if (SAT_WV_FLASH == 2) wv_super(i); }
void wv_on_berserker_end(int i) { (void)i; fl_done = 0; }
#if !defined(SAT_WV_NATIVE_GFX)   /* HOST test only (the native build gets these events from wolverine.c): his state 02000c, edge and enemies' health */
static u8 hs_on CARTVAR;
static u16 hs_hp CARTVAR;
static void wv_host_events(int i)
{
    int in = R8(PL(i) + 4) == 2 && R8(PL(i) + 5) == 0 && R8(PL(i) + 6) == 0x0c;
    u32 b; u16 t = 0;
    for (b = EN_FIRST; b < EN_FIRST + EN_N * EN_STRIDE; b += EN_STRIDE) if (R8(b) && R8(b + 8) == 0x0c) t = (u16)(t + R16(b + 0x40));
    if (in) { if (!hs_on) { hs_on = 1; wv_on_berserker_start(i); } else if (t < hs_hp) wv_on_berserker_connect(i, hs_hp - t); hs_hp = t; }
    else if (hs_on) { hs_on = 0; wv_on_berserker_end(i); }
}
#endif
static void wv_flash_vblank(void)   /* once a vblank: the colour offset (enable: every layer, offset A) follows the table, then off */
{
    if (fl_left) {
        u16 v = fl_tab[FL_N - fl_left] & 0x1ff;
        VDP2R(0x110) = 0x007f; VDP2R(0x112) = 0;
        VDP2R(0x114) = v; VDP2R(0x116) = v; VDP2R(0x118) = v;
        fl_left--;
    } else if (VDP2R(0x110)) {
        VDP2R(0x110) = 0;
        VDP2R(0x114) = VDP2R(0x116) = VDP2R(0x118) = 0;
    }
}
#endif

#if defined(SAT_WV_HEAL) || defined(WVF_HOST) || (defined(SAT_WV_FLASH) && SAT_WV_FLASH_HOLD)
/* f_195ec's pre-hook: every player update (a6 = the player's block). Returns his answer (0 = skip this update). */
int sat_guest_wolverine_tick(unsigned long a6)
{
    int r;
#if defined(SAT_WV_FLASH) && SAT_WV_FLASH_HOLD
    if ((fz_left & 0x7f) && (a6 == PL(0) || a6 == PL(1)) && (int)((a6 - PL(0)) >> 8) == (fz_left >> 7)) { fz_left--; return 0; }
#endif
    wvf_enemies();
    r = wv_tick_inner(a6);
#if defined(SAT_WV_FLASH) && !defined(SAT_WV_NATIVE_GFX)
    if ((a6 == PL(0) || a6 == PL(1)) && (sat_guest_sel & 1) && R8(a6 + 1) == 1) wv_host_events((int)((a6 - PL(0)) >> 8));
#endif
#ifdef SAT_WV_HEAL
    if (a6 == PL(0) || a6 == PL(1)) {
        int i = (int)((a6 - PL(0)) >> 8);
        if ((sat_guest_sel & 1) && R8(a6 + 1) == 1) wv_heal(i);
        else hl_t[i] = 0;
    }
#endif
    return r;
}
#endif

#ifdef SAT_WV_FLASH
/* pad.c's once-a-vblank call */
void sat_guest_wolverine_pad(u16 *in0)
{
    wv_pad_inner(in0);
    wv_flash_vblank();
}
#endif
