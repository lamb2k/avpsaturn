/* Wolverine (bonus character 0, guests.c) in Schaefer's slot. SAT_GUESTS builds only; runs from the cart (cold code).
   Phase 2: the game still runs Schaefer's own logic for that player (input, movement, hits); here his sprites leave the frame's object
   list and Wolverine's pose is drawn at the player's place: idle when still, walk when moving, facing the way he moves.
   Tables: gen/wolverine_data.inc (tools/wolverine/gen_c.py, from the user's MSHvSF set at build time). Called from sat_gfx_snapshot. */
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
typedef signed char s8; typedef short s16; typedef int s32;
#include "guests.h"
#include "wolverine_data.inc"

extern u8 RAMB[];
#define R8(a) (*(volatile u8 *)(RAMB + ((a) - 0xff0000u)))
#define R16(a) (*(volatile u16 *)(RAMB + ((a) - 0xff0000u)))
#define PL(i) (0xff8380u + (u32)(i) * 0x100u)
/* Calibrated in Yaba on stage 02 (probe_sch.py, lane avp-wolverine): see WV_* below. */
/* Yaba probe, stage 02, Schaefer as player 1 (probe_sch.py): block byte +1 is the character (mask bit 1 << it, Schaefer 1); his sprites are
   palette row 1, big blocks centred about 72 px right of (+0x10 x - ff8278 camera) in object coordinates; feet at about 523 - (+0x14). */
#define WV_CHAR_OFF 1
#define WV_CHAR_SCH 1
#define WV_SCH_PAL 1        /* Schaefer's sprite palette row: his sprites leave the list, Wolverine's first row takes it */
/* Wolverine's second row (claws, highlights), per stage word: from a per-frame census of four whole-game MAME walks (tools/wolverine/pal_census.lua,
   11-08), the fourth row no sprite uses in that stage; Mega Man (lane avp-megaman) takes the first three. Odd words: 22. */
static const u8 wv_row1[0x28] = {10,22,21,22,20,22,18,22,22,22,8,22,23,22,22,22,21,22,22,22,10,22,21,22,27,22,18,22,31,22,18,22,21,22,18,22,21,22,12,22};
#define WV_PALROW1 ((R16(0xff81e8) & 0xff) < 0x28 ? wv_row1[R16(0xff81e8) & 0xff] : 22)
#define WV_OX 72
#define WV_OY 523

static u8 step_[2], left_[2], face_[2], moving_[2], cur_[2] = {255, 255}, chain_[2], lastc_[2], held_[2];

/* Schaefer's player block state +4 +5 +6, measured under MAME (tools/wolverine/schaefer_states.lua, 11-08):
   020000 stand, 020002 walk (also depth and the dash), 020004 jump, 020006 attack (chain), 02000e chain finisher, 02000c gun,
   020008 special (attack + jump), 0202xx hit (about 28 frames; 107 when knocked down), 0204xx grab and throw (walking into an enemy),
   0208xx getting up, 04xxxx dying, 08xxxx entering. His own moves take their place: the gun is the Berserker Barrage (no gun for him),
   the special the Tornado Claw, a hit held past 40 frames the knockdown. */
#define ONCE(m) ((m) == WV_LP || (m) == WV_HP || (m) == WV_HK || (m) == WV_TORNADO || (m) == WV_KNOCKDOWN || (m) == WV_THROW || (m) == WV_HIT_ETC)
static int move_for(int i)
{
    u8 a = R8(PL(i) + 4), b = R8(PL(i) + 5), c = R8(PL(i) + 6);
    int m = WV_IDLE;
    if (a == 2 && b == 0) {
        switch (c) {
        case 0x02: m = WV_WALK; break;
        case 0x04: m = WV_JUMP; break;
        case 0x06:   /* each new attack takes the next of his normals */
            if (lastc_[i] != 0x06) chain_[i] = (u8)((chain_[i] + 1) & 1);
            m = chain_[i] ? WV_HP : WV_LP; break;
        case 0x0e: m = WV_HK; break;
        case 0x0c: m = WV_BERSERKER; break;
        case 0x08: m = WV_TORNADO; break;
        }
    } else if (a == 2 && b == 2) m = held_[i] > 40 ? WV_KNOCKDOWN : WV_HIT_ETC;
    else if (a == 2 && b == 4) m = WV_THROW;
    else if (a == 2 && b == 8) m = WV_CROUCH;   /* getting up: his crouch rises back to stand */
    else if (a == 4) m = WV_KNOCKDOWN;
    else if (a == 8) m = WV_WALK;
    held_[i] = (a == 2 && b == 2) ? (u8)(held_[i] < 255 ? held_[i] + 1 : 255) : 0;
    lastc_[i] = (a == 2 && b == 0) ? c : 0;
    return m;
}
static u16 lastx_[2];

static void put16(u8 *p, u16 v) { p[0] = (u8)(v >> 8); p[1] = (u8)v; }

static int is_wolverine(int i)
{
    return R8(PL(i)) != 0 && R8(PL(i) + WV_CHAR_OFF) == WV_CHAR_SCH;
}

/* obj: the frame's object list (8 bytes each), count entries; returns the new count. pal0: sprite palette page (32 rows of 16 words). */
int sat_guest_touched;   /* set when this frame's palette page was changed */
int sat_guest_objects(u8 *obj, int count, int max, u8 *pal0)
{
    int i, k, n, j, any = 0;
    if (!(sat_guest_sel & 1)) return count;
    for (i = 0; i < 2; i++) {
        u16 x, cam;
        int move, st, sx, sy;
        if (!is_wolverine(i)) continue;
        any = 1;
        x = R16(PL(i) + 0x10);
        face_[i] = (u8)(R8(PL(i) + 0x0f) & 1);
        lastx_[i] = x;
        move = move_for(i);
        if (move != cur_[i]) { cur_[i] = (u8)move; step_[i] = 0; left_[i] = 0; }
        /* the move's steps: hold each pose its captured frames; one-shot moves keep their last pose until the state changes */
        n = wv_move_start[move + 1] - wv_move_start[move];
        if (step_[i] >= n) step_[i] = 0;
        if (++left_[i] >= wv_steps[wv_move_start[move] + step_[i]].frames) {
            left_[i] = 0;
            if (step_[i] + 1 < n) step_[i]++;
            else if (!ONCE(move)) step_[i] = 0;
        }
        st = wv_steps[wv_move_start[move] + step_[i]].pose;
        cam = R16(0xff8278);
        sx = (int)x - (int)cam + WV_OX;
        sy = WV_OY - (s16)R16(PL(i) + 0x14);
        /* Schaefer's own sprites near him go */
        for (j = k = 0; j < count; j++) {
            u8 *e = obj + j * 8;
            int ex = ((e[0] << 8 | e[1]) & 0x3ff), pal = e[7] & 31;
            if (ex >= 768) ex -= 1024;
            if (pal == WV_SCH_PAL && ex > sx - 140 && ex < sx + 140) continue;
            if (k != j) { int b; for (b = 0; b < 8; b++) obj[k * 8 + b] = e[b]; }
            k++;
        }
        count = k;
        /* his tiles go at the head of the list: earlier entries are in front on the board */
        n = wv_pose_start[st + 1] - wv_pose_start[st];
        if (count + n > max) n = max - count;
        for (j = count * 8 - 1; j >= 0; j--) obj[j + n * 8] = obj[j];
        for (k = 0; k < n; k++) {
            const WvTile *t = &wv_tiles[wv_pose_start[st] + k];
            int hf = (t->flags & 1) ^ face_[i], dx = face_[i] ? -t->dx - 16 : t->dx;
            u8 *o = obj + k * 8;
            put16(o, (u16)((sx + dx) & 0x3ff));
            put16(o + 2, (u16)((sy + t->dy) & 0x3ff));
            put16(o + 4, t->key);
            put16(o + 6, (u16)(((t->flags >> 2) ? WV_PALROW1 : WV_SCH_PAL) | (hf << 5) | ((t->flags & 2) << 5)));
        }
        count += n;
    }
    sat_guest_touched = any;
    if (any) for (k = 0; k < 16; k++) { put16(pal0 + WV_SCH_PAL * 32 + k * 2, wv_pal[k]); put16(pal0 + WV_PALROW1 * 32 + k * 2, wv_pal[16 + k]); }
    return count;
}
