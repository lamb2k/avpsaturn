#ifndef AVSP_PORT_V2_PLAYER_ENEMY_H
#define AVSP_PORT_V2_PLAYER_ENEMY_H

#include "../../player/player.h"
#include "../../enemy/enemy.h"

#define AVSP_PORT_V2_PLAYER_ENEMY_INTERFACE_VERSION 1

#define AVSP_PORT_V2_PLAYER_ENEMY_ACTOR_COUNT 2
#define AVSP_PORT_V2_PLAYER_ENEMY_RENDER_PLAYER 1
#define AVSP_PORT_V2_PLAYER_ENEMY_RENDER_ENEMY 2
#define AVSP_PORT_V2_PLAYER_ENEMY_ENEMY_RENDER_TILES 32

typedef int (*AvspPortV2PlayerEnemyLoadStep)(void);

typedef struct
{
    AvspPortV2PlayerEnemyLoadStep load_tile_archive;
    AvspPortV2PlayerEnemyLoadStep load_background;
    AvspPortV2PlayerEnemyLoadStep load_player_idle;
    AvspPortV2PlayerEnemyLoadStep load_player_actions;
    AvspPortV2PlayerEnemyLoadStep create_player_sprites;
} AvspPortV2PlayerEnemyLoadOps;

typedef struct
{
    AvspPortV2PlayerInput player;
    int enemy_translated;
} AvspPortV2PlayerEnemyInput;

typedef struct
{
    AvspPortV2PlayerRuntime player;
    AvspPortV2EnemyRuntime enemy;
} AvspPortV2PlayerEnemyRuntime;

typedef struct
{
    AvspPortV2PlayerView player;
    AvspPortV2EnemyView enemy;
    int actor_count;
    int render_order[AVSP_PORT_V2_PLAYER_ENEMY_ACTOR_COUNT];
    int render_command_count;
} AvspPortV2PlayerEnemyView;

int avsp_port_v2_player_enemy_load(int cartridge_available, const AvspPortV2PlayerEnemyLoadOps *operations);
int avsp_port_v2_player_enemy_approvals_valid(void);
int avsp_port_v2_player_enemy_render_order_valid(const int *render_order,
                                                  int actor_count);
void avsp_port_v2_player_enemy_init(AvspPortV2PlayerEnemyRuntime *runtime);
void avsp_port_v2_player_enemy_step(AvspPortV2PlayerEnemyRuntime *runtime,
                                    const AvspPortV2PlayerEnemyInput *input);
void avsp_port_v2_player_enemy_view(
    const AvspPortV2PlayerEnemyRuntime *runtime,
    AvspPortV2PlayerEnemyView *view);

#endif
