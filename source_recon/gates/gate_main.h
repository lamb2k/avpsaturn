/* Shared driver for a gate program: parse cases, run the unit, print changed bytes and calls. */
#ifndef GATE_MAIN_H
#define GATE_MAIN_H
#include <stdio.h>
#include <string.h>
#include "avsrc.h"
typedef struct GateCase { u32 d[8]; u32 a[7]; } GateCase;
static AvsrcMem g_mem, g_old;
static u32 g_calls[64][2];
static int g_ncalls;
static void gate_call(u32 addr, u32 d0) { if (g_ncalls < 64) { g_calls[g_ncalls][0] = addr; g_calls[g_ncalls][1] = d0; g_ncalls++; } }
static void gate_seed(u32 a, unsigned v)
{
    if (a >= 0xff0000u) g_mem.ram[a - 0xff0000u] = (u8)v;
    else if (a >= 0x90c000u && a < 0x90d000u) g_mem.pal[a - 0x90c000u] = (u8)v;
}
static void gate_print(void)
{
    u32 i; int c;
    for (i = 0; i < AVSRC_PAL_SIZE; i++) if (g_mem.pal[i] != g_old.pal[i]) printf("m:%x:%x ", 0x90c000u + i, g_mem.pal[i]);
    for (i = 0; i < AVSRC_RAM_SIZE; i++) if (g_mem.ram[i] != g_old.ram[i]) printf("m:%x:%x ", 0xff0000u + i, g_mem.ram[i]);
    for (c = 0; c < g_ncalls; c++) printf("c:%x:%x ", g_calls[c][0], g_calls[c][1]);
    printf("\n");
}
int gate_dispatch(const char *name, const GateCase *c);
int main(void)
{
    char name[64];
    while (scanf("%63s", name) == 1) {
        GateCase c; int i, n;
        for (i = 0; i < 8; i++) scanf("%x", &c.d[i]);
        for (i = 0; i < 7; i++) scanf("%x", &c.a[i]);
        memset(&g_mem, 0, sizeof g_mem);
        g_ncalls = 0;
        scanf("%d", &n);
        for (i = 0; i < n; i++) { u32 a; unsigned v; scanf("%x %x", &a, &v); gate_seed(a, v); }
        memcpy(&g_old, &g_mem, sizeof g_mem);
        if (!gate_dispatch(name, &c)) return 2;
        gate_print();
    }
    return 0;
}
#endif
