#include <jo/jo.h>
#include <string.h>
#include "capability_model.h"
#include "generated/avsp_enemy_animation.h"
#include "generated/avsp_palette.h"
#include "generated/avsp_player_animation.h"
#include "generated/avsp_snapshot_palette.h"

#define CEL_WIDTH 192
#define CEL_HEIGHT 192
#define CEL_BYTES ((CEL_WIDTH * CEL_HEIGHT) / 2)
#define BACKGROUND_WIDTH 512
#define BACKGROUND_HEIGHT 256
#define SNAPSHOT_WIDTH 384
#define SNAPSHOT_HEIGHT 224
#define SNAPSHOT_BYTES (SNAPSHOT_WIDTH * SNAPSHOT_HEIGHT)

#if JO_TV_WIDTH != CAP_VIEW_WIDTH || JO_TV_HEIGHT != 224
#error "The AvP fidelity build requires Saturn TV_352x224"
#endif

extern jo_color *nbg1_bitmap;

typedef enum
{
    CEL_PLAYER_IDLE_0 = 0,
    CEL_PLAYER_IDLE_1,
    CEL_COUNT
} CelId;

typedef struct
{
    const char *filename;
    unsigned short width;
    unsigned short height;
    int expected_bytes;
    jo_img_4bits image;
} CelAsset;

static CelAsset cel_assets[CEL_COUNT] =
{
    {"PXI0.BIN", CEL_WIDTH, CEL_HEIGHT, CEL_BYTES, {0, 0, JO_NULL}},
    {"PXI1.BIN", CEL_WIDTH, CEL_HEIGHT, CEL_BYTES, {0, 0, JO_NULL}}
};

static CapWorld world;
static jo_palette background_palette;
static jo_palette actor_palette;
static jo_palette snapshot_palette;
static jo_img_8bits background_image;
static jo_img_8bits snapshot_image;
static unsigned char *background_bitmap;
static jo_img_4bits player_attack_images[AVSP_PLAYER_ATTACK_POSES][AVSP_PLAYER_ATTACK_LAYERS];
static jo_img_4bits enemy_walk_images[AVSP_ENEMY_WALK_POSES];
static int player_idle_sprites[2];
static int player_attack_sprites[AVSP_PLAYER_ATTACK_LAYERS];
static int enemy_walk_sprite;
static int snapshot_sprite;
static int current_player_attack_pose;
static int current_enemy_walk_pose;
static int debug_hud_enabled;
static const char *failed_asset;
static int runtime_ready;
static int cart_available;

static int load_cel_asset(CelAsset *asset)
{
    int length = 0;
    asset->image.width = asset->width;
    asset->image.height = asset->height;
    asset->image.data = (unsigned char *)jo_fs_read_file_in_dir(asset->filename, "SPR4", &length);
    if (asset->image.data == JO_NULL || length != asset->expected_bytes)
    {
        failed_asset = asset->filename;
        return 0;
    }
    return 1;
}

static int load_all_cels(void)
{
    int index;
    for (index = 0; index < CEL_COUNT; ++index)
        if (!load_cel_asset(&cel_assets[index])) return 0;
    return 1;
}

static int load_player_attack_sequence(void)
{
    int pose;
    int layer;
    int length;
    for (pose = 0; pose < AVSP_PLAYER_ATTACK_POSES; ++pose)
    {
        for (layer = 0; layer < AVSP_PLAYER_ATTACK_LAYERS; ++layer)
        {
            jo_img_4bits *image = &player_attack_images[pose][layer];
            image->width = CEL_WIDTH;
            image->height = CEL_HEIGHT;
            length = 0;
            image->data = (unsigned char *)jo_fs_read_file_in_dir(
                avsp_player_attack_files[pose][layer], "SPR4", &length);
            if (image->data == JO_NULL || length != CEL_BYTES)
            {
                failed_asset = avsp_player_attack_files[pose][layer];
                return 0;
            }
        }
    }
    return 1;
}

static int load_enemy_walk_sequence(void)
{
    int pose;
    int length;
    for (pose = 0; pose < AVSP_ENEMY_WALK_POSES; ++pose)
    {
        jo_img_4bits *image = &enemy_walk_images[pose];
        image->width = CEL_WIDTH;
        image->height = CEL_HEIGHT;
        length = 0;
        image->data = (unsigned char *)jo_fs_read_file_in_dir(
            avsp_enemy_walk_files[pose], "SPR4", &length);
        if (image->data == JO_NULL || length != CEL_BYTES)
        {
            failed_asset = avsp_enemy_walk_files[pose];
            return 0;
        }
    }
    return 1;
}

static void set_actor_palette(void)
{
    static jo_color colors[256];
    int bank;
    int index;

    for (index = 0; index < 256; ++index) colors[index] = JO_COLOR_Black;
    for (bank = 0; bank < AVSP_EXACT_PALETTE_BANKS; ++bank)
    {
        for (index = 0; index < 15; ++index)
            /* Jo's palette allocation starts at CRAM base + 1. Sprite pen 1
               therefore reads array entry 0, not array entry 1. */
            colors[bank * 16 + index] = JO_COLOR_RGB(
                avsp_exact_palettes[bank][index][0],
                avsp_exact_palettes[bank][index][1],
                avsp_exact_palettes[bank][index][2]);
    }

    jo_create_palette_from(&actor_palette, colors, 256);
}

static void set_snapshot_palette(void)
{
    static jo_color colors[256];
    int index;

    for (index = 0; index < 256; ++index)
        colors[index] = JO_COLOR_RGB(
            avsp_snapshot_palette[index][0],
            avsp_snapshot_palette[index][1],
            avsp_snapshot_palette[index][2]);
    jo_create_palette_from(&snapshot_palette, colors, 256);
}

static int load_snapshot_asset(void)
{
    int length = 0;
    snapshot_image.width = SNAPSHOT_WIDTH;
    snapshot_image.height = SNAPSHOT_HEIGHT;
    snapshot_image.data = (unsigned char *)jo_fs_read_file_in_dir(
        "OBJFRM.BIN", "SPR8", &length);
    if (snapshot_image.data == JO_NULL || length != SNAPSHOT_BYTES)
    {
        failed_asset = "OBJFRM.BIN";
        return 0;
    }
    snapshot_sprite = jo_sprite_add_8bits_image(&snapshot_image);
    if (snapshot_sprite < 0)
    {
        failed_asset = "OBJFRM VDP1";
        return 0;
    }
    return 1;
}

static int load_background(void)
{
    background_image.data = JO_NULL;
    jo_create_palette(&background_palette);
    if (background_palette.data == JO_NULL)
    {
        failed_asset = "BG PALETTE";
        return 0;
    }
    jo_set_tga_default_palette(&background_palette);
    if (jo_tga_8bits_loader(&background_image, "BG", "CORRIDOR.TGA", 0) != JO_TGA_OK ||
        background_image.width != BACKGROUND_WIDTH ||
        background_image.height != BACKGROUND_HEIGHT)
    {
        failed_asset = "CORRIDOR.TGA";
        return 0;
    }
    if (nbg1_bitmap != JO_NULL)
    {
        jo_vdp2_free(nbg1_bitmap);
        nbg1_bitmap = JO_NULL;
    }
    background_bitmap = (unsigned char *)jo_vdp2_malloc(
        JO_VDP2_RAM_BITMAP_NBG1, BACKGROUND_WIDTH * BACKGROUND_HEIGHT);
    if (background_bitmap == JO_NULL)
    {
        failed_asset = "NBG1 BITMAP";
        return 0;
    }
    slBitMapNbg1(COL_TYPE_256, BM_512x256, background_bitmap);
    slBMPaletteNbg1((unsigned short)background_palette.id);
    jo_dma_copy(background_image.data, background_bitmap, BACKGROUND_WIDTH * BACKGROUND_HEIGHT);
    jo_set_displayed_screens(JO_NBG0_SCREEN | JO_NBG1_SCREEN);
    return 1;
}

static int add_sprite_for_asset(const CelId cel)
{
    int sprite_id = jo_sprite_add_4bits_image(&cel_assets[cel].image);
    if (sprite_id < 0) failed_asset = cel_assets[cel].filename;
    return sprite_id;
}

static int create_sprite_working_set(void)
{
    int layer;
    player_idle_sprites[0] = add_sprite_for_asset(CEL_PLAYER_IDLE_0);
    player_idle_sprites[1] = add_sprite_for_asset(CEL_PLAYER_IDLE_1);
    for (layer = 0; layer < AVSP_PLAYER_ATTACK_LAYERS; ++layer)
    {
        player_attack_sprites[layer] = jo_sprite_add_4bits_image(
            &player_attack_images[0][layer]);
        if (player_attack_sprites[layer] < 0)
            failed_asset = avsp_player_attack_files[0][layer];
    }
    current_player_attack_pose = 0;
    enemy_walk_sprite = jo_sprite_add_4bits_image(&enemy_walk_images[0]);
    if (enemy_walk_sprite < 0) failed_asset = avsp_enemy_walk_files[0];
    current_enemy_walk_pose = 0;
    return failed_asset == JO_NULL;
}

static void draw_exact_layer(const CapActor *actor, const int screen_x,
                             const int sprite_id, const int palette_bank,
                             const int depth)
{
    /* Captured player and enemy pivots sit at pixel 184 in each 192px cel. */
    int screen_y = actor->lane - 200;
    jo_sprite_set_palette_4bits(actor_palette.id, palette_bank);
    if (actor->facing < 0) jo_sprite_enable_horizontal_flip();
    jo_sprite_draw3D(sprite_id, screen_x, screen_y, depth);
    if (actor->facing < 0) jo_sprite_disable_horizontal_flip();
}

static void draw_player(const CapActor *actor, const int screen_x)
{
    int depth = 330 - actor->lane;
    int layer;
    if (actor->action == CAP_ACT_ATTACK || actor->action == CAP_ACT_SPECIAL)
    {
        int pose = actor->action_frame / 4;
        if (pose >= AVSP_PLAYER_ATTACK_POSES) pose = AVSP_PLAYER_ATTACK_POSES - 1;
        if (pose != current_player_attack_pose)
        {
            for (layer = 0; layer < AVSP_PLAYER_ATTACK_LAYERS; ++layer)
                jo_sprite_replace_4bits_image(
                    &player_attack_images[pose][layer], player_attack_sprites[layer]);
            current_player_attack_pose = pose;
        }
        for (layer = 0; layer < AVSP_PLAYER_ATTACK_LAYERS; ++layer)
            draw_exact_layer(actor, screen_x, player_attack_sprites[layer],
                             layer, depth - layer);
    }
    else
    {
        draw_exact_layer(actor, screen_x, player_idle_sprites[0], 0, depth);
        draw_exact_layer(actor, screen_x, player_idle_sprites[1], 1, depth - 1);
    }
}

static void draw_alien(const CapActor *actor, const int screen_x)
{
    int depth = 330 - actor->lane;
    draw_exact_layer(actor, screen_x, enemy_walk_sprite,
                     3 + actor->variant, depth);
}

static void draw_world(void)
{
    int index;
    int player_x = world.player.x - world.camera_x - JO_TV_WIDTH_2;
    int background_scroll =
        (world.camera_x * (BACKGROUND_WIDTH - JO_TV_WIDTH)) /
        (CAP_WORLD_WIDTH - JO_TV_WIDTH);

    jo_move_background(background_scroll, 8);
    if (!world.encounter_started)
    {
        jo_sprite_set_palette(snapshot_palette.id);
        jo_sprite_draw3D(snapshot_sprite, 0, 0, 160);
        return;
    }
    draw_player(&world.player, player_x);
    {
        int pose = (world.frame / 4) % AVSP_ENEMY_WALK_POSES;
        if (pose != current_enemy_walk_pose)
        {
            jo_sprite_replace_4bits_image(
                &enemy_walk_images[pose], enemy_walk_sprite);
            current_enemy_walk_pose = pose;
        }
    }
    for (index = 0; index < CAP_MAX_ENEMIES; ++index)
    {
        CapActor *enemy = &world.enemies[index];
        int screen_x = enemy->x - world.camera_x - JO_TV_WIDTH_2;
        if (!enemy->active) continue;
        if (screen_x < -256 || screen_x > 256) continue;
        draw_alien(enemy, screen_x);
    }
}

static CapInput read_input(void)
{
    CapInput input;
    input.left = jo_is_pad1_key_pressed(JO_KEY_LEFT);
    input.right = jo_is_pad1_key_pressed(JO_KEY_RIGHT);
    input.up = jo_is_pad1_key_pressed(JO_KEY_UP);
    input.down = jo_is_pad1_key_pressed(JO_KEY_DOWN);
    input.attack_pressed = jo_is_pad1_key_down(JO_KEY_A);
    input.special_pressed = jo_is_pad1_key_down(JO_KEY_C);
    input.dash_held = jo_is_pad1_key_pressed(JO_KEY_B);
    return input;
}

#ifdef AVSP_ENCOUNTER_TEST
static int active_enemy_count(void)
{
    int count = 0;
    int index;
    for (index = 0; index < CAP_MAX_ENEMIES; ++index)
        if (world.enemies[index].active) ++count;
    return count;
}

static CapInput encounter_test_input(void)
{
    CapInput input;
    int index;
    memset(&input, 0, sizeof(input));
    if (!world.encounter_started)
    {
        input.right = 1;
        return input;
    }
    world.player.health = CAP_PLAYER_MAX_HEALTH;
    if (world.encounter_state == CAP_ENCOUNTER_WAVE_ONE ||
        world.encounter_state == CAP_ENCOUNTER_WAVE_TWO)
    {
        /* Keep the five-enemy opening wave visible long enough to inspect
           after a real BIOS/CD boot before the automated clear begins. */
        if (world.frame >= 600)
        {
            for (index = 0; index < CAP_MAX_ENEMIES; ++index)
            {
                CapActor *enemy = &world.enemies[index];
                if (!enemy->active || enemy->action == CAP_ACT_KO) continue;
                enemy->x = world.player.x + 34 + (index & 1) * 8;
                enemy->lane = world.player.lane;
                enemy->health = 1;
            }
            if (world.player.action == CAP_ACT_IDLE ||
                world.player.action == CAP_ACT_WALK)
                input.attack_pressed = 1;
        }
    }
    else if (world.encounter_state == CAP_ENCOUNTER_CLEAR)
        input.right = 1;
    return input;
}
#endif

static void draw_hud(void)
{
    if (!debug_hud_enabled) return;
    jo_printf(0, 0, "AVP CPS2 -> SATURN NATIVE SLICE");
    jo_printf(0, 1, "ROUND 1 CITY OF DESPAIR  HP %02d", world.player.health);
    jo_printf(0, 2, "SCORE %05d  KO %d/%d  CART %s",
              world.score, world.enemies_defeated, CAP_STAGE1_TOTAL_ENEMIES,
              cart_available ? "4MB" : "FAIL");
    jo_printf(0, 3, "VDP1 %02d%% EXACT CPS2 PALETTE LAYERS",
              jo_sprite_usage_percent());
    jo_printf(0, 4, "CART %s  ORIGINAL SCALE  X HIDES HUD",
              cart_available ? "4MB" : "FAIL");
    jo_printf(0, 5, "ROOM %d  LOCK %d  EXIT %d",
              world.encounter_state, world.room_locked, world.stage_transitioned);
    jo_printf(0, 27, "D-PAD MOVE  A HIT  B DASH  C SPECIAL");
}

static void frame_callback(void)
{
    CapInput input;
    if (!runtime_ready)
    {
        jo_printf(1, 12, "CAPABILITY TEST FAILED: %s", failed_asset == JO_NULL ? "UNKNOWN" : failed_asset);
        return;
    }
#ifdef AVSP_VISUAL_TEST
    if (world.player.action == CAP_ACT_IDLE)
    {
        world.player.action = CAP_ACT_ATTACK;
        world.player.action_frame = 0;
    }
#endif
    input = read_input();
#ifdef AVSP_ENCOUNTER_TEST
    input = encounter_test_input();
#endif
    cap_world_step(&world, &input);
#ifdef AVSP_VISUAL_TEST
    world.enemies[0].x = world.player.x + 112;
    world.enemies[0].lane = world.player.lane;
    world.enemies[0].action = CAP_ACT_WALK;
    world.enemies[0].active = 1;
#endif
#ifdef AVSP_ENCOUNTER_TEST
    jo_printf(0, 6, "ENCOUNTER %d KO %d/%d ACTIVE %d EXIT %d",
              world.encounter_state, world.enemies_defeated,
              CAP_STAGE1_TOTAL_ENEMIES, active_enemy_count(),
              world.stage_transitioned);
#endif
    if (jo_is_pad1_key_down(JO_KEY_X)) debug_hud_enabled = !debug_hud_enabled;
    draw_world();
    draw_hud();
#ifdef AVSP_VISUAL_TEST
    jo_printf(0, 5, "VISUAL P%02d/%02d E%02d",
              world.player.action_frame, current_player_attack_pose,
              current_enemy_walk_pose);
#endif
}

void jo_main(void)
{
    int index;
    failed_asset = JO_NULL;
    background_bitmap = JO_NULL;
    background_image.data = JO_NULL;
    snapshot_image.data = JO_NULL;
    debug_hud_enabled = 0;

    jo_core_init(JO_COLOR_Black);
    cart_available = jo_get_extended_ram_cartridge_type() == CART_32MBits;
    set_actor_palette();
    set_snapshot_palette();
    if (!cart_available)
    {
        failed_asset = "4MB RAM CART REQUIRED";
        runtime_ready = 0;
    }
    else
    {
        runtime_ready = load_background() && load_snapshot_asset() &&
                        load_all_cels() && load_player_attack_sequence() &&
                        load_enemy_walk_sequence() &&
                        create_sprite_working_set();
    }
    cap_world_init(&world);
#ifdef AVSP_VISUAL_TEST
    world.encounter_started = 1;
    world.frame = 1;
    world.player.x = JO_TV_WIDTH_2;
    world.enemies[0].x = world.player.x + 112;
    world.enemies[0].lane = world.player.lane;
    for (index = 1; index < CAP_MAX_ENEMIES; ++index)
        world.enemies[index].x = 900;
#else
    JO_UNUSED_ARG(index);
#endif
    jo_core_set_screens_order(JO_NBG0_SCREEN, JO_SPRITE_SCREEN, JO_NBG1_SCREEN);
    jo_core_add_callback(frame_callback);
    jo_core_run();
}
