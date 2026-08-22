#include <string.h>

#include "diagnostic.h"
#include "../../../../src/port_v2/combat/hit_ko/hit_ko.h"

#define AVSP_HIT_KO_CANARY_HEAD 0x48495448UL
#define AVSP_HIT_KO_CANARY_TAIL 0x4B4F544CUL

typedef struct
{
    unsigned long head_canary;
    AvspPortV2HitKoRuntime runtime;
    int frame;
    int phase;
    int sample;
    int hit_sample_count;
    int ko_sample_count;
    int negative_rejections;
    int failures;
    unsigned long tail_canary;
} AvspHitKoDiagnosticState;

static AvspHitKoDiagnosticState diagnostic;

volatile int avsp_diag_hit_ko_interface_version;
volatile int avsp_diag_hit_ko_frame;
volatile int avsp_diag_hit_ko_phase;
volatile int avsp_diag_hit_ko_sample;
volatile int avsp_diag_hit_ko_state;
volatile int avsp_diag_hit_ko_sub_state;
volatile int avsp_diag_hit_ko_action;
volatile unsigned long avsp_diag_hit_ko_anim_record;
volatile int avsp_diag_hit_ko_anim_timer;
volatile int avsp_diag_hit_ko_health;
volatile int avsp_diag_hit_ko_hit_value;
volatile int avsp_diag_hit_ko_hit_sample_count;
volatile int avsp_diag_hit_ko_ko_sample_count;
volatile int avsp_diag_hit_ko_negative_rejections;
volatile int avsp_diag_hit_ko_failures;
volatile int avsp_diag_hit_ko_complete;
volatile int avsp_diag_hit_ko_canary_ok;

static void publish(void)
{
    avsp_diag_hit_ko_interface_version =
        AVSP_HIT_KO_DIAGNOSTIC_INTERFACE_VERSION;
    avsp_diag_hit_ko_frame = diagnostic.frame;
    avsp_diag_hit_ko_phase = diagnostic.phase;
    avsp_diag_hit_ko_sample = diagnostic.sample;
    avsp_diag_hit_ko_state = diagnostic.runtime.actor.state;
    avsp_diag_hit_ko_sub_state = diagnostic.runtime.actor.sub_state;
    avsp_diag_hit_ko_action = diagnostic.runtime.actor.action;
    avsp_diag_hit_ko_anim_record = diagnostic.runtime.actor.anim_record;
    avsp_diag_hit_ko_anim_timer = diagnostic.runtime.actor.anim_timer;
    avsp_diag_hit_ko_health = diagnostic.runtime.actor.health;
    avsp_diag_hit_ko_hit_value = diagnostic.runtime.actor.hit_value;
    avsp_diag_hit_ko_hit_sample_count = diagnostic.hit_sample_count;
    avsp_diag_hit_ko_ko_sample_count = diagnostic.ko_sample_count;
    avsp_diag_hit_ko_negative_rejections = diagnostic.negative_rejections;
    avsp_diag_hit_ko_failures = diagnostic.failures;
    avsp_diag_hit_ko_complete = diagnostic.phase == 3;
    avsp_diag_hit_ko_canary_ok =
        diagnostic.head_canary == AVSP_HIT_KO_CANARY_HEAD &&
        diagnostic.tail_canary == AVSP_HIT_KO_CANARY_TAIL;
}

int avsp_hit_ko_diagnostic_init(void)
{
    AvspPortV2HitKoActorState mutation;
    memset(&diagnostic, 0, sizeof(diagnostic));
    diagnostic.head_canary = AVSP_HIT_KO_CANARY_HEAD;
    diagnostic.tail_canary = AVSP_HIT_KO_CANARY_TAIL;
    mutation = avsp_port_v2_hit_source_before;
    mutation.anim_record = AVSP_PORT_V2_HIT_RECOVERY_ANIM_RECORD;
    if (!avsp_port_v2_hit_ko_begin(
            &diagnostic.runtime, AVSP_PORT_V2_HIT_KO_HIT, &mutation))
        ++diagnostic.negative_rejections;
    else
        ++diagnostic.failures;
    if (!avsp_port_v2_hit_ko_begin(
            &diagnostic.runtime, AVSP_PORT_V2_HIT_KO_HIT,
            &avsp_port_v2_hit_source_before))
        ++diagnostic.failures;
    diagnostic.phase = 1;
    diagnostic.sample = AVSP_PORT_V2_HIT_SOURCE_SAMPLE;
    diagnostic.hit_sample_count = 1;
    publish();
    return diagnostic.failures == 0 && diagnostic.negative_rejections == 1;
}

static void finish_hit(void)
{
    if (diagnostic.runtime.actor.state != 0x0001u ||
        diagnostic.runtime.actor.sub_state != 0x0200u ||
        diagnostic.runtime.actor.action != 0x0000u ||
        diagnostic.runtime.actor.anim_record !=
            AVSP_PORT_V2_HIT_RECOVERY_ANIM_RECORD ||
        diagnostic.runtime.actor.anim_timer != 0x0400u ||
        diagnostic.runtime.actor.health != 63 ||
        diagnostic.runtime.actor.hit_value != 0u)
        ++diagnostic.failures;
    if (!avsp_port_v2_hit_ko_begin(
            &diagnostic.runtime, AVSP_PORT_V2_HIT_KO_KO,
            &avsp_port_v2_ko_source_before))
        ++diagnostic.failures;
    diagnostic.phase = 2;
    diagnostic.sample = AVSP_PORT_V2_KO_SOURCE_SAMPLE;
    diagnostic.ko_sample_count = 1;
}

static void finish_ko(void)
{
    if (diagnostic.runtime.actor.state != 0x0002u ||
        diagnostic.runtime.actor.sub_state != 0x0600u ||
        diagnostic.runtime.actor.action != 0x0000u ||
        diagnostic.runtime.actor.anim_record != AVSP_PORT_V2_KO_ANIM_RECORD_5 ||
        diagnostic.runtime.actor.anim_timer != 0x0006u ||
        diagnostic.runtime.actor.health != -1 ||
        diagnostic.runtime.actor.hit_value != 0u)
        ++diagnostic.failures;
    diagnostic.phase = 3;
}

void avsp_hit_ko_diagnostic_step(void)
{
    ++diagnostic.frame;
    if (diagnostic.phase == 1)
    {
        if (diagnostic.sample < AVSP_PORT_V2_HIT_LAST_SAMPLE)
        {
            if (!avsp_port_v2_hit_ko_step(&diagnostic.runtime))
                ++diagnostic.failures;
            ++diagnostic.sample;
            ++diagnostic.hit_sample_count;
        }
        if (diagnostic.sample == AVSP_PORT_V2_HIT_LAST_SAMPLE)
            finish_hit();
    }
    else if (diagnostic.phase == 2)
    {
        if (diagnostic.sample < AVSP_PORT_V2_KO_LAST_SAMPLE)
        {
            if (!avsp_port_v2_hit_ko_step(&diagnostic.runtime))
                ++diagnostic.failures;
            ++diagnostic.sample;
            ++diagnostic.ko_sample_count;
        }
        if (diagnostic.sample == AVSP_PORT_V2_KO_LAST_SAMPLE)
            finish_ko();
    }
    publish();
}
