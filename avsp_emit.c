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

/* The origin routine 0x0AA59A, shared by every decoded family: consumes the
 * u32 at `d2_addr` (the record's trailing long) and derives the per-record
 * origin from actor world position, the live camera anchors, and the
 * facing-conditional halves of that long. */
static int emit_origin(const unsigned char *rom, unsigned long rom_size,
                       unsigned long d2_addr, const AvspEmitActor *actor,
                       unsigned int *origin_x, unsigned int *origin_y)
{
    int ok = 1;
    unsigned long d2 = rd32(rom, rom_size, d2_addr, &ok);
    unsigned int d2_hi;
    unsigned int d2_lo;
    unsigned int x;
    unsigned int y;

    if (!ok) {
        return -2;
    }
    d2_hi = (unsigned int)((d2 >> 16) & 0xFFFFul);
    d2_lo = (unsigned int)(d2 & 0xFFFFul);

    y = ((unsigned int)actor->anchor_y - (unsigned int)actor->world_y
         + 0x100u) & 0xFFFFu;
    if (actor->facing & 0x02u) {
        y = (y + d2_lo) & 0xFFFFu;
    } else {
        y = (y - d2_lo) & 0xFFFFu;
    }
    x = ((unsigned int)actor->world_x - (unsigned int)actor->anchor_x
         + 0x40u) & 0xFFFFu;
    if (actor->facing & 0x01u) {
        x = (x + d2_hi) & 0xFFFFu;
    } else {
        x = (x - d2_hi) & 0xFFFFu;
    }
    *origin_x = x;
    *origin_y = y;
    return 0;
}

int avsp_emit_group(const unsigned char *rom, unsigned long rom_size,
                    unsigned long header, const AvspEmitActor *actor,
                    AvspObjectEntry *out, int cap)
{
    int ok = 1;
    unsigned int count;
    unsigned int selector;
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

    if (!ok || emit_origin(rom, rom_size, header + 6ul, actor,
                           &origin_x, &origin_y) != 0) {
        return -2;
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

/* Family 0x0002 (handler 0x0A9D52, live-disassembled): a single entry with
 * inline attr/selector/D2/code. `payload` points past [tag][budget]. */
static int emit_family2(const unsigned char *rom, unsigned long rom_size,
                        unsigned long payload, const AvspEmitActor *actor,
                        AvspObjectEntry *out, int cap)
{
    int ok = 1;
    unsigned int attr_raw = rd16(rom, rom_size, payload, &ok);
    unsigned int selector = rd16(rom, rom_size, payload + 2ul, &ok);
    unsigned int code = rd16(rom, rom_size, payload + 8ul, &ok);
    unsigned long a2;
    unsigned int origin_x;
    unsigned int origin_y;
    unsigned int dx;
    unsigned int dy;
    unsigned int attr;
    unsigned int x;
    unsigned int y;

    a2 = AVSP_EMIT_A2_TABLE
       + rd16(rom, rom_size, AVSP_EMIT_A2_TABLE + (unsigned long)selector * 2ul, &ok);
    dx = rd16(rom, rom_size, a2, &ok);
    dy = rd16(rom, rom_size, a2 + 2ul, &ok);
    if (!ok || emit_origin(rom, rom_size, payload + 4ul, actor,
                           &origin_x, &origin_y) != 0) {
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

    if (cap > 0) {
        out->x = (unsigned short)(x | (unsigned int)actor->or_value);
        out->y = (unsigned short)y;
        out->code = (unsigned short)code;
        out->attr = (unsigned short)attr;
    }
    return 1;
}

int avsp_emit_pose(const unsigned char *rom, unsigned long rom_size,
                   unsigned long assembly, const AvspEmitActor *actor,
                   AvspObjectEntry *out, int cap)
{
    int ok = 1;
    unsigned int top;
    unsigned long pos;
    int n_records;
    int total = 0;
    int r;

    if (rom == 0 || actor == 0 || (out == 0 && cap > 0)) {
        return -3;
    }

    /* Top word: 0x000C = two records follow; a known family tag = one
     * record starting right here. Anything else is an undecoded layout. */
    top = rd16(rom, rom_size, assembly, &ok);
    if (!ok) {
        return -2;
    }
    if (top == AVSP_EMIT_SEL_TWO) {
        pos = assembly + 2ul;
        n_records = 2;
    } else if (top == 0x0002u || top == AVSP_EMIT_TAG) {
        pos = assembly;
        n_records = 1;
    } else {
        return -1;
    }

    for (r = 0; r < n_records; ++r) {
        unsigned int tag = rd16(rom, rom_size, pos, &ok);
        int n;

        if (!ok) {
            return -2;
        }
        if (tag == AVSP_EMIT_TAG) {          /* family 6: multi-part group */
            unsigned long header = pos + 2ul;
            unsigned int count = rd16(rom, rom_size, header + 2ul, &ok);

            if (!ok || count < 1u || count > 8u) {
                return -2;
            }
            n = avsp_emit_group(rom, rom_size, header, actor,
                                (total < cap) ? out + total : 0,
                                (total < cap) ? cap - total : 0);
            if (n < 0) {
                return n;
            }
            total += n;
            pos = header + 10ul + (unsigned long)count * 6ul;
        } else if (tag == 0x0002u) {         /* family 2: single entry */
            n = emit_family2(rom, rom_size, pos + 4ul, actor,
                             (total < cap) ? out + total : 0,
                             (total < cap) ? cap - total : 0);
            if (n < 0) {
                return n;
            }
            total += n;
            pos += 14ul;
        } else if (tag == 0x0008u) {         /* no-op tag (handler is rts) */
            pos += 4ul;
        } else {
            return -1;
        }
    }
    return total;
}
