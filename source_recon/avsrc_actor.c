#include "avsrc_actor.h"

const u8 *g_avsrc_rom;

static u32 mem8(const AvsrcMem *m, u32 a)
{
    if (a >= 0xff0000u) return m->ram[a - 0xff0000u];
    return g_avsrc_rom[a];
}
static u32 mem16(const AvsrcMem *m, u32 a) { return (mem8(m, a) << 8) | mem8(m, a + 1); }
static u32 mem32(const AvsrcMem *m, u32 a) { return (mem16(m, a) << 16) | mem16(m, a + 2); }
static void copy16(AvsrcMem *m, u32 to, u32 from) { RAM16W(m, to, RAM16(m, from)); }

/* Field sets cleared on release, as longs. Tag 8 keeps +0x6c, tag 12 also clears +0x46. */
static const u8 CLEAR_SHORT[] = { 0x00, 0x04, 0x0c, 0xff };
static const u8 CLEAR_TAG8[] = { 0x00, 0x04, 0x0c, 0x2c, 0x54, 0x5c, 0x4c, 0x70, 0x74, 0xff };
static const u8 CLEAR_TAG12[] = { 0x00, 0x04, 0x0c, 0x2c, 0x54, 0x5c, 0x4c, 0x46, 0x70, 0x6c, 0x74, 0xff };
static const u8 CLEAR_FULL[] = { 0x00, 0x04, 0x0c, 0x2c, 0x54, 0x5c, 0x4c, 0x70, 0x6c, 0x74, 0xff };

typedef struct ActorPool {
    u32 first_slot;
    u32 slots;
    u32 stride;
    u32 tag;
    u32 count_addr;     /* byte */
    u32 top_addr;       /* word: low half of the stack pointer */
    u32 stack_end;      /* first word past the stack */
    u32 dispatch;       /* class table in ROM; 0 when not traversed */
    const u8 *clear;
} ActorPool;

static const ActorPool POOLS[POOL_COUNT] = {
    { 0xff8680u, 24, 0x80,  0x04, 0xffee7cu, 0xffee50u, 0xffee92u, 0x1b878u, CLEAR_FULL },
    { 0xff9280u,  4, 0xc0,  0x08, 0xffee7eu, 0xffee54u, 0xffeef2u, 0x1b958u, CLEAR_TAG8 },
    { 0xff9580u, 20, 0xc0,  0x0c, 0xffee80u, 0xffee58u, 0xffeeeau, 0x1b9b6u, CLEAR_TAG12 },
    { 0xffa480u, 20, 0x80,  0x10, 0xffee83u, 0xffee5eu, 0xffef1au, 0x1b8eeu, CLEAR_FULL },
    { 0xffae80u, 16, 0x80,  0x14, 0xffee85u, 0xffee62u, 0xffef3au, 0x1bc7au, CLEAR_FULL },
    { 0xffb680u, 32, 0x80,  0x18, 0xffee89u, 0xffee6au, 0xffef7au, 0x1ba94u, CLEAR_FULL },
    { 0xffc680u, 16, 0x80,  0x1c, 0xffee8cu, 0xffee70u, 0xffef9au, 0x1bd0cu, CLEAR_FULL },
    { 0xffce80u,  4, 0x100, 0x20, 0xffee8eu, 0xffee74u, 0xffefa2u, 0,        CLEAR_SHORT },
    { 0xffd280u, 64, 0x40,  0x24, 0xffee8fu, 0xffee76u, 0xfff022u, 0x1bd7au, CLEAR_SHORT },
    /* QUIRK: this last pool carries tag 0x18 like pool 24 (0x17490), though its own alloc is 0x178da. */
    { 0xffe280u, 16, 0x80,  0x18, 0xffee90u, 0xffee78u, 0xfff042u, 0,        CLEAR_SHORT }
};

u32 pool_alloc(AvsrcMem *m, ActorPoolId pool)
{
    const ActorPool *p = &POOLS[pool];
    u32 top, slot;
    if (RAM8(m, p->count_addr) == 0) return 0;
    RAM8(m, p->count_addr)--;
    top = 0xff0000u | RAM16(m, p->top_addr);
    slot = 0xff0000u | RAM16(m, top);
    RAM16W(m, p->top_addr, top + 2);
    return slot;
}

void pool_release(AvsrcMem *m, ActorPoolId pool, u32 slot)
{
    const ActorPool *p = &POOLS[pool];
    const u8 *f;
    u32 top;
    for (f = p->clear; *f != 0xff; f++) RAM32W(m, slot + *f, 0);
    top = 0xff0000u | ((RAM16(m, p->top_addr) - 2) & 0xffffu);
    RAM16W(m, top, slot);
    RAM16W(m, p->top_addr, top);
    RAM8(m, p->count_addr)++;
}

/* Second list heads next to each free stack; their readers are not reconstructed yet. */
static const u32 LIST_HEADS[][2] = {
    { 0xffee52u, 0xf072u }, { 0xffee56u, 0xf07au }, { 0xffee5au, 0xf0a2u }, { 0xffee5cu, 0xf0cau }, { 0xffee60u, 0xf0f2u },
    { 0xffee66u, 0xf132u }, { 0xffee68u, 0xf152u }, { 0xffee6cu, 0xf192u }, { 0xffee6eu, 0xf1d2u }, { 0xffee72u, 0xf1f2u },
    { 0xffee7au, 0xf300u }
};
static const u32 LIST_COUNTS[] = {
    0xffee7du, 0xffee7fu, 0xffee81u, 0xffee82u, 0xffee84u, 0xffee87u, 0xffee88u, 0xffee8au, 0xffee8bu, 0xffee8du, 0xffee91u
};
static const u32 ROUND_WORDS_ZERO[] = {
    0xff1738u, 0xff173au, 0xff173cu, 0xff1a3cu, 0xff1a3eu, 0xff1a40u, 0xff1a42u, 0xff1a44u, 0xff1a46u, 0xff1a48u, 0xff1a4au,
    0xff1a50u, 0xff1a52u, 0xff1a54u, 0xff1a56u, 0xff1a58u, 0xff1a5au, 0xff1a5cu, 0xff1a5eu, 0xff1a60u, 0xff1a66u, 0xff1a10u,
    0xff1a12u, 0xff1eaau, 0xff19feu, 0xff1a00u, 0xff1a02u, 0xff1a04u, 0xff1a06u, 0xff1a08u, 0xff1a0au, 0xff1b14u, 0xff1b16u,
    0xff1b18u, 0xff1a38u, 0xff1a3au, 0xff1a4cu, 0xff1a4eu, 0xff1a0cu, 0xff1a0eu
};

static void clear_range(AvsrcMem *m, u32 first, u32 bytes)
{
    u32 i;
    for (i = 0; i < bytes; i++) RAM8(m, first + i) = 0;
}

void pools_reset(AvsrcMem *m)
{
    unsigned p;
    u32 i;
    for (p = 0; p < POOL_COUNT; p++) {
        const ActorPool *q = &POOLS[p];
        u32 stack_low = q->stack_end - q->slots * 2;
        clear_range(m, q->first_slot, q->slots * q->stride);
        RAM8(m, q->count_addr) = (u8)q->slots;
        for (i = 0; i < q->slots; i++) {
            u32 slot = q->first_slot + i * q->stride;
            RAM8(m, slot + ACT_TAG) = (u8)q->tag;
            /* QUIRK: pool 4 stacks upward from its base (0x17326), so it allocates lowest slot first;
               every other pool allocates highest first. */
            if (p == POOL_4) RAM16W(m, q->stack_end + i * 2, slot);
            else RAM16W(m, stack_low + (q->slots - 1 - i) * 2, slot);
        }
        RAM16W(m, q->top_addr, p == POOL_4 ? q->stack_end : stack_low);
    }
    clear_range(m, 0xffea80u, 0x40);
    clear_range(m, 0xff8228u, 0x40);
    RAM8(m, 0xff81d6u) = 0;
    RAM16W(m, 0xff802cu, 0x90c0);
    avsrc_actor_call(m, 0x1c164u, 0);
    avsrc_actor_call(m, 0xae2f4u, 0);
    avsrc_actor_call(m, 0x1d6fau, 0);
    RAM16W(m, 0xff173eu, 0xffff);
    RAM16W(m, 0xff1740u, 0xffff);
    RAM16W(m, 0xff1742u, 0xffff);
    for (i = 0; i < sizeof ROUND_WORDS_ZERO / sizeof ROUND_WORDS_ZERO[0]; i++) RAM16W(m, ROUND_WORDS_ZERO[i], 0);
    RAM8(m, 0xff221cu) = 0;
    RAM8(m, 0xff221du) = 0;
    clear_range(m, 0xff18feu, 0x100);
    for (i = 0; i < sizeof LIST_HEADS / sizeof LIST_HEADS[0]; i++) RAM16W(m, LIST_HEADS[i][0], LIST_HEADS[i][1]);
    for (i = 0; i < sizeof LIST_COUNTS / sizeof LIST_COUNTS[0]; i++) RAM8(m, LIST_COUNTS[i]) = 0;
}

void pool_traverse(AvsrcMem *m, ActorPoolId pool)
{
    const ActorPool *p = &POOLS[pool];
    u32 i;
    if (pool == POOL_20) {
        RAM16W(m, 0xff83f4u, 0);
        RAM16W(m, 0xff84f4u, 0);
        RAM16W(m, 0xff85f4u, 0);
        RAM16W(m, 0xff221cu, 0);
    }
    for (i = 0; i < p->slots; i++) {
        u32 slot = p->first_slot + i * p->stride;
        if (RAM8(m, slot + ACT_ACTIVE) == 0) continue;
        if ((pool == POOL_8 || pool == POOL_12) && RAM8(m, slot + ACT_FLASH_LEFT) != 0) {
            if (--RAM8(m, slot + ACT_FLASH_LEFT) == 0) RAM8(m, slot + 0x47) = 0;
        }
        avsrc_actor_call(m, mem32(m, p->dispatch + (u32)RAM8(m, slot + ACT_CLASS) * 4u), 0);
    }
}

/* Spawn entry, 16 bytes in ROM. */
#define SPAWN_CAMERA    0x00u  /* word: spawn once the camera reaches it; negative ends the table */
#define SPAWN_X         0x02u
#define SPAWN_Y         0x04u
#define SPAWN_KIND      0x06u  /* word: pool selector, or one of the two controls below */
#define SPAWN_CLASS     0x08u  /* word: class and variant; for controls, the argument */
#define SPAWN_MIN_DIFF  0x0au  /* byte: >0 needs difficulty >= it; <0 needs difficulty < its magnitude */
#define SPAWN_FORM      0x0bu  /* byte: nonzero needs this player form */
#define SPAWN_FACING    0x0cu
#define SPAWN_FIELD0C   0x0du
#define SPAWN_TIMER2A   0x0eu
#define SPAWN_KIND_SET  0x1cu
#define SPAWN_KIND_CALL 0x18u

static ActorPoolId spawn_kind_pool(u32 kind)
{
    /* source table 0x1c14c, in steps of four */
    static const ActorPoolId BY_KIND[] = { POOL_12, POOL_20, POOL_24, POOL_28, POOL_8, POOL_32 };
    return BY_KIND[kind / 4];
}

static int spawn_entry_applies(const AvsrcMem *m, u32 e)
{
    u32 gate = mem8(m, e + SPAWN_MIN_DIFF), form = mem8(m, e + SPAWN_FORM);
    u32 difficulty = RAM8(m, G_DIFFICULTY + 1);
    if (form != 0 && form != RAM8(m, G_PLAYER_FORM)) return 0;
    if (gate & 0x80u) return ((0x100u - gate) & 0xffu) > difficulty;
    return gate <= difficulty;
}

void spawn_table_step(AvsrcMem *m)
{
    u32 ctrl = G_SPAWN_CTRL, phase = RAM8(m, ctrl + 4), e;
    if (phase == 4) return;
    if (phase == 0) {
        RAM8(m, ctrl + 4) = 2;
        RAM32W(m, ctrl + 0x1c, mem32(m, 0x1be82u + (u32)RAM16(m, G_STAGE) * 2u));
    }
    e = RAM32(m, ctrl + 0x1c);
    for (;;) {
        u32 camera = mem16(m, e + SPAWN_CAMERA);
        if (camera & 0x8000u) {
            RAM8(m, ctrl + 4) = (u8)(RAM8(m, ctrl + 4) + 2);
            return;
        }
        if (camera > RAM16(m, G_CAMERA_X)) return;
        if (spawn_entry_applies(m, e)) {
            u32 kind = mem16(m, e + SPAWN_KIND);
            if (kind == SPAWN_KIND_SET) {
                RAM16W(m, G_SPAWN_SET, mem16(m, e + SPAWN_CLASS));
                avsrc_actor_call(m, 0x17a1eu, SPAWN_KIND_SET);
            } else if (kind == SPAWN_KIND_CALL) {
                avsrc_actor_call(m, 0xad580u, mem16(m, e + SPAWN_CLASS));
            } else {
                u32 slot = pool_alloc(m, spawn_kind_pool(kind));
                /* A full pool keeps the cursor here, so the entry retries on the next tick. */
                if (slot == 0) return;
                RAM8(m, slot + ACT_ACTIVE)++;
                RAM16W(m, slot + ACT_CLASS, mem16(m, e + SPAWN_CLASS));
                RAM16W(m, slot + ACT_X, mem16(m, e + SPAWN_X));
                RAM16W(m, slot + ACT_Y, mem16(m, e + SPAWN_Y));
                RAM8(m, slot + ACT_FACING) = (u8)mem8(m, e + SPAWN_FACING);
                RAM8(m, slot + ACT_FIELD0C) = (u8)mem8(m, e + SPAWN_FIELD0C);
                RAM8(m, slot + ACT_TIMER2A) = (u8)mem8(m, e + SPAWN_TIMER2A);
            }
        }
        e += 16;
        RAM32W(m, ctrl + 0x1c, e);
    }
}

/* Damage tables. Attack rows give a column; the defender gives a row of 128 bytes. */
#define TAB_ATTACK_COLUMN 0x115420u  /* [attack class * 32 + difficulty] */
#define TAB_ENEMY_ROW     0x114000u  /* [armour * 32 + difficulty] */
#define TAB_DAMAGE        0x1142a0u  /* [row * 128 + column] */
#define TAB_PLAYER_ROWS   0x1d612u   /* longs by player: row by current health */

static u32 attack_column(const AvsrcMem *m, u32 attacker, u32 attack)
{
    u32 difficulty = RAM16(m, G_DIFFICULTY);
    u32 base = mem8(m, TAB_ATTACK_COLUMN + (u32)RAM8(m, attacker + ACT_ATK_CLASS) * 32u + difficulty);
    return (base + mem8(m, attack + 9)) & 0xffu;   /* QUIRK: byte add, wraps */
}

static u32 reduced(u32 damage, unsigned shift)
{
    /* QUIRK: floors at 1 even when the table gave 0 (0x1d574, 0x1d584). */
    damage >>= shift;
    return damage ? damage : 1;
}

static void take_damage(AvsrcMem *m, u32 defender, u32 damage)
{
    u32 h = (RAM16(m, defender + ACT_HEALTH) - damage) & 0xffffu;
    RAM16W(m, defender + ACT_HEALTH, (h & 0x8000u) ? 0xffffu : h);
}

void damage_apply(AvsrcMem *m, u32 attacker, u32 defender, u32 attack)
{
    u32 damage;
    if (RAM16(m, G_DAMAGE_OFF) != 0) return;
    if (RAM8(m, defender + ACT_TAG) != 0) {
        u32 column = attack_column(m, attacker, attack);
        u32 row = mem8(m, TAB_ENEMY_ROW + (u32)RAM8(m, defender + ACT_ARMOUR) * 32u + RAM16(m, G_DIFFICULTY));
        damage = mem8(m, TAB_DAMAGE + row * 128u + column);
        if (RAM8(m, G_QUARTER_11) != 0 && RAM8(m, defender + ACT_CLASS) == 0x11) damage = reduced(damage, 2);
        if (RAM8(m, defender + ACT_HALVED) != 0) damage = reduced(damage, 1);
        take_damage(m, defender, damage);
        return;
    }
    /* Player defender: the row depends on current health, so low health hurts differently. */
    if (RAM8(m, attacker + ACT_TAG) != 0) {
        u32 column = attack_column(m, attacker, attack);
        u32 rows = mem32(m, TAB_PLAYER_ROWS + (u32)RAM8(m, defender + ACT_PLAYER) * 4u);
        u32 row = mem8(m, rows + RAM16(m, defender + ACT_HEALTH));
        damage = mem8(m, TAB_DAMAGE + row * 128u + column);
    } else {
        /* Another player's attack does a token 1, none on a player already at zero. */
        damage = RAM16(m, defender + ACT_HEALTH) != 0 ? 1u : 0u;
    }
    take_damage(m, defender, damage);
    /* A surviving player with under 6 drops to 0; overkill stays -1. */
    if (RAM16(m, defender + ACT_HEALTH) < 6) RAM16W(m, defender + ACT_HEALTH, 0);
}

void player_energy_drain(AvsrcMem *m, u32 player)
{
    u32 cost = mem16(m, 0x1b4bcu + (u32)RAM8(m, player + ACT_DRAIN_LEVEL) * 2u);
    u32 h = (RAM16(m, player + ACT_HEALTH) - cost) & 0xffffu;
    if ((h & 0x8000u) || h < 6) h = 0;
    RAM16W(m, player + ACT_HEALTH, h);
    RAM16W(m, player + ACT_HEALTH_SEEN, h);
}

#define HEALTH_FULL 0x65u

void pickup_heal(AvsrcMem *m, u32 player, u32 item)
{
    u32 row = 0xbcd3eu + (u32)RAM8(m, item + ACT_VARIANT) * 2u;
    u32 h = RAM16(m, player + ACT_HEALTH);
    if (h == HEALTH_FULL) {
        RAM8(m, item + 0x4e) = (u8)mem8(m, row + 1);
        avsrc_actor_call(m, 0xabdd2u, mem8(m, row + 1));
        return;
    }
    /* Reviving from zero starts at 5. */
    if (h == 0) h = 5;
    h = (h + mem8(m, row)) & 0xffffu;
    if (h >= HEALTH_FULL) h = HEALTH_FULL;
    RAM16W(m, player + ACT_HEALTH, h);
    RAM16W(m, player + ACT_HEALTH_SEEN, h);
    RAM8(m, item + 0x4e) = 0xff;
}

void hit_commit(AvsrcMem *m, u32 attacker, u32 defender, u32 attack, HitIdentity identity)
{
    u32 stop = mem8(m, attack + 0x0e), mode = mem8(m, attack + 0x0a);
    u32 face = RAM8(m, attacker + ACT_FACING);
    /* Both sides freeze; an attacker already frozen keeps its own count. */
    RAM8(m, defender + ACT_HITSTOP) = (u8)stop;
    if (RAM8(m, attacker + ACT_HITSTOP) == 0) RAM8(m, attacker + ACT_HITSTOP) = (u8)stop;
    if (identity == HIT_ONCE_SINGLE) {
        if (RAM8(m, defender + ACT_TAG) == 0) avsrc_actor_call(m, 0x1d73au, 0);
        RAM8(m, defender + ACT_HIT_ID) = RAM8(m, attacker + ACT_ATK_ID);
    } else if (identity == HIT_ONCE_PER_PLAYER) {
        RAM8(m, defender + ACT_HIT_IDS + RAM8(m, attacker + ACT_PLAYER)) = RAM8(m, attacker + ACT_ATK_ID);
    } else if (!(RAM8(m, attacker + ACT_ROW65) & 0x80u)) {
        RAM8(m, defender + ACT_HIT_IDS + RAM8(m, attacker + ACT_ROW65)) = RAM8(m, attacker + ACT_ATK_ID);
    }
    if (mode == 0) {
        RAM8(m, defender + ACT_HIT_FACING) = (u8)face;
    } else if (mode & 0x80u) {
        RAM8(m, defender + ACT_HIT_FACING) = (u8)(face ^ 1u);
    } else {
        /* Mode above zero: react by side, unsigned x compare. */
        RAM8(m, defender + ACT_HIT_FACING) = RAM16(m, attacker + ACT_X) < RAM16(m, defender + ACT_X) ? 1 : 0;
    }
    avsrc_actor_call(m, 0x1d314u, 0);
    avsrc_actor_call(m, 0x1d504u, 0);
    avsrc_actor_call(m, 0x1d492u, 0);
    avsrc_actor_call(m, 0x1d622u, 0);
    avsrc_actor_call(m, 0x1d6e2u, 0);
}

void emitter_tick(AvsrcMem *m, u32 self)
{
    int paused = (RAM8(m, 0xff822au) | RAM8(m, 0xff81f3u) | RAM8(m, 0xff8208u)) != 0;
    if (!paused) {
        u32 t = (RAM16(m, self + ACT_TIMER2A) - 1) & 0xffffu;
        RAM16W(m, self + ACT_TIMER2A, t);
        if (!(t & 0x8000u)) {
            avsrc_actor_call(m, 0x16536u, 0);   /* animation step */
            return;
        }
        /* Period 49 gameplay ticks: the reload is 0x30 and the count passes zero. */
        RAM16W(m, self + ACT_TIMER2A, 0x30);
        {
            u32 puff = pool_alloc(m, POOL_24);
            if (puff != 0) {
                RAM8(m, puff + ACT_ACTIVE)++;
                RAM16W(m, puff + ACT_CLASS, 0x1004);
                copy16(m, puff + ACT_X, self + ACT_X);
                copy16(m, puff + ACT_Y, self + ACT_Y);
                copy16(m, puff + ACT_GROUND, self + ACT_GROUND);
            }
        }
    }
    avsrc_actor_call(m, 0x16518u, 0);           /* animation restart, record 0 */
}
