/* Source 0x8140 tick tail, 0x14b4a idle fast-forward, 0x170xx button hold. */
#include "avsrc_kernel.h"

int tick_should_sleep(AvsrcMem *m)
{
    u32 task = RAM32(m, G_CURRENT_TASK);
    u8 *catchup = &RAM8(m, task + TASK_CATCHUP);

    if (RAM8(m, G_LOOP_GUARD) != 0) {   /* tick fitted before the vblank */
        *catchup = 0;
        return 1;
    }
    (*catchup)++;
    if (*catchup >= TICK_MAX_CATCHUP) {
        *catchup = 0;
        return 1;
    }
    return 0;                           /* overran: run the next tick straight away */
}

void idle_fast_forward(AvsrcMem *m)
{
    u32 task = G_TASKS;
    unsigned i;

    if (RAM8(m, G_FAST_FORWARD) == 0)
        return;
    for (i = 0; i < TASK_COUNT; i++, task += TASK_SIZE) {
        if (RAM8(m, task) != TASK_SLEEPING || i == TASK_VIDEO_RATE)
            continue;
        if (--RAM8(m, task + 1) == 0)
            RAM8(m, task) = TASK_READY;
    }
}

static int participant_pressed(const AvsrcMem *m, u8 participants, u8 button_mask)
{
    unsigned player;

    for (player = 0; player < 3; player++) {
        if ((participants & (1u << player)) &&
            (m->ram[G_INPUT_P1 + player * 2 - 0xff0000u] & button_mask))
            return 1;
    }
    return 0;
}

void hold_button_fast_forward(AvsrcMem *m)
{
    int was_counting = RAM8(m, G_ANY_BUTTON) != 0 && RAM16(m, G_HELD_POLLS) != 0;
    int pressed = participant_pressed(m, RAM8(m, G_PARTICIPANTS), 0x7f);

    RAM8(m, G_FAST_FORWARD) = 0;
    if (!was_counting) {
        /* QUIRK: a stale G_ANY_BUTTON with a zero count also starts the count without a press. */
        if (pressed || RAM8(m, G_ANY_BUTTON) != 0) {
            RAM8(m, G_ANY_BUTTON) = 1;
            RAM16W(m, G_HELD_POLLS, 1);
        } else {
            RAM16W(m, G_HELD_POLLS, 0);
        }
        return;
    }
    RAM8(m, G_ANY_BUTTON) = (u8)pressed;
    if (!pressed) {
        RAM16W(m, G_HELD_POLLS, 0);
        return;
    }
    if (RAM16(m, G_HELD_POLLS) + 1u >= 5u) {
        RAM8(m, G_FAST_FORWARD) = 1;
        RAM16W(m, G_HELD_POLLS, 5);
    } else {
        RAM16W(m, G_HELD_POLLS, RAM16(m, G_HELD_POLLS) + 1);
    }
}
