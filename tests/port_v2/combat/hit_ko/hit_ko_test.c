#include <stdio.h>
#include <string.h>

#include "../../../../src/port_v2/combat/hit_ko/hit_ko.h"

static void emit(const int sample, const AvspPortV2HitKoRuntime *runtime)
{
    const AvspPortV2HitKoActorState *actor = &runtime->actor;
    printf("%d,%u,%u,%u,%lu,%u,%d,%u,%u\n",
           sample, (unsigned int)actor->state,
           (unsigned int)actor->sub_state,
           (unsigned int)actor->action, actor->anim_record,
           (unsigned int)actor->anim_timer, (int)actor->health,
           (unsigned int)actor->hit_value, (unsigned int)runtime->active);
}

static int emit_trace(const AvspPortV2HitKoKind kind)
{
    AvspPortV2HitKoRuntime runtime;
    const AvspPortV2HitKoActorState *before;
    int sample;
    int last;
    if (kind == AVSP_PORT_V2_HIT_KO_HIT)
    {
        before = &avsp_port_v2_hit_source_before;
        sample = AVSP_PORT_V2_HIT_SOURCE_SAMPLE;
        last = AVSP_PORT_V2_HIT_LAST_SAMPLE;
    }
    else
    {
        before = &avsp_port_v2_ko_source_before;
        sample = AVSP_PORT_V2_KO_SOURCE_SAMPLE;
        last = AVSP_PORT_V2_KO_LAST_SAMPLE;
    }
    if (!avsp_port_v2_hit_ko_begin(&runtime, kind, before)) return 0;
    emit(sample, &runtime);
    while (sample < last)
    {
        ++sample;
        if (!avsp_port_v2_hit_ko_step(&runtime)) return 0;
        emit(sample, &runtime);
    }
    return !runtime.active && !avsp_port_v2_hit_ko_step(&runtime);
}

static int negative_prestate_control(void)
{
    AvspPortV2HitKoRuntime runtime;
    AvspPortV2HitKoActorState mutation = avsp_port_v2_hit_source_before;
    mutation.anim_record = AVSP_PORT_V2_HIT_RECOVERY_ANIM_RECORD;
    if (avsp_port_v2_hit_ko_begin(
            &runtime, AVSP_PORT_V2_HIT_KO_HIT, &mutation)) return 0;
    mutation = avsp_port_v2_ko_source_before;
    mutation.sub_state = 0x0402u;
    return !avsp_port_v2_hit_ko_begin(
        &runtime, AVSP_PORT_V2_HIT_KO_KO, &mutation);
}

int main(const int argc, char **argv)
{
    if (argc == 2 && strcmp(argv[1], "hit") == 0)
        return emit_trace(AVSP_PORT_V2_HIT_KO_HIT) ? 0 : 1;
    if (argc == 2 && strcmp(argv[1], "ko") == 0)
        return emit_trace(AVSP_PORT_V2_HIT_KO_KO) ? 0 : 1;
    if (argc == 2 && strcmp(argv[1], "--negative-prestate") == 0)
    {
        if (!negative_prestate_control()) return 1;
        puts("unsupported pre-state rejected");
        return 0;
    }
    return 2;
}
