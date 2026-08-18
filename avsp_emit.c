/* See avsp_emit.h for derivation and evidence. */

#include "avsp_emit.h"

static unsigned short mask10(int v)
{
    return (unsigned short)(((unsigned int)v) & 0x3FFu);
}

void avsp_emit_part_flipped(unsigned short origin_x, unsigned short origin_y,
                            short dx, short dy, unsigned short code,
                            unsigned short attr, unsigned short or_value,
                            AvspObjectEntry *out)
{
    unsigned int nx;
    int width;
    unsigned short x_masked;
    unsigned short y_masked;

    if (out == 0) {
        return;
    }

    nx = ((unsigned int)attr >> 8) & 0xFu;
    width = (int)((nx + 1u) * 16u);

    x_masked = mask10((int)origin_x - width - (int)dx);
    y_masked = mask10((int)origin_y + (int)dy);

    out->x = (unsigned short)(x_masked | or_value);
    out->y = y_masked;
    out->code = code;
    out->attr = attr;
}
