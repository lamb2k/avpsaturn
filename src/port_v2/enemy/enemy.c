#include "enemy.h"

const AvspPortV2EnemyConfig avsp_port_v2_enemy_approved_config =
{
    AVSP_PORT_V2_ENEMY_CLASS_ID,
    AVSP_PORT_V2_ENEMY_PALETTE_BANK,
    192, 240, 200, -1, 120,
    AVSP_PORT_V2_ENEMY_WALK_FRAMES,
    AVSP_PORT_V2_ENEMY_WALK_POSES
};

int avsp_port_v2_enemy_validate_config(const AvspPortV2EnemyConfig *config)
{
    const AvspPortV2EnemyConfig *approved =
        &avsp_port_v2_enemy_approved_config;
    if (config == 0) return 0;
    return config->class_id == approved->class_id &&
           config->palette_bank == approved->palette_bank &&
           config->stationary_x == approved->stationary_x &&
           config->translated_x == approved->translated_x &&
           config->lane == approved->lane &&
           config->facing == approved->facing &&
           config->phase_frames == approved->phase_frames &&
           config->walk_frames == approved->walk_frames &&
           config->walk_poses == approved->walk_poses;
}

int avsp_port_v2_enemy_load(const int cartridge_available,
                            const AvspPortV2EnemyLoadOps *operations)
{
    if (!cartridge_available || operations == 0 ||
        operations->load_tile_archive == 0 ||
        operations->load_background == 0)
        return 0;
    return operations->load_tile_archive() && operations->load_background();
}

void avsp_port_v2_enemy_init(AvspPortV2EnemyRuntime *runtime)
{
    if (runtime == 0) return;
    runtime->frame = 0;
    runtime->x = avsp_port_v2_enemy_approved_config.stationary_x;
    runtime->lane = avsp_port_v2_enemy_approved_config.lane;
    runtime->facing = avsp_port_v2_enemy_approved_config.facing;
    runtime->locomotion_frame = 0;
    runtime->phase = 0;
}

void avsp_port_v2_enemy_step(AvspPortV2EnemyRuntime *runtime,
                             const AvspPortV2EnemyInput *input)
{
    if (runtime == 0 || input == 0) return;
    runtime->phase = input->translated ? 1 : 0;
    runtime->x = input->translated ?
        avsp_port_v2_enemy_approved_config.translated_x :
        avsp_port_v2_enemy_approved_config.stationary_x;
    runtime->locomotion_frame = runtime->frame;
    ++runtime->frame;
    if (runtime->frame >= avsp_port_v2_enemy_approved_config.phase_frames * 2)
        runtime->frame = 0;
}

void avsp_port_v2_enemy_view(const AvspPortV2EnemyRuntime *runtime,
                             AvspPortV2EnemyView *view)
{
    if (runtime == 0 || view == 0) return;
    view->class_id = avsp_port_v2_enemy_approved_config.class_id;
    view->palette_bank = avsp_port_v2_enemy_approved_config.palette_bank;
    view->world_x = runtime->x;
    view->lane = runtime->lane;
    view->facing = runtime->facing;
    view->locomotion_frame = runtime->locomotion_frame;
    view->phase = runtime->phase;
}
