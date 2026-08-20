#include "avsp_disc_guard.h"

void avsp_disc_guard_init(AvspDiscGuard *guard)
{
    guard->cdda_active = 0;
    guard->window_open = 0;
    guard->window_reason = 0;
    guard->late_read_attempts = 0;
    guard->refused_windows = 0;
    guard->allowed_reads = 0;
}

void avsp_disc_guard_cdda_started(AvspDiscGuard *guard)
{
    guard->cdda_active = 1;
}

void avsp_disc_guard_cdda_stopped(AvspDiscGuard *guard)
{
    guard->cdda_active = 0;
}

int avsp_disc_guard_window_begin(AvspDiscGuard *guard, const char *reason)
{
    if (guard->cdda_active)
    {
        ++guard->refused_windows;
        return 0;
    }
    guard->window_open = 1;
    guard->window_reason = reason;
    return 1;
}

void avsp_disc_guard_window_end(AvspDiscGuard *guard)
{
    guard->window_open = 0;
    guard->window_reason = 0;
}

int avsp_disc_guard_check(AvspDiscGuard *guard)
{
    if (guard->cdda_active && !guard->window_open)
    {
        ++guard->late_read_attempts;
        return 0;
    }
    ++guard->allowed_reads;
    return 1;
}
