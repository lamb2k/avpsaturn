/* Bonus character Mega Man (Marvel vs. Capcom), Predator Hunter's slot (mask 4). SAT_GUESTS builds with his data only.
   Draws his pose in place of the Hunter body group the game drew this frame (guests.c finds the group), chosen from the player block's
   state bytes; the Hunter's game logic, boxes and timing run underneath (phase 2). Tables: gen/guest_megaman.inc from
   tools/megaman/gen_runtime.py (ROM-derived, build time only). Palette rows: per stage, from the palette census (stage_rows). */
#include "guest_megaman.inc"
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned long u32;
extern u8 *PAGE[256];
#define R8(a) (PAGE[((a) >> 16) & 0xffu][(a) & 0xffffu])

enum { M_IDLE, M_WALK, M_WALKBACK, M_DASH, M_CROUCH, M_JUMP, M_LP, M_HP, M_HK, M_SLIDE, M_BUSTER, M_RUSH, M_THROW, M_HITALL, M_WIN, M_SHOOT, M_SHOT,
       M_HIT, M_KNOCKDOWN, M_GETUP, M_KO };
/* Sprite palettes for his rows (body, Rush, shot), per stage word / 2: the first three no character, enemy or effect uses in that stage in
   the four whole-game MAME walks (lane avp-wolverine palcensus c0-c3, union). Wolverine takes the next free one (guests share the rule). */
static const u8 stage_rows[20][3] = {{4,7,9},{9,10,20},{8,9,18},{8,9,10},{8,10,20},{5,6,7},{8,18,21},{8,18,21},{8,18,19},{10,11,18},
                                     {6,8,9},{8,18,20},{8,22,24},{8,10,16},{8,18,24},{4,8,9},{8,18,20},{4,6,8},{8,10,18},{4,8,11}};
static const u8 *row_pal = stage_rows[1];
static void pick_rows(void) { unsigned st = R8(0xff81e9) >> 1; row_pal = stage_rows[st < 20 ? st : 1]; }
unsigned char sat_mm_tone = MM_DEFAULT_TONE;   /* 0 capcom, 1 soft, 2 avp (default), 3 dark */
/* moves that hold their last pose instead of looping */
#define ONCE(m) ((m) == M_LP || (m) == M_HP || (m) == M_HK || (m) == M_KNOCKDOWN || (m) == M_GETUP || (m) == M_KO || (m) == M_SHOOT || (m) == M_RUSH || (m) == M_HIT)

static struct { u8 move, step, left, chain, last_c; short shot_x, shot_y; u8 shot_t, shot_left, shot_step, shot_dir; } anim[3];

/* Player block state +4 +5 +6, measured for the Predator Hunter under MAME (tools/megaman/avp_states.lua, lane avp-megaman):
   020000 stand, 020002 walk (also depth), 020004 jump, 020014 attack (chain), 02000c / 02001a gun, 020008 special (attack + jump),
   020200 / 020202 hit, 020400 hit (light); 0402xx hit / 040204 knockdown / 040206 dying, 0404xx gone; 0208xx getting up; 08xxxx entering. */
static int move_for(u32 actor, int slot)
{
    u8 a = R8(actor + 4), b = R8(actor + 5), c = R8(actor + 6);
    if (a == 2 && b == 0) {
        switch (c) {
        case 0x00: return M_IDLE;
        case 0x02: return M_WALK;
        case 0x04: return M_JUMP;
        case 0x14:   /* each new attack takes the next of his three normals */
            if (anim[slot].last_c != 0x14) anim[slot].chain = (u8)((anim[slot].chain + 1) % 3);
            return anim[slot].chain == 0 ? M_LP : anim[slot].chain == 1 ? M_HP : M_HK;
        case 0x0c: case 0x1a: return M_SHOOT;
        case 0x08: return M_RUSH;
        default: return M_IDLE;
        }
    }
    if (a == 2 && (b == 2 || b == 4)) return M_HIT;
    if (a == 2 && b == 8) return M_GETUP;
    if (a == 4 && b == 2) return c == 4 ? M_KNOCKDOWN : c == 6 ? M_KO : c == 8 ? M_GETUP : M_HIT;   /* 040208: up again (Yaba run5) */
    if (a == 4) return M_KO;
    return M_IDLE;
}

void sat_guest_megaman_palette(u8 *page0)
{
    int r, p;
    pick_rows();
    for (r = 0; r < 3; r++)
        for (p = 0; p < 15; p++) {
            u16 c = MM_PAL[sat_mm_tone & 3][r][p];
            u8 *d = page0 + ((u32)row_pal[r] * 16 + p) * 2;
            d[0] = (u8)(c >> 8); d[1] = (u8)c;
        }
}

static int put_pose(u8 *out, int room, int pose, int ax, int bottom, u16 xhi, u16 ahi, int left);

/* Writes his pose as one-tile objects (CPS object words) at out; ax/bottom = the Hunter group's feet in object coordinates;
   xhi = priority bits of the first replaced word, ahi = its offset flag (0x80). Returns objects written. */
int sat_guest_megaman_draw(u8 *out, int room, u32 actor, int ax, int bottom, u16 xhi, u16 ahi)
{
    int slot = (int)((actor - 0xff8380UL) >> 8) & 3, n, mv, st, pose, left = R8(actor + 0x0f) & 1;
    if (slot > 2) slot = 2;
    mv = move_for(actor, slot);
    anim[slot].last_c = (R8(actor + 4) == 2 && R8(actor + 5) == 0) ? R8(actor + 6) : 0;
    if (!MM_MOVES[mv][1]) mv = M_IDLE;
    if (anim[slot].move != mv) {
        if (mv == M_SHOOT && !anim[slot].shot_t) {   /* one Mega Buster shot on screen; the Hunter's own shot does the hitting */
            anim[slot].shot_t = 40; anim[slot].shot_x = (short)(left ? -40 : 24); anim[slot].shot_y = -64;
            anim[slot].shot_dir = (u8)left; anim[slot].shot_step = 0; anim[slot].shot_left = 0;
        }
        anim[slot].move = (u8)mv; anim[slot].step = 0; anim[slot].left = 0;
    }
    st = MM_MOVES[mv][0] + anim[slot].step;
    if (!anim[slot].left) anim[slot].left = MM_STEPS[st][1];
    if (--anim[slot].left == 0) {
        if (anim[slot].step + 1 < MM_MOVES[mv][1]) anim[slot].step++;
        else if (!ONCE(mv)) anim[slot].step = 0;
        else anim[slot].left = 1;
    }
    pose = MM_STEPS[st][0];
    n = put_pose(out, room, pose, ax, bottom, xhi, ahi, left);
    if (anim[slot].shot_t && MM_MOVES[M_SHOT][1]) {
        int sst = MM_MOVES[M_SHOT][0] + anim[slot].shot_step;
        n += put_pose(out + n * 8, room - n, MM_STEPS[sst][0], ax + anim[slot].shot_x, bottom - 4, xhi, ahi, !anim[slot].shot_dir);   /* the captured shot faces left */
        anim[slot].shot_x = (short)(anim[slot].shot_x + (anim[slot].shot_dir ? -6 : 6));
        if (++anim[slot].shot_left >= MM_STEPS[sst][1]) { anim[slot].shot_left = 0; anim[slot].shot_step = (u8)((anim[slot].shot_step + 1) % MM_MOVES[M_SHOT][1]); }
        anim[slot].shot_t--;
    }
    return n;
}

static int put_pose(u8 *out, int room, int pose, int ax, int bottom, u16 xhi, u16 ahi, int left)
{
    const unsigned short *ps = MM_POSES[pose];
    int i, n = 0;
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
