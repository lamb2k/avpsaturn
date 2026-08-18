/* Native actor record mirroring the game's own actor layout.
 *
 * Offsets and semantics are in data/avsp_actor_layout.json, which carries the
 * routine address that proves each field. Only fields the game's collision,
 * animation-selection and emission paths are proven to consume appear here; the
 * rest of the 0xC0 record is deliberately unlabelled.
 *
 * The record mirrors the source layout so that decoded ROM tables index
 * correctly and, later, statically translated 68000 routines need no field
 * shims. Loading is separated from the layout: avsp_actor_load reads one actor
 * out of a work-RAM image, which is what the host tests use; the Saturn runtime
 * fills the same struct from its own state.
 *
 * C90. No dynamic allocation.
 */

#ifndef AVSP_ACTOR_H
#define AVSP_ACTOR_H

#define AVSP_ACTOR_STRIDE      0xC0u
#define AVSP_WORK_RAM_FIRST    0xFF8000uL
#define AVSP_WORK_RAM_SIZE     0x8000uL
/* The player slot; every other actor slot is this plus a multiple of the stride. */
#define AVSP_ACTOR_GRID_ANCHOR 0xFF8380uL
#define AVSP_ACTOR_LATCH_SLOTS 8

typedef struct {
    unsigned long  address;      /* work-RAM address this record was read from */
    unsigned char  state;        /* +0x00 */
    unsigned char  type;         /* +0x08 */
    unsigned char  facing;       /* +0x0F */
    unsigned short world_x;      /* +0x10 */
    unsigned short world_y;      /* +0x14 */
    unsigned short world_z;      /* +0x18 */
    unsigned long  anim_record;  /* +0x1C */
    unsigned char  hit_value;    /* +0x2C */
    unsigned char  hit_source;   /* +0x2D */
    unsigned long  table_set;    /* +0x50 */
    unsigned char  attacker_id;  /* +0x67 */
    unsigned char  latch[AVSP_ACTOR_LATCH_SLOTS];  /* +0x68 */
    unsigned char  suppress;     /* +0x70 */
    unsigned char  latch_index;  /* +0xD1 */

    /* Resolved from the live animation record rather than stored in it. The
     * host tests read them from the program image; the runtime supplies them
     * from its own animation state. Zero means "cannot be hit" / "cannot hit",
     * which the game tests before any table read. */
    unsigned char  sel_hurt;     /* animation record +8 */
    unsigned char  sel_attack;   /* animation record +9 */
} AvspActor;

/* Read one actor from a work-RAM image. `work` must cover AVSP_WORK_RAM_SIZE
 * bytes starting at AVSP_WORK_RAM_FIRST. Returns 0 when the address is outside
 * that image, otherwise 1. sel_hurt/sel_attack are left zero; the caller fills
 * them from the animation record. */
int avsp_actor_load(AvspActor *actor, const unsigned char *work, unsigned long address);

/* Is this address on the actor grid? */
int avsp_actor_is_slot(unsigned long address);

#endif /* AVSP_ACTOR_H */
