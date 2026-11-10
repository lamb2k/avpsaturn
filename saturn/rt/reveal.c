/* The post-credits Wolverine reveal (SAT_GUESTS builds with the reveal art, SAT_WV_REVEAL). An OVERLAY, not resident code (owner 11-10: the resident cost near zero, the cart step kept):
   build.py links this file at 0x02750000 (SAT_PACK + 0xFC000, in the cart's pack room, past stage 26's and the front end's tile packs) against the finished sat.elf and writes it to the disc as
   REVCODE.BIN. The only resident pieces are a flag test in the vblank (kernel.c) and, in cart cold code, sat_reveal_poll and sat_reveal_call (guests.c). At the ending the poll reads REVCODE.BIN into
   0x02750000 and calls begin through the table at its head; after that it calls step each frame until the card ends. Nothing of it stays: the room is the pack's.
   It replaces the GAME OVER card after the epilogue. The card is stage word 0x26 with ff8005 = 8 (EMULATOR, Yaba 11-09: ff8005 is 10 through the ending, 8 for the card's 432 vblanks,
   14 once the stage word is 0 and the ranking is up). The game keeps running through it; its own card timer is the reveal's hold, so the front end follows at the arcade's moment.
   The reveal owns the picture meanwhile (takeover below: the vblank hands the slave nothing). VDP2 NBG0 shows a 512 x 256, 8 bit bitmap: frame 1 in bank A1 (0x20000),
   frame 2 in B0 (0x40000), frame 3 in B1 (0x60000), the palette in CRAM 0, the zoom of SAT_GFX_FIT (384 pixels on 352) or its 16 pixel crop, sprites off (priority 0), black outside the picture rows.
   The art (REVEAL.BIN) and the voice (RVVOICE.BIN) are read into the pack room one megabyte into the stage's pack (SAT_PACK + 0x100000), copied into VDP2 VRAM and SCSP RAM, and the room is free again.
   The chips go back to the game with sat_gfx_init: every cache empty, so each tile loads again.
   Plays only when it has not played before and Wolverine is OFF (owner 11-10; the poll tests that); otherwise the stock card follows.
   Timing, vblanks (60 a second): frame 1 for 90, frame 2 for 90, frame 3 until the card ends (about 250, so about 1.5 s, 1.5 s, 4.2 s of the card's 7.2 s). The voice starts with frame 3.
   After frame 1 is up, the first time the reveal plays, Wolverine is switched on if he is off and that is written to backup RAM (boot.c unlock_io); later endings leave the player's setting alone. */
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
#include "../gfx/sat_gfx.h"
#include "unlock_save.h"
extern u8 RAMB[];
extern u32 sat_vblanks_now(void);
extern long sat_reveal_call(int which, u32 a, u32 b, u32 c);
extern int sat_gfx_init(const void *pack);
extern unsigned char sat_guest_sel;
extern u32 gfx_done, gfx_handed;              /* kernel.c: the slave's hand-off counters (global in a reveal build) */
#define UNCACHED(v) (*(volatile u32 *)((u32)&(v) | 0x20000000u))
#define UNLOCK_FLAGS (*(volatile u32 *)0x06013fdcu)
extern u8 SAT_PACK[];
#ifdef SAT_HOME
extern int sat_gfx_nudge_x, sat_gfx_nudge_y;
#define NUDGE_X sat_gfx_nudge_x
#define NUDGE_Y sat_gfx_nudge_y
#else
#define NUDGE_X 0
#define NUDGE_Y 0
#endif
#define G(a) RAMB[(a) - 0xff0000u]
#define DIAG ((volatile u32 *)0x06013fe0u)   /* [5] takeover (kernel.c tests it in the vblank), [6] state: 0 idle, 1 to 3 frame showing, 4 done until the ending is left; boot.c clears both */
#define BUF ((u8 *)0x02754000u)              /* SAT_PACK + 1 MB, in the pack room, beyond stage 26's pack */
#define V2(o) (*(volatile u16 *)(0x25F80000UL + (o)))
#define VRAM32 ((volatile u32 *)0x25E00000UL)
#define CRAM16 ((volatile u16 *)0x25F00000UL)
#define SCSP_RAM ((volatile u16 *)0x25A00000UL)
#define SLOT(n, r) (*(volatile u16 *)(0x25B00000UL + 0x20UL * (n) + (r)))
#define VOICE_AT 0x70000UL                   /* SCSP RAM: stage 26's clips end near 0x55000 */
#define VOICE_SLOT 18                        /* 0 to 15 are the sound channels, 16 and 17 the CD */
#define T_FRAME2 90u
#define T_FRAME3 180u
#define MAX_VBLANKS 900u                     /* safety: the card is 432 */
static u32 t0 = 1, voice_samples = 1, voice_tl = 1, voice_oct = 0xf;         /* initialised data: this code's bss is not cleared */
static u32 be32(const u8 *p) { return (u32)p[0] << 24 | (u32)p[1] << 16 | (u32)p[2] << 8 | p[3]; }
static void frame_up(int f) { V2(0x3c) = (u16)(1 + f); }
static void show_setup(const u8 *r)
{
    u32 i, f;
    V2(0x00) = 0x0001;                                     /* display off while the picture is built */
    V2(0x0e) = 0x1300;                                     /* four VRAM banks, CRAM mode 1 */
    V2(0x10) = 0xffff; V2(0x12) = 0xffff;                  /* A0 untouched */
    for (i = 0x14; i <= 0x1e; i += 2) V2(i) = 0x4444;      /* A1, B0, B1: every slot reads NBG0 bitmap data */
    V2(0x20) = 0x0001;                                     /* NBG0 only */
    V2(0x22) = 0; V2(0x24) = 0; V2(0x26) = 0;
    V2(0x28) = 0x0012;                                     /* NBG0: bitmap, 512 x 256, 256 colours */
    V2(0x2a) = 0; V2(0x2c) = 0; V2(0x2e) = 0;             /* palette 0 */
    V2(0x3c) = 1;                                          /* bitmap at bank A1 */
#if SAT_GFX_FIT == 1
    V2(0x78) = 1; V2(0x7a) = 0x1700; V2(0x7c) = 1; V2(0x7e) = 0; V2(0x98) = 0x0101;   /* 384 pixels on 352, as the game's layers */
    V2(0x70) = (u16)((0 - NUDGE_X) & 0x7ff);
#else
    V2(0x78) = 1; V2(0x7a) = 0; V2(0x7c) = 1; V2(0x7e) = 0; V2(0x98) = 0;
    V2(0x70) = (u16)((SAT_GFX_CROP_X - NUDGE_X) & 0x7ff);        /* the 1:1 centre crop */
#endif
    V2(0x72) = 0; V2(0x76) = 0; V2(0x9a) = 0;
    V2(0x74) = (u16)((0 - NUDGE_Y) & 0x7ff);
    for (i = 0xe2; i <= 0xee; i += 2) V2(i) = 0;
    V2(0x10a) = 0;
    V2(0xf0) = 0; V2(0xf2) = 0; V2(0xf4) = 0; V2(0xf6) = 0;   /* sprites (priority 0) off */
    V2(0xf8) = 0x0002; V2(0xfa) = 0;
    for (i = 0; i < 128; i++) CRAM16[i] = (u16)(r[24 + i * 2] << 8 | r[25 + i * 2]);
    for (i = 0x8000; i < 0x20000; i++) VRAM32[i] = 0;      /* banks A1, B0, B1 clear: outside the picture rows the back screen shows */
    *(volatile u16 *)0x25E1fffeUL = 0;                     /* the back colour, black */
    for (f = 0; f < 3; f++) {
        const u8 *rec = r + be32(r + 12 + f * 4);
        u32 first = (u32)(rec[0] << 8 | rec[1]), rows = (u32)(rec[2] << 8 | rec[3]), y;
        const u32 *src = (const u32 *)(rec + 4);
        volatile u32 *dst = VRAM32 + (0x20000UL * (1 + f) + first * 512) / 4;
        for (y = 0; y < rows; y++, dst += 128, src += 96) for (i = 0; i < 96; i++) dst[i] = src[i];   /* 384 pixels of each 512 */
    }
    V2(0x00) = 0x8001;
}
/* The voice (his round-entrance line): PCM 8 bit in SCSP RAM, one slot of its own. File: 'RVV1', u32 samples, u8 total level, u8 octave nibble (0xe 11025 Hz, 0xf 22050 Hz), 6 reserved, the samples. */
static void voice_load(const u8 *p)
{
    u32 n = be32(p + 4), i;
    for (i = 0; i < n; i += 2) SCSP_RAM[(VOICE_AT + i) >> 1] = (u16)(p[16 + i] << 8 | p[17 + i]);
}
static void voice_play(u32 samples)
{
    SLOT(VOICE_SLOT, 0x00) = (u16)(0x0010u | (VOICE_AT >> 16));
    SLOT(VOICE_SLOT, 0x02) = (u16)VOICE_AT;
    SLOT(VOICE_SLOT, 0x04) = 0; SLOT(VOICE_SLOT, 0x06) = (u16)(samples > 0xffffu ? 0xffffu : samples);
    SLOT(VOICE_SLOT, 0x08) = 0x001fu | 1u << 5; SLOT(VOICE_SLOT, 0x0a) = 0x001fu; SLOT(VOICE_SLOT, 0x0c) = (u16)voice_tl; SLOT(VOICE_SLOT, 0x0e) = 0;
    SLOT(VOICE_SLOT, 0x10) = (u16)(voice_oct << 11);       /* octave -2: 11025 Hz, -1: 22050 Hz */
    SLOT(VOICE_SLOT, 0x12) = 0; SLOT(VOICE_SLOT, 0x14) = 0;
    SLOT(VOICE_SLOT, 0x16) = (u16)(7u << 13);
    SLOT(VOICE_SLOT, 0x00) = (u16)(SLOT(VOICE_SLOT, 0x00) | 0x1800u);   /* key on, execute */
}
static void takeover(int on)
{
    DIAG[5] = (u32)on;
    if (on) while (UNCACHED(gfx_done) != UNCACHED(gfx_handed)) ;
}
/* The first time: Wolverine goes on and the setting and the flag are written in one go (the art and voice are copied out already, so the scratch is free). */
static void reveal_done(void)
{
    if (UNLOCK_FLAGS & 1u) return;
    sat_guest_sel |= 1;
    sat_reveal_call(2, 1, 1u | 0x400u | ((u32)(sat_guest_sel & 3) << 8), 0x02754000u);
}
static void begin(void)
{
    long n;
    u32 size;
    takeover(1);
    n = sat_reveal_call(1, (u32)"REVEAL.BIN", (u32)BUF, 0);
    size = be32(BUF + 4);
    if (n < 280 || BUF[0] != 'R' || BUF[1] != 'V' || BUF[2] != 'L' || BUF[3] != '1' || (u32)n < size) { takeover(0); return; }
    show_setup(BUF);
    voice_samples = 0;
    if (sat_reveal_call(1, (u32)"RVVOICE.BIN", (u32)(BUF + size), 0) > 16 && BUF[size] == 'R') {
        voice_samples = be32(BUF + size + 4);
        voice_tl = BUF[size + 8]; voice_oct = BUF[size + 9] & 15;
        if (!voice_oct) voice_oct = 0xf;                    /* a file with no octave byte (the first RVV1 layout, 8 reserved bytes) is 22050 Hz */
        voice_load(BUF + size);
    }
    reveal_done();
    t0 = sat_vblanks_now();
    DIAG[6] = 1;
}
static void finish(void)
{
    __asm__ volatile ("ldc %0,sr" : : "r"(0xf0));
    sat_gfx_init(SAT_PACK);
    takeover(0);
    __asm__ volatile ("ldc %0,sr" : : "r"(0x00));
    DIAG[6] = 4;
}
/* Called each frame while a frame is showing (DIAG[6] 1 to 3); the poll in guests.c has done the idle, seen-before and stage checks and calls begin once. */
static void step(void)
{
    u32 st = DIAG[6], t = sat_vblanks_now() - t0;
    int card = (G(0xff81e8) << 8 | G(0xff81e9)) == 0x26 && G(0xff8001) == 2 && G(0xff8005) == 8;
    if (!card || t > MAX_VBLANKS) { finish(); return; }
    if (t >= T_FRAME3 && st < 3) { frame_up(2); DIAG[6] = 3; if (voice_samples) voice_play(voice_samples); }
    else if (t >= T_FRAME2 && st < 2) { frame_up(1); DIAG[6] = 2; }
}
/* The table at the head of REVCODE.BIN (reveal_ov.ld puts .ovhead first): magic, begin, step. */
__attribute__((section(".ovhead"))) const u32 reveal_table[3] = { 0x52564331u, (u32)begin, (u32)step };
