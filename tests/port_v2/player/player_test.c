#include <stdio.h>
#include <string.h>

#include "../../../src/port_v2/player/player.h"

static int load_index;
static int load_failure_index;

static int load_step_one(void)
{
    ++load_index;
    return load_failure_index != load_index && load_index == 1;
}

static int load_step_two(void)
{
    ++load_index;
    return load_failure_index != load_index && load_index == 2;
}

static int load_step_three(void)
{
    ++load_index;
    return load_failure_index != load_index && load_index == 3;
}

static int load_step_four(void)
{
    ++load_index;
    return load_failure_index != load_index && load_index == 4;
}

static int require_true(const int condition, const char *message)
{
    if (condition) return 1;
    fprintf(stderr, "%s\n", message);
    return 0;
}

static int test_loader(void)
{
    AvspPortV2PlayerLoadOps operations;
    operations.load_background = load_step_one;
    operations.load_idle_cels = load_step_two;
    operations.load_action_sequences = load_step_three;
    operations.create_sprite_working_set = load_step_four;

    load_index = 0;
    load_failure_index = 0;
    if (!require_true(avsp_port_v2_player_load(1, &operations) == 1 &&
                      load_index == 4,
                      "approved loader order did not complete")) return 0;
    load_index = 0;
    if (!require_true(avsp_port_v2_player_load(0, &operations) == 0 &&
                      load_index == 0,
                      "missing cartridge reached a load callback")) return 0;
    load_index = 0;
    load_failure_index = 3;
    if (!require_true(avsp_port_v2_player_load(1, &operations) == 0 &&
                      load_index == 3,
                      "failed action archive did not short-circuit")) return 0;
    load_failure_index = 0;
    operations.load_action_sequences = 0;
    if (!require_true(avsp_port_v2_player_load(1, &operations) == 0,
                      "missing loader callback was accepted")) return 0;
    return 1;
}

static void pulse(AvspPortV2PlayerRuntime *runtime, const int direction,
                  const int frames)
{
    AvspPortV2PlayerInput input;
    int frame;
    memset(&input, 0, sizeof(input));
    for (frame = 0; frame < frames; ++frame)
    {
        input.left = direction == AVSP_PORT_V2_PLAYER_INPUT_LEFT;
        input.right = direction == AVSP_PORT_V2_PLAYER_INPUT_RIGHT;
        input.up = direction == AVSP_PORT_V2_PLAYER_INPUT_UP;
        input.down = direction == AVSP_PORT_V2_PLAYER_INPUT_DOWN;
        avsp_port_v2_player_step(runtime, &input);
    }
    memset(&input, 0, sizeof(input));
    avsp_port_v2_player_step(runtime, &input);
}

static void replay(AvspPortV2PlayerRuntime *runtime)
{
    avsp_port_v2_player_init(runtime);
    pulse(runtime, AVSP_PORT_V2_PLAYER_INPUT_RIGHT, 8);
    pulse(runtime, AVSP_PORT_V2_PLAYER_INPUT_DOWN, 6);
    pulse(runtime, AVSP_PORT_V2_PLAYER_INPUT_LEFT, 5);
    pulse(runtime, AVSP_PORT_V2_PLAYER_INPUT_UP, 3);
}

static int runtime_equal(const AvspPortV2PlayerRuntime *first,
                         const AvspPortV2PlayerRuntime *second)
{
    return first->x == second->x && first->lane == second->lane &&
           first->facing == second->facing &&
           first->action == second->action &&
           first->locomotion_frame == second->locomotion_frame &&
           first->input_mask == second->input_mask &&
           first->input_edges == second->input_edges &&
           first->previous_input_mask == second->previous_input_mask;
}

static int test_replay(void)
{
    AvspPortV2PlayerRuntime first;
    AvspPortV2PlayerRuntime second;
    AvspPortV2PlayerView view;
    replay(&first);
    replay(&second);
    if (!require_true(runtime_equal(&first, &second),
                      "deterministic player replay drifted")) return 0;
    if (!require_true(first.x == 198 && first.lane == 181 &&
                      first.facing == -1 &&
                      first.action == AVSP_PORT_V2_PLAYER_ACTION_IDLE &&
                      first.locomotion_frame == 22 &&
                      first.input_mask == 0 && first.input_edges == 0,
                      "approved replay result drifted")) return 0;
    avsp_port_v2_player_view(&first, &view);
    if (!require_true(view.world_x == 198 && view.lane == 181 &&
                      view.facing == -1 && view.render_layers == 2,
                      "approved render view drifted")) return 0;
    return 1;
}

static int test_negative_control(void)
{
    AvspPortV2PlayerConfig mutation = avsp_port_v2_player_approved_config;
    mutation.horizontal_step = 3;
    if (!require_true(!avsp_port_v2_player_validate_config(&mutation),
                      "mutated movement adapter was accepted")) return 0;
    mutation = avsp_port_v2_player_approved_config;
    mutation.idle_bottom = 232;
    if (!require_true(!avsp_port_v2_player_validate_config(&mutation),
                      "rejected cropped-pivot adapter was accepted")) return 0;
    if (!require_true(!avsp_port_v2_player_bounds_valid(56, 122, 136, 232),
                      "bottom-232 crop passed the cel bound")) return 0;
    return 1;
}

int main(const int argc, char **argv)
{
    const int negative = argc == 2 &&
        strcmp(argv[1], "--negative-control") == 0;
    if (!require_true(avsp_port_v2_player_validate_config(
            &avsp_port_v2_player_approved_config),
            "approved player config was rejected")) return 1;
    if (!require_true(avsp_port_v2_player_bounds_valid(56, 74, 136, 184),
                      "approved idle bounds were rejected")) return 1;
    if (!test_loader() || !test_replay()) return 1;
    if (negative && !test_negative_control()) return 1;
    puts(negative ? "Player port_v2 negative control: PASS" :
                    "Player port_v2 contract: PASS");
    return 0;
}
