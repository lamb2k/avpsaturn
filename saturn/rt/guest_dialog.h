/* Wolverine's story box wording (saturn/rt/guests.c, tools/wolverine/dialog.py). SAT_WV_DIALOG builds only.
   The arcade's story box text is in its program ROM image as 16 bit cell codes (a record: 64 words; line 1 is words 7 to 34, line 2 words 36
   to 63), and the Saturn keeps that image in cart RAM. While Wolverine's stage files are the loaded ones, his lines are written over
   Schaefer's records, otherwise the originals are written back. Writes happen only where the bytes differ, so with the guest off the image
   is never changed. Plain C so a host test can run it over a buffer (tests/test_wolverine_dialog.py).
   dlg_data: per record: ROM offset of line 1 (4 bytes, big endian, 0 ends the list), then new line 1, new line 2, old line 1, old line 2, each a
   length byte and that many indices into the glyph table; the rest of the 28 cells is the blank cell 0x100. */
#ifndef SAT_GUEST_DIALOG_H
#define SAT_GUEST_DIALOG_H
typedef struct {
    unsigned long at;              /* ROM offset of the name field */
    unsigned char n;               /* field length */
    const unsigned char *neu;      /* Wolverine's name, padded */
    const unsigned char *orig;     /* the arcade's bytes */
} GuestName;

static void __attribute__((unused)) guest_dialog_sync(const unsigned char *p, const unsigned short *glyph, int on, volatile unsigned char *rom)
{
    for (;;) {
        unsigned long at = ((unsigned long)p[0] << 24) | ((unsigned long)p[1] << 16) | ((unsigned long)p[2] << 8) | p[3];
        int pass, line, i;
        p += 4;
        if (!at) break;
        for (pass = 0; pass < 2; pass++)
            for (line = 0; line < 2; line++) {
                unsigned n = *p++;
                const unsigned char *c = p;
                p += n;
                if (pass != !on) continue;           /* new lines when on, the originals when off */
                for (i = 0; i < 28; i++) {
                    unsigned short w = i < (int)n ? glyph[c[i]] : 0x100;
                    volatile unsigned char *d = rom + at + (unsigned long)line * 58 + (unsigned long)i * 2;
                    if (d[0] != (unsigned char)(w >> 8)) d[0] = (unsigned char)(w >> 8);
                    if (d[1] != (unsigned char)w) d[1] = (unsigned char)w;
                }
            }
    }
}

static void __attribute__((unused)) guest_name_sync(const GuestName *t, int count, int on, volatile unsigned char *rom)
{
    int i, k;
    for (i = 0; i < count; i++) {
        const unsigned char *b = on ? t[i].neu : t[i].orig;
        for (k = 0; k < t[i].n; k++)
            if (rom[t[i].at + k] != b[k]) rom[t[i].at + k] = b[k];
    }
}
#endif
