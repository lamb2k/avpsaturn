#include "SEGA_GFS.H"

#define AVSP_GAME_LOAD_ADDRESS ((void *)0x06004000u)
#define AVSP_GAME_STAGING_ADDRESS ((void *)0x00200000u)
#define AVSP_TRAMPOLINE_ADDRESS ((void *)0x060D0000u)
#define AVSP_LOADER_DIAGNOSTICS ((volatile unsigned long *)0x060CFFF0u)
#define AVSP_LOADER_MAX_ROOT_FILES 128

extern unsigned char _bstart;
extern unsigned char _bend;
extern unsigned char avsp_trampoline_start;
extern unsigned char avsp_trampoline_end;

static unsigned char gfs_work[GFS_WORK_SIZE(1)];
static GfsDirTbl gfs_directory;
static GfsDirName gfs_names[AVSP_LOADER_MAX_ROOT_FILES];

static void loader_record(unsigned long status, unsigned long detail)
{
    AVSP_LOADER_DIAGNOSTICS[0] = 0x4156504Cu; /* AVPL */
    AVSP_LOADER_DIAGNOSTICS[1] = status;
    AVSP_LOADER_DIAGNOSTICS[2] = detail;
}

static void loader_clear_bss(void)
{
    unsigned char *cursor = &_bstart;

    while (cursor < &_bend)
        *cursor++ = 0;
}

static void loader_halt(unsigned long status, unsigned long detail)
{
    loader_record(status, detail);
    for (;;)
        __asm__ volatile ("nop");
}

int main(void)
{
    Sint32 file_count;
    Sint32 game_id;
    Sint32 loaded;
    GfsHn game;
    Sint32 sector_size;
    Sint32 sectors;
    Sint32 last_sector_size;
    Sint32 game_size;
    unsigned char *trampoline_source;
    unsigned char *trampoline_destination;
    unsigned long trampoline_size;
    void (*trampoline)(void *, void *, unsigned long);

    loader_clear_bss();
    loader_record(1u, 0u);

    GFS_DIRTBL_TYPE(&gfs_directory) = GFS_DIR_NAME;
    GFS_DIRTBL_DIRNAME(&gfs_directory) = gfs_names;
    GFS_DIRTBL_NDIR(&gfs_directory) = AVSP_LOADER_MAX_ROOT_FILES;
    file_count = GFS_Init(1, gfs_work, &gfs_directory);
    if (file_count < 0)
        loader_halt(0xE001u, (unsigned long)file_count);
    loader_record(2u, (unsigned long)file_count);

    game_id = GFS_NameToId((Sint8 *)"GAME.BIN");
    if (game_id < 0)
        loader_halt(0xE002u, (unsigned long)game_id);

    game = GFS_Open(game_id);
    if (game == (GfsHn)0)
        loader_halt(0xE003u, (unsigned long)game_id);
    GFS_GetFileSize(game, &sector_size, &sectors, &last_sector_size);
    GFS_Close(game);
    if (sectors <= 0 || sector_size <= 0 || last_sector_size <= 0)
        loader_halt(0xE004u, (unsigned long)sectors);
    game_size = sector_size * (sectors - 1) + last_sector_size;
    loader_record(3u, (unsigned long)game_size);

    loaded = GFS_Load(game_id, 0, AVSP_GAME_STAGING_ADDRESS, game_size);
    if (loaded <= 0)
        loader_halt(0xE005u, (unsigned long)loaded);
    loader_record(4u, (unsigned long)loaded);

    /* GAME.BIN starts a fresh SGL/Jo runtime. Do not carry this first-stage
       GFS instance across that boundary. */
    GFS_Reset();

    trampoline_source = &avsp_trampoline_start;
    trampoline_destination = (unsigned char *)AVSP_TRAMPOLINE_ADDRESS;
    trampoline_size = (unsigned long)(&avsp_trampoline_end -
                                      &avsp_trampoline_start);
    while (trampoline_size-- != 0u)
        *trampoline_destination++ = *trampoline_source++;

    loader_record(5u, (unsigned long)AVSP_GAME_LOAD_ADDRESS);
    trampoline = (void (*)(void *, void *, unsigned long))
        AVSP_TRAMPOLINE_ADDRESS;
    trampoline(AVSP_GAME_STAGING_ADDRESS, AVSP_GAME_LOAD_ADDRESS,
               (unsigned long)game_size);
    loader_halt(0xE006u, 0u);
    return 0;
}
