/* Actor-local collision, ported from the game's own routines.
 *
 * The overlap test is 0x01D25E..0x01D312 and the guards are the caller's checks
 * at 0x01D042..0x01D060. Box records come from generated/avsp_collision.h,
 * which tools/decode_avsp_collision.py emits from the game's tables; the
 * decode and its falsification are described in data/avsp_collision.json and
 * the handoff's milestone-2 section.
 *
 * Nothing here is inferred from damage frames or overlay pixels.
 *
 * C90. No dynamic allocation, no floating point.
 */

#ifndef AVSP_COLLISION_H_API
#define AVSP_COLLISION_H_API

#include "avsp_actor.h"

/* Three axes of signed centre plus unsigned half-extent, actor-local. */
typedef struct {
    signed char   x_center;
    signed char   y_center;
    unsigned char x_half;
    unsigned char y_half;
    signed char   z_center;
    unsigned char z_half;
} AvspBox;

typedef struct {
    AvspBox       box;
    unsigned char hit_value;      /* record +0x0E; latched into the defender's +0x2C */
    signed char   knockback_mode; /* record +0x0A */
} AvspAttackBox;

/* Resolve a family's box for a selector. Returns 0 when the family is unknown,
 * the selector is 0 (the game rejects it before any table read), or the
 * selector is out of range for that family. */
int avsp_collision_hurt_box(unsigned long table_set, unsigned char selector, AvspBox *out);
int avsp_collision_attack_box(unsigned long table_set, unsigned char selector, AvspAttackBox *out);

/* The game's overlap test. Returns 1 when the attacker's active attack box
 * overlaps the defender's active hurt box, and writes the attack record's hit
 * value to *hit_value when non-null. Returns 0 otherwise, including when either
 * selector is 0 or either family is unknown. */
int avsp_collision_overlap(const AvspActor *attacker, const AvspActor *defender,
                           unsigned char *hit_value);

/* The caller's guards at 0x01D042..0x01D060: the defender must be in state 1
 * with its suppress byte clear, and must not already carry this attacker's id
 * in the per-attacker latch slot the attacker indexes. Returns 1 when the hit
 * is guarded off. */
int avsp_collision_guarded(const AvspActor *attacker, const AvspActor *defender);

#endif /* AVSP_COLLISION_H_API */
