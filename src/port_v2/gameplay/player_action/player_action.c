#include "player_action.h"

#define AVSP_PW_START_X 978
#define AVSP_PW_START_LANE 320
#define AVSP_PW_START_HEALTH 101
#define AVSP_PW_MOVEMENT_DENOMINATOR 20
#define AVSP_PW_COMBO_RESET_FRAMES 30
#define AVSP_PW_HIT_RECOVERY_FRAMES 16
#define AVSP_PW_WORLD_X_MIN 864
#define AVSP_PW_WORLD_X_MAX 1184
#define AVSP_PW_WORLD_Z_MIN 224
#define AVSP_PW_WORLD_Z_MAX 327
#define AVSP_PW_UPPER_WORLD_Z 320
#define AVSP_PW_UPPER_WORLD_X_MAX 1091
#define AVSP_PW_IDLE_RECORD 0x0015F1F4UL

static const unsigned long avsp_pw_records_1[19] =
{
    0x0015F1F4UL, 0x001600E8UL, 0x001600F8UL, 0x001600F8UL,
    0x001600F8UL, 0x001600F8UL, 0x001600F8UL, 0x001600F8UL,
    0x001600F8UL, 0x001600F8UL, 0x001600F8UL, 0x001600F8UL,
    0x001600F8UL, 0x00160108UL, 0x00160108UL, 0x00160108UL,
    0x00160108UL, 0x00160108UL, 0x00160118UL
};

static const unsigned long avsp_pw_records_2[19] =
{
    0x0015F1F4UL, 0x0016012CUL, 0x0016013CUL, 0x0016014CUL,
    0x0016014CUL, 0x0016014CUL, 0x0016014CUL, 0x0016014CUL,
    0x0016014CUL, 0x0016014CUL, 0x0016014CUL, 0x0016014CUL,
    0x0016014CUL, 0x0016015CUL, 0x0016015CUL, 0x0016015CUL,
    0x0016016CUL, 0x0016016CUL, 0x0016017CUL
};

static const unsigned long avsp_pw_records_3[24] =
{
    0x0015F1F4UL, 0x00160190UL, 0x001601A0UL, 0x001601B0UL,
    0x001601B0UL, 0x001601C0UL, 0x001601C0UL, 0x001601C0UL,
    0x001601C0UL, 0x001601C0UL, 0x001601C0UL, 0x001601C0UL,
    0x001601C0UL, 0x001601C0UL, 0x001601C0UL, 0x001601C0UL,
    0x001601C0UL, 0x001601C0UL, 0x001601D0UL, 0x001601D0UL,
    0x001601D0UL, 0x001601D0UL, 0x001601D0UL, 0x001601E0UL
};

static const unsigned long avsp_pw_records_4[31] =
{
    0x0015F1F4UL, 0x001601F4UL, 0x00160204UL, 0x00160214UL,
    0x00160224UL, 0x00160224UL, 0x00160234UL, 0x00160234UL,
    0x00160234UL, 0x00160234UL, 0x00160234UL, 0x00160234UL,
    0x00160234UL, 0x00160234UL, 0x00160234UL, 0x00160234UL,
    0x00160234UL, 0x00160234UL, 0x00160234UL, 0x00160234UL,
    0x00160234UL, 0x00160234UL, 0x00160244UL, 0x00160244UL,
    0x00160244UL, 0x00160244UL, 0x00160254UL, 0x00160254UL,
    0x00160264UL, 0x00160274UL, 0x00160274UL
};

const AvspPwAttackDef avsp_pw_action_defs[AVSP_PW_ACTION_COUNT] =
{
    { 1u, 2u, 4u, 14u, 21u, 1538u, { -36, 39, 55, 25, 0, 8, 8 } },
    { 2u, 2u, 5u, 14u, 21u, 1538u, { -36, 39, 62, 18, 0, 8, 8 } },
    { 3u, 2u, 7u, 19u, 26u, 1538u, { -44, 43, 54, 17, 0, 9, 10 } },
    { 4u, 2u, 8u, 23u, 33u, 1542u, { -57, 55, 52, 52, 0, 12, 12 } }
};

static const short avsp_pw_selector4_heights[34] =
{
    0, 0, 0, 0, 0, 4, 8, 11, 13, 15, 15, 15, 15, 15, 15, 15, 15,
    15, 15, 15, 15, 17, 18, 18, 18, 17, 15, 13, 11, 8, 4, 0, 0, 0
};

static int avsp_pw_box_equal(const AvspPwAttackBox *first,
                             const AvspPwAttackBox *second)
{
    return first->x_center == second->x_center &&
           first->x_half == second->x_half &&
           first->y_center == second->y_center &&
           first->y_half == second->y_half &&
           first->z_center == second->z_center &&
           first->z_half == second->z_half &&
           first->hit_value == second->hit_value;
}

int avsp_pw_action_defs_valid(const AvspPwAttackDef *defs,
                              const unsigned int count)
{
    unsigned int index;
    if (defs == 0 || count != AVSP_PW_ACTION_COUNT) return 0;
    for (index = 0; index < count; ++index)
    {
        const AvspPwAttackDef *approved = &avsp_pw_action_defs[index];
        const AvspPwAttackDef *candidate = &defs[index];
        if (candidate->selector != approved->selector ||
            candidate->presentation_first != approved->presentation_first ||
            candidate->active_first != approved->active_first ||
            candidate->active_last != approved->active_last ||
            candidate->return_frame != approved->return_frame ||
            candidate->source_action != approved->source_action ||
            !avsp_pw_box_equal(&candidate->box, &approved->box)) return 0;
    }
    return 1;
}

int avsp_pw_render_facing(const unsigned short source_facing)
{
    /* ORACLE-04 records 0 for left and 1 for right. CapActor rendering uses
       a negative sign for left-facing horizontal flip and positive for right. */
    return source_facing == 0u ? -1 : 1;
}

int avsp_pw_source_presentation_ready(const unsigned short selector,
                                      const unsigned short action_elapsed)
{
    const AvspPwAttackDef *definition;
    if (selector < 1u || selector > AVSP_PW_ACTION_COUNT) return 0;
    definition = &avsp_pw_action_defs[selector - 1u];
    return action_elapsed >= definition->presentation_first &&
           action_elapsed < definition->return_frame;
}

unsigned long avsp_pw_assembly_for_record(const unsigned long record)
{
    switch (record)
    {
        case 0x0015F1F4UL: return 0x001626A4UL;
        case 0x001600E8UL: return 0x001629E6UL;
        case 0x001600F8UL: return 0x00162A04UL;
        case 0x00160108UL: return 0x001629E6UL;
        case 0x00160118UL: return 0x001629E6UL;
        case 0x0016012CUL: return 0x00162A32UL;
        case 0x0016013CUL: return 0x00162A5AUL;
        case 0x0016014CUL: return 0x00162A82UL;
        case 0x0016015CUL: return 0x00162A5AUL;
        case 0x0016016CUL: return 0x00162A32UL;
        case 0x0016017CUL: return 0x00162A32UL;
        case 0x00160190UL: return 0x00162A32UL;
        case 0x001601A0UL: return 0x0016144EUL;
        case 0x001601B0UL: return 0x00161476UL;
        case 0x001601C0UL: return 0x001614A4UL;
        case 0x001601D0UL: return 0x00161476UL;
        case 0x001601E0UL: return 0x00161476UL;
        case 0x001601F4UL: return 0x00162AA6UL;
        case 0x00160204UL: return 0x00162ABEUL;
        case 0x00160214UL: return 0x00162AD6UL;
        case 0x00160224UL: return 0x00162AFEUL;
        case 0x00160234UL: return 0x00162B26UL;
        case 0x00160244UL: return 0x00162B5AUL;
        case 0x00160254UL: return 0x00162B82UL;
        case 0x00160264UL: return 0x00162AA6UL;
        case 0x00160274UL: return 0x00162AA6UL;
        default: return 0UL;
    }
}

static void avsp_pw_update_presentation(AvspPwRuntime *runtime)
{
    unsigned int frame;
    const unsigned long *records;
    unsigned int count;
    runtime->animation_record = AVSP_PW_IDLE_RECORD;
    if (runtime->state != AVSP_PW_STATE_ATTACK ||
        runtime->action_elapsed < 2u) goto resolved;
    frame = (unsigned int)runtime->action_elapsed - 2u;
    records = 0;
    count = 0u;
    if (runtime->selector == 1u)
    {
        records = avsp_pw_records_1;
        count = 19u;
    }
    else if (runtime->selector == 2u)
    {
        records = avsp_pw_records_2;
        count = 19u;
    }
    else if (runtime->selector == 3u)
    {
        records = avsp_pw_records_3;
        count = 24u;
    }
    else if (runtime->selector == 4u)
    {
        records = avsp_pw_records_4;
        count = 31u;
    }
    if (records != 0 && frame < count) runtime->animation_record = records[frame];
resolved:
    runtime->assembly = avsp_pw_assembly_for_record(runtime->animation_record);
}

void avsp_pw_resolve_navigation(short *world_x, short *world_z)
{
    if (world_x == 0 || world_z == 0) return;
    if (*world_z < AVSP_PW_WORLD_Z_MIN) *world_z = AVSP_PW_WORLD_Z_MIN;
    if (*world_z > AVSP_PW_WORLD_Z_MAX) *world_z = AVSP_PW_WORLD_Z_MAX;
    if (*world_x < AVSP_PW_WORLD_X_MIN) *world_x = AVSP_PW_WORLD_X_MIN;
    if (*world_x > AVSP_PW_WORLD_X_MAX) *world_x = AVSP_PW_WORLD_X_MAX;
    if (*world_z >= AVSP_PW_UPPER_WORLD_Z &&
        *world_x > AVSP_PW_UPPER_WORLD_X_MAX)
        *world_x = AVSP_PW_UPPER_WORLD_X_MAX;
}

static void avsp_pw_apply_fraction(long *numerator, short *position,
                                   const int amount)
{
    long before;
    long after;
    before = *numerator / AVSP_PW_MOVEMENT_DENOMINATOR;
    *numerator += amount;
    after = *numerator / AVSP_PW_MOVEMENT_DENOMINATOR;
    *position = (short)(*position + (short)(after - before));
}

static void avsp_pw_apply_movement(AvspPwRuntime *runtime,
                                   const unsigned short mask)
{
    if ((mask & AVSP_PW_INPUT_LEFT) != 0u &&
        (mask & AVSP_PW_INPUT_RIGHT) == 0u)
    {
        avsp_pw_apply_fraction(&runtime->x_numerator, &runtime->x, -45);
        runtime->facing = 0;
    }
    else if ((mask & AVSP_PW_INPUT_RIGHT) != 0u &&
             (mask & AVSP_PW_INPUT_LEFT) == 0u)
    {
        avsp_pw_apply_fraction(&runtime->x_numerator, &runtime->x, 45);
        runtime->facing = 1;
    }
    if ((mask & AVSP_PW_INPUT_UP) != 0u &&
        (mask & AVSP_PW_INPUT_DOWN) == 0u)
        avsp_pw_apply_fraction(&runtime->lane_numerator, &runtime->lane, 7);
    else if ((mask & AVSP_PW_INPUT_DOWN) != 0u &&
             (mask & AVSP_PW_INPUT_UP) == 0u)
        avsp_pw_apply_fraction(&runtime->lane_numerator, &runtime->lane, -12);
    avsp_pw_resolve_navigation(&runtime->x, &runtime->lane);
}

static void avsp_pw_begin_attack(AvspPwRuntime *runtime)
{
    unsigned short selector = 1u;
    if (runtime->combo_followup_counter > 1u &&
        runtime->completed_close_step >= 1u &&
        runtime->completed_close_step < AVSP_PW_ACTION_COUNT)
        selector = (unsigned short)(runtime->completed_close_step + 1u);
    runtime->state = AVSP_PW_STATE_ATTACK;
    runtime->phase = AVSP_PW_PHASE_STARTUP;
    runtime->selector = selector;
    runtime->action_elapsed = 0u;
    runtime->source_action = 2u;
    runtime->source_substate = 512u;
    runtime->attack_active = 0u;
    runtime->height = 0;
    runtime->combo_next = selector;
    runtime->combo_idle_frames = 0u;
    runtime->combo_followup_counter = 0u;
    runtime->action_local_equipment_flag = 0u;
    avsp_pw_update_presentation(runtime);
    ++runtime->accepted_attack_edges;
}

static void avsp_pw_advance_attack(AvspPwRuntime *runtime)
{
    const AvspPwAttackDef *definition;
    ++runtime->action_elapsed;
    definition = &avsp_pw_action_defs[runtime->selector - 1u];
    runtime->source_action = runtime->action_elapsed <
        definition->presentation_first ? 2u : definition->source_action;
    if (runtime->selector == 4u)
    {
        if (runtime->action_elapsed == 2u) runtime->source_action = 1536u;
        else if (runtime->action_elapsed == 3u) runtime->source_action = 1540u;
        else if (runtime->action_elapsed == 32u) runtime->source_action = 1544u;
        if (runtime->action_elapsed < 34u)
            runtime->height = avsp_pw_selector4_heights[runtime->action_elapsed];
    }
    else if (runtime->action_elapsed == 2u)
        runtime->source_action = 1536u;
    runtime->attack_active = runtime->action_elapsed >= definition->active_first &&
        runtime->action_elapsed <= definition->active_last;
    if (runtime->attack_active) runtime->phase = AVSP_PW_PHASE_ACTIVE;
    else if (runtime->action_elapsed > definition->active_last)
    {
        if (runtime->phase != AVSP_PW_PHASE_RECOVERY)
        {
            runtime->completed_close_step = runtime->selector;
            runtime->combo_followup_counter = AVSP_PW_COMBO_RESET_FRAMES;
            runtime->combo_next = (unsigned short)(runtime->selector < 4u ?
                runtime->selector + 1u : 1u);
        }
        runtime->phase = AVSP_PW_PHASE_RECOVERY;
        if (runtime->combo_followup_counter > 0u)
            --runtime->combo_followup_counter;
    }
    avsp_pw_update_presentation(runtime);
    if (runtime->action_elapsed >= definition->return_frame)
    {
        runtime->state = AVSP_PW_STATE_CONTROL;
        runtime->phase = AVSP_PW_PHASE_NONE;
        runtime->selector = 0u;
        runtime->source_action = 0u;
        runtime->attack_active = 0u;
        runtime->height = 0;
        runtime->animation_record = AVSP_PW_IDLE_RECORD;
        runtime->assembly = avsp_pw_assembly_for_record(AVSP_PW_IDLE_RECORD);
        runtime->combo_idle_frames = 0u;
    }
}

void avsp_pw_init(AvspPwRuntime *runtime)
{
    unsigned int index;
    if (runtime == 0) return;
    runtime->x_numerator = 0;
    runtime->lane_numerator = 0;
    runtime->x = AVSP_PW_START_X;
    runtime->lane = AVSP_PW_START_LANE;
    runtime->height = 0;
    runtime->health = AVSP_PW_START_HEALTH;
    runtime->facing = 0;
    runtime->state = AVSP_PW_STATE_CONTROL;
    runtime->phase = AVSP_PW_PHASE_NONE;
    runtime->selector = 0u;
    runtime->action_elapsed = 0u;
    runtime->source_action = 0u;
    runtime->source_substate = 512u;
    runtime->attack_active = 0u;
    runtime->hit_timer = 0u;
    runtime->combo_next = 1u;
    runtime->combo_idle_frames = 0u;
    runtime->completed_close_step = 0u;
    runtime->combo_followup_counter = 0u;
    runtime->action_local_equipment_flag = 0u;
    runtime->animation_record = AVSP_PW_IDLE_RECORD;
    runtime->assembly = avsp_pw_assembly_for_record(AVSP_PW_IDLE_RECORD);
    runtime->current_mask = 0u;
    runtime->previous_mask = 0u;
    runtime->input_edges = 0u;
    for (index = 0; index < AVSP_PW_DIRECTION_LATENCY; ++index)
        runtime->direction_history[index] = 0u;
    runtime->accepted_attack_edges = 0UL;
    runtime->rejected_attack_edges = 0UL;
    runtime->contact_reports = 0UL;
}

void avsp_pw_step(AvspPwRuntime *runtime, const AvspPwInput *input)
{
    unsigned short direction_mask;
    unsigned short delayed_direction;
    unsigned int index;
    int attack_edge;
    if (runtime == 0 || input == 0) return;
    runtime->current_mask = input->mask;
    runtime->input_edges = (unsigned short)(runtime->current_mask &
                                             ~runtime->previous_mask);
    attack_edge = (runtime->input_edges & AVSP_PW_INPUT_ATTACK) != 0u;
    direction_mask = (unsigned short)(runtime->current_mask &
        (AVSP_PW_INPUT_LEFT | AVSP_PW_INPUT_RIGHT |
         AVSP_PW_INPUT_UP | AVSP_PW_INPUT_DOWN));
    delayed_direction = runtime->direction_history[AVSP_PW_DIRECTION_LATENCY - 1];
    for (index = AVSP_PW_DIRECTION_LATENCY - 1; index > 0; --index)
        runtime->direction_history[index] = runtime->direction_history[index - 1];
    runtime->direction_history[0] = direction_mask;

    if (input->received_damage > 0 && runtime->state != AVSP_PW_STATE_KO)
    {
        runtime->health = (short)(runtime->health - input->received_damage);
        runtime->attack_active = 0u;
        runtime->selector = 0u;
        runtime->combo_next = 1u;
        runtime->combo_idle_frames = 0u;
        runtime->completed_close_step = 0u;
        runtime->combo_followup_counter = 0u;
        runtime->action_local_equipment_flag = 0u;
        runtime->height = 0;
        if (runtime->health <= 0)
        {
            runtime->state = AVSP_PW_STATE_KO;
            runtime->phase = AVSP_PW_PHASE_NONE;
            runtime->source_action = 1024u;
        }
        else
        {
            runtime->state = AVSP_PW_STATE_HIT;
            runtime->phase = AVSP_PW_PHASE_RECOVERY;
            runtime->source_action = 514u;
            runtime->hit_timer = AVSP_PW_HIT_RECOVERY_FRAMES;
        }
    }

    if (runtime->state == AVSP_PW_STATE_CONTROL)
    {
        avsp_pw_apply_movement(runtime, delayed_direction);
        if (attack_edge) avsp_pw_begin_attack(runtime);
        else
        {
            if (runtime->combo_idle_frames < 0xffffu)
                ++runtime->combo_idle_frames;
            if (runtime->combo_followup_counter > 0u)
                --runtime->combo_followup_counter;
            if (runtime->combo_followup_counter == 0u)
            {
                runtime->combo_next = 1u;
                runtime->completed_close_step = 0u;
            }
        }
    }
    else if (runtime->state == AVSP_PW_STATE_ATTACK)
    {
        if (attack_edge && runtime->phase == AVSP_PW_PHASE_RECOVERY &&
            runtime->combo_followup_counter > 1u)
            avsp_pw_begin_attack(runtime);
        else
        {
            if (attack_edge) ++runtime->rejected_attack_edges;
            avsp_pw_advance_attack(runtime);
        }
    }
    else if (runtime->state == AVSP_PW_STATE_HIT)
    {
        if (attack_edge) ++runtime->rejected_attack_edges;
        if (runtime->hit_timer > 0u) --runtime->hit_timer;
        if (runtime->hit_timer == 0u)
        {
            runtime->state = AVSP_PW_STATE_CONTROL;
            runtime->phase = AVSP_PW_PHASE_NONE;
            runtime->source_action = 0u;
            runtime->animation_record = AVSP_PW_IDLE_RECORD;
            runtime->assembly = avsp_pw_assembly_for_record(AVSP_PW_IDLE_RECORD);
        }
    }
    else if (attack_edge) ++runtime->rejected_attack_edges;
    runtime->previous_mask = runtime->current_mask;
}

void avsp_pw_view(const AvspPwRuntime *runtime, AvspPwView *view)
{
    if (runtime == 0 || view == 0) return;
    view->x = runtime->x;
    view->lane = runtime->lane;
    view->height = runtime->height;
    view->health = runtime->health;
    view->facing = runtime->facing;
    view->state = runtime->state;
    view->phase = runtime->phase;
    view->selector = runtime->selector;
    view->action_elapsed = runtime->action_elapsed;
    view->source_action = runtime->source_action;
    view->source_substate = runtime->source_substate;
    view->attack_active = runtime->attack_active;
    view->completed_close_step = runtime->completed_close_step;
    view->combo_followup_counter = runtime->combo_followup_counter;
    view->action_local_equipment_flag = runtime->action_local_equipment_flag;
    view->animation_record = runtime->animation_record;
    view->assembly = runtime->assembly;
    if (runtime->selector >= 1u && runtime->selector <= 4u)
        view->attack_box = avsp_pw_action_defs[runtime->selector - 1u].box;
    else
    {
        view->attack_box.x_center = 0;
        view->attack_box.x_half = 0;
        view->attack_box.y_center = 0;
        view->attack_box.y_half = 0;
        view->attack_box.z_center = 0;
        view->attack_box.z_half = 0;
        view->attack_box.hit_value = 0;
    }
}

void avsp_pw_report_contact(AvspPwRuntime *runtime)
{
    if (runtime != 0) ++runtime->contact_reports;
}

int avsp_pw_can_control(const AvspPwRuntime *runtime)
{
    return runtime != 0 && runtime->state == AVSP_PW_STATE_CONTROL;
}
