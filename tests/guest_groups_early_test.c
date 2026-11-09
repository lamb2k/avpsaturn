/* Synthetic HOST check for SAT_GUEST_GROUPS_EARLY (saturn/rt/guests.c). No ROM bytes. Linked with guests.c and wolverine.c (built with
   -Dsat_guest_objects=sat_guest_wolverine_objects, as saturn/rt/build.py does). A scripted random scenario builds the groups the game would write in a
   frame (sat_guest_group), an object list and a palette page, optionally runs the early pass (the end of the game frame) and then the snapshot's
   sat_guest_objects. The script is the same for every build; the dump of the resulting list, count and palette must be byte-identical whether the
   early pass is compiled in or not, including the cases that must fall back (stale stamp). Counters go to stderr for the Python side. */
#define _GNU_SOURCE
#include <stdio.h>
#include <sys/mman.h>
#include <string.h>
#include "guests.h"

typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
u8 RAMB[65536];
u8 *PAGE[256];
unsigned int sat_vblank_now_value;
unsigned int sat_vblanks_now(void) { return sat_vblank_now_value; }
struct sat_rounds_s { u32 current, loads, sectors, last_vblank; } sat_rounds;
int sat_guest_pal_keep;
#if SAT_GUEST_GROUPS_EARLY
extern unsigned int sat_gearly[8];
void sat_guest_groups_early(void);
void sat_guest_groups_task(int i);
#endif
void sat_guest_group(unsigned long actor, unsigned long objptr);
int sat_guest_objects(u8 *obj, int count, int max, u8 *page0);

/* A stand-in Mega Man: draws 3 tiles derived from the arguments, so a different group split gives different bytes. */
int sat_guest_megaman_draw(u8 *out, int room, unsigned long actor, int ax, int bottom, unsigned short xhi, unsigned short ahi)
{
    int i, n = room < 3 ? room : 3;
    for (i = 0; i < n * 8; i++) out[i] = (u8)(actor + ax * 3 + bottom * 5 + xhi + ahi + i);
    return n;
}
void sat_guest_megaman_palette(u8 *page0) { page0[64] ^= 0x55; }

static u32 rng = 7;
static u32 rnd(void) { rng = rng * 1664525u + 1013904223u; return rng >> 8; }
#define R8(a) (RAMB[(a) - 0xff0000u])

static u32 shot_at[24];
static void setup_actors(void)
{
    int i;
    memset(RAMB, 0, sizeof RAMB);
    for (i = 0; i < 3; i++) {   /* player blocks 8380 8480 8580 */
        u32 b = 0x8380u + (u32)i * 0x100u;
        RAMB[b] = (u8)(rnd() % 5 ? 1 : 0);
        RAMB[b + 1] = (u8)(rnd() & 3);
        RAMB[b + 0xd2] = (u8)(rnd() & 3);
        RAMB[b + 0x10] = (u8)(rnd() & 3); RAMB[b + 0x11] = (u8)rnd();
    }
    RAMB[0x8278] = (u8)(rnd() & 3); RAMB[0x8279] = (u8)rnd();
    RAMB[0x827c] = 1; RAMB[0x827d] = 0;
    RAMB[0x81e8] = 0; RAMB[0x81e9] = (u8)(rnd() & 0x3f);
    for (i = 0; i < 24; i++) {   /* shots (tag 4, owner +0x26) in 8680..9580 and flashes (tag 0x24, owner +0x28) in e080.. */
        u32 o = (i < 16) ? 0x8680u + (u32)(rnd() % 0xe00u) : 0xe080u + (u32)(rnd() % 0xf0u), owner = 0x8380u + (u32)(rnd() % 3) * 0x100u;
        shot_at[i] = o;
        RAMB[o + 8] = (u8)(i < 16 ? 4 : 0x24);
        RAMB[o + 2] = (u8)(rnd() % 2 ? 0 : 5);
        RAMB[o + 0x26] = (u8)(owner >> 8); RAMB[o + 0x27] = (u8)(rnd() % 7 ? owner : owner + 1);   /* owner + 1: not a player block, a miss */
        RAMB[o + 0x28] = (u8)(owner >> 8); RAMB[o + 0x29] = (u8)owner;
    }
}

static u32 pick_actor(void)
{
    u32 k = rnd() % 10;
    if (k < 3) return 0xff8380u + (rnd() % 3) * 0x100u;      /* a player body */
    if (k < 8) return 0xff0000u + shot_at[rnd() % 24];       /* a shot or flash slot that was set up */
    return 0xff9000u + (rnd() % 0x2000u);                     /* anything else */
}

static void dump(const char *tag, int t, int count, const u8 *obj, const u8 *pal)
{
    int k;
    printf("%s %d %d\n", tag, t, count);
    for (k = 0; k < count * 8; k++) printf("%02x", obj[k]);
    printf("\n");
    for (k = 0; k < 1024; k++) printf("%02x", pal[k]);
    printf("\n");
}

int main(void)
{
    static u8 obj[8 * 1024], pal[1024];
    int t;
    unsigned vb = 1000;
    if (mmap((void *)0x02400000u, 0x200000, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED_NOREPLACE, -1, 0) == MAP_FAILED) return 2;   /* cart RAM, where the guest writes names */
    PAGE[0xff] = RAMB;
    for (t = 0; t < 1500; t++) {
        int ng = (int)(rnd() % 14), g, count = 0, kase = (int)(rnd() % 10), i;
        u32 at = 0;
        sat_guest_sel = (u8)(rnd() % 4 == 0 ? 3 : rnd() % 7 == 0 ? 2 : 1);
        if (rnd() % 11 == 0) sat_guest_sel = 0;
        if (t % 17 == 0) setup_actors();   /* players too: kind, presence */
        else if (t % 3 == 0) {   /* the game moved a few things */
            for (i = 0; i < 6; i++) RAMB[shot_at[rnd() % 24] + 8] = (u8)(rnd() % 3 == 0 ? 4 : rnd() % 3 == 0 ? 0x24 : rnd());
        }
        /* the game's frame: groups in list order, each with 1 to 9 entries; sometimes a second list begins (the table restarts) */
        for (g = 0; g < ng; g++) {
            u32 actor = pick_actor(), n = 1 + rnd() % 9;
            if (rnd() % 23 == 0) at = 0;
            if (at + n >= 1000) break;
            sat_guest_group(actor, 0x708000UL + at * 8);
            for (i = 0; i < (int)n; i++, at++) {
                u8 *e = obj + at * 8;
                e[0] = (u8)(rnd() & 3); e[1] = (u8)rnd(); e[2] = (u8)(rnd() & 3); e[3] = (u8)rnd();
                e[4] = (u8)rnd(); e[5] = (u8)rnd(); e[6] = (u8)rnd();
                e[7] = (u8)(((rnd() % 4 == 0) ? 1 : (rnd() % 32)) | (rnd() & 0xe0));
            }
            if ((int)at > count) count = (int)at;
        }
        for (i = 0; i < 1024; i++) pal[i] = (u8)rnd();
        sat_vblank_now_value = vb;
#if SAT_GUEST_GROUPS_EARLY
        if (kase != 8) sat_guest_groups_early();   /* case 8: the frame overran, no early run */
        switch (kase) {
        case 1: sat_guest_groups_task(0); R8(0xff8688u) = (u8)(R8(0xff8688u) ^ 4); break;   /* a task (0, not listed) ran after the frame: state changed, invalidated */
        case 6: sat_guest_groups_task(1); break;                                                    /* a listed task (1) ran: the result stays valid */
        case 2: sat_guest_group(0xff8380u, 0x708000UL + 900 * 8); break;                         /* one more group written: sequence moved */
        case 3: sat_guest_sel = (u8)(sat_guest_sel ^ 2); break;                                  /* the setting changed */
        case 4: vb += 1; break;                                                                   /* a vblank passed with no new early run: stamp two old */
        case 5: vb -= 1; break;                                                                   /* a stamp from the future */
        default: break;
        }
#else
        if (kase == 1) R8(0xff8688u) = (u8)(R8(0xff8688u) ^ 4);
        else if (kase == 2) sat_guest_group(0xff8380u, 0x708000UL + 900 * 8);
        else if (kase == 3) sat_guest_sel = (u8)(sat_guest_sel ^ 2);
        else if (kase == 4) vb += 1;
        else if (kase == 5) vb -= 1;
#endif
        sat_vblank_now_value = vb + 1;   /* the vblank rises by one before the snapshot runs */
        {
            static u8 o2[8 * 1024];
            memcpy(o2, obj, sizeof o2);
            count = sat_guest_objects(o2, count, 1000, pal);
            dump("S", t, count, o2, pal);
        }
        vb += 3;
        if (kase == 4) vb -= 1;
        if (kase == 5) vb += 1;
    }
#if SAT_GUEST_GROUPS_EARLY
    fprintf(stderr, "seen %u used %u own %u differ %u early_runs %u special %u\n", sat_gearly[0], sat_gearly[1], sat_gearly[2], sat_gearly[3], sat_gearly[4], sat_gearly[6]);
#endif
    return 0;
}
