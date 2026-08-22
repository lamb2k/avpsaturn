#ifndef AVSP_PORT_V2_HIT_KO_H
#define AVSP_PORT_V2_HIT_KO_H

#define AVSP_PORT_V2_HIT_KO_INTERFACE_VERSION 1
#define AVSP_PORT_V2_HIT_KO_CLASS_ID 31

#define AVSP_PORT_V2_HIT_SOURCE_SAMPLE 5191
#define AVSP_PORT_V2_HIT_LAST_SAMPLE 5227
#define AVSP_PORT_V2_KO_SOURCE_SAMPLE 5330
#define AVSP_PORT_V2_KO_LAST_SAMPLE 5469

#define AVSP_PORT_V2_HIT_ANIM_RECORD 0x0012DD50UL
#define AVSP_PORT_V2_HIT_RECOVERY_ANIM_RECORD 0x0012D2F8UL
#define AVSP_PORT_V2_KO_ANIM_RECORD 0x0012E214UL
#define AVSP_PORT_V2_KO_ANIM_RECORD_1 0x0012E224UL
#define AVSP_PORT_V2_KO_ANIM_RECORD_2 0x0012E234UL
#define AVSP_PORT_V2_KO_ANIM_RECORD_3 0x0012E244UL
#define AVSP_PORT_V2_KO_ANIM_RECORD_4 0x0012E254UL
#define AVSP_PORT_V2_KO_ANIM_RECORD_5 0x0012E268UL

typedef enum
{
    AVSP_PORT_V2_HIT_KO_NONE = 0,
    AVSP_PORT_V2_HIT_KO_HIT = 1,
    AVSP_PORT_V2_HIT_KO_KO = 2
} AvspPortV2HitKoKind;

typedef struct
{
    unsigned short state;
    unsigned short sub_state;
    unsigned short action;
    unsigned long anim_record;
    unsigned short anim_timer;
    short health;
    unsigned short hit_value;
} AvspPortV2HitKoActorState;

typedef struct
{
    AvspPortV2HitKoActorState actor;
    unsigned short kind;
    unsigned short elapsed;
    unsigned short active;
} AvspPortV2HitKoRuntime;

extern const AvspPortV2HitKoActorState avsp_port_v2_hit_source_before;
extern const AvspPortV2HitKoActorState avsp_port_v2_ko_source_before;

int avsp_port_v2_hit_ko_state_equal(
    const AvspPortV2HitKoActorState *first,
    const AvspPortV2HitKoActorState *second);
int avsp_port_v2_hit_ko_begin(
    AvspPortV2HitKoRuntime *runtime,
    AvspPortV2HitKoKind kind,
    const AvspPortV2HitKoActorState *source_before);
int avsp_port_v2_hit_ko_step(AvspPortV2HitKoRuntime *runtime);

#endif
