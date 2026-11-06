/* Interface of the Saturn runtime kernel to other Saturn lanes. The includer defines u8 and u32. */
#ifndef SAT_RT_H
#define SAT_RT_H
typedef struct {
    u32 magic, stage, vblanks, ff8018, task_runs, idle_calls, task_stack_high;
    u32 fatal, fatal_detail, fatal_task, fatal_a[3], exc_pc, exc_pr;
    u32 gfx_ticks, irq_ticks, game_ticks, gfx_peak, irq_peak, game_peak, overruns, obj_flips, snap_ticks, snap_peak, gfx_skips;
} SatDebug;
extern SatDebug sat_dbg;
void sat_fatal(u32 code, u32 detail);
/* saturn/gfx. The master takes a snapshot at the start of a vblank, before the game's IRQ body, when the slave has finished the last one;
   the slave draws it. */
int sat_gfx_init(const void *pack);
void sat_gfx_snapshot(void);
void sat_gfx_draw(void);
/* saturn/audio */
int sat_audio_init(const void *pack);
void sat_audio_frame(void);
/* Remap one 64 KB page of the 68000 address space for indirect accesses. */
void sat_map_page(u32 page, u8 *base);
extern u8 SAT_OBJ[];        /* two object banks of 8 KB, each seen at 0x708000 */
extern u8 SAT_PACK[];       /* tile pack, SGP1 */
#endif
