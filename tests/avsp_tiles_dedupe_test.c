/* AVT2 deduplicated archive: two codes share one payload, one has its own, and
 * a table entry naming a payload that is not stored must be refused.
 * Run: gcc -std=c90 -pedantic -Wall -Wextra -Werror avsp_tiles.c tests/avsp_tiles_dedupe_test.c
 */
#include <stdio.h>
#include <string.h>

#include "../avsp_tiles.h"

#define OFFSET (0x10 + 32 + 32)
#define SIZE (OFFSET + 3 * 4 + 2 * AVSP_TILE_BYTES)

static unsigned char blob[SIZE];

static void put(unsigned char *at, unsigned long value)
{
    at[0] = (unsigned char)(value >> 24);
    at[1] = (unsigned char)(value >> 16);
    at[2] = (unsigned char)(value >> 8);
    at[3] = (unsigned char)value;
}

static int fail(const char *what)
{
    fprintf(stderr, "avsp_tiles_dedupe: %s\n", what);
    return 1;
}

int main(void)
{
    AvspTileArchive archive;
    const unsigned char *a, *b, *c;
    unsigned long table = OFFSET;
    memset(blob, 0, sizeof(blob));
    put(blob, AVSP_TILE_MAGIC_DEDUPED);
    put(blob + 4, 3UL);
    put(blob + 8, 1UL);
    put(blob + 12, (unsigned long)OFFSET);
    put(blob + table, 0x00010UL | (0UL << AVSP_TILE_CODE_BITS));
    put(blob + table + 4, 0x00020UL | (1UL << AVSP_TILE_CODE_BITS));
    put(blob + table + 8, 0x1FFFFUL | (0UL << AVSP_TILE_CODE_BITS));
    memset(blob + table + 12, 0x11, AVSP_TILE_BYTES);
    memset(blob + table + 12 + AVSP_TILE_BYTES, 0x22, AVSP_TILE_BYTES);
    if (!avsp_tiles_open(&archive, blob, SIZE)) return fail("open refused");
    if (avsp_tiles_find(&archive, 0x10UL) != 0 ||
        avsp_tiles_find(&archive, 0x20UL) != 1 ||
        avsp_tiles_find(&archive, 0x1FFFFUL) != 2 ||
        avsp_tiles_find(&archive, 0x30UL) != -1)
        return fail("find ignored the payload bits");
    if (avsp_tiles_code(&archive, 1) != 0x20UL) return fail("code kept payload bits");
    a = avsp_tiles_texture(&archive, 0);
    b = avsp_tiles_texture(&archive, 1);
    c = avsp_tiles_texture(&archive, 2);
    if (a != c || a == b || a[0] != 0x11 || b[0] != 0x22)
        return fail("texture did not follow the payload index");
    put(blob + table + 4, 0x00020UL | (2UL << AVSP_TILE_CODE_BITS));
    if (avsp_tiles_open(&archive, blob, SIZE))
        return fail("negative control: out-of-range payload accepted");
    printf("avsp_tiles_dedupe: PASS\n");
    return 0;
}
