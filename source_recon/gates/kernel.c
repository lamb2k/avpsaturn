#include "avsrc_kernel.h"
#include "gates/gate_main.h"
int gate_dispatch(const char *name, const GateCase *c)
{
    (void)c;
    if (!strcmp(name, "tick_tail")) { if (tick_should_sleep(&g_mem)) gate_call(0x1060, 1); }
    else if (!strcmp(name, "idle_fast_forward")) { idle_fast_forward(&g_mem); gate_call(0x14b70, RAM8(&g_mem, G_FAST_FORWARD) ? 0xffffu : c->d[0]); }
    else if (!strcmp(name, "hold_button_fast_forward")) hold_button_fast_forward(&g_mem);
    else return 0;
    return 1;
}
