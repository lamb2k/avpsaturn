#include <jo/jo.h>
#include <string.h>
#include "capability_model.h"
#include "generated/avsp_boss_animation.h"
#include "generated/avsp_audio.h"
#include "generated/avsp_enemy_animation.h"
#include "generated/avsp_frontend_palette.h"
#include "generated/avsp_hud.h"
#include "generated/avsp_melee_audio.h"
#include "generated/avsp_palette.h"
#include "generated/avsp_player_action_animation.h"
#include "generated/avsp_sequence_palette.h"

#define CEL_WIDTH 192
#define CEL_HEIGHT 192
#define CEL_BYTES ((CEL_WIDTH * CEL_HEIGHT) / 2)
#define BACKGROUND_WIDTH CAP_BACKGROUND_WIDTH
#define BACKGROUND_HEIGHT 256
#define SNAPSHOT_FIT_WIDTH CAP_VIEW_WIDTH
#define SNAPSHOT_HEIGHT 224
#define SNAPSHOT_FIT_BYTES (SNAPSHOT_FIT_WIDTH * SNAPSHOT_HEIGHT)
#define AVSP_CART_DRAM1_BASE ((unsigned char *)0x22600000)
#define AVSP_CART_DRAM1_BYTES 0x200000
#define BOSS_CEL_BYTES ((AVSP_BOSS_CEL_WIDTH * AVSP_BOSS_CEL_HEIGHT) / 2)
#define BITMAP_SCENE_NONE (-1000)
#define BITMAP_SCENE_CORRIDOR (-2)
#define BITMAP_SCENE_BOSS (-3)
#define BITMAP_SCENE_FRONTEND_BASE 100
#define BITMAP_SCENE_ROUTE_BASE 200
#define AVSP_VDP1_TEXTURE_BUDGET 458488
#define AVSP_VDP1_TEXTURE_BYTES \
    (2 * CEL_BYTES + \
     AVSP_PLAYER_ACTION_LAYERS * AVSP_PLAYER_ACTION_DECODED_BYTES + \
     CAP_MAX_ENEMIES * AVSP_ENEMY_DECODED_BYTES + BOSS_CEL_BYTES + \
     AVSP_HUD_TEXTURE_BYTES)

#if JO_TV_WIDTH != CAP_VIEW_WIDTH || JO_TV_HEIGHT != 224
#error "The AvP fidelity build requires Saturn TV_352x224"
#endif
#if AVSP_VDP1_TEXTURE_BYTES > AVSP_VDP1_TEXTURE_BUDGET
#error "The AvP actor working set exceeds Saturn VDP1 texture VRAM"
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
static jo_palette boss_background_palette;
static jo_palette actor_palette;
static jo_palette hud_palette;
static jo_palette frontend_palettes[AVSP_FRONTEND_SCENES];
static jo_img_8bits background_image;
static jo_img_8bits boss_background_image;
static jo_img_8bits frontend_images[AVSP_FRONTEND_SCENES];
static unsigned char *sequence_rle[AVSP_SEQUENCE_SCENES];
static unsigned char *sequence_pixels;
static unsigned char *background_bitmap;
static unsigned char *player_action_archive;
static unsigned char *enemy_action_archive;
static jo_img_4bits player_action_images[AVSP_PLAYER_ACTION_LAYERS];
static jo_img_4bits enemy_action_images[CAP_MAX_ENEMIES];
static jo_img_4bits boss_idle_images[AVSP_BOSS_IDLE_LAYERS];
static jo_img_8bits hud_top_image;
static jo_img_8bits hud_prompt_image;
static jo_img_8bits hud_heat_image;
static jo_sound weapon_sound;
static jo_sound melee_sound;
static int player_idle_sprites[2];
static int player_action_sprites[AVSP_PLAYER_ACTION_LAYERS];
static int enemy_action_sprites[CAP_MAX_ENEMIES];
static int boss_idle_sprites[AVSP_BOSS_IDLE_LAYERS];
static int hud_top_sprite;
static int hud_prompt_sprite;
static int hud_heat_sprite;
static int displayed_hud_health;
static int displayed_hud_energy;
static int current_player_action_pose;
static int current_enemy_action_poses[CAP_MAX_ENEMIES];
static int debug_hud_enabled;
static const char *failed_asset;
static int runtime_ready;
static int cart_available;
static int stage_music_started;
static int weapon_audio_played_shots;
static int weapon_audio_pending_shot;
static int weapon_audio_channel_observed;
static int melee_audio_pending;
static int melee_audio_play_count;
static int melee_audio_channel_observed;
static int current_bitmap_scene;
#ifdef AVSP_VISUAL_TEST
static int visual_action_index;
static int visual_walk_frames;
static int visual_enemy_action_index;
static int visual_enemy_frame;
#endif

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

static int load_pcm_audio(jo_sound *sound, const char *filename,
                          const char *directory, const int expected_bytes,
                          const int sample_rate)
{
    int length = 0;
    sound->data = jo_fs_read_file_in_dir(filename, directory, &length);
    if (sound->data == JO_NULL || length != expected_bytes)
    {
        failed_asset = filename;
        return 0;
    }
    sound->data_length = length;
    sound->mode = JoSoundStereo16Bit;
    sound->current_playing_channel = 0;
    sound->sample_rate = sample_rate;
    sound->volume = JO_MAX_AUDIO_VOLUME;
    sound->pan = 0;
    return 1;
}

static int load_action_audio(void)
{
    return load_pcm_audio(&weapon_sound, AVSP_GUN_PCM_FILE,
                          AVSP_GUN_PCM_DIRECTORY, AVSP_GUN_PCM_BYTES,
                          AVSP_GUN_PCM_SAMPLE_RATE) &&
           load_pcm_audio(&melee_sound, AVSP_MELEE_PCM_FILE,
                          AVSP_MELEE_PCM_DIRECTORY, AVSP_MELEE_PCM_BYTES,
                          AVSP_MELEE_PCM_SAMPLE_RATE);
}

static int load_player_action_sequences(void)
{
    int layer;
    int length = 0;
    player_action_archive = (unsigned char *)jo_fs_read_file_in_dir(
        AVSP_PLAYER_ACTION_ARCHIVE_FILE, "SPR4", &length);
    if (player_action_archive == JO_NULL ||
        length != AVSP_PLAYER_ACTION_ARCHIVE_BYTES)
    {
        failed_asset = AVSP_PLAYER_ACTION_ARCHIVE_FILE;
        return 0;
    }
    for (layer = 0; layer < AVSP_PLAYER_ACTION_LAYERS; ++layer)
    {
        player_action_images[layer].width = CEL_WIDTH;
        player_action_images[layer].height = CEL_HEIGHT;
        player_action_images[layer].data =
            (unsigned char *)jo_malloc(AVSP_PLAYER_ACTION_DECODED_BYTES);
        if (player_action_images[layer].data == JO_NULL)
        {
            failed_asset = "PLAYER ACTION BUFFER";
            return 0;
        }
    }
    return 1;
}

static int decode_player_action_pose(const int pose)
{
    int layer;
    for (layer = 0; layer < AVSP_PLAYER_ACTION_LAYERS; ++layer)
    {
        unsigned int source = 0;
        unsigned int target = 0;
        const unsigned int source_offset =
            avsp_player_action_rle_offsets[pose][layer];
        const unsigned int source_length =
            avsp_player_action_rle_bytes[pose][layer];
        const unsigned char *source_data;
        unsigned char *output = player_action_images[layer].data;
        if (source_offset + source_length > AVSP_PLAYER_ACTION_ARCHIVE_BYTES)
        {
            failed_asset = "PLAYER ACTION INDEX";
            return 0;
        }
        source_data = player_action_archive + source_offset;
        while (source + 1 < source_length)
        {
            unsigned int count = source_data[source++];
            unsigned char value = source_data[source++];
            if (count == 0 || target + count > AVSP_PLAYER_ACTION_DECODED_BYTES)
            {
                failed_asset = "PLAYER ACTION RLE";
                return 0;
            }
            memset(output + target, value, count);
            target += count;
        }
        if (source != source_length ||
            target != AVSP_PLAYER_ACTION_DECODED_BYTES)
        {
            failed_asset = "PLAYER ACTION SIZE";
            return 0;
        }
    }
    return 1;
}

static int load_enemy_action_sequences(void)
{
    int slot;
    int length = 0;
    enemy_action_archive = (unsigned char *)jo_fs_read_file_in_dir(
        AVSP_ENEMY_ARCHIVE_FILE, "SPR4", &length);
    if (enemy_action_archive == JO_NULL ||
        length != AVSP_ENEMY_ARCHIVE_BYTES)
    {
        failed_asset = AVSP_ENEMY_ARCHIVE_FILE;
        return 0;
    }
    for (slot = 0; slot < CAP_MAX_ENEMIES; ++slot)
    {
        enemy_action_images[slot].width = AVSP_ENEMY_CEL_WIDTH;
        enemy_action_images[slot].height = AVSP_ENEMY_CEL_HEIGHT;
        enemy_action_images[slot].data =
            (unsigned char *)jo_malloc(AVSP_ENEMY_DECODED_BYTES);
        if (enemy_action_images[slot].data == JO_NULL)
        {
            failed_asset = "ENEMY ACTION BUFFER";
            return 0;
        }
    }
    return 1;
}

static int decode_enemy_action_pose(const int pose, const int slot)
{
    unsigned int source = 0;
    unsigned int target = 0;
    const unsigned int source_offset = avsp_enemy_rle_offsets[pose];
    const unsigned int source_length = avsp_enemy_rle_bytes[pose];
    const unsigned char *source_data;
    unsigned char *output = enemy_action_images[slot].data;
    if (source_offset + source_length > AVSP_ENEMY_ARCHIVE_BYTES)
    {
        failed_asset = "ENEMY ACTION INDEX";
        return 0;
    }
    source_data = enemy_action_archive + source_offset;
    while (source + 1 < source_length)
    {
        unsigned int count = source_data[source++];
        unsigned char value = source_data[source++];
        if (count == 0 || target + count > AVSP_ENEMY_DECODED_BYTES)
        {
            failed_asset = "ENEMY ACTION RLE";
            return 0;
        }
        memset(output + target, value, count);
        target += count;
    }
    if (source != source_length || target != AVSP_ENEMY_DECODED_BYTES)
    {
        failed_asset = "ENEMY ACTION SIZE";
        return 0;
    }
    return 1;
}

static int load_boss_idle(void)
{
    int layer;
    int length;
    for (layer = 0; layer < AVSP_BOSS_IDLE_LAYERS; ++layer)
    {
        jo_img_4bits *image = &boss_idle_images[layer];
        image->width = AVSP_BOSS_CEL_WIDTH;
        image->height = AVSP_BOSS_CEL_HEIGHT;
        length = 0;
        image->data = (unsigned char *)jo_fs_read_file_in_dir(
            avsp_boss_idle_files[layer], "SPR4", &length);
        if (image->data == JO_NULL || length != BOSS_CEL_BYTES)
        {
            failed_asset = avsp_boss_idle_files[layer];
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

static void set_frontend_palettes(void)
{
    static jo_color colors[256];
    int scene;
    int index;

    for (scene = 0; scene < AVSP_FRONTEND_SCENES; ++scene)
    {
        for (index = 0; index < 256; ++index)
            colors[index] = JO_COLOR_RGB(
                avsp_frontend_palettes[scene][index][0],
                avsp_frontend_palettes[scene][index][1],
                avsp_frontend_palettes[scene][index][2]);
        jo_create_palette_from(&frontend_palettes[scene], colors, 256);
    }
}

static void set_hud_palette(void)
{
    static jo_color colors[256];
    int index;
    for (index = 0; index < 256; ++index)
        colors[index] = JO_COLOR_RGB(
            avsp_hud_palette[index][0], avsp_hud_palette[index][1],
            avsp_hud_palette[index][2]);
    jo_create_palette_from(&hud_palette, colors, 256);
}

static int load_hud_image(jo_img_8bits *image, const char *filename,
                          const int width, const int height)
{
    int length = 0;
    image->width = width;
    image->height = height;
    image->data = (unsigned char *)jo_fs_read_file_in_dir(
        filename, "SPR8", &length);
    if (image->data == JO_NULL || length != width * height)
    {
        failed_asset = filename;
        return 0;
    }
    return 1;
}

static int load_hud_assets(void)
{
    return load_hud_image(&hud_top_image, "HUDTOP.BIN",
                          AVSP_HUD_TOP_WIDTH, AVSP_HUD_TOP_HEIGHT) &&
           load_hud_image(&hud_prompt_image, "HUDP2.BIN",
                          AVSP_HUD_PROMPT_WIDTH, AVSP_HUD_PROMPT_HEIGHT) &&
           load_hud_image(&hud_heat_image, "HUDHEAT.BIN",
                          AVSP_HUD_HEAT_WIDTH, AVSP_HUD_HEAT_HEIGHT);
}

static int load_frontend_assets(void)
{
    int scene;
    int length;
    for (scene = 0; scene < AVSP_FRONTEND_SCENES; ++scene)
    {
        jo_img_8bits *image = &frontend_images[scene];
        image->width = SNAPSHOT_FIT_WIDTH;
        image->height = SNAPSHOT_HEIGHT;
        length = 0;
        image->data = (unsigned char *)jo_fs_read_file_in_dir(
            avsp_frontend_files[scene], "SPR8", &length);
        if (image->data == JO_NULL || length != SNAPSHOT_FIT_BYTES)
        {
            failed_asset = avsp_frontend_files[scene];
            return 0;
        }
    }
    return 1;
}

static void copy_snapshot_to_background(const unsigned char *source)
{
    static unsigned char empty_row[BACKGROUND_WIDTH];
    int y;
    for (y = 0; y < BACKGROUND_HEIGHT; ++y)
    {
        unsigned char *target = background_bitmap + y * BACKGROUND_WIDTH;
        jo_dma_copy(empty_row, target, BACKGROUND_WIDTH);
        if (y < SNAPSHOT_HEIGHT)
            jo_dma_copy((void *)(source + y * SNAPSHOT_FIT_WIDTH), target,
                        SNAPSHOT_FIT_WIDTH);
    }
}

static int activate_frontend_scene(const int scene)
{
    int bitmap_scene = BITMAP_SCENE_FRONTEND_BASE + scene;
    if (current_bitmap_scene == bitmap_scene) return 1;
    if (scene < 0 || scene >= AVSP_FRONTEND_SCENES ||
        frontend_images[scene].data == JO_NULL)
    {
        failed_asset = "FRONTEND SCENE";
        return 0;
    }
    copy_snapshot_to_background(frontend_images[scene].data);
    slBMPaletteNbg1((unsigned short)frontend_palettes[scene].id);
    jo_move_background(0, 0);
    current_bitmap_scene = bitmap_scene;
    return 1;
}

static int load_route_sequences(void)
{
    int scene;
    int length;
    sequence_pixels = (unsigned char *)jo_malloc(SNAPSHOT_FIT_BYTES);
    if (sequence_pixels == JO_NULL)
    {
        failed_asset = "SEQUENCE BUFFER";
        return 0;
    }
    for (scene = 0; scene < AVSP_SEQUENCE_SCENES; ++scene)
    {
        length = 0;
        sequence_rle[scene] = (unsigned char *)jo_fs_read_file_in_dir(
            avsp_sequence_files[scene], "SPR8", &length);
        if (sequence_rle[scene] == JO_NULL ||
            length != (int)avsp_sequence_rle_bytes[scene])
        {
            failed_asset = avsp_sequence_files[scene];
            return 0;
        }
    }
    return 1;
}

static int sequence_scene_for_world(void)
{
    if (world.encounter_state == CAP_ENCOUNTER_ROUND_TITLE)
        return AVSP_SEQUENCE_ROUND_1_TITLE;
    if (world.encounter_state == CAP_ENCOUNTER_BARRICADE_INTRO)
    {
        if (world.encounter_timer < 120) return AVSP_SEQUENCE_BARRICADE_INTRO;
        if (world.encounter_timer < 240) return AVSP_SEQUENCE_WITHDRAW_DIALOGUE;
        return AVSP_SEQUENCE_BARRICADE_BREACH;
    }
    if (world.encounter_state == CAP_ENCOUNTER_DOOR_DIALOGUE)
        return AVSP_SEQUENCE_DOOR_DIALOGUE;
    if (world.encounter_state == CAP_ENCOUNTER_INTERIOR_TRANSITION)
        return AVSP_SEQUENCE_INTERIOR_TRANSITION;
    if (world.encounter_state == CAP_ENCOUNTER_BOSS_DEFEAT)
        return AVSP_SEQUENCE_BOSS_DEATH_EXPLOSION;
    if (world.encounter_state == CAP_ENCOUNTER_STAGE_CLEAR)
        return AVSP_SEQUENCE_STAGE_CLEAR;
    if (world.encounter_state == CAP_ENCOUNTER_RESULTS)
        return world.encounter_timer < 300 ? AVSP_SEQUENCE_RESULTS_BEGIN :
                                             AVSP_SEQUENCE_RESULTS_COMPLETE;
    if (world.encounter_state == CAP_ENCOUNTER_RESULTS_EXIT)
        return AVSP_SEQUENCE_RESULTS_EXIT;
    if (world.encounter_state == CAP_ENCOUNTER_INTERMISSION)
        return AVSP_SEQUENCE_INTERMISSION;
    if (world.encounter_state == CAP_ENCOUNTER_COMPLETE)
        return AVSP_SEQUENCE_ROUND_2_BOUNDARY;
    return -1;
}

static int activate_route_sequence(const int scene)
{
    static jo_color colors[256];
    unsigned int source = 0;
    unsigned int target = 0;
    int index;

    if (scene < 0 || current_bitmap_scene == BITMAP_SCENE_ROUTE_BASE + scene)
        return 1;
    while (source + 1 < avsp_sequence_rle_bytes[scene])
    {
        unsigned int count = sequence_rle[scene][source++];
        unsigned char value = sequence_rle[scene][source++];
        if (count == 0 || target + count > SNAPSHOT_FIT_BYTES)
        {
            failed_asset = "SEQUENCE RLE";
            return 0;
        }
        memset(sequence_pixels + target, value, count);
        target += count;
    }
    if (source != avsp_sequence_rle_bytes[scene] ||
        target != SNAPSHOT_FIT_BYTES)
    {
        failed_asset = "SEQUENCE SIZE";
        return 0;
    }
    for (index = 0; index < 256; ++index)
        colors[index] = JO_COLOR_RGB(
            avsp_sequence_palettes[scene][index][0],
            avsp_sequence_palettes[scene][index][1],
            avsp_sequence_palettes[scene][index][2]);
    jo_palette_to_cram(colors, frontend_palettes[0].data, 256);
    copy_snapshot_to_background(sequence_pixels);
    slBMPaletteNbg1((unsigned short)frontend_palettes[0].id);
    jo_move_background(0, 0);
    current_bitmap_scene = BITMAP_SCENE_ROUTE_BASE + scene;
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
    /* The generated background is already horizontally fitted to Saturn's
       352-pixel field.  Keep VDP2 at 1:1 so emulator and hardware paths use
       the same deterministic coordinate mapping. */
    slZoomModeNbg1(ZOOM_1);
    slBMPaletteNbg1((unsigned short)background_palette.id);
    jo_dma_copy(background_image.data, background_bitmap, BACKGROUND_WIDTH * BACKGROUND_HEIGHT);
    current_bitmap_scene = BITMAP_SCENE_CORRIDOR;
    jo_set_displayed_screens(JO_NBG0_SCREEN | JO_NBG1_SCREEN);
    return 1;
}

static int load_boss_background(void)
{
    boss_background_image.data = JO_NULL;
    jo_create_palette(&boss_background_palette);
    if (boss_background_palette.data == JO_NULL)
    {
        failed_asset = "BOSS BG PALETTE";
        return 0;
    }
    jo_set_tga_default_palette(&boss_background_palette);
    if (jo_tga_8bits_loader(&boss_background_image, "BG", "BOSSROOM.TGA", 0) != JO_TGA_OK ||
        boss_background_image.width != BACKGROUND_WIDTH ||
        boss_background_image.height != BACKGROUND_HEIGHT)
    {
        failed_asset = "BOSSROOM.TGA";
        return 0;
    }
    return 1;
}

static void activate_gameplay_background(const int stage_area)
{
    int requested = stage_area == 1 ? BITMAP_SCENE_BOSS : BITMAP_SCENE_CORRIDOR;
    if (current_bitmap_scene == requested) return;
    if (stage_area == 1)
    {
        jo_dma_copy(boss_background_image.data, background_bitmap,
                    BACKGROUND_WIDTH * BACKGROUND_HEIGHT);
        slBMPaletteNbg1((unsigned short)boss_background_palette.id);
    }
    else
    {
        jo_dma_copy(background_image.data, background_bitmap,
                    BACKGROUND_WIDTH * BACKGROUND_HEIGHT);
        slBMPaletteNbg1((unsigned short)background_palette.id);
    }
    current_bitmap_scene = requested;
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
    int slot;
    player_idle_sprites[0] = add_sprite_for_asset(CEL_PLAYER_IDLE_0);
    player_idle_sprites[1] = add_sprite_for_asset(CEL_PLAYER_IDLE_1);
    if (!decode_player_action_pose(0)) return 0;
    for (layer = 0; layer < AVSP_PLAYER_ACTION_LAYERS; ++layer)
    {
        player_action_sprites[layer] = jo_sprite_add_4bits_image(
            &player_action_images[layer]);
        if (player_action_sprites[layer] < 0)
            failed_asset = "PLAYER ACTION VDP1";
    }
    current_player_action_pose = 0;
    for (slot = 0; slot < CAP_MAX_ENEMIES; ++slot)
    {
        if (!decode_enemy_action_pose(0, slot)) return 0;
        enemy_action_sprites[slot] = jo_sprite_add_4bits_image(
            &enemy_action_images[slot]);
        if (enemy_action_sprites[slot] < 0)
            failed_asset = "ENEMY ACTION VDP1";
        current_enemy_action_poses[slot] = 0;
    }
    for (layer = 0; layer < AVSP_BOSS_IDLE_LAYERS; ++layer)
    {
        boss_idle_sprites[layer] = jo_sprite_add_4bits_image(
            &boss_idle_images[layer]);
        if (boss_idle_sprites[layer] < 0)
            failed_asset = avsp_boss_idle_files[layer];
    }
    hud_top_sprite = jo_sprite_add_8bits_image(&hud_top_image);
    hud_prompt_sprite = jo_sprite_add_8bits_image(&hud_prompt_image);
    hud_heat_sprite = jo_sprite_add_8bits_image(&hud_heat_image);
    if (hud_top_sprite < 0 || hud_prompt_sprite < 0 || hud_heat_sprite < 0)
        failed_asset = "HUD VDP1";
    displayed_hud_health = -1;
    displayed_hud_energy = -1;
    return failed_asset == JO_NULL;
}

static int player_clip_for_action(const CapAction action)
{
    if (action == CAP_ACT_SHOOT) return AVSP_PLAYER_CLIP_GUN;
    if (action == CAP_ACT_ATTACK) return AVSP_PLAYER_CLIP_MELEE;
    if (action == CAP_ACT_JUMP) return AVSP_PLAYER_CLIP_JUMP;
    if (action == CAP_ACT_DASH) return AVSP_PLAYER_CLIP_DASH;
    if (action == CAP_ACT_SPECIAL) return AVSP_PLAYER_CLIP_SPECIAL;
    if (action == CAP_ACT_WALK) return AVSP_PLAYER_CLIP_WALK;
    if (action == CAP_ACT_HIT) return AVSP_PLAYER_CLIP_HIT;
    if (action == CAP_ACT_KO) return AVSP_PLAYER_CLIP_KO;
    return -1;
}

#ifdef AVSP_VISUAL_TEST
static CapAction visual_action_for_index(const int index)
{
    if (index == 0) return CAP_ACT_WALK;
    if (index == 1) return CAP_ACT_SHOOT;
    if (index == 2) return CAP_ACT_ATTACK;
    if (index == 3) return CAP_ACT_JUMP;
    if (index == 4) return CAP_ACT_DASH;
    if (index == 5) return CAP_ACT_SPECIAL;
    if (index == 6) return CAP_ACT_HIT;
    return CAP_ACT_KO;
}

static CapAction visual_enemy_action_for_index(const int index)
{
    if (index == 1) return CAP_ACT_ATTACK;
    if (index == 2) return CAP_ACT_HIT;
    if (index == 3) return CAP_ACT_KO;
    return CAP_ACT_WALK;
}
#endif

static int player_pose_for_frame(const int clip, const int action_frame)
{
    int step;
    int remaining = action_frame;
    for (step = 0; step < avsp_player_action_step_counts[clip]; ++step)
    {
        int duration = avsp_player_action_step_durations[clip][step];
        if (remaining < duration)
            return avsp_player_action_step_poses[clip][step];
        remaining -= duration;
    }
    return avsp_player_action_step_poses[clip]
        [avsp_player_action_step_counts[clip] - 1];
}

static int enemy_clip_for_action(const CapAction action)
{
    if (action == CAP_ACT_ATTACK) return AVSP_ENEMY_CLIP_ATTACK;
    if (action == CAP_ACT_HIT) return AVSP_ENEMY_CLIP_HIT;
    if (action == CAP_ACT_KO) return AVSP_ENEMY_CLIP_KO;
    return AVSP_ENEMY_CLIP_WALK;
}

static int enemy_pose_for_frame(const int clip, const int action_frame)
{
    int step;
    int remaining = action_frame;
    for (step = 0; step < avsp_enemy_step_counts[clip]; ++step)
    {
        int duration = avsp_enemy_step_durations[clip][step];
        if (remaining < duration)
            return avsp_enemy_step_poses[clip][step];
        remaining -= duration;
    }
    return avsp_enemy_step_poses[clip][avsp_enemy_step_counts[clip] - 1];
}

static void draw_exact_layer_offset(const CapActor *actor, const int screen_x,
                                    const int screen_offset_x,
                                    const int screen_offset_y,
                                    const int sprite_id, const int palette_bank,
                                    const int depth)
{
    /* Captured player and enemy pivots sit at pixel 184 in each 192px cel. */
    int screen_y = actor->lane - 200 - actor->height + screen_offset_y;
    jo_sprite_set_palette_4bits(actor_palette.id, palette_bank);
    if (actor->facing < 0) jo_sprite_enable_horizontal_flip();
    jo_sprite_draw3D(sprite_id, screen_x + screen_offset_x, screen_y, depth);
    if (actor->facing < 0) jo_sprite_disable_horizontal_flip();
}

static void draw_exact_layer(const CapActor *actor, const int screen_x,
                             const int sprite_id, const int palette_bank,
                             const int depth)
{
    draw_exact_layer_offset(actor, screen_x, 0, 0,
                            sprite_id, palette_bank, depth);
}

static void draw_player(const CapActor *actor, const int screen_x)
{
    int depth = 330 - actor->lane;
    int layer;
    int clip = player_clip_for_action(actor->action);
    if (clip >= 0)
    {
        int frame = actor->action == CAP_ACT_WALK ?
            (actor->locomotion_frame > 0 ? actor->locomotion_frame - 1 : 0) :
            actor->action_frame;
        int screen_offset_x;
        int screen_offset_y;
        int pose;
        if (actor->action == CAP_ACT_WALK)
            frame %= avsp_player_action_total_frames[clip];
        else if (frame >= avsp_player_action_total_frames[clip])
            frame = avsp_player_action_total_frames[clip] - 1;
        pose = player_pose_for_frame(clip, frame);
        screen_offset_x = avsp_player_action_frame_x[clip][frame] *
            CAP_VIEW_WIDTH / CAP_CPS2_VIEW_WIDTH;
        if (actor->facing < 0) screen_offset_x = -screen_offset_x;
        screen_offset_y = avsp_player_action_frame_y[clip][frame];
        if (pose != current_player_action_pose)
        {
            if (!decode_player_action_pose(pose))
            {
                runtime_ready = 0;
                return;
            }
            for (layer = 0; layer < AVSP_PLAYER_ACTION_LAYERS; ++layer)
                jo_sprite_replace_4bits_image(
                    &player_action_images[layer], player_action_sprites[layer]);
            current_player_action_pose = pose;
        }
        for (layer = 0; layer < AVSP_PLAYER_ACTION_LAYERS; ++layer)
            draw_exact_layer_offset(
                actor, screen_x, screen_offset_x, screen_offset_y,
                player_action_sprites[layer], layer, depth - layer);
    }
    else
    {
        draw_exact_layer(actor, screen_x, player_idle_sprites[0], 0, depth);
        draw_exact_layer(actor, screen_x, player_idle_sprites[1], 1, depth - 1);
    }
}

static void draw_alien(const CapActor *actor, const int screen_x,
                       const int slot)
{
    int depth = 330 - actor->lane;
    int clip = enemy_clip_for_action(actor->action);
    int frame = (actor->action == CAP_ACT_WALK ||
                 actor->action == CAP_ACT_IDLE) ?
        actor->locomotion_frame : actor->action_frame;
    int pose;
    if (clip == AVSP_ENEMY_CLIP_WALK)
        frame %= avsp_enemy_total_frames[clip];
    else if (frame >= avsp_enemy_total_frames[clip])
        frame = avsp_enemy_total_frames[clip] - 1;
    pose = enemy_pose_for_frame(clip, frame);
    if (pose != current_enemy_action_poses[slot])
    {
        if (!decode_enemy_action_pose(pose, slot))
        {
            runtime_ready = 0;
            return;
        }
        jo_sprite_replace_4bits_image(
            &enemy_action_images[slot], enemy_action_sprites[slot]);
        current_enemy_action_poses[slot] = pose;
    }
    draw_exact_layer(actor, screen_x, enemy_action_sprites[slot],
                     3 + actor->variant, depth);
}

static void draw_boss(const CapActor *actor, const int screen_x)
{
    int depth = 330 - actor->lane;
    int layer;
    for (layer = 0; layer < AVSP_BOSS_IDLE_LAYERS; ++layer)
        draw_exact_layer(actor, screen_x, boss_idle_sprites[layer],
                         avsp_boss_idle_palette_banks[layer], depth - layer);
}

static void draw_world(void)
{
    int index;
    int player_x = cap_actor_screen_x(world.player.x, world.camera_x, 1);
    int background_scroll = cap_background_fit_scroll_x(
        world.camera_x, world.stage_area);

    if (world.encounter_state == CAP_ENCOUNTER_MAIN_MENU ||
        world.encounter_state == CAP_ENCOUNTER_CHARACTER_SELECT)
    {
        int scene = world.encounter_state == CAP_ENCOUNTER_MAIN_MENU ? 0 : 1;
        if (!activate_frontend_scene(scene)) runtime_ready = 0;
        return;
    }
    if (sequence_scene_for_world() >= 0)
        return;
    activate_gameplay_background(world.stage_area);
    /* The source capture is already exactly 224 lines high.  A non-zero Y
       scroll silently discards arcade scanlines and is therefore a crop. */
    jo_move_background(background_scroll, 0);
    jo_sprite_change_sprite_scale_xy(
        (float)CAP_VIEW_WIDTH / (float)CAP_CPS2_VIEW_WIDTH, 1.0f);
    draw_player(&world.player, player_x);
    for (index = 0; index < CAP_MAX_ENEMIES; ++index)
    {
        CapActor *enemy = &world.enemies[index];
        int screen_x = cap_actor_screen_x(enemy->x, world.camera_x, 1);
        if (!enemy->active) continue;
        if (screen_x < -256 || screen_x > 256) continue;
        if (enemy->kind == CAP_ACTOR_BOSS)
            draw_boss(enemy, screen_x);
        else
            draw_alien(enemy, screen_x, index);
    }
    jo_sprite_restore_sprite_scale();
}

static void update_hud_textures(void)
{
    int x;
    int y;
    if (displayed_hud_health != world.player.health &&
        !(displayed_hud_health >= 0 &&
          (world.player.action == CAP_ACT_HIT ||
           world.player.action == CAP_ACT_KO) &&
          world.player.action_frame < 2))
    {
        int source_fill = (world.player.health * 5) / 4;
        int fill = (source_fill * CAP_VIEW_WIDTH + CAP_CPS2_VIEW_WIDTH - 1) /
                   CAP_CPS2_VIEW_WIDTH;
        if (fill > AVSP_HUD_HEALTH_WIDTH) fill = AVSP_HUD_HEALTH_WIDTH;
        for (y = 0; y < AVSP_HUD_HEALTH_HEIGHT; ++y)
            for (x = 0; x < AVSP_HUD_HEALTH_WIDTH; ++x)
                hud_top_image.data[
                    (AVSP_HUD_HEALTH_Y + y) * AVSP_HUD_TOP_WIDTH +
                    AVSP_HUD_HEALTH_X + x] =
                        x < fill ? AVSP_HUD_YELLOW_INDEX : AVSP_HUD_RED_INDEX;
        jo_sprite_replace((const jo_img *)&hud_top_image, hud_top_sprite);
        displayed_hud_health = world.player.health;
    }
    if (displayed_hud_energy != world.weapon_energy &&
        !(displayed_hud_energy >= 0 &&
          world.player.action == CAP_ACT_SHOOT &&
          world.player.action_frame < 3))
    {
        int fill = (world.weapon_energy * AVSP_HUD_HEAT_BAR_WIDTH +
                    CAP_WEAPON_MAX_ENERGY - 1) / CAP_WEAPON_MAX_ENERGY;
        for (y = 0; y < AVSP_HUD_HEAT_BAR_HEIGHT; ++y)
            for (x = 0; x < AVSP_HUD_HEAT_BAR_WIDTH; ++x)
                hud_heat_image.data[
                    (AVSP_HUD_HEAT_BAR_Y + y) * AVSP_HUD_HEAT_WIDTH +
                    AVSP_HUD_HEAT_BAR_X + x] =
                        x < fill ? AVSP_HUD_ENERGY_INDEX : AVSP_HUD_EMPTY_INDEX;
        jo_sprite_replace((const jo_img *)&hud_heat_image, hud_heat_sprite);
        displayed_hud_energy = world.weapon_energy;
    }
}

static void draw_arcade_hud(void)
{
    if (world.encounter_state == CAP_ENCOUNTER_MAIN_MENU ||
        world.encounter_state == CAP_ENCOUNTER_CHARACTER_SELECT ||
        sequence_scene_for_world() >= 0)
        return;
    update_hud_textures();
    jo_sprite_set_palette(hud_palette.id);
    jo_sprite_draw3D(hud_top_sprite,
                     -JO_TV_WIDTH_2 + AVSP_HUD_TOP_WIDTH / 2,
                     -JO_TV_HEIGHT_2 + AVSP_HUD_TOP_HEIGHT / 2, 100);
    if ((world.frame & 63) < 32)
        jo_sprite_draw3D(hud_prompt_sprite,
                         -JO_TV_WIDTH_2 + AVSP_HUD_PROMPT_X +
                             AVSP_HUD_PROMPT_WIDTH / 2,
                         -JO_TV_HEIGHT_2 + AVSP_HUD_PROMPT_HEIGHT / 2, 100);
    jo_sprite_draw3D(hud_heat_sprite,
                     -JO_TV_WIDTH_2 + AVSP_HUD_HEAT_WIDTH / 2,
                     -JO_TV_HEIGHT_2 + AVSP_HUD_HEAT_Y +
                         AVSP_HUD_HEAT_HEIGHT / 2, 100);
}

static CapInput read_input(void)
{
    CapInput input;
    input.left = jo_is_pad1_key_pressed(JO_KEY_LEFT);
    input.right = jo_is_pad1_key_pressed(JO_KEY_RIGHT);
    input.up = jo_is_pad1_key_pressed(JO_KEY_UP);
    input.down = jo_is_pad1_key_pressed(JO_KEY_DOWN);
    input.shoot_pressed = jo_is_pad1_key_down(JO_KEY_A);
    input.attack_pressed = jo_is_pad1_key_down(JO_KEY_B);
    input.jump_pressed = jo_is_pad1_key_down(JO_KEY_C);
    input.start_pressed = jo_is_pad1_key_down(JO_KEY_START);
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
    if (world.encounter_state == CAP_ENCOUNTER_MAIN_MENU)
    {
        if (world.frame >= 120) input.start_pressed = 1;
        return input;
    }
    if (world.encounter_state == CAP_ENCOUNTER_CHARACTER_SELECT)
    {
        if (world.frame >= 240) input.attack_pressed = 1;
        return input;
    }
    world.player.health = CAP_PLAYER_MAX_HEALTH;
    if (world.encounter_state == CAP_ENCOUNTER_WAVE_ONE ||
        world.encounter_state == CAP_ENCOUNTER_WAVE_TWO ||
        world.encounter_state == CAP_ENCOUNTER_BOSS)
    {
        if (world.encounter_state == CAP_ENCOUNTER_BOSS &&
            world.encounter_timer < 600)
            return input;
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
            {
                if (world.shots_fired == 0)
                    input.shoot_pressed = 1;
                else
                    input.attack_pressed = 1;
            }
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
    jo_printf(0, 4, "VIEW FULL FIT  X HUD");
    jo_printf(0, 5, "ROOM %d  LOCK %d  EXIT %d",
              world.encounter_state, world.room_locked, world.stage_transitioned);
    if (world.encounter_state == CAP_ENCOUNTER_BOSS && world.enemies[0].active)
        jo_printf(0, 6, "CHRYSALIS HP %02d/%02d", world.enemies[0].health,
                   CAP_BOSS_MAX_HEALTH);
    if (world.stage_area == 1)
        jo_printf(0, 7, "STALKER %d/%d  WAVE %d/2",
                  world.boss_adds_defeated, world.boss_adds_spawned,
                  world.boss_reinforcement_wave);
    jo_printf(0, 27, "D-PAD MOVE  A GUN  B ATTACK  C JUMP/DASH");
}

static void draw_route_overlay(void)
{
    if (world.encounter_state == CAP_ENCOUNTER_CLEAR)
        jo_printf(35, 12, "GO >>>");
}

static void frame_callback(void)
{
    CapInput input;
    CapClipRequest clip_request;
    jo_clear_screen();
    if (!runtime_ready)
    {
        jo_printf(1, 12, "CAPABILITY TEST FAILED: %s", failed_asset == JO_NULL ? "UNKNOWN" : failed_asset);
        return;
    }
#ifdef AVSP_VISUAL_TEST
    if (world.player.action == CAP_ACT_IDLE)
    {
        world.player.action = visual_action_for_index(visual_action_index);
        world.player.action_frame = 0;
        if (world.player.action == CAP_ACT_WALK)
            visual_walk_frames = AVSP_PLAYER_ACTION_MAX_FRAMES * 8;
        visual_action_index = (visual_action_index + 1) % AVSP_PLAYER_ACTION_CLIPS;
    }
#endif
    input = read_input();
#ifdef AVSP_VISUAL_TEST
    if (world.player.action == CAP_ACT_WALK && visual_walk_frames > 0)
    {
        input.right = 1;
        --visual_walk_frames;
    }
#endif
#ifdef AVSP_ENCOUNTER_TEST
    input = encounter_test_input();
#endif
    clip_request = cap_world_step(&world, &input);
    if (clip_request == CAP_CLIP_SHOOT)
        weapon_audio_pending_shot = world.shots_fired;
    if (clip_request == CAP_CLIP_ATTACK)
        melee_audio_pending = 1;
    /* The CPS2 input is injected at source frame 2525 and QSound voice 12
       becomes audible at frame 2530. Bind the processed SCSP cue to that same
       five-frame action offset, not to the controller edge. */
    if (world.player.action == CAP_ACT_SHOOT &&
        world.player.action_frame == 5 &&
        weapon_audio_played_shots < weapon_audio_pending_shot)
    {
        jo_audio_play_sound(&weapon_sound);
        weapon_audio_played_shots = weapon_audio_pending_shot;
    }
    if (weapon_audio_played_shots > 0 &&
        jo_audio_is_channel_playing(weapon_sound.current_playing_channel))
        weapon_audio_channel_observed = 1;
    /* The melee composite first differs from idle three frames after input.
       Retrigger its own prior channel so fast attacks follow the CPS2 voice
       reuse behavior instead of exhausting all six Jo PCM slots. */
    if (world.player.action == CAP_ACT_ATTACK &&
        world.player.action_frame == 3 && melee_audio_pending)
    {
        if (melee_audio_play_count > 0 &&
            jo_audio_is_channel_playing(melee_sound.current_playing_channel))
            jo_audio_stop_sound(&melee_sound);
        jo_audio_play_sound(&melee_sound);
        melee_audio_pending = 0;
        ++melee_audio_play_count;
    }
    if (melee_audio_play_count > 0 &&
        jo_audio_is_channel_playing(melee_sound.current_playing_channel))
        melee_audio_channel_observed = 1;
#ifdef AVSP_VISUAL_TEST
    if (world.player.action == CAP_ACT_WALK)
        world.player.x = JO_TV_WIDTH_2;
#endif
    if (!activate_route_sequence(sequence_scene_for_world()))
    {
        runtime_ready = 0;
        return;
    }
    if (world.encounter_started && !stage_music_started)
    {
        /* Track 2 is an ignored, locally captured QSound reference mix. The
           Saturn plays it through its CD audio path; no QSound emulator ships
           in the executable. Isolated SCSP PCM event cues are the next audio
           fidelity step. */
        jo_audio_play_cd_track(2, 2, true);
        stage_music_started = 1;
    }
#ifdef AVSP_VISUAL_TEST
    {
        int clip = visual_enemy_action_index;
        int total = avsp_enemy_total_frames[clip];
        CapActor *enemy = &world.enemies[0];
        enemy->x = world.player.x + 112;
        enemy->lane = world.player.lane;
        enemy->action = visual_enemy_action_for_index(visual_enemy_action_index);
        enemy->active = 1;
        enemy->kind = CAP_ACTOR_ALIEN;
        enemy->facing = -1;
        if (enemy->action == CAP_ACT_WALK)
            enemy->locomotion_frame = visual_enemy_frame;
        else
            enemy->action_frame = visual_enemy_frame;
        ++visual_enemy_frame;
        if (visual_enemy_frame >= total)
        {
            visual_enemy_frame = 0;
            visual_enemy_action_index =
                (visual_enemy_action_index + 1) % AVSP_ENEMY_ACTION_CLIPS;
        }
    }
#endif
    if (jo_is_pad1_key_down(JO_KEY_X)) debug_hud_enabled = !debug_hud_enabled;
    draw_world();
    draw_arcade_hud();
    draw_route_overlay();
    draw_hud();
#ifdef AVSP_ENCOUNTER_TEST
    /* Draw test evidence last so captured VDP1 actors cannot obscure it. */
    jo_printf(0, 7, "ENCOUNTER %d KO %d/%d ACTIVE %d EXIT %d LVL %d",
              world.encounter_state, world.enemies_defeated,
              CAP_STAGE1_TOTAL_ENEMIES, active_enemy_count(),
              world.stage_transitioned, world.level_completed);
    jo_printf(0, 8, "PCM SHOT %d PLAYED %d CH %d SEEN %d",
              world.shots_fired, weapon_audio_played_shots,
              jo_audio_is_channel_playing(
                  weapon_sound.current_playing_channel),
              weapon_audio_channel_observed);
    jo_printf(0, 9, "PCM MELEE %d CH %d SEEN %d",
              melee_audio_play_count,
              jo_audio_is_channel_playing(melee_sound.current_playing_channel),
              melee_audio_channel_observed);
#endif
#ifdef AVSP_VISUAL_TEST
    jo_printf(0, 5, "VISUAL A%d P%02d/%02d E%d:%03d/%02d",
              world.player.action, world.player.action_frame,
              current_player_action_pose,
              visual_enemy_action_index, visual_enemy_frame,
              current_enemy_action_poses[0]);
#endif
}

void jo_main(void)
{
    int index;
    failed_asset = JO_NULL;
    background_bitmap = JO_NULL;
    background_image.data = JO_NULL;
    boss_background_image.data = JO_NULL;
    hud_top_image.data = JO_NULL;
    hud_prompt_image.data = JO_NULL;
    hud_heat_image.data = JO_NULL;
    debug_hud_enabled = 0;
    stage_music_started = 0;
    weapon_audio_played_shots = 0;
    weapon_audio_pending_shot = 0;
    weapon_audio_channel_observed = 0;
    melee_audio_pending = 0;
    melee_audio_play_count = 0;
    melee_audio_channel_observed = 0;
    current_bitmap_scene = BITMAP_SCENE_NONE;
#ifdef AVSP_VISUAL_TEST
    visual_action_index = 0;
    visual_walk_frames = 0;
    visual_enemy_action_index = 0;
    visual_enemy_frame = 0;
    debug_hud_enabled = 1;
#endif
    sequence_pixels = JO_NULL;
    for (index = 0; index < AVSP_SEQUENCE_SCENES; ++index)
        sequence_rle[index] = JO_NULL;

    jo_core_init(JO_COLOR_Black);
    cart_available = jo_get_extended_ram_cartridge_type() == CART_32MBits;
    if (cart_available)
    {
        /* Jo Engine registers only DRAM0 for a 32 Mbit cartridge. The Sega
           expansion-RAM map provides a second 2 MiB data bank at
           0x22600000-0x227fffff. Register it before loading assets so the
           runtime can use the cartridge's complete 4 MiB capacity. */
        jo_add_memory_zone(AVSP_CART_DRAM1_BASE, AVSP_CART_DRAM1_BYTES);
    }
    set_actor_palette();
    set_frontend_palettes();
    set_hud_palette();
    if (!cart_available)
    {
        failed_asset = "4MB RAM CART REQUIRED";
        runtime_ready = 0;
    }
    else
    {
        runtime_ready = load_frontend_assets() &&
                        load_route_sequences() &&
                        load_background() && load_boss_background() &&
                        load_hud_assets() &&
                        load_action_audio() &&
                        load_all_cels() && load_player_action_sequences() &&
                        load_enemy_action_sequences() && load_boss_idle() &&
                        create_sprite_working_set();
    }
    cap_world_init(&world);
#ifdef AVSP_VISUAL_TEST
    world.encounter_started = 1;
    world.encounter_state = CAP_ENCOUNTER_WAVE_ONE;
    world.room_locked = 1;
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
