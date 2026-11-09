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
   palette row 1, big blocks centred about 72 px right of (+0x10 x - ff8278 camera) in object coordinates; feet at about 523 - (+0x14) with the camera's depth word ff827c at rest (0x100); ff827c follows the player's depth and scrolls
   his sprites by (ff827c - 0x100) (probe_cam.py, 11-08: before that fix Wolverine stood up to 48 px below Schaefer's body at the front of the stage). */
#define WV_CHAR_OFF 1
#define WV_CHAR_SCH 1
#define WV_SCH_PAL 1        /* Schaefer's sprite palette row: his sprites leave the list, Wolverine's first row takes it */
/* Wolverine's second row (claws, highlights), per stage word: from a per-frame census of four whole-game MAME walks (tools/wolverine/pal_census.lua,
   11-08), the fourth row no sprite uses in that stage; Mega Man (lane avp-megaman) takes the first three. Odd words: 22. */
static const u8 wv_row1[0x28] = {10,22,21,22,20,22,18,22,22,22,8,22,23,22,22,22,21,22,22,22,10,22,21,22,27,22,18,22,31,22,18,22,21,22,18,22,21,22,12,22};
#define WV_PALROW1 ((R16(0xff81e8) & 0xff) < 0x28 ? wv_row1[R16(0xff81e8) & 0xff] : 22)
#define WV_OX 72
#define WV_OY 523

/* Debug (lane avp-wolverine, anchor check): per player, the box of Schaefer's removed sprites and of Wolverine's drawn tiles in object
   coordinates (x0, y0, x1, y1), plus his state and pose. Read by the Yaba probe; never written to the screen. */
s16 wv_dbg[2][12];
s16 wv_lst[2][3];   /* per player: objects before his tiles, tiles asked, tiles that fit (a full list drops his tiles) */
static u8 step_[2], left_[2], face_[2], cur_[2] = {255, 255}, chain_[2], lastc_[2], held_[2];

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

/* Boxes (option B, lane avp-wolverine-b). AvP's collision pass f_1cf54 (attacker a6, target a1) takes the attack box from the attacker's
   frame record (+1c) byte 9 and the hurt box from the target's byte 8, as indexes into the character's box table (+50):
   attack = T + word T[2] + idx * 16, hurt = T + word T[0] + idx * 8; bytes 0..5 of either: x (forward, s8), y (up, s8), x half, y half,
   depth, depth half (f_1d25e). Around each call for a Wolverine player the hook writes his MSHvSF box for the step he shows
   (gen/wolverine_data.inc wv_box, tools/wolverine/boxes.py) over x, y and the halves, keeps AvP's depth bytes and the rest of the record
   (damage, knockback), and puts every byte back after the call. Records are ROM image pages the game reads, so stage tiles never take them.
   His hit is out only on the steps where MSHvSF had one, in Schaefer's attack states; when Schaefer's own frame has none there, the frame's
   index is borrowed from the last attack Schaefer's state showed (same damage record). */
static int is_wolverine(int i);
extern u8 *PAGE[256];
#define PBY(a) (PAGE[((u32)(a) >> 16) & 0xff] + ((u32)(a) & 0xffff))
static u16 wv_step_now[2] = {0xffff, 0xffff};   /* index into wv_box of the step he shows, per player; 0xffff none */
static u8 atk_cache[2][16];                       /* last nonzero attack index per Schaefer state +6 (by state >> 1) */
static struct { u8 *p; u8 v[4]; } undo[8];
static int nundo;
static u32 rd32(u32 a) { u8 *p = PBY(a); return (u32)p[0] << 24 | (u32)p[1] << 16 | (u32)p[2] << 8 | p[3]; }
static u32 rd16(u32 a) { u8 *p = PBY(a); return (u32)p[0] << 8 | p[1]; }
static void poke4(u8 *p, int a, int b, int c, int d)
{
    int k;
    if (nundo >= 8) return;
    undo[nundo].p = p;
    for (k = 0; k < 4; k++) undo[nundo].v[k] = p[k];
    nundo++;
    p[0] = (u8)a; p[1] = (u8)b; p[2] = (u8)c; p[3] = (u8)d;
}
static int wv_player(u32 b)
{
    if (!(sat_guest_sel & 1) || (b != PL(0) && b != PL(1))) return -1;
    return is_wolverine((int)((b - PL(0)) >> 8)) ? (int)((b - PL(0)) >> 8) : -1;
}
static int attack_state(int i, int *slot)
{
    u8 a = R8(PL(i) + 4), b = R8(PL(i) + 5), c = R8(PL(i) + 6);
    *slot = (c >> 1) & 15;
    return a == 2 && b == 0 && (c == 0x06 || c == 0x0e || c == 0x0c || c == 0x08);
}
static const WvBox *box_now(int i)
{
    u16 k = wv_step_now[i];
    if (k == 0xffff) return 0;
    if (!wv_box[k].uw) return &wv_box[wv_move_start[WV_IDLE]];   /* a step without a capture keeps his standing hurt box */
    return &wv_box[k];
}
/* restore = 0: before the call; 1: after it */
void sat_guest_wolverine_boxes(unsigned long a6, unsigned long a1, int restore)
{
    int i, slot;
    if (restore) {
        while (nundo > 0) { nundo--; { int k; for (k = 0; k < 4; k++) undo[nundo].p[k] = undo[nundo].v[k]; } }
        return;
    }
    nundo = 0;
    if (!WV_HAVE_BOXES) return;
    if ((i = wv_player((u32)a6)) >= 0) {   /* his hit */
        const WvBox *w = box_now(i);
        u32 fr = rd32((u32)a6 + 0x1c), t = rd32((u32)a6 + 0x50);
        u8 *f = PBY(fr), idx = f[9];
        int att = attack_state(i, &slot);
        if (att && idx) atk_cache[i][slot] = idx;
        if (!att || !w || !w->hw) { if (idx) poke4(f + 8, f[8], 0, f[10], f[11]); }
        else {
            if (!idx) idx = atk_cache[i][slot];
            if (idx) {
                u8 *r = PBY(t + rd16(t + 2) + (u32)(s8)idx * 16);
                if (idx != f[9]) poke4(f + 8, f[8], idx, f[10], f[11]);
                poke4(r, -w->hx, w->hy, w->hw, w->hh);   /* AvP's record x is backward-positive (f_1d25e negates it when +0f is set, facing right) */
            }
        }
    }
    if ((i = wv_player((u32)a1)) >= 0) {   /* his hurt box */
        const WvBox *w = box_now(i);
        u32 fr = rd32((u32)a1 + 0x1c), t = rd32((u32)a1 + 0x50);
        u8 idx = PBY(fr)[8];
        if (w && idx) poke4(PBY(t + rd16(t) + (u32)(s8)idx * 8), -w->ux, w->uy, w->uw, w->uh);
    }
}
/* Debug for the box sheets (wv_box_dbg[player]): Schaefer's own attack and hurt box from his frame (x0 y0 x1 y1, object coordinates),
   then Wolverine's. 9999 = none. */
s16 wv_box_dbg[2][16];
static void box_rect(s16 *o, int sx, int sy, int face, int x, int y, int hw, int hh)
{
    int cx = face ? sx - x : sx + x, cy = sy - y;
    o[0] = (s16)(cx - hw); o[1] = (s16)(cy - hh); o[2] = (s16)(cx + hw); o[3] = (s16)(cy + hh);
}
static void box_debug(int i, int sx, int sy)
{
    u32 b = PL(i), fr = rd32(b + 0x1c), t = rd32(b + 0x50);
    u8 *f = PBY(fr), *r;
    const WvBox *w = box_now(i);
    int k, face = R8(b + 0x0f) != 0, slot, att = attack_state(i, &slot);
    for (k = 0; k < 16; k++) wv_box_dbg[i][k] = 9999;
    if (f[9]) { r = PBY(t + rd16(t + 2) + (u32)(s8)f[9] * 16); box_rect(&wv_box_dbg[i][0], sx, sy, face, (s8)r[0], (s8)r[1], r[2], r[3]); }
    if (f[8]) { r = PBY(t + rd16(t) + (u32)(s8)f[8] * 8); box_rect(&wv_box_dbg[i][4], sx, sy, face, (s8)r[0], (s8)r[1], r[2], r[3]); }
    if (w && w->hw && att) box_rect(&wv_box_dbg[i][8], sx, sy, face, -w->hx, w->hy, w->hw, w->hh);
    if (w) box_rect(&wv_box_dbg[i][12], sx, sy, face, -w->ux, w->uy, w->uw, w->uh);
}

static void put16(u8 *p, u16 v) { p[0] = (u8)(v >> 8); p[1] = (u8)v; }

static int is_wolverine(int i)
{
    return R8(PL(i)) != 0 && R8(PL(i) + WV_CHAR_OFF) == WV_CHAR_SCH;
}

/* Names: the game prints its character names from text in its ROM image, which the Saturn keeps in cart RAM (ROMB). While Wolverine is
   chosen, Schaefer's HUD name (16-byte field at 0xaedca) and his select-screen name (0xac699) read WOLVERINE; turned off, the bytes go back.
   Both are on pages the game reads, which stage files never take for tiles. */
#define ROMB ((volatile u8 *)0x02400000u)
static const struct { u32 at; u8 n; const char *wv; } wv_names[2] = {
    { 0xaedca, 16, "WOLVERINE       " },
    { 0xac699, 14, "  WOLVERINE   " },
};
static u8 name_saved[2][16], names_on;
static void names(int on)
{
    int i, k;
    if (on == names_on) {
        if (!on) return;
        for (i = 0; i < 2; i++) for (k = 0; k < wv_names[i].n; k++) if (ROMB[wv_names[i].at + k] != (u8)wv_names[i].wv[k]) goto write;   /* a stage load restored the page */
        return;
    }
write:
    for (i = 0; i < 2; i++)
        for (k = 0; k < wv_names[i].n; k++) {
            if (on && !names_on) name_saved[i][k] = ROMB[wv_names[i].at + k];
            ROMB[wv_names[i].at + k] = on ? (u8)wv_names[i].wv[k] : name_saved[i][k];
        }
    names_on = (u8)on;
}

/* Move clock and timings (option B). The move clock runs in game ticks (one call of the player state machine, f_195ec, wrapped in game_bind.c),
   not in drawn frames, so his poses, his box steps and the game's hits share one time. For each attack the capture's length T (MSHvSF frames from the
   press to his return to stand, after the last frame with an attack box) is compared with how many ticks Schaefer's own state of that slot runs
   (wv_nat, measured: wv_tdbg). When T is longer the state machine is held on the ticks in between (Bresenham, nat of every T ticks run), which
   stretches Schaefer's timers to MSHvSF's: his startup, active frames and recovery land where the capture has them. The hit still needs an
   MSHvSF attack box on the step shown (sat_guest_wolverine_boxes). Shorter captures are not cut (the state returns to stand on its own).
   Held ticks freeze the whole state machine of that player (position, frame record, timers); other actors run on. */
u8 wv_tdbg[5][4];   /* per held move (LP HP HK Berserker Tornado): last ticks run, last ticks passed, times seen, last T; read by the Yaba probe (little room in low RAM) */
static int tslot(int m) { return m == WV_LP ? 0 : m == WV_HP ? 1 : m == WV_HK ? 2 : m == WV_BERSERKER ? 3 : m == WV_TORNADO ? 4 : -1; }
/* Schaefer's ticks per state slot, MAME (tools/wolverine/schaefer_states.lua: a tap of attack 15, the finisher 02000e 32, the special 020008 57);
   gun 02000c measured on Yaba from wv_tdbg. 0 = never held. */
#ifndef WV_NAT_GUN
#define WV_NAT_GUN 30
#endif
static u16 wv_nat(int move)
{
#ifdef WV_MEASURE
    return 0;   /* test build: no holds, wv_tdbg shows Schaefer's own tick counts */
#endif
    switch (move) {
    case WV_LP: case WV_HP: return 15;
    case WV_HK: return 32;
    case WV_BERSERKER: return WV_NAT_GUN;
    case WV_TORNADO: return 57;
    }
    return 0;
}
static int wv_move_len(int move)
{
    int s = wv_move_start[move], n = wv_move_start[move + 1] - s, k, last = -1, T = 0;
    for (k = 0; k < n; k++) if (wv_box[s + k].hw) last = k;
    for (k = 0; k < n; k++) {
        if (last >= 0 && k > last && wv_steps[s + k].pose == WV_STANCE) break;   /* the ready stance after the last attack frame ends the move */
        T += wv_steps[s + k].frames;
    }
    return T;
}
static u16 acc_[2], exec_[2], wall_[2];
/* The walk cycle runs on distance, not time: his captured stride (MSHvSF: about 119 px of ground per 41-frame loop at his walk speed, boxcap/boxes.txt)
   is stepped by how far Schaefer's walk carried the player this tick (x and depth), so his feet keep to the ground at AvP's walk speed and the dash.
   The loop is the stretch of the capture's walk steps between a pose and its next appearance (steps before it are the start of the walk); standing still
   freezes the pose. wph_ is in 1/16 frame of the capture. */
#ifndef WV_STRIDE
#define WV_STRIDE 119
#endif
static u16 wph_[2], wlx_[2], wlz_[2];
static u8 wwalk_[2];
static void wv_walk_step(int i)
{
    int s = wv_move_start[WV_WALK], n = wv_move_start[WV_WALK + 1] - s, a, b = -1, k, loop_len = 0, start_len = 0;
    u16 x = R16(PL(i) + 0x10), z = R16(PL(i) + 0x18);
    int dx = (s16)(x - wlx_[i]), dz = (s16)(z - wlz_[i]), dist;
    u32 q;
    for (a = 0; a < n && b < 0; a++) for (k = a + 1; k < n; k++) if (wv_steps[s + k].pose == wv_steps[s + a].pose) { b = k; break; }
    a--;
    if (b < 0) { a = 0; b = n; }   /* no repeat in the capture: the whole walk loops */
    for (k = 0; k < a; k++) start_len += wv_steps[s + k].frames;
    for (k = a; k < b; k++) loop_len += wv_steps[s + k].frames;
    if (!wwalk_[i]) { wwalk_[i] = 1; wph_[i] = 0; dx = dz = 0; }   /* first tick of the walk: no distance yet */
    dist = (dx < 0 ? -dx : dx) + (dz < 0 ? -dz : dz);
    if (dist > 40) dist = 0;   /* a jump of position (scene cut, knock-back), not a step */
    wlx_[i] = x; wlz_[i] = z;
    {   /* 1/16 frame units, wrapped inside the loop once the start is past */
        u32 add = ((u32)dist * (u32)loop_len * 16u) / WV_STRIDE;
        u32 p = (u32)wph_[i] + add, lim = ((u32)start_len + (u32)loop_len) * 16u;
        if (p >= lim) p = (u32)start_len * 16u + (p - (u32)start_len * 16u) % ((u32)loop_len * 16u);
        wph_[i] = (u16)p;
        q = p >> 4;
    }
    if (q < (u32)start_len) {
        for (k = 0; k < a; k++) { if (q < wv_steps[s + k].frames) break; q -= wv_steps[s + k].frames; }
        step_[i] = (u8)k;
    } else {
        q -= (u32)start_len;
        for (k = a; k < b; k++) { if (q < wv_steps[s + k].frames) break; q -= wv_steps[s + k].frames; }
        step_[i] = (u8)(k < b ? k : b - 1);
    }
    left_[i] = 0;
}

/* one tick of player i's move clock; returns 1 when the state machine runs this tick, 0 when held */
static int wv_tick_move(int i)
{
    int move = move_for(i), n, hold = 0, T, nat;
    if (move != cur_[i]) {
        if (cur_[i] < WV_MOVES && tslot(cur_[i]) >= 0 && exec_[i]) { u8 *d = wv_tdbg[tslot(cur_[i])]; d[0] = (u8)(exec_[i] > 255 ? 255 : exec_[i]); d[1] = (u8)(wall_[i] > 255 ? 255 : wall_[i]); d[2]++; }
        cur_[i] = (u8)move; step_[i] = 0; left_[i] = 0; exec_[i] = wall_[i] = 0; wwalk_[i] = 0;
        nat = wv_nat(move); T = nat ? wv_move_len(move) : 0;
        acc_[i] = (T > nat) ? (u16)(T - nat) : 0;   /* the first tick of the state runs */
    }
    n = wv_move_start[move + 1] - wv_move_start[move];
    if (move == WV_WALK) wv_walk_step(i);
    else {
        if (step_[i] >= n) step_[i] = 0;
        if (++left_[i] >= wv_steps[wv_move_start[move] + step_[i]].frames) {   /* the move's steps: each pose its captured frames */
            left_[i] = 0;
            if (step_[i] + 1 < n) step_[i]++;
            else if (!ONCE(move)) step_[i] = 0;
        }
    }
    wv_step_now[i] = (u16)(wv_move_start[move] + step_[i]);
    nat = wv_nat(move);
    if (nat && WV_HAVE_BOXES) {
        T = wv_move_len(move);
        wv_tdbg[tslot(move)][3] = (u8)T;
        if (T > nat) { acc_[i] = (u16)(acc_[i] + nat); if (acc_[i] < T) hold = 1; else acc_[i] = (u16)(acc_[i] - T); }
    }
    if (wall_[i] < 65535) wall_[i]++;
    if (!hold && exec_[i] < 65535) exec_[i]++;
    return !hold;
}
/* wrapper hook for f_195ec (player state machine, a6 = the player's block): 1 run it, 0 skip this tick */
int sat_guest_wolverine_tick(unsigned long a6)
{
    int i = wv_player((u32)a6);
    if (i < 0) return 1;
    return wv_tick_move(i);
}
/* a gun shot (tag 4 in ff8680..ff957f, owner word +0x26; +2 is 5 while one flies) of a Wolverine player: Berserker Barrage is his gun slot's move, the shot itself does nothing */
int sat_guest_wolverine_bullet(unsigned long a6)
{
    u8 *b = PAGE[0xff];
    u32 o = (u32)a6 & 0xffff, owner;
    if (!(sat_guest_sel & 1) || (a6 >> 16) != 0xff || o < 0x8680 || o >= 0x9580 || b[o + 8] != 4) return 0;
    owner = 0xff0000u | ((u32)b[o + 0x26] << 8) | b[o + 0x27];
    return wv_player(owner) >= 0;
}
/* obj: the frame's object list (8 bytes each), count entries; returns the new count. pal0: sprite palette page (32 rows of 16 words). */
int sat_guest_touched;   /* set when this frame's palette page was changed */
int sat_guest_objects(u8 *obj, int count, int max, u8 *pal0)
{
    int i, k, n, j, any = 0;
    names(sat_guest_sel & 1);
    if (!(sat_guest_sel & 1)) return count;
    for (i = 0; i < 2; i++) {
        u16 x, cam;
        int move, st, sx, sy;
        if (!is_wolverine(i)) continue;
        any = 1;
        x = R16(PL(i) + 0x10);
        face_[i] = (u8)((R8(PL(i) + 0x0f) & 1) ^ 1);   /* +0f set = facing right (Yaba 11-08: set while walking right); his poses were captured facing right, so they mirror when it is clear */
        if (cur_[i] == 255) wv_tick_move(i);   /* game ticks drive the move clock (sat_guest_wolverine_tick); this only covers the first frame */
        move = cur_[i];
        st = wv_steps[wv_move_start[move] + step_[i]].pose;
        wv_step_now[i] = (u16)(wv_move_start[move] + step_[i]);
        cam = R16(0xff8278);
        sx = (int)x - (int)cam + WV_OX;
        sy = WV_OY - 0x100 - (s16)R16(PL(i) + 0x14) + (s16)R16(0xff827c);   /* the camera's depth (ff827c, 0x100 at rest) scrolls him as it does Schaefer */
        wv_dbg[i][0] = wv_dbg[i][1] = wv_dbg[i][4] = wv_dbg[i][5] = 9999; wv_dbg[i][2] = wv_dbg[i][3] = wv_dbg[i][6] = wv_dbg[i][7] = -9999;
        box_debug(i, sx, sy);
        wv_dbg[i][8] = (s16)sx; wv_dbg[i][9] = (s16)sy; wv_dbg[i][10] = (s16)(R8(PL(i) + 6) | R8(PL(i) + 5) << 8); wv_dbg[i][11] = (s16)(st | face_[i] << 12);
        /* Schaefer's own sprites near him go */
        for (j = k = 0; j < count; j++) {
            u8 *e = obj + j * 8;
            int ex = ((e[0] << 8 | e[1]) & 0x3ff), pal = e[7] & 31;
            if (ex >= 768) ex -= 1024;
            if (pal == WV_SCH_PAL && ex > sx - 140 && ex < sx + 140) {
                int ey = ((e[2] << 8 | e[3]) & 0x3ff), w = ((e[6] >> 0) & 15) + 1, h = ((e[6] >> 4) & 15) + 1;
                if (ey >= 768) ey -= 1024;
                if (ex < wv_dbg[i][0]) wv_dbg[i][0] = (s16)ex;
                if (ey < wv_dbg[i][1]) wv_dbg[i][1] = (s16)ey;
                if (ex + 16 * w > wv_dbg[i][2]) wv_dbg[i][2] = (s16)(ex + 16 * w);
                if (ey + 16 * h > wv_dbg[i][3]) wv_dbg[i][3] = (s16)(ey + 16 * h);
                continue;
            }
            if (k != j) { int b; for (b = 0; b < 8; b++) obj[k * 8 + b] = e[b]; }
            k++;
        }
        count = k;
        /* his tiles go at the head of the list: earlier entries are in front on the board */
        n = wv_pose_start[st + 1] - wv_pose_start[st];
        wv_lst[i][0] = (s16)count; wv_lst[i][1] = (s16)n;
        if (count + n > max) n = max - count;
        wv_lst[i][2] = (s16)n;
        for (j = count * 8 - 1; j >= 0; j--) obj[j + n * 8] = obj[j];
        for (k = 0; k < n; k++) {
            const WvTile *t = &wv_tiles[wv_pose_start[st] + k];
            int hf = (t->flags & 1) ^ face_[i], dx = face_[i] ? -t->dx - 16 : t->dx;
            u8 *o = obj + k * 8;
            if (sx + dx < wv_dbg[i][4]) wv_dbg[i][4] = (s16)(sx + dx);
            if (sy + t->dy < wv_dbg[i][5]) wv_dbg[i][5] = (s16)(sy + t->dy);
            if (sx + dx + 16 > wv_dbg[i][6]) wv_dbg[i][6] = (s16)(sx + dx + 16);
            if (sy + t->dy + 16 > wv_dbg[i][7]) wv_dbg[i][7] = (s16)(sy + t->dy + 16);
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

/* Motion inputs (option B), MSHvSF style: the game's pad word (pad.c in0: per player byte, active low, 1 right, 2 left, 4 down, 8 up,
   0x10 gun, 0x20 attack, 0x40 jump) passes through here once a vblank. Directions are read against his facing (+0f: 1 right).
   Berserker Barrage: down, down-forward, forward, then attack within the window -> the gun button (his gun state slot, 020c).
   Tornado Claw: forward, down, down-forward, then attack -> attack + jump (the special slot, 0208). The attack press that ends the motion
   is replaced, so the plain attack does not also come out. Each step of the motion must follow the last within WV_CMD_GAP vblanks, and the
   button within WV_CMD_GAP of the last direction (MSHvSF's buffer is of this order; tuned on Yaba). */
#define WV_CMD_GAP 10
#define WV_CMD_HOLD 4
static u8 dir_hist[2][4], dir_age[2][4], inj_left[2], inj_bits[2], last_btn[2];
static int dir_of(u8 w, int face)   /* 1 forward, 2 down-forward, 3 down, 0 other; w active high */
{
    int fwd = face ? (w & 1) : (w & 2), dn = w & 4;   /* +0f set: facing right (Yaba, stage 02: Schaefer's attack box sits right of him) */
    if (dn && fwd) return 2;
    if (dn) return 3;
    if (fwd && !(w & 8)) return 1;
    return 0;
}
static int seen(int i, const u8 *seq)   /* the last three distinct directions, oldest first, inside the gap */
{
    return dir_hist[i][2] == seq[0] && dir_hist[i][1] == seq[1] && dir_hist[i][0] == seq[2] &&
           dir_age[i][0] <= WV_CMD_GAP && dir_age[i][1] <= WV_CMD_GAP * 2 && dir_age[i][2] <= WV_CMD_GAP * 3;
}
void sat_guest_wolverine_pad(u16 *in0)
{
    static const u8 qcf[3] = {3, 2, 1}, dp[3] = {1, 3, 2};
    int i, k;
    if (!(sat_guest_sel & 1)) return;
    for (i = 0; i < 2; i++) {
        int sh = i * 8, d;
        u8 w = (u8)~(*in0 >> sh), btn;
        if (!is_wolverine(i)) { inj_left[i] = 0; continue; }
        for (k = 0; k < 4; k++) if (dir_age[i][k] < 255) dir_age[i][k]++;
        d = dir_of(w, R8(PL(i) + 0x0f) != 0);
        if (d && d != dir_hist[i][0]) {
            for (k = 3; k > 0; k--) { dir_hist[i][k] = dir_hist[i][k - 1]; dir_age[i][k] = dir_age[i][k - 1]; }
            dir_hist[i][0] = (u8)d;
        }
        if (d) dir_age[i][0] = 0;
        btn = w & 0x20;
        if (btn && !last_btn[i] && !inj_left[i]) {
            if (seen(i, dp)) { inj_bits[i] = 0x60; inj_left[i] = WV_CMD_HOLD; }        /* Tornado Claw: attack + jump */
            else if (seen(i, qcf)) { inj_bits[i] = 0x10; inj_left[i] = WV_CMD_HOLD; }  /* Berserker Barrage: gun */
            if (inj_left[i]) for (k = 0; k < 4; k++) dir_hist[i][k] = 0;
        }
        last_btn[i] = btn;
        if (inj_left[i]) {
            u16 m = (u16)(0x70u << sh);
            inj_left[i]--;
            *in0 = (u16)((*in0 | m) & ~((u16)inj_bits[i] << sh));
        }
    }
}
