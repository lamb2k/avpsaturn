#include <stdlib.h>
#include "avsrc_actor.h"
#include "gates/gate_main.h"
void avsrc_actor_call(AvsrcMem *m, u32 target, u32 arg) { (void)m; gate_call(target, arg); }
static void load_rom(void)
{
    static u8 *img;
    if (!img) {
        FILE *f = fopen("/mnt/e/AvP/learning/actor/merged_actor.bin", "rb");
        img = (u8 *)malloc(0x200000);
        if (!f || !img || fread(img, 1, 0x200000, f) == 0) exit(3);
        fclose(f);
        g_avsrc_rom = img;
    }
}
/* Registers the ROM routine leaves as a result, stored by the gate at a scratch address. */
static void result_slot(u32 slot)
{
    RAM16W(&g_mem, 0xff0e00u, slot & 0xffffu);
}
int gate_dispatch(const char *name, const GateCase *c)
{
    AvsrcMem *m = &g_mem;
    load_rom();
    if (!strncmp(name, "pool_alloc_", 11)) result_slot(pool_alloc(m, (ActorPoolId)atoi(name + 11)));
    else if (!strncmp(name, "pool_release_", 13)) pool_release(m, (ActorPoolId)atoi(name + 13), c->a[6]);
    else if (!strncmp(name, "pool_traverse_", 14)) pool_traverse(m, (ActorPoolId)atoi(name + 14)), RAM8(m, 0xff0e04u) = (u8)g_ncalls;
    else if (!strcmp(name, "pools_reset")) pools_reset(m);
    else if (!strcmp(name, "spawn_table_step")) spawn_table_step(m);
    else if (!strcmp(name, "damage_apply")) damage_apply(m, c->a[6], c->a[1], c->a[3]);
    else if (!strcmp(name, "player_energy_drain")) player_energy_drain(m, c->a[6]);
    else if (!strcmp(name, "pickup_heal")) pickup_heal(m, c->a[6], c->a[4]);
    else if (!strcmp(name, "hit_commit_single")) hit_commit(m, c->a[6], c->a[1], c->a[3], HIT_ONCE_SINGLE);
    else if (!strcmp(name, "hit_commit_player")) hit_commit(m, c->a[6], c->a[1], c->a[3], HIT_ONCE_PER_PLAYER);
    else if (!strcmp(name, "hit_commit_row65")) hit_commit(m, c->a[6], c->a[1], c->a[3], HIT_ONCE_PER_ROW65);
    else if (!strcmp(name, "emitter_tick")) emitter_tick(m, c->a[6]);
    else return 0;
    return 1;
}
