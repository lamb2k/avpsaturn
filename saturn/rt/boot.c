/* First read at 0x06004000: map the cart, load segments from disc, enter the runtime. Lifted code never sees GFS. */
#include "SEGA_GFS.H"
#include "SEGA_BUP.H"
#include "unlock_save.h"
#define LOADER_DIAG ((volatile unsigned long *)0x06013fe0u)
#define LOADER_API ((volatile unsigned long *)0x06013fd0u)
#define ENTRY 0x06014000u
extern unsigned char _bstart, _bend;
static unsigned char gfs_work[GFS_WORK_SIZE(1)];
static GfsDirTbl dir;
static GfsDirName names[256];
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
#ifdef SECTOR_STORE
/* SECTOR_STORE (tools/sector_store.py): the round files live as runs of one shared STORE.BIN. RNNN.BIN names round NNN; its runs, read in order,
   are that file's sectors, so the walk below sees the same stream and the cart gets the same bytes. Adjacent runs were joined when packed. */
#ifdef STORE_HEAD2   /* guest builds: more than 255 rounds, a two-sector directory */
static unsigned long store_dir[1024], store_run[512];
#define STORE_HS (store_dir[1] > 255 ? 2 : 1)
#else
static unsigned long store_dir[512], store_run[512];
#define STORE_HS 1
#endif
static Sint32 run_at, run_left, run_sec = -1, run_next, run_end;
static Sint32 vread(GfsHn h, Sint32 secs, unsigned char *dest)
{
    while (secs) {
        Sint32 take, got;
        if (!run_left) {
            Sint32 s;
            if (run_next >= run_end) return -1;
            s = STORE_HS + run_next / 512;
            if (s != run_sec) {
                if (GFS_Seek(h, s, GFS_SEEK_SET) < 0 || GFS_Fread(h, 1, store_run, 2048) != 2048) return -2;
                run_sec = s;
            }
            run_at = (Sint32)(store_run[run_next % 512] >> 14); run_left = (Sint32)(store_run[run_next % 512] & 0x3fff); run_next++;
            if (GFS_Seek(h, run_at, GFS_SEEK_SET) < 0) return -3;
        }
        take = secs < run_left ? secs : run_left;
        got = GFS_Fread(h, take, dest, take * 2048);
        if (got != take * 2048) return -4;
        run_at += take; run_left -= take; secs -= take; dest += take * 2048;
    }
    return 0;
}
static long load_regions(const char *name, void (*mark)(void))
{
    Sint32 id, total = 1, r = (name[1] - '0') * 100 + (name[2] - '0') * 10 + (name[3] - '0');
    GfsHn h;
    unsigned long i;
    if (GFS_Init(1, gfs_work, &dir) < 0) return -1;
    id = GFS_NameToId((Sint8 *)"STORE.BIN");
    if (id < 0) { GFS_Reset(); return -2; }
    h = GFS_Open(id);
    if (!h) { GFS_Reset(); return -3; }
    GFS_SetTmode(h, GFS_TMODE_CPU);
    /* The directory is read once and kept (the loader stays resident); so is a one-sector run table, so a load seeks only to its own runs. */
    if (store_dir[0] != 0x53535431u) {
        if (GFS_Fread(h, 1, store_dir, 2048) != 2048 || store_dir[0] != 0x53535431u) { store_dir[0] = 0; GFS_Close(h); GFS_Reset(); return -0x100; }
#ifdef STORE_HEAD2
        if (STORE_HS == 2 && GFS_Fread(h, 1, store_dir + 512, 2048) != 2048) { store_dir[0] = 0; GFS_Close(h); GFS_Reset(); return -0x100; }
#endif
        run_sec = -1;
    }
    if ((unsigned long)r >= store_dir[1]) { GFS_Close(h); GFS_Reset(); return -0x100; }
    run_next = (Sint32)store_dir[2 + r * 2]; run_end = run_next + (Sint32)store_dir[3 + r * 2]; run_left = 0;
    if (vread(h, 1, (unsigned char *)load_head)) { GFS_Close(h); GFS_Reset(); return -0x101; }
    for (i = 0; i < load_head[0]; i++) {
        Sint32 secs = (Sint32)(load_head[2 + i * 2] / 2048u);
        if (load_head[1 + i * 2] == 1) { mark(); continue; }
        if (vread(h, secs, (unsigned char *)load_head[1 + i * 2])) { GFS_Close(h); GFS_Reset(); return -4 - (long)i; }
        total += secs;
    }
    GFS_Close(h);
    GFS_Reset();
    return total;
}
#else
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
#endif
/* Any one file of the disc into RAM (the post-credits reveal reads its art and voice this way at the ending, kernel.c sat_reveal_call). The caller has masked interrupts and stopped the slave. Returns bytes read, or a negative stage. */
static long load_file(const char *name, void *dest)
{
    Sint32 id, ss, n, last, got;
    GfsHn h;
    if (GFS_Init(1, gfs_work, &dir) < 0) return -1;
    id = GFS_NameToId((Sint8 *)name);
    if (id < 0) { GFS_Reset(); return -2; }
    h = GFS_Open(id);
    if (!h) { GFS_Reset(); return -3; }
    GFS_GetFileSize(h, &ss, &n, &last);
    GFS_SetTmode(h, GFS_TMODE_CPU);
    got = GFS_Fread(h, n, dest, ss * n);
    GFS_Close(h);
    GFS_Reset();
    return got > 0 ? got : -4;
}
/* The unlock record in the Saturn's internal backup RAM, one 64 byte file through the BIOS backup library (unlock_save.h has the format and the rules).
   op 0 reads, 1 sets the flag bits, 2 clears them (the debug build's CLEAR UNLOCK). scratch: 24 KB of RAM nobody uses at that moment, 4 byte aligned (the library
   copies itself into the first 16 KB and keeps its work in the next 8 KB). The flags word LOADER_API[3] (bit 31 set once read, bit 0 Wolverine) is what the
   runtime reads; a set is in it before the write is tried, so a full or missing backup RAM still unlocks this power-on. A failed read leaves the flags clear (locked).
   The device is only formatted when the library says it is unformatted, never for any other state. Returns 0, or a negative stage. */
static long unlock_io(unsigned op, unsigned bits, unsigned char *scratch)
{
    static const Uint8 name[12] = { 'A', 'V', 'P', 'S', 'A', 'T', '_', 'S', 'A', 'V', 'E', 0 };
    BupConfig cfg[3];
    BupStat st;
    BupDir bd;
    BupDate when;
    unsigned char old[SAVE_SIZE], rec[SAVE_SIZE];
    unsigned have = 0, flags;
    long r;
    unsigned long vec = *(volatile unsigned long *)0x6000354, init = *(volatile unsigned long *)0x6000358;
    if (op == 1) LOADER_API[3] |= 0x80000000u | bits; else if (op == 2) LOADER_API[3] &= ~bits;
    if (vec < 0x100 || vec >= 0x80000 || init < 0x100 || init >= 0x80000) return -1;
    BUP_Init((volatile Uint32 *)scratch, (Uint32 *)(scratch + 0x4000), cfg);
    r = BUP_Stat(0, SAVE_SIZE, &st);
    if (r == BUP_UNFORMAT && op) { if (BUP_Format(0)) return -2; r = BUP_Stat(0, SAVE_SIZE, &st); }
    if (r) return -3;
    if (BUP_Dir(0, (Uint8 *)name, 1, &bd) > 0 && !BUP_Read(0, (Uint8 *)name, old)) have = SAVE_SIZE;
    flags = save_flags(old, have);
    if (!op) { LOADER_API[3] = 0x80000000u | flags; return 0; }
    save_merge(rec, old, have, op == 1 ? bits : 0, op == 2 ? bits : 0);
    for (r = 0; r < 12; r++) bd.filename[r] = name[r];
    for (r = 0; r < 11; r++) bd.comment[r] = "AVP SAVE   "[r];
    bd.comment[10] = 0;
    bd.language = BUP_ENGLISH;
    when.year = 17; when.month = 1; when.day = 1; when.time = 0; when.min = 0; when.week = 0;
    bd.date = BUP_SetDate(&when);
    bd.datasize = SAVE_SIZE;
    bd.blocksize = 0;
    return BUP_Write(0, &bd, rec, 0) ? -4 : 0;
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
    LOADER_API[1] = (unsigned long)load_file;
    LOADER_API[2] = (unsigned long)unlock_io;
    LOADER_API[3] = 0;
    LOADER_DIAG[5] = 0; LOADER_DIAG[6] = 0; LOADER_DIAG[7] = 0;   /* the reveal's takeover flag and state (reveal.c) */
    unlock_io(0, 0, (unsigned char *)ENTRY);   /* the unlock record, before the runtime lands on this RAM */
    cart[0] = 0x12345678; cart[1] = 0xedcba987;
    if (cart[0] != 0x12345678 || cart[1] != 0xedcba987) halt(0xe0f0, cart[0]);
    GFS_DIRTBL_TYPE(&dir) = GFS_DIR_NAME;
    GFS_DIRTBL_DIRNAME(&dir) = names;
    GFS_DIRTBL_NDIR(&dir) = 256;
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
