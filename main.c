#include <jo/jo.h>
#include <string.h>
#include "capability_model.h"

#define CEL_WIDTH 192
#define CEL_HEIGHT 192
#define CEL_BYTES ((CEL_WIDTH * CEL_HEIGHT) / 2)
#define SHADOW_WIDTH 64
#define SHADOW_HEIGHT 16
#define SHADOW_BYTES ((SHADOW_WIDTH * SHADOW_HEIGHT) / 2)
#define FX_WIDTH 64
#define FX_HEIGHT 64
#define FX_BYTES ((FX_WIDTH * FX_HEIGHT) / 2)
#define BACKGROUND_WIDTH 512
#define BACKGROUND_HEIGHT 256
#define CACHE_SLOT_COUNT 8

extern jo_color *nbg1_bitmap;

typedef enum
{
    CEL_PLAYER_IDLE = 0,
    CEL_PLAYER_WALK_1,
    CEL_PLAYER_WALK_2,
    CEL_PLAYER_ATTACK_1,
    CEL_PLAYER_ATTACK_2,
    CEL_PLAYER_SPECIAL_1,
    CEL_PLAYER_SPECIAL_2,
    CEL_PLAYER_HIT,
    CEL_CRAWLER_IDLE,
    CEL_CRAWLER_WALK_1,
    CEL_CRAWLER_WALK_2,
    CEL_CRAWLER_ATTACK_1,
    CEL_CRAWLER_ATTACK_2,
    CEL_CRAWLER_HIT,
    CEL_CRAWLER_KO,
    CEL_SHADOW,
    CEL_HIT_FLASH,
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
    {"P_IDLE.BIN", CEL_WIDTH, CEL_HEIGHT, CEL_BYTES, {0, 0, JO_NULL}},
    {"P_WLK1.BIN", CEL_WIDTH, CEL_HEIGHT, CEL_BYTES, {0, 0, JO_NULL}},
    {"P_WLK2.BIN", CEL_WIDTH, CEL_HEIGHT, CEL_BYTES, {0, 0, JO_NULL}},
    {"P_ATK1.BIN", CEL_WIDTH, CEL_HEIGHT, CEL_BYTES, {0, 0, JO_NULL}},
    {"P_ATK2.BIN", CEL_WIDTH, CEL_HEIGHT, CEL_BYTES, {0, 0, JO_NULL}},
    {"P_SPC1.BIN", CEL_WIDTH, CEL_HEIGHT, CEL_BYTES, {0, 0, JO_NULL}},
    {"P_SPC2.BIN", CEL_WIDTH, CEL_HEIGHT, CEL_BYTES, {0, 0, JO_NULL}},
    {"P_HIT.BIN", CEL_WIDTH, CEL_HEIGHT, CEL_BYTES, {0, 0, JO_NULL}},
    {"E_IDLE.BIN", CEL_WIDTH, CEL_HEIGHT, CEL_BYTES, {0, 0, JO_NULL}},
    {"E_WLK1.BIN", CEL_WIDTH, CEL_HEIGHT, CEL_BYTES, {0, 0, JO_NULL}},
    {"E_WLK2.BIN", CEL_WIDTH, CEL_HEIGHT, CEL_BYTES, {0, 0, JO_NULL}},
    {"E_ATK1.BIN", CEL_WIDTH, CEL_HEIGHT, CEL_BYTES, {0, 0, JO_NULL}},
    {"E_ATK2.BIN", CEL_WIDTH, CEL_HEIGHT, CEL_BYTES, {0, 0, JO_NULL}},
    {"E_HIT.BIN", CEL_WIDTH, CEL_HEIGHT, CEL_BYTES, {0, 0, JO_NULL}},
    {"E_KO.BIN", CEL_WIDTH, CEL_HEIGHT, CEL_BYTES, {0, 0, JO_NULL}},
    {"SHADOW.BIN", SHADOW_WIDTH, SHADOW_HEIGHT, SHADOW_BYTES, {0, 0, JO_NULL}},
    {"HITFX.BIN", FX_WIDTH, FX_HEIGHT, FX_BYTES, {0, 0, JO_NULL}}
};

static CapWorld world;
static jo_palette background_palette;
static jo_palette actor_palette;
static jo_img_8bits background_image;
static unsigned char *background_bitmap;
static int player_idle_sprite;
static int player_walk_sprites[2];
static int player_hit_sprite;
static int crawler_sprites[7];
static int shadow_sprite;
static int hit_flash_sprite;
static int cache_sprite_ids[CACHE_SLOT_COUNT];
static CapClipRequest resident_player_clip;
static unsigned int dma_bytes;
static unsigned int dma_swaps;
static int cache_stress_enabled;
static int cache_stress_cursor;
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

static void set_actor_palette(void)
{
    static jo_color colors[256];
    int index;

    for (index = 0; index < 256; ++index) colors[index] = JO_COLOR_Black;

    colors[1] = JO_COLOR_RGB(22, 30, 38);
    colors[2] = JO_COLOR_RGB(45, 66, 78);
    colors[3] = JO_COLOR_RGB(77, 103, 112);
    colors[4] = JO_COLOR_RGB(132, 157, 161);
    colors[5] = JO_COLOR_RGB(219, 224, 211);
    colors[6] = JO_COLOR_RGB(53, 84, 142);
    colors[7] = JO_COLOR_RGB(75, 132, 187);
    colors[8] = JO_COLOR_RGB(221, 125, 48);
    colors[9] = JO_COLOR_RGB(250, 190, 74);
    colors[10] = JO_COLOR_RGB(122, 64, 38);
    colors[11] = JO_COLOR_RGB(191, 117, 73);
    colors[12] = JO_COLOR_RGB(239, 185, 137);
    colors[13] = JO_COLOR_RGB(255, 237, 194);
    colors[14] = JO_COLOR_RGB(151, 35, 40);
    colors[15] = JO_COLOR_RGB(244, 76, 65);

    colors[17] = JO_COLOR_RGB(8, 14, 12);
    colors[18] = JO_COLOR_RGB(18, 31, 25);
    colors[19] = JO_COLOR_RGB(28, 50, 38);
    colors[20] = JO_COLOR_RGB(41, 72, 51);
    colors[21] = JO_COLOR_RGB(64, 103, 69);
    colors[22] = JO_COLOR_RGB(93, 137, 88);
    colors[23] = JO_COLOR_RGB(134, 174, 110);
    colors[24] = JO_COLOR_RGB(180, 211, 143);
    colors[25] = JO_COLOR_RGB(196, 220, 76);
    colors[26] = JO_COLOR_RGB(135, 154, 36);
    colors[27] = JO_COLOR_RGB(77, 91, 24);
    colors[28] = JO_COLOR_RGB(42, 48, 25);
    colors[29] = JO_COLOR_RGB(115, 48, 52);
    colors[30] = JO_COLOR_RGB(185, 65, 58);
    colors[31] = JO_COLOR_RGB(232, 132, 71);

    colors[33] = JO_COLOR_RGB(16, 18, 21);
    colors[34] = JO_COLOR_RGB(48, 50, 55);
    colors[35] = JO_COLOR_RGB(91, 94, 99);
    colors[36] = JO_COLOR_RGB(171, 177, 181);
    colors[37] = JO_COLOR_RGB(247, 245, 218);
    colors[38] = JO_COLOR_RGB(255, 213, 65);
    colors[39] = JO_COLOR_RGB(255, 145, 45);
    colors[40] = JO_COLOR_RGB(249, 71, 49);
    colors[41] = JO_COLOR_RGB(176, 34, 41);
    colors[42] = JO_COLOR_RGB(79, 31, 40);
    colors[43] = JO_COLOR_RGB(53, 103, 130);
    colors[44] = JO_COLOR_RGB(68, 164, 178);
    colors[45] = JO_COLOR_RGB(132, 220, 190);
    colors[46] = JO_COLOR_RGB(212, 255, 217);
    colors[47] = JO_COLOR_White;

    jo_create_palette_from(&actor_palette, colors, 256);
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
    int index;
    player_idle_sprite = add_sprite_for_asset(CEL_PLAYER_IDLE);
    player_walk_sprites[0] = add_sprite_for_asset(CEL_PLAYER_WALK_1);
    player_walk_sprites[1] = add_sprite_for_asset(CEL_PLAYER_WALK_2);
    player_hit_sprite = add_sprite_for_asset(CEL_PLAYER_HIT);
    crawler_sprites[0] = add_sprite_for_asset(CEL_CRAWLER_IDLE);
    crawler_sprites[1] = add_sprite_for_asset(CEL_CRAWLER_WALK_1);
    crawler_sprites[2] = add_sprite_for_asset(CEL_CRAWLER_WALK_2);
    crawler_sprites[3] = add_sprite_for_asset(CEL_CRAWLER_ATTACK_1);
    crawler_sprites[4] = add_sprite_for_asset(CEL_CRAWLER_ATTACK_2);
    crawler_sprites[5] = add_sprite_for_asset(CEL_CRAWLER_HIT);
    crawler_sprites[6] = add_sprite_for_asset(CEL_CRAWLER_KO);
    shadow_sprite = add_sprite_for_asset(CEL_SHADOW);
    hit_flash_sprite = add_sprite_for_asset(CEL_HIT_FLASH);
    for (index = 0; index < CACHE_SLOT_COUNT; ++index)
    {
        cache_sprite_ids[index] = add_sprite_for_asset(CEL_PLAYER_ATTACK_1);
        if (cache_sprite_ids[index] < 0) return 0;
    }
    resident_player_clip = CAP_CLIP_NONE;
    return failed_asset == JO_NULL;
}

static void replace_cache_slot(const int slot, const CelId cel)
{
    jo_sprite_replace_4bits_image(&cel_assets[cel].image, cache_sprite_ids[slot]);
    dma_bytes += (unsigned int)cel_assets[cel].expected_bytes;
    ++dma_swaps;
}

static void prefetch_player_clip(const CapClipRequest clip)
{
    if (clip == CAP_CLIP_NONE || clip == resident_player_clip) return;
    if (clip == CAP_CLIP_ATTACK)
    {
        replace_cache_slot(0, CEL_PLAYER_ATTACK_1);
        replace_cache_slot(1, CEL_PLAYER_ATTACK_2);
    }
    else
    {
        replace_cache_slot(0, CEL_PLAYER_SPECIAL_1);
        replace_cache_slot(1, CEL_PLAYER_SPECIAL_2);
    }
    resident_player_clip = clip;
}

static int player_sprite_id(void)
{
    const CapActor *player = &world.player;
    if (player->action == CAP_ACT_WALK)
        return player_walk_sprites[(player->locomotion_frame / 7) & 1];
    if (player->action == CAP_ACT_ATTACK || player->action == CAP_ACT_SPECIAL)
        return cache_sprite_ids[player->action_frame < 12 ? 0 : 1];
    if (player->action == CAP_ACT_HIT || player->action == CAP_ACT_KO)
        return player_hit_sprite;
    return player_idle_sprite;
}

static int crawler_sprite_id(const CapActor *enemy)
{
    if (enemy->action == CAP_ACT_WALK)
        return crawler_sprites[1 + ((enemy->locomotion_frame / 8) & 1)];
    if (enemy->action == CAP_ACT_ATTACK)
        return crawler_sprites[3 + (enemy->action_frame >= 12 ? 1 : 0)];
    if (enemy->action == CAP_ACT_HIT) return crawler_sprites[5];
    if (enemy->action == CAP_ACT_KO) return crawler_sprites[6];
    return crawler_sprites[0];
}

static void draw_shadow(const CapActor *actor, const int screen_x)
{
    jo_sprite_set_palette_4bits(actor_palette.id, 2);
    jo_sprite_change_sprite_scale_xy(actor->action == CAP_ACT_KO ? 2.2f : 1.45f, 0.72f);
    jo_sprite_draw3D(shadow_sprite, screen_x, actor->lane - 120, 350 - actor->lane);
    jo_sprite_restore_sprite_scale();
}

static void draw_actor_sprite(const CapActor *actor, const int screen_x,
                              const int sprite_id, const int subpalette)
{
    int screen_y = actor->lane - 120 - CEL_HEIGHT / 2;
    int depth = 330 - actor->lane;
    draw_shadow(actor, screen_x);
    jo_sprite_set_palette_4bits(actor_palette.id, subpalette);
    if (actor->facing < 0) jo_sprite_enable_horizontal_flip();
    jo_sprite_draw3D(sprite_id, screen_x, screen_y, depth);
    if (actor->facing < 0) jo_sprite_disable_horizontal_flip();
    if (actor->action == CAP_ACT_HIT && actor->action_frame < 6)
    {
        jo_sprite_set_palette_4bits(actor_palette.id, 2);
        jo_sprite_draw3D(hit_flash_sprite, screen_x + actor->facing * 12,
                         screen_y - 5, depth - 4);
    }
}

static void draw_world(void)
{
    int index;
    int player_x = world.player.x - world.camera_x - 160;
    int background_scroll = (world.camera_x * 192) / (CAP_WORLD_WIDTH - 320);

    jo_move_background(background_scroll, 8);
    draw_actor_sprite(&world.player, player_x, player_sprite_id(), 0);
    for (index = 0; index < CAP_MAX_ENEMIES; ++index)
    {
        CapActor *enemy = &world.enemies[index];
        int screen_x = enemy->x - world.camera_x - 160;
        if (screen_x < -256 || screen_x > 256) continue;
        draw_actor_sprite(enemy, screen_x, crawler_sprite_id(enemy), 1);
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

static void update_cache_stress(void)
{
    if (jo_is_pad1_key_down(JO_KEY_X)) cache_stress_enabled = !cache_stress_enabled;
    if (!cache_stress_enabled || (world.frame & 3) != 0) return;
    replace_cache_slot(2 + cache_stress_cursor,
                       (cache_stress_cursor & 1) ? CEL_PLAYER_ATTACK_1 : CEL_PLAYER_SPECIAL_1);
    ++cache_stress_cursor;
    if (cache_stress_cursor >= CACHE_SLOT_COUNT - 2) cache_stress_cursor = 0;
}

static void draw_hud(void)
{
    jo_printf(0, 0, "PRIVATE SATURN 4BPP CAPABILITY TEST");
    jo_printf(0, 1, "HP %02d  SCORE %05d  ENEMIES %d", world.player.health,
              world.score, CAP_MAX_ENEMIES);
    jo_printf(0, 2, "VDP1 %02d%%  CACHE %02d  CART %s   ",
              jo_sprite_usage_percent(), CACHE_SLOT_COUNT,
              cart_available ? "4MB" : "FALLBACK");
    jo_printf(0, 3, "DMA %07u B  SWAPS %05u  STRESS %s ", dma_bytes,
              dma_swaps, cache_stress_enabled ? "ON " : "OFF");
    jo_printf(0, 27, "D-PAD MOVE  A HIT  B DASH  C SPECIAL  X STRESS");
}

static void frame_callback(void)
{
    CapInput input;
    CapClipRequest request;
    if (!runtime_ready)
    {
        jo_printf(1, 12, "CAPABILITY TEST FAILED: %s", failed_asset == JO_NULL ? "UNKNOWN" : failed_asset);
        return;
    }
    input = read_input();
    request = cap_world_step(&world, &input);
    prefetch_player_clip(request);
    update_cache_stress();
    draw_world();
    draw_hud();
}

void jo_main(void)
{
    failed_asset = JO_NULL;
    background_bitmap = JO_NULL;
    background_image.data = JO_NULL;
    dma_bytes = 0;
    dma_swaps = 0;
    cache_stress_enabled = 0;
    cache_stress_cursor = 0;

    jo_core_init(JO_COLOR_Black);
    cart_available = jo_get_extended_ram_cartridge_type() == CART_32MBits;
    set_actor_palette();
    if (!cart_available)
    {
        failed_asset = "4MB RAM CART REQUIRED";
        runtime_ready = 0;
    }
    else
    {
        runtime_ready = load_background() && load_all_cels() && create_sprite_working_set();
    }
    cap_world_init(&world);
    if (runtime_ready) prefetch_player_clip(CAP_CLIP_ATTACK);
    jo_core_set_screens_order(JO_NBG0_SCREEN, JO_SPRITE_SCREEN, JO_NBG1_SCREEN);
    jo_core_add_callback(frame_callback);
    jo_core_run();
}
