/* Host falsification for the ROM tile archive and the per-entry tile
 * expansion (S2 Body E texture source).
 *
 * Checks, against the generated cd/SPR4/TILES.BIN (skips cleanly when the
 * archive has not been generated on this machine):
 *   1. the header parses and every structural invariant holds;
 *   2. the code table is strictly ascending and find() inverts code();
 *   3. every tile referenced by the committed oracle entries of
 *      data/avsp_object_stream.json (transcribed fixtures below, both
 *      facings) is present, and their palette banks resolve to slots;
 *   4. CRAM colours carry the Saturn RGB-mode bit.
 */
#include <stdio.h>
#include <stdlib.h>

#include "../avsp_tiles.h"

static unsigned char *read_file(const char *path, unsigned long *size_out)
{
    FILE *f = fopen(path, "rb");
    unsigned char *data;
    long size;
    if (f == 0) return 0;
    if (fseek(f, 0, SEEK_END) != 0 || (size = ftell(f)) <= 0 ||
        fseek(f, 0, SEEK_SET) != 0)
    {
        fclose(f);
        return 0;
    }
    data = (unsigned char *)malloc((unsigned long)size);
    if (data == 0 || fread(data, 1, (unsigned long)size, f) !=
        (unsigned long)size)
    {
        fclose(f);
        free(data);
        return 0;
    }
    fclose(f);
    *size_out = (unsigned long)size;
    return data;
}

/* Oracle entries transcribed from data/avsp_object_stream.json: frame 4214
 * group 1 (plain-attr street alien) and frame 4214 group 2 (flipped attrs
 * 0x2431/0x1331 with nx>1, exercising the mirrored tile order). y carries
 * only the 10-bit screen Y for these actors, so the (y & 0x6000) code
 * extension stays zero, which the fixtures assert explicitly. */
static const struct
{
    unsigned short y;
    unsigned short code;
    unsigned short attr;
} fixtures[] = {
    {0x0099, 0x4efe, 0x0131},
    {0x00a9, 0x4ef6, 0x0431},
    {0x00b9, 0x4fc8, 0x0131},
    {0x007b, 0x473a, 0x2431},
    {0x00ab, 0x479c, 0x1331},
};

int main(void)
{
    AvspTileArchive archive;
    unsigned long size = 0;
    unsigned char *data = read_file("build/avsp_cd/SPR4/TILES.BIN", &size);
    unsigned long rank;
    unsigned long checked = 0;
    unsigned long i;

    if (data == 0)
    {
        printf("avsp_tiles_test: SKIP (build/avsp_cd/SPR4/TILES.BIN not "
               "generated)\n");
        return 0;
    }
    if (!avsp_tiles_open(&archive, data, size))
    {
        printf("FAIL: archive header rejected\n");
        return 1;
    }
    for (rank = 1; rank < archive.tile_count; ++rank)
    {
        if (avsp_tiles_code(&archive, (long)rank - 1) >=
            avsp_tiles_code(&archive, (long)rank))
        {
            printf("FAIL: code table not strictly ascending at %lu\n", rank);
            return 1;
        }
    }
    for (rank = 0; rank < archive.tile_count;
         rank += archive.tile_count / 97 + 1)
    {
        unsigned long code = avsp_tiles_code(&archive, (long)rank);
        if (avsp_tiles_find(&archive, code) != (long)rank)
        {
            printf("FAIL: find(code(%lu)) != %lu\n", rank, rank);
            return 1;
        }
        ++checked;
    }
    for (i = 0; i < sizeof(fixtures) / sizeof(fixtures[0]); ++i)
    {
        AvspEntryTile tiles[64];
        int n;
        int t;
        int slot;
        if ((fixtures[i].y & 0x6000) != 0)
        {
            printf("FAIL: fixture %lu carries code-extension Y bits\n", i);
            return 1;
        }
        n = avsp_entry_tiles(fixtures[i].y, fixtures[i].code,
                             fixtures[i].attr, tiles, 64);
        if (n <= 0)
        {
            printf("FAIL: fixture %lu expanded to %d tiles\n", i, n);
            return 1;
        }
        for (t = 0; t < n; ++t)
        {
            long found = avsp_tiles_find(&archive, tiles[t].code);
            if (found < 0)
            {
                printf("FAIL: fixture %lu tile 0x%lX absent\n", i,
                       tiles[t].code);
                return 1;
            }
            if (avsp_tiles_texture(&archive, found) == 0)
            {
                printf("FAIL: fixture %lu tile 0x%lX has no texture\n", i,
                       tiles[t].code);
                return 1;
            }
        }
        slot = avsp_tiles_bank_slot(&archive, fixtures[i].attr & 0x1F);
        if (slot < 0)
        {
            printf("FAIL: fixture %lu palette bank 0x%02X unresolved\n", i,
                   fixtures[i].attr & 0x1F);
            return 1;
        }
        for (t = 0; t < 15; ++t)
        {
            if ((avsp_tiles_cram_color(&archive, slot, t) & 0x8000U) == 0)
            {
                printf("FAIL: slot %d colour %d missing RGB bit\n", slot, t);
                return 1;
            }
        }
    }
    {
        /* A synthetic two-tile archive proves both local pixel mirroring and
         * the flipped block's reversed tile-code order. */
        unsigned char synthetic[0x50 + 8 + 256];
        AvspTileArchive source;
        unsigned char composite[256];
        long bytes;
        unsigned long p;
        for (p = 0; p < sizeof(synthetic); ++p) synthetic[p] = 0;
        synthetic[0] = 'A'; synthetic[1] = 'V';
        synthetic[2] = 'T'; synthetic[3] = 'L';
        synthetic[7] = 2;       /* two tiles */
        synthetic[11] = 1;      /* one palette slot */
        synthetic[15] = 0x50;   /* code table offset */
        synthetic[0x10] = 0;    /* bank zero -> slot zero */
        synthetic[0x53] = 1;    /* code 1 */
        synthetic[0x57] = 2;    /* code 2 */
        for (p = 0; p < 128; ++p)
        {
            synthetic[0x58 + p] = 0x12;
            synthetic[0x58 + 128 + p] = 0x34;
        }
        if (!avsp_tiles_open(&source, synthetic, sizeof(synthetic)))
        {
            printf("FAIL: synthetic composite archive rejected\n");
            return 1;
        }
        bytes = avsp_compose_entry_texture(&source, 0, 1, 0x0120,
                                           composite, sizeof(composite));
        if (bytes != 256 || composite[0] != 0x43 ||
            composite[8] != 0x21)
        {
            printf("FAIL: flipped composite texture mismatch (%ld, %02X, "
                   "%02X)\n", bytes, composite[0], composite[8]);
            return 1;
        }
        if (avsp_compose_entry_texture(&source, 0, 1, 0x0120,
                                       composite, 255) != 0)
        {
            printf("FAIL: undersized composite destination accepted\n");
            return 1;
        }
    }
    printf("avsp_tiles_test: PASS (%lu tiles, %lu ranks spot-checked, %lu "
           "oracle entries covered)\n",
           archive.tile_count, checked,
           (unsigned long)(sizeof(fixtures) / sizeof(fixtures[0])));
    free(data);
    return 0;
}
