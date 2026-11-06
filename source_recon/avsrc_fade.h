#ifndef AVSRC_FADE_H
#define AVSRC_FADE_H
#include "avsrc.h"

/* Globals of the fade and command system (source addresses). */
#define G_CMD_TAIL      0xff801cu  /* ring read offset */
#define G_CMD_HEAD      0xff801au  /* ring write offset */
#define G_CMD_RING      0xff8086u  /* 64 pairs of words */
#define G_PAL_DONE_SUM  0xff1746u  /* sum of the four bank masks; 0xfffffffc means all black */
#define G_FADE_MASKS    0xff8368u  /* one 32-bit done mask per bank, one bit per palette */
#define G_ROUTE_WAIT    0xff837bu  /* set by the waiter, cleared by the helper when finished */
#define G_SCREEN_BLACK  0xff8378u  /* word: nonzero while the screen is faded out */

/* source 0x1620a */
void cmd_ring_push(AvsrcMem *m, u16 command, u16 param);
/* source 0x1840e: one palette, one step. Delta is 0xf000 (darken) or 0x1000 (brighten). */
void palette_fade_step(AvsrcMem *m, unsigned bank, unsigned palette, u16 delta);
/* source 0x183f8: one bank; adds its done mask to the sum */
void palette_fade_bank(AvsrcMem *m, unsigned bank, u16 delta);
/* source 0x183b6: all four banks, clearing the sum first */
void palette_fade_all(AvsrcMem *m, u16 delta);

/* Frame-stepped continuation for the route wait at source 0x1614a (see notes). */
typedef enum { FADE_OUT = 0, FADE_IN = 1 } FadeKind;
typedef struct RouteWait {
    int active;
    int stage;
    int frames_left;
    FadeKind kind;
} RouteWait;
void route_wait_begin(RouteWait *w, AvsrcMem *m, FadeKind kind);
/* Advance one video frame. Returns nonzero when the waiting route tick may continue. */
int route_wait_frame(RouteWait *w, AvsrcMem *m);

#endif
