/* RP5 host test: the disc-read guard must reject data reads while CDDA is
 * active, permit them before CDDA and inside explicit measured windows,
 * refuse windows opened while CDDA is active, and count every decision.
 * Negative controls invert each rule and must be caught. */
#include <stdio.h>

#include "../avsp_disc_guard.h"

static int failures;

static void expect(const int condition, const char *label)
{
    if (!condition)
    {
        printf("FAIL: %s\n", label);
        ++failures;
    }
}

int main(void)
{
    AvspDiscGuard guard;

    avsp_disc_guard_init(&guard);
    expect(avsp_disc_guard_check(&guard) == 1,
           "pre-CDDA read is permitted");
    expect(guard.allowed_reads == 1, "permitted read counted");
    expect(guard.late_read_attempts == 0, "no late reads yet");

    avsp_disc_guard_cdda_started(&guard);
    expect(avsp_disc_guard_check(&guard) == 0,
           "read while CDDA active is rejected");
    expect(guard.late_read_attempts == 1, "late read counted");
    expect(avsp_disc_guard_check(&guard) == 0,
           "second late read also rejected");
    expect(guard.late_read_attempts == 2, "second late read counted");

    expect(avsp_disc_guard_window_begin(&guard, "illegal") == 0,
           "window refused while CDDA active");
    expect(guard.refused_windows == 1, "refused window counted");
    expect(guard.window_open == 0, "refused window stays closed");

    avsp_disc_guard_cdda_stopped(&guard);
    expect(avsp_disc_guard_check(&guard) == 1,
           "read after CDDA stop is permitted");
    expect(avsp_disc_guard_window_begin(&guard, "phase-boundary") == 1,
           "window opens while CDDA inactive");

    /* CDDA restarting while a measured window is open: the window was
       opened legally, and the load inside it completes; this mirrors the
       interior-transition contract where the window brackets one bounded
       read. */
    avsp_disc_guard_cdda_started(&guard);
    expect(avsp_disc_guard_check(&guard) == 1,
           "read inside an open measured window is permitted");
    avsp_disc_guard_window_end(&guard);
    expect(avsp_disc_guard_check(&guard) == 0,
           "read after window close with CDDA active is rejected");

    /* Negative controls: assert the guard is NOT trivially permissive or
       trivially blocking. */
    avsp_disc_guard_init(&guard);
    avsp_disc_guard_cdda_started(&guard);
    expect(avsp_disc_guard_check(&guard) != 1,
           "control: guard is not trivially permissive");
    avsp_disc_guard_init(&guard);
    expect(avsp_disc_guard_check(&guard) != 0,
           "control: guard is not trivially blocking");

    if (failures)
    {
        printf("avsp_disc_guard_test: %d failure(s)\n", failures);
        return 1;
    }
    printf("avsp_disc_guard_test: all checks passed\n");
    return 0;
}
