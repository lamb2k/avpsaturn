/* First read at 0x06004000: map the cart, load segments from disc, enter the runtime. Lifted code never sees GFS. */
#include "SEGA_GFS.H"
#define LOADER_DIAG ((volatile unsigned long *)0x06013fe0u)
#define ENTRY 0x06014000u
extern unsigned char _bstart, _bend;
static unsigned char gfs_work[GFS_WORK_SIZE(1)];
static GfsDirTbl dir;
static GfsDirName names[16];
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
    GFS_DIRTBL_NDIR(&dir) = 16;
    if (GFS_Init(1, gfs_work, &dir) < 0) halt(0xe001, 0);
    load("LW.BIN", (void *)0x00200000u, 0x100);
    load("ROM.BIN", (void *)0x02400000u, 0x200);
    load("OPX.BIN", (void *)0x02600000u, 0x300);
    load("PACK.BIN", (void *)0x0264c000u, 0x500);
    load("COLD1.BIN", (void *)COLD1_ADDR, 0x600);
    load("HW.BIN", (void *)ENTRY, 0x400);
    GFS_Reset();
    *(volatile unsigned char *)0xfffffe92 = 0x10;
    *(volatile unsigned char *)0xfffffe92 = 0x01;
    ((void (*)(void))ENTRY)();
    return 0;
}
