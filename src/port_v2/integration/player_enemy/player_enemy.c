#include "player_enemy.h"
#include "../../player/player.h"
#include "../../enemy/enemy.h"
int avsp_port_v2_player_enemy_load(const int cart, const AvspPortV2PlayerEnemyLoadOps *ops)
{
    if (!cart || ops == 0 || ops->load_tile_archive == 0 || ops->load_background == 0 || ops->load_player_idle == 0 || ops->load_player_actions == 0 || ops->create_player_sprites == 0) return 0;
    return ops->load_tile_archive() && ops->load_background() && ops->load_player_idle() && ops->load_player_actions() && ops->create_player_sprites();
}
int avsp_port_v2_player_enemy_approvals_valid(void)
{
    return avsp_port_v2_player_validate_config(&avsp_port_v2_player_approved_config) && avsp_port_v2_enemy_validate_config(&avsp_port_v2_enemy_approved_config);
}
