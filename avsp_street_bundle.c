#include "avsp_street_bundle.h"

/* Every read below is preceded by an explicit fit check against `bytes`,
 * so a truncated or corrupt bundle is rejected before any dereference
 * outside the actually-read region. Offsets are accumulated in unsigned
 * long with overflow guards on every multiply/add that involves
 * file-supplied counts. */

#define AVSP_STREET_HEADER_BYTES 8UL
#define AVSP_STREET_PLANE_HEADER_BYTES 20UL
#define AVSP_STREET_PALETTE_BYTES 512UL
#define AVSP_STREET_CYCLE_HEADER_END (48UL + 1024UL + 6UL)

static unsigned int bundle_u16(const unsigned char *data,
                               unsigned long offset)
{
    return ((unsigned int)data[offset] << 8) | data[offset + 1];
}

static unsigned long bundle_u32(const unsigned char *data,
                                unsigned long offset)
{
    return ((unsigned long)bundle_u16(data, offset) << 16) |
           bundle_u16(data, offset + 2);
}

/* offset + count*stride fits in [0, bytes] without unsigned wraparound. */
static int bundle_fits(long bytes, unsigned long offset,
                       unsigned long count, unsigned long stride)
{
    unsigned long span;

    if (bytes <= 0 || offset > (unsigned long)bytes)
        return 0;
    if (count != 0 && stride > ((unsigned long)-1) / count)
        return 0;
    span = count * stride;
    return span <= (unsigned long)bytes - offset;
}

int avsp_street_bundle_parse(const unsigned char *data, long bytes,
                             AvspStreetBundle *out,
                             unsigned long *frame_offsets, int max_frames,
                             const char **error_name)
{
    int plane;
    int frame;
    unsigned long cursor;

    /* A rejected bundle must leave the view unusable: frames stays 0
       (an invalid count) unless every section validates. */
    out->frames = 0;
    *error_name = (const char *)0;
    if (bytes < (long)AVSP_STREET_HEADER_BYTES ||
        bundle_u32(data, 0) != 0x41565353UL ||
        bundle_u16(data, 4) != 1)
    {
        *error_name = "STRIPS.BIN";
        out->frames = 0;
        return 0;
    }
    out->bytes = bytes;
    out->frames = (int)bundle_u16(data, 6);
    if (out->frames <= 0 || out->frames > max_frames)
    {
        *error_name = "STRIPS FRAMES";
        out->frames = 0;
        return 0;
    }
    /* Fixed region: two 20-byte plane headers, two 512-byte palette
       blocks, six-byte cycle header. Each stretch is proved present
       before anything in it is decoded, and the failure names the first
       section the read stopped short of. */
    if (bytes < 48L)
    {
        *error_name = "STRIPS PLANE";
        out->frames = 0;
        return 0;
    }
    if (bytes < 48L + 2L * (long)AVSP_STREET_PALETTE_BYTES)
    {
        *error_name = "STRIPS PALETTE";
        out->frames = 0;
        return 0;
    }
    if (bytes < (long)AVSP_STREET_CYCLE_HEADER_END)
    {
        *error_name = "STRIPS CYCLE";
        out->frames = 0;
        return 0;
    }
    for (plane = 0; plane < 2; ++plane)
    {
        AvspStreetPlaneInfo *info = &out->plane[plane];
        const unsigned long at = AVSP_STREET_HEADER_BYTES +
            (unsigned long)plane * AVSP_STREET_PLANE_HEADER_BYTES;
        info->cell_cols = (int)bundle_u16(data, at);
        info->cell_rows = (int)bundle_u16(data, at + 2);
        info->world_x0 = (int)bundle_u16(data, at + 4);
        info->row0 = (int)bundle_u16(data, at + 6);
        info->char_count = (int)bundle_u16(data, at + 8);
        info->char_offset = bundle_u32(data, at + 12);
        info->pnt_offset = bundle_u32(data, at + 16);
        if (info->cell_cols <= 0 || info->cell_cols > 128 ||
            info->cell_rows <= 0 || info->cell_rows > 64 ||
            info->char_count <= 0 || info->char_count > 2048 ||
            !bundle_fits(bytes, info->char_offset,
                         (unsigned long)info->char_count, 64UL) ||
            !bundle_fits(bytes, info->pnt_offset,
                         (unsigned long)info->cell_cols *
                         (unsigned long)info->cell_rows, 2UL))
        {
            *error_name = "STRIPS PLANE";
            out->frames = 0;
            return 0;
        }
    }
    out->palette_offset = AVSP_STREET_HEADER_BYTES +
        2UL * AVSP_STREET_PLANE_HEADER_BYTES;   /* 48 */

    out->cycle_period = (int)bundle_u16(data, 48UL + 1024UL);
    out->cycle_first_flip = (int)bundle_u16(data, 48UL + 1026UL);
    out->cycle_entries = (int)bundle_u16(data, 48UL + 1028UL);
    out->cycle_offset = AVSP_STREET_CYCLE_HEADER_END;
    if (!bundle_fits(bytes, out->cycle_offset,
                     (unsigned long)out->cycle_entries, 6UL))
    {
        *error_name = "STRIPS CYCLE";
        out->frames = 0;
        return 0;
    }
    out->scroll_offset = out->cycle_offset +
        (unsigned long)out->cycle_entries * 6UL;
    if (!bundle_fits(bytes, out->scroll_offset,
                     (unsigned long)out->frames, 8UL))
    {
        *error_name = "STRIPS SCROLL";
        out->frames = 0;
        return 0;
    }
    out->patch_offset = out->scroll_offset +
        (unsigned long)out->frames * 8UL;

    /* Patch section: count u16, then per patch a six-byte header whose
       cell count sizes the six-byte cell list. Each header read is
       bounds-proved before it happens; a truncated patch list rejects
       instead of walking past the read region. */
    if (!bundle_fits(bytes, out->patch_offset, 1UL, 2UL))
    {
        *error_name = "STRIPS PATCH";
        out->frames = 0;
        return 0;
    }
    {
        const int patch_count = (int)bundle_u16(data, out->patch_offset);
        int patch;
        cursor = out->patch_offset + 2UL;
        for (patch = 0; patch < patch_count; ++patch)
        {
            unsigned long updates;
            if (!bundle_fits(bytes, cursor, 1UL, 6UL))
            {
                *error_name = "STRIPS PATCH";
                out->frames = 0;
                return 0;
            }
            updates = bundle_u16(data, cursor + 4);
            if (!bundle_fits(bytes, cursor + 6UL, updates, 6UL))
            {
                *error_name = "STRIPS PATCH";
                out->frames = 0;
                return 0;
            }
            cursor += 6UL + updates * 6UL;
        }
    }
    out->objects_offset = cursor;

    /* Per-frame object lists: count u16 then count entries of 8 bytes,
       every frame proved to fit before its offset is published. */
    for (frame = 0; frame < out->frames; ++frame)
    {
        unsigned long count;
        if (!bundle_fits(bytes, cursor, 1UL, 2UL))
        {
            *error_name = "STRIPS OBJECTS";
            out->frames = 0;
            return 0;
        }
        count = bundle_u16(data, cursor);
        if (!bundle_fits(bytes, cursor + 2UL, count, 8UL))
        {
            *error_name = "STRIPS OBJECTS";
            out->frames = 0;
            return 0;
        }
        frame_offsets[frame] = cursor;
        cursor += 2UL + count * 8UL;
    }
    return 1;
}
