/* Actor pools, spawn table, damage and hit commit of avspu. Readable reconstruction, research only.
   Addresses are source addresses. Field names follow the SPEC fixtures where those exist. */
#ifndef AVSRC_ACTOR_H
#define AVSRC_ACTOR_H
#include "avsrc.h"

/* ROM image used for tables (never committed). The port supplies its own extracted tables. */
extern const u8 *g_avsrc_rom;
/* Calls to bodies outside this module. The port binds these, the gate records them. */
void avsrc_actor_call(AvsrcMem *m, u32 target, u32 arg);

/* Actor fields, offset from the slot. */
#define ACT_ACTIVE      0x00u  /* byte */
#define ACT_CLASS       0x02u  /* byte: index into the pool's dispatch table */
#define ACT_VARIANT     0x03u  /* byte */
#define ACT_PHASE       0x04u  /* byte: state; +5 substate */
#define ACT_TAG         0x08u  /* byte: pool tag, fixed at round reset; 0 for player slots */
#define ACT_FIELD0C     0x0cu  /* byte: from the spawn entry */
#define ACT_FACING      0x0fu  /* byte */
#define ACT_X           0x10u  /* word */
#define ACT_Y           0x14u  /* word */
#define ACT_GROUND      0x18u  /* word */
#define ACT_TIMER2A     0x2au  /* byte or word, per class */
#define ACT_HITSTOP     0x2cu  /* byte: gameplay ticks, see AVP_NOTES_ACTOR.md */
#define ACT_HIT_ID      0x2du  /* byte: id of the last attack that landed (single-hit form) */
#define ACT_HEALTH      0x40u  /* word, signed; -1 after an overkill */
#define ACT_HEALTH_SEEN 0x42u  /* word: health latched for the display */
#define ACT_FLASH_LEFT  0x48u  /* byte: tags 8 and 12 only, counts down, clears +0x47 at zero */
#define ACT_HIT_FACING  0x4fu  /* byte: reaction_facing */
#define ACT_ARMOUR      0x57u  /* byte: defender row selector */
#define ACT_ATK_CLASS   0x5eu  /* byte: attacker row selector */
#define ACT_ATK_ID      0x67u  /* byte: attacker_id67 */
#define ACT_HIT_IDS     0x68u  /* bytes: last attack id per player */
#define ACT_HALVED      0x73u  /* byte: nonzero halves damage taken (interrupt73) */
#define ACT_DRAIN_LEVEL 0x9fu  /* byte: player, selects the energy drain */
#define ACT_PLAYER      0xd1u  /* byte: player index */
#define ACT_ROW65       0x65u  /* byte, signed: latch_index65, negative for none */

/* Globals. */
#define G_CAMERA_X      0xff8278u  /* word */
#define G_STAGE         0xff81e8u  /* word: even; selects the spawn table */
#define G_DIFFICULTY    0xff81eau  /* word: stage_parameter, 0..31 */
#define G_PLAYER_FORM   0xff820eu  /* byte: player_variant */
#define G_QUARTER_11    0xff8244u  /* byte: with class 0x11 defenders, quarter damage */
#define G_DAMAGE_OFF    0xff189eu  /* word: nonzero skips damage */
#define G_SPAWN_CTRL    0xff1812u  /* spawn controller record: +4 phase, +0x1c cursor */
#define G_SPAWN_SET     0xff8218u  /* word: written by kind 0x1c entries */

/* One entry per pool. Free slots live on a word stack that grows down; top holds the next slot. */
typedef enum {
    POOL_4, POOL_8, POOL_12, POOL_16, POOL_20, POOL_24, POOL_28, POOL_32, POOL_36, POOL_40, POOL_COUNT
} ActorPoolId;

/* source 0x1773e, 0x17654, 0x1769e, 0x1778c, 0x176f0, 0x177da, 0x17828, 0x178a8, 0x17876, 0x178da.
   Returns the slot, or 0 when the pool is empty. The record is not cleared. */
u32 pool_alloc(AvsrcMem *m, ActorPoolId pool);
/* source 0x17754 and siblings: clear the pool's lifecycle fields and push the slot. */
void pool_release(AvsrcMem *m, ActorPoolId pool, u32 slot);
/* source 0x1729c: wipe all pools, fill free stacks, clear per-round globals. */
void pools_reset(AvsrcMem *m);
/* source 0x1b846, 0x1b916, 0x1b974, 0x1b8bc, 0x1bc38, 0x1ba62, 0x1bcda, 0x1bd48, called in this order
   from 0x849e. Pools 32 and 40 are not traversed here. */
void pool_traverse(AvsrcMem *m, ActorPoolId pool);
/* source 0x1be5e: the camera-driven spawn table, one call per tick. */
void spawn_table_step(AvsrcMem *m);

/* source 0x1d504: subtract table damage. attack is the attack box record. */
void damage_apply(AvsrcMem *m, u32 attacker, u32 defender, u32 attack);
/* source 0x1b492: fixed cost of a player special, by drain level. */
void player_energy_drain(AvsrcMem *m, u32 player);
/* source 0xbc60a: pickup heal. At full health it scores instead. */
void pickup_heal(AvsrcMem *m, u32 player, u32 item);

typedef enum {
    HIT_ONCE_SINGLE = 0,   /* source 0x1cfca: one id in +0x2d; player defenders also run 0x1d73a */
    HIT_ONCE_PER_PLAYER,   /* source 0x1d0a8: id per attacker player index */
    HIT_ONCE_PER_ROW65     /* source 0x1d186: as above, indexed by +0x65, negative records nothing */
} HitIdentity;
/* The common tail after the box test: hitstop, id, reaction facing, then the five effects. */
void hit_commit(AvsrcMem *m, u32 attacker, u32 defender, u32 attack, HitIdentity identity);

/* source 0xa7394: type 28 class 0x0e, timed emitter body phase. */
void emitter_tick(AvsrcMem *m, u32 self);

#endif
