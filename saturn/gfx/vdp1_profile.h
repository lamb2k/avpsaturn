/* Optional presentation diagnostics. No storage or calls without
 * -DSAT_VDP1_PROFILE on both the kernel and graphics compilation.
 * These are 32-bit words on SH-2 and on the host fixture. Read through the
 * uncached alias, with the target paused, and decode with tools/vdp1_profile.py.
 * The first word is written last; zero means a row is being replaced.
 */
#ifndef SAT_VDP1_PROFILE_H
#define SAT_VDP1_PROFILE_H

#ifdef SAT_VDP1_PROFILE
#ifndef SAT_VDP1_PROFILE_DEPTH
#define SAT_VDP1_PROFILE_DEPTH 16
#endif
#if SAT_VDP1_PROFILE_DEPTH < 2 || (SAT_VDP1_PROFILE_DEPTH & (SAT_VDP1_PROFILE_DEPTH - 1))
#error SAT_VDP1_PROFILE_DEPTH must be a power of two, at least 2
#endif

enum SatVdp1PlotWord {
    VP_ATTEMPT, VP_SERIAL, VP_SOURCE_VBLANK, VP_STAGE_CHARACTERS,
    VP_SNAPSHOT_TICKS, VP_HANDOFF_TICK, VP_START_VBLANK, VP_SUBMIT_TICK,
    VP_WAIT_END_TICKS, VP_SPRITE_TICKS, VP_UPLOAD_TICKS, VP_UPLOAD_BYTES,
    VP_WAIT_CHANGE_TICKS, VP_WAIT_LATCH_TICKS, VP_LAYER_TICKS, VP_CPU_TICKS,
    VP_OBJECTS, VP_COMMANDS, VP_SOURCE_TEXELS, VP_SPRITE_PIXELS,
    VP_CLEAR_PIXELS, VP_HALF_TRANSPARENT, VP_COLOUR_MODES, VP_FLAGS,
    VP_RASTER_UPPER_TICKS, VP_PLOT_WORDS
};
enum SatVdp1FrameWord {
    VF_VBLANK, VF_STARTED, VF_SHOWN_BEFORE, VF_SHOWN_AFTER,
    VF_EDSR, VF_CPU_BUSY, VF_FRAME_WORDS
};
#define VP_SUBMITTED 1u
#define VP_END_TIMEOUT 2u
#define VP_CHANGE_TIMEOUT 4u
#define VP_LATCH_TIMEOUT 8u
#define VP_CEF_AT_CPU_DONE 16u

extern volatile unsigned int sat_vdp1_plots[SAT_VDP1_PROFILE_DEPTH][VP_PLOT_WORDS];
extern volatile unsigned int sat_vdp1_frames[SAT_VDP1_PROFILE_DEPTH][VF_FRAME_WORDS];

/* Kernel-side read of the existing handoff counters, on the master only. */
int sat_gfx_profile_busy(void);
#endif
#endif
