#ifndef AVSP_DISC_GUARD_H
#define AVSP_DISC_GUARD_H

/* RP5 disc-read guard.
 *
 * Contract: while CDDA owns the drive, no unmeasured data-track read may
 * start. Every reader must ask avsp_disc_guard_check() before touching the
 * data track; a rejected request is counted, never silently retried.
 *
 * Phase-boundary loads (e.g. the interior-transition PCM load) may open an
 * explicit measured window ONLY when CDDA is not active in that phase; the
 * window carries a reason string so the evidence trail names every legal
 * seek. Opening a window while CDDA is flagged active is itself an error
 * and is refused and counted.
 */

typedef struct
{
    int cdda_active;         /* CDDA currently owns the drive            */
    int window_open;         /* explicit measured data-read window       */
    const char *window_reason;
    int late_read_attempts;  /* reads rejected because CDDA was active   */
    int refused_windows;     /* windows refused because CDDA was active  */
    int allowed_reads;       /* reads permitted (pre-CDDA or in-window)  */
} AvspDiscGuard;

void avsp_disc_guard_init(AvspDiscGuard *guard);

/* CDDA ownership transitions. */
void avsp_disc_guard_cdda_started(AvspDiscGuard *guard);
void avsp_disc_guard_cdda_stopped(AvspDiscGuard *guard);

/* Explicit measured data-read window. Returns 1 when the window opened,
 * 0 (and counts the refusal) when CDDA is active. */
int avsp_disc_guard_window_begin(AvspDiscGuard *guard, const char *reason);
void avsp_disc_guard_window_end(AvspDiscGuard *guard);

/* Ask before starting a data-track read. Returns 1 when the read may
 * proceed; 0 (and counts the late attempt) when CDDA is active and no
 * window is open. */
int avsp_disc_guard_check(AvspDiscGuard *guard);

#endif
