/* Actor-local collision, ported from 0x01D25E..0x01D312 and its caller's
 * guards. See avsp_collision.h. */

#include "avsp_collision.h"
#include "generated/avsp_collision.h"
#include "generated/avsp_table_set_classes.h"

int avsp_table_set_for_class(unsigned char class_id, unsigned long *out)
{
    unsigned short i;

    if (out == 0) {
        return 0;
    }
    for (i = 0; i < avsp_class_table_set_count; ++i) {
        if (avsp_class_table_sets[i].class_id == class_id) {
            *out = avsp_class_table_sets[i].table_set;
            return 1;
        }
    }
    return 0;
}

static const avsp_collision_family *find_family(unsigned long table_set)
{
    unsigned short i;
    for (i = 0; i < avsp_collision_family_count; ++i) {
        if (avsp_collision_families[i].table_set == table_set) {
            return &avsp_collision_families[i];
        }
    }
    return 0;
}

int avsp_collision_hurt_box(unsigned long table_set, unsigned char selector, AvspBox *out)
{
    const avsp_collision_family *fam;
    const avsp_collision_box *src;

    if (out == 0 || selector == 0u) {
        return 0;
    }
    fam = find_family(table_set);
    if (fam == 0 || (unsigned short)selector >= fam->hurt_count) {
        return 0;
    }
    src = &fam->hurt[selector];
    out->x_center = src->x_center;
    out->y_center = src->y_center;
    out->x_half   = src->x_half;
    out->y_half   = src->y_half;
    out->z_center = src->z_center;
    out->z_half   = src->z_half;
    return 1;
}

int avsp_collision_attack_box(unsigned long table_set, unsigned char selector, AvspAttackBox *out)
{
    const avsp_collision_family *fam;
    const avsp_collision_attack *src;

    if (out == 0 || selector == 0u) {
        return 0;
    }
    fam = find_family(table_set);
    if (fam == 0 || (unsigned short)selector >= fam->attack_count) {
        return 0;
    }
    src = &fam->attack[selector];
    out->box.x_center = src->box.x_center;
    out->box.y_center = src->box.y_center;
    out->box.x_half   = src->box.x_half;
    out->box.y_half   = src->box.y_half;
    out->box.z_center = src->box.z_center;
    out->box.z_half   = src->box.z_half;
    out->hit_value      = src->hit_value;
    out->knockback_mode = src->knockback_mode;
    return 1;
}

/* The source works in 16-bit words throughout; keep the same width so wrap
 * behaviour matches. */
static short as_word(long v)
{
    unsigned short u = (unsigned short)((unsigned long)v & 0xFFFFuL);
    return (u > 0x7FFFu) ? (short)((long)u - 0x10000L) : (short)u;
}

static short abs_word(short v)
{
    return (short)((v < 0) ? -v : v);
}

int avsp_collision_overlap(const AvspActor *attacker, const AvspActor *defender,
                           unsigned char *hit_value)
{
    AvspAttackBox atk;
    AvspBox hurt;
    short depth_delta;
    short ax, dx, ay, dy;

    if (attacker == 0 || defender == 0) {
        return 0;
    }
    if (attacker->sel_attack == 0u || defender->sel_hurt == 0u) {
        return 0;
    }
    if (!avsp_collision_attack_box(attacker->table_set, attacker->sel_attack, &atk)) {
        return 0;
    }
    if (!avsp_collision_hurt_box(defender->table_set, defender->sel_hurt, &hurt)) {
        return 0;
    }

    /* Depth. The signed delta is kept, because the Y axis reuses it as the
     * belt-scroller's depth-to-screen projection (0x01D2E6). */
    depth_delta = as_word(((long)hurt.z_center + (long)defender->world_z)
                        - ((long)atk.box.z_center + (long)attacker->world_z));
    if (abs_word(depth_delta) > (short)((int)atk.box.z_half + (int)hurt.z_half)) {
        return 0;
    }

    /* X. Each box's own owner's facing byte mirrors its centre (0x01D296). */
    ax = as_word((attacker->facing ? -(long)atk.box.x_center : (long)atk.box.x_center)
                 + (long)attacker->world_x);
    dx = as_word((defender->facing ? -(long)hurt.x_center : (long)hurt.x_center)
                 + (long)defender->world_x);
    if (abs_word(as_word((long)dx - (long)ax)) > (short)((int)atk.box.x_half + (int)hurt.x_half)) {
        return 0;
    }

    /* Y, with the depth delta folded into the attacker's side. */
    ay = as_word((long)atk.box.y_center + (long)depth_delta + (long)attacker->world_y);
    dy = as_word((long)hurt.y_center + (long)defender->world_y);
    if (abs_word(as_word((long)dy - (long)ay)) > (short)((int)atk.box.y_half + (int)hurt.y_half)) {
        return 0;
    }

    if (hit_value != 0) {
        *hit_value = atk.hit_value;
    }
    return 1;
}

int avsp_collision_guarded(const AvspActor *attacker, const AvspActor *defender)
{
    if (attacker == 0 || defender == 0) {
        return 1;
    }
    if (defender->state != 1u || defender->suppress != 0u) {
        return 1;
    }
    if (attacker->latch_index < (unsigned char)AVSP_ACTOR_LATCH_SLOTS) {
        if (defender->latch[attacker->latch_index] == attacker->attacker_id) {
            return 1;
        }
    }
    return 0;
}
