#ifndef AVSP_PORT_V2_ENEMY_H
#define AVSP_PORT_V2_ENEMY_H

#define AVSP_PORT_V2_ENEMY_INTERFACE_VERSION 1
#define AVSP_PORT_V2_ENEMY_CLASS_ID 31
#define AVSP_PORT_V2_ENEMY_PALETTE_BANK 17
#define AVSP_PORT_V2_ENEMY_WALK_FRAMES 39
#define AVSP_PORT_V2_ENEMY_WALK_POSES 19

typedef struct
{
    int class_id;
    int palette_bank;
    int stationary_x;
    int translated_x;
    int lane;
    int facing;
    int phase_frames;
    int walk_frames;
    int walk_poses;
} AvspPortV2EnemyConfig;

typedef struct
{
    int translated;
} AvspPortV2EnemyInput;

typedef struct
{
    int frame;
    int x;
    int lane;
    int facing;
    int locomotion_frame;
    int phase;
} AvspPortV2EnemyRuntime;

typedef struct
{
    int class_id;
    int palette_bank;
    int world_x;
    int lane;
    int facing;
    int locomotion_frame;
    int phase;
} AvspPortV2EnemyView;

typedef int (*AvspPortV2EnemyLoadStep)(void);

typedef struct
{
    AvspPortV2EnemyLoadStep load_tile_archive;
    AvspPortV2EnemyLoadStep load_background;
} AvspPortV2EnemyLoadOps;

extern const AvspPortV2EnemyConfig avsp_port_v2_enemy_approved_config;

int avsp_port_v2_enemy_validate_config(const AvspPortV2EnemyConfig *config);
int avsp_port_v2_enemy_load(int cartridge_available,
                            const AvspPortV2EnemyLoadOps *operations);
void avsp_port_v2_enemy_init(AvspPortV2EnemyRuntime *runtime);
void avsp_port_v2_enemy_step(AvspPortV2EnemyRuntime *runtime,
                             const AvspPortV2EnemyInput *input);
void avsp_port_v2_enemy_view(const AvspPortV2EnemyRuntime *runtime,
                             AvspPortV2EnemyView *view);

#endif
