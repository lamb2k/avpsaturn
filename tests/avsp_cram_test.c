/* Bounded CRAM palette writes under Jo Engine's one-based palette contract.
 *
 * Jo hands out jo_palette::data one entry above its 256-entry colour-RAM
 * block base, and documents a 255-colour maximum, because Saturn pixel and
 * pen value zero is transparent: pixel p reads data[p - 1]. The two entries
 * a palette must never touch are therefore the hardware block boundaries
 * 256 * id, which is data[-1], and 256 * (id + 1), which is data[255]. Both
 * belong to a neighbouring Jo allocation.
 *
 * Every case below lays the destination out in a simulated colour RAM with a
 * canary in each of those boundary entries, so a copy that runs one entry
 * short or one entry long is caught as a boundary write rather than as a
 * plausible off-by-one in the visible result.
 *
 * Check A - a full 255-colour surface payload copies exactly, mapping pixel
 *   value p to file entry p, and disturbs neither canary.
 * Check B - sub-banks 0 and 15 each copy their fifteen live colours to the
 *   pens the hardware reads, and sub-bank 15, the one that ends nearest the
 *   far boundary, still stops one entry short of it.
 * Check C - a source-indexed payload, the convention the generated actor,
 *   tile, HUD and route-sequence tables already use, transcribes straight
 *   through without a shift.
 * Check D - one-based surface validation accepts a live surface and rejects
 *   one containing a zero pixel.
 *
 * Negative controls, each of which must be refused rather than clamped:
 *   256 surface colours, zero colours, sub-bank 16, a negative sub-bank, and
 *   a null destination. A zero-based surface must fail check D.
 */
#include <stdio.h>
#include <string.h>

#include "../avsp_cram.h"

/* The simulated block is one entry longer than a hardware block so that both
   boundaries are represented: sim[0] is entry 256 * id, sim[1 .. 255] are the
   255 entries this palette owns, and sim[256] is entry 256 * (id + 1), the
   first entry of the next allocation. With data = sim + 1 that places the far
   canary exactly on data[255], the entry a 256-colour copy would reach. */
#define CANARY_LOW 0xC0DE
#define CANARY_HIGH 0xFEED
#define SIM_ENTRIES (AVSP_CRAM_BLOCK_ENTRIES + 1)

static int failures;

static void fail(const char *what)
{
    printf("  FAIL %s\n", what);
    ++failures;
}

/* data[] points one entry into the simulated block, exactly as Jo's
   allocator hands it out. sim[0] is hardware entry 256 * id and
   sim[SIM_ENTRIES - 1] is hardware entry 256 * (id + 1). */
static unsigned short sim[SIM_ENTRIES];

static unsigned short *reset_block(void)
{
    memset(sim, 0, sizeof(sim));
    sim[0] = CANARY_LOW;
    sim[SIM_ENTRIES - 1] = CANARY_HIGH;
    return sim + 1;
}

static int canaries_intact(const char *what)
{
    int ok = 1;
    if (sim[0] != CANARY_LOW)
    {
        fail(what);
        printf("    low boundary entry 256*id was overwritten with 0x%04X\n",
               sim[0]);
        ok = 0;
    }
    if (sim[SIM_ENTRIES - 1] != CANARY_HIGH)
    {
        fail(what);
        printf("    high boundary entry 256*(id+1) was overwritten with "
               "0x%04X\n", sim[SIM_ENTRIES - 1]);
        ok = 0;
    }
    return ok;
}

static unsigned short file_entry(int index)
{
    /* Distinct, non-zero, and derived from the index so a one-entry shift is
       visible rather than plausible. */
    return (unsigned short)(0x8000 | (index * 7 + 1));
}

int main(void)
{
    unsigned short file[AVSP_CRAM_BLOCK_ENTRIES];
    unsigned short subfile[AVSP_CRAM_SUBBANK_ENTRIES];
    unsigned short source[AVSP_CRAM_BLOCK_ENTRIES];
    unsigned char pixels[64];
    unsigned short *data;
    int index;
    int subbank;

    printf("avsp_cram: bounded palette writes under Jo's one-based contract\n");

    for (index = 0; index < AVSP_CRAM_BLOCK_ENTRIES; ++index)
    {
        file[index] = index ? file_entry(index) : 0;
        source[index] = (unsigned short)(0x8000 | (index * 3 + 2));
    }
    for (index = 0; index < AVSP_CRAM_SUBBANK_ENTRIES; ++index)
        subfile[index] = index ? (unsigned short)(0x8000 | (index * 11 + 5)) : 0;

    /* Check A: full surface payload. */
    data = reset_block();
    if (!avsp_cram_copy_surface(data, file, AVSP_CRAM_MAX_COLOURS))
        fail("check A: a 255-colour surface copy was refused");
    else
    {
        for (index = 1; index <= AVSP_CRAM_MAX_COLOURS; ++index)
            if (data[index - 1] != file[index])
            {
                fail("check A: pixel value does not read its own file entry");
                printf("    pixel %d read 0x%04X, expected 0x%04X\n",
                       index, data[index - 1], file[index]);
                break;
            }
        canaries_intact("check A");
    }

    /* Check B: 4bpp sub-banks, including the one nearest the far boundary. */
    for (subbank = 0; subbank < AVSP_CRAM_SUBBANK_COUNT; subbank += 15)
    {
        data = reset_block();
        if (!avsp_cram_copy_subbank(data, subfile, subbank))
        {
            fail("check B: a valid sub-bank copy was refused");
            continue;
        }
        for (index = 1; index <= AVSP_CRAM_SUBBANK_COLOURS; ++index)
        {
            int pen = subbank * AVSP_CRAM_SUBBANK_ENTRIES + index;
            if (data[pen - 1] != subfile[index])
            {
                fail("check B: pen does not read its own file entry");
                printf("    sub-bank %d pen %d read 0x%04X, expected 0x%04X\n",
                       subbank, index, data[pen - 1], subfile[index]);
                break;
            }
        }
        canaries_intact("check B");
    }

    /* Check C: source-indexed payload transcribes without a shift. */
    data = reset_block();
    if (!avsp_cram_copy_source_indexed(data, source, AVSP_CRAM_MAX_COLOURS))
        fail("check C: a 255-colour source-indexed copy was refused");
    else
    {
        for (index = 0; index < AVSP_CRAM_MAX_COLOURS; ++index)
            if (data[index] != source[index])
            {
                fail("check C: source-indexed entry shifted");
                break;
            }
        canaries_intact("check C");
    }

    /* Check D: one-based surface validation. */
    for (index = 0; index < (int)sizeof(pixels); ++index)
        pixels[index] = (unsigned char)(index % 255 + 1);
    if (!avsp_cram_surface_is_one_based(pixels, sizeof(pixels)))
        fail("check D: a live one-based surface was rejected");

    /* Negative controls. Each must be refused, not clamped. */
    data = reset_block();
    if (avsp_cram_copy_surface(data, file, AVSP_CRAM_BLOCK_ENTRIES))
        fail("negative control: 256 surface colours were accepted");
    if (avsp_cram_copy_surface(data, file, 0))
        fail("negative control: a zero-colour surface copy was accepted");
    if (avsp_cram_copy_source_indexed(data, source, AVSP_CRAM_BLOCK_ENTRIES))
        fail("negative control: 256 source-indexed colours were accepted");
    if (avsp_cram_copy_subbank(data, subfile, AVSP_CRAM_SUBBANK_COUNT))
        fail("negative control: sub-bank 16 was accepted");
    if (avsp_cram_copy_subbank(data, subfile, -1))
        fail("negative control: a negative sub-bank was accepted");
    if (avsp_cram_copy_surface(0, file, AVSP_CRAM_MAX_COLOURS))
        fail("negative control: a null destination was accepted");
    if (!canaries_intact("negative controls"))
        fail("negative control: a refused copy still wrote a boundary");

    pixels[17] = 0;
    if (avsp_cram_surface_is_one_based(pixels, sizeof(pixels)))
        fail("negative control: a zero-based surface pixel was accepted");

    /* Canary liveness. The checks above only prove a boundary was not written
       if writing one would actually be seen, so perform the exact write the
       rejected 256-colour copy would have made and require both canaries to
       report it. Without this the whole harness could pass vacuously. */
    data = reset_block();
    data[255] = 0x1234;
    if (sim[SIM_ENTRIES - 1] == CANARY_HIGH)
        fail("canary liveness: writing data[255] did not disturb entry "
             "256*(id+1)");
    data = reset_block();
    data[-1] = 0x1234;
    if (sim[0] == CANARY_LOW)
        fail("canary liveness: writing data[-1] did not disturb entry 256*id");
    (void)reset_block();

    if (failures)
    {
        printf("avsp_cram: FAIL - %d failing assertions\n", failures);
        return 1;
    }
    printf("avsp_cram: PASS - 255-colour surface, sub-banks 0 and 15, "
           "source-indexed transcription, one-based validation, "
           "both block boundaries untouched, 7 negative controls refused, "
           "canaries proven live\n");
    return 0;
}
