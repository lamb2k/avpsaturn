/* Screen fade and the route wait built on it. Source 0x1614a, 0x1620a, 0xab4c0, 0x18194, 0x183b6. */
#include "avsrc_fade.h"

u16 avsrc_r16(const u8 *p) { return (u16)((p[0] << 8) | p[1]); }
u32 avsrc_r32(const u8 *p) { return ((u32)avsrc_r16(p) << 16) | avsrc_r16(p + 2); }
void avsrc_w16(u8 *p, u16 v) { p[0] = (u8)(v >> 8); p[1] = (u8)v; }
void avsrc_w32(u8 *p, u32 v) { avsrc_w16(p, (u16)(v >> 16)); avsrc_w16(p + 2, (u16)v); }

void cmd_ring_push(AvsrcMem *m, u16 command, u16 param)
{
    u16 head = RAM16(m, G_CMD_HEAD);
    u16 next = (u16)((head + 4) & 0xfc);

    if (next == RAM16(m, G_CMD_TAIL))
        return;                         /* full: the command is dropped */
    RAM16W(m, G_CMD_HEAD, next);
    RAM16W(m, G_CMD_RING + head, command);
    RAM16W(m, G_CMD_RING + head + 2, param);
}

void palette_fade_step(AvsrcMem *m, unsigned bank, unsigned palette, u16 delta)
{
    u8 *colour = &m->pal[bank * 0x400 + palette * 0x20];
    u8 *mask = &m->ram[G_FADE_MASKS + bank * 4 - 0xff0000u];
    u16 first = avsrc_r16(colour);
    int darkening = (delta & 0x8000) != 0;
    u32 done;
    int i;

    /* Darkening tests the current brightness nibble, brightening tests the one it would reach. */
    if (!darkening)
        first = (u16)(first + delta);
    if (first & 0xf000) {
        for (i = 0; i < 16; i++)
            avsrc_w16(colour + i * 2, (u16)(avsrc_r16(colour + i * 2) + delta));
        return;
    }
    done = avsrc_r32(mask);
    if (darkening)
        done |= 1u << (31u - palette);   /* first palette in the bank owns the top bit */
    else
        done &= ~(1u << (31u - palette));
    avsrc_w32(mask, done);
}

void palette_fade_bank(AvsrcMem *m, unsigned bank, u16 delta)
{
    unsigned palette;

    for (palette = 0; palette < 32; palette++)
        palette_fade_step(m, bank, palette, delta);
    RAM32W(m, G_PAL_DONE_SUM, RAM32(m, G_PAL_DONE_SUM) + RAM32(m, G_FADE_MASKS + bank * 4));
}

void palette_fade_all(AvsrcMem *m, u16 delta)
{
    unsigned bank;

    RAM32W(m, G_PAL_DONE_SUM, 0);
    for (bank = 0; bank < 4; bank++)
        palette_fade_bank(m, bank, delta);
}

/* Route wait: the gameplay task sleeps in 0x1615c until the helper clears G_ROUTE_WAIT, so a route
   tick spans many frames and no gameplay tick runs meanwhile. Stage lengths below reproduce the
   measured waits (see notes): 25 from full brightness, 10 from black when not yet flagged,
   7 when already flagged black, and 18 for a fade-in. */
enum { STAGE_START, STAGE_STEPS, STAGE_TAIL };

void route_wait_begin(RouteWait *w, AvsrcMem *m, FadeKind kind)
{
    RAM8(m, G_ROUTE_WAIT) = 1;
    w->active = 1;
    w->kind = kind;
    w->stage = STAGE_START;
    w->frames_left = 0;
}

int route_wait_frame(RouteWait *w, AvsrcMem *m)
{
    if (!w->active)
        return 1;
    switch (w->stage) {
    case STAGE_START:                  /* idle task pops the command and starts the helper */
        if (w->kind == FADE_OUT && RAM16(m, G_SCREEN_BLACK) != 0) {
            w->stage = STAGE_TAIL;     /* nothing to fade: poll frame plus the settle sleep */
            w->frames_left = 6;
        } else {
            w->stage = STAGE_STEPS;
        }
        return 0;
    case STAGE_STEPS:
        palette_fade_all(m, w->kind == FADE_OUT ? 0xf000u : 0x1000u);
        if (w->kind == FADE_OUT && RAM32(m, G_PAL_DONE_SUM) == 0xfffffffcu) {
            RAM16W(m, G_SCREEN_BLACK, 1);
            w->stage = STAGE_TAIL;
            w->frames_left = 8;        /* two flip frames, one poll, five settle */
        } else if (w->kind == FADE_IN && RAM32(m, G_PAL_DONE_SUM) == 0) {
            RAM16W(m, G_SCREEN_BLACK, 0);
            w->stage = STAGE_TAIL;
            w->frames_left = 1;
        }
        return 0;
    default:
        if (--w->frames_left > 0)
            return 0;
        RAM8(m, G_ROUTE_WAIT) = 0;
        w->active = 0;
        return 1;
    }
}
