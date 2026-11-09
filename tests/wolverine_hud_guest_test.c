/* HOST test of saturn/rt/guests.c's select screen and HUD art selection (sat_guest_file for the front end, sat_guest_loaded and guest_pal.h).
   tests/test_wolverine_hud_art.py writes guest_files.inc and guest_hudpal.inc (the real generator's text) beside it and builds this with guests.c.
   Tables: Wolverine (row 0 of sat_guests) has a front file 40 and stage row 3 files 41 (variant 1) and 42 (variant 2); Mega Man has none at the front.
   Palette sets: set 0 pens 0..14 at ROM offsets 0x1000 and 0x3000, set 1 pens 0 and 9 at 0x2000. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "guests.h"

unsigned char *PAGE[256];
#define ROMSIZE 0x4000
static unsigned char rom[ROMSIZE], orig[ROMSIZE];

static int fails;
#define CHECK(c) do { if (!(c)) { printf("FAIL line %d: %s\n", __LINE__, #c); fails++; } } while (0)
#define SAME() (memcmp(rom, orig, ROMSIZE) == 0)

static unsigned word(int at) { return (unsigned)(rom[at] << 8 | rom[at + 1]); }

int main(void)
{
    int i, row, chars, var;
    for (i = 0; i < ROMSIZE; i++) orig[i] = (unsigned char)(i * 37 + 11);
    for (i = 0; i < 15; i++) {   /* the arcade's words in the three table copies, tags after them */
        int w = 0x200 + i;
        orig[0x1000 + i * 2] = orig[0x3000 + i * 2] = (unsigned char)(w >> 8); orig[0x1001 + i * 2] = orig[0x3001 + i * 2] = (unsigned char)w;
        orig[0x2000 + i * 2] = (unsigned char)(w >> 8); orig[0x2001 + i * 2] = (unsigned char)w;
    }
    memcpy(rom, orig, ROMSIZE);
    PAGE[0] = rom;

    /* Off: every row, character set and variant picks the arcade's file, and a load rewrites nothing. */
    sat_guest_sel = 0;
    for (row = 0; row < 5; row++) for (chars = 0; chars < 16; chars++) for (var = 0; var < 3; var++) {
        CHECK(sat_guest_file(row, chars, var, 7) == 7);
        sat_guest_loaded(row, chars, var, 7);
        CHECK(SAME());
    }
    /* A file number that happens to be a guest's, with the guest off, is the arcade's file: no colours. */
    sat_guest_loaded(0, 0, 0, 40); CHECK(SAME());

    /* Wolverine on. The front end (row 0) has his file whatever the characters; a stage row needs his slot (Schaefer, bit 2) in play. */
    sat_guest_sel = 1;
    CHECK(sat_guest_file(0, 0, 0, 0) == 40);
    CHECK(sat_guest_file(3, 2, 1, 5) == 41);
    CHECK(sat_guest_file(3, 3, 2, 5) == 42);
    CHECK(sat_guest_file(3, 1, 1, 5) == 5);     /* Warrior alone */
    CHECK(sat_guest_file(3, 8, 0, 5) == 5);
    CHECK(sat_guest_file(2, 2, 1, 5) == 5);     /* a stage row he has no file for */
    sat_guest_loaded(0, 0, 0, 40);
    CHECK(!SAME());
    for (i = 0; i < 15; i++) {
        CHECK(word(0x1000 + i * 2) == 0x300u + (unsigned)i && word(0x3000 + i * 2) == 0x300u + (unsigned)i);   /* set 0 (set 1's pens first: see below) */
    }
    CHECK(word(0x2000) == 0x400u && word(0x2000 + 18) == 0x409u);                   /* set 1: pens 0 and 9 only */
    for (i = 1; i < 15; i++) if (i != 9) CHECK(word(0x2000 + i * 2) == 0x200u + (unsigned)i);
    CHECK(memcmp(rom + 0x1000 + 30, orig + 0x1000 + 30, 2) == 0 && memcmp(rom + 0x3000 + 30, orig + 0x3000 + 30, 2) == 0);   /* tags */
    for (i = 0; i < ROMSIZE; i++) if (!((i >= 0x1000 && i < 0x101e) || (i >= 0x3000 && i < 0x301e) || i == 0x2000 || i == 0x2001 || i == 0x2012 || i == 0x2013)) CHECK(rom[i] == orig[i]);

    /* A stage file load restores a ROM page behind us: the next load puts the colours back. */
    memcpy(rom + 0x3000, orig + 0x3000, 0x20);
    sat_guest_loaded(3, 2, 1, 41);
    CHECK(word(0x3000) == 0x300u);
    /* A stage without him (his file is not the one loaded) gets the arcade's colours again: the ROM is byte for byte the original. */
    sat_guest_loaded(3, 1, 1, 5);
    CHECK(SAME());
    /* And the front end loaded without his file (the setting changed to off at the title menu): the same. */
    sat_guest_loaded(0, 0, 0, 40);
    CHECK(!SAME());
    sat_guest_sel = 0;
    CHECK(sat_guest_file(0, 0, 0, 0) == 0);
    sat_guest_loaded(0, 0, 0, 0);
    CHECK(SAME());

    /* Mega Man alone has no art here: nothing changes, the front end is the arcade's. */
    sat_guest_sel = 2;
    CHECK(sat_guest_file(0, 0, 0, 0) == 0);
    sat_guest_loaded(0, 0, 0, 0); CHECK(SAME());
    /* Both: Wolverine's front file (Mega Man has none). */
    sat_guest_sel = 3;
    CHECK(sat_guest_file(0, 0, 0, 0) == 40);

    printf(fails ? "hud guest test FAILED\n" : "hud guest test passed\n");
    return fails != 0;
}
