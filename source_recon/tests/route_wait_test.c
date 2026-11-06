/* Replays the fade waits measured in MAME (hold probe, Coffee Shop route). */
#include <stdio.h>
#include <string.h>
#include "avsrc_fade.h"
static AvsrcMem m;
static int run(FadeKind k, int top, int black)
{
    RouteWait w; int n = 0; unsigned i;
    memset(&m, 0, sizeof m);
    for (i = 0; i < AVSRC_PAL_SIZE; i += 2) m.pal[i] = (u8)(top << 4);
    if (k == FADE_IN) for (i = 0; i < 16; i += 4) RAM32W(&m, G_FADE_MASKS + i, 0xffffffffu);
    RAM16W(&m, G_SCREEN_BLACK, black);
    route_wait_begin(&w, &m, k);
    while (!route_wait_frame(&w, &m)) if (++n > 100) return -1;
    return n + 1;
}
int main(void)
{
    struct { const char *name; FadeKind k; int top, black, lo, hi; } t[] = {
        {"out from full (frames 419,646,952,5523: 25; 1085,1231,1938: 26)", FADE_OUT, 15, 0, 25, 26},
        {"out from black, not flagged (frame 82: 10)", FADE_OUT, 0, 0, 10, 10},
        {"out when flagged black (1259, 5550: 7)", FADE_OUT, 0, 1, 7, 7},
        {"in from black (94, 986, 1114: 18)", FADE_IN, 0, 1, 18, 18}
    };
    unsigned i; int bad = 0;
    for (i = 0; i < sizeof t / sizeof t[0]; i++) {
        int n = run(t[i].k, t[i].top, t[i].black);
        int ok = n >= t[i].lo && n <= t[i].hi;
        printf("%s %d frames: %s\n", ok ? "PASS" : "FAIL", n, t[i].name);
        bad |= !ok;
    }
    return bad;
}
