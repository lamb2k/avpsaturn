/* Target macros for lifted C on the SH-2. Replaces the non-HOST block of the lifter's header at build time (build.py), since
   the 68000 reads longs on 2-byte boundaries and the SH-2 faults on those. On target P(a) is empty.
   Types u8..s32 and Cpu come from the including file. */
#ifndef LIFT_TARGET_H
#define LIFT_TARGET_H
register Cpu *R __asm__("r14");
extern u8 *PAGE[256];
extern u8 RAMB[];
extern u8 ROMB[];            /* program image, flat, cart */
#define P(a)

static inline u32 w2_rd32(const volatile void *p) { const volatile u16 *q = (const volatile u16 *)p; return ((u32)q[0] << 16) | q[1]; }
static inline void w2_wr32(volatile void *p, u32 v) { volatile u16 *q = (volatile u16 *)p; q[0] = (u16)(v >> 16); q[1] = (u16)v; }
#ifdef SAT_READMAP   /* diagnostic: one bit per 1 KB page of the program ROM the lifted code reads, cleared at each stage file load (kernel.c) */
extern u8 *pb_rm(u32 a);
#define pb_at pb_rm
#else
static inline u8 *pb_at(u32 a) { return PAGE[(a >> 16) & 0xff] + (a & 0xffff); }
#endif

#define RAM8(o) (*(volatile u8 *)(RAMB + (o)))
#define RAM16(o) (*(volatile u16 *)(RAMB + (o)))
#define RAM32(o) (((o) & 2) ? w2_rd32(RAMB + (o)) : *(volatile u32 *)(RAMB + (o)))
#define RAMW8(o, v) (RAM8(o) = (v))
#define RAMW16(o, v) (RAM16(o) = (v))
#define RAMW32(o, v) do { if ((o) & 2) w2_wr32(RAMB + (o), (v)); else *(volatile u32 *)(RAMB + (o)) = (v); } while (0)
/* Opcode view: only what the lifted code reads through it, in a side store (tools/satint_merge.py). build.py rewrites each base to its store offset. */
extern u8 OPX[];
#define OP8(a) (*(const u8 *)(OPX + (u32)(a)))
#define OP16(a) (*(const u16 *)(OPX + (u32)(a)))
#define OP32(a) w2_rd32(OPX + (u32)(a))
#define ROM8(o) (*(const u8 *)(ROMB + (o)))
#define ROM16(o) (*(const u16 *)(ROMB + (o)))
#define ROM32(o) (((o) & 2) ? w2_rd32(ROMB + (o)) : *(const u32 *)(ROMB + (o)))
#define RD8(a) (*(volatile u8 *)pb_at((u32)(a)))
#define RD16(a) (*(volatile u16 *)pb_at((u32)(a)))
#define RD32(a) w2_rd32(pb_at((u32)(a)))
#define WR8(a, v) (*(volatile u8 *)pb_at((u32)(a)) = (v))
#define WR16(a, v) (*(volatile u16 *)pb_at((u32)(a)) = (v))
#define WR32(a, v) w2_wr32(pb_at((u32)(a)), (v))
#endif
