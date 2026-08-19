/* See avsp_emit.h for the derivation, live-disassembly provenance, and the
 * 6,010-instance corpus falsification. C90. */

#include "avsp_emit.h"

#define AVSP_EMIT_TAG        0x0006u
#define AVSP_EMIT_SEL_ONE    0x0006u
#define AVSP_EMIT_SEL_TWO    0x000Cu
#define AVSP_EMIT_A2_TABLE   0x1FD1C8ul

static const unsigned char *view_at(const AvspRomView *view,
                                    unsigned long addr, unsigned long need)
{
    int i;

    for (i = 0; i < view->span_count; ++i) {
        const AvspRomSpan *s = &view->spans[i];
        if (addr >= s->base && addr + need <= s->base + s->size) {
            return s->data + (addr - s->base);
        }
    }
    return 0;
}

static unsigned int vrd16(const AvspRomView *view, unsigned long addr, int *ok)
{
    const unsigned char *p = view_at(view, addr, 2ul);
    if (p == 0) {
        *ok = 0;
        return 0;
    }
    return ((unsigned int)p[0] << 8) | (unsigned int)p[1];
}

static unsigned long vrd32(const AvspRomView *view, unsigned long addr, int *ok)
{
    const unsigned char *p = view_at(view, addr, 4ul);
    if (p == 0) {
        *ok = 0;
        return 0;
    }
    return ((unsigned long)p[0] << 24) | ((unsigned long)p[1] << 16)
         | ((unsigned long)p[2] << 8) | (unsigned long)p[3];
}

/* The origin routine 0x0AA59A, shared by every decoded family: consumes the
 * u32 at `d2_addr` (the record's trailing long) and derives the per-record
 * origin from actor world position, the live camera anchors, and the
 * facing-conditional halves of that long. */
static int emit_origin(const AvspRomView *view,
                       unsigned long d2_addr, const AvspEmitActor *actor,
                       unsigned int *origin_x, unsigned int *origin_y)
{
    int ok = 1;
    unsigned long d2 = vrd32(view, d2_addr, &ok);
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

/* attr transform shared by every decoded family: palette-injected in the
 * positive +0x0D mode, raw in the zero/negative mode; the facing flip XOR
 * (bit 5) applies in both. */
static unsigned int attr_final(unsigned int attr_raw,
                               const AvspEmitActor *actor)
{
    unsigned int flip = (unsigned int)(actor->facing & 0x01u) << 5;

    if (actor->mode >= 0x01u && actor->mode <= 0x7Fu) {
        return (attr_raw & 0xFF00u)
             | ((((attr_raw & 0xE0u) + (unsigned int)actor->palette) ^ flip)
                & 0xFFu);
    }
    return (attr_raw & 0xFF00u) | ((attr_raw ^ flip) & 0xFFu);
}

static int emit_group_ex(const AvspRomView *view,
                         unsigned long header, const AvspEmitActor *actor,
                         AvspObjectEntry *out, int cap, int has_advance)
{
    int ok = 1;
    unsigned int count;
    unsigned int selector;
    unsigned long a0;
    unsigned long a2;
    unsigned int origin_x;
    unsigned int origin_y;
    unsigned int i;

    if (view == 0 || actor == 0 || (out == 0 && cap > 0)) {
        return -3;
    }

    /* header: budget (unused here - the frame-budget gate is the caller's
     * scheduling concern), count, selector */
    count = vrd16(view, header + 2ul, &ok);
    selector = vrd16(view, header + 4ul, &ok);
    if (!ok || count < 1u || count > 8u) {
        return -2;
    }

    /* A2 = 0x1FD1C8 + word[0x1FD1C8 + selector*2] */
    a2 = AVSP_EMIT_A2_TABLE
       + vrd16(view, AVSP_EMIT_A2_TABLE + (unsigned long)selector * 2ul, &ok);

    if (!ok || emit_origin(view, header + 6ul, actor,
                           &origin_x, &origin_y) != 0) {
        return -2;
    }

    a0 = header + 0x0Aul;
    for (i = 0; i < count; ++i) {
        unsigned int code = vrd16(view, a0, &ok);
        unsigned int attr_raw = vrd16(view, a0 + 2ul, &ok);
        unsigned int advance = has_advance
            ? vrd16(view, a0 + 4ul, &ok) : 0u;
        unsigned int dx = vrd16(view, a2, &ok);
        unsigned int dy = vrd16(view, a2 + 2ul, &ok);
        unsigned int attr;
        unsigned int x;
        unsigned int y;

        if (!ok) {
            return -2;
        }

        attr = attr_final(attr_raw, actor);

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

        a0 += has_advance ? 6ul : 4ul;
        a2 += 4ul + (unsigned long)advance;
    }

    return (int)count;
}

/* Family 0x0002 (handler 0x0A9D52, live-disassembled): a single entry with
 * inline attr/selector/D2/code. `payload` points past [tag][budget]. */
static int emit_family2(const AvspRomView *view,
                        unsigned long payload, const AvspEmitActor *actor,
                        AvspObjectEntry *out, int cap)
{
    int ok = 1;
    unsigned int attr_raw = vrd16(view, payload, &ok);
    unsigned int selector = vrd16(view, payload + 2ul, &ok);
    unsigned int code = vrd16(view, payload + 8ul, &ok);
    unsigned long a2;
    unsigned int origin_x;
    unsigned int origin_y;
    unsigned int dx;
    unsigned int dy;
    unsigned int attr;
    unsigned int x;
    unsigned int y;

    a2 = AVSP_EMIT_A2_TABLE
       + vrd16(view, AVSP_EMIT_A2_TABLE + (unsigned long)selector * 2ul, &ok);
    dx = vrd16(view, a2, &ok);
    dy = vrd16(view, a2 + 2ul, &ok);
    if (!ok || emit_origin(view, payload + 4ul, actor,
                           &origin_x, &origin_y) != 0) {
        return -2;
    }

    attr = attr_final(attr_raw, actor);
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

int avsp_emit_group(const unsigned char *rom, unsigned long rom_size,
                    unsigned long header, const AvspEmitActor *actor,
                    AvspObjectEntry *out, int cap)
{
    AvspRomSpan span;
    AvspRomView view;

    span.data = rom;
    span.base = 0;
    span.size = rom_size;
    view.spans = &span;
    view.span_count = 1;
    return emit_group_ex(&view, header, actor, out, cap, 1);
}

/* Family 0x000A (handler 0x0AA38A, live-traced): [count][pad][D2 long] then
 * parts of 8 bytes each - code|attr plus INLINE dx,dy (no A2 table).
 * `payload` points past [tag][budget]. Returns count, and sets *end to the
 * first byte past the record. */
static int emit_familyA(const AvspRomView *view,
                        unsigned long payload, const AvspEmitActor *actor,
                        AvspObjectEntry *out, int cap, unsigned long *end)
{
    int ok = 1;
    unsigned int count = vrd16(view, payload, &ok);
    unsigned int origin_x;
    unsigned int origin_y;
    unsigned long p;
    unsigned int i;

    if (!ok || count < 1u || count > 16u) {
        return -2;
    }
    if (emit_origin(view, payload + 4ul, actor,
                    &origin_x, &origin_y) != 0) {
        return -2;
    }
    p = payload + 8ul;
    for (i = 0; i < count; ++i) {
        unsigned int code = vrd16(view, p, &ok);
        unsigned int attr_raw = vrd16(view, p + 2ul, &ok);
        unsigned int dx = vrd16(view, p + 4ul, &ok);
        unsigned int dy = vrd16(view, p + 6ul, &ok);
        unsigned int attr;
        unsigned int x;
        unsigned int y;

        if (!ok) {
            return -2;
        }
        attr = attr_final(attr_raw, actor);
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
        p += 8ul;
    }
    *end = p;
    return (int)count;
}

int avsp_emit_pose_view(const AvspRomView *view, unsigned long assembly,
                        const AvspEmitActor *actor, AvspObjectEntry *out,
                        int cap)
{
    int ok = 1;
    unsigned int top;
    unsigned long pos;
    int n_records;
    int total = 0;
    int r;

    if (view == 0 || view->spans == 0 || actor == 0
        || (out == 0 && cap > 0)) {
        return -3;
    }

    /* Top word: 0x000C = two records follow; a known family tag = one
     * record starting right here. Anything else is an undecoded layout. */
    top = vrd16(view, assembly, &ok);
    if (!ok) {
        return -2;
    }
    if (top == AVSP_EMIT_SEL_TWO) {
        pos = assembly + 2ul;
        n_records = 2;
    } else if (top == 0x0002u || top == 0x0004u || top == AVSP_EMIT_TAG
               || top == 0x000Au) {
        pos = assembly;
        n_records = 1;
    } else {
        return -1;
    }

    for (r = 0; r < n_records; ++r) {
        unsigned int tag = vrd16(view, pos, &ok);
        int n;

        if (!ok) {
            return -2;
        }
        if (tag == AVSP_EMIT_TAG || tag == 0x0004u) {
            /* family 6: multi-part group; family 4: same layout with 4-byte
             * parts and no advance word (fixed A2 stride). */
            unsigned long header = pos + 2ul;
            unsigned int count = vrd16(view, header + 2ul, &ok);
            int adv = (tag == AVSP_EMIT_TAG);

            if (!ok || count < 1u || count > 8u) {
                return -2;
            }
            n = emit_group_ex(view, header, actor,
                              (total < cap) ? out + total : 0,
                              (total < cap) ? cap - total : 0, adv);
            if (n < 0) {
                return n;
            }
            total += n;
            pos = header + 10ul + (unsigned long)count * (adv ? 6ul : 4ul);
        } else if (tag == 0x000Au) {         /* family A: inline dx/dy */
            unsigned long rec_end = 0;

            n = emit_familyA(view, pos + 4ul, actor,
                             (total < cap) ? out + total : 0,
                             (total < cap) ? cap - total : 0, &rec_end);
            if (n < 0) {
                return n;
            }
            total += n;
            pos = rec_end;
        } else if (tag == 0x0002u) {         /* family 2: single entry */
            n = emit_family2(view, pos + 4ul, actor,
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

int avsp_emit_pose(const unsigned char *rom, unsigned long rom_size,
                   unsigned long assembly, const AvspEmitActor *actor,
                   AvspObjectEntry *out, int cap)
{
    AvspRomSpan span;
    AvspRomView view;

    if (rom == 0) {
        return -3;
    }
    span.data = rom;
    span.base = 0;
    span.size = rom_size;
    view.spans = &span;
    view.span_count = 1;
    return avsp_emit_pose_view(&view, assembly, actor, out, cap);
}
