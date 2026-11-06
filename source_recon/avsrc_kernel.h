#ifndef AVSRC_KERNEL_H
#define AVSRC_KERNEL_H
#include "avsrc.h"

/* Cooperative kernel and the gameplay tick contract. See AVP_LEARNING_NOTES.md. */
#define G_LOOP_GUARD     0xff81bcu /* set when a tick starts, cleared by the vblank IRQ */
#define G_FAST_FORWARD   0xff81b9u
#define G_ANY_BUTTON     0xff823au
#define G_HELD_POLLS     0xff1744u
#define G_INPUT_P1       0xff8064u /* per player, 2 bytes apart */
#define G_PARTICIPANTS   0xff81bfu
#define G_CURRENT_TASK   0xff025cu
#define G_TASKS          0xff0058u
#define TASK_SIZE        0x20u
#define TASK_COUNT       16u
#define TASK_SLEEPING    1u
#define TASK_READY       4u
#define TASK_VIDEO_RATE  3u         /* credit and join pass keeps real time during fast-forward */
#define TICK_MAX_CATCHUP 4u
#define TASK_CATCHUP     0x10u

/* Result of the end of a gameplay tick: sleep one vblank, or run the next tick now. */
int tick_should_sleep(AvsrcMem *m);
/* Idle task's fast-forward: wake sleeping tasks early, except the video-rate one. */
void idle_fast_forward(AvsrcMem *m);
/* Button-hold detector for scripted segments: fast-forward after 5 polls with a button. */
void hold_button_fast_forward(AvsrcMem *m);

#endif
