#include <stdio.h>
#include <string.h>

#include "../../../../src/port_v2/integration/live_encounter/live_encounter.h"
#include "../../../../src/port_v2/audio/pcm/pcm.h"

typedef struct
{
    unsigned long frames;
    unsigned long contacts;
    unsigned long alien_contacts;
    unsigned long misses;
    unsigned long hits;
    unsigned long kos;
    unsigned long clears;
    unsigned short player_health;
    unsigned short alien_state;
    unsigned short route_unlocked;
    unsigned short continued;
} Result;

static int near_target(const AvspLiveEncounterRuntime *runtime)
{
    int dx = runtime->alien.x - runtime->player.x;
    int dz = runtime->alien.lane - runtime->player.lane;
    if (dx < 0) dx = -dx;
    if (dz < 0) dz = -dz;
    return dx <= 52 && dz <= 6;
}

static unsigned short policy(AvspLiveEncounterRuntime *runtime,
                             int *phase, int *release)
{
    unsigned short mask = 0u;
    if (*release)
    {
        *release = 0;
        return 0u;
    }
    if (*phase == 0)
    {
        if (runtime->encounter_state == AVSP_LIVE_ENCOUNTER_WAIT_ENTRY)
            return AVSP_PW_INPUT_RIGHT;
        *phase = 1;
    }
    if (*phase == 1)
    {
        if (runtime->alien_contacts == 0UL) return 0u;
        *phase = 2;
    }
    if (*phase == 2)
    {
        if (runtime->player.x > 240) return AVSP_PW_INPUT_LEFT;
        if (avsp_pw_can_control(&runtime->player))
        {
            *phase = 3;
            *release = 1;
            return AVSP_PW_INPUT_ATTACK;
        }
        return 0u;
    }
    if (*phase == 3)
    {
        if (runtime->player.state != AVSP_PW_STATE_CONTROL) return 0u;
        if (runtime->player.x < runtime->alien.x - 42)
            mask |= AVSP_PW_INPUT_RIGHT;
        else if (runtime->player.x > runtime->alien.x + 42)
            mask |= AVSP_PW_INPUT_LEFT;
        if (runtime->player.lane < runtime->alien.lane - 4)
            mask |= AVSP_PW_INPUT_UP;
        else if (runtime->player.lane > runtime->alien.lane + 4)
            mask |= AVSP_PW_INPUT_DOWN;
        if (near_target(runtime))
        {
            *release = 1;
            return AVSP_PW_INPUT_ATTACK;
        }
        return mask;
    }
    return AVSP_PW_INPUT_RIGHT;
}

static int replay(Result *result)
{
    AvspLiveEncounterRuntime runtime;
    AvspLiveEncounterFrame frame;
    AvspLiveEncounterInput input;
    AvspPortV2PcmRuntime pcm_runtime;
    AvspPortV2PcmInput pcm_input;
    AvspPortV2PcmFrame pcm_frame;
    int phase = 0;
    int release = 0;
    int pcm_retriggers = 0;
    unsigned long limit;
    avsp_live_encounter_init(&runtime);
    avsp_port_v2_pcm_init(&pcm_runtime);
    memset(result, 0, sizeof(*result));
    for (limit = 0; limit < 5000UL; ++limit)
    {
        input.frame = runtime.frame;
        input.player_mask = policy(&runtime, &phase, &release);
        if (!avsp_live_encounter_step(&runtime, &input, &frame)) return 0;
        pcm_input.frame = (int)frame.frame;
        pcm_input.cue_event = frame.player_contact;
        pcm_input.cue_id = AVSP_PORT_V2_PCM_CUE_PREDATOR_MELEE;
        if (pcm_input.cue_event && (pcm_runtime.pending || pcm_runtime.active))
        {
            avsp_port_v2_pcm_init(&pcm_runtime);
            ++pcm_retriggers;
        }
        if (!avsp_port_v2_pcm_step(&pcm_runtime, &pcm_input, &pcm_frame))
        {
            printf("INTEGRATE-04A PCM chronology rejected frame=%lu pending=%d active=%d contacts=%lu\n",
                   frame.frame, pcm_runtime.pending, pcm_runtime.active,
                   runtime.player_contacts);
            return 0;
        }
        if (runtime.route_unlocked) phase = 4;
        if (runtime.continued_after_unlock && runtime.camera_world_x > 0)
            break;
    }
    result->frames = runtime.frame;
    result->contacts = runtime.player_contacts;
    result->alien_contacts = runtime.alien_contacts;
    result->misses = runtime.player_misses;
    result->hits = runtime.hit_events;
    result->kos = runtime.ko_events;
    result->clears = runtime.clear_events;
    result->player_health = (unsigned short)runtime.player.health;
    result->alien_state = runtime.alien.state;
    result->route_unlocked = runtime.route_unlocked;
    result->continued = runtime.continued_after_unlock;
    return pcm_retriggers > 0 && runtime.failures == 0UL &&
        runtime.fallback_count == 0UL &&
        avsp_live_encounter_canaries_ok(&runtime);
}

int main(void)
{
    Result first;
    Result second;
    unsigned int selector;
    if (avsp_live_encounter_contract_flags() != 15u ||
        !avsp_live_encounter_contract_valid() ||
        avsp_live_encounter_clear_allowed(0u, 0u, 1u, 1u) ||
        avsp_live_encounter_clear_allowed(1u, 0u, 1u, 1u) ||
        avsp_live_encounter_clear_allowed(0u, 1u, 0u, 0u) ||
        !avsp_live_encounter_clear_allowed(1u, 1u, 0u, 0u))
        return 1;
    if (avsp_pw_render_facing(0u) != -1 ||
        avsp_pw_render_facing(1u) != 1)
        return 4;
    for (selector = 1u; selector <= AVSP_PW_ACTION_COUNT; ++selector)
    {
        const AvspPwAttackDef *definition = &avsp_pw_action_defs[selector - 1u];
        if (avsp_pw_source_presentation_ready(
                (unsigned short)selector,
                (unsigned short)(definition->presentation_first - 1u)) ||
            !avsp_pw_source_presentation_ready(
                (unsigned short)selector, definition->presentation_first) ||
            avsp_pw_source_presentation_ready(
                (unsigned short)selector, definition->return_frame))
            return 5;
    }
    if (avsp_pw_source_presentation_ready(0u, 2u) ||
        avsp_pw_source_presentation_ready(5u, 2u))
        return 6;
    if (!replay(&first) || !replay(&second) ||
        memcmp(&first, &second, sizeof(first)) != 0)
        return 2;
    if (first.contacts < 4UL || first.alien_contacts < 1UL ||
        first.misses < 1UL || first.hits < 1UL || first.kos != 1UL ||
        first.clears != 1UL || !first.route_unlocked || !first.continued ||
        first.alien_state != AVSP_ALIEN_STATE_INACTIVE)
        return 3;
    printf("INTEGRATE-04A live encounter core: PASS frames=%lu contacts=%lu misses=%lu received=%lu\n",
           first.frames, first.contacts, first.misses, first.alien_contacts);
    return 0;
}
