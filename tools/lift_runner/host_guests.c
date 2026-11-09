/* Host runner side of the bonus-character wrappers (tools/lift_runner/build_native_host.py). HOST only.
   sat_guest_sel: env WV_SEL (hex, default 0 = guest off: the wrappers pass through).
   sat_wv_fork_on: env WVF (hex fork mask, bit = forkgen.py id, default 0). In identity runs the mask alone decides, whoever the player is;
   the target's version (wolverine.c, SAT_WV_NATIVE) also requires the guest to be selected and the player to be Wolverine. */
#include <stdlib.h>
typedef unsigned char u8;
extern u8 ROMB[];
u8 *const wv_host_rom = ROMB;
static unsigned long mask; static int init;
#ifndef SAT_WV_NATIVE   /* the native build's own (wolverine.c) takes the player and the guest into account */
int sat_wv_fork_on(unsigned long a6, int id)
{
    (void)a6;
    if (!init) { const char *e = getenv("WVF"); mask = e ? strtoul(e, 0, 16) : 0; init = 1; }
    return (int)((mask >> id) & 1);
}
#endif
extern unsigned char sat_guest_sel;
__attribute__((constructor)) static void wv_host_sel(void) { const char *e = getenv("WV_SEL"); if (e) sat_guest_sel = (unsigned char)strtoul(e, 0, 16); }
/* WVTRACE=file: text record per player update (wolverine.c, built with -DWV_HOST_TRACE). Fields: vblank kind player a b c cur step left exec wall chain cstg hw x z. */
#include <stdio.h>
extern long host_vblank;
void wv_host_trace(int kind, int player, int a, int b, int c, int cur, int step, int left, int exec, int wall, int chain, int cstg, int hw, int x, int z)
{
    static FILE *f; static int init;
    if (!init) { const char *e = getenv("WVTRACE"); init = 1; if (e) f = fopen(e, "w"); }
    if (f) fprintf(f, "%ld %d %d %02x %02x %02x %d %d %d %d %d %d %d %d %d %d\n", host_vblank, kind, player, a, b, c, cur, step, left, exec, wall, chain, cstg, hw, x, z);
}
