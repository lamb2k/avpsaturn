/* See avsp_emit.h for the derivation, live-disassembly provenance, and the
 * 6,010-instance corpus falsification. C90. */

#include "avsp_emit.h"

#define AVSP_EMIT_TAG        0x0006u
#define AVSP_EMIT_SEL_ONE    0x0006u
#define AVSP_EMIT_SEL_TWO    0x000Cu
#define AVSP_EMIT_A2_TABLE   0x1FD1C8ul

static unsigned int rd16(const unsigned char *rom, unsigned long rom_size,
                         unsigned long addr, int *ok)
{
    if (addr + 2ul > rom_size) {
        *ok = 0;
        return 0;
    }
    return ((unsigned int)rom[addr] << 8) | (unsigned int)rom[addr + 1ul];
}

static unsigned long rd32(const unsigned char *rom, unsigned long rom_size,
                          unsigned long addr, int *ok)
{
    if (addr + 4ul > rom_size) {
        *ok = 0;
        return 0;
    }
    return ((unsigned long)rom[addr] << 24)
         | ((unsigned long)rom[addr + 1ul] << 16)
         | ((unsigned long)rom[addr + 2ul] << 8)
         | (unsigned long)rom[addr + 3ul];
}

int avsp_emit_group(const unsigned char *rom, unsigned long rom_size,
                    unsigned long header, const AvspEmitActor *actor,
                    AvspObjectEntry *out, int cap)
{
    int ok = 1;
    unsigned int count;
    unsigned int selector;
    unsigned long d2;
    unsigned long a0;
    unsigned long a2;
    unsigned int origin_x;
    unsigned int origin_y;
    unsigned int i;

    if (rom == 0 || actor == 0 || (out == 0 && cap > 0)) {
        return -3;
    }

    /* header: budget (unused here - the frame-budget gate is the caller's
     * scheduling concern), count, selector */
    count = rd16(rom, rom_size, header + 2ul, &ok);
    selector = rd16(rom, rom_size, header + 4ul, &ok);
    if (!ok || count < 1u || count > 8u) {
        return -2;
    }

    /* A2 = 0x1FD1C8 + word[0x1FD1C8 + selector*2] */
    a2 = AVSP_EMIT_A2_TABLE
       + rd16(rom, rom_size, AVSP_EMIT_A2_TABLE + (unsigned long)selector * 2ul, &ok);

    /* origin routine 0x0AA59A: consumes the header's trailing u32 as D2 */
    d2 = rd32(rom, rom_size, header + 6ul, &ok);
    if (!ok) {
        return -2;
    }
    {
        unsigned int d2_hi = (unsigned int)((d2 >> 16) & 0xFFFFul);
        unsigned int d2_lo = (unsigned int)(d2 & 0xFFFFul);

        origin_y = ((unsigned int)actor->anchor_y - (unsigned int)actor->world_y
                    + 0x100u) & 0xFFFFu;
        if (actor->facing & 0x02u) {
            origin_y = (origin_y + d2_lo) & 0xFFFFu;
        } else {
            origin_y = (origin_y - d2_lo) & 0xFFFFu;
        }
        origin_x = ((unsigned int)actor->world_x - (unsigned int)actor->anchor_x
                    + 0x40u) & 0xFFFFu;
        if (actor->facing & 0x01u) {
            origin_x = (origin_x + d2_hi) & 0xFFFFu;
        } else {
            origin_x = (origin_x - d2_hi) & 0xFFFFu;
        }
    }

    a0 = header + 0x0Aul;
    for (i = 0; i < count; ++i) {
        unsigned int code = rd16(rom, rom_size, a0, &ok);
        unsigned int attr_raw = rd16(rom, rom_size, a0 + 2ul, &ok);
        unsigned int advance = rd16(rom, rom_size, a0 + 4ul, &ok);
        unsigned int dx = rd16(rom, rom_size, a2, &ok);
        unsigned int dy = rd16(rom, rom_size, a2 + 2ul, &ok);
        unsigned int attr;
        unsigned int x;
        unsigned int y;

        if (!ok) {
            return -2;
        }

        attr = (attr_raw & 0xFF00u)
             | ((((attr_raw & 0xE0u) + (unsigned int)actor->palette)
                 ^ ((unsigned int)(actor->facing & 0x01u) << 5)) & 0xFFu);

        if (actor->facing & 0x01u) {
            unsigned int width = ((((attr_raw >> 8) & 0xFu) + 1u) * 16u);
            x = (origin_x - width - dx) & 0x3FFu;
        } else {
            x = (origin_x + dx) & 0x3FFu;
        }
        y = (origin_y + dy) & 0x3FFu;

        if ((int)i < cap) {
            out[i].x = (unsigned short)(x | (unsigned int)actor->or_value);
            out[i].y = (unsigned short)y;
            out[i].code = (unsigned short)code;
            out[i].attr = (unsigned short)attr;
        }

        a0 += 6ul;
        a2 += 4ul + (unsigned long)advance;
    }

    return (int)count;
}

int avsp_emit_pose(const unsigned char *rom, unsigned long rom_size,
                   unsigned long assembly, const AvspEmitActor *actor,
                   AvspObjectEntry *out, int cap)
{
    int ok = 1;
    unsigned int selector;
    int total;
    int n;

    if (rom == 0 || actor == 0 || (out == 0 && cap > 0)) {
        return -3;
    }

    selector = rd16(rom, rom_size, assembly, &ok);
    if (!ok) {
        return -2;
    }

    if (selector == AVSP_EMIT_SEL_ONE) {
        return avsp_emit_group(rom, rom_size, assembly + 2ul, actor, out, cap);
    }

    if (selector == AVSP_EMIT_SEL_TWO) {
        unsigned long h1;
        unsigned long tag2;
        unsigned int count1;

        if (rd16(rom, rom_size, assembly + 2ul, &ok) != AVSP_EMIT_TAG || !ok) {
            return -1;
        }
        h1 = assembly + 4ul;
        count1 = rd16(rom, rom_size, h1 + 2ul, &ok);
        if (!ok || count1 < 1u || count1 > 8u) {
            return -2;
        }
        tag2 = h1 + 6ul + 4ul + (unsigned long)count1 * 6ul;
        if (rd16(rom, rom_size, tag2, &ok) != AVSP_EMIT_TAG || !ok) {
            return -1;
        }

        total = avsp_emit_group(rom, rom_size, h1, actor, out, cap);
        if (total < 0) {
            return total;
        }
        n = avsp_emit_group(rom, rom_size, tag2 + 2ul, actor,
                            (total < cap) ? out + total : 0,
                            (total < cap) ? cap - total : 0);
        if (n < 0) {
            return n;
        }
        return total + n;
    }

    return -1;
}
