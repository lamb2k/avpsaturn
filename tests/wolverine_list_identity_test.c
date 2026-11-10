/* Synthetic HOST check: the object-list pass of the guest must give the same list and palette bytes whichever of the speed switches
   (SAT_GUEST_FAST_LIST, SAT_GUEST_FOLD, SAT_GUEST_NAMES_LAZY) are compiled in. Prints a dump; the Python test compares the dumps of several builds. */
#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include "../saturn/guests/wolverine/wolverine.c"

u8 RAMB[65536];
u8 *PAGE[256];
u8 sat_guest_sel;
int sat_guest_pal_keep;
#if !SAT_GUEST_NAMES_LAZY
struct sat_rounds_s { u32 current, loads, sectors, last_vblank; };
#endif
struct sat_rounds_s sat_rounds;
static u32 rng = 12345;
static u32 rnd(void) { rng = rng * 1664525u + 1013904223u; return rng >> 8; }

int main(void)
{
    static u8 obj[8 * 1024], pal[1024];
    int t, i, count, max;
    void *rom = mmap((void *)0x02400000u, 0x200000, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED_NOREPLACE, -1, 0);
    if (rom == MAP_FAILED) return 2;
    PAGE[0xff] = RAMB;
    sat_guest_sel = 1;
    wv_reset(0); wv_reset(1);
    R8(PL(0)) = 1; R8(PL(0) + WV_CHAR_OFF) = WV_CHAR_SCH;
    for (t = 0; t < 400; t++) {
        unsigned sx;
        R16(PL(0) + 0x10) = (u16)(rnd() & 0x3ff);
        R16(0xff8278) = (u16)(rnd() & 0x3ff);
        R16(0xff827c) = 0x100;
        R8(PL(0) + 0x0f) = (u8)(rnd() & 1);
        wv_step_now[0] = (u16)(rnd() % wv_move_start[WV_MOVES]);
        sat_rounds.loads = (u32)(t / 50);
        count = (int)(rnd() % (t % 7 == 0 ? 600 : 100));
        max = (t % 5 == 0) ? count + (int)(rnd() % 40) : 1024;
        sx = (unsigned)((int)R16(PL(0) + 0x10) - (int)R16(0xff8278) + WV_OX);
        for (i = 0; i < count; i++) {
            unsigned x = (rnd() % 3 == 0) ? (unsigned)((int)sx + (int)(rnd() % 320) - 160) & 0x3ff : rnd() & 0x3ff;
            u8 *e = obj + i * 8;
            e[0] = (u8)(x >> 8); e[1] = (u8)x; e[2] = (u8)(rnd() & 3); e[3] = (u8)rnd();
            e[4] = (u8)rnd(); e[5] = (u8)rnd(); e[6] = (u8)rnd();
            e[7] = (u8)((rnd() % 3 == 0 ? WV_SCH_PAL : rnd() % 32) | (rnd() & 0xe0));
        }
        for (i = 0; i < 1024; i++) pal[i] = (u8)(rnd() & 0xff);
        i = sat_guest_objects(obj, count, max, pal);
        printf("%d %d %d %d\n", t, count, max, i);
        { int k; for (k = 0; k < i * 8; k++) printf("%02x", obj[k]); printf("\n"); for (k = 0; k < 1024; k++) printf("%02x", pal[k]); printf("\n"); }
    }
    return 0;
}
