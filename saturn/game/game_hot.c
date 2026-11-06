#include "game_hot.h"

#define TARGET_LIST 0xff18feu
#define TARGET_LIST_WORDS 128
#define ACTOR_STATE 0x04u
#define STATE_FINISHED 4u

/* source 0x209d4: drop list entries whose actor is inactive or finished; the list is empty when no entry survives. */
void target_list_prune(TargetListResult *result)
{
    u32 slot = TARGET_LIST;
    unsigned left = 0;
    int i;
    for (i = 0; i < TARGET_LIST_WORDS; i++, slot += 2) {
        u16 entry = GAME_R16(slot);
        if (entry) {
            u32 actor = NEAR_PTR(entry);
            result->last_entry = actor;
            if (GAME_R8(actor) == 0 || GAME_R8(actor + ACTOR_STATE) >= STATE_FINISHED) {
                GAME_W16(slot, 0);
                entry = 0;
            }
        }
        left |= entry;
    }
    result->empty = left == 0;
}

#define DRAW_COUNT 0xffee91u
#define DRAW_LIST 0xffee7au
#define ACTOR_DEPTH 0x18u

/* source 0xaa840: one bubble pass per slot over the draw list, carrying the entry that belongs in the slot: higher depth wins, and on equal depth the
   higher actor address. Nothing to do below two entries. */
void draw_list_sort(DrawSortResult *result, unsigned *count_out)
{
    unsigned count = GAME_R8(DRAW_COUNT);
    u32 slot, scan = 0, prev = 0, held = 0, other = 0;
    u16 key = 0;
    unsigned passes;
    *count_out = count;
    result->sorted = 0;
    if (count < 2) return;
    slot = NEAR_PTR(GAME_R16(DRAW_LIST));
    for (passes = count - 1; passes > 0; passes--, slot += 2) {
        unsigned compares;
        scan = NEAR_PTR(slot);
        held = NEAR_PTR(GAME_R16(scan));
        scan += 2;
        key = GAME_R16(held + ACTOR_DEPTH);
        for (compares = passes; compares > 0; compares--) {
            u16 other_key;
            prev = NEAR_PTR(scan);
            other = NEAR_PTR(GAME_R16(scan));
            scan += 2;
            other_key = GAME_R16(other + ACTOR_DEPTH);
            if (key < other_key || (key == other_key && other >= held)) {
                GAME_W16(prev, held);
                held = other;
                key = GAME_R16(other + ACTOR_DEPTH);
            }
        }
        GAME_W16(slot, held);
    }
    result->slot = slot;
    result->scan = scan;
    result->slot_prev = prev;
    result->held = held;
    result->compared = other;
    result->key = key;
    result->sorted = 1;
}

#define ACTOR_FACING 0x0fu
#define ACTOR_X 0x10u
#define ACTOR_Z 0x14u
#define CAMERA_X 0xff8278u
#define CAMERA_Z 0xff827cu
#define SPRITE_ORIGIN 0xff1b0cu

/* source 0xaa59a: screen origin of an actor's sprite group from the camera, with the group offset mirrored by the actor's facing bits. */
void sprite_origin_compute(SpriteOriginResult *result, u32 actor, u32 offsets)
{
    unsigned facing = GAME_R8(actor + ACTOR_FACING);
    u32 offset_pair = GAME_R32(offsets);
    u16 down = (u16)offset_pair, across = (u16)(offset_pair >> 16);
    u16 y = (u16)(0x100u - (u16)(GAME_R16(actor + ACTOR_Z) - GAME_R16(CAMERA_Z)));
    u16 x = (u16)(GAME_R16(actor + ACTOR_X) - GAME_R16(CAMERA_X) + 0x40u);
    y = (u16)((facing & 2u) ? y + down : y - down);
    x = (u16)((facing & 1u) ? x + across : x - across);
    result->packed = ((u32)y << 16) | x;
    GAME_W32(SPRITE_ORIGIN, result->packed);
    result->offset_swapped = (offset_pair << 16) | (offset_pair >> 16);
    result->facing_bits = facing;
}

#define ACTOR_HOLD 0x4cu
#define ACTOR_ANIM 0x1cu
#define ACTOR_BOXES 0x50u
#define ACTOR_DOWNED 0x93u
#define ACTOR_KIND 0xd2u
#define ACTOR_REACH_BIAS 0x84u
#define SLOT_DISTANCE 0x06u

/* source 0x1689a: is this target in melee reach of the attacker, and nearer than the best so far? Keeps the nearest in the slot. */
void melee_candidate_check(MeleeCheck *check, u32 attacker, u32 target, u32 best_slot)
{
    u16 band, height, across, bias, reach;
    u32 anim, boxes, box;
    check->stage = 0;
    if (GAME_R8(attacker + ACTOR_HOLD) || GAME_R8(target + ACTOR_DOWNED) || !GAME_R8(target)) return;
    band = GAME_R8(target + ACTOR_KIND) == 3 ? 8 : 3;
    /* QUIRK: the height test is one unsigned window, -band to +band, as in the source. */
    height = (u16)(GAME_R16(attacker + ACTOR_DEPTH) - GAME_R16(target + ACTOR_DEPTH) + band);
    check->distance = height;
    check->limit = (u16)(band * 2);
    check->stage = 1;
    if (height > check->limit) return;
    anim = GAME_R32(attacker + ACTOR_ANIM);
    boxes = GAME_R32(attacker + ACTOR_BOXES);
    box = boxes + (u32)(int)(s16)GAME_R16(boxes) + (u32)(int)(s16)(u16)((u32)GAME_R8(anim + 8) << 3);
    across = (u16)(int)(signed char)GAME_R8(box);
    if (GAME_R8(attacker + ACTOR_FACING)) across = (u16)(0u - across);
    bias = GAME_R16(target + ACTOR_REACH_BIAS);
    if (GAME_R8(target + ACTOR_FACING)) bias = (u16)(0u - bias);
    across = (u16)(across + GAME_R16(attacker + ACTOR_X) - GAME_R16(target + ACTOR_X) + bias);
    if (across & 0x8000u) across = (u16)(0u - across);
    reach = (u16)(GAME_R8(box + 2) + 6u);
    check->box = box;
    check->reach = reach;
    check->distance = across;
    check->stage = 2;
    if (across > reach || across >= GAME_R16(best_slot + SLOT_DISTANCE)) return;
    GAME_W16(best_slot, attacker);
    GAME_W16(best_slot + SLOT_DISTANCE, across);
}
