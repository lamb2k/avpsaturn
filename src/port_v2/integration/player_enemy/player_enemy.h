#ifndef AVSP_PORT_V2_PLAYER_ENEMY_H
#define AVSP_PORT_V2_PLAYER_ENEMY_H
#define AVSP_PORT_V2_PLAYER_ENEMY_INTERFACE_VERSION 1
typedef int (*AvspPortV2PlayerEnemyLoadStep)(void);
typedef struct { AvspPortV2PlayerEnemyLoadStep load_tile_archive, load_background, load_player_idle, load_player_actions, create_player_sprites; } AvspPortV2PlayerEnemyLoadOps;
int avsp_port_v2_player_enemy_load(int cartridge_available, const AvspPortV2PlayerEnemyLoadOps *operations);
int avsp_port_v2_player_enemy_approvals_valid(void);
#endif
