#include "avsp_cram.h"

int avsp_cram_copy_surface(unsigned short *data, const unsigned short *file,
                           int colours)
{
    int index;
    if (data == 0 || file == 0) return 0;
    if (colours < 1 || colours > AVSP_CRAM_MAX_COLOURS) return 0;
    for (index = 0; index < colours; ++index)
        data[index] = file[index + 1];
    return 1;
}

int avsp_cram_copy_source_indexed(unsigned short *data,
                                  const unsigned short *source, int colours)
{
    int index;
    if (data == 0 || source == 0) return 0;
    if (colours < 1 || colours > AVSP_CRAM_MAX_COLOURS) return 0;
    for (index = 0; index < colours; ++index)
        data[index] = source[index];
    return 1;
}

int avsp_cram_copy_subbank(unsigned short *data, const unsigned short *file,
                           int subbank)
{
    int index;
    int base;
    if (data == 0 || file == 0) return 0;
    if (subbank < 0 || subbank >= AVSP_CRAM_SUBBANK_COUNT) return 0;
    /* Hardware pen 16 * subbank + p reads data[16 * subbank + p - 1], so the
       fifteen live colours start where pen 1 of this sub-bank lands. The last
       sub-bank therefore ends at data[254], one entry short of the block
       boundary that belongs to the next allocation. */
    base = subbank * AVSP_CRAM_SUBBANK_ENTRIES;
    for (index = 0; index < AVSP_CRAM_SUBBANK_COLOURS; ++index)
        data[base + index] = file[index + 1];
    return 1;
}

int avsp_cram_surface_is_one_based(const unsigned char *pixels,
                                   unsigned long count)
{
    unsigned long index;
    if (pixels == 0) return 0;
    for (index = 0; index < count; ++index)
        if (pixels[index] == 0) return 0;
    return 1;
}
