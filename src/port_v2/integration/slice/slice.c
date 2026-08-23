#include <string.h>

#include "slice.h"

static void avsp_port_v2_slice_contact_input(
    const AvspPortV2CombatSourceEvent *source,
    AvspPortV2CombatContactInput *input)
{
    memset(input, 0, sizeof(*input));
    input->source_sample = source->source_sample;
    input->attack_selector = source->attack_selector;
    input->enemy_hurt_selector = AVSP_PORT_V2_COMBAT_ENEMY_HURT_SELECTOR;
    input->player_facing = source->player_facing;
    input->enemy_facing = source->enemy_facing;
    input->player_x = source->player_x;
    input->player_y = source->player_y;
    input->player_z = source->player_z;
    input->enemy_x = source->enemy_x;
    input->enemy_y = source->enemy_y;
    input->enemy_z = source->enemy_z;
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

static int avsp_port_v2_slice_combat_step(
    AvspPortV2SliceRuntime *runtime, const AvspPortV2SliceInput *input)
{
    AvspPortV2CombatSourceEvent source;
    AvspPortV2CombatContactInput contact;
    if (input->contact_event)
    {
        if (!avsp_port_v2_combat_source_event(input->contact_index, &source))
            return 0;
        avsp_port_v2_slice_contact_input(&source, &contact);
        if (!avsp_port_v2_combat_apply_contact(
                &runtime->combat, &contact, &runtime->last_combat))
            return 0;
        ++runtime->combat_event_count;
    }
    else if (runtime->combat.transition.active &&
             !avsp_port_v2_combat_step_transition(&runtime->combat))
        return 0;
    return 1;
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
    if (runtime == 0 || input == 0 || frame == 0 || !runtime->ready ||
        input->frame != runtime->frame || !avsp_port_v2_slice_canaries_ok(runtime))
        return 0;
    memset(frame, 0, sizeof(*frame));
    actor_input.player = input->player;
    actor_input.enemy_translated = input->enemy_translated;
    avsp_port_v2_player_enemy_step(&runtime->combat.presentation, &actor_input);
    if (!avsp_port_v2_slice_combat_step(runtime, input)) return 0;
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
    pcm_input.cue_event = input->pcm_cue_event;
    pcm_input.cue_id = AVSP_PORT_V2_PCM_CUE_PREDATOR_MELEE;
    if (!avsp_port_v2_pcm_step(&runtime->pcm, &pcm_input, &frame->pcm) ||
        !avsp_port_v2_slice_cdda_step(runtime, input, &frame->cdda))
        return 0;
    avsp_port_v2_player_enemy_view(&runtime->combat.presentation,
                                   &frame->actors);
    frame->interface_version = AVSP_PORT_V2_SLICE_INTERFACE_VERSION;
    frame->ready = runtime->ready;
    frame->frame = input->frame;
    frame->combat = runtime->last_combat;
    frame->combat_event_count = runtime->combat_event_count;
    frame->asset_failures = runtime->asset_failures;
    frame->fallback_used = runtime->fallback_used;
    frame->canaries_ok = avsp_port_v2_slice_canaries_ok(runtime);
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
