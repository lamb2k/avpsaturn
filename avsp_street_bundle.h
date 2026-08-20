#ifndef AVSP_STREET_BUNDLE_H
#define AVSP_STREET_BUNDLE_H

/* RP4 street strip bundle (STRIPS.BIN v1) parser and validator.
 *
 * Pure, platform-free (C90, no libc): every header, palette, cycle,
 * scroll, patch, and object section is bounds-checked against the actual
 * read length BEFORE any consumer dereferences it. main.c calls this from
 * street_setup; the host test feeds corrupt and truncated bundles and
 * requires every case to reject with the exact section name without
 * reading outside the buffer.
 *
 * Layout (big-endian): magic 'AVSS' u32, schema u16 = 1, frame_count u16;
 * two 20-byte plane headers; two 256-entry RGB555 palettes; cycle block
 * (period u16, first_flip u16, entry_count u16, entries of 6 bytes);
 * scroll table frame_count x 8 bytes; patch section (count u16, then per
 * patch: frame_rel u16, plane u16, cell_count u16, cells of 6 bytes);
 * per-frame object lists (count u16, entries of 8 bytes); character
 * pools and base pattern grids at the offsets the plane headers name. */

typedef struct
{
    int cell_cols;
    int cell_rows;
    int world_x0;
    int row0;
    int char_count;
    unsigned long char_offset;
    unsigned long pnt_offset;
} AvspStreetPlaneInfo;

typedef struct
{
    long bytes;
    int frames;
    AvspStreetPlaneInfo plane[2];
    unsigned long palette_offset;   /* two 512-byte blocks              */
    int cycle_period;
    int cycle_first_flip;
    int cycle_entries;
    unsigned long cycle_offset;
    unsigned long scroll_offset;
    unsigned long patch_offset;
    unsigned long objects_offset;
} AvspStreetBundle;

/* Validate and index the bundle. frame_offsets receives the per-frame
 * object-list offsets (max_frames capacity). Returns 0 on success and
 * fills *error_name with a stable section name on failure:
 * "STRIPS.BIN" (header/magic/schema), "STRIPS FRAMES", "STRIPS PLANE",
 * "STRIPS PALETTE", "STRIPS CYCLE", "STRIPS SCROLL", "STRIPS PATCH",
 * "STRIPS OBJECTS". */
int avsp_street_bundle_parse(const unsigned char *data, long bytes,
                             AvspStreetBundle *out,
                             unsigned long *frame_offsets, int max_frames,
                             const char **error_name);

#endif
