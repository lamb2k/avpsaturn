/* Diagnostic only: master-clock phases paired by source vblank. The kernel
   includes this once; the host fixture exercises the same recorder. */
#ifndef SAT_CPU_SLACK_PROFILE_H
#define SAT_CPU_SLACK_PROFILE_H

#ifdef SAT_CPU_SLACK_PROFILE
#ifndef SAT_CPU_SLACK_DEPTH
#define SAT_CPU_SLACK_DEPTH 16
#endif
#if SAT_CPU_SLACK_DEPTH < 2 || (SAT_CPU_SLACK_DEPTH & (SAT_CPU_SLACK_DEPTH - 1))
#error SAT_CPU_SLACK_DEPTH must be a power of two, at least two
#endif

enum SatCpuSlackWord {
    CS_VBLANK, CS_FLAGS, CS_PERIOD, CS_HANDOFF, CS_LAYERS, CS_IRQ,
    CS_DONE, CS_HANDOFF_SERIAL, CS_GFX_HANDED_END, CS_GFX_DONE_END,
    CS_CONTEXT, CS_WORDS
};
#define CS_FINISHED 1u
#define CS_OVERRUN 2u
#define CS_HOME 4u
#define CS_BUSY_BEGIN 8u
#define CS_BUSY_DONE 16u
#define CS_BUSY_END 32u
#define CS_TIMER_WRAP 64u
#define CS_UNPAIRED_DONE 128u
#define CS_BAD_ORDER 256u
#define CS_HANDED 512u
#define CS_PREVIOUS_OVERRUN 1024u
#define CS_UNKNOWN 0xffffffffu

/* Ordinary kernel BSS: high work RAM, never .lwgfx. The output row's first
   word is committed last. Dump while paused; word zero means no complete row. */
volatile unsigned int sat_cpu_slack[SAT_CPU_SLACK_DEPTH][CS_WORDS];
static unsigned int cpu_slack_current[CS_WORDS];
/* Main publishes only this mailbox. The IRQ never modifies it: an interrupt
   between publication writes sees an invalid/old tag, not a mixed sample. */
static volatile unsigned int cpu_slack_done[3];
#ifndef CPU_SLACK_ROW
#define CPU_SLACK_ROW(i) sat_cpu_slack[i]
#endif

static void cpu_slack_publish_done(unsigned int vblank, unsigned int tick,
                                   unsigned int flags)
{
    cpu_slack_done[0] = 0;
    cpu_slack_done[1] = tick;
    cpu_slack_done[2] = flags;
    cpu_slack_done[0] = vblank;
}

static void cpu_slack_close(unsigned int period, int finished,
                            unsigned int flags, unsigned int handed,
                            unsigned int done)
{
    unsigned int i, vblank = cpu_slack_current[CS_VBLANK];
    volatile unsigned int *out;
    if (!vblank) return;
    cpu_slack_current[CS_PERIOD] = period;
    cpu_slack_current[CS_GFX_HANDED_END] = handed;
    cpu_slack_current[CS_GFX_DONE_END] = done;
    if (handed != done) flags |= CS_BUSY_END;
    if (!finished) flags |= CS_OVERRUN;
    else if (cpu_slack_current[CS_FLAGS] & CS_HOME) {
        flags |= CS_FINISHED;
        cpu_slack_current[CS_DONE] = cpu_slack_current[CS_IRQ];
    } else if (cpu_slack_done[0] == vblank) {
        flags |= CS_FINISHED | cpu_slack_done[2];
        cpu_slack_current[CS_DONE] = cpu_slack_done[1];
    } else flags |= CS_UNPAIRED_DONE;
    cpu_slack_current[CS_FLAGS] |= flags;
    if (cpu_slack_current[CS_IRQ] > period ||
        ((flags & CS_FINISHED) &&
         (cpu_slack_current[CS_DONE] < cpu_slack_current[CS_IRQ] ||
          cpu_slack_current[CS_DONE] > period)))
        cpu_slack_current[CS_FLAGS] |= CS_BAD_ORDER;
    out = CPU_SLACK_ROW(vblank & (SAT_CPU_SLACK_DEPTH - 1));
    out[CS_VBLANK] = 0;
    for (i = 1; i < CS_WORDS; i++) out[i] = cpu_slack_current[i];
    out[CS_VBLANK] = vblank;
}

static void cpu_slack_begin(unsigned int vblank, unsigned int flags,
                            unsigned int context)
{
    unsigned int i;
    for (i = 0; i < CS_WORDS; i++) cpu_slack_current[i] = CS_UNKNOWN;
    cpu_slack_current[CS_VBLANK] = vblank;
    cpu_slack_current[CS_FLAGS] = flags;
    cpu_slack_current[CS_HANDOFF_SERIAL] = 0;
    cpu_slack_current[CS_CONTEXT] = context;
}

static void cpu_slack_handoff(unsigned int serial, unsigned int tick)
{
    cpu_slack_current[CS_HANDOFF_SERIAL] = serial;
    cpu_slack_current[CS_HANDOFF] = tick;
    cpu_slack_current[CS_FLAGS] |= CS_HANDED;
}

static void cpu_slack_layers(unsigned int tick)
{
    cpu_slack_current[CS_LAYERS] = tick;
}

static void cpu_slack_irq(unsigned int tick, int home)
{
    cpu_slack_current[CS_IRQ] = tick;
    if (home) cpu_slack_current[CS_FLAGS] |= CS_HOME;
}
#endif
#endif
