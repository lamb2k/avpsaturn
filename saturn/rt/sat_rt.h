/* Interface of the Saturn runtime kernel to other Saturn lanes. The includer defines u8 and u32. */
#ifndef SAT_RT_H
#define SAT_RT_H
typedef struct {
    u32 magic, stage, vblanks, ff8018, task_runs, idle_calls, task_stack_high;
    u32 fatal, fatal_detail, fatal_task, fatal_a[3], exc_pc, exc_pr;
} SatDebug;
extern SatDebug sat_dbg;
void sat_fatal(u32 code, u32 detail);
/* Called at each vblank after the game's own IRQ. Weak stub calls sat_gfx_frame(). */
void sat_present(void);
/* Supplied by saturn/gfx; weak empty stubs here. */
void sat_gfx_init(void);
void sat_gfx_frame(void);
/* Remap one 64 KB page of the 68000 address space for indirect accesses. */
void sat_map_page(u32 page, u8 *base);
extern u8 SAT_OBJ[];        /* page 0x70; CPS2 object list at SAT_OBJ + 0x8000, 0x2000 bytes */
extern u8 SAT_CART_FREE[];  /* first free cart byte */
#endif
