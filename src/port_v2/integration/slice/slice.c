#include <string.h>

#include "slice.h"

static void avsp_port_v2_slice_contact_input(
    const AvspPortV2CombatSourceEvent *source,
    const AvspPortV2SliceRuntime *runtime,
    AvspPortV2CombatContactInput *input)
{
    (void)runtime;
    memset(input, 0, sizeof(*input));
    input->source_sample = source->source_sample;
    input->attack_selector = source->attack_selector;
    input->enemy_hurt_selector = AVSP_PORT_V2_COMBAT_ENEMY_HURT_SELECTOR;
    input->player_facing = source->player_facing;
    input->enemy_facing = source->enemy_facing;
    /* Collision remains in the source coordinate space.  The same event is
     * transformed below for presentation; keeping both views on this one
     * event prevents a rendered pose from drifting away from its selector. */
    input->player_x = source->player_x;
    input->player_y = source->player_y;
    input->player_z = source->player_z;
    input->enemy_x = source->enemy_x;
    input->enemy_y = source->enemy_y;
    input->enemy_z = source->enemy_z;
}

static int avsp_port_v2_slice_target_delta(const int source_delta)
{
    if (source_delta < 0)
        return -((-source_delta * AVSP_PORT_V2_COMBAT_TARGET_VIEW_WIDTH) /
                 AVSP_PORT_V2_COMBAT_SOURCE_VIEW_WIDTH);
    return (source_delta * AVSP_PORT_V2_COMBAT_TARGET_VIEW_WIDTH) /
        AVSP_PORT_V2_COMBAT_SOURCE_VIEW_WIDTH;
}

static int avsp_port_v2_slice_source_sample(const int frame)
{
    return AVSP_PORT_V2_SLICE_SOURCE_FIRST_CONTACT + frame -
        AVSP_PORT_V2_SLICE_FIRST_CONTACT_FRAME;
}

static int avsp_port_v2_slice_player_event(const int source_sample)
{
    AvspPortV2CombatSourceEvent source;
    int index;
    for (index = 0; index < AVSP_PORT_V2_COMBAT_SOURCE_EVENT_COUNT; ++index)
    {
        if (avsp_port_v2_combat_source_event(index, &source) &&
            source_sample >= source.player_presentation_start &&
            source_sample <= source.player_presentation_end)
            return index;
    }
    return -1;
}

static int avsp_port_v2_slice_reaction_event(const int source_sample)
{
    AvspPortV2CombatSourceEvent source;
    int index;
    for (index = 0; index < AVSP_PORT_V2_COMBAT_SOURCE_EVENT_COUNT; ++index)
    {
        if (avsp_port_v2_combat_source_event(index, &source) &&
            source_sample >= source.enemy_reaction_start &&
            source_sample <= source.enemy_reaction_end)
            return index;
    }
    return -1;
}

int avsp_port_v2_slice_identity_valid(
    const AvspPortV2SliceActorIdentity *identity)
{
    if (identity == 0) return 0;
    if (identity->role == AVSP_PORT_V2_SLICE_ROLE_PLAYER)
        return identity->actor_id == AVSP_PORT_V2_SLICE_ACTOR_PLAYER &&
            identity->class_id == AVSP_PORT_V2_SLICE_CLASS_NOT_APPLICABLE &&
            identity->archetype_id ==
                AVSP_PORT_V2_SLICE_ARCHETYPE_PREDATOR_WARRIOR &&
            identity->asset_set_id ==
                AVSP_PORT_V2_SLICE_ASSET_PLAYER_APPROVED &&
            identity->animation_set_id ==
                AVSP_PORT_V2_SLICE_ANIM_PLAYER_APPROVED;
    if (identity->role == AVSP_PORT_V2_SLICE_ROLE_ENEMY)
        return identity->actor_id ==
                AVSP_PORT_V2_SLICE_ACTOR_STREET_ALIEN &&
            identity->class_id == AVSP_PORT_V2_ENEMY_CLASS_ID &&
            identity->archetype_id ==
                AVSP_PORT_V2_SLICE_ARCHETYPE_STREET_ALIEN &&
            identity->asset_set_id ==
                AVSP_PORT_V2_SLICE_ASSET_STREET_ALIEN_ROM &&
            identity->animation_set_id ==
                AVSP_PORT_V2_SLICE_ANIM_STREET_ALIEN_ROM &&
            identity->archetype_id != AVSP_PORT_V2_SLICE_ARCHETYPE_STALKER &&
            identity->asset_set_id !=
                AVSP_PORT_V2_SLICE_ASSET_STALKER_CAPTURE &&
            identity->animation_set_id !=
                AVSP_PORT_V2_SLICE_ANIM_STALKER_CAPTURE;
    return 0;
}

int avsp_port_v2_slice_scene_valid(const AvspPortV2SliceSceneTrace *scene)
{
    if (scene == 0 ||
        !avsp_port_v2_slice_identity_valid(&scene->player_identity) ||
        !avsp_port_v2_slice_identity_valid(&scene->enemy_identity) ||
        scene->player_screen_x != scene->player_world_x -
            scene->camera_world_x + scene->aperture_origin_x ||
        scene->enemy_screen_x != scene->enemy_world_x -
            scene->camera_world_x + scene->aperture_origin_x ||
        scene->player_delta_screen_x != scene->player_delta_world_x -
            scene->delta_camera_world_x ||
        scene->enemy_delta_screen_x != scene->enemy_delta_world_x -
            scene->delta_camera_world_x ||
        scene->layer_scroll_x[0] != scene->camera_world_x)
        return 0;
    if (scene->player_presentation_active &&
        (scene->attack_sequence_step != scene->source_event_index + 1 ||
         scene->attack_selector != scene->attack_sequence_step ||
         scene->player_action != AVSP_PORT_V2_SLICE_ACTION_ATTACK ||
         scene->player_identity.animation_record == 0UL ||
         scene->player_identity.emitted_object_identity == 0UL ||
         scene->player_identity.emitted_tile_identity == 0UL))
        return 0;
    if (scene->source_sample >= AVSP_PORT_V2_SLICE_SOURCE_FIRST &&
        scene->source_sample <= AVSP_PORT_V2_SLICE_SOURCE_LAST &&
        (scene->enemy_identity.animation_record == 0UL ||
         scene->enemy_identity.emitted_object_identity == 0UL ||
         scene->enemy_identity.emitted_tile_identity == 0UL))
        return 0;
    if (scene->collision_result &&
        (!scene->player_attack_active ||
         scene->attacker_id != AVSP_PORT_V2_SLICE_ACTOR_PLAYER ||
         scene->defender_id != AVSP_PORT_V2_SLICE_ACTOR_STREET_ALIEN ||
         scene->health_after >= scene->health_before))
        return 0;
    if (!scene->collision_result &&
        scene->health_after != scene->health_before)
        return 0;
    if ((scene->semantic_hit || scene->semantic_ko) &&
        scene->defender_id != AVSP_PORT_V2_SLICE_ACTOR_STREET_ALIEN)
        return 0;
    if (scene->enemy_action == AVSP_PORT_V2_SLICE_ACTION_HIT &&
        !scene->semantic_hit)
        return 0;
    if (scene->enemy_action == AVSP_PORT_V2_SLICE_ACTION_KO &&
        !scene->semantic_ko)
        return 0;
    return 1;
}

int avsp_port_v2_slice_approval_locks_valid(void)
{
    return avsp_port_v2_combat_approval_locks_valid() &&
           avsp_port_v2_camera_validate_config(
               &avsp_port_v2_camera_approved_config) &&
           avsp_port_v2_stage_validate_config(
               &avsp_port_v2_stage_approved_config) &&
           avsp_port_v2_hud_validate_config(
               &avsp_port_v2_hud_approved_config) &&
           avsp_port_v2_pcm_validate_config(
               &avsp_port_v2_pcm_predator_melee_config) &&
           avsp_port_v2_cdda_validate_config(
               &avsp_port_v2_cdda_stage1_config) &&
           avsp_port_v2_residency_validate_manifest(
               &avsp_port_v2_stage1_residency_manifest);
}

void avsp_port_v2_slice_init(AvspPortV2SliceRuntime *runtime)
{
    if (runtime == 0) return;
    memset(runtime, 0, sizeof(*runtime));
    runtime->head_canary = AVSP_PORT_V2_SLICE_CANARY_HEAD;
    runtime->tail_canary = AVSP_PORT_V2_SLICE_CANARY_TAIL;
    avsp_port_v2_combat_init(&runtime->combat);
    avsp_port_v2_camera_init(&runtime->camera);
    avsp_port_v2_pcm_init(&runtime->pcm);
    avsp_port_v2_cdda_init(&runtime->cdda);
    avsp_port_v2_residency_init(&runtime->residency);
    runtime->player_world_x = AVSP_PORT_V2_SLICE_PLAYER_WORLD_X_INITIAL;
    runtime->player_lane = AVSP_PORT_V2_SLICE_PLAYER_LANE_INITIAL;
    runtime->enemy_world_x = AVSP_PORT_V2_SLICE_ENEMY_WORLD_X_INITIAL;
    runtime->enemy_lane = AVSP_PORT_V2_SLICE_ENEMY_LANE;
    runtime->previous_player_world_x = runtime->player_world_x;
    runtime->previous_enemy_world_x = runtime->enemy_world_x;
    runtime->enemy_action = AVSP_PORT_V2_SLICE_ACTION_WALK;
    runtime->source_event_index = -1;
    runtime->armed_source_event = -1;
}

int avsp_port_v2_slice_load(AvspPortV2SliceRuntime *runtime,
                            const int cartridge_available,
                            const AvspPortV2SliceLoadOps *operations)
{
    if (runtime == 0 || operations == 0 ||
        operations->residency_assets.read == 0 ||
        operations->load_hud == 0 || operations->load_pcm == 0 ||
        !cartridge_available || !avsp_port_v2_slice_approval_locks_valid())
    {
        if (runtime != 0) ++runtime->asset_failures;
        return 0;
    }
    if (!avsp_port_v2_residency_window_begin(&runtime->residency) ||
        !avsp_port_v2_residency_submit_read(
            &runtime->residency,
            AVSP_PORT_V2_RESIDENCY_REGION_DIAGNOSTIC,
            runtime->residency_buffer,
            AVSP_PORT_V2_RESIDENCY_FIXTURE_BYTES,
            &operations->residency_assets) ||
        !avsp_port_v2_residency_window_end(&runtime->residency) ||
        !avsp_port_v2_player_enemy_load(
            cartridge_available, &operations->actor_assets) ||
        !operations->load_hud() || !operations->load_pcm())
    {
        ++runtime->asset_failures;
        return 0;
    }
    runtime->ready = 1;
    return 1;
}

static void avsp_port_v2_slice_motion_step(
    AvspPortV2SliceRuntime *runtime, const AvspPortV2SliceInput *input)
{
    AvspPortV2CombatSourceEvent source;
    int player_event;
    int enemy_sample;
    runtime->previous_player_world_x = runtime->player_world_x;
    runtime->previous_enemy_world_x = runtime->enemy_world_x;
    runtime->previous_camera_world_x = runtime->camera_world_x;
    if (input->player.left && !input->player.right)
        runtime->player_world_x -=
            avsp_port_v2_player_approved_config.horizontal_step;
    else if (input->player.right && !input->player.left)
        runtime->player_world_x +=
            avsp_port_v2_player_approved_config.horizontal_step;
    if (input->player.up && !input->player.down)
        --runtime->player_lane;
    else if (input->player.down && !input->player.up)
        ++runtime->player_lane;
    if (input->enemy_move < 0)
        --runtime->enemy_world_x;
    else if (input->enemy_move > 0)
        ++runtime->enemy_world_x;
    runtime->camera_world_x = input->camera.scroll_x[0];
    runtime->source_sample = avsp_port_v2_slice_source_sample(input->frame);
    runtime->player_presentation_active = 0;
    runtime->player_attack_active = 0;
    runtime->player_attack_frame = 0;
    memset(&runtime->player_source, 0, sizeof(runtime->player_source));
    if (runtime->source_sample >= AVSP_PORT_V2_SLICE_SOURCE_FIRST &&
        runtime->source_sample <= AVSP_PORT_V2_SLICE_SOURCE_LAST)
    {
        player_event = avsp_port_v2_slice_player_event(runtime->source_sample);
        if (player_event >= 0 &&
            avsp_port_v2_combat_source_event(player_event, &source) &&
            avsp_port_v2_combat_source_player_frame(
                player_event,
                runtime->source_sample - source.player_presentation_start,
                &runtime->player_source))
        {
            runtime->source_event_index = player_event;
            runtime->player_presentation_active = 1;
            runtime->player_attack_active =
                runtime->player_source.attack_active;
            runtime->player_attack_frame =
                runtime->player_source.action_frame;
            runtime->player_height = runtime->player_source.height;
        }
        else
        {
            runtime->source_event_index = -1;
            runtime->player_height = 0;
        }
        runtime->player_world_x =
            AVSP_PORT_V2_SLICE_SOURCE_PLAYER_ANCHOR_X;
        runtime->player_lane =
            AVSP_PORT_V2_SLICE_SOURCE_PLAYER_ANCHOR_LANE;
        enemy_sample = runtime->source_sample > AVSP_PORT_V2_SLICE_SOURCE_FIRST ?
            runtime->source_sample - 1 : runtime->source_sample;
        if (avsp_port_v2_combat_source_enemy_sample(
                enemy_sample, &runtime->enemy_source))
        {
            runtime->enemy_world_x =
                AVSP_PORT_V2_SLICE_SOURCE_PLAYER_ANCHOR_X -
                avsp_port_v2_slice_target_delta(
                    1360 - runtime->enemy_source.world_x);
            runtime->enemy_lane =
                AVSP_PORT_V2_SLICE_SOURCE_PLAYER_ANCHOR_LANE -
                (319 - runtime->enemy_source.world_z);
        }
        if (input->player_attack)
        {
            int index;
            for (index = 0; index < AVSP_PORT_V2_COMBAT_SOURCE_EVENT_COUNT;
                 ++index)
            {
                if (avsp_port_v2_combat_source_event(index, &source) &&
                    runtime->source_sample == source.attack_input_sample)
                    runtime->armed_source_event = index;
            }
        }
    }
    else
    {
        runtime->player_height = input->player_height;
        if (runtime->source_sample < AVSP_PORT_V2_SLICE_SOURCE_FIRST ||
            runtime->combat.enemy_health >= 0)
            memset(&runtime->enemy_source, 0, sizeof(runtime->enemy_source));
    }
    runtime->player_attack_previous = input->player_attack;
}

static int avsp_port_v2_slice_attack_is_active(
    const AvspPortV2SliceRuntime *runtime)
{
    return runtime->player_presentation_active &&
        runtime->player_attack_active &&
        ((runtime->source_event_index == runtime->combat_event_count &&
          runtime->armed_source_event == runtime->combat_event_count) ||
         runtime->contact_this_frame);
}

static int avsp_port_v2_slice_combat_step(
    AvspPortV2SliceRuntime *runtime)
{
    AvspPortV2CombatSourceEvent source;
    AvspPortV2CombatContactInput contact;
    runtime->contact_this_frame = 0;
    if (runtime->combat_event_count < AVSP_PORT_V2_COMBAT_SOURCE_EVENT_COUNT &&
        avsp_port_v2_combat_source_event(
            runtime->combat_event_count, &source) &&
        runtime->source_sample == source.source_sample)
    {
        if (!avsp_port_v2_slice_attack_is_active(runtime) ||
            runtime->player_source.attack_selector != source.attack_selector)
            return 0;
        avsp_port_v2_slice_contact_input(&source, runtime, &contact);
        if (!avsp_port_v2_combat_apply_contact(
                &runtime->combat, &contact, &runtime->last_combat))
            return 0;
        runtime->contact_this_frame = runtime->last_combat.contact;
        if (runtime->last_combat.kind !=
            AVSP_PORT_V2_COMBAT_EVENT_CONTACT_MISS)
        {
            ++runtime->combat_event_count;
            runtime->armed_source_event = -1;
        }
    }
    else if (runtime->combat.transition.active &&
             !avsp_port_v2_combat_step_transition(&runtime->combat))
        return 0;
    return 1;
}

static void avsp_port_v2_slice_identity(
    AvspPortV2SliceRuntime *runtime, AvspPortV2SliceSceneTrace *scene)
{
    memset(&scene->player_identity, 0, sizeof(scene->player_identity));
    scene->player_identity.actor_id = AVSP_PORT_V2_SLICE_ACTOR_PLAYER;
    scene->player_identity.role = AVSP_PORT_V2_SLICE_ROLE_PLAYER;
    scene->player_identity.class_id =
        AVSP_PORT_V2_SLICE_CLASS_NOT_APPLICABLE;
    scene->player_identity.archetype_id =
        AVSP_PORT_V2_SLICE_ARCHETYPE_PREDATOR_WARRIOR;
    scene->player_identity.asset_set_id =
        AVSP_PORT_V2_SLICE_ASSET_PLAYER_APPROVED;
    scene->player_identity.animation_set_id =
        AVSP_PORT_V2_SLICE_ANIM_PLAYER_APPROVED;
    if (runtime->player_presentation_active)
    {
        scene->player_identity.animation_record =
            runtime->player_source.source_animation_record;
        scene->player_identity.emitted_object_identity =
            runtime->player_source.source_object_identity;
        scene->player_identity.emitted_tile_identity =
            runtime->player_source.source_tile_identity;
    }
    scene->enemy_identity.actor_id =
        AVSP_PORT_V2_SLICE_ACTOR_STREET_ALIEN;
    scene->enemy_identity.role = AVSP_PORT_V2_SLICE_ROLE_ENEMY;
    scene->enemy_identity.class_id = AVSP_PORT_V2_ENEMY_CLASS_ID;
    scene->enemy_identity.archetype_id =
        AVSP_PORT_V2_SLICE_ARCHETYPE_STREET_ALIEN;
    scene->enemy_identity.asset_set_id =
        AVSP_PORT_V2_SLICE_ASSET_STREET_ALIEN_ROM;
    scene->enemy_identity.animation_set_id =
        AVSP_PORT_V2_SLICE_ANIM_STREET_ALIEN_ROM;
    if (runtime->enemy_source.source_animation_record != 0UL)
    {
        scene->enemy_identity.palette_bank = runtime->enemy_source.palette;
        scene->enemy_identity.animation_record =
            runtime->enemy_source.source_animation_record;
        scene->enemy_identity.emitted_object_identity =
            runtime->enemy_source.source_object_identity;
        scene->enemy_identity.emitted_tile_identity =
            runtime->enemy_source.source_tile_identity;
    }
    else
    {
        scene->enemy_identity.palette_bank = AVSP_PORT_V2_ENEMY_PALETTE_BANK;
        scene->enemy_identity.animation_record =
            AVSP_PORT_V2_SLICE_ENEMY_WALK_RECORD;
    }
}

static void avsp_port_v2_slice_scene(
    AvspPortV2SliceRuntime *runtime, AvspPortV2SliceSceneTrace *scene)
{
    memset(scene, 0, sizeof(*scene));
    scene->player_world_x = runtime->player_world_x;
    scene->enemy_world_x = runtime->enemy_world_x;
    scene->camera_world_x = runtime->camera_world_x;
    scene->aperture_origin_x = AVSP_PORT_V2_SLICE_APERTURE_ORIGIN_X;
    scene->player_screen_x = scene->player_world_x - scene->camera_world_x +
        scene->aperture_origin_x;
    scene->enemy_screen_x = scene->enemy_world_x - scene->camera_world_x +
        scene->aperture_origin_x;
    scene->player_delta_world_x = runtime->player_world_x -
        runtime->previous_player_world_x;
    scene->enemy_delta_world_x = runtime->enemy_world_x -
        runtime->previous_enemy_world_x;
    scene->delta_camera_world_x = runtime->camera_world_x -
        runtime->previous_camera_world_x;
    scene->player_delta_screen_x = scene->player_delta_world_x -
        scene->delta_camera_world_x;
    scene->enemy_delta_screen_x = scene->enemy_delta_world_x -
        scene->delta_camera_world_x;
    scene->player_action = runtime->player_presentation_active ?
        AVSP_PORT_V2_SLICE_ACTION_ATTACK :
        ((scene->player_delta_world_x != 0) ?
         AVSP_PORT_V2_SLICE_ACTION_WALK : AVSP_PORT_V2_SLICE_ACTION_IDLE);
    scene->player_action_frame = runtime->player_attack_frame;
    scene->player_attack_active = avsp_port_v2_slice_attack_is_active(runtime);
    scene->player_presentation_active =
        runtime->player_presentation_active;
    scene->source_sample = runtime->source_sample;
    scene->source_event_index = runtime->source_event_index;
    if (runtime->player_presentation_active)
    {
        scene->attack_sequence_step = runtime->player_source.sequence_step;
        scene->attack_selector = runtime->player_source.attack_selector;
        scene->player_source_action = runtime->player_source.source_action;
        scene->player_source_substate =
            runtime->player_source.source_substate;
        scene->player_source_pose = runtime->player_source.pose_index;
        scene->player_source_pivot_x = runtime->player_source.pivot_x;
        scene->player_source_pivot_y = runtime->player_source.pivot_y;
        scene->player_source_height = runtime->player_source.height;
    }
    scene->enemy_action = runtime->enemy_action;
    scene->enemy_action_frame = runtime->enemy_action_frame;
    scene->enemy_source_action = runtime->enemy_source.source_action;
    scene->enemy_source_substate = runtime->enemy_source.source_substate;
    scene->collision_result = runtime->contact_this_frame;
    scene->health_before = runtime->combat.enemy_health;
    scene->health_after = runtime->combat.enemy_health;
    if (runtime->contact_this_frame)
    {
        scene->health_before = runtime->last_combat.health_before;
        scene->health_after = runtime->last_combat.health_after;
    }
    scene->semantic_hit = runtime->semantic_hit;
    scene->semantic_ko = runtime->semantic_ko;
    if (runtime->contact_this_frame)
    {
        scene->attacker_id = AVSP_PORT_V2_SLICE_ACTOR_PLAYER;
        scene->defender_id = AVSP_PORT_V2_SLICE_ACTOR_STREET_ALIEN;
    }
    else if (runtime->semantic_hit || runtime->semantic_ko)
        scene->defender_id = AVSP_PORT_V2_SLICE_ACTOR_STREET_ALIEN;
    avsp_port_v2_slice_identity(runtime, scene);
}

static int avsp_port_v2_slice_cdda_step(
    AvspPortV2SliceRuntime *runtime, const AvspPortV2SliceInput *input,
    AvspPortV2CddaFrame *frame)
{
    AvspPortV2CddaInput cdda_input;
    cdda_input.command = input->cdda_command;
    cdda_input.track = AVSP_PORT_V2_CDDA_TRACK_STAGE1;
    cdda_input.source_frame = AVSP_PORT_V2_CDDA_SOURCE_FRAME_STAGE1;
    if (!avsp_port_v2_cdda_step(&runtime->cdda, &cdda_input, frame)) return 0;
    if (frame->start_request &&
        !avsp_port_v2_residency_cdda_started(&runtime->residency)) return 0;
    if (frame->stop_request &&
        !avsp_port_v2_residency_cdda_stopped(&runtime->residency)) return 0;
    return 1;
}

int avsp_port_v2_slice_step(AvspPortV2SliceRuntime *runtime,
                            const AvspPortV2SliceInput *input,
                            AvspPortV2SliceFrame *frame)
{
    AvspPortV2PlayerEnemyInput actor_input;
    AvspPortV2HudInput hud_input;
    AvspPortV2PcmInput pcm_input;
    int reaction_event;
    if (runtime == 0 || input == 0 || frame == 0 || !runtime->ready ||
        input->frame != runtime->frame || !avsp_port_v2_slice_canaries_ok(runtime))
        return 0;
    memset(frame, 0, sizeof(*frame));
    actor_input.player = input->player;
    actor_input.enemy_translated = input->enemy_move != 0;
    avsp_port_v2_player_enemy_step(&runtime->combat.presentation, &actor_input);
    avsp_port_v2_slice_motion_step(runtime, input);
    if (!avsp_port_v2_slice_combat_step(runtime)) return 0;
    reaction_event = avsp_port_v2_slice_reaction_event(
        runtime->source_sample);
    runtime->semantic_hit = reaction_event >= 0 && reaction_event < 3 &&
        runtime->combat_event_count > reaction_event;
    runtime->semantic_ko = runtime->combat.enemy_health < 0;
    if (runtime->semantic_ko)
        runtime->enemy_action = AVSP_PORT_V2_SLICE_ACTION_KO;
    else if (runtime->semantic_hit)
        runtime->enemy_action = AVSP_PORT_V2_SLICE_ACTION_HIT;
    else
        runtime->enemy_action = AVSP_PORT_V2_SLICE_ACTION_WALK;
    runtime->enemy_action_frame =
        runtime->enemy_source.source_animation_record != 0UL ?
        runtime->enemy_source.action_frame :
        runtime->combat.presentation.enemy.locomotion_frame;
    avsp_port_v2_camera_step(&runtime->camera, &input->camera);
    avsp_port_v2_camera_view(&runtime->camera, &frame->camera);
    if (!avsp_port_v2_stage_build_frame(&frame->camera, &frame->stage))
        return 0;
    memset(&hud_input, 0, sizeof(hud_input));
    hud_input.players[AVSP_PORT_V2_HUD_P1].visible = 1;
    hud_input.players[AVSP_PORT_V2_HUD_P1].character_id =
        AVSP_PORT_V2_CHARACTER_PREDATOR_WARRIOR;
    hud_input.players[AVSP_PORT_V2_HUD_P1].health = input->player_health;
    hud_input.players[AVSP_PORT_V2_HUD_P1].energy = input->player_energy;
    hud_input.players[AVSP_PORT_V2_HUD_P2].visible = input->player2_visible;
    hud_input.players[AVSP_PORT_V2_HUD_P2].character_id =
        AVSP_PORT_V2_CHARACTER_MAJOR_SCHAEFER;
    hud_input.players[AVSP_PORT_V2_HUD_P2].health = input->player2_health;
    hud_input.players[AVSP_PORT_V2_HUD_P2].energy = input->player2_energy;
    if (!avsp_port_v2_hud_build_frame(&hud_input, &frame->hud)) return 0;
    pcm_input.frame = input->frame;
    pcm_input.cue_event = input->pcm_cue_event &&
        runtime->contact_this_frame && runtime->combat_event_count == 1;
    pcm_input.cue_id = AVSP_PORT_V2_PCM_CUE_PREDATOR_MELEE;
    if (!avsp_port_v2_pcm_step(&runtime->pcm, &pcm_input, &frame->pcm) ||
        !avsp_port_v2_slice_cdda_step(runtime, input, &frame->cdda))
        return 0;
    avsp_port_v2_player_enemy_view(&runtime->combat.presentation,
                                   &frame->actors);
    frame->actors.player.world_x = runtime->player_world_x;
    frame->actors.player.lane = runtime->player_lane;
    frame->actors.player.facing = 1;
    frame->actors.enemy.world_x = runtime->enemy_world_x;
    frame->actors.enemy.lane = runtime->enemy_lane;
    frame->actors.enemy.facing =
        avsp_port_v2_enemy_approved_config.facing;
    avsp_port_v2_slice_scene(runtime, &frame->scene);
    frame->scene.layer_scroll_x[0] = frame->stage.layers[0].scroll_x;
    frame->scene.layer_scroll_x[1] = frame->stage.layers[1].scroll_x;
    frame->interface_version = AVSP_PORT_V2_SLICE_INTERFACE_VERSION;
    frame->ready = runtime->ready;
    frame->frame = input->frame;
    frame->combat = runtime->last_combat;
    frame->combat_event_count = runtime->combat_event_count;
    frame->asset_failures = runtime->asset_failures;
    frame->fallback_used = runtime->fallback_used;
    frame->canaries_ok = avsp_port_v2_slice_canaries_ok(runtime);
    if (!avsp_port_v2_slice_scene_valid(&frame->scene)) return 0;
    ++runtime->frame;
    return 1;
}

int avsp_port_v2_slice_submit_read(AvspPortV2SliceRuntime *runtime,
                                   const int region_id,
                                   unsigned char *destination,
                                   const int capacity,
                                   const AvspPortV2ResidencyAssetOps *operations)
{
    if (runtime == 0) return 0;
    return avsp_port_v2_residency_submit_read(
        &runtime->residency, region_id, destination, capacity, operations);
}

int avsp_port_v2_slice_canaries_ok(const AvspPortV2SliceRuntime *runtime)
{
    return runtime != 0 &&
           runtime->head_canary == AVSP_PORT_V2_SLICE_CANARY_HEAD &&
           runtime->tail_canary == AVSP_PORT_V2_SLICE_CANARY_TAIL &&
           avsp_port_v2_residency_canaries_ok(&runtime->residency);
}
