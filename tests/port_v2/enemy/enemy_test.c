#include <stdio.h>
#include <string.h>

#include "../../../src/port_v2/enemy/enemy.h"

static int load_index;
static int fail_index;

static int load_tiles(void)
{
    ++load_index;
    return load_index == 1 && fail_index != load_index;
}

static int load_background(void)
{
    ++load_index;
    return load_index == 2 && fail_index != load_index;
}

static int require_true(const int condition, const char *message)
{
    if (condition) return 1;
    fprintf(stderr, "%s\n", message);
    return 0;
}

static int test_loader(void)
{
    AvspPortV2EnemyLoadOps operations;
    operations.load_tile_archive = load_tiles;
    operations.load_background = load_background;
    load_index = 0;
    fail_index = 0;
    if (!require_true(avsp_port_v2_enemy_load(1, &operations) &&
                      load_index == 2, "approved loader order failed")) return 0;
    load_index = 0;
    if (!require_true(!avsp_port_v2_enemy_load(0, &operations) &&
                      load_index == 0, "missing cartridge reached loader")) return 0;
    load_index = 0;
    fail_index = 1;
    if (!require_true(!avsp_port_v2_enemy_load(1, &operations) &&
                      load_index == 1, "tile failure did not short-circuit")) return 0;
    fail_index = 0;
    operations.load_background = 0;
    return require_true(!avsp_port_v2_enemy_load(1, &operations),
                        "missing loader callback was accepted");
}

static void replay(AvspPortV2EnemyRuntime *runtime)
{
    AvspPortV2EnemyInput input;
    int frame;
    avsp_port_v2_enemy_init(runtime);
    for (frame = 0; frame < 240; ++frame)
    {
        input.translated = frame >= 120;
        avsp_port_v2_enemy_step(runtime, &input);
    }
}

static int runtime_equal(const AvspPortV2EnemyRuntime *first,
                         const AvspPortV2EnemyRuntime *second)
{
    return first->frame == second->frame && first->x == second->x &&
           first->lane == second->lane && first->facing == second->facing &&
           first->locomotion_frame == second->locomotion_frame &&
           first->phase == second->phase;
}

static int test_replay(void)
{
    AvspPortV2EnemyRuntime first;
    AvspPortV2EnemyRuntime second;
    AvspPortV2EnemyInput input;
    AvspPortV2EnemyView view;
    replay(&first);
    replay(&second);
    if (!require_true(runtime_equal(&first, &second) && first.frame == 0,
                      "deterministic enemy cycle drifted")) return 0;
    input.translated = 0;
    avsp_port_v2_enemy_step(&first, &input);
    avsp_port_v2_enemy_view(&first, &view);
    return require_true(view.class_id == 31 && view.palette_bank == 17 &&
                        view.world_x == 192 && view.lane == 200 &&
                        view.facing == -1 && view.locomotion_frame == 0 &&
                        view.phase == 0, "approved enemy view drifted");
}

static int test_negative_control(void)
{
    AvspPortV2EnemyConfig mutation = avsp_port_v2_enemy_approved_config;
    mutation.walk_frames = 38;
    if (!require_true(!avsp_port_v2_enemy_validate_config(&mutation),
                      "mutated walk duration was accepted")) return 0;
    mutation = avsp_port_v2_enemy_approved_config;
    mutation.palette_bank = 16;
    if (!require_true(!avsp_port_v2_enemy_validate_config(&mutation),
                      "mutated palette adapter was accepted")) return 0;
    mutation = avsp_port_v2_enemy_approved_config;
    mutation.translated_x = 239;
    return require_true(!avsp_port_v2_enemy_validate_config(&mutation),
                        "mutated movement adapter was accepted");
}

int main(const int argc, char **argv)
{
    const int negative = argc == 2 &&
        strcmp(argv[1], "--negative-control") == 0;
    if (!require_true(avsp_port_v2_enemy_validate_config(
            &avsp_port_v2_enemy_approved_config),
            "approved enemy config was rejected")) return 1;
    if (!test_loader() || !test_replay()) return 1;
    if (negative && !test_negative_control()) return 1;
    puts(negative ? "Enemy port_v2 negative control: PASS" :
                    "Enemy port_v2 contract: PASS");
    return 0;
}
