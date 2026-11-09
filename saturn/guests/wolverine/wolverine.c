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
#ifdef SAT_WOLVERINE_DEBUG
s16 wv_dbg[2][12];
s16 wv_lst[2][3];   /* per player: objects before his tiles, tiles asked, tiles that fit (a full list drops his tiles) */
#endif
static u8 step_[2], left_[2], face_[2], cur_[2] = {255, 255}, chain_[2], lastc_[2], held_[2], hitk_[2], restart_[2], gap_[2], cstg_[2];
static u16 acc_[2], exec_[2], wall_[2];
static u8 landed_[2];   /* his attack in the current chain hit something (the collision hook saw the target take a hit) */
static s16 sx_[2], sz_[2];   /* sub-pixel remainder of the walk speed scale, 1/16 px */
static u16 xb_[2], zb_[2];  /* position before this tick's native update */
static u16 hp_[2];   /* health before a hit; the hit's size picks his reaction */
static void wv_reset(int i);

/* Schaefer's player block state +4 +5 +6, measured under MAME (tools/wolverine/schaefer_states.lua, 11-08):
   020000 stand, 020002 walk (also depth and the dash), 020004 jump, 020006 attack (chain), 02000e chain finisher, 02000c gun,
   020008 special (attack + jump), 0202xx hit (about 28 frames; 107 when knocked down), 0204xx grab and throw (walking into an enemy),
   0208xx getting up, 04xxxx dying, 08xxxx entering. His own moves take their place: the gun is the Berserker Barrage (no gun for him),
   the special the Tornado Claw, a hit held past 40 frames the knockdown. */
#ifndef WV_HIT_MEDIUM
#define WV_HIT_MEDIUM 13   /* health a hit took: medium from here, heavy from WV_HIT_HEAVY (player hits seen: 10 to 17, docs/notes/AVP_NOTES_ACTOR.md) */
#define WV_HIT_HEAVY 17
#endif
#define ONCE(m) ((m) == WV_JUMP || (m) == WV_LP || (m) == WV_HP || (m) == WV_HK || (m) == WV_TORNADO || (m) == WV_KNOCKDOWN || (m) == WV_THROW || (m) == WV_HIT_ETC || (m) == WV_HIT_M || (m) == WV_HIT_H)
/* Attack chain: Schaefer's attack state 020006 repeats while the button is tapped (measured: 56 ticks of it for about four 15-tick attacks, the
   state byte never leaves it), so each new attack of a chain is told by the native ticks of the one before it: when the update that follows its 15th has
   run and the state is still 020006 (post = 1; before that update a lone attack looks the same). His chain is light, light, heavy, then the kick as the finisher (MSHvSF normals); it starts over after WV_CHAIN_GAP ticks without an
   attack. chain_ is the stage of the NEXT attack. */
#ifndef WV_CHAIN_GAP
#define WV_CHAIN_GAP 30
#endif
#define WV_NAT_ATK 15
static int move_for(int i, int post)
{
    u8 a = R8(PL(i) + 4), b = R8(PL(i) + 5), c = R8(PL(i) + 6);
    int m = WV_IDLE;
    if (a == 2 && b == 0) {
        switch (c) {
        case 0x02: m = WV_WALK; break;
        case 0x04: m = WV_JUMP; break;
        case 0x06:   /* each new attack takes the next of his normals */
            if (lastc_[i] != 0x06 || (post && exec_[i] > WV_NAT_ATK && (cur_[i] == WV_LP || cur_[i] == WV_HP || cur_[i] == WV_HK))) {
#ifdef SAT_WV_NATIVE_TIMING
                if (!landed_[i]) chain_[i] = 0;   /* the chain goes on only from a landed hit; a whiff starts it over */
#endif
                landed_[i] = 0;
                cstg_[i] = chain_[i];
                chain_[i] = (u8)((chain_[i] + 1) & 3);
                if (lastc_[i] == 0x06) restart_[i] = 1;
            }
            m = wv_chain_tab[cstg_[i]]; break;
        case 0x0e: m = WV_HK; break;
        case 0x0c: m = WV_BERSERKER; break;
        case 0x08: m = WV_TORNADO; break;
        }
    } else if (a == 2 && b == 2) {
        /* A hit that does not knock him down is one of three standing reactions of MSHvSF (hitstun of the capture, state +06 = 12), by the health
           the hit took: light (the stagger back), medium (arched back and hunched), heavy (curled and recovering). Longer than 40 ticks is the knockdown. */
        if (!held_[i]) {
            u16 hp = R16(PL(i) + 0x40), d = hp_[i] > hp ? (u16)(hp_[i] - hp) : 0;
            hitk_[i] = (u8)(d >= WV_HIT_HEAVY ? 2 : d >= WV_HIT_MEDIUM ? 1 : 0);
        }
        m = held_[i] > 40 ? WV_KNOCKDOWN : hitk_[i] == 2 ? WV_HIT_H : hitk_[i] == 1 ? WV_HIT_M : WV_HIT_ETC;
    }
    else if (a == 2 && b == 4) m = WV_THROW;
    else if (a == 2 && b == 8) m = WV_CROUCH;   /* getting up: his crouch rises back to stand */
    else if (a == 4) m = WV_KNOCKDOWN;
    else if (a == 8) m = WV_WALK;
    if (!(a == 2 && b == 2)) hp_[i] = R16(PL(i) + 0x40);
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
/* Lane wolverine-ground, default off: -DSAT_WV_SCALE=S draws him at S/16 of his size (sat_gfx put_sprite_fit_s, same scaled-sprite command) and scales his
   boxes with him: centre and half sizes by S/16 about his feet (depth bytes are AvP's and stay). Unset: no code at all. */
#ifdef SAT_WV_SCALE
#define WVS(v) ((int)(v) * SAT_WV_SCALE / 16)
#define WVH(v) (WVS(v) < 1 ? 1 : WVS(v))
#else
#define WVS(v) (v)
#define WVH(v) (v)
#endif
extern u8 *PAGE[256];
#define PBY(a) (PAGE[((u32)(a) >> 16) & 0xff] + ((u32)(a) & 0xffff))
/* One aligned word publishes a complete pose/box step to the vblank snapshot.
   The IRQ must not combine cur_ from a new move with its previous step_. */
static volatile u16 wv_step_now[2] = {0xffff, 0xffff};
static u8 atk_cache[2][16];                       /* last nonzero attack index per Schaefer state +6 (by state >> 1) */
static struct { u8 *p; u8 v[4]; } undo[8];
static int hit_i = -1;   /* Wolverine attacker of the collision call in flight */
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
    if (k >= wv_move_start[WV_MOVES]) return 0;
    if (!wv_box[k].uw) return &wv_box[wv_move_start[WV_IDLE]];   /* a step without a capture keeps his standing hurt box */
    return &wv_box[k];
}
/* restore = 0: before the call; 1: after it; 2: after it, and the pass answered hit (d0 = 1) */
void sat_guest_wolverine_boxes(unsigned long a6, unsigned long a1, int restore)
{
    int i, slot;
    if (restore) {
        if (hit_i >= 0 && restore == 2) landed_[hit_i] = 1;   /* the pass answered hit (d0 = 1) */
        hit_i = -1;
        while (nundo > 0) { nundo--; { int k; for (k = 0; k < 4; k++) undo[nundo].p[k] = undo[nundo].v[k]; } }
        return;
    }
    nundo = 0;
    if (!WV_HAVE_BOXES) return;
    hit_i = -1;
    if ((i = wv_player((u32)a6)) >= 0) {   /* his hit */
        const WvBox *w = box_now(i);
        u32 fr = rd32((u32)a6 + 0x1c), t = rd32((u32)a6 + 0x50);
        u8 *f = PBY(fr), idx = f[9];
        int att = attack_state(i, &slot);
        hit_i = i;
        if (att && idx) atk_cache[i][slot] = idx;
        if (!att || !w || !w->hw) { if (idx) poke4(f + 8, f[8], 0, f[10], f[11]); }
        else {
            if (!idx) idx = atk_cache[i][slot];
            if (idx) {
                u8 *r = PBY(t + rd16(t + 2) + (u32)(s8)idx * 16);
                if (idx != f[9]) poke4(f + 8, f[8], idx, f[10], f[11]);
                poke4(r, WVS(-w->hx), WVS(w->hy), WVH(w->hw), WVH(w->hh));   /* AvP's record x is backward-positive (f_1d25e negates it when +0f is set, facing right) */
            }
        }
    }
    if ((i = wv_player((u32)a1)) >= 0) {   /* his hurt box */
        const WvBox *w = box_now(i);
        u32 fr = rd32((u32)a1 + 0x1c), t = rd32((u32)a1 + 0x50);
        u8 idx = PBY(fr)[8];
        if (w && idx) poke4(PBY(t + rd16(t) + (u32)(s8)idx * 8), WVS(-w->ux), WVS(w->uy), WVH(w->uw), WVH(w->uh));
    }
}
/* Debug for the box sheets (wv_box_dbg[player]): Schaefer's own attack and hurt box from his frame (x0 y0 x1 y1, object coordinates),
   then Wolverine's. 9999 = none. */
#ifdef SAT_WOLVERINE_DEBUG
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
#endif

static void put16(u8 *p, u16 v) { p[0] = (u8)(v >> 8); p[1] = (u8)v; }
#ifndef SAT_GUEST_PAL_KEEP
#define SAT_GUEST_PAL_KEEP 0   /* default off: the snapshot recopies sprite palette page 0 and the guest rewrites its rows every frame (as v4.1) */
#endif
#if SAT_GUEST_PAL_KEEP
extern int sat_guest_pal_keep;   /* sat_gfx.c: the page still holds this guest's rows from the last snapshot and the game's page did not change */
#endif
#ifndef SAT_GUEST_FAST_LIST
#define SAT_GUEST_FAST_LIST 0   /* default off: byte loops as v4.1 */
#endif
#if SAT_GUEST_FAST_LIST
/* The pass rewrites the 8 byte object list on the master in the snapshot, from cart code: word moves and one 32 bit store a half entry. */
typedef u32 __attribute__((may_alias)) au32;
static void put32b(u8 *p, u32 v)
{
#if defined(__BYTE_ORDER__) && __BYTE_ORDER__ == __ORDER_BIG_ENDIAN__
    *(au32 *)(void *)p = v;
#else
    p[0] = (u8)(v >> 24); p[1] = (u8)(v >> 16); p[2] = (u8)(v >> 8); p[3] = (u8)v;
#endif
}
static void copy8(u8 *d, const u8 *s) { ((au32 *)(void *)d)[0] = ((const au32 *)(const void *)s)[0]; ((au32 *)(void *)d)[1] = ((const au32 *)(const void *)s)[1]; }
#endif

/* The block's character byte is not stable at KO: in the dying state (04) the game's death blink toggles byte +1 between its value and 0 every frame
   (Yaba 11-09, state 0400 for about 60 frames, Schaefer and Wolverine alike; the blank frames are the game hiding the body). Read raw, the slot stopped
   being his every other frame, wv_reset restarted his clock each time and the knockdown never got past its first pose. The identity is latched while he is
   alive and kept while the state is dying; the body is hidden on the blank frames (wv_blank), as the game hides Schaefer's. */
static u8 wvid_[2];
static int is_wolverine(int i)
{
    if (R8(PL(i)) == 0) return wvid_[i] = 0;
    if (R8(PL(i) + 4) == 4 && wvid_[i]) return 1;
    return wvid_[i] = R8(PL(i) + WV_CHAR_OFF) == WV_CHAR_SCH;
}
static int wv_blank(int i)   /* the death blink's blank frame: the game draws no body */
{
    return R8(PL(i) + 4) == 4 && R8(PL(i) + WV_CHAR_OFF) != WV_CHAR_SCH;
}

/* Names: the game prints its character names from text in its ROM image, which the Saturn keeps in cart RAM (ROMB). While Wolverine is
   chosen, Schaefer's HUD name (16-byte field at 0xaedca) and his select-screen name (0xac699) read WOLVERINE; turned off, the bytes go back.
   Both are on pages the game reads, which stage files never take for tiles. */
#define ROMB ((volatile u8 *)0x02400000u)
static const struct { u32 at; u8 n; const char *wv; } wv_names[2] = {
    { 0xaedca, 16, "WOLVERINE       " },
    { 0xac699, 14, "  WOLVERINE   " },
};
#ifndef SAT_GUEST_NAMES_LAZY
#define SAT_GUEST_NAMES_LAZY 0   /* default off: check the name bytes every snapshot (as v4.1) */
#endif
static u8 name_saved[2][16], names_on;
static void names(int on)
{
    int i, k;
    if (on == names_on) {
        if (!on) return;
#if SAT_GUEST_NAMES_LAZY
        /* The check below reads 30 bytes of cart RAM (A-bus) every snapshot, on the master: about 15 FRT ticks a snapshot (Yaba, lane fps-held).
           Only a stage load restores the page, so check again only when the load count moves. =2 never checks (measurement only). */
        {
            extern struct { u32 current, loads, sectors, last_vblank; } sat_rounds;
            static u32 seen_loads = 0xffffffffu;
            if (SAT_GUEST_NAMES_LAZY == 2 || sat_rounds.loads == seen_loads) return;
            seen_loads = sat_rounds.loads;
        }
#endif
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

/* Move clock and timings (option B). The clock runs in player updates (source
   0x195ec), never in snapshots. The existing measured native tick estimates
   distribute updates through a longer captured move. A shorter actual native
   path cannot truncate the remaining guest recovery: the post-hook observes
   its return, without rolling back game RAM or replaying damage calls.
   This is a duration/presentation contract, not a proof that AvP's attack,
   damage or hitstop mechanics now match MSHvSF. Longer native moves are kept.
   Held ticks freeze this player's native update; other actors still run. */
#ifdef SAT_WOLVERINE_DEBUG
u8 wv_tdbg[5][4];   /* per held move (LP HP HK Berserker Tornado): last ticks run, last ticks passed, times seen, last T */
#endif
#if !defined(WV_MEASURE) || defined(SAT_WOLVERINE_DEBUG)
static int tslot(int m) { return m == WV_LP ? 0 : m == WV_HP ? 1 : m == WV_HK ? 2 : m == WV_BERSERKER ? 3 : m == WV_TORNADO ? 4 : -1; }
#endif
/* Schaefer's ticks per state slot (table wv_nat_tab, tools/wolverine/gen_c.py NATIVE), MAME tools/wolverine/schaefer_states.lua: a tap of attack 15, the finisher
   02000e 32, the special 020008 57; gun 02000c measured on Yaba from wv_tdbg. 0 = never held. */
static u16 wv_nat(int move)
{
#ifdef WV_MEASURE
    return 0;   /* test build: no holds, wv_tdbg shows Schaefer's own tick counts */
#endif
    return move < WV_MOVES ? wv_nat_tab[move] : 0;   /* wv_nat_tab: gen_c.py NATIVE */
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
/* A native attack can return sooner than wv_nat predicts. Keep only its remaining
   presentation/recovery time; the completed game state is never rolled back and
   no additional damage calls are invented. Hit, grab, death and entry states
   cancel this hold immediately. */
static u8 recovery_[2];
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

static void wv_begin_move(int i, int move)
{
#ifdef SAT_WOLVERINE_DEBUG
    if (cur_[i] < WV_MOVES && tslot(cur_[i]) >= 0 && exec_[i]) {
        u8 *d = wv_tdbg[tslot(cur_[i])];
        d[0] = (u8)(exec_[i] > 255 ? 255 : exec_[i]);
        d[1] = (u8)(wall_[i] > 255 ? 255 : wall_[i]);
        d[2]++;
    }
#endif
    cur_[i] = (u8)move;
    step_[i] = left_[i] = wwalk_[i] = recovery_[i] = restart_[i] = 0;
    acc_[i] = exec_[i] = wall_[i] = 0;
}

/* Publish this tick's pose before aging it. A one-tick opening pose must be
   visible once; advancing at ++left >= frames used to skip it altogether. */
static void wv_advance(int i)
{
    int move = cur_[i];
    int n = wv_move_start[move + 1] - wv_move_start[move];
    if (move == WV_WALK) wv_walk_step(i);
    else {
        if (step_[i] >= n) step_[i] = 0;
        if (left_[i] >= wv_steps[wv_move_start[move] + step_[i]].frames) {
            left_[i] = 0;
            if (step_[i] + 1 < n) step_[i]++;
            else if (!ONCE(move)) step_[i] = 0;
        }
        if (left_[i] < 255) left_[i]++;
    }
    wv_step_now[i] = (u16)(wv_move_start[move] + step_[i]);
    if (wall_[i] < 65535) wall_[i]++;
}

static int wv_resting(int i)
{
    return R8(PL(i) + 4) == 2 && R8(PL(i) + 5) == 0 &&
           (R8(PL(i) + 6) == 0 || R8(PL(i) + 6) == 2);
}

/* One player update, independently of how often its picture is drawn. A
   completed native state stays completed: only a subsequent idle/walk update
   is held for the remaining captured recovery. Other state changes interrupt
   the guest immediately and retain all externally written game fields. */
static int wv_tick_move(int i)
{
    int move = move_for(i, 0), hold = 0, T, nat;
    held_[i] = (R8(PL(i) + 4) == 2 && R8(PL(i) + 5) == 2) ?
        (u8)(held_[i] < 255 ? held_[i] + 1 : 255) : 0;
    if (recovery_[i] && wv_resting(i) && wall_[i] < wv_move_len(cur_[i])) {
        wv_advance(i);
        return 0;
    }
    if (move == WV_LP || move == WV_HP || move == WV_HK || move == WV_BERSERKER || move == WV_TORNADO) gap_[i] = 0;
    else if (gap_[i] < 255 && ++gap_[i] > WV_CHAIN_GAP) chain_[i] = 0;
    if (move != cur_[i] || recovery_[i] || restart_[i]) wv_begin_move(i, move);
    wv_advance(i);
    nat = wv_nat(move);
    if (nat && move == WV_HK && R8(PL(i) + 6) == 0x06) nat = WV_NAT_ATK;   /* the chain's kick runs in the attack state's 15 ticks */
    if (nat && WV_HAVE_BOXES) {
        T = wv_move_len(move);
#ifdef SAT_WOLVERINE_DEBUG
        wv_tdbg[tslot(move)][3] = (u8)T;
#endif
        /* Run the first native update on tick 1 and the last on tick T.
           The old nat/T accumulator finished a 15-update, 51-tick move on
           tick 49. Distribute the remaining nat-1 updates over T-1 ticks. */
        if (T > nat && exec_[i] && wall_[i] < (u16)T) {
            u32 next = (u32)acc_[i] + (u32)nat - 1u;
            if (next < (u32)T - 1u) hold = 1;
            else next -= (u32)T - 1u;
            acc_[i] = (u16)next;
        }
    }
    if (!hold && exec_[i] < 65535) exec_[i]++;
    return !hold;
}
/* His ground speed (wv_speed_tab, 16 = Schaefer's): the native walk moved the player dx, dz this tick; the difference to the scaled step is added now,
   with the remainder kept, to x and to both depth words. A jump of position (scene cut, knock-back) is left alone. */
static void wv_speed(int i)
{
    int sp = wv_speed_tab[WV_WALK], dx, dz, e;
    if (sp == 16 || R8(PL(i) + 4) != 2 || R8(PL(i) + 5) != 0 || R8(PL(i) + 6) != 2) { sx_[i] = sz_[i] = 0; return; }
    dx = (s16)(R16(PL(i) + 0x10) - xb_[i]); dz = (s16)(R16(PL(i) + 0x18) - zb_[i]);
    if (dx > 24 || dx < -24 || dz > 24 || dz < -24) return;
    sx_[i] = (s16)(sx_[i] + dx * (sp - 16)); e = sx_[i] / 16; sx_[i] = (s16)(sx_[i] - e * 16);
    R16(PL(i) + 0x10) = (u16)(R16(PL(i) + 0x10) + e);
    sz_[i] = (s16)(sz_[i] + dz * (sp - 16)); e = sz_[i] / 16; sz_[i] = (s16)(sz_[i] - e * 16);
    R16(PL(i) + 0x14) = (u16)(R16(PL(i) + 0x14) + e);
    R16(PL(i) + 0x18) = (u16)(R16(PL(i) + 0x18) + e);
}
/* wrapper hook for f_195ec (player state machine, a6 = the player's block): 1 run it, 0 skip this tick */
int sat_guest_wolverine_tick(unsigned long a6)
{
    int i = wv_player((u32)a6);
    if (i < 0) {
        if (a6 == PL(0) || a6 == PL(1)) wv_reset((int)((a6 - PL(0)) >> 8));
        return 1;
    }
    xb_[i] = R16(PL(i) + 0x10); zb_[i] = R16(PL(i) + 0x18);
    return wv_tick_move(i);
}

/* source 0x195ec: observe the state selected by the native player update in
   this same tick. Waiting until the next pre-hook lost the first pose and let
   early native returns truncate the guest's move. No game field is restored. */
void sat_guest_wolverine_after_tick(unsigned long a6)
{
    int i = wv_player((u32)a6), move;
    if (i < 0) {
        if (a6 == PL(0) || a6 == PL(1)) wv_reset((int)((a6 - PL(0)) >> 8));
        return;
    }
    wv_speed(i);
    move = move_for(i, 1);
    if (move == cur_[i] && !restart_[i]) return;
#ifndef WV_MEASURE
    if (cur_[i] < WV_MOVES && tslot(cur_[i]) >= 0 &&
        WV_HAVE_BOXES && wv_resting(i)) {
        recovery_[i] = 1;
        return;
    }
#endif
    wv_begin_move(i, move);
    wv_advance(i);
    exec_[i] = 1;
}
/* Pick-ups (game_bind.c f_19f9a): he takes food and score items only (kinds 0a and 0b of the item's byte +2); weapons and held items stay on the floor.
   MSHvSF's Wolverine has no items. Returns nonzero when the pick-up is allowed. */
int sat_guest_wolverine_pickup(unsigned long a6, unsigned long a4)
{
    u8 kind;
    if (wv_player((u32)a6) < 0) return 1;
    kind = PBY(0xff0000u | ((u32)a4 & 0xffffu))[2];
    return kind == 0x0a || kind == 0x0b;
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
#ifdef SAT_GUEST_PROF
u32 sat_gprof_w[8];   /* measurement: ticks summed over calls that drew a guest: 0 names, 1 setup, 2 remove Schaefer's sprites, 3 shift, 4 tiles, 5 palette, 6 calls */
#define WT() ((((u32)*(volatile u8 *)0xfffffe12UL << 8) | *(volatile u8 *)0xfffffe13UL) & 0xffffu)
#define WM(slot) do { u32 t_ = WT(); wp_[slot] += (t_ - wl_) & 0xffffu; wl_ = t_; } while (0)
#else
#define WM(slot) ((void)0)
#endif
int sat_guest_objects(u8 *obj, int count, int max, u8 *pal0)
{
    int i, k, n, j, any = 0;
#ifdef SAT_GUEST_PROF
    u32 wp_[8] = {0, 0, 0, 0, 0, 0, 0, 0}, wl_ = WT();
#endif
    names(sat_guest_sel & 1);
    WM(0);
    if (!(sat_guest_sel & 1)) return count;
    for (i = 0; i < 2; i++) {
        u16 x, cam, draw_step;
        int st, sx, sy;
        if (!is_wolverine(i)) continue;
        any = 1;
        if (wv_blank(i)) continue;
        WM(0);
        x = R16(PL(i) + 0x10);
        face_[i] = (u8)((R8(PL(i) + 0x0f) & 1) ^ 1);   /* +0f set = facing right (Yaba 11-08: set while walking right); his poses were captured facing right, so they mirror when it is clear */
        /* A snapshot may happen before the first player update. It can show
           idle, but it must not tick simulation or choose an attack chain. */
        draw_step = wv_step_now[i];
        if (draw_step >= wv_move_start[WV_MOVES]) draw_step = wv_move_start[WV_IDLE];
        st = wv_steps[draw_step].pose;
        cam = R16(0xff8278);
        sx = (int)x - (int)cam + WV_OX;
        sy = WV_OY - 0x100 - (s16)R16(PL(i) + 0x14) + (s16)R16(0xff827c);   /* the camera's depth (ff827c, 0x100 at rest) scrolls him as it does Schaefer */
        {   /* height above his feet line (wv_lift, a jump): from the step's start value to its end value across the step */
            int l0 = wv_lift[2 * draw_step], l1 = wv_lift[2 * draw_step + 1];
            if (l0 | l1) {
                int fr = wv_steps[draw_step].frames, a = left_[i] > 0 ? left_[i] - 1 : 0;
                sy -= l0 + (fr > 1 ? (l1 - l0) * (a > fr ? fr : a) / fr : 0);
            }
        }
#ifdef SAT_WV_GROUND   /* lane wolverine-ground, default off: the step's feet-on-the-floor offset (gen_c.py wv_gy, tools/wolverine/ground.py) */
        sy += wv_gy[draw_step];
#endif
#ifdef SAT_WOLVERINE_DEBUG
        wv_dbg[i][0] = wv_dbg[i][1] = wv_dbg[i][4] = wv_dbg[i][5] = 9999; wv_dbg[i][2] = wv_dbg[i][3] = wv_dbg[i][6] = wv_dbg[i][7] = -9999;
        box_debug(i, sx, sy);
        wv_dbg[i][8] = (s16)sx; wv_dbg[i][9] = (s16)sy; wv_dbg[i][10] = (s16)(R8(PL(i) + 6) | R8(PL(i) + 5) << 8); wv_dbg[i][11] = (s16)(st | face_[i] << 12);
#endif
        WM(1);
        /* Schaefer's own sprites near him go */
        for (j = k = 0; j < count; j++) {
            u8 *e = obj + j * 8;
#if SAT_GUEST_FAST_LIST && defined(__BYTE_ORDER__) && __BYTE_ORDER__ == __ORDER_BIG_ENDIAN__
            int ex = (int)((((const au32 *)(const void *)e)[0] >> 16) & 0x3ff), pal = (int)(((const au32 *)(const void *)e)[1] & 31);
#else
            int ex = ((e[0] << 8 | e[1]) & 0x3ff), pal = e[7] & 31;
#endif
            if (ex >= 768) ex -= 1024;
            if (pal == WV_SCH_PAL && ex > sx - 140 && ex < sx + 140) {
#ifdef SAT_WOLVERINE_DEBUG
                int ey = ((e[2] << 8 | e[3]) & 0x3ff), w = ((e[6] >> 0) & 15) + 1, h = ((e[6] >> 4) & 15) + 1;
                if (ey >= 768) ey -= 1024;
                if (ex < wv_dbg[i][0]) wv_dbg[i][0] = (s16)ex;
                if (ey < wv_dbg[i][1]) wv_dbg[i][1] = (s16)ey;
                if (ex + 16 * w > wv_dbg[i][2]) wv_dbg[i][2] = (s16)(ex + 16 * w);
                if (ey + 16 * h > wv_dbg[i][3]) wv_dbg[i][3] = (s16)(ey + 16 * h);
#endif
                continue;
            }
#if SAT_GUEST_FAST_LIST
            if (k != j) copy8(obj + k * 8, e);
#else
            if (k != j) { int b; for (b = 0; b < 8; b++) obj[k * 8 + b] = e[b]; }
#endif
            k++;
        }
        count = k;
        WM(2);
        /* his tiles go at the head of the list: earlier entries are in front on the board */
        n = wv_pose_start[st + 1] - wv_pose_start[st];
#ifdef SAT_WOLVERINE_DEBUG
        wv_lst[i][0] = (s16)count; wv_lst[i][1] = (s16)n;
#endif
        if (count + n > max) n = max - count;
#ifdef SAT_WOLVERINE_DEBUG
        wv_lst[i][2] = (s16)n;
#endif
#if SAT_GUEST_FAST_LIST
        for (j = count - 1; j >= 0; j--) copy8(obj + (j + n) * 8, obj + j * 8);
#else
        for (j = count * 8 - 1; j >= 0; j--) obj[j + n * 8] = obj[j];
#endif
        WM(3);
        for (k = 0; k < n; k++) {
            const WvTile *t = &wv_tiles[wv_pose_start[st] + k];
            int hf = (t->flags & 1) ^ face_[i], dx = face_[i] ? -t->dx - 16 : t->dx;
            u8 *o = obj + k * 8;
#ifdef SAT_WOLVERINE_DEBUG
            if (sx + dx < wv_dbg[i][4]) wv_dbg[i][4] = (s16)(sx + dx);
            if (sy + t->dy < wv_dbg[i][5]) wv_dbg[i][5] = (s16)(sy + t->dy);
            if (sx + dx + 16 > wv_dbg[i][6]) wv_dbg[i][6] = (s16)(sx + dx + 16);
            if (sy + t->dy + 16 > wv_dbg[i][7]) wv_dbg[i][7] = (s16)(sy + t->dy + 16);
#endif
#if SAT_GUEST_FAST_LIST && !defined(SAT_WV_SCALE)   /* the scale comparison keeps the word writes */
            put32b(o, (u32)((sx + dx) & 0x3ff) << 16 | (u32)((sy + t->dy) & 0x3ff));
            put32b(o + 4, (u32)t->key << 16 | (u16)(((t->flags >> 2) ? WV_PALROW1 : WV_SCH_PAL) | (hf << 5) | ((t->flags & 2) << 5)));
#else
#ifdef SAT_WV_SCALE
            dx = (dx * SAT_WV_SCALE) >> 4;   /* about his centre line and the stance's sole row (7 rows above the grid bottom): tile origins stay S apart */
            put16(o, (u16)(((sx + dx) & 0x3ff) | ((16 - SAT_WV_SCALE) << 10)));
            put16(o + 2, (u16)((sy + (((t->dy + 7) * SAT_WV_SCALE) >> 4) - 7) & 0x3ff));
#else
            put16(o, (u16)((sx + dx) & 0x3ff));
            put16(o + 2, (u16)((sy + t->dy) & 0x3ff));
#endif
            put16(o + 4, t->key);
            put16(o + 6, (u16)(((t->flags >> 2) ? WV_PALROW1 : WV_SCH_PAL) | (hf << 5) | ((t->flags & 2) << 5)));
#endif
        }
        count += n;
        WM(4);
    }
    sat_guest_touched = any;
#if SAT_GUEST_PAL_KEEP
    if (any && !sat_guest_pal_keep)
#else
    if (any)
#endif
#if SAT_GUEST_FAST_LIST
    for (k = 0; k < 16; k += 2) { put32b(pal0 + WV_SCH_PAL * 32 + k * 2, (u32)wv_pal[k] << 16 | wv_pal[k + 1]); put32b(pal0 + WV_PALROW1 * 32 + k * 2, (u32)wv_pal[16 + k] << 16 | wv_pal[17 + k]); }
#else
    for (k = 0; k < 16; k++) { put16(pal0 + WV_SCH_PAL * 32 + k * 2, wv_pal[k]); put16(pal0 + WV_PALROW1 * 32 + k * 2, wv_pal[16 + k]); }
#endif
#ifdef SAT_GUEST_PROF
    if (any) { WM(5); wp_[6] = 1; for (k = 0; k < 7; k++) sat_gprof_w[k] += wp_[k]; }
#endif
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
static void wv_reset(int i)
{
    int k;
    cur_[i] = 255;
    step_[i] = left_[i] = face_[i] = chain_[i] = lastc_[i] = held_[i] = hitk_[i] = restart_[i] = gap_[i] = cstg_[i] = landed_[i] = 0; hp_[i] = 0;
    sx_[i] = sz_[i] = 0;
    acc_[i] = exec_[i] = wall_[i] = wph_[i] = wlx_[i] = wlz_[i] = 0;
    wwalk_[i] = recovery_[i] = inj_left[i] = inj_bits[i] = last_btn[i] = wvid_[i] = 0;
    wv_step_now[i] = 0xffff;
    for (k = 0; k < 16; k++) atk_cache[i][k] = 0;
    for (k = 0; k < 4; k++) dir_hist[i][k] = dir_age[i][k] = 0;
}
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
    if (!(sat_guest_sel & 1)) {
        wv_reset(0); wv_reset(1);
        return;
    }
    for (i = 0; i < 2; i++) {
        int sh = i * 8, d;
        u8 w = (u8)~(*in0 >> sh), btn;
        if (!is_wolverine(i)) { wv_reset(i); continue; }
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
