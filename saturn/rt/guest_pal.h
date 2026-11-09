/* Guest select-screen and HUD colours (saturn/rt/guests.c, tools/wolverine/hud_art.py). SAT_GUESTS builds only.
   The arcade loads these palettes from tables in its program ROM (32 bytes a table: pens 0 to 14 as 0RGB words, then a tag word), and the
   Saturn keeps that ROM image in cart RAM. While a guest's art files are the ones loaded, the guest's colours are written over the
   tables' pens (mask); otherwise the originals are written back. Writes happen only where the bytes differ, so a guest that is off
   (or has no art) never changes a byte. Plain C so a host test can run it over a buffer (tests/test_wolverine_hud_art.py). */
#ifndef SAT_GUEST_PAL_H
#define SAT_GUEST_PAL_H
typedef struct {
    unsigned char guest;           /* art bit of the guest (1 << its row in sat_guests[]) */
    unsigned short mask;           /* pens to replace, bit n = pen n (0 to 14) */
    const unsigned short *neu;     /* the guest's 15 words, 0RGB */
    const unsigned short *orig;    /* the arcade's 15 words */
    const unsigned long *at;       /* ROM offsets of every copy of the table */
    unsigned char n;               /* copies */
} GuestPal;

static void __attribute__((unused)) guest_pal_sync(const GuestPal *t, int count, unsigned art, volatile unsigned char *rom)
{
    int i, k, p;
    for (i = 0; i < count; i++) {
        const unsigned short *w = (art & t[i].guest) ? t[i].neu : t[i].orig;
        for (k = 0; k < t[i].n; k++)
            for (p = 0; p < 15; p++) {
                volatile unsigned char *d = rom + t[i].at[k] + (unsigned long)p * 2;
                unsigned char hi = (unsigned char)(w[p] >> 8), lo = (unsigned char)w[p];
                if (!((t[i].mask >> p) & 1)) continue;
                if (d[0] != hi) d[0] = hi;
                if (d[1] != lo) d[1] = lo;
            }
    }
}
#endif
