/* Actor record loading. See avsp_actor.h and data/avsp_actor_layout.json. */

#include "avsp_actor.h"

#define OFF_STATE        0x00u
#define OFF_CLASS_ID     0x02u
#define OFF_SUB_STATE    0x04u
#define OFF_ACTION_WORD  0x06u
#define OFF_TYPE         0x08u
#define OFF_FACING       0x0Fu
#define OFF_WORLD_X      0x10u
#define OFF_WORLD_Y      0x14u
#define OFF_WORLD_Z      0x18u
#define OFF_ANIM_RECORD  0x1Cu
#define OFF_HIT_VALUE    0x2Cu
#define OFF_HIT_SOURCE   0x2Du
#define OFF_TABLE_SET    0x50u
#define OFF_ATTACKER_ID  0x67u
#define OFF_LATCH        0x68u
#define OFF_SUPPRESS     0x70u
#define OFF_LATCH_INDEX  0xD1u

/* The source is a 68000: every multi-byte field is big-endian. */
static unsigned short be16(const unsigned char *p)
{
    return (unsigned short)(((unsigned short)p[0] << 8) | (unsigned short)p[1]);
}

static unsigned long be32(const unsigned char *p)
{
    return ((unsigned long)p[0] << 24) | ((unsigned long)p[1] << 16)
         | ((unsigned long)p[2] << 8)  | (unsigned long)p[3];
}

int avsp_actor_is_slot(unsigned long address)
{
    if (address < AVSP_ACTOR_GRID_ANCHOR) {
        return 0;
    }
    return ((address - AVSP_ACTOR_GRID_ANCHOR) % AVSP_ACTOR_STRIDE) == 0uL;
}

int avsp_actor_load(AvspActor *actor, const unsigned char *work, unsigned long address)
{
    const unsigned char *p;
    unsigned long offset;
    int i;

    if (actor == 0 || work == 0) {
        return 0;
    }
    if (address < AVSP_WORK_RAM_FIRST) {
        return 0;
    }
    offset = address - AVSP_WORK_RAM_FIRST;
    if (offset + AVSP_ACTOR_STRIDE > AVSP_WORK_RAM_SIZE) {
        return 0;
    }
    p = work + offset;

    actor->address     = address;
    actor->state       = p[OFF_STATE];
    actor->class_id    = p[OFF_CLASS_ID];
    actor->sub_state   = be16(p + OFF_SUB_STATE);
    actor->action_word = be16(p + OFF_ACTION_WORD);
    actor->type        = p[OFF_TYPE];
    actor->facing      = p[OFF_FACING];
    actor->world_x     = be16(p + OFF_WORLD_X);
    actor->world_y     = be16(p + OFF_WORLD_Y);
    actor->world_z     = be16(p + OFF_WORLD_Z);
    actor->anim_record = be32(p + OFF_ANIM_RECORD);
    actor->hit_value   = p[OFF_HIT_VALUE];
    actor->hit_source  = p[OFF_HIT_SOURCE];
    actor->table_set   = be32(p + OFF_TABLE_SET);
    actor->attacker_id = p[OFF_ATTACKER_ID];
    for (i = 0; i < AVSP_ACTOR_LATCH_SLOTS; ++i) {
        actor->latch[i] = p[OFF_LATCH + (unsigned long)i];
    }
    actor->suppress    = p[OFF_SUPPRESS];
    actor->latch_index = p[OFF_LATCH_INDEX];
    actor->sel_hurt    = 0u;
    actor->sel_attack  = 0u;
    return 1;
}
