#include <jo/jo.h>
#include <string.h>

#include "core.h"

#define PROTO_BG_WIDTH 512
#define PROTO_BG_HEIGHT 256
#define PROTO_ACTOR_WIDTH 32
#define PROTO_ACTOR_HEIGHT 48

enum
{
    PROTO_INPUT_LEFT = 1,
    PROTO_INPUT_RIGHT = 2,
    PROTO_INPUT_UP = 4,
    PROTO_INPUT_DOWN = 8
};

volatile unsigned long prototype_diag_ready;
volatile unsigned long prototype_diag_frame;
volatile long prototype_diag_player_x;
volatile long prototype_diag_player_lane;
volatile unsigned long prototype_diag_inject_input;
volatile unsigned long prototype_diag_seen_input;
volatile unsigned long prototype_diag_render_heartbeat;

static PrototypeWorld world;
static jo_img_8bits background_image;
static jo_palette background_palette;
static unsigned char *background_bitmap;
static jo_img player_image;
static jo_color player_pixels[PROTO_ACTOR_WIDTH * PROTO_ACTOR_HEIGHT];
static int player_sprite;
static int runtime_ready;

static int load_stage(void)
{
    background_image.data = JO_NULL;
    jo_create_palette(&background_palette);
    if (background_palette.data == JO_NULL) return 0;
    jo_set_tga_default_palette(&background_palette);
    if (jo_tga_8bits_loader(&background_image, "BG", "CORRIDOR.TGA", 0) !=
            JO_TGA_OK ||
        background_image.width != PROTO_BG_WIDTH ||
        background_image.height != PROTO_BG_HEIGHT)
        return 0;
    background_bitmap = (unsigned char *)jo_vdp2_malloc(
        JO_VDP2_RAM_BITMAP_NBG1, PROTO_BG_WIDTH * PROTO_BG_HEIGHT);
    if (background_bitmap == JO_NULL) return 0;
    slBitMapNbg1(COL_TYPE_256, BM_512x256, background_bitmap);
    slZoomModeNbg1(ZOOM_1);
    slBMPaletteNbg1((unsigned short)background_palette.id);
    memcpy(background_bitmap, background_image.data,
           PROTO_BG_WIDTH * PROTO_BG_HEIGHT);
    jo_move_background(0, 0);
    jo_set_displayed_screens(JO_NBG0_SCREEN | JO_NBG1_SCREEN);
    return 1;
}

static void paint_player(void)
{
    int x;
    int y;
    for (y = 0; y < PROTO_ACTOR_HEIGHT; ++y)
        for (x = 0; x < PROTO_ACTOR_WIDTH; ++x)
            player_pixels[y * PROTO_ACTOR_WIDTH + x] = JO_COLOR_Transparent;
    for (y = 5; y < 16; ++y)
        for (x = 10; x < 22; ++x)
            player_pixels[y * PROTO_ACTOR_WIDTH + x] = JO_COLOR_RGB(230, 204, 146);
    for (y = 16; y < 36; ++y)
        for (x = 7; x < 25; ++x)
            player_pixels[y * PROTO_ACTOR_WIDTH + x] = JO_COLOR_RGB(52, 122, 94);
    for (y = 36; y < 47; ++y)
    {
        for (x = 8; x < 14; ++x)
            player_pixels[y * PROTO_ACTOR_WIDTH + x] = JO_COLOR_RGB(42, 55, 68);
        for (x = 18; x < 24; ++x)
            player_pixels[y * PROTO_ACTOR_WIDTH + x] = JO_COLOR_RGB(42, 55, 68);
    }
    player_image.width = PROTO_ACTOR_WIDTH;
    player_image.height = PROTO_ACTOR_HEIGHT;
    player_image.data = player_pixels;
    player_sprite = jo_sprite_add(&player_image);
}

static PrototypeInput read_input(void)
{
    PrototypeInput input;
    volatile unsigned long *uncached_inject =
        (volatile unsigned long *)
            ((unsigned long)&prototype_diag_inject_input | 0x20000000ul);
    unsigned long injected = *uncached_inject;
    prototype_diag_seen_input = injected;
    input.left = jo_is_pad1_key_pressed(JO_KEY_LEFT) ||
                 (injected & PROTO_INPUT_LEFT) != 0;
    input.right = jo_is_pad1_key_pressed(JO_KEY_RIGHT) ||
                  (injected & PROTO_INPUT_RIGHT) != 0;
    input.up = jo_is_pad1_key_pressed(JO_KEY_UP) ||
               (injected & PROTO_INPUT_UP) != 0;
    input.down = jo_is_pad1_key_pressed(JO_KEY_DOWN) ||
                 (injected & PROTO_INPUT_DOWN) != 0;
    return input;
}

static void frame_callback(void)
{
    PrototypeInput input;
    if (!runtime_ready)
    {
        jo_printf(2, 2, "PROTOTYPE V1 P0 LOAD FAILED");
        return;
    }
    input = read_input();
    prototype_v1_step(&world, &input);

    if (world.player_facing < 0) jo_sprite_enable_horizontal_flip();
    jo_sprite_draw3D(player_sprite, world.player_x, world.player_lane + 18,
                     300 - world.player_lane);
    if (world.player_facing < 0) jo_sprite_disable_horizontal_flip();

    jo_printf(1, 1, "AVP PLAYABLE SKELETON P0");
    jo_printf(1, 2, "D-PAD: MOVE + CHANGE LANE");
    jo_printf(1, 26, "X %4d  LANE %3d", world.player_x, world.player_lane);
    prototype_diag_ready = 1;
    prototype_diag_frame = world.frame;
    prototype_diag_player_x = world.player_x;
    prototype_diag_player_lane = world.player_lane;
    ++prototype_diag_render_heartbeat;
}

void jo_main(void)
{
    prototype_diag_ready = 0;
    prototype_diag_frame = 0;
    prototype_diag_inject_input = 0;
    prototype_diag_seen_input = 0;
    prototype_diag_render_heartbeat = 0;
    background_bitmap = JO_NULL;
    player_sprite = -1;
    jo_core_init(JO_COLOR_Black);
    runtime_ready = load_stage();
    if (runtime_ready)
    {
        paint_player();
        runtime_ready = player_sprite >= 0;
    }
    prototype_v1_init(&world);
    jo_core_set_screens_order(JO_NBG0_SCREEN, JO_SPRITE_SCREEN,
                              JO_NBG1_SCREEN);
    jo_core_add_callback(frame_callback);
    jo_core_run();
}
