/* Binds the readable routines into the lifted game: same entry, same registers and flags left behind, because the lifted code around them reads those.
   This file is the adapter, so registers appear here and only here.
   HOST_CHECK: a recorded IRQ that lands inside a routine needs that routine's instruction points, so those calls take the lifted body. Counted. */
#include "game_hot.h"
typedef struct { u32 d[8]; u32 a[8]; u32 ccz, ccn, ccc, ccv, ccx; } Cpu;
#ifdef SAT_TARGET
register Cpu *R __asm__("r14");
#else
extern Cpu *R;
#endif
#define LOW16(reg, v) ((reg) = ((reg) & 0xffff0000u) | ((u32)(v) & 0xffffu))
#define FLAGS(z, n, c, v, x) (R->ccz = (z), R->ccn = (n), R->ccc = (c), R->ccv = (v), R->ccx = (x))

#ifdef HOST_CHECK
extern u32 irq_pc;
long game_bind_fallbacks, game_bind_native;
#define GUARD(lifted, from, to) if (irq_pc >= (from) && irq_pc < (to)) { extern void lifted(void); game_bind_fallbacks++; lifted(); return; } game_bind_native++;
#else
#define GUARD(lifted, from, to)
#endif

void f_209d4(void)
{
    TargetListResult r;
    GUARD(lifted_209d4, 0x209d4u, 0x20a10u)
    r.last_entry = R->a[3];
    target_list_prune(&r);
    R->a[3] = r.last_entry;
    R->a[4] = 0xff19feu;
    R->d[6] = 0xffffu;
    R->d[0] = r.empty ? 1u : 0u;
    FLAGS(!r.empty, 0, 0, 0, 0);
}

void f_aa840(void)
{
    DrawSortResult r;
    unsigned count;
    GUARD(lifted_aa840, 0xaa840u, 0xaa886u)
    draw_list_sort(&r, &count);
    R->d[0] = count;
    if (!r.sorted) return;
    R->d[0] = 0xffffu;
    LOW16(R->d[1], 0xffffu);
    LOW16(R->d[2], r.key);
    R->a[0] = r.slot_prev;
    R->a[2] = r.slot;
    R->a[3] = r.held;
    R->a[4] = r.scan;
    R->a[6] = r.compared;
}

void f_aa59a(void)
{
    SpriteOriginResult r;
    u32 shifted, out;
    GUARD(lifted_aa59a, 0xaa59au, 0xaa5e8u)
#ifdef SAT_GUESTS
    { extern void sat_guest_group(unsigned long actor, unsigned long objptr); sat_guest_group(R->a[4], R->a[1]); }   /* bonus characters: rt/guests.c */
#endif
    sprite_origin_compute(&r, R->a[4], R->a[0]);
    R->a[0] += 4;
    R->d[2] = r.offset_swapped;
    R->d[3] = r.packed;
    shifted = (r.facing_bits << 5) & 0xffu;
    out = (r.facing_bits >> 3) & 1u;
    R->d[1] = shifted;
    FLAGS(shifted == 0, (shifted & 0x80u) != 0, out, 0, out);
}

#ifdef SAT_GUESTS
/* Bonus characters (build.py GUEST_WRAP keeps each lifted body whole as lifted_NNN):
   - the collision passes f_1cf54 and f_1d03e (attacker a6, target a1) run with a Wolverine player's own boxes in place
     (saturn/guests/wolverine/wolverine.c). f_1d03e is the players' melee pass (list 0xfff112 targets, 0x1cc3e), f_1cf54 the enemy and shot passes.
   - a Wolverine player's gun shots do no damage (no gun for him): the pass answers "no hit" the way the lifted body does at its exit.
   - f_195ec (the player state machine, a6 = block) is held on some ticks to stretch Schaefer's state timers to MSHvSF's. */
extern void sat_guest_wolverine_boxes(unsigned long a6, unsigned long a1, int restore) __attribute__((weak));
extern int sat_guest_wolverine_bullet(unsigned long a6) __attribute__((weak));
extern int sat_guest_wolverine_tick(unsigned long a6) __attribute__((weak));
u8 wv_hdbg[8];   /* Yaba probe: calls with a player attacker: 0 f_1cf54, 1 f_1d03e, 2 f_1d116; hits: 3 f_1cf54, 4 f_1d03e, 5 f_1d116; 6 shots refused */
static void guest_pass(void (*lifted)(void), int which)
{
    if (sat_guest_wolverine_bullet && sat_guest_wolverine_bullet(R->a[6])) {
        wv_hdbg[6]++;
        R->d[0] = 0;
        FLAGS(1, 0, 0, 0, 0);
        return;
    }
    if (!sat_guest_wolverine_boxes) { lifted(); return; }
    sat_guest_wolverine_boxes(R->a[6], R->a[1], 0);
    lifted();
    sat_guest_wolverine_boxes(0, 0, 1);
    if (R->a[6] >= 0xff8380u && R->a[6] < 0xff8580u) { wv_hdbg[which]++; if (R->d[0] == 1) wv_hdbg[3 + which]++; }
}
void f_1cf54(void) { extern void lifted_1cf54(void); guest_pass(lifted_1cf54, 0); }
void f_1d03e(void) { extern void lifted_1d03e(void); guest_pass(lifted_1d03e, 1); }
void f_1d116(void) { extern void lifted_1d116(void); guest_pass(lifted_1d116, 2); }
void f_195ec(void)
{
    extern void lifted_195ec(void);
    if (sat_guest_wolverine_tick && !sat_guest_wolverine_tick(R->a[6])) return;
    lifted_195ec();
}
#endif

void f_1689a(void)
{
    MeleeCheck c;
    GUARD(lifted_1689a, 0x1689au, 0x16924u)
    melee_candidate_check(&c, R->a[6], R->a[1], R->a[0]);
    if (c.stage == 0) return;
    LOW16(R->d[0], c.distance);
    R->d[1] = c.limit;
    if (c.stage == 1) return;
    R->a[2] = c.box;
    R->d[0] = c.distance;
    R->d[1] = c.reach;
}
