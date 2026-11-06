/* Readable replacements for the game's hottest routines. Behaviour-matched against the ROM routine (gate game_hot), then swapped in for the lifted
   function by game_bind.c. Game memory stays big-endian at its original offsets and is reached through the 64 KB page map. */
#ifndef GAME_HOT_H
#define GAME_HOT_H
#ifndef AVSRC_H
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef short s16;
#endif
extern u8 *PAGE[256];
#define GAME_AT(a) (PAGE[((a) >> 16) & 0xffu] + ((a) & 0xffffu))
#define GAME_R8(a) (*(const volatile u8 *)GAME_AT(a))
#define GAME_W8(a, v) (*(volatile u8 *)GAME_AT(a) = (u8)(v))
#ifdef SAT_TARGET
#define GAME_R16(a) (*(const volatile u16 *)GAME_AT(a))
#define GAME_W16(a, v) (*(volatile u16 *)GAME_AT(a) = (u16)(v))
#else
#define GAME_R16(a) ((u16)((GAME_AT(a)[0] << 8) | GAME_AT((a) + 1)[0]))
#define GAME_W16(a, v) (GAME_AT(a)[0] = (u8)((u16)(v) >> 8), GAME_AT((a) + 1)[0] = (u8)(v))
#endif
#define GAME_R32(a) (((u32)GAME_R16(a) << 16) | GAME_R16((a) + 2))
#define GAME_W32(a, v) (GAME_W16((a), (u32)(v) >> 16), GAME_W16((a) + 2, (u32)(v)))
/* The game keeps most pointers as 16-bit words, sign extended: high words are work RAM. */
#define NEAR_PTR(w) ((u32)(int)(s16)(w))

/* Each routine reports what it leaves behind, because the lifted game around it still reads those registers. */
typedef struct { u32 last_entry; int empty; } TargetListResult;
void target_list_prune(TargetListResult *result);

typedef struct { u32 slot, scan, slot_prev, held, compared, key; int sorted; } DrawSortResult;
void draw_list_sort(DrawSortResult *result, unsigned *count_out);

typedef struct { u32 offset_swapped, packed; unsigned facing_bits; } SpriteOriginResult;
void sprite_origin_compute(SpriteOriginResult *result, u32 actor, u32 offsets);

/* stage: 0 stopped before the height test, 1 height window tested, 2 reach computed. */
typedef struct { int stage; u16 distance, limit; u32 reach, box; } MeleeCheck;
void melee_candidate_check(MeleeCheck *check, u32 attacker, u32 target, u32 best_slot);
#endif
