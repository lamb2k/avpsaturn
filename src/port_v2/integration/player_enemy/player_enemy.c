#include "player_enemy.h"

int avsp_port_v2_player_enemy_load(const int cart, const AvspPortV2PlayerEnemyLoadOps *ops)
{
    if (!cart || ops == 0 || ops->load_tile_archive == 0 ||
        ops->load_background == 0 || ops->load_player_idle == 0 ||
        ops->load_player_actions == 0 || ops->create_player_sprites == 0)
        return 0;
    return ops->load_tile_archive() && ops->load_background() &&
           ops->load_player_idle() && ops->load_player_actions() &&
           ops->create_player_sprites();
}

int avsp_port_v2_player_enemy_approvals_valid(void)
{
    return avsp_port_v2_player_validate_config(
               &avsp_port_v2_player_approved_config) &&
           avsp_port_v2_enemy_validate_config(
               &avsp_port_v2_enemy_approved_config);
}

int avsp_port_v2_player_enemy_render_order_valid(const int *render_order,
                                                  const int actor_count)
{
    return render_order != 0 &&
           actor_count == AVSP_PORT_V2_PLAYER_ENEMY_ACTOR_COUNT &&
           render_order[0] == AVSP_PORT_V2_PLAYER_ENEMY_RENDER_PLAYER &&
           render_order[1] == AVSP_PORT_V2_PLAYER_ENEMY_RENDER_ENEMY;
}

void avsp_port_v2_player_enemy_init(AvspPortV2PlayerEnemyRuntime *runtime)
{
    avsp_port_v2_player_init(&runtime->player);
    avsp_port_v2_enemy_init(&runtime->enemy);
}

void avsp_port_v2_player_enemy_step(AvspPortV2PlayerEnemyRuntime *runtime,
                                    const AvspPortV2PlayerEnemyInput *input)
{
    AvspPortV2EnemyInput enemy_input;
    avsp_port_v2_player_step(&runtime->player, &input->player);
    enemy_input.translated = input->enemy_translated;
    avsp_port_v2_enemy_step(&runtime->enemy, &enemy_input);
}

void avsp_port_v2_player_enemy_view(
    const AvspPortV2PlayerEnemyRuntime *runtime,
    AvspPortV2PlayerEnemyView *view)
{
    avsp_port_v2_player_view(&runtime->player, &view->player);
    avsp_port_v2_enemy_view(&runtime->enemy, &view->enemy);
    view->actor_count = AVSP_PORT_V2_PLAYER_ENEMY_ACTOR_COUNT;
    view->render_order[0] = AVSP_PORT_V2_PLAYER_ENEMY_RENDER_PLAYER;
    view->render_order[1] = AVSP_PORT_V2_PLAYER_ENEMY_RENDER_ENEMY;
    view->render_command_count = view->player.render_layers +
        AVSP_PORT_V2_PLAYER_ENEMY_ENEMY_RENDER_TILES;
}
