/* Host test of the unlock record (saturn/rt/unlock_save.h): locked by default, set and clear, an old record (no flags byte, or a bad one) reads locked and
   nothing else in it is lost on the rewrite, a foreign record starts from zero. Build: gcc -std=c90 -Wall -Wextra -Werror tests/unlock_save_test.c */
#include <stdio.h>
#include <string.h>
#include "../saturn/rt/unlock_save.h"
static int fails;
#define CHECK(c) do { if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
static void seal(unsigned char *r)
{
    unsigned s = save_sum(r);
    r[SAVE_SIZE - 2] = (unsigned char)(s >> 8); r[SAVE_SIZE - 1] = (unsigned char)s;
}
int main(void)
{
    unsigned char a[SAVE_SIZE], b[SAVE_SIZE], legacy[SAVE_SIZE];
    unsigned i;
    /* no record: locked; a first set makes a valid record with the flag and nothing else */
    memset(a, 0xee, sizeof a);
    CHECK(save_flags(a, 0) == 0);
    save_merge(b, a, 0, SAVE_FLAG_WOLVERINE, 0);
    CHECK(save_flags(b, SAVE_SIZE) == SAVE_FLAG_WOLVERINE);
    CHECK(b[0] == 'A' && b[3] == 'S' && b[4] == SAVE_VERSION);
    for (i = 8; i < SAVE_SIZE - 2; i++) CHECK(b[i] == 0);
    /* clearing gives locked again, record still valid */
    save_merge(a, b, SAVE_SIZE, 0, SAVE_FLAG_WOLVERINE);
    CHECK(save_flags(a, SAVE_SIZE) == 0 && a[4] == SAVE_VERSION && save_magic(a, SAVE_SIZE));
    /* an older record: version 0, no flags byte, settings in bytes 8 to 61 and a byte of junk where the flags will live: reads locked, keeps its settings when the flag is set */
    memset(legacy, 0, sizeof legacy);
    legacy[0] = 'A'; legacy[1] = 'V'; legacy[2] = 'P'; legacy[3] = 'S'; legacy[4] = 0; legacy[5] = 8; legacy[6] = 0;
    for (i = 8; i < SAVE_SIZE - 2; i++) legacy[i] = (unsigned char)(i * 7 + 3);
    seal(legacy);
    CHECK(save_flags(legacy, SAVE_SIZE) == 0);
    legacy[6] = 1;   /* a v0 writer that left something there is still not a flag */
    seal(legacy);
    CHECK(save_flags(legacy, SAVE_SIZE) == 0);
    save_merge(b, legacy, SAVE_SIZE, SAVE_FLAG_WOLVERINE, 0);
    CHECK(save_flags(b, SAVE_SIZE) == SAVE_FLAG_WOLVERINE && b[4] == SAVE_VERSION);
    for (i = 8; i < SAVE_SIZE - 2; i++) CHECK(b[i] == (unsigned char)(i * 7 + 3));
    /* a bad checksum reads locked, and the rewrite still keeps the bytes (the record is ours, only its sum is wrong) */
    memcpy(a, b, sizeof a);
    a[20] ^= 0x55;
    CHECK(save_flags(a, SAVE_SIZE) == 0);
    save_merge(b, a, SAVE_SIZE, SAVE_FLAG_WOLVERINE, 0);
    CHECK(save_flags(b, SAVE_SIZE) == SAVE_FLAG_WOLVERINE && b[20] == a[20]);
    /* a short read (a file smaller than a record) is no record */
    CHECK(save_flags(b, SAVE_SIZE - 1) == 0);
    /* not ours at all: starts from zero */
    memset(a, 0x5a, sizeof a);
    save_merge(b, a, SAVE_SIZE, SAVE_FLAG_WOLVERINE, 0);
    CHECK(save_flags(b, SAVE_SIZE) == SAVE_FLAG_WOLVERINE && b[30] == 0);
    /* flags of a later version that has more bits: untouched bits survive a set and a clear of ours */
    save_merge(a, b, SAVE_SIZE, 0x40, 0);
    CHECK(save_flags(a, SAVE_SIZE) == (SAVE_FLAG_WOLVERINE | 0x40));
    save_merge(b, a, SAVE_SIZE, 0, SAVE_FLAG_WOLVERINE);
    CHECK(save_flags(b, SAVE_SIZE) == 0x40);
    /* the saved bonus-character setting (byte 7): none in a record without one, stored and read back, kept by a flag write, dropped when the sum failed, neighbours untouched */
    memset(a, 0, sizeof a);
    save_merge(a, a, 0, SAVE_FLAG_WOLVERINE, 0);
    CHECK(save_sel(a, SAVE_SIZE) == -1);                         /* the first version's record: flag only, no setting */
    save_merge2(b, a, SAVE_SIZE, 0, 0, 1);
    CHECK(save_sel(b, SAVE_SIZE) == 1 && save_flags(b, SAVE_SIZE) == SAVE_FLAG_WOLVERINE);
    save_merge2(a, b, SAVE_SIZE, 0, 0, 0);                       /* the player turns him off: saved as 0, not "none" */
    CHECK(save_sel(a, SAVE_SIZE) == 0 && save_flags(a, SAVE_SIZE) == SAVE_FLAG_WOLVERINE);
    save_merge(b, a, SAVE_SIZE, 0x40, 0);                        /* a flags write keeps the saved setting */
    CHECK(save_sel(b, SAVE_SIZE) == 0);
    save_merge2(a, b, SAVE_SIZE, 0, 0, 3);
    CHECK(save_sel(a, SAVE_SIZE) == 3);
    for (i = 8; i < SAVE_SIZE - 2; i++) CHECK(a[i] == b[i]);
    memcpy(b, a, sizeof b);
    b[30] ^= 0x11;                                              /* sum fails: no setting is trusted, and a rewrite does not bring it back */
    CHECK(save_sel(b, SAVE_SIZE) == -1);
    save_merge(a, b, SAVE_SIZE, SAVE_FLAG_WOLVERINE, 0);
    CHECK(save_sel(a, SAVE_SIZE) == -1 && b[30] == a[30]);
    memset(b, 0x5a, sizeof b);                                   /* not ours: from zero */
    save_merge2(a, b, SAVE_SIZE, 0, 0, 2);
    CHECK(save_sel(a, SAVE_SIZE) == 2 && save_flags(a, SAVE_SIZE) == 0 && a[30] == 0);
    if (fails) return 1;
    printf("unlock_save: pass\n");
    return 0;
}
