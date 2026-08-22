#include "hit_ko.h"

const AvspPortV2HitKoActorState avsp_port_v2_hit_source_before =
{
    0x0001u, 0x0202u, 0x0000u, 0x0012EB4CUL,
    0x0000u, 63, 0x0008u
};

const AvspPortV2HitKoActorState avsp_port_v2_ko_source_before =
{
    0x0001u, 0x0400u, 0x0000u, 0x0012EB1CUL,
    0x0400u, -1, 0x000Cu
};

int avsp_port_v2_hit_ko_state_equal(
    const AvspPortV2HitKoActorState *first,
    const AvspPortV2HitKoActorState *second)
{
    if (first == 0 || second == 0) return 0;
    return first->state == second->state &&
           first->sub_state == second->sub_state &&
           first->action == second->action &&
           first->anim_record == second->anim_record &&
           first->anim_timer == second->anim_timer &&
           first->health == second->health &&
           first->hit_value == second->hit_value;
}

static void begin_hit(AvspPortV2HitKoRuntime *runtime)
{
    runtime->actor.action = 0x0002u;
    runtime->actor.anim_record = AVSP_PORT_V2_HIT_ANIM_RECORD;
    runtime->actor.anim_timer = 0x0400u;
}

static void begin_ko(AvspPortV2HitKoRuntime *runtime)
{
    runtime->actor.state = 0x0002u;
    runtime->actor.sub_state = 0x0402u;
    runtime->actor.anim_record = AVSP_PORT_V2_KO_ANIM_RECORD;
    runtime->actor.anim_timer = 0x0406u;
}

int avsp_port_v2_hit_ko_begin(
    AvspPortV2HitKoRuntime *runtime,
    const AvspPortV2HitKoKind kind,
    const AvspPortV2HitKoActorState *source_before)
{
    const AvspPortV2HitKoActorState *expected;
    if (runtime == 0 || source_before == 0) return 0;
    if (kind == AVSP_PORT_V2_HIT_KO_HIT)
        expected = &avsp_port_v2_hit_source_before;
    else if (kind == AVSP_PORT_V2_HIT_KO_KO)
        expected = &avsp_port_v2_ko_source_before;
    else
        return 0;
    if (!avsp_port_v2_hit_ko_state_equal(source_before, expected)) return 0;
    runtime->actor = *source_before;
    runtime->kind = (unsigned short)kind;
    runtime->elapsed = 0u;
    runtime->active = 1u;
    if (kind == AVSP_PORT_V2_HIT_KO_HIT)
        begin_hit(runtime);
    else
        begin_ko(runtime);
    return 1;
}

static void step_hit(AvspPortV2HitKoRuntime *runtime)
{
    if (runtime->elapsed <= 8u)
        --runtime->actor.hit_value;
    else if (runtime->elapsed == 9u)
        runtime->actor.action = 0x0200u;
    else if (runtime->elapsed == 10u)
        runtime->actor.action = 0x0202u;
    else if (runtime->elapsed == 33u)
    {
        runtime->actor.action = 0x0204u;
        runtime->actor.anim_record = AVSP_PORT_V2_HIT_RECOVERY_ANIM_RECORD;
    }
    else if (runtime->elapsed == 36u)
    {
        runtime->actor.action = 0x0000u;
        runtime->actor.sub_state = 0x0200u;
        runtime->active = 0u;
    }
}

static void step_ko(AvspPortV2HitKoRuntime *runtime)
{
    if (runtime->elapsed <= 12u)
        --runtime->actor.hit_value;
    if (runtime->elapsed == 13u)
    {
        runtime->actor.action = 0x0200u;
        runtime->actor.anim_record = AVSP_PORT_V2_KO_ANIM_RECORD_1;
    }
    else if (runtime->elapsed == 15u)
        runtime->actor.anim_record = AVSP_PORT_V2_KO_ANIM_RECORD_2;
    else if (runtime->elapsed == 20u)
        runtime->actor.anim_record = AVSP_PORT_V2_KO_ANIM_RECORD_3;
    else if (runtime->elapsed == 27u)
        runtime->actor.anim_record = AVSP_PORT_V2_KO_ANIM_RECORD_4;
    else if (runtime->elapsed == 65u)
    {
        runtime->actor.action = 0x0400u;
        runtime->actor.anim_record = AVSP_PORT_V2_KO_ANIM_RECORD_5;
        runtime->actor.anim_timer = 0x0306u;
    }
    else if (runtime->elapsed == 66u || runtime->elapsed == 67u)
        runtime->actor.anim_timer =
            (unsigned short)(runtime->actor.anim_timer - 0x0100u);
    else if (runtime->elapsed == 68u)
    {
        runtime->actor.action = 0x0600u;
        runtime->actor.anim_record = AVSP_PORT_V2_KO_ANIM_RECORD_4;
        runtime->actor.anim_timer = 0x0006u;
    }
    else if (runtime->elapsed == 79u)
    {
        runtime->actor.action = 0x0000u;
        runtime->actor.anim_record = AVSP_PORT_V2_KO_ANIM_RECORD_5;
        runtime->actor.anim_timer = 0x3C06u;
        runtime->actor.sub_state = 0x0404u;
    }
    else if (runtime->elapsed >= 80u && runtime->elapsed <= 139u)
    {
        runtime->actor.anim_timer =
            (unsigned short)(runtime->actor.anim_timer - 0x0100u);
        if (runtime->elapsed == 139u)
        {
            runtime->actor.sub_state = 0x0600u;
            runtime->active = 0u;
        }
    }
}

int avsp_port_v2_hit_ko_step(AvspPortV2HitKoRuntime *runtime)
{
    if (runtime == 0 || !runtime->active) return 0;
    ++runtime->elapsed;
    if (runtime->kind == (unsigned short)AVSP_PORT_V2_HIT_KO_HIT)
        step_hit(runtime);
    else if (runtime->kind == (unsigned short)AVSP_PORT_V2_HIT_KO_KO)
        step_ko(runtime);
    else
        return 0;
    return 1;
}
