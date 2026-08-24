#include <stdio.h>
#include <string.h>

#include "../../../../src/port_v2/integration/slice/slice.h"

static int load_order[9];
static int load_count;
static int stage_submits;
static int hud_submits;
static int pcm_starts;
static int pcm_stops;
static int cdda_starts;
static int cdda_stops;

static int record_load(const int step)
{
    if (load_count >= 9) return 0;
    load_order[load_count++] = step;
    return 1;
}

static int read_fixture(const int region_id, unsigned char *destination,
                        const int capacity)
{
    static const unsigned char payload[64] =
        "AVSP-CDDA-RESIDENCY-V1|TRACK=02|WINDOW=PHASE-BOUNDARY|OK!!!!!!!\n";
    if (region_id != AVSP_PORT_V2_RESIDENCY_REGION_DIAGNOSTIC ||
        capacity < 64 || !record_load(1)) return -1;
    memcpy(destination, payload, 64);
    return 64;
}

static int load_tiles(void) { return record_load(2); }
static int load_stage(void) { return record_load(3); }
static int load_idle(void) { return record_load(4); }
static int load_actions(void) { return record_load(5); }
static int create_sprites(void) { return record_load(6); }
static int load_hud(void) { return record_load(7); }
static int load_pcm(void) { return record_load(8); }

static int stage_layer(const AvspPortV2StageLayerEvent *event)
{
    if (event == 0 || event->layer_id < 0 || event->layer_id > 1) return 0;
    ++stage_submits;
    return 1;
}

static int stage_priorities(const int actor, const int foreground)
{
    if (actor != 4 || foreground != 6) return 0;
    ++stage_submits;
    return 1;
}

static int hud_frame(const AvspPortV2HudFrame *frame)
{
    if (frame == 0 || frame->player_count != 2) return 0;
    ++hud_submits;
    return 1;
}

static int pcm_start(const AvspPortV2PcmFrame *frame)
{
    if (frame == 0 || frame->cue_id != 1) return 0;
    ++pcm_starts;
    return 1;
}

static int pcm_stop(const AvspPortV2PcmFrame *frame)
{
    if (frame == 0 || frame->cue_id != 1) return 0;
    ++pcm_stops;
    return 1;
}

static int cdda_start(const AvspPortV2CddaFrame *frame)
{
    if (frame == 0 || frame->track != 2) return 0;
    ++cdda_starts;
    return 1;
}

static int cdda_stop(const AvspPortV2CddaFrame *frame)
{
    if (frame == 0 || frame->track != 2) return 0;
    ++cdda_stops;
    return 1;
}

static void load_operations(AvspPortV2SliceLoadOps *operations)
{
    memset(operations, 0, sizeof(*operations));
    operations->residency_assets.read = read_fixture;
    operations->actor_assets.load_tile_archive = load_tiles;
    operations->actor_assets.load_background = load_stage;
    operations->actor_assets.load_player_idle = load_idle;
    operations->actor_assets.load_player_actions = load_actions;
    operations->actor_assets.create_player_sprites = create_sprites;
    operations->load_hud = load_hud;
    operations->load_pcm = load_pcm;
}

static void adapted_stage_camera(const int tick, AvspPortV2CameraInput *camera)
{
    /* ADAPTED capability-slice choreography. These checkpoints mirror the
     * pinned stage adapter's observed pan and final hold; they are not a
     * production camera controller. Keeping the final 161-pixel anchor here
     * prevents the host replay from inventing a post-KO exit that the Saturn
     * scene does not perform. */
    if (tick < 46)
    {
        camera->scroll_x[0] = 0;
        camera->scroll_x[1] = 7;
    }
    else if (tick < 50)
    {
        camera->scroll_x[0] = 10;
        camera->scroll_x[1] = 15;
    }
    else if (tick < 60)
    {
        camera->scroll_x[0] = 44;
        camera->scroll_x[1] = 45;
    }
    else if (tick < 70)
    {
        camera->scroll_x[0] = 95;
        camera->scroll_x[1] = 90;
    }
    else if (tick < 80)
    {
        camera->scroll_x[0] = 123;
        camera->scroll_x[1] = 115;
    }
    else if (tick < 90)
    {
        camera->scroll_x[0] = 144;
        camera->scroll_x[1] = 133;
    }
    else
    {
        camera->scroll_x[0] = 161;
        camera->scroll_x[1] = 148;
    }
}

static int replay(AvspPortV2SliceFrame *final_frame,
                  AvspPortV2SliceFrame *first_contact_frame,
                  const int emit)
{
    AvspPortV2SliceRuntime runtime;
    AvspPortV2SliceLoadOps loads;
    AvspPortV2SliceInput input;
    AvspPortV2SliceFrame frame;
    AvspPortV2StageRenderOps stage;
    AvspPortV2HudRenderOps hud;
    AvspPortV2PcmAudioOps pcm;
    AvspPortV2CddaAudioOps cdda;
    unsigned char read_buffer[64];
    int tick;
    load_count = stage_submits = hud_submits = 0;
    pcm_starts = pcm_stops = cdda_starts = cdda_stops = 0;
    load_operations(&loads);
    avsp_port_v2_slice_init(&runtime);
    if (!avsp_port_v2_slice_load(&runtime, 1, &loads)) return 0;
    stage.submit_layer = stage_layer;
    stage.submit_sprite_priorities = stage_priorities;
    hud.submit_frame = hud_frame;
    pcm.start = pcm_start;
    pcm.stop = pcm_stop;
    cdda.start = cdda_start;
    cdda.stop = cdda_stop;
    for (tick = 0; tick < 3001; ++tick)
    {
        memset(&input, 0, sizeof(input));
        input.frame = tick;
        input.player.down = tick >= 30 && tick < 60;
        input.player.right = tick >= 300 && tick < 335;
        input.enemy_move = tick >= 300 && tick < 490;
        input.player_attack = tick == 595 || tick == 640 ||
            tick == 685 || tick == 730;
        input.player_height = 0;
        adapted_stage_camera(tick, &input.camera);
        input.player_health = 101;
        input.player_energy = 64;
        input.player2_visible = 1;
        input.player2_health = 50;
        input.player2_energy = 32;
        if (tick == 0) input.cdda_command = AVSP_PORT_V2_CDDA_START;
        if (tick == 3000) input.cdda_command = AVSP_PORT_V2_CDDA_STOP;
        input.pcm_cue_event = tick == 600;
        if (!avsp_port_v2_slice_step(&runtime, &input, &frame) ||
            !avsp_port_v2_stage_submit(&frame.stage, &stage) ||
            !avsp_port_v2_hud_submit(&frame.hud, &hud) ||
            !avsp_port_v2_pcm_submit(&frame.pcm, &pcm) ||
            !avsp_port_v2_cdda_submit(&frame.cdda, &cdda)) return 0;
        if (tick == 600 && first_contact_frame != 0)
            *first_contact_frame = frame;
        if (tick == 60 && avsp_port_v2_slice_submit_read(
                &runtime, AVSP_PORT_V2_RESIDENCY_REGION_DIAGNOSTIC,
                read_buffer, sizeof(read_buffer), &loads.residency_assets))
            return 0;
    }
    if (emit)
        printf("F%d A%d C%d HP%d HIT%d KO%d HUD%d PCM%d/%d CDDA%d/%d "
               "LATE%d NEG%d SCROLL%d FALLBACK%d CANARY%d "
               "PW%d EW%d CAM%d PS%d ES%d PAL%d REC%lx\n",
               frame.frame, frame.actors.actor_count,
               frame.combat_event_count, runtime.combat.enemy_health,
               runtime.combat.hit_count, runtime.combat.ko_count,
               frame.hud.render_count, pcm_starts, pcm_stops,
               cdda_starts, cdda_stops,
               runtime.residency.late_read_attempts,
               runtime.residency.negative_rejections,
               frame.camera.scroll_steps, frame.fallback_used,
               frame.canaries_ok, frame.scene.player_world_x,
               frame.scene.enemy_world_x, frame.scene.camera_world_x,
               frame.scene.player_screen_x, frame.scene.enemy_screen_x,
               frame.scene.enemy_identity.palette_bank,
               frame.scene.enemy_identity.animation_record);
    *final_frame = frame;
    return load_count == 8 && load_order[0] == 1 && load_order[1] == 2 &&
           load_order[2] == 3 && load_order[3] == 4 && load_order[4] == 5 &&
           load_order[5] == 6 && load_order[6] == 7 && load_order[7] == 8 &&
           frame.interface_version == 3 && frame.ready &&
           frame.actors.actor_count == 2 && frame.combat_event_count == 4 &&
           runtime.combat.enemy_health == -1 && runtime.combat.hit_count == 1 &&
           runtime.combat.ko_count == 1 && frame.hud.render_count == 4 &&
           pcm_starts == 1 && pcm_stops == 1 && cdda_starts == 1 &&
           cdda_stops == 1 && runtime.residency.late_read_attempts == 1 &&
           runtime.residency.negative_rejections == 1 &&
           frame.camera.scroll_steps == 6 && !frame.fallback_used &&
           frame.canaries_ok && stage_submits == 9003 && hud_submits == 3001 &&
           frame.scene.player_world_x == 440 &&
           frame.scene.camera_world_x == 161 &&
           frame.scene.player_screen_x == 103 &&
           frame.scene.enemy_identity.archetype_id ==
               AVSP_PORT_V2_SLICE_ARCHETYPE_STREET_ALIEN &&
           frame.scene.enemy_identity.palette_bank == 19 &&
           frame.scene.enemy_identity.animation_record ==
               AVSP_PORT_V2_KO_ANIM_RECORD_5;
}

static int negative_controls(const AvspPortV2SliceFrame *contact_frame,
                             const AvspPortV2SliceFrame *final_frame)
{
    AvspPortV2SliceRuntime runtime;
    AvspPortV2SliceLoadOps loads;
    unsigned char buffer[64];
    load_count = 0;
    load_operations(&loads);
    avsp_port_v2_slice_init(&runtime);
    loads.actor_assets.load_player_actions = 0;
    if (avsp_port_v2_slice_load(&runtime, 1, &loads) ||
        runtime.asset_failures != 1) return 0;
    load_count = 0;
    load_operations(&loads);
    avsp_port_v2_slice_init(&runtime);
    if (!avsp_port_v2_slice_load(&runtime, 1, &loads) ||
        !avsp_port_v2_residency_cdda_started(&runtime.residency) ||
        avsp_port_v2_slice_submit_read(
            &runtime, AVSP_PORT_V2_RESIDENCY_REGION_DIAGNOSTIC,
            buffer, sizeof(buffer), &loads.residency_assets) ||
        runtime.residency.late_read_attempts != 1) return 0;
    runtime.tail_canary = 0;
    if (avsp_port_v2_slice_canaries_ok(&runtime)) return 0;
    {
        AvspPortV2SliceRuntime encounter;
        AvspPortV2SliceInput input;
        AvspPortV2SliceFrame frame;
        int tick;
        load_count = 0;
        load_operations(&loads);
        avsp_port_v2_slice_init(&encounter);
        if (!avsp_port_v2_slice_load(&encounter, 1, &loads)) return 0;
        for (tick = 0; tick <= 600; ++tick)
        {
            int stepped;
            memset(&input, 0, sizeof(input));
            input.frame = tick;
            input.player_health = 101;
            input.player_energy = 64;
            stepped = avsp_port_v2_slice_step(&encounter, &input, &frame);
            if (tick < 600 && !stepped) return 0;
            if (tick == 600 && stepped) return 0;
            if (tick < 600 &&
                (encounter.combat.damage_count != 0 ||
                 encounter.combat_event_count != 0)) return 0;
        }
        if (encounter.combat.damage_count != 0 ||
            encounter.combat_event_count != 0 ||
            encounter.combat.enemy_health != 87 ||
            encounter.last_combat.kind != AVSP_PORT_V2_COMBAT_EVENT_NONE)
            return 0;
    }
    {
        AvspPortV2SliceSceneTrace scene = final_frame->scene;
        scene.player_screen_x =
            scene.player_world_x + scene.aperture_origin_x;
        if (avsp_port_v2_slice_scene_valid(&scene))
        { puts("negative omitted camera term accepted"); return 0; }
    }
    {
        AvspPortV2SliceSceneTrace scene = final_frame->scene;
        scene.player_screen_x = scene.player_world_x +
            scene.camera_world_x + scene.aperture_origin_x;
        if (avsp_port_v2_slice_scene_valid(&scene))
        { puts("negative camera term accepted"); return 0; }
    }
    {
        AvspPortV2SliceSceneTrace scene = final_frame->scene;
        scene.enemy_identity.archetype_id =
            AVSP_PORT_V2_SLICE_ARCHETYPE_STALKER;
        scene.enemy_identity.asset_set_id =
            AVSP_PORT_V2_SLICE_ASSET_STALKER_CAPTURE;
        scene.enemy_identity.animation_set_id =
            AVSP_PORT_V2_SLICE_ANIM_STALKER_CAPTURE;
        if (avsp_port_v2_slice_scene_valid(&scene))
        { puts("negative stalker identity accepted"); return 0; }
    }
    {
        AvspPortV2SliceSceneTrace scene = contact_frame->scene;
        scene.player_attack_active = 0;
        if (avsp_port_v2_slice_scene_valid(&scene))
        { puts("negative pre-active damage accepted"); return 0; }
        scene = contact_frame->scene;
        scene.attacker_id = AVSP_PORT_V2_SLICE_ACTOR_STREET_ALIEN;
        scene.defender_id = AVSP_PORT_V2_SLICE_ACTOR_PLAYER;
        if (avsp_port_v2_slice_scene_valid(&scene))
        { puts("negative attacker swap accepted"); return 0; }
        scene = contact_frame->scene;
        scene.defender_id = AVSP_PORT_V2_SLICE_ACTOR_PLAYER;
        if (avsp_port_v2_slice_scene_valid(&scene))
        { puts("negative defender routing accepted"); return 0; }
        scene = contact_frame->scene;
        scene.attacker_id = AVSP_PORT_V2_SLICE_ACTOR_STREET_ALIEN;
        if (avsp_port_v2_slice_scene_valid(&scene))
        { puts("negative enemy-versus-enemy contact accepted"); return 0; }
        scene = contact_frame->scene;
        scene.collision_result = 0;
        if (avsp_port_v2_slice_scene_valid(&scene))
        { puts("negative damage without contact accepted"); return 0; }
        scene = contact_frame->scene;
        scene.enemy_action = AVSP_PORT_V2_SLICE_ACTION_HIT;
        scene.semantic_hit = 0;
        if (avsp_port_v2_slice_scene_valid(&scene))
        { puts("negative visual HIT accepted"); return 0; }
    }
    return 1;
}

int main(const int argc, char **argv)
{
    AvspPortV2SliceFrame first;
    AvspPortV2SliceFrame second;
    AvspPortV2SliceFrame first_contact;
    AvspPortV2SliceFrame second_contact;
    int negative = argc == 2 && strcmp(argv[1], "--negative-control") == 0;
    if (argc > 2 || (argc == 2 && !negative)) return 2;
    if (negative)
    {
        if (!replay(&first, &first_contact, 0) ||
            !negative_controls(&first_contact, &first)) return 1;
        puts("Playable slice negative controls: PASS");
        return 0;
    }
    if (!avsp_port_v2_slice_approval_locks_valid() ||
        !replay(&first, &first_contact, 1) ||
        !replay(&second, &second_contact, 0) ||
        memcmp(&first, &second, sizeof(first)) != 0 ||
        memcmp(&first_contact, &second_contact,
               sizeof(first_contact)) != 0) return 1;
    puts("Playable slice deterministic integration: PASS");
    return 0;
}
