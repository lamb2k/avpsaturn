/* Bonus character Mega Man (Marvel vs. Capcom), Predator Hunter's slot (mask 4). SAT_GUESTS builds with his data only.
   Draws his pose in place of the Hunter body group the game drew this frame (guests.c finds the group), chosen from the player block's
   state bytes; the Hunter's game logic, boxes and timing run underneath (phase 2). Tables: gen/guest_megaman.inc from
   tools/megaman/gen_runtime.py (ROM-derived, build time only). Palette rows go to sprite palettes MM_PAL_BODY.. (free on stage 02). */
#include "guest_megaman.inc"
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned long u32;
extern u8 *PAGE[256];
#define R8(a) (PAGE[((a) >> 16) & 0xffu][(a) & 0xffffu])

enum { M_IDLE, M_WALK, M_WALKBACK, M_DASH, M_CROUCH, M_JUMP, M_LP, M_HP, M_HK, M_SLIDE, M_BUSTER, M_RUSH, M_THROW, M_HIT, M_WIN, M_SHOOT, M_SHOT };
#define MM_PAL_BODY 22      /* sprite palettes: body, Rush, shot (rows 0, 1, 2) */
static const u8 row_pal[3] = { MM_PAL_BODY, 26, 24 };
unsigned char sat_mm_tone = MM_DEFAULT_TONE;   /* 0 capcom, 1 soft, 2 avp (default), 3 dark */

static struct { u8 move, step, left; u16 last_state; } anim[3];

/* Player block state +4 +5 +6 (lane alien-measure reading) to one of his moves. */
static int move_for(u32 actor)
{
    u8 a = R8(actor + 4), b = R8(actor + 5), c = R8(actor + 6);
    if (a == 2 && b == 0) {
        switch (c) {
        case 0x08: return M_IDLE;
        case 0x00: case 0x02: case 0x04: return M_WALK;
        case 0x12: case 0x14: return M_JUMP;
        case 0x0c: return M_HP;
        case 0x10: return M_LP;
        case 0x18: return M_HK;
        case 0x16: return M_SHOOT;
        default: return M_IDLE;
        }
    }
    if (a == 2 && b == 2) return M_HIT;      /* grabbed / thrown */
    if (a == 2 && b == 4) return M_SHOOT;    /* gun */
    if (a == 2 && b == 6) return M_RUSH;     /* special */
    if (a == 4) return M_HIT;                /* hit, shot hit, knockdown, dying */
    if (a == 8) return M_CROUCH;             /* pickup / get up */
    return M_IDLE;
}

void sat_guest_megaman_palette(u8 *page0)
{
    int r, p;
    for (r = 0; r < 3; r++)
        for (p = 0; p < 15; p++) {
            u16 c = MM_PAL[sat_mm_tone & 3][r][p];
            u8 *d = page0 + ((u32)row_pal[r] * 16 + p) * 2;
            d[0] = (u8)(c >> 8); d[1] = (u8)c;
        }
}

/* Writes his pose as one-tile objects (CPS object words) at out; ax/bottom = the Hunter group's feet in object coordinates;
   xhi = priority bits of the first replaced word, ahi = its offset flag (0x80). Returns objects written. */
int sat_guest_megaman_draw(u8 *out, int room, u32 actor, int ax, int bottom, u16 xhi, u16 ahi)
{
    int slot = (int)((actor - 0xff8380UL) >> 8) & 3, n = 0, mv, st, pose, i, left = R8(actor + 0x0f) & 1;
    const unsigned short *ps;
    if (slot > 2) slot = 2;
    mv = move_for(actor);
    if (anim[slot].move != mv || !MM_MOVES[mv][1]) { anim[slot].move = (u8)mv; anim[slot].step = 0; anim[slot].left = 0; }
    if (!MM_MOVES[mv][1]) mv = M_IDLE;
    st = MM_MOVES[mv][0] + anim[slot].step;
    if (!anim[slot].left) anim[slot].left = MM_STEPS[st][1];
    if (--anim[slot].left == 0) anim[slot].step = (u8)((anim[slot].step + 1) % MM_MOVES[mv][1]);
    pose = MM_STEPS[st][0];
    ps = MM_POSES[pose];
    for (i = 0; i < ps[1] && n < room; i++) {
        int dx = MM_ENT[ps[0] + i].dx, dy = MM_ENT[ps[0] + i].dy, fl = MM_ENT[ps[0] + i].flags;
        u16 key = MM_ENT[ps[0] + i].key, x, y, a;
        int hf = fl & 1;
        if (left) { dx = -dx - 16; hf ^= 1; }   /* captured facing right */
        x = (u16)(((ax + dx) & 0x3ff) | xhi);
        y = (u16)((bottom + dy) & 0x3ff);
        a = (u16)(ahi | (hf << 5) | ((fl & 2) << 5) | row_pal[(fl >> 2) & 3]);
        out[0] = (u8)(x >> 8); out[1] = (u8)x; out[2] = (u8)(y >> 8); out[3] = (u8)y;
        out[4] = (u8)(key >> 8); out[5] = (u8)key; out[6] = (u8)(a >> 8); out[7] = (u8)a;
        out += 8; n++;
    }
    return n;
}
