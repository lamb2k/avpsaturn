/* Gate adapter for saturn/game/game_hot.c: mirrors game_bind.c. Final registers and flags go to a pseudo block in RAM, compared with the ROM routine's. */
#include <stdlib.h>
#include "avsrc.h"
#include "../../saturn/game/game_hot.h"
#include "gates/gate_main.h"
u8 *PAGE[256];
static u8 g_rom[0x200000];
#define REG_BLOCK 0xe000u
#define LOW16(reg, v) ((reg) = ((reg) & 0xffff0000u) | ((u32)(v) & 0xffffu))
static void put_regs(const u32 *d, const u32 *a, int flags)
{
    int i;
    for (i = 0; i < 15; i++) {
        u32 v = i < 8 ? d[i] : a[i - 8];
        g_mem.ram[REG_BLOCK + i * 4] = (u8)(v >> 24); g_mem.ram[REG_BLOCK + i * 4 + 1] = (u8)(v >> 16);
        g_mem.ram[REG_BLOCK + i * 4 + 2] = (u8)(v >> 8); g_mem.ram[REG_BLOCK + i * 4 + 3] = (u8)v;
    }
    g_mem.ram[REG_BLOCK + 60] = (u8)flags;
}
int gate_dispatch(const char *name, const GateCase *cs)
{
    u32 d[8], a[7];
    int i, flags = 0;
    static int ready;
    if (!ready) {
        FILE *f = fopen("/mnt/e/AvP/learning/merged.bin", "rb");
        if (!f || fread(g_rom, 1, sizeof g_rom, f) != sizeof g_rom) return 0;
        fclose(f);
        ready = 1;
    }
    for (i = 0; i < 0x20; i++) PAGE[i] = g_rom + ((u32)i << 16);
    PAGE[0xff] = g_mem.ram;
    for (i = 0; i < 8; i++) d[i] = cs->d[i];
    for (i = 0; i < 7; i++) a[i] = cs->a[i];
    if (!strcmp(name, "target_list_prune")) {
        TargetListResult r;
        r.last_entry = a[3];
        target_list_prune(&r);
        a[3] = r.last_entry; a[4] = 0xff19feu; d[6] = 0xffffu; d[0] = r.empty ? 1u : 0u;
    } else if (!strcmp(name, "draw_list_sort")) {
        DrawSortResult r; unsigned count;
        draw_list_sort(&r, &count);
        d[0] = count;
        if (r.sorted) { d[0] = 0xffffu; LOW16(d[1], 0xffffu); LOW16(d[2], r.key); a[0] = r.slot_prev; a[2] = r.slot; a[3] = r.held; a[4] = r.scan; a[6] = r.compared; }
    } else if (!strcmp(name, "sprite_origin_compute")) {
        SpriteOriginResult r; u32 s;
        sprite_origin_compute(&r, a[4], a[0]);
        a[0] += 4; d[2] = r.offset_swapped; d[3] = r.packed;
        s = (r.facing_bits << 5) & 0xffu; d[1] = s;
        flags = (s == 0 ? 4 : 0) | ((s & 0x80u) ? 8 : 0) | (int)((r.facing_bits >> 3) & 1u);
    } else if (!strcmp(name, "melee_candidate_check")) {
        MeleeCheck c;
        melee_candidate_check(&c, a[6], a[1], a[0]);
        if (c.stage >= 1) { LOW16(d[0], c.distance); d[1] = c.limit; }
        if (c.stage == 2) { a[2] = c.box; d[0] = c.distance; d[1] = c.reach; }
    } else return 0;
    put_regs(d, a, flags);
    return 1;
}
