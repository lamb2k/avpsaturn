#include <stdio.h>
#include <string.h>

#include "../../../../src/port_v2/integration/player_enemy/player_enemy.h"

static int load_index;
static int fail_index;

static int load_step_one(void)
{
    ++load_index;
    return load_index == 1 && fail_index != load_index;
}

static int load_step_two(void)
{
    ++load_index;
    return load_index == 2 && fail_index != load_index;
}

static int load_step_three(void)
{
    ++load_index;
    return load_index == 3 && fail_index != load_index;
}

static int load_step_four(void)
{
    ++load_index;
    return load_index == 4 && fail_index != load_index;
}

static int load_step_five(void)
{
    ++load_index;
    return load_index == 5 && fail_index != load_index;
}

static int require_true(const int condition, const char *message)
{
    if (condition) return 1;
    fprintf(stderr, "%s\n", message);
    return 0;
}

static AvspPortV2PlayerEnemyLoadOps approved_load_ops(void)
{
    AvspPortV2PlayerEnemyLoadOps operations;
    operations.load_tile_archive = load_step_one;
    operations.load_background = load_step_two;
    operations.load_player_idle = load_step_three;
    operations.load_player_actions = load_step_four;
    operations.create_player_sprites = load_step_five;
    return operations;
}

static int test_loader(void)
{
    AvspPortV2PlayerEnemyLoadOps operations = approved_load_ops();
    load_index = 0;
    fail_index = 0;
    if (!require_true(avsp_port_v2_player_enemy_load(1, &operations) &&
                      load_index == 5,
                      "approved integration loader order failed")) return 0;
    load_index = 0;
    if (!require_true(!avsp_port_v2_player_enemy_load(0, &operations) &&
                      load_index == 0,
                      "missing cartridge reached integration loader")) return 0;
    load_index = 0;
    fail_index = 3;
    if (!require_true(!avsp_port_v2_player_enemy_load(1, &operations) &&
                      load_index == 3,
                      "integration load failure did not short-circuit")) return 0;
    fail_index = 0;
    operations.load_player_actions = 0;
    return require_true(!avsp_port_v2_player_enemy_load(1, &operations),
                        "missing integration dependency was accepted");
}

static void replay(AvspPortV2PlayerEnemyRuntime *runtime)
{
    AvspPortV2PlayerEnemyInput input;
    int frame;
    memset(&input, 0, sizeof(input));
    avsp_port_v2_player_enemy_init(runtime);
    for (frame = 0; frame < 260; ++frame)
    {
        input.player.right = frame >= 4 && frame < 12;
        input.player.down = frame >= 16 && frame < 22;
        input.player.left = frame >= 24 && frame < 29;
        input.enemy_translated = (frame % 240) >= 120;
        avsp_port_v2_player_enemy_step(runtime, &input);
    }
}

static int runtime_equal(const AvspPortV2PlayerEnemyRuntime *first,
                         const AvspPortV2PlayerEnemyRuntime *second)
{
    return memcmp(first, second, sizeof(*first)) == 0;
}

static int test_deterministic_integration(void)
{
    AvspPortV2PlayerEnemyRuntime first;
    AvspPortV2PlayerEnemyRuntime second;
    AvspPortV2PlayerEnemyView view;
    replay(&first);
    replay(&second);
    if (!require_true(runtime_equal(&first, &second),
                      "deterministic integration replay drifted")) return 0;
    avsp_port_v2_player_enemy_view(&first, &view);
    if (!require_true(view.actor_count == 2 &&
                      view.player.world_x == 198 &&
                      view.player.lane == 184 &&
                      view.player.render_layers == 2 &&
                      view.enemy.class_id == 31 &&
                      view.enemy.palette_bank == 17 &&
                      view.enemy.world_x == 192 &&
                      view.enemy.locomotion_frame == 19 &&
                      view.render_command_count == 34,
                      "integrated promoted views drifted")) return 0;
    return require_true(avsp_port_v2_player_enemy_render_order_valid(
                            view.render_order, view.actor_count),
                        "approved integration render order drifted");
}

static int test_negative_control(void)
{
    AvspPortV2PlayerEnemyLoadOps operations = approved_load_ops();
    int swapped_order[2];
    swapped_order[0] = AVSP_PORT_V2_PLAYER_ENEMY_RENDER_ENEMY;
    swapped_order[1] = AVSP_PORT_V2_PLAYER_ENEMY_RENDER_PLAYER;
    if (!require_true(!avsp_port_v2_player_enemy_render_order_valid(
                          swapped_order, 2),
                      "swapped actor render order was accepted")) return 0;
    operations.load_tile_archive = load_step_two;
    operations.load_background = load_step_one;
    load_index = 0;
    fail_index = 0;
    return require_true(!avsp_port_v2_player_enemy_load(1, &operations) &&
                        load_index == 1,
                        "reordered integration dependency was accepted");
}

int main(const int argc, char **argv)
{
    const int negative = argc == 2 &&
        strcmp(argv[1], "--negative-control") == 0;
    if (!require_true(avsp_port_v2_player_enemy_approvals_valid(),
                      "approved component locks failed")) return 1;
    if (!test_loader() || !test_deterministic_integration()) return 1;
    if (negative && !test_negative_control()) return 1;
    puts(negative ? "PlayerEnemy integration negative control: PASS" :
                    "PlayerEnemy integration contract: PASS");
    return 0;
}
