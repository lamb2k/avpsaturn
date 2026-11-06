#include "avsrc_fade.h"
#include "gates/gate_main.h"
int gate_dispatch(const char *name, const GateCase *c)
{
    if (!strcmp(name, "cmd_ring_push")) cmd_ring_push(&g_mem, (u16)c->d[0], (u16)c->d[1]);
    else if (!strcmp(name, "palette_fade_step")) palette_fade_step(&g_mem, (unsigned)((c->a[0] - 0x90c000u) >> 10), (unsigned)(((c->a[0] - 0x90c000u) >> 5) & 31), (u16)c->d[2]);
    else if (!strcmp(name, "palette_fade_all")) palette_fade_all(&g_mem, (u16)c->d[2]);
    else return 0;
    return 1;
}
