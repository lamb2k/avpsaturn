#include <jo/jo.h>
#include <string.h>
#include "capability_model.h"
#include "avsp_tiles.h"
#include "avsp_collision.h"
#include "avsp_cram.h"
#include "avsp_frontend.h"
#include "avsp_disc_guard.h"

#include "generated/avsp_anim_records.h"
#include "generated/avsp_emit_windows.h"
#include "generated/avsp_boss_animation.h"
#include "generated/avsp_boss_clear_audio.h"
#include "generated/avsp_boss_intro_audio.h"
#include "generated/avsp_boss_rom.h"
#include "generated/avsp_breach_audio.h"
#include "generated/avsp_audio.h"
#include "generated/avsp_contact_audio.h"
#include "generated/avsp_door_dialogue_audio.h"
#include "generated/avsp_enemy_animation.h"
#include "generated/avsp_hud.h"
#include "generated/avsp_ko_contact_audio.h"
#include "generated/avsp_interior_transition_audio.h"
#include "generated/avsp_melee_audio.h"
#include "generated/avsp_palette.h"
#include "generated/avsp_player_action_animation.h"
#include "generated/avsp_round_title_a_audio.h"
#include "generated/avsp_round_title_b_audio.h"
#include "generated/avsp_sequence_palette.h"
#include "generated/avsp_stalker_animation.h"
#include "generated/avsp_withdraw_audio.h"

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
/* Body E: the ROM tile archive owns a carved region at the head of
   cartridge bank 1, mirroring the reference port's cart-resident,
   byte-stable texture source; only the remainder joins the general
   allocator, so the archive can never displace main-pool assets.
   MEASURED budget ceiling: growing this to 0xC0000 for the full
   four-route archive (612,720 bytes) left EACT.RLE (131,552 bytes)
   with no single zone holding it - cart bank0 had ~13 KB free and
   bank1 ~103 KB, neither enough alone. The street-only archive
   (202,564 bytes) is what currently fits; widening to stalkers/boss
   needs more PCM moved to phase-boundary loads first (S3 enabler,
   tracked in the handoff), not a bigger carve alone. */
/* Widened from 0x40000 for the RP4 street archive (297,764 bytes with the
 * representative-interval object tiles). Scene loading boundaries are the
 * residency lever: the carve holds one scene-scope archive at a time and is
 * reloaded during transitions, when data-track reads are legal. */
#define AVSP_TILE_REGION_BYTES 0x50000

/* RP4 street test: the interval strip bundle is staged after the tile
 * carve, outside the allocator, only in that build profile. */
#ifdef AVSP_STREET_TEST
#define AVSP_STRIPS_REGION_BYTES 0x48000
#else
#define AVSP_STRIPS_REGION_BYTES 0
#endif

#ifdef AVSP_STREET_TEST
/* MEASURED (live write watchpoint at 0x25E40000 -> prnt_0): SGL's
 * slPrint/slLocate write the ASCII text map at VDP2_VRAM_B0 (0x25E40000),
 * which the street test owns as the NBG0 pattern-name area. Every
 * jo_printf in this profile is therefore redirected into a work-RAM
 * buffer that the debug rig reads back over MCP, and frame_callback's
 * jo_clear_screen is compiled out; nothing may write the ASCII layer. */
char avsp_diag_print_buffer[128];
#undef jo_printf
#define jo_printf(X, Y, ...) sprintf(avsp_diag_print_buffer, __VA_ARGS__)
#endif
#define AVSP_PCM_CHANNEL_WEAPON 0
#define AVSP_PCM_CHANNEL_MELEE 1
#define AVSP_PCM_CHANNEL_CONTACT 2
#define AVSP_PCM_CHANNEL_SEQUENCE 3
#define AVSP_PCM_CHANNEL_TRANSITION 4
#define AVSP_PCM_CHANNEL_OPENING 5
#define BITMAP_SCENE_NONE (-1000)
#define BITMAP_SCENE_CORRIDOR (-2)
#define BITMAP_SCENE_BOSS (-3)
#define BITMAP_SCENE_FRONTEND_BASE 100
#define BITMAP_SCENE_ROUTE_BASE 200
#define AVSP_VDP1_TEXTURE_BUDGET 458488
/* S2 Body E: resident VDP1 pool of 16x16 ROM tile textures, LRU-replaced
   in place, so the per-frame cost is command-table-only (the reference
   port's measured model: per-16x16-tile normal sprites in colour-bank
   mode). */
#define AVSP_TILE_SPRITE_POOL 96
#define AVSP_VDP1_TEXTURE_BYTES \
    (2 * CEL_BYTES + \
     AVSP_PLAYER_ACTION_LAYERS * AVSP_PLAYER_ACTION_DECODED_BYTES + \
     CAP_MAX_ENEMIES * AVSP_ENEMY_DECODED_BYTES + \
     AVSP_BOSS_DECODED_BYTES + \
     AVSP_HUD_TEXTURE_BYTES + \
     AVSP_TILE_SPRITE_POOL * AVSP_TILE_BYTES + \
     AVSP_FRONTEND_VDP1_MAX_BYTES)

#if JO_TV_WIDTH != CAP_VIEW_WIDTH || JO_TV_HEIGHT != 224
#error "The AvP fidelity build requires Saturn TV_352x224"
#endif
#if AVSP_FRONTEND_START_TRANSITION_FRAMES != CAP_START_TRANSITION_FRAMES
#error "Frontend model and generated source transition schedules differ"
#endif
#if AVSP_STALKER_DECODED_BYTES != AVSP_ENEMY_DECODED_BYTES || \
    AVSP_STALKER_CEL_WIDTH != AVSP_ENEMY_CEL_WIDTH || \
    AVSP_STALKER_CEL_HEIGHT != AVSP_ENEMY_CEL_HEIGHT
#error "Stalker clips must reuse the existing alien VDP1 slot pool"
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
static AvspFrontend frontend_runtime;
static unsigned char *sequence_rle[AVSP_SEQUENCE_SCENES];
static unsigned char *sequence_pixels;
static unsigned char *background_bitmap;
static unsigned char *player_action_archive;
static unsigned char *enemy_action_archive;
static unsigned char *stalker_action_archive;
static unsigned char *enemy_action_buffer;
static jo_img_4bits player_action_images[AVSP_PLAYER_ACTION_LAYERS];
static jo_img_4bits enemy_action_images[CAP_MAX_ENEMIES];
static jo_img_4bits boss_action_image;
static jo_img_8bits hud_top_image;
static jo_img_8bits hud_prompt_image;
static jo_img_8bits hud_heat_image;
static jo_sound weapon_sound;
static jo_sound melee_sound;
static jo_sound contact_sound;
static jo_sound ko_contact_sound;
static jo_sound *contact_channel_sound;
static jo_sound boss_intro_sound;
static jo_sound boss_clear_sound;
static jo_sound *sequence_channel_sound;
static jo_sound door_dialogue_sound;
static jo_sound interior_transition_sound;
static jo_sound *transition_channel_sound;
static jo_sound round_title_a_sound;
static jo_sound round_title_b_sound;
static jo_sound withdraw_sound;
static jo_sound breach_sound;
static jo_sound *opening_channel_sound;
static int player_idle_sprites[2];
static int player_action_sprites[AVSP_PLAYER_ACTION_LAYERS];
static int enemy_action_sprites[CAP_MAX_ENEMIES];
static int boss_action_sprite;
static int hud_top_sprite;
static int hud_prompt_sprite;
static int hud_heat_sprite;
static int displayed_hud_health;
static int displayed_hud_energy;
static int current_player_action_pose;
static int current_enemy_action_poses[CAP_MAX_ENEMIES];
static CapActorKind current_enemy_action_kinds[CAP_MAX_ENEMIES];
static int current_boss_action_pose;
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
static int contact_audio_play_count;
static int ko_contact_audio_play_count;
static int contact_audio_channel_observed;
static int boss_intro_audio_play_count;
static int boss_clear_audio_play_count;
static int sequence_audio_channel_observed;
static int door_dialogue_audio_play_count;
static int interior_transition_audio_play_count;
static int transition_audio_channel_observed;
static int round_title_a_audio_play_count;
static int round_title_b_audio_play_count;
static int withdraw_audio_play_count;
static int breach_audio_play_count;
static int opening_audio_channel_observed;
static int enemy_runtime_ready;
static int boss_runtime_ready;
static int current_bitmap_scene;

/* Stable headless readback surface. These are intentionally global and
 * volatile so stock emulator debugger memory reads can verify the focused
 * frontend profile without relying on a GUI screenshot. */
volatile int avsp_diag_runtime_ready;
volatile int avsp_diag_encounter_state;
volatile int avsp_diag_world_frame;
volatile int avsp_diag_selected_character;
volatile int avsp_diag_selection_cursor;
volatile int avsp_diag_encounter_timer;
volatile int avsp_diag_background_bitmap;
volatile int avsp_diag_frontend_late_reads;
volatile int avsp_diag_frontend_missing_assets;
volatile int avsp_diag_frontend_rle_errors;
volatile int avsp_diag_frontend_palette_errors;
volatile int avsp_diag_frontend_palette_boundary_writes;
volatile int avsp_diag_frontend_commands;
#ifdef AVSP_FRONTEND_SHOT_TEST
/* Visual-verification profile. The frontend surfaces this pass must compare
 * are short-lived - the ROM's cursor intro is three source frames - so a
 * wall-clock screenshot cannot land on them. Instead the route stops the
 * world at a listed (encounter state, encounter timer) point while rendering
 * continues, so the VDP1 command table and colour RAM can be read at an
 * exact frame. Holds are visited in listed order and never re-armed. */
#define AVSP_SHOT_HOLD_TICKS 300
typedef struct
{
    int state;
    int timer;
} AvspShotHold;
static const AvspShotHold avsp_shot_holds[] = {
    { CAP_ENCOUNTER_MAIN_MENU,        60 },  /* settled title             */
    { CAP_ENCOUNTER_START_TRANSITION,  1 },  /* mask plate, first frame   */
    { CAP_ENCOUNTER_START_TRANSITION, 10 },  /* mask bars, intermediate   */
    { CAP_ENCOUNTER_START_TRANSITION, 20 },  /* mask bars, intermediate   */
    { CAP_ENCOUNTER_START_TRANSITION, 25 },  /* mask bars, last drawn     */
    { CAP_ENCOUNTER_START_TRANSITION, 27 },  /* cursor intro cel 0        */
    { CAP_ENCOUNTER_START_TRANSITION, 28 },  /* cursor intro cel 1        */
    { CAP_ENCOUNTER_START_TRANSITION, 29 },  /* cursor intro cel 2        */
    { CAP_ENCOUNTER_CHARACTER_SELECT,  1 },  /* cursor cycle phase 1      */
    { CAP_ENCOUNTER_CHARACTER_SELECT,  2 },  /* cursor cycle phase 2      */
    { CAP_ENCOUNTER_CHARACTER_SELECT,  3 },  /* cursor cycle phase 3      */
    { CAP_ENCOUNTER_CHARACTER_SELECT, 30 },  /* settled cursor 0 Warrior  */
    { CAP_ENCOUNTER_CHARACTER_SELECT, 60 },  /* settled cursor 1 Schaefer */
    { CAP_ENCOUNTER_CHARACTER_SELECT,100 },  /* settled cursor 2 Hunter   */
    { CAP_ENCOUNTER_CHARACTER_SELECT,140 },  /* settled cursor 3 Linn     */
    { CAP_ENCOUNTER_CHARACTER_CONFIRM, 1 },  /* marker blink visible      */
    { CAP_ENCOUNTER_CHARACTER_CONFIRM,10 },  /* marker blink visible      */
    { CAP_ENCOUNTER_CHARACTER_CONFIRM,20 },  /* marker blink blank        */
    { CAP_ENCOUNTER_CHARACTER_CONFIRM,40 },  /* markers retired           */
    { CAP_ENCOUNTER_CHARACTER_CONFIRM,90 },  /* shutter moving            */
    { CAP_ENCOUNTER_CHARACTER_CONFIRM,100 }, /* shutter moving            */
    { CAP_ENCOUNTER_CHARACTER_CONFIRM,110 }, /* shutter closed            */
    { CAP_ENCOUNTER_ROUND_TITLE,      20 },  /* title text over black     */
    { CAP_ENCOUNTER_ROUND_TITLE,      60 },  /* title text over street    */
    { CAP_ENCOUNTER_ROUND_TITLE,     100 }   /* street after text clear   */
};
#define AVSP_SHOT_HOLD_COUNT ((int)(sizeof(avsp_shot_holds) / sizeof(avsp_shot_holds[0])))
static int avsp_shot_hold_index;
static int avsp_shot_hold_ticks;
/* cap_update_encounter() does not advance encounter_timer in every state,
 * so the shot route counts frames spent in the current state itself. The
 * counter only advances on frames the world actually stepped, which is what
 * makes a hold frame-exact. */
static int avsp_shot_state = -1;
static int avsp_shot_state_frames;
volatile int avsp_diag_hold_index = -1;
volatile int avsp_diag_hold_active;
volatile int avsp_diag_hold_timer = -1;
static int avsp_shot_should_hold(void)
{
    if (avsp_shot_hold_index >= AVSP_SHOT_HOLD_COUNT) return 0;
    if ((int)world.encounter_state !=
            avsp_shot_holds[avsp_shot_hold_index].state ||
        avsp_shot_state_frames !=
            avsp_shot_holds[avsp_shot_hold_index].timer)
        return 0;
    avsp_diag_hold_index = avsp_shot_hold_index;
    avsp_diag_hold_timer = avsp_shot_state_frames;
    avsp_diag_hold_active = 1;
    if (++avsp_shot_hold_ticks < AVSP_SHOT_HOLD_TICKS) return 1;
    avsp_shot_hold_ticks = 0;
    avsp_diag_hold_active = 0;
    ++avsp_shot_hold_index;
    return 0;
}
#endif

#ifdef AVSP_VISUAL_TEST
static int visual_action_index;
static int visual_walk_frames;
static int visual_enemy_action_index;
static int visual_enemy_frame;
#endif

/* Cartridge-safe file read. jo_fs_read_file_in_dir's whole-file GFS_Load
 * path cannot fill a buffer the allocator places in cartridge DRAM (SBL's
 * default transfer is SCU DMA, and SCU DMA cannot write the A-bus), and
 * with the 4 MB cartridge carrying most of the working set almost every
 * large allocation lands there. Following the proven period pattern
 * (BrooklynBangout2D's asset staging), every read streams through a fixed
 * work-RAM staging buffer in 32-sector bursts and is copied out with the
 * CPU, which every destination accepts. jo_fs_read_next_bytes is NOT used:
 * it refills with a single-sector GFS_Fread regardless of the configured
 * buffer size, so enlarging jo's stream buffer serves garbage.
 * All disc reads in this file go through here. */
/* 31 sectors, not 32: the encounter profile's BSS crossed the
 * 0x060C0000 user work-RAM limit by 0x5a0 bytes after the RP3 carve
 * rework, and one sector off this burst buffer reclaims 2 KiB without
 * changing behavior (the read loop accepts any burst size). */
#define AVSP_FS_STAGING_SECTORS 31
#define AVSP_FS_SECTOR_BYTES 2048
#define AVSP_FS_STAGING_BYTES (AVSP_FS_STAGING_SECTORS * AVSP_FS_SECTOR_BYTES)
static unsigned char avsp_fs_staging[AVSP_FS_STAGING_BYTES];
/* Boot-bringup diagnostic: which stage of the cartridge-safe reader
 * failed last. Volatile so the release optimizer keeps these
 * debugger-read fields. */
/* RP5: every data-track read asks this guard first; CDDA ownership and
 * measured phase-boundary windows are the only inputs. Non-static so the
 * debug rig reads the counters by symbol. */
AvspDiscGuard avsp_disc_guard_state;
static const char *volatile avsp_fs_last_error;
static volatile int avsp_fs_last_read;
volatile const char *avsp_diag_fs_name;
volatile const char *avsp_diag_fs_dir;
volatile int avsp_diag_fs_expected;
volatile int avsp_diag_fs_offset;
volatile int avsp_diag_fs_reads;

/* Stream one file into dest (any bus). Returns bytes read, or -1. */
static int avsp_fs_read_into(const char *const filename,
                             const char *const sub_dir,
                             unsigned char *dest, const int max_bytes)
{
    Sint32 fid;
    GfsHn gfs;
    Sint32 sctsize;
    Sint32 nsct;
    Sint32 lastsize;
    int fsize;
    int offset = 0;

    if (!avsp_disc_guard_check(&avsp_disc_guard_state))
    {
        /* CDDA owns the drive and no measured window is open: reject the
           read loudly instead of seeking the data track mid-music. */
        avsp_fs_last_error = "FS CDDA LOCK";
        return -1;
    }
    avsp_diag_fs_name = filename;
    avsp_diag_fs_dir = sub_dir;
    avsp_diag_fs_expected = 0;
    avsp_diag_fs_offset = 0;
    jo_fs_cd(sub_dir);
    fid = GFS_NameToId((Sint8 *)filename);
    if (fid < 0)
    {
        jo_fs_cd(JO_PARENT_DIR);
        avsp_fs_last_error = "FS NAME";
        return -1;
    }
    gfs = GFS_Open(fid);
    if (gfs == JO_NULL)
    {
        jo_fs_cd(JO_PARENT_DIR);
        avsp_fs_last_error = "FS OPEN";
        return -1;
    }
    GFS_GetFileSize(gfs, &sctsize, &nsct, &lastsize);
    fsize = sctsize * (nsct - 1) + lastsize;
    avsp_diag_fs_expected = fsize;
    if (fsize <= 0 || fsize > max_bytes)
    {
        GFS_Close(gfs);
        jo_fs_cd(JO_PARENT_DIR);
        avsp_fs_last_error = "FS SIZE";
        avsp_fs_last_read = fsize;
        return -1;
    }
    while (offset < fsize)
    {
        int chunk;
        avsp_diag_fs_offset = offset;
        ++avsp_diag_fs_reads;
        Sint32 got = GFS_Fread(gfs, AVSP_FS_STAGING_SECTORS,
                               avsp_fs_staging, AVSP_FS_STAGING_BYTES);
        if (got <= 0)
        {
            GFS_Close(gfs);
            jo_fs_cd(JO_PARENT_DIR);
            avsp_fs_last_error = "FS READ";
            avsp_fs_last_read = offset;
            return -1;
        }
        chunk = (int)got;
        /* The final burst is sector-padded past the true file size. */
        if (offset + chunk > fsize) chunk = fsize - offset;
        memcpy(dest + offset, avsp_fs_staging, (unsigned int)chunk);
        offset += chunk;
    }
    GFS_Close(gfs);
    jo_fs_cd(JO_PARENT_DIR);
    return fsize;
}

static char *avsp_fs_read_file_in_dir(const char *const filename,
                                      const char *const sub_dir, int *len)
{
    jo_file probe;
    int opened;
    int read_bytes;
    char *dest;

    /* Size the allocation with a jo probe, then stream for real. */
    jo_fs_cd(sub_dir);
    opened = jo_fs_open(&probe, filename);
    if (opened) jo_fs_close(&probe);
    jo_fs_cd(JO_PARENT_DIR);
    if (!opened || probe.size <= 0)
    {
        avsp_fs_last_error = "FS PROBE";
        return JO_NULL;
    }
    dest = (char *)jo_malloc_with_behaviour((unsigned int)probe.size,
                                            JO_MALLOC_TRY_REUSE_BLOCK);
    if (dest == JO_NULL)
    {
        avsp_fs_last_error = "FS ALLOC";
        return JO_NULL;
    }
    read_bytes = avsp_fs_read_into(filename, sub_dir,
                                   (unsigned char *)dest, probe.size);
    if (read_bytes != probe.size)
    {
        jo_free(dest);
        return JO_NULL;
    }
    if (len != JO_NULL) *len = read_bytes;
    return dest;
}

static int load_cel_asset(CelAsset *asset)
{
    int length = 0;
    asset->image.width = asset->width;
    asset->image.height = asset->height;
    asset->image.data = (unsigned char *)avsp_fs_read_file_in_dir(asset->filename, "SPR4", &length);
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
    sound->data = avsp_fs_read_file_in_dir(filename, directory, &length);
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
                          AVSP_MELEE_PCM_SAMPLE_RATE) &&
           load_pcm_audio(&contact_sound, AVSP_CONTACT_PCM_FILE,
                          AVSP_CONTACT_PCM_DIRECTORY,
                          AVSP_CONTACT_PCM_BYTES,
                          AVSP_CONTACT_PCM_SAMPLE_RATE) &&
           load_pcm_audio(&ko_contact_sound, AVSP_KO_CONTACT_PCM_FILE,
                          AVSP_KO_CONTACT_PCM_DIRECTORY,
                          AVSP_KO_CONTACT_PCM_BYTES,
                          AVSP_KO_CONTACT_PCM_SAMPLE_RATE) &&
           load_pcm_audio(&boss_intro_sound, AVSP_BOSS_INTRO_PCM_FILE,
                          AVSP_BOSS_INTRO_PCM_DIRECTORY,
                          AVSP_BOSS_INTRO_PCM_BYTES,
                          AVSP_BOSS_INTRO_PCM_SAMPLE_RATE) &&
           /* boss_clear_sound (637 KB, the largest PCM) is phase-loaded at
              the interior transition instead of boot: the 32 Mbit cartridge
              cannot hold the whole boot working set plus the Body E ROM
              tile archive at once, and by that phase the ~900 KB of
              released opening PCM leaves ample room. CDDA is not active
              there (stage music start is currently disabled; when it
              returns, the interior wipe remains a legal seek window). */
           load_pcm_audio(&door_dialogue_sound,
                          AVSP_DOOR_DIALOGUE_PCM_FILE,
                          AVSP_DOOR_DIALOGUE_PCM_DIRECTORY,
                          AVSP_DOOR_DIALOGUE_PCM_BYTES,
                          AVSP_DOOR_DIALOGUE_PCM_SAMPLE_RATE) &&
           load_pcm_audio(&interior_transition_sound,
                          AVSP_INTERIOR_TRANSITION_PCM_FILE,
                          AVSP_INTERIOR_TRANSITION_PCM_DIRECTORY,
                          AVSP_INTERIOR_TRANSITION_PCM_BYTES,
                          AVSP_INTERIOR_TRANSITION_PCM_SAMPLE_RATE);
}

/* The four opening-overlay PCMs (title A/B, withdrawal, breach) are the
   phase-transient part of the boot working set: all four are released by the
   first wave. Jo's allocator never coalesces free neighbours and only a
   block adjacent to the zone's bump pointer rolls it back, so these MUST be
   the LAST large boot allocations - at the TOP of their zone - or their
   ~900 KB returns as unmergeable islands. The measured 2026-08-19 heap dump
   showed exactly that: with these loaded before the cel/archive sweep they
   sat at the BOTTOM of cartridge bank 1 under permanent assets, and the
   637,084-byte BOSSCLR.PCM phase load could never find more than 498,552
   contiguous bytes. Called last in the jo_main init chain; do not fold back
   into load_action_audio. */
static int load_opening_audio(void)
{
    return load_pcm_audio(&round_title_a_sound,
                          AVSP_ROUND_TITLE_A_PCM_FILE,
                          AVSP_ROUND_TITLE_A_PCM_DIRECTORY,
                          AVSP_ROUND_TITLE_A_PCM_BYTES,
                          AVSP_ROUND_TITLE_A_PCM_SAMPLE_RATE) &&
           load_pcm_audio(&round_title_b_sound,
                          AVSP_ROUND_TITLE_B_PCM_FILE,
                          AVSP_ROUND_TITLE_B_PCM_DIRECTORY,
                          AVSP_ROUND_TITLE_B_PCM_BYTES,
                          AVSP_ROUND_TITLE_B_PCM_SAMPLE_RATE) &&
           load_pcm_audio(&withdraw_sound, AVSP_WITHDRAW_PCM_FILE,
                          AVSP_WITHDRAW_PCM_DIRECTORY,
                          AVSP_WITHDRAW_PCM_BYTES,
                          AVSP_WITHDRAW_PCM_SAMPLE_RATE) &&
           load_pcm_audio(&breach_sound, AVSP_BREACH_PCM_FILE,
                          AVSP_BREACH_PCM_DIRECTORY,
                          AVSP_BREACH_PCM_BYTES,
                          AVSP_BREACH_PCM_SAMPLE_RATE);
}

static void release_pcm_data(jo_sound *sound)
{
    if (sound->data == JO_NULL) return;
    jo_free(sound->data);
    sound->data = JO_NULL;
    sound->data_length = 0;
}

/* Jo Engine queues SGL sound commands and flushes before, rather than after,
   slPCMOn. Explicitly commit both halves of a retrigger so a cue requested on
   the following frame cannot leave the prior start pending or see a stale
   channel state. This is required by the verified +2/+3 contact pair. */
static void play_pcm_committed(jo_sound *sound, jo_sound *previous_sound,
                               const unsigned char channel)
{
    if (previous_sound != JO_NULL && jo_audio_is_channel_playing(channel))
    {
        jo_audio_stop_sound(previous_sound);
        slSndFlush();
    }
    jo_audio_play_sound_on_channel(sound, channel);
    slSndFlush();
}

static int load_player_action_sequences(void)
{
    int layer;
    int length = 0;
    player_action_archive = (unsigned char *)avsp_fs_read_file_in_dir(
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

static int load_enemy_action_archive(void)
{
    int length = 0;
    enemy_action_archive = (unsigned char *)avsp_fs_read_file_in_dir(
        AVSP_ENEMY_ARCHIVE_FILE, "SPR4", &length);
    if (enemy_action_archive == JO_NULL ||
        length != AVSP_ENEMY_ARCHIVE_BYTES)
    {
        failed_asset = AVSP_ENEMY_ARCHIVE_FILE;
        return 0;
    }
    return 1;
}

static int allocate_enemy_action_buffer(void)
{
    int slot;
    const unsigned int total_bytes =
        CAP_MAX_ENEMIES * AVSP_ENEMY_DECODED_BYTES;

    if (enemy_action_buffer != JO_NULL) return 1;
    /* One contiguous pool can reuse the completed 396 KiB withdrawal PCM
       block. Jo's allocator does not split a reused free block, so eight
       individual allocations would strand most of that phase-overlay RAM. */
    enemy_action_buffer = (unsigned char *)jo_malloc_with_behaviour(
        total_bytes, JO_MALLOC_TRY_REUSE_BLOCK);
    if (enemy_action_buffer == JO_NULL)
    {
        failed_asset = "ENEMY ACTION BUFFER";
        return 0;
    }
    for (slot = 0; slot < CAP_MAX_ENEMIES; ++slot)
    {
        enemy_action_images[slot].width = AVSP_ENEMY_CEL_WIDTH;
        enemy_action_images[slot].height = AVSP_ENEMY_CEL_HEIGHT;
        enemy_action_images[slot].data = enemy_action_buffer +
            slot * AVSP_ENEMY_DECODED_BYTES;
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

static int load_stalker_action_archive(void)
{
    int length = 0;
    stalker_action_archive = (unsigned char *)avsp_fs_read_file_in_dir(
        AVSP_STALKER_ARCHIVE_FILE, "SPR4", &length);
    if (stalker_action_archive == JO_NULL ||
        length != AVSP_STALKER_ARCHIVE_BYTES)
    {
        failed_asset = AVSP_STALKER_ARCHIVE_FILE;
        return 0;
    }
    return 1;
}

static int decode_stalker_action_pose(const int pose, const int slot)
{
    unsigned int source = 0;
    unsigned int target = 0;
    const unsigned int source_offset = avsp_stalker_rle_offsets[pose];
    const unsigned int source_length = avsp_stalker_rle_bytes[pose];
    const unsigned char *source_data;
    unsigned char *output = enemy_action_images[slot].data;
    if (source_offset + source_length > AVSP_STALKER_ARCHIVE_BYTES)
    {
        failed_asset = "STALKER ACTION INDEX";
        return 0;
    }
    source_data = stalker_action_archive + source_offset;
    while (source + 1 < source_length)
    {
        unsigned int count = source_data[source++];
        unsigned char value = source_data[source++];
        if (count == 0 || target + count > AVSP_STALKER_DECODED_BYTES)
        {
            failed_asset = "STALKER ACTION RLE";
            return 0;
        }
        memset(output + target, value, count);
        target += count;
    }
    if (source != source_length || target != AVSP_STALKER_DECODED_BYTES)
    {
        failed_asset = "STALKER ACTION SIZE";
        return 0;
    }
    return 1;
}

/* Compose the given Chrysalis pose into boss_action_image from the ROM tile
   tables in generated/avsp_boss_rom.h. The ROM stores raw CPS2 pens (0..14
   visible, 15 transparent) in two-pens-per-byte tiles; the composed cel keeps
   pen+1 so the buffer's zero value stays transparent, in the same 4bpp
   high-nibble-first layout the VDP1 sprite and the archive oracles use. Parts
   are painted in reverse order so earlier parts overdraw later ones, matching
   the host-test compose that verifies all 29 poses against the archived
   BACT/BHIT/BKO output pixel for pixel. */
static int compose_boss_rom_pose(const int pose)
{
    const AvspBossRomPose *rom_pose;
    const AvspBossRomPart *parts;
    const AvspBossRomPart *part;
    const unsigned short *part_tiles;
    const unsigned char *tile;
    unsigned char *output;
    int min_x, max_x, min_y, max_y;
    int origin_x, origin_y;
    int i, p, tile_x, tile_y;
    int source_x, source_y, index, dest_x, dest_y;
    int tx, ty, src_tx, src_ty, cx, cy, pen, bit, tile_byte;

    output = boss_action_image.data;
    if (pose < 0 || pose >= AVSP_BOSS_ROM_POSE_COUNT || output == JO_NULL)
    {
        failed_asset = "BOSS ROM POSE";
        return 0;
    }
    memset(output, 0, AVSP_BOSS_DECODED_BYTES);
    rom_pose = &avsp_boss_rom_poses[pose];
    parts = &avsp_boss_rom_parts[rom_pose->part_offset];
    if (rom_pose->part_count == 0)
        return 1;
    min_x = -parts[0].lx - parts[0].nx * 16;
    max_x = -parts[0].lx;
    min_y = parts[0].ly;
    max_y = parts[0].ly + parts[0].ny * 16;
    for (i = 1; i < (int)rom_pose->part_count; ++i)
    {
        part = &parts[i];
        if (-part->lx - part->nx * 16 < min_x)
            min_x = -part->lx - part->nx * 16;
        if (-part->lx > max_x)
            max_x = -part->lx;
        if (part->ly < min_y)
            min_y = part->ly;
        if (part->ly + part->ny * 16 > max_y)
            max_y = part->ly + part->ny * 16;
    }
    origin_x = AVSP_BOSS_ROM_CEL_WIDTH / 2 - (min_x + max_x) / 2 + rom_pose->dx;
    origin_y = AVSP_BOSS_ROM_CEL_HEIGHT / 2 - (min_y + max_y) / 2 + rom_pose->dy;
    for (p = (int)rom_pose->part_count - 1; p >= 0; --p)
    {
        part = &parts[p];
        part_tiles = &avsp_boss_rom_part_tiles[part->tile_offset];
        for (tile_y = 0; tile_y < part->ny; ++tile_y)
        {
            for (tile_x = 0; tile_x < part->nx; ++tile_x)
            {
                source_y = part->flip_y ? part->ny - 1 - tile_y : tile_y;
                source_x = part->flip_x ? part->nx - 1 - tile_x : tile_x;
                index = part_tiles[source_y * part->nx + source_x];
                tile = &avsp_boss_rom_tiles[index * AVSP_BOSS_ROM_TILE_BYTES];
                dest_x = origin_x - part->lx - part->nx * 16 + tile_x * 16;
                dest_y = origin_y + part->ly + tile_y * 16;
                for (ty = 0; ty < 16; ++ty)
                {
                    for (tx = 0; tx < 16; ++tx)
                    {
                        src_ty = part->flip_y ? 15 - ty : ty;
                        src_tx = part->flip_x ? 15 - tx : tx;
                        tile_byte = tile[(src_ty * 16 + src_tx) / 2];
                        pen = (src_tx & 1) ? (tile_byte & 0xF) :
                            (tile_byte >> 4);
                        if (pen == 15)
                            continue;
                        cx = dest_x + tx;
                        cy = dest_y + ty;
                        if (cx < 0 || cx >= AVSP_BOSS_ROM_CEL_WIDTH ||
                            cy < 0 || cy >= AVSP_BOSS_ROM_CEL_HEIGHT)
                            continue;
                        bit = cy * AVSP_BOSS_ROM_CEL_WIDTH + cx;
                        if (bit & 1)
                        {
                            output[bit / 2] = (unsigned char)
                                ((output[bit / 2] & 0x0F) | ((pen + 1) << 4));
                        }
                        else
                        {
                            output[bit / 2] = (unsigned char)
                                ((output[bit / 2] & 0xF0) | (pen + 1));
                        }
                    }
                }
            }
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

    jo_create_palette_from(&actor_palette, colors, AVSP_CRAM_MAX_COLOURS);
}

static void set_frontend_palettes(void)
{
    static jo_color colors[256];
    int scene;
    int index;

    for (scene = 0; scene < AVSP_FRONTEND_SCENES; ++scene)
    {
        for (index = 0; index < 256; ++index)
            colors[index] = JO_COLOR_Black;
        jo_create_palette_from(&frontend_palettes[scene], colors,
                               AVSP_CRAM_MAX_COLOURS);
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
    jo_create_palette_from(&hud_palette, colors, AVSP_CRAM_MAX_COLOURS);
}

static int load_hud_image(jo_img_8bits *image, const char *filename,
                          const int width, const int height)
{
    int length = 0;
    image->width = width;
    image->height = height;
    image->data = (unsigned char *)avsp_fs_read_file_in_dir(
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
    avsp_frontend_init(&frontend_runtime, avsp_fs_read_file_in_dir,
                       background_bitmap, &frontend_palettes[0],
                       &frontend_palettes[1]);
    if (!avsp_frontend_load_title_surface(&frontend_runtime))
    {
        failed_asset = "ROM FRONTEND TITLE";
        return 0;
    }
    return 1;
}

static void release_frontend_scene(const int scene)
{
    if (scene == 0)
        avsp_frontend_release_title_objects(&frontend_runtime);
    else if (scene == 1)
        avsp_frontend_release_select_objects(&frontend_runtime);
}

static void copy_snapshot_to_background(const unsigned char *source)
{
    static unsigned char empty_row[BACKGROUND_WIDTH];
    int y;
    for (y = 0; y < BACKGROUND_HEIGHT; ++y)
    {
        unsigned char *target = background_bitmap + y * BACKGROUND_WIDTH;
        /* CPU copies avoid the transition-time DMA busy-wait deadlock seen
         * in interactive boots. This helper remains shared by the route
         * sequence surfaces; the ROM frontend RLE decoder writes NBG1
         * directly and does not call it. */
        memcpy(target, empty_row, BACKGROUND_WIDTH);
        if (y < SNAPSHOT_HEIGHT)
            memcpy(target, source + y * SNAPSHOT_FIT_WIDTH,
                   SNAPSHOT_FIT_WIDTH);
    }
}

static int activate_frontend_scene(const int scene)
{
    int bitmap_scene = BITMAP_SCENE_FRONTEND_BASE + scene;
    if (current_bitmap_scene == bitmap_scene) return 1;
    if (scene == 0 && !frontend_runtime.title_surface_ready)
    {
        failed_asset = "ROM FRONTEND TITLE";
        return 0;
    }
    if (scene == 1 && !frontend_runtime.select_surface_ready)
    {
        failed_asset = "ROM FRONTEND SELECT";
        return 0;
    }
    if (scene == 0)
        avsp_frontend_activate_title(&frontend_runtime);
    else
        avsp_frontend_activate_select(&frontend_runtime);
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
        sequence_rle[scene] = (unsigned char *)avsp_fs_read_file_in_dir(
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
        return world.encounter_timer < 60 ? -1 :
            AVSP_SEQUENCE_BOSS_DEATH_EXPLOSION;
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
    /* The route-sequence RLE pixels are already one-based (measured minimum 1
       across all thirteen holds), and avsp_sequence_palettes is indexed by
       source colour, so entry k is the colour of pixel k + 1 and transcribes
       straight into the Jo data range. 255 entries, not 256: the 256th would
       land on the next allocation's block boundary. */
    if (!avsp_cram_copy_source_indexed(
            (unsigned short *)frontend_palettes[0].data,
            (const unsigned short *)colors, AVSP_CRAM_MAX_COLOURS))
    {
        failed_asset = "SEQUENCE PALETTE COPY";
        return 0;
    }
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
    memcpy(background_bitmap, background_image.data, BACKGROUND_WIDTH * BACKGROUND_HEIGHT);
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
        memcpy(background_bitmap, boss_background_image.data,
                    BACKGROUND_WIDTH * BACKGROUND_HEIGHT);
        slBMPaletteNbg1((unsigned short)boss_background_palette.id);
    }
    else
    {
        memcpy(background_bitmap, background_image.data,
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
    hud_top_sprite = jo_sprite_add_8bits_image(&hud_top_image);
    hud_prompt_sprite = jo_sprite_add_8bits_image(&hud_prompt_image);
    hud_heat_sprite = jo_sprite_add_8bits_image(&hud_heat_image);
    if (hud_top_sprite < 0 || hud_prompt_sprite < 0 || hud_heat_sprite < 0)
        failed_asset = "HUD VDP1";
    displayed_hud_health = -1;
    displayed_hud_energy = -1;
    return failed_asset == JO_NULL;
}

static int prepare_enemy_runtime(void)
{
    int slot;

    if (enemy_runtime_ready) return 1;
    if (!allocate_enemy_action_buffer()) return 0;
    for (slot = 0; slot < CAP_MAX_ENEMIES; ++slot)
    {
        if (!decode_enemy_action_pose(0, slot)) return 0;
        enemy_action_sprites[slot] = jo_sprite_add_4bits_image(
            &enemy_action_images[slot]);
        if (enemy_action_sprites[slot] < 0)
        {
            failed_asset = "ENEMY ACTION VDP1";
            return 0;
        }
        current_enemy_action_poses[slot] = 0;
        current_enemy_action_kinds[slot] = CAP_ACTOR_ALIEN;
    }
    enemy_runtime_ready = 1;
    return 1;
}

static int prepare_boss_runtime(void)
{
    if (boss_runtime_ready) return 1;
    /* The boss is composed entirely from the ROM tile tables (see
       compose_boss_rom_pose), so no archive is loaded for its animation.
       Only the single decoded-cel buffer is allocated here. */
    boss_action_image.width = AVSP_BOSS_CEL_WIDTH;
    boss_action_image.height = AVSP_BOSS_CEL_HEIGHT;
    boss_action_image.data = (unsigned char *)jo_malloc_with_behaviour(
        AVSP_BOSS_DECODED_BYTES, JO_MALLOC_TRY_REUSE_BLOCK);
    if (boss_action_image.data == JO_NULL)
    {
        failed_asset = "BOSS ACTION BUFFER";
        return 0;
    }
    if (!compose_boss_rom_pose(0)) return 0;
    boss_action_sprite = jo_sprite_add_4bits_image(&boss_action_image);
    if (boss_action_sprite < 0)
    {
        failed_asset = "BOSS ACTION VDP1";
        return 0;
    }
    current_boss_action_pose = 0;
    boss_runtime_ready = 1;
    return 1;
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

static int stalker_clip_for_action(const CapAction action)
{
    if (action == CAP_ACT_ATTACK) return AVSP_STALKER_CLIP_ATTACK;
    if (action == CAP_ACT_HIT) return AVSP_STALKER_CLIP_HIT;
    if (action == CAP_ACT_KO) return AVSP_STALKER_CLIP_KO;
    return AVSP_STALKER_CLIP_WALK;
}

static int stalker_pose_for_frame(const int clip, const int action_frame)
{
    int step;
    int remaining = action_frame;
    for (step = 0; step < avsp_stalker_step_counts[clip]; ++step)
    {
        int duration = avsp_stalker_step_durations[clip][step];
        if (remaining < duration)
            return avsp_stalker_step_poses[clip][step];
        remaining -= duration;
    }
    return avsp_stalker_step_poses[clip]
        [avsp_stalker_step_counts[clip] - 1];
}

static int boss_clip_for_action(const CapAction action)
{
    if (action == CAP_ACT_ATTACK) return AVSP_BOSS_CLIP_ATTACK;
    if (action == CAP_ACT_HIT) return AVSP_BOSS_CLIP_HIT;
    if (action == CAP_ACT_KO) return AVSP_BOSS_CLIP_KO;
    if (action == CAP_ACT_WALK) return AVSP_BOSS_CLIP_WALK;
    return AVSP_BOSS_CLIP_IDLE;
}

static int boss_pose_for_frame(const int clip, const int action_frame)
{
    int step;
    int remaining = action_frame;
    for (step = 0; step < avsp_boss_step_counts[clip]; ++step)
    {
        int duration = avsp_boss_step_durations[clip][step];
        if (remaining < duration)
            return avsp_boss_step_poses[clip][step];
        remaining -= duration;
    }
    return avsp_boss_step_poses[clip][avsp_boss_step_counts[clip] - 1];
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
    int is_stalker = actor->kind == CAP_ACTOR_STALKER;
    int depth = 330 - actor->lane;
    int clip = is_stalker ? stalker_clip_for_action(actor->action) :
                            enemy_clip_for_action(actor->action);
    int frame = (actor->action == CAP_ACT_WALK ||
                 actor->action == CAP_ACT_IDLE) ?
        actor->locomotion_frame : actor->action_frame;
    int total_frames = is_stalker ? avsp_stalker_total_frames[clip] :
                                    avsp_enemy_total_frames[clip];
    int pose;
    if ((is_stalker && clip == AVSP_STALKER_CLIP_WALK) ||
        (!is_stalker && clip == AVSP_ENEMY_CLIP_WALK))
        frame %= total_frames;
    else if (frame >= total_frames)
        frame = total_frames - 1;
    pose = is_stalker ? stalker_pose_for_frame(clip, frame) :
                        enemy_pose_for_frame(clip, frame);
    if (pose != current_enemy_action_poses[slot] ||
        current_enemy_action_kinds[slot] != actor->kind)
    {
        int decoded = is_stalker ? decode_stalker_action_pose(pose, slot) :
                                   decode_enemy_action_pose(pose, slot);
        if (!decoded)
        {
            runtime_ready = 0;
            return;
        }
        jo_sprite_replace_4bits_image(
            &enemy_action_images[slot], enemy_action_sprites[slot]);
        current_enemy_action_poses[slot] = pose;
        current_enemy_action_kinds[slot] = actor->kind;
    }
    draw_exact_layer(actor, screen_x, enemy_action_sprites[slot],
                     is_stalker ? AVSP_STALKER_PALETTE_BANK :
                                  3 + actor->variant, depth);
}

static void draw_boss(const CapActor *actor, const int screen_x)
{
    int depth = 330 - actor->lane;
    int clip = boss_clip_for_action(actor->action);
    int frame = clip == AVSP_BOSS_CLIP_WALK ?
        actor->locomotion_frame : actor->action_frame;
    int pose;
    int screen_offset_x;
    int screen_offset_y;
    /* Boss graphics enter the working set only after the opening PCM overlay
       has ended. This avoids reserving a second large decoded actor cel during
       the cold-boot menu and first-wave allocation phase. */
    if (!prepare_boss_runtime())
    {
        runtime_ready = 0;
        return;
    }
    if (clip == AVSP_BOSS_CLIP_WALK)
        frame %= avsp_boss_total_frames[clip];
    else if (frame >= avsp_boss_total_frames[clip])
        frame = avsp_boss_total_frames[clip] - 1;
    screen_offset_x = avsp_boss_frame_x[clip][frame] *
        CAP_VIEW_WIDTH / CAP_CPS2_VIEW_WIDTH;
    screen_offset_y = avsp_boss_frame_y[clip][frame];
    pose = boss_pose_for_frame(clip, frame);
    if (pose != current_boss_action_pose)
    {
        if (!compose_boss_rom_pose(pose))
        {
            runtime_ready = 0;
            return;
        }
        jo_sprite_replace_4bits_image(
            &boss_action_image, boss_action_sprite);
        current_boss_action_pose = pose;
    }
    draw_exact_layer_offset(actor, screen_x, screen_offset_x, screen_offset_y,
                            boss_action_sprite, AVSP_BOSS_PALETTE_BANK, depth);
}

/* The captured character-confirm transition is a row shutter over the held
   selection image, not an animation: every visible row is byte-identical to
   the held frame and everything else is black. The selection pixels are
   already in the VDP2 bitmap, so the shutter is a progressive blackout of
   that bitmap and needs no stored frames and no source surface. Blacking is
   safe because the band only ever shrinks; only the rows newly hidden since
   the previous frame are written. See docs/AGENT_HANDOFF.md and
   data/frontend_geometry_cadence1.json. */
static void apply_confirm_shutter(void)
{
    static unsigned char empty_row[BACKGROUND_WIDTH];
    int top = 0;
    int bottom = 0;
    int previous_top = 0;
    int previous_bottom = 0;
    int row;

    /* The band is a function of frames since the confirm input. The
       rendered encounter timer leads that count by one (the confirm step
       both zeroes and increments it), and the complete-interval proof in
       tools/verify_confirm_shutter.py pins the first masked source frame
       to input + 86, so the timer is converted back before the lookup. */
    if (world.encounter_timer - 1 <= CAP_CONFIRM_SHUTTER_START_TIMER) return;
    (void)cap_confirm_shutter_band(world.encounter_timer - 1, &top, &bottom);
    (void)cap_confirm_shutter_band(world.encounter_timer - 2, &previous_top,
                                   &previous_bottom);
    if (previous_top > previous_bottom) return;
    if (top > bottom)
    {
        top = previous_bottom + 1;
        bottom = previous_bottom;
    }
    for (row = previous_top; row < top; ++row)
        memcpy(background_bitmap + row * BACKGROUND_WIDTH, empty_row,
                    BACKGROUND_WIDTH);
    for (row = bottom + 1; row <= previous_bottom; ++row)
        memcpy(background_bitmap + row * BACKGROUND_WIDTH, empty_row,
                    BACKGROUND_WIDTH);
}

/* S2 Body D, widened toward the full cast: EVERY active street alien
 * carries a real animation record (avsp_anim_frame_tick over the shipped
 * spans) and produces its semantic object list each frame through the
 * proven decoder (avsp_emit_pose_view over the generated ROM windows).
 * Coverage boundary, stated plainly: the ROM path runs for street aliens
 * in their WALK and ATTACK actions only, using the same two live-verified
 * script seeds Body D shipped; hit/KO/spawn actions and stalkers fall
 * back to the capture cels.
 *
 * tools/gen_avsp_action_seeds.py mined a real (actor_type, action ->
 * record) table from the captures (data/avsp_action_seeds.json), but it
 * is NOT wired here: its key is the game's OWN action word at actor
 * +0x06, a different space from this model's CapAction enum, and no
 * translation between the two exists yet - inventing one would be a
 * guess, not a measurement. That table becomes usable once S5 supplies
 * the real action-selection logic (which naturally produces the ROM
 * action word instead of the model's enum); until then it is decoded
 * evidence, not a wireable bridge. Of 42 mined keys only 16 were
 * unanimous across every observed re-point; the rest showed the game
 * choosing among per-instance variants this table doesn't yet resolve,
 * and were withheld rather than guessed.
 *
 * Pose seeding on action change is ADAPTED from the capability model's
 * action enum; the coordinate/anchor mapping between model space and
 * CPS2 world space is ADAPTED likewise; the per-slot palette follows the
 * corpus-observed street bank set 0x10..0x13 through the model's variant
 * field (ADAPTED). */
static AvspAnimScript rom_actor_script;
static AvspRomView rom_actor_view;
static AvspAnimFrame rom_actor_frames[CAP_MAX_ENEMIES];
static AvspActor rom_actor_collision_views[CAP_MAX_ENEMIES];
static unsigned char rom_actor_seeded[CAP_MAX_ENEMIES];
static int rom_actor_last_actions[CAP_MAX_ENEMIES];
static AvspObjectEntry rom_actor_entries_all[CAP_MAX_ENEMIES][16];
static int rom_actor_entry_counts[CAP_MAX_ENEMIES];
/* HUD/back-compat aggregates: total entries and the first live code. */
static int rom_actor_entry_count = 0;
static AvspObjectEntry rom_actor_entries[16];
/* Step 3 collision diagnostics, both per-frame and cumulative.
 *
 * NH counts the MEASURED cannot-be-hit verdict: the live record advertises a
 * hurt selector of 0, which the game rejects before any table read. That is a
 * real rule, so it is honored with no fallback to the point approximation.
 *
 * GAP counts the opposite case - a ROM-driven slot for which this frame
 * produced NO measured verdict at all (a pose outside the two street loops,
 * an unresolvable record, or a selector the decoded family cannot resolve).
 * A missing measurement is not evidence of invulnerability, so those frames
 * keep the pre-existing ADAPTED point approximation; the counter is what keeps
 * the gap visible instead of silent. */
static volatile int rom_collision_no_hurt;
static volatile int rom_collision_no_hurt_frame;
static volatile int rom_collision_gap;
static volatile int rom_collision_gap_frame;
static volatile int rom_class_lookup_miss;
static volatile int rom_class_lookup_miss_frame;

/* Resolve the record, emitted objects and collision view that BOTH gameplay
 * and rendering consume this frame. Animation advancement is deliberately in
 * rom_actor_advance() after draw_world(), so collision and pixels cannot see
 * adjacent records. */
static void rom_actor_prepare(void)
{
    int index;
    AvspEmitActor state;

    rom_actor_entry_count = 0;
    rom_collision_no_hurt_frame = 0;
    rom_collision_gap_frame = 0;
    rom_class_lookup_miss_frame = 0;
    /* The ROM collision view is valid only for ROM-driven street aliens in the
     * two street-wave states; zero it for every slot each frame so the point
     * approximation applies everywhere else (capture-cel actors, boss, etc.). */
    for (index = 0; index < CAP_MAX_ENEMIES; ++index)
    {
        memset(&rom_actor_collision_views[index], 0, sizeof(AvspActor));
        world.enemies[index].rom_street_alien = 0;
        world.enemies[index].rom_can_hit = 0;
        world.enemies[index].rom_box_x_lo = 0;
        world.enemies[index].rom_box_x_hi = 0;
    }
    /* Run only in the two street-wave combat states: outside them enemy
     * slots can be mid-initialization, and a reported freeze at the
     * character-confirm transition traced to ticking against one. */
    if (world.encounter_state != CAP_ENCOUNTER_WAVE_ONE &&
        world.encounter_state != CAP_ENCOUNTER_WAVE_TWO)
    {
        for (index = 0; index < CAP_MAX_ENEMIES; ++index)
        {
            rom_actor_seeded[index] = 0;
            rom_actor_entry_counts[index] = 0;
        }
        return;
    }
    if (rom_actor_script.spans == 0)
    {
        rom_actor_script.rom = 0;
        rom_actor_script.base = 0;
        rom_actor_script.size = 0;
        rom_actor_script.spans = avsp_anim_spans;
        rom_actor_script.span_count = avsp_anim_span_count;
        rom_actor_view.spans = avsp_emit_windows;
        rom_actor_view.span_count = AVSP_EMIT_WINDOW_COUNT;
    }
    for (index = 0; index < CAP_MAX_ENEMIES; ++index)
    {
        CapActor *enemy = &world.enemies[index];
        unsigned int seed;
        int n;

        rom_actor_entry_counts[index] = 0;
        if (!enemy->active || enemy->kind != CAP_ACTOR_ALIEN)
        {
            rom_actor_seeded[index] = 0;
            continue;
        }
        if (enemy->action != CAP_ACT_WALK &&
            enemy->action != CAP_ACT_ATTACK)
        {
            /* No ROM record is driven outside the two street loops (hit, KO,
             * idle, spawn), so this frame has NO measured hit geometry for the
             * slot. It keeps the ADAPTED point approximation: silence about a
             * pose is not a measurement that it cannot be hit, and inventing a
             * 36-frame hitstun invulnerability out of missing data would be a
             * fabricated rule. Per-state ROM coverage needs the state-dispatch
             * decode first (docs/NEXT_AGENT_PROMPT.md). */
            rom_actor_seeded[index] = 0;
            ++rom_collision_gap;
            ++rom_collision_gap_frame;
            continue;
        }
        /* ADAPTED action bridge: the two live-verified street-alien loops. */
        seed = (enemy->action == CAP_ACT_ATTACK) ? 0x12D8A0u : 0x12EB4Cu;
        if (!rom_actor_seeded[index] ||
            (int)enemy->action != rom_actor_last_actions[index])
        {
            avsp_anim_frame_start(&rom_actor_frames[index],
                                  &rom_actor_script, seed);
            rom_actor_seeded[index] = 1;
            rom_actor_last_actions[index] = (int)enemy->action;
        }
        if (!rom_actor_frames[index].pose.valid) continue;
        /* ADAPTED coordinate bridge: model-space camera as the anchor pair
         * so decoded X approximates screen position. */
        state.world_x = (unsigned short)enemy->x;
        state.world_y = (unsigned short)(200 + enemy->height);
        state.facing = (unsigned char)(enemy->facing < 0 ? 1 : 0);
        state.palette = (unsigned char)(0x10 + (enemy->variant & 3));
        state.mode = 1;
        state.or_value = 0x8000;
        state.anchor_x = (unsigned short)world.camera_x;
        state.anchor_y = 0x00FF;
        n = avsp_emit_pose_view(&rom_actor_view,
                                rom_actor_frames[index].pose.assembly,
                                &state, rom_actor_entries_all[index], 16);
        rom_actor_entry_counts[index] = (n > 0) ? n : 0;
        if (rom_actor_entry_counts[index] > 0 && rom_actor_entry_count == 0)
            rom_actor_entries[0] = rom_actor_entries_all[index][0];
        rom_actor_entry_count += rom_actor_entry_counts[index];
        /* S4: the DEFENDER's MEASURED hurt box. sel_hurt is the live
         * animation record's byte +8 (byte +9, sel_attack, is the attacker
         * side and is deferred - the player has no ROM record yet). The X
         * centre is resolved in the same ADAPTED model-space world_x/facing
         * the emitter above used, so it is comparable to the player's reach in
         * cap_resolve_player_hit. The canonical AvspActor below is also the
         * single source for record, selectors and collision table this frame. */
        {
            const unsigned char *rec = avsp_anim_resolve(&rom_actor_script,
                                                         rom_actor_frames[index].addr,
                                                         10);
            unsigned char sel_hurt = (rec != 0) ? rec[8] : 0u;
            unsigned char sel_attack = (rec != 0) ? rec[9] : 0u;
            AvspActor *view = &rom_actor_collision_views[index];
            AvspBox hurt;

            /* Class 0x1F is assigned only on this validated street-alien path.
             * The approximate model does not produce source sub_state or
             * action_word values, so those remain zero/unresolved rather than
             * fabricating class 0x00/0x06 transitions. */
            view->state = 1u;
            view->class_id = 0x1Fu;
            view->type = 0x0Cu;
            view->facing = state.facing;
            view->world_x = state.world_x;
            view->world_y = state.world_y;
            view->world_z = (unsigned short)enemy->lane;
            view->anim_record = (unsigned long)rom_actor_frames[index].addr;
            view->sel_hurt = sel_hurt;
            view->sel_attack = sel_attack;
            if (!avsp_table_set_for_class(view->class_id, &view->table_set))
            {
                ++rom_class_lookup_miss;
                ++rom_class_lookup_miss_frame;
                ++rom_collision_gap;
                ++rom_collision_gap_frame;
                continue;
            }
            /* rom_street_alien is set ONLY where this frame produced a measured
             * verdict, so cap_resolve_player_hit leaves every other frame on the
             * ADAPTED approximation rather than on an invented invulnerability. */
            if (rec != 0 && sel_hurt == 0u)
            {
                /* MEASURED cannot-be-hit: the game rejects selector 0 before
                 * any table read. Honor it with no fallback, and count it. */
                enemy->rom_street_alien = 1;
                enemy->rom_can_hit = 0;
                ++rom_collision_no_hurt;
                ++rom_collision_no_hurt_frame;
            }
            else if (rec != 0 &&
                     avsp_collision_hurt_box(view->table_set, sel_hurt, &hurt))
            {
                int center = (int)state.world_x +
                             (state.facing ? -(int)hurt.x_center
                                           : (int)hurt.x_center);
                enemy->rom_street_alien = 1;
                enemy->rom_can_hit = 1;
                enemy->rom_box_x_lo = center - (int)hurt.x_half;
                enemy->rom_box_x_hi = center + (int)hurt.x_half;
            }
            else
            {
                /* Unresolvable record, or a selector the decoded family cannot
                 * resolve: a DATA GAP, not a cannot-hit pose. It must not occur
                 * for the checked street class, so it stays on the ADAPTED
                 * approximation and is counted where it can be seen. */
                ++rom_collision_gap;
                ++rom_collision_gap_frame;
            }
        }
    }
}

/* Advance exactly once after the prepared record has been rendered. If the
 * approximate model changed action during cap_world_step(), discard the old
 * program instead; the next frame starts the newly selected ADAPTED seed. */
static void rom_actor_advance(void)
{
    int index;

    for (index = 0; index < CAP_MAX_ENEMIES; ++index)
    {
        if (!rom_actor_seeded[index]) continue;
        if (!world.enemies[index].active ||
            world.enemies[index].kind != CAP_ACTOR_ALIEN ||
            (int)world.enemies[index].action != rom_actor_last_actions[index])
        {
            rom_actor_seeded[index] = 0;
            continue;
        }
        avsp_anim_frame_tick(&rom_actor_frames[index], &rom_actor_script);
    }
}

/* S2 Body E: the per-object VDP1 consumer. The ROM actor's semantic object
 * list renders as one 16x16 normal-sprite draw per referenced tile - the
 * measured architecture of the reference Capcom Saturn port (all foreground
 * commands 16x16, 16-colour bank mode, flip in the command, flat draw
 * order) - textured from the cart-resident TILES.BIN archive through a
 * fixed VDP1 pool with in-place LRU replacement. */
static unsigned char *tile_archive_data;
static AvspTileArchive tile_archive;
static jo_palette tile_palette;
static int tile_archive_ready;
static int tile_pool_sprite[AVSP_TILE_SPRITE_POOL];
static long tile_pool_rank[AVSP_TILE_SPRITE_POOL];
static unsigned long tile_pool_stamp[AVSP_TILE_SPRITE_POOL];
static unsigned long tile_pool_clock;
static int tile_pool_used;
/* A missing tile or bank is an asset defect, never a silent skip: these
   counters surface on the debug HUD and stay readable by the headless
   debugger (volatile so the release optimizer keeps them). */
static volatile int tile_diag_no_bank;
static volatile int tile_diag_no_rank;
static volatile int tile_diag_no_sprite;

static int load_tile_archive(void)
{
    int read_bytes;
    int slot;
    int index;
    static jo_color colors[256];

    /* Staged CPU read straight into the carved cartridge region. */
    tile_archive_data = AVSP_CART_DRAM1_BASE;
    read_bytes = avsp_fs_read_into("TILES.BIN", "SPR4", tile_archive_data,
                                   AVSP_TILE_REGION_BYTES);
    if (read_bytes <= 0 ||
        !avsp_tiles_open(&tile_archive, tile_archive_data,
                         (unsigned long)read_bytes))
    {
        failed_asset = "TILES.BIN";
        return 0;
    }
    /* Pixel value p+1 reads palette array entry p after Jo's CRAM base+1
       shift, so slot colours transcribe directly. */
    for (index = 0; index < 256; ++index) colors[index] = JO_COLOR_Black;
    for (slot = 0; slot < (int)tile_archive.palette_slots; ++slot)
        for (index = 0; index < 15; ++index)
            colors[slot * 16 + index] = (jo_color)
                avsp_tiles_cram_color(&tile_archive, slot, index);
    jo_create_palette_from(&tile_palette, colors, AVSP_CRAM_MAX_COLOURS);
    tile_pool_used = 0;
    tile_pool_clock = 0;
    tile_archive_ready = 1;
    return 1;
}

static int tile_sprite_for_rank(const long rank)
{
    int index;
    int victim = 0;
    jo_img_4bits img;

    for (index = 0; index < tile_pool_used; ++index)
    {
        if (tile_pool_rank[index] == rank)
        {
            tile_pool_stamp[index] = ++tile_pool_clock;
            return tile_pool_sprite[index];
        }
    }
    img.width = 16;
    img.height = 16;
    img.data = (unsigned char *)avsp_tiles_texture(&tile_archive, rank);
    if (img.data == JO_NULL) return -1;
    if (tile_pool_used < AVSP_TILE_SPRITE_POOL)
    {
        int sprite_id = jo_sprite_add_4bits_image(&img);
        if (sprite_id < 0) return -1;
        tile_pool_sprite[tile_pool_used] = sprite_id;
        tile_pool_rank[tile_pool_used] = rank;
        tile_pool_stamp[tile_pool_used] = ++tile_pool_clock;
        return tile_pool_sprite[tile_pool_used++];
    }
    for (index = 1; index < AVSP_TILE_SPRITE_POOL; ++index)
        if (tile_pool_stamp[index] < tile_pool_stamp[victim]) victim = index;
    if (jo_sprite_replace_4bits_image(&img, tile_pool_sprite[victim]) < 0)
        return -1;
    tile_pool_rank[victim] = rank;
    tile_pool_stamp[victim] = ++tile_pool_clock;
    return tile_pool_sprite[victim];
}

static int wrap_signed_10bit(int delta)
{
    delta &= 0x3FF;
    if (delta >= 512) delta -= 1024;
    return delta;
}

static int fit_352(const int cps_x)
{
    if (cps_x < 0) return -((-cps_x * CAP_VIEW_WIDTH) / CAP_CPS2_VIEW_WIDTH);
    return (cps_x * CAP_VIEW_WIDTH) / CAP_CPS2_VIEW_WIDTH;
}

static void draw_rom_actor_tiles(const CapActor *actor, const int slot)
{
    /* ADAPTED placement bridge: the emitter ran with model-space anchors
       (rom_actor_prepare), so entries are positioned as offsets from the
       decoded origin and re-anchored at the actor's model screen position;
       exact CPS2 anchor alignment lands with S5's world-space translation.
       The cel pivot convention (pixel 184 of a 192px cel drawn centred at
       lane-200-height) puts the actor's CPS2 origin 88px below the cel
       centre. */
    const int origin_cps_x = 0x40 + actor->x - world.camera_x;
    const int origin_dec_y = (0x100 + 0xFF - (200 + actor->height)) & 0x3FF;
    const int anchor_jo_y = actor->lane - 200 - actor->height + 88;
    const int depth = 330 - actor->lane;
    int index;

    jo_sprite_set_palette_4bits(tile_palette.id, 0);
    for (index = rom_actor_entry_counts[slot] - 1; index >= 0; --index)
    {
        const AvspObjectEntry *entry = &rom_actor_entries_all[slot][index];
        AvspEntryTile tiles[64];
        int offset_x = wrap_signed_10bit((int)(entry->x & 0x3FF) -
                                         (origin_cps_x & 0x3FF));
        int offset_y = wrap_signed_10bit((int)(entry->y & 0x3FF) -
                                         origin_dec_y);
        int bank_slot = avsp_tiles_bank_slot(&tile_archive,
                                             entry->attr & 0x1F);
        int count = avsp_entry_tiles(entry->y, entry->code, entry->attr,
                                     tiles, 64);
        int tile;
        if (count <= 0 || bank_slot < 0)
        {
            ++tile_diag_no_bank;
            continue;
        }
        jo_sprite_set_palette_4bits(tile_palette.id, bank_slot);
        for (tile = 0; tile < count; ++tile)
        {
            long rank = avsp_tiles_find(&tile_archive, tiles[tile].code);
            int sprite_id;
            int jo_x;
            int jo_y;
            if (rank < 0)
            {
                ++tile_diag_no_rank;
                continue;
            }
            sprite_id = tile_sprite_for_rank(rank);
            if (sprite_id < 0)
            {
                ++tile_diag_no_sprite;
                continue;
            }
            jo_x = fit_352(origin_cps_x - 256 + offset_x +
                           tiles[tile].dx + 8);
            jo_y = anchor_jo_y + offset_y + tiles[tile].dy + 8;
            if (tiles[tile].flip_x) jo_sprite_enable_horizontal_flip();
            if (tiles[tile].flip_y) jo_sprite_enable_vertical_flip();
            jo_sprite_draw3D(sprite_id, jo_x, jo_y, depth);
            if (tiles[tile].flip_x) jo_sprite_disable_horizontal_flip();
            if (tiles[tile].flip_y) jo_sprite_disable_vertical_flip();
        }
    }
}


#ifdef AVSP_STREET_TEST
/* ---- RP4 representative street interval (source frames 3474-3674) ----
 *
 * Plays the STRIPS.BIN bundle generated by tools/gen_avsp_street_planes.py:
 * scroll3 on NBG1 and scroll2 on NBG0 as VDP2 cell planes built offline
 * from ROM tiles at the shared endpoint-aligned 384-to-352 pre-scale,
 * per-frame independent scroll from the captured CPS-A registers, the
 * measured bank-1 palette cycle as CRAM rewrites, the measured map-cell
 * animation as pattern-name updates, and the recorded object schedule
 * through the same avsp_entry_tiles VDP1 path gameplay uses. */

#define STREET_NBG0_CEL ((unsigned char *)VDP2_VRAM_A0)
#define STREET_NBG1_CEL ((unsigned char *)VDP2_VRAM_A1)
#define STREET_NBG0_PNT ((unsigned short *)VDP2_VRAM_B0)
#define STREET_NBG1_PNT ((unsigned short *)(VDP2_VRAM_B0 + 0x4000))
#define STREET_PAGE_WORDS 0x1000 /* one 64x64 1-word pattern page */

extern void slPageNbg0(void *, void *, Uint16);
extern void slMapNbg0(void *, void *, void *, void *);
extern void slPlaneNbg0(Uint16);
extern void slScrPosNbg0(FIXED, FIXED);
extern void slColRAMOffsetNbg0(Uint16);
extern void slColRAMOffsetNbg1(Uint16);
/* SGL's SL_DEF.H (in scope through the Jo/SGL include chain) already
   defines the sprite-class screen selectors; keep guarded fallbacks so
   the values (-8, -5) stay pinned to the measured registers. */
#ifndef scnSPR1
#define scnSPR1 (-8)
#endif
#ifndef scnSPR2
#define scnSPR2 (-5)
#endif

typedef struct
{
    int cell_cols;
    int cell_rows;
    int world_x0;
    int row0;
    int char_count;
    unsigned long char_offset;
    unsigned long pnt_offset;
} StreetPlane;

static unsigned char *street_data;
static long street_bytes;
static int street_ready;
static int street_frames;
static StreetPlane street_plane[2];
static unsigned long street_scroll_offset;
static unsigned long street_patch_offset;
static unsigned long street_objects_offset;
static int street_cycle_period;
static int street_cycle_first_flip;
static int street_cycle_entries;
static unsigned long street_cycle_offset;
static jo_palette street_palette[2];
#define STREET_MAX_FRAMES 256
#define STREET_MAX_PATCH_CELLS 64
static unsigned long street_object_frame_offset[STREET_MAX_FRAMES];
static unsigned long street_patch_revert[STREET_MAX_PATCH_CELLS][2];
static int street_patch_revert_count;
volatile int avsp_diag_street_frame;
volatile int avsp_diag_street_scx[2];
volatile int avsp_diag_street_objects;

static void street_load_planes(void);

/* CPS object priority -> Saturn sprite priority class. SPCTL is type 3
 * (measured 0x0023): frame-buffer bits 14-13 select the sprite priority
 * register. Jo leaves them zero (class 0, the HUD/default class); the
 * street objects OR class 1 (CPS priority 1, actors) or class 2 (CPS
 * priority 4, foreground) into the colour-bank word, exactly the
 * mechanism the official MSHvSF port was measured to use (0x6000/0x7000
 * prefixes over the 11-bit colour entry). */
#define STREET_SPR_CLASS_ACTOR 0x2000UL
#define STREET_SPR_CLASS_FOREGROUND 0x4000UL
extern jo_sprite_attributes __jo_sprite_attributes;

static void street_object_palette(const int bank_slot, const int priority)
{
    jo_sprite_set_palette_4bits(tile_palette.id, bank_slot);
    __jo_sprite_attributes.color_table_index |=
        priority >= 4 ? STREET_SPR_CLASS_FOREGROUND :
        STREET_SPR_CLASS_ACTOR;
}

static unsigned int street_u16(const unsigned long offset)
{
    return ((unsigned int)street_data[offset] << 8) |
           street_data[offset + 1];
}

static unsigned long street_u32(const unsigned long offset)
{
    return ((unsigned long)street_u16(offset) << 16) |
           street_u16(offset + 2);
}

/* Runtime inverse of the generator's out_of(): the smallest output column
 * whose endpoint-aligned source is at least world_x. */
static int street_out_of(const int world_x)
{
    return (world_x * 351 - 175 + 382) / 383;
}

static int street_setup(void)
{
    long read_bytes;
    int plane;
    int index;

    street_data = AVSP_CART_DRAM1_BASE + AVSP_TILE_REGION_BYTES;
    read_bytes = avsp_fs_read_into("STRIPS.BIN", "ST1", street_data,
                                   AVSP_STRIPS_REGION_BYTES);
    if (read_bytes <= 0 || street_u32(0) != 0x41565353UL ||
        street_u16(4) != 1)
    {
        failed_asset = "STRIPS.BIN";
        return 0;
    }
    street_bytes = read_bytes;
    street_frames = (int)street_u16(6);
    if (street_frames <= 0 || street_frames > STREET_MAX_FRAMES)
    {
        failed_asset = "STRIPS FRAMES";
        return 0;
    }
    /* Each plane header is 20 bytes: six u16 fields then two u32s. */
    for (plane = 0; plane < 2; ++plane)
    {
        const unsigned long at = 8 + (unsigned long)plane * 20;
        street_plane[plane].cell_cols = (int)street_u16(at);
        street_plane[plane].cell_rows = (int)street_u16(at + 2);
        street_plane[plane].world_x0 = (int)street_u16(at + 4);
        street_plane[plane].row0 = (int)street_u16(at + 6);
        street_plane[plane].char_count = (int)street_u16(at + 8);
        street_plane[plane].char_offset = street_u32(at + 12);
        street_plane[plane].pnt_offset = street_u32(at + 16);
        if (street_plane[plane].cell_cols <= 0 ||
            street_plane[plane].cell_cols > 128 ||
            street_plane[plane].cell_rows <= 0 ||
            street_plane[plane].cell_rows > 64 ||
            street_plane[plane].char_count <= 0 ||
            street_plane[plane].char_count > 2048 ||
            street_plane[plane].char_offset +
                (unsigned long)street_plane[plane].char_count * 64 >
                (unsigned long)street_bytes ||
            street_plane[plane].pnt_offset +
                (unsigned long)street_plane[plane].cell_cols *
                street_plane[plane].cell_rows * 2 >
                (unsigned long)street_bytes)
        {
            failed_asset = "STRIPS PLANE";
            return 0;
        }
    }

    /* Palettes: two 256-entry blocks; strip pixel i reads block[i], with
       Jo's data pointer starting one entry above the block base. The
       street test REUSES the two frontend scene palette blocks instead of
       allocating new ones: boot already claims every remaining CRAM
       block, and Jo reports out-of-VDP2-memory on a fresh allocation
       (observed live). The frontend surfaces never draw in this mode. */
    for (plane = 0; plane < 2; ++plane)
    {
        const unsigned long at = 48 + (unsigned long)plane * 512;
        street_palette[plane] = frontend_palettes[plane];
        for (index = 1; index < 256; ++index)
            street_palette[plane].data[index - 1] =
                (jo_color)street_u16(at + (unsigned long)index * 2);
    }
    street_cycle_period = (int)street_u16(48 + 1024);
    street_cycle_first_flip = (int)street_u16(48 + 1026);
    street_cycle_entries = (int)street_u16(48 + 1028);
    street_cycle_offset = 48 + 1030;
    street_scroll_offset = street_cycle_offset +
        (unsigned long)street_cycle_entries * 6;
    street_patch_offset = street_scroll_offset +
        (unsigned long)street_frames * 8;
    street_objects_offset = street_patch_offset + 2;
    {
        int patch;
        const int patch_count = (int)street_u16(street_patch_offset);
        unsigned long cursor = street_patch_offset + 2;
        for (patch = 0; patch < patch_count; ++patch)
        {
            const int updates = (int)street_u16(cursor + 4);
            cursor += 6 + (unsigned long)updates * 6;
        }
        street_objects_offset = cursor;
    }
    /* Index every frame's object list once so per-frame lookup is O(1),
       and bounds-check the whole schedule against the file size. */
    {
        unsigned long cursor = street_objects_offset;
        int frame;
        for (frame = 0; frame < street_frames; ++frame)
        {
            int count;
            if (cursor + 2 > (unsigned long)street_bytes)
            {
                failed_asset = "STRIPS OBJECTS";
                return 0;
            }
            street_object_frame_offset[frame] = cursor;
            count = (int)street_u16(cursor);
            cursor += 2 + (unsigned long)count * 8;
        }
        if (cursor > (unsigned long)street_bytes)
        {
            failed_asset = "STRIPS OBJECTS";
            return 0;
        }
    }

    /* Character data and base pattern grids. */
    street_load_planes();

    slColRAMOffsetNbg0((Uint16)street_palette[0].id);
    slColRAMOffsetNbg1((Uint16)street_palette[1].id);
    slCharNbg0(COL_TYPE_256, CHAR_SIZE_1x1);
    slCharNbg1(COL_TYPE_256, CHAR_SIZE_1x1);
    slPageNbg0((void *)STREET_NBG0_CEL, 0, PNB_1WORD | CN_12BIT);
    slPageNbg1((void *)STREET_NBG1_CEL, 0, PNB_1WORD | CN_12BIT);
    slPlaneNbg0(PL_SIZE_2x1);
    slPlaneNbg1(PL_SIZE_2x1);
    slMapNbg0((void *)STREET_NBG0_PNT, (void *)STREET_NBG0_PNT,
              (void *)STREET_NBG0_PNT, (void *)STREET_NBG0_PNT);
    slMapNbg1((void *)STREET_NBG1_PNT, (void *)STREET_NBG1_PNT,
              (void *)STREET_NBG1_PNT, (void *)STREET_NBG1_PNT);
    slPriority(scnNBG0, 3);
    slPriority(scnNBG1, 2);
    /* Sprite class registers: class 0 (Jo default, HUD/debug) stays at 6;
       class 1 carries CPS priority-1 actors above both planes; class 2
       carries CPS priority-4 foreground above the actors. */
    slPriority(scnSPR1, 4);
    slPriority(scnSPR2, 6);
    jo_set_displayed_screens(JO_NBG0_SCREEN | JO_NBG1_SCREEN |
                             JO_SPRITE_SCREEN);
    street_ready = 1;
    return 1;
}

static void street_load_planes(void)
{
    int plane;
    for (plane = 0; plane < 2; ++plane)
    {
        const StreetPlane *sp = &street_plane[plane];
        unsigned short *cel = plane == 0 ?
            (unsigned short *)STREET_NBG0_CEL :
            (unsigned short *)STREET_NBG1_CEL;
        unsigned short *pnt = plane == 0 ? STREET_NBG0_PNT :
            STREET_NBG1_PNT;
        const unsigned long char_words =
            (unsigned long)sp->char_count * 32;
        unsigned long word;
        int cx;
        int cy;
        for (word = 0; word < char_words; ++word)
            cel[word] = (unsigned short)street_u16(sp->char_offset +
                                                   word * 2);
        /* Pattern pages: plane is 2x1 pages; cell (cx,cy) lands in page
           cx/64 at slot cy*64 + cx%64. 256-colour chars advance the
           12-bit character number by 2 per 8x8 cell. */
        for (word = 0; word < STREET_PAGE_WORDS * 2; ++word)
            pnt[word] = 0;
        for (cy = 0; cy < sp->cell_rows; ++cy)
            for (cx = 0; cx < sp->cell_cols; ++cx)
            {
                const unsigned int char_index = street_u16(
                    sp->pnt_offset +
                    ((unsigned long)cy * sp->cell_cols + cx) * 2);
                pnt[(cx / 64) * STREET_PAGE_WORDS +
                    (unsigned long)cy * 64 + (cx % 64)] =
                    (unsigned short)(char_index * 2);
            }
    }
}

static void street_apply_patches(const int rel)
{
    const int patch_count = (int)street_u16(street_patch_offset);
    unsigned long cursor = street_patch_offset + 2;
    int patch;
    for (patch = 0; patch < patch_count; ++patch)
    {
        const int frame_rel = (int)street_u16(cursor);
        const int plane = (int)street_u16(cursor + 2);
        const int updates = (int)street_u16(cursor + 4);
        if (frame_rel == rel)
        {
            unsigned short *pnt = plane == 0 ? STREET_NBG0_PNT :
                STREET_NBG1_PNT;
            int update;
            for (update = 0; update < updates; ++update)
            {
                const unsigned long at = cursor + 6 +
                    (unsigned long)update * 6;
                const int cx = (int)street_u16(at);
                const int cy = (int)street_u16(at + 2);
                const unsigned int char_index = street_u16(at + 4);
                unsigned short *slot = &pnt[(cx / 64) * STREET_PAGE_WORDS +
                    (unsigned long)cy * 64 + (cx % 64)];
                if (street_patch_revert_count < STREET_MAX_PATCH_CELLS)
                {
                    street_patch_revert[street_patch_revert_count][0] =
                        (unsigned long)slot;
                    street_patch_revert[street_patch_revert_count][1] =
                        *slot;
                    ++street_patch_revert_count;
                }
                *slot = (unsigned short)(char_index * 2);
            }
        }
        cursor += 6 + (unsigned long)updates * 6;
    }
}

static void street_apply_cycle(const int rel)
{
    /* First-flip semantics: measured state A until the first flip
       frame, then alternate every cycle period. */
    const int step = (street_cycle_period > 0 &&
                      rel >= street_cycle_first_flip) ?
        (((rel - street_cycle_first_flip) / street_cycle_period) + 1) & 1 : 0;
    int entry;
    for (entry = 0; entry < street_cycle_entries; ++entry)
    {
        const unsigned long at = street_cycle_offset +
            (unsigned long)entry * 6;
        const int index = (int)street_u16(at);
        const unsigned short colour = (unsigned short)
            street_u16(at + 2 + (unsigned long)step * 2);
        street_palette[0].data[index - 1] = colour;
    }
}

static void street_test_frame(void)
{
    static int frame_counter = 0;
    const int rel = frame_counter % street_frames;
    unsigned long at;
    unsigned long objects;
    int entry_count;
    int entry;
    int drawn = 0;

    if (!street_ready)
    {
        if (!street_setup())
        {
            jo_printf(1, 12, "STREET TEST FAILED: %s",
                      failed_asset == JO_NULL ? "UNKNOWN" : failed_asset);
            return;
        }
        frame_counter = 0;
    }
    if (rel == 0 && street_patch_revert_count > 0)
    {
        /* Loop wrap: undo the measured map patches by restoring the
           original pattern words recorded when they were applied. */
        int revert;
        for (revert = 0; revert < street_patch_revert_count; ++revert)
            *(unsigned short *)street_patch_revert[revert][0] =
                (unsigned short)street_patch_revert[revert][1];
        street_patch_revert_count = 0;
    }

    at = street_scroll_offset + (unsigned long)rel * 8;
    {
        const int s2x = (int)street_u16(at);
        const int s2y = (int)street_u16(at + 2);
        const int s3x = (int)street_u16(at + 4);
        const int s3y = (int)street_u16(at + 6);
        const int scx0 = street_out_of(s2x + 64) -
            street_out_of(street_plane[0].world_x0);
        const int scy0 = s2y + 16 - street_plane[0].row0 * 16;
        const int scx1 = street_out_of(s3x + 64) -
            street_out_of(street_plane[1].world_x0);
        const int scy1 = s3y + 16 - street_plane[1].row0 * 32;
        slScrPosNbg0(toFIXED(scx0), toFIXED(scy0));
        slScrPosNbg1(toFIXED(scx1), toFIXED(scy1));
        avsp_diag_street_scx[0] = scx0;
        avsp_diag_street_scx[1] = scx1;
    }
    street_apply_cycle(rel);
    street_apply_patches(rel);

    /* Recorded object schedule through the gameplay tile path. */
    objects = street_object_frame_offset[rel];
    entry_count = (int)street_u16(objects);
    objects += 2;
    for (entry = 0; entry < entry_count; ++entry)
    {
        const unsigned int x = street_u16(objects);
        const unsigned int y = street_u16(objects + 2);
        const unsigned int code = street_u16(objects + 4);
        const unsigned int attr = street_u16(objects + 6);
        const int priority = (int)((x >> 13) & 7);
        AvspEntryTile entry_tiles[64];
        const int bank_slot = avsp_tiles_bank_slot(&tile_archive,
                                                   (int)(attr & 0x1F));
        const int count = avsp_entry_tiles((unsigned short)y,
                                           (unsigned short)code,
                                           (unsigned short)attr,
                                           entry_tiles, 64);
        int tile;
        objects += 8;
        if (count <= 0 || bank_slot < 0) continue;
        street_object_palette(bank_slot, priority);
        for (tile = 0; tile < count; ++tile)
        {
            const long rank = avsp_tiles_find(&tile_archive,
                                              entry_tiles[tile].code);
            int sprite_id;
            if (rank < 0) continue;
            sprite_id = tile_sprite_for_rank(rank);
            if (sprite_id < 0) continue;
            if (entry_tiles[tile].flip_x) jo_sprite_enable_horizontal_flip();
            if (entry_tiles[tile].flip_y) jo_sprite_enable_vertical_flip();
            /* Objects share the plane's endpoint-aligned 384->352 rule
               (street_out_of), then shift into Jo's centered space; the
               centered fit_352 sat 1 px left of the plane mapping for
               6,761 of the 12,118 scheduled objects (measured). */
            jo_sprite_draw3D(sprite_id,
                             street_out_of((int)(x & 0x3FF) - 64 +
                                           entry_tiles[tile].dx + 8) - 176,
                             (int)(y & 0x3FF) - 16 +
                                 entry_tiles[tile].dy + 8 - 112,
                             priority >= 4 ? 120 : 240);
            if (entry_tiles[tile].flip_x)
                jo_sprite_disable_horizontal_flip();
            if (entry_tiles[tile].flip_y)
                jo_sprite_disable_vertical_flip();
            ++drawn;
        }
    }
    avsp_diag_street_objects = drawn;
    avsp_diag_street_frame = rel;
    ++frame_counter;
}
#endif

static void draw_world(void)
{
    int index;
    int player_x = cap_actor_screen_x(world.player.x, world.camera_x, 1);
    int background_scroll = cap_background_fit_scroll_x(
        world.camera_x, world.stage_area);

    /* Per-frame evidence: states that draw no frontend objects must report
     * zero rather than the previous state's count. */
    frontend_runtime.vdp1_commands_last_frame = 0;

    if (world.encounter_state == CAP_ENCOUNTER_MAIN_MENU ||
        world.encounter_state == CAP_ENCOUNTER_START_TRANSITION ||
        world.encounter_state == CAP_ENCOUNTER_CHARACTER_SELECT ||
        world.encounter_state == CAP_ENCOUNTER_CHARACTER_CONFIRM)
    {
        int scene = world.encounter_state == CAP_ENCOUNTER_MAIN_MENU ? 0 : 1;
        int cursor_visible = 1;
        if (!activate_frontend_scene(scene)) runtime_ready = 0;
        if (world.encounter_state == CAP_ENCOUNTER_MAIN_MENU)
            avsp_frontend_draw_title(&frontend_runtime);
        else if (world.encounter_state == CAP_ENCOUNTER_START_TRANSITION)
            avsp_frontend_draw_start_transition(
                &frontend_runtime, world.encounter_timer);
        else
        {
            /* The measured blink: the markers first vanish three frames
             * after the confirm input, alternate every four frames, and
             * retire permanently after their fourth visible window - the
             * complete captured confirm interval shows no marker from
             * frames-since-input 27 onward. cap_confirm_character() zeroes
             * encounter_timer on the confirm step and
             * cap_update_encounter() increments it in that same step, so
             * frames since input is encounter_timer - 1. */
            if (world.encounter_state == CAP_ENCOUNTER_CHARACTER_CONFIRM &&
                world.encounter_timer - 1 >= 3)
                cursor_visible = world.encounter_timer - 1 < 27 &&
                    (((world.encounter_timer - 1 - 3) / 4) & 1) != 0;
            avsp_frontend_draw_cursor(
                &frontend_runtime, world.selection_cursor,
                world.encounter_timer, cursor_visible);
            /* The Round 1 title text appears over the shutter-blacked
             * screen 171 frames after the confirm input and fades in
             * through the source's own sixteen measured palette rows. */
            if (world.encounter_state == CAP_ENCOUNTER_CHARACTER_CONFIRM &&
                world.encounter_timer - 1 >= AVSP_FRONTEND_R1TEXT_CONFIRM_FRAME)
            {
                avsp_frontend_set_r1text_fade(
                    &frontend_runtime, world.encounter_timer - 1 -
                        AVSP_FRONTEND_R1TEXT_CONFIRM_FRAME);
                avsp_frontend_draw_round1_text(&frontend_runtime);
            }
        }
        if (world.encounter_state == CAP_ENCOUNTER_CHARACTER_CONFIRM)
            apply_confirm_shutter();
        return;
    }
    if (world.encounter_state == CAP_ENCOUNTER_ROUND_TITLE)
    {
        /* Measured Round 1 title: the text stays over the shutter-blacked
         * bitmap until the street scene pops in at frame 35, and clears
         * instantly at frame 90. The scene itself is the native street
         * renderer below, not a captured picture. */
        if (world.encounter_timer < AVSP_FRONTEND_R1TEXT_CLEAR_FRAME)
            avsp_frontend_draw_round1_text(&frontend_runtime);
        if (world.encounter_timer < AVSP_FRONTEND_R1SCENE_POP_FRAME)
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
        else if (rom_actor_entry_counts[index] > 0 && tile_archive_ready)
            /* Body E: any ROM-driven actor renders from its own decoded
               object list; its capture cel stays unused as the
               regression/comparison path. */
            draw_rom_actor_tiles(enemy, index);
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
    /* Every frontend state, including the Start transition. The transition
     * is drawn by the frontend over the title surface and the ROM shows no
     * gameplay HUD across it; reading the live VDP1 list at held transition
     * frames caught the arcade HUD emitting two to three sprites there. */
    if (world.encounter_state == CAP_ENCOUNTER_MAIN_MENU ||
        world.encounter_state == CAP_ENCOUNTER_START_TRANSITION ||
        world.encounter_state == CAP_ENCOUNTER_CHARACTER_SELECT ||
        world.encounter_state == CAP_ENCOUNTER_CHARACTER_CONFIRM ||
        sequence_scene_for_world() >= 0)
        return;
    /* The source writes the gameplay HUD tilemap 32 frames into the Round 1
       title, three frames before the street scene pops in. */
    if (world.encounter_state == CAP_ENCOUNTER_ROUND_TITLE &&
        world.encounter_timer < AVSP_FRONTEND_R1HUD_FRAME)
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
    /* Prove both contact composites without sacrificing deterministic route
       completion: accept one normal hit, arm the next contact as lethal, then
       restore the diagnostic's usual invulnerability after the KO cue fires. */
    if (contact_audio_play_count > 0 && ko_contact_audio_play_count == 0)
        world.player.health = CAP_ENEMY_CONTACT_DAMAGE;
    else
        world.player.health = CAP_PLAYER_MAX_HEALTH;
    if (world.encounter_state == CAP_ENCOUNTER_WAVE_ONE ||
        world.encounter_state == CAP_ENCOUNTER_WAVE_TWO ||
        world.encounter_state == CAP_ENCOUNTER_BOSS)
    {
        if (world.encounter_state == CAP_ENCOUNTER_BOSS &&
            world.encounter_timer < 600)
            return input;
        /* Exercise the natural 40-frame Chrysalis hit clip before the
           diagnostic starts its deterministic one-hit clear. One B edge at
           timer 600 lands at the captured melee contact offset; keeping four
           health leaves the boss alive at one health for the full reaction. */
        if (world.encounter_state == CAP_ENCOUNTER_BOSS &&
            world.encounter_timer < 680)
        {
            CapActor *boss = &world.enemies[0];
            boss->x = world.player.x + 34;
            boss->lane = world.player.lane;
            if (boss->action != CAP_ACT_HIT) boss->health = 4;
            if (world.encounter_timer == 600)
                input.attack_pressed = 1;
            return input;
        }
        /* Keep the five-enemy opening wave visible long enough to inspect
           after a real BIOS/CD boot before the automated clear begins. */
        if (world.frame >= 600)
        {
            for (index = 0; index < CAP_MAX_ENEMIES; ++index)
            {
                CapActor *enemy = &world.enemies[index];
                if (!enemy->active || enemy->action == CAP_ACT_KO) continue;
                if (ko_contact_audio_play_count > 0 &&
                    enemy->action == CAP_ACT_ATTACK)
                {
                    /* The diagnostic has already proven normal and KO
                       contact. Cancel later windups so the forced respawn is
                       not permanently hit-locked by six adjacent actors. */
                    enemy->action = CAP_ACT_IDLE;
                    enemy->action_frame = 0;
                    enemy->hit_latched = 0;
                }
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

#ifdef AVSP_FRONTEND_TEST
static CapInput frontend_test_input(void)
{
    CapInput input;
    memset(&input, 0, sizeof(input));
    if (world.encounter_state == CAP_ENCOUNTER_MAIN_MENU)
    {
        if (world.frame == 120) input.start_pressed = 1;
    }
    else if (world.encounter_state == CAP_ENCOUNTER_CHARACTER_SELECT)
    {
        /* Warrior -> Schaefer -> Hunter, with releases between source edges. */
        if (world.frame == 180) input.right = 1;
        if (world.frame == 200) input.down = 1;
        if (world.frame == 240) input.jump_pressed = 1;
    }
    return input;
}
#endif

#ifdef AVSP_FRONTEND_SHOT_TEST
/* Same source semantics as the focused frontend route, but keyed to the
 * encounter timer and extended to settle on every one of the four cursor
 * positions. The source has no cancel action, so the walk is right, down,
 * left, which visits Warrior, Schaefer, Hunter and Linn in turn. */
static CapInput frontend_shot_input(void)
{
    CapInput input;
    memset(&input, 0, sizeof(input));
    if (world.encounter_state == CAP_ENCOUNTER_MAIN_MENU)
    {
        if (avsp_shot_state_frames == 120) input.start_pressed = 1;
    }
    else if (world.encounter_state == CAP_ENCOUNTER_CHARACTER_SELECT)
    {
        if (avsp_shot_state_frames == 40) input.right = 1;
        if (avsp_shot_state_frames == 80) input.down = 1;
        if (avsp_shot_state_frames == 120) input.left = 1;
        if (avsp_shot_state_frames == 160) input.jump_pressed = 1;
    }
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
#ifndef AVSP_STREET_TEST
    /* MEASURED (write watchpoint, prnt_0 via jo_clear_screen_line): the
     * SGL ASCII text map lives at VDP2_VRAM_B0 (0x25E40000), which the
     * street test owns as the NBG0 pattern-name area. Clearing the text
     * screen every frame would space-fill the street map, so the street
     * profile never touches the SGL ASCII layer. */
    jo_clear_screen();
#endif
    avsp_diag_runtime_ready = runtime_ready;
    avsp_diag_encounter_state = (int)world.encounter_state;
    avsp_diag_world_frame = world.frame;
    if (!runtime_ready)
    {
        jo_printf(1, 12, "CAPABILITY TEST FAILED: %s", failed_asset == JO_NULL ? "UNKNOWN" : failed_asset);
        return;
    }
#ifdef AVSP_STREET_TEST
    street_test_frame();
    return;
#endif
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
#ifdef AVSP_FRONTEND_TEST
    input = frontend_test_input();
#endif
#ifdef AVSP_FRONTEND_SHOT_TEST
    input = frontend_shot_input();
#endif
#ifdef AVSP_BOSS_HIT_TEST
    /* Repeat the 40-frame reaction every two seconds so visual inspection is
       not timing-sensitive after the emulator's long CD preload. */
    if ((world.frame % 120) == 1)
    {
        world.enemies[0].action = CAP_ACT_HIT;
        world.enemies[0].action_frame = 0;
        world.enemies[0].hit_latched = 0;
    }
#endif
#ifdef AVSP_BOSS_KO_TEST
    /* Replay the complete lethal reaction and grounded-corpse hold on a
       timing-insensitive ten-second loop. After the complete 428-frame source
       motion, keep the last captured corpse frame visible for inspection;
       production builds retain the measured 60-frame hold. */
    if ((world.frame % 600) == 1)
    {
        CapActor *boss = &world.enemies[0];
        boss->x = 240;
        boss->lane = world.player.lane;
        boss->height = 0;
        boss->health = 0;
        boss->action = CAP_ACT_KO;
        boss->action_frame = 0;
        boss->hit_latched = 0;
        boss->active = 1;
        boss->kind = CAP_ACTOR_BOSS;
    }
    else if ((world.frame % 600) >=
                 avsp_boss_total_frames[AVSP_BOSS_CLIP_KO] &&
             (world.frame % 600) < 599)
    {
        CapActor *boss = &world.enemies[0];
        boss->action = CAP_ACT_KO;
        boss->action_frame =
            avsp_boss_total_frames[AVSP_BOSS_CLIP_KO] - 2;
        boss->active = 1;
    }
#endif
    /* Prepare one canonical ROM record before gameplay. cap_world_step() and
     * draw_world() therefore consume the same collision/render frame. */
#ifdef AVSP_FRONTEND_SHOT_TEST
    if (avsp_shot_should_hold())
    {
        /* Held: render the same frame again without advancing the world. */
        memset(&clip_request, 0, sizeof(clip_request));
    }
    else
#endif
    {
        rom_actor_prepare();
        clip_request = cap_world_step(&world, &input);
#ifdef AVSP_FRONTEND_SHOT_TEST
        if ((int)world.encounter_state != avsp_shot_state)
        {
            avsp_shot_state = (int)world.encounter_state;
            avsp_shot_state_frames = 0;
        }
        else
            ++avsp_shot_state_frames;
#endif
    }
    /* Start permanently leaves the title scene. Reuse its 78,848-byte RAM
       block for the 64,118-byte Stalker archive before character confirmation
       starts CDDA. This keeps the cold-boot working set unchanged and avoids
       any data-disc seek while Stage 1 music is playing. */
    if (world.encounter_state == CAP_ENCOUNTER_START_TRANSITION &&
        !frontend_runtime.select_surface_ready)
    {
        if (!avsp_frontend_enter_select(&frontend_runtime))
        {
            failed_asset = "ROM FRONTEND SELECT";
            runtime_ready = 0;
            return;
        }
        current_bitmap_scene = BITMAP_SCENE_NONE;
    }
    if (world.encounter_state == CAP_ENCOUNTER_CHARACTER_SELECT &&
        stalker_action_archive == JO_NULL)
    {
        if (!load_stalker_action_archive())
        {
            runtime_ready = 0;
            return;
        }
    }
    /* Body E note: the ROM tile archive is loaded during jo_main init (see
       the comment there) - by character select both cartridge banks are
       already nearly full. */
    /* Phase-boundary load: the Stage Clear composite arrives during the
       interior wipe, long before its BOSS_DEFEAT timer-150 play. The
       loading line is the standing pattern for stage-boundary CD reads:
       printed before the blocking read so it shows during the stall,
       cleared on the next frame. */
    if (world.encounter_state == CAP_ENCOUNTER_INTERIOR_TRANSITION &&
        boss_clear_sound.data == JO_NULL)
    {
        int loaded;
        /* The breach cue's natural WAVE_ONE release is gated on the channel
           going idle, but slPCMStat can stay asserted forever after a finite
           buffer elapses on Yaba Sanshiro (the withdraw path documents the
           same quirk), leaving its 298 KB block held. The breach source is
           long finished by the interior wipe, so close and reclaim it
           unconditionally here - it is the top-of-zone block whose free
           rolls the bump pointer back for the load below. */
        if (breach_sound.data != JO_NULL)
        {
            if (jo_audio_is_channel_playing(AVSP_PCM_CHANNEL_OPENING))
            {
                jo_audio_stop_sound(&breach_sound);
                slSndFlush();
            }
            release_pcm_data(&breach_sound);
        }
        /* Reclaim any trailing run of freed blocks into bump space; jo_free
           alone rolls back only a block directly adjacent to the pointer. */
        jo_reduce_memory_fragmentation();
        /* The interior wipe is the declared legal seek window: stage CDDA
           is paused for the wipe (the start call itself is still disabled,
           so today this encodes the contract skeleton - ADAPTED until the
           CD track start returns), the one bounded load runs inside an
           explicit measured window, and music ownership is restored after.
           Reads outside declared windows after the music point are
           rejected and counted by the guard. */
        avsp_disc_guard_cdda_stopped(&avsp_disc_guard_state);
        if (!avsp_disc_guard_window_begin(&avsp_disc_guard_state,
                                          "interior wipe: CDDA paused"))
        {
            failed_asset = "DISC WINDOW";
            runtime_ready = 0;
            return;
        }
        jo_printf(15, 13, "NOW LOADING");
        loaded = load_pcm_audio(&boss_clear_sound, AVSP_BOSS_CLEAR_PCM_FILE,
                                AVSP_BOSS_CLEAR_PCM_DIRECTORY,
                                AVSP_BOSS_CLEAR_PCM_BYTES,
                                AVSP_BOSS_CLEAR_PCM_SAMPLE_RATE);
        jo_printf(15, 13, "           ");
        avsp_disc_guard_window_end(&avsp_disc_guard_state);
        avsp_disc_guard_cdda_started(&avsp_disc_guard_state);
        if (!loaded)
        {
            runtime_ready = 0;
            return;
        }
    }
    /* Character confirmation keeps the already-copied selection pixels in
       VDP2, so its 78,848-byte source block can return to the allocator for
       the stage. The Chrysalis boss is composed from ROM tables and needs no
       archive, so nothing is loaded here (release_frontend_scene is
       idempotent). */
    if (world.encounter_state == CAP_ENCOUNTER_ROUND_TITLE &&
        world.encounter_timer >= AVSP_FRONTEND_R1TEXT_CLEAR_FRAME)
        release_frontend_scene(1);
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
        play_pcm_committed(&weapon_sound, &weapon_sound,
                           AVSP_PCM_CHANNEL_WEAPON);
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
        play_pcm_committed(&melee_sound, &melee_sound,
                           AVSP_PCM_CHANNEL_MELEE);
        melee_audio_pending = 0;
        ++melee_audio_play_count;
    }
    if (melee_audio_play_count > 0 &&
        jo_audio_is_channel_playing(melee_sound.current_playing_channel))
        melee_audio_channel_observed = 1;
    /* Each contact composite is a paired QSound capture of impact at +2 and
       the shared player vocal at +3. One SCSP start preserves that internal
       offset without issuing fragile back-to-back stereo upload commands. */
    if ((world.player.action == CAP_ACT_HIT ||
         world.player.action == CAP_ACT_KO) &&
        world.player.action_frame == 2)
    {
        jo_sound *next_contact = world.player.action == CAP_ACT_KO ?
                                 &ko_contact_sound : &contact_sound;
        play_pcm_committed(next_contact, contact_channel_sound,
                           AVSP_PCM_CHANNEL_CONTACT);
        contact_channel_sound = next_contact;
        if (world.player.action == CAP_ACT_KO)
            ++ko_contact_audio_play_count;
        else
            ++contact_audio_play_count;
    }
    if ((contact_audio_play_count > 0 || ko_contact_audio_play_count > 0) &&
        jo_audio_is_channel_playing(AVSP_PCM_CHANNEL_CONTACT))
        contact_audio_channel_observed = 1;
    /* The boss-room voice starts eight CPS2 frames after the captured room
       entry. The defeat/Stage Clear composite begins 150 frames after the
       Chrysalis defeat and deliberately continues across the native
       BOSS_DEFEAT -> STAGE_CLEAR -> RESULTS boundaries. Both use one SCSP
       channel because the source events cannot overlap. */
    if (world.encounter_state == CAP_ENCOUNTER_BOSS_INTRO &&
        world.encounter_timer == 8 && boss_intro_audio_play_count == 0)
    {
        play_pcm_committed(&boss_intro_sound, sequence_channel_sound,
                           AVSP_PCM_CHANNEL_SEQUENCE);
        sequence_channel_sound = &boss_intro_sound;
        ++boss_intro_audio_play_count;
    }
    if (world.encounter_state == CAP_ENCOUNTER_BOSS_DEFEAT &&
        world.encounter_timer == 150 && boss_clear_audio_play_count == 0 &&
        boss_clear_sound.data != JO_NULL)
    {
        play_pcm_committed(&boss_clear_sound, sequence_channel_sound,
                           AVSP_PCM_CHANNEL_SEQUENCE);
        sequence_channel_sound = &boss_clear_sound;
        ++boss_clear_audio_play_count;
    }
    if ((boss_intro_audio_play_count > 0 || boss_clear_audio_play_count > 0) &&
        jo_audio_is_channel_playing(AVSP_PCM_CHANNEL_SEQUENCE))
        sequence_audio_channel_observed = 1;
    /* The doorway voice and following transition effect are source-sequential,
       so one bounded SCSP channel reproduces both without consuming the final
       available slot. Their native state timers are aligned to source frames
       5384 (+44 from the doorway anchor) and 5438 (+38 from the interior
       transition anchor). */
    if (world.encounter_state == CAP_ENCOUNTER_DOOR_DIALOGUE &&
        world.encounter_timer == 44 && door_dialogue_audio_play_count == 0)
    {
        play_pcm_committed(&door_dialogue_sound, transition_channel_sound,
                           AVSP_PCM_CHANNEL_TRANSITION);
        transition_channel_sound = &door_dialogue_sound;
        ++door_dialogue_audio_play_count;
    }
    if (world.encounter_state == CAP_ENCOUNTER_INTERIOR_TRANSITION &&
        world.encounter_timer == 38 &&
        interior_transition_audio_play_count == 0)
    {
        play_pcm_committed(&interior_transition_sound,
                           transition_channel_sound,
                           AVSP_PCM_CHANNEL_TRANSITION);
        transition_channel_sound = &interior_transition_sound;
        ++interior_transition_audio_play_count;
    }
    if ((door_dialogue_audio_play_count > 0 ||
         interior_transition_audio_play_count > 0) &&
        jo_audio_is_channel_playing(AVSP_PCM_CHANNEL_TRANSITION))
        transition_audio_channel_observed = 1;
    /* Character confirmation occurs at source frame 1800. The first Round 1
       cue starts 231 frames later, nine frames before the sampled title card;
       the second starts at title timer 36. The withdraw and breach composites
       then start at barricade timers 95 and 259. Their source windows never
       overlap, so all four reuse the final bounded Jo/SGL PCM channel. */
    if (world.encounter_state == CAP_ENCOUNTER_CHARACTER_CONFIRM &&
        world.encounter_timer == 231 &&
        round_title_a_audio_play_count == 0)
    {
        play_pcm_committed(&round_title_a_sound, opening_channel_sound,
                           AVSP_PCM_CHANNEL_OPENING);
        opening_channel_sound = &round_title_a_sound;
        ++round_title_a_audio_play_count;
    }
    if (world.encounter_state == CAP_ENCOUNTER_ROUND_TITLE &&
        world.encounter_timer == 36 && round_title_b_audio_play_count == 0)
    {
        /* The first title cue has completed. Its main-RAM copy is no longer
           needed after SGL reports the shared opening channel idle. */
        if (!jo_audio_is_channel_playing(AVSP_PCM_CHANNEL_OPENING))
            release_pcm_data(&round_title_a_sound);
        play_pcm_committed(&round_title_b_sound, opening_channel_sound,
                           AVSP_PCM_CHANNEL_OPENING);
        opening_channel_sound = &round_title_b_sound;
        ++round_title_b_audio_play_count;
    }
    if (world.encounter_state == CAP_ENCOUNTER_BARRICADE_INTRO &&
        world.encounter_timer == 95 && withdraw_audio_play_count == 0)
    {
        if (!jo_audio_is_channel_playing(AVSP_PCM_CHANNEL_OPENING))
        {
            release_pcm_data(&round_title_a_sound);
            release_pcm_data(&round_title_b_sound);
        }
        play_pcm_committed(&withdraw_sound, opening_channel_sound,
                           AVSP_PCM_CHANNEL_OPENING);
        opening_channel_sound = &withdraw_sound;
        ++withdraw_audio_play_count;
    }
    if (world.encounter_state == CAP_ENCOUNTER_BARRICADE_INTRO &&
        world.encounter_timer == 259 && breach_audio_play_count == 0)
    {
        /* The source withdrawal composite ends at barricade timer 228. Free
           that 396 KiB block and reuse it as the complete eight-slot alien
           decode pool before the breach reveals the first playable wave. */
        /* slPCMStat can remain asserted after the finite source buffer has
           elapsed on Yaba Sanshiro. The capture has already been silent for
           31 source frames here, so explicitly close and flush the slot before
           returning its main-RAM buffer to the phase overlay. */
        if (jo_audio_is_channel_playing(AVSP_PCM_CHANNEL_OPENING))
        {
            jo_audio_stop_sound(&withdraw_sound);
            slSndFlush();
        }
        release_pcm_data(&round_title_a_sound);
        release_pcm_data(&round_title_b_sound);
        release_pcm_data(&withdraw_sound);
        if (!prepare_enemy_runtime())
        {
            runtime_ready = 0;
            return;
        }
        play_pcm_committed(&breach_sound, opening_channel_sound,
                           AVSP_PCM_CHANNEL_OPENING);
        opening_channel_sound = &breach_sound;
        ++breach_audio_play_count;
    }
    if ((round_title_a_audio_play_count > 0 ||
         round_title_b_audio_play_count > 0 ||
         withdraw_audio_play_count > 0 || breach_audio_play_count > 0) &&
        jo_audio_is_channel_playing(AVSP_PCM_CHANNEL_OPENING))
        opening_audio_channel_observed = 1;
    if (world.encounter_state == CAP_ENCOUNTER_WAVE_ONE &&
        breach_sound.data != JO_NULL &&
        !jo_audio_is_channel_playing(AVSP_PCM_CHANNEL_OPENING))
        release_pcm_data(&breach_sound);
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
        /* Boot-bringup probe: the second boot wall is ST 3 / T 2 - exactly
         * when this CD-DA start command fires - matching a CDC command
         * ACK spin. Disabled to test; stage music returns once the CD
         * track start is made non-blocking or the cue layout is fixed. */
        /* jo_audio_play_cd_track(2, 2, true); */
        stage_music_started = 1;
        avsp_frontend_lock_disc_reads(&frontend_runtime);
        /* The data-read guard mirrors the frontend lock: from here the
           drive belongs to CDDA (the start call is temporarily disabled,
           but the residency contract is enforced as if it were live). */
        avsp_disc_guard_cdda_started(&avsp_disc_guard_state);
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
    /* Boot-bringup breadcrumb: encounter state + timer heartbeat. The
     * staged boot into WAVE_ONE is now verified, so this no longer runs
     * unconditionally - it drew over the frontend surfaces the visual
     * comparison pass captures. Kept behind the debug HUD toggle because
     * it still distinguishes "stuck inside a draw/load call" from "state
     * machine never transitions". */
    if (debug_hud_enabled)
    {
        jo_printf(0, 0, "ST %d T %d F %d   ",
                  (int)world.encounter_state, (int)world.encounter_timer,
                  (int)world.frame);
    }
    /* Rows 24/25: draw_hud() runs after this and rewrites rows 0-7, so a
     * diagnostic printed on row 2 was overwritten in the same frame - it could
     * never be read back. These two rows are clear of every overlay. */
    if (debug_hud_enabled && rom_actor_entry_count > 0)
    {
        jo_printf(0, 24, "ROM n=%d code=%04x MISS %d/%d/%d POOL %d    ",
                  rom_actor_entry_count, rom_actor_entries[0].code,
                  tile_diag_no_bank, tile_diag_no_rank, tile_diag_no_sprite,
                  tile_pool_used);
        jo_printf(0, 25, "COLL N%d/%d G%d/%d C%d/%d H%d/%d    ",
                  rom_collision_no_hurt_frame, rom_collision_no_hurt,
                  rom_collision_gap_frame, rom_collision_gap,
                  rom_class_lookup_miss_frame, rom_class_lookup_miss,
                  cap_rom_box_hits, cap_approx_hits);
    }
    draw_world();
    rom_actor_advance();
    draw_arcade_hud();
    draw_route_overlay();
    draw_hud();
#ifdef AVSP_ENCOUNTER_TEST
    /* Draw test evidence last so captured VDP1 actors cannot obscure it. */
    jo_printf(0, 4, "PCM OPEN %d%d%d%d CH %d SEEN %d",
              round_title_a_audio_play_count,
              round_title_b_audio_play_count,
              withdraw_audio_play_count, breach_audio_play_count,
              jo_audio_is_channel_playing(AVSP_PCM_CHANNEL_OPENING),
              opening_audio_channel_observed);
    jo_printf(0, 5, "PCM D/T %d/%d CH %d SEEN %d",
              door_dialogue_audio_play_count,
              interior_transition_audio_play_count,
              jo_audio_is_channel_playing(AVSP_PCM_CHANNEL_TRANSITION),
              transition_audio_channel_observed);
    jo_printf(0, 6, "PCM SEQ %d/%d CH %d SEEN %d",
              boss_intro_audio_play_count, boss_clear_audio_play_count,
              jo_audio_is_channel_playing(AVSP_PCM_CHANNEL_SEQUENCE),
              sequence_audio_channel_observed);
    jo_printf(0, 7, "PCM CONTACT %d/%d SEEN %d",
              contact_audio_play_count, ko_contact_audio_play_count,
              contact_audio_channel_observed);
    jo_printf(0, 8, "PCM SHOT %d PLAYED %d CH %d SEEN %d",
              world.shots_fired, weapon_audio_played_shots,
              jo_audio_is_channel_playing(
                  weapon_sound.current_playing_channel),
              weapon_audio_channel_observed);
    jo_printf(0, 9, "PCM MELEE %d CH %d SEEN %d",
              melee_audio_play_count,
              jo_audio_is_channel_playing(melee_sound.current_playing_channel),
              melee_audio_channel_observed);
    jo_printf(0, 10, "ENCOUNTER %d KO %d/%d ACTIVE %d EXIT %d LVL %d",
              world.encounter_state, world.enemies_defeated,
              CAP_STAGE1_TOTAL_ENEMIES, active_enemy_count(),
              world.stage_transitioned, world.level_completed);
    jo_printf(0, 11, "FRONT SEL %d CUR %d ADAPT %d LATE %d MISS %d",
              world.selected_character, world.selection_cursor,
              world.adapted_character_fallbacks,
              frontend_runtime.late_disc_reads,
              frontend_runtime.missing_assets);
    jo_printf(0, 12, "FRONT RLE %d PAL %d CMD %d",
              frontend_runtime.rle_errors, frontend_runtime.palette_errors,
              frontend_runtime.vdp1_commands_last_frame);
#endif
#ifdef AVSP_VISUAL_TEST
    jo_printf(0, 5, "VISUAL A%d P%02d/%02d E%d:%03d/%02d",
              world.player.action, world.player.action_frame,
              current_player_action_pose,
              visual_enemy_action_index, visual_enemy_frame,
              current_enemy_action_poses[0]);
#endif
#ifdef AVSP_BOSS_HIT_TEST
    jo_printf(0, 20, "BOSS HIT A%d F%02d P%02d HP %02d",
              world.enemies[0].action, world.enemies[0].action_frame,
              current_boss_action_pose, world.enemies[0].health);
#endif
#ifdef AVSP_BOSS_KO_TEST
    jo_printf(0, 20, "BOSS KO A%d F%03d P%02d LIVE %d",
              world.enemies[0].action, world.enemies[0].action_frame,
              current_boss_action_pose, world.enemies[0].active);
#endif
    avsp_diag_runtime_ready = runtime_ready;
    avsp_diag_encounter_state = (int)world.encounter_state;
    avsp_diag_world_frame = world.frame;
    avsp_diag_selected_character = (int)world.selected_character;
    avsp_diag_selection_cursor = world.selection_cursor;
    avsp_diag_encounter_timer = (int)world.encounter_timer;
    avsp_diag_background_bitmap = (int)background_bitmap;
    avsp_diag_frontend_late_reads = frontend_runtime.late_disc_reads;
    avsp_diag_frontend_missing_assets = frontend_runtime.missing_assets;
    avsp_diag_frontend_rle_errors = frontend_runtime.rle_errors;
    avsp_diag_frontend_palette_boundary_writes =
        frontend_runtime.palette_boundary_writes;
    avsp_diag_frontend_palette_errors = frontend_runtime.palette_errors;
    avsp_diag_frontend_commands = frontend_runtime.vdp1_commands_last_frame;
}

void jo_main(void)
{
    int index;
    failed_asset = JO_NULL;
    avsp_disc_guard_init(&avsp_disc_guard_state);
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
    contact_audio_play_count = 0;
    ko_contact_audio_play_count = 0;
    contact_audio_channel_observed = 0;
    contact_channel_sound = JO_NULL;
    boss_intro_audio_play_count = 0;
    boss_clear_audio_play_count = 0;
    sequence_audio_channel_observed = 0;
    sequence_channel_sound = JO_NULL;
    door_dialogue_audio_play_count = 0;
    interior_transition_audio_play_count = 0;
    transition_audio_channel_observed = 0;
    transition_channel_sound = JO_NULL;
    round_title_a_audio_play_count = 0;
    round_title_b_audio_play_count = 0;
    withdraw_audio_play_count = 0;
    breach_audio_play_count = 0;
    opening_audio_channel_observed = 0;
    opening_channel_sound = JO_NULL;
    enemy_action_buffer = JO_NULL;
    enemy_runtime_ready = 0;
    boss_action_image.data = JO_NULL;
    boss_runtime_ready = 0;
    current_bitmap_scene = BITMAP_SCENE_NONE;
#ifdef AVSP_VISUAL_TEST
    visual_action_index = 0;
    visual_walk_frames = 0;
    visual_enemy_action_index = 0;
    visual_enemy_frame = 0;
    debug_hud_enabled = 1;
#endif
#ifdef AVSP_FRONTEND_TEST
    debug_hud_enabled = 1;
#endif
#ifdef AVSP_FRONTEND_SHOT_TEST
    /* The visual pass compares frontend surfaces; keep the debug text off. */
    debug_hud_enabled = 0;
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
           runtime can use the cartridge's complete 4 MiB capacity. The
           first AVSP_TILE_REGION_BYTES are carved out for the ROM tile
           archive and stay outside the allocator. */
        jo_add_memory_zone(AVSP_CART_DRAM1_BASE + AVSP_TILE_REGION_BYTES +
                               AVSP_STRIPS_REGION_BYTES,
                           AVSP_CART_DRAM1_BYTES - AVSP_TILE_REGION_BYTES -
                               AVSP_STRIPS_REGION_BYTES);
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
        /* The ROM tile archive loads FIRST: it needs one ~200 KB
           contiguous cartridge block, and the boot asset sweep below
           fills both cartridge banks nearly to capacity (the measured
           post-boot free space is under 130 KB per bank). No CDDA is
           active at init, so the early read is seek-safe. */
        runtime_ready = load_tile_archive() &&
                        load_route_sequences() &&
                        load_background() && load_boss_background() &&
                        load_frontend_assets() &&
                        load_hud_assets() &&
                        load_action_audio() &&
                        load_all_cels() && load_player_action_sequences() &&
                        load_enemy_action_archive() &&
                        create_sprite_working_set() &&
                        avsp_frontend_load_title_objects(&frontend_runtime) &&
                        /* LAST on purpose: the opening overlay's ~900 KB must
                           sit at the top of its zone so its release rolls the
                           bump pointer back for the BOSSCLR.PCM phase load
                           (see load_opening_audio). */
                        load_opening_audio();
    }
#ifdef AVSP_VISUAL_TEST
    if (runtime_ready)
    {
        /* The visual loop starts directly in combat and never consumes the
           frontend opening cues, so release their overlay immediately. */
        release_pcm_data(&round_title_a_sound);
        release_pcm_data(&round_title_b_sound);
        release_pcm_data(&withdraw_sound);
        release_pcm_data(&breach_sound);
        runtime_ready = prepare_enemy_runtime();
    }
#endif
#if defined(AVSP_BOSS_HIT_TEST) || defined(AVSP_BOSS_KO_TEST)
    if (runtime_ready)
    {
        /* Focused boss diagnostics bypass the frontend, so the main loop's
           CHARACTER_SELECT/CONFIRM scene releases are skipped; free those
           lifetime assets here to leave room for the stage working set. The
           boss itself is composed from ROM tables and needs no archive. */
        release_frontend_scene(0);
        release_frontend_scene(1);
        release_pcm_data(&round_title_a_sound);
        release_pcm_data(&round_title_b_sound);
        release_pcm_data(&withdraw_sound);
        release_pcm_data(&breach_sound);
        /* The four frees above are not last-in-first-out, so only the final
           one rolled the bump pointer back; compact the rest of the trailing
           free run before the large allocation below. */
        jo_reduce_memory_fragmentation();
        /* These profiles skip the interior transition where the Stage
           Clear composite is phase-loaded; load it here instead so a
           forced BOSS_DEFEAT still plays it. */
        if (runtime_ready)
            runtime_ready = load_pcm_audio(
                &boss_clear_sound, AVSP_BOSS_CLEAR_PCM_FILE,
                AVSP_BOSS_CLEAR_PCM_DIRECTORY, AVSP_BOSS_CLEAR_PCM_BYTES,
                AVSP_BOSS_CLEAR_PCM_SAMPLE_RATE);
    }
#endif
    cap_world_init(&world);
#if defined(AVSP_BOSS_HIT_TEST) || defined(AVSP_BOSS_KO_TEST)
    world.encounter_started = 1;
    world.encounter_state = CAP_ENCOUNTER_BOSS;
    world.room_locked = 1;
    world.stage_area = 1;
#ifdef AVSP_BOSS_KO_TEST
    world.boss_reinforcement_wave = 2;
#endif
    world.frame = 1;
    world.player.x = 170;
    world.player.lane = 182;
    for (index = 0; index < CAP_MAX_ENEMIES; ++index)
        world.enemies[index].active = 0;
    world.enemies[0].x = 240;
    world.enemies[0].lane = world.player.lane;
    world.enemies[0].height = 0;
    world.enemies[0].facing = -1;
    world.enemies[0].health =
#ifdef AVSP_BOSS_KO_TEST
        0;
    world.enemies[0].action = CAP_ACT_KO;
#else
        21;
    world.enemies[0].action = CAP_ACT_HIT;
#endif
    world.enemies[0].action_frame = 0;
    world.enemies[0].active = 1;
    world.enemies[0].kind = CAP_ACTOR_BOSS;
    debug_hud_enabled = 1;
#elif defined(AVSP_VISUAL_TEST)
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
