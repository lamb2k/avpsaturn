#include <stdio.h>
#include <string.h>

#include "../../../src/port_v2/hud/hud.h"

static int submit_count;
static AvspPortV2HudFrame submitted;

static int capture_frame(const AvspPortV2HudFrame *frame)
{
    ++submit_count;
    submitted = *frame;
    return 1;
}

static int expect(const int condition, const char *message)
{
    if (!condition)
    {
        fprintf(stderr, "%s\n", message);
        return 0;
    }
    return 1;
}

static void set_state(AvspPortV2HudInput *input, const int health,
                      const int energy, const int visible)
{
    memset(input, 0, sizeof(*input));
    input->players[0].visible = visible;
    input->players[0].character_id =
        AVSP_PORT_V2_CHARACTER_PREDATOR_WARRIOR;
    input->players[0].health = health;
    input->players[0].energy = energy;
    input->players[1].visible = visible;
    input->players[1].character_id = AVSP_PORT_V2_CHARACTER_MAJOR_SCHAEFER;
    input->players[1].health = health;
    input->players[1].energy = energy;
}

int main(const int argc, char **argv)
{
    AvspPortV2HudInput input;
    AvspPortV2HudFrame frame;
    AvspPortV2HudFrame repeat;
    AvspPortV2HudRenderOps operations;
    AvspPortV2HudConfig rejected;
    int negative = 0;

    if (argc == 2 && strcmp(argv[1], "--broken-colors") == 0) negative = 1;
    if (argc == 2 && strcmp(argv[1], "--missing-p2") == 0) negative = 2;
    if (argc > 2 || (argc == 2 && negative == 0)) return 2;

    rejected = avsp_port_v2_hud_approved_config;
    if (negative == 1)
    {
        rejected.palette_source_offset = 0;
        return expect(!avsp_port_v2_hud_validate_config(&rejected),
                      "zero-based palette binding was accepted") ? 0 : 1;
    }
    if (negative == 2)
    {
        rejected.player_render_count[AVSP_PORT_V2_HUD_P2] = 0;
        return expect(!avsp_port_v2_hud_validate_config(&rejected),
                      "missing P2 HUD binding was accepted") ? 0 : 1;
    }

    if (!expect(avsp_port_v2_hud_validate_config(
                    &avsp_port_v2_hud_approved_config),
                "approved HUD config rejected")) return 1;
    set_state(&input, 0, 0, 1);
    if (!expect(avsp_port_v2_hud_build_frame(&input, &frame),
                "zero frame failed")) return 1;
    if (!expect(frame.render_count == 4 &&
                frame.players[0].health_fill == 0 &&
                frame.players[1].energy_fill == 0,
                "zero HUD state drifted")) return 1;

    set_state(&input, 50, 32, 1);
    if (!expect(avsp_port_v2_hud_build_frame(&input, &frame),
                "mid frame failed")) return 1;
    if (!expect(frame.render_count == 4 &&
                frame.players[0].health_fill == 57 &&
                frame.players[0].energy_fill == 30 &&
                frame.players[1].health_fill == 57 &&
                frame.players[1].energy_fill == 30,
                "mid HUD state drifted")) return 1;
    if (!expect(frame.players[0].character_id ==
                    AVSP_PORT_V2_CHARACTER_PREDATOR_WARRIOR &&
                frame.players[1].character_id ==
                    AVSP_PORT_V2_CHARACTER_MAJOR_SCHAEFER,
                "approved character bindings drifted")) return 1;

    if (!expect(avsp_port_v2_hud_build_frame(&input, &repeat) &&
                memcmp(&frame, &repeat, sizeof(frame)) == 0,
                "deterministic repeat drifted")) return 1;
    operations.submit_frame = capture_frame;
    if (!expect(avsp_port_v2_hud_submit(&frame, &operations) &&
                submit_count == 1 &&
                memcmp(&frame, &submitted, sizeof(frame)) == 0,
                "semantic render submission drifted")) return 1;

    set_state(&input, 101, 64, 1);
    if (!expect(avsp_port_v2_hud_build_frame(&input, &frame) &&
                frame.players[0].health_fill == 116 &&
                frame.players[0].energy_fill == 59,
                "full HUD state drifted")) return 1;
    set_state(&input, 50, 32, 0);
    if (!expect(avsp_port_v2_hud_build_frame(&input, &frame) &&
                frame.render_count == 0,
                "hidden HUD emitted render events")) return 1;
    puts("HUD promotion host contract: PASS");
    return 0;
}
