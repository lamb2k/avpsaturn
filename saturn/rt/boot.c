/* First read at 0x06004000: map the cart, load segments from disc, enter the runtime. Lifted code never sees GFS. */
#include "SEGA_GFS.H"
#define LOADER_DIAG ((volatile unsigned long *)0x06013fe0u)
#define LOADER_API ((volatile unsigned long *)0x06013fd0u)
#define ENTRY 0x06014000u
extern unsigned char _bstart, _bend;
static unsigned char gfs_work[GFS_WORK_SIZE(1)];
static GfsDirTbl dir;
static GfsDirName names[64];
static void halt(unsigned long s, unsigned long d) { LOADER_DIAG[0] = 0x4156504c; LOADER_DIAG[1] = s; LOADER_DIAG[2] = d; for (;;) __asm__ volatile ("nop"); }
static void load(const char *name, void *dest, unsigned long code)
{
    Sint32 id = GFS_NameToId((Sint8 *)name), ss, n, last, got;
    GfsHn h;
    if (id < 0) halt(code | 1, (unsigned long)id);
    h = GFS_Open(id);
    if (!h) halt(code | 2, 0);
    GFS_GetFileSize(h, &ss, &n, &last);
    GFS_SetTmode(h, GFS_TMODE_CPU);
    got = GFS_Fread(h, n, dest, ss * n);
    GFS_Close(h);
    if (got <= 0) halt(code | 3, (unsigned long)got);
    LOADER_DIAG[3] = code; LOADER_DIAG[4] = (unsigned long)got;
}
/* Between rounds the runtime calls this through LOADER_API (lifted code never does): one file of whole sectors, its first sector a list of
   u32 count, then count pairs of u32 destination, u32 bytes (multiples of 2048), destination 1 being a call to mark. The caller has masked interrupts and stopped the slave. Returns sectors read, or a negative stage. */
static unsigned long load_head[512];
static long load_regions(const char *name, void (*mark)(void))
{
    Sint32 id, ss, n, last, got, total = 1;
    GfsHn h;
    unsigned long i;
    if (GFS_Init(1, gfs_work, &dir) < 0) return -1;
    id = GFS_NameToId((Sint8 *)name);
    if (id < 0) { GFS_Reset(); return -2; }
    h = GFS_Open(id);
    if (!h) { GFS_Reset(); return -3; }
    GFS_GetFileSize(h, &ss, &n, &last);
    GFS_SetTmode(h, GFS_TMODE_CPU);
    GFS_Fread(h, 1, load_head, 2048);
    for (i = 0; i < load_head[0]; i++) {
        Sint32 secs = (Sint32)(load_head[2 + i * 2] / 2048u);
        if (load_head[1 + i * 2] == 1) { mark(); continue; }   /* destination 1: what came before is ready, the caller takes it before later regions overwrite it */
        got = GFS_Fread(h, secs, (void *)load_head[1 + i * 2], secs * 2048);
        if (got != secs * 2048) { GFS_Close(h); GFS_Reset(); return -4 - (long)i; }
        total += secs;
    }
    GFS_Close(h);
    GFS_Reset();
    return total;
}
int main(void)
{
    unsigned char *c;
    volatile unsigned long *cart = (volatile unsigned long *)0x02700000u;
    for (c = &_bstart; c < &_bend; c++) *c = 0;
    /* A-bus timing and cart enable, as the 4 MB cart requires. */
    *(volatile unsigned long *)0x25fe00b0 = 0x23301ff0;
    *(volatile unsigned long *)0x25fe00b8 = 0x00000013;
    *(volatile unsigned short *)0x257efffe = 1;
    cart[0] = 0x12345678; cart[1] = 0xedcba987;
    if (cart[0] != 0x12345678 || cart[1] != 0xedcba987) halt(0xe0f0, cart[0]);
    GFS_DIRTBL_TYPE(&dir) = GFS_DIR_NAME;
    GFS_DIRTBL_DIRNAME(&dir) = names;
    GFS_DIRTBL_NDIR(&dir) = 64;
    if (GFS_Init(1, gfs_work, &dir) < 0) halt(0xe001, 0);
    load("LW.BIN", (void *)0x00200000u, 0x100);
    load("ROM.BIN", (void *)0x02400000u, 0x200);
    load("OPX.BIN", (void *)0x02600000u, 0x300);
    load("COLD1.BIN", (void *)COLD1_ADDR, 0x600);
    load("HW.BIN", (void *)ENTRY, 0x400);
    GFS_Reset();
    LOADER_API[0] = (unsigned long)load_regions;
    *(volatile unsigned char *)0xfffffe92 = 0x10;
    *(volatile unsigned char *)0xfffffe92 = 0x01;
    ((void (*)(void))ENTRY)();
    return 0;
}
