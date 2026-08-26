#define AVSP_FRONTEND_IMPLEMENTATION
#include "avsp_frontend.h"

#include <string.h>

#include "avsp_cram.h"

/* Frontend loading runs only at scene boundaries; this unit is built for size. */

#define AVSP_FRONTEND_DIRECTORY "FRONT"
#define AVSP_FRONTEND_BITMAP_STRIDE 512

static void *frontend_read(AvspFrontend *frontend, const char *filename,
                           const int expected_bytes)
{
    int length = 0;
    void *data;
    if (frontend->disc_reads_locked)
    {
        ++frontend->late_disc_reads;
        return JO_NULL;
    }
    data = frontend->read_file(filename, AVSP_FRONTEND_DIRECTORY, &length);
    if (data == JO_NULL || length != expected_bytes)
    {
        if (data != JO_NULL) jo_free(data);
        ++frontend->missing_assets;
        return JO_NULL;
    }
    return data;
}

/* Jo's palette layout is intentionally one-based, and the frontend obeys it
   rather than working around it.  Colour RAM is allocated in 256-entry
   blocks, jo_palette::data is the entry after the block base, and Saturn
   pixel and pen value zero is transparent, so an 8bpp bitmap pixel p and a
   4bpp sprite pen p both read data[p - 1].  Jo's own TGA reader follows the
   same rule by adding one to every decoded pixel, and JO_PALETTE_MAX_COLORS
   is 255 for exactly this reason.

   The converter now emits one-based surfaces and palette files indexed by
   pixel value, so the runtime copies through jo_palette::data with the
   bounded helpers in avsp_cram.h.  Writing at the hardware block base
   instead would alias the preceding allocation's last entry and depend on
   Jo's allocation order; that approach was measured working and rejected.

   This validation exists only to catch a future allocator or ordering change
   that would silently break the assumption the bounded copies rely on. */
static int palette_layout_ok(AvspFrontend *frontend, jo_palette *palette)
{
    /* Only the low three bits of a bitmap palette number reach the colour
       address, so a frontend palette cannot live above CRAM block 7. */
    if (palette->id < 0 || palette->id > 7)
    {
        ++frontend->palette_errors;
        return 0;
    }
    if (palette->data !=
        ((jo_color *)JO_VDP2_CRAM) + palette->id * AVSP_CRAM_BLOCK_ENTRIES + 1)
    {
        ++frontend->palette_errors;
        return 0;
    }
    return 1;
}

/* The two colour-RAM entries a palette must never touch are its block
   boundaries: 256 * id, which is data[-1] and the dead slot above the
   previous allocation's 255 colours, and 256 * (id + 1), which is data[255]
   and the next allocation's first live colour. tests/avsp_cram_test.c proves
   the bounded copies respect that with host canaries; this is the same check
   in situ, so a live load that ever reached a neighbouring allocation is
   counted rather than inferred. Both entries are only sampled, never written,
   so the observation cannot itself disturb them. */
static jo_color *palette_block(jo_palette *palette)
{
    return ((jo_color *)JO_VDP2_CRAM) + palette->id * AVSP_CRAM_BLOCK_ENTRIES;
}

static int load_palette(AvspFrontend *frontend, jo_palette *palette,
                        const char *filename)
{
    unsigned short *data;
    jo_color *block;
    jo_color low;
    jo_color high;
    int copied;
    if (!palette_layout_ok(frontend, palette)) return 0;
    data = (unsigned short *)frontend_read(
        frontend, filename, AVSP_FRONTEND_PALETTE_BYTES);
    if (data == JO_NULL) return 0;
    block = palette_block(palette);
    low = block[0];
    high = block[AVSP_CRAM_BLOCK_ENTRIES];
    copied = avsp_cram_copy_surface((unsigned short *)palette->data, data,
                                    AVSP_CRAM_MAX_COLOURS);
    jo_free(data);
    if (block[0] != low || block[AVSP_CRAM_BLOCK_ENTRIES] != high)
        ++frontend->palette_boundary_writes;
    if (!copied)
    {
        ++frontend->palette_errors;
        return 0;
    }
    return 1;
}

static int load_subpalette(AvspFrontend *frontend, jo_palette *palette,
                           const char *filename, const int subbank)
{
    unsigned short *data;
    jo_color *block;
    jo_color low;
    jo_color high;
    int copied;
    if (!palette_layout_ok(frontend, palette)) return 0;
    data = (unsigned short *)frontend_read(
        frontend, filename, AVSP_FRONTEND_SUBPALETTE_BYTES);
    if (data == JO_NULL) return 0;
    block = palette_block(palette);
    low = block[0];
    high = block[AVSP_CRAM_BLOCK_ENTRIES];
    /* The cel palette files keep an explicit reserved entry zero, so the
       fifteen live colours are file entries 1..15 and land on the hardware
       pens 16 * subbank + 1 .. 16 * subbank + 15 that a 4bpp sprite reads. */
    copied = avsp_cram_copy_subbank((unsigned short *)palette->data, data,
                                    subbank);
    jo_free(data);
    if (block[0] != low || block[AVSP_CRAM_BLOCK_ENTRIES] != high)
        ++frontend->palette_boundary_writes;
    if (!copied)
    {
        ++frontend->palette_errors;
        return 0;
    }
    return 1;
}

static int load_surface(AvspFrontend *frontend, jo_palette *palette,
                        const char *palette_file, const char *rle_file,
                        const int rle_bytes)
{
    unsigned char *rle;
    unsigned int source = 0;
    unsigned int target = 0;
    int y;
    if (!load_palette(frontend, palette, palette_file)) return 0;
    rle = (unsigned char *)frontend_read(frontend, rle_file, rle_bytes);
    if (rle == JO_NULL) return 0;
    for (y = 0; y < AVSP_FRONTEND_HEIGHT; ++y)
        memset(frontend->background_bitmap + y * AVSP_FRONTEND_BITMAP_STRIDE,
               0, AVSP_FRONTEND_BITMAP_STRIDE);
    while (source + 1 < (unsigned int)rle_bytes)
    {
        unsigned int count = rle[source++];
        unsigned char value = rle[source++];
        unsigned int item;
        if (count == 0 || target + count > AVSP_FRONTEND_DECODED_BYTES)
        {
            ++frontend->rle_errors;
            jo_free(rle);
            return 0;
        }
        for (item = 0; item < count; ++item)
        {
            unsigned int pixel = target + item;
            unsigned int row = pixel / AVSP_FRONTEND_WIDTH;
            unsigned int column = pixel - row * AVSP_FRONTEND_WIDTH;
            frontend->background_bitmap[
                row * AVSP_FRONTEND_BITMAP_STRIDE + column] = value;
        }
        target += count;
    }
    jo_free(rle);
    if (source != (unsigned int)rle_bytes ||
        target != AVSP_FRONTEND_DECODED_BYTES)
    {
        ++frontend->rle_errors;
        return 0;
    }
    /* An opaque fitted page must be entirely one-based. A zero pixel would
       read the entry below jo_palette::data, which belongs to the preceding
       allocation, so treat it as a decode failure rather than rendering a
       neighbouring palette's colour. */
    for (y = 0; y < AVSP_FRONTEND_HEIGHT; ++y)
        if (!avsp_cram_surface_is_one_based(
                frontend->background_bitmap + y * AVSP_FRONTEND_BITMAP_STRIDE,
                AVSP_FRONTEND_WIDTH))
        {
            ++frontend->rle_errors;
            return 0;
        }
    return 1;
}

static int add_sprite(AvspFrontend *frontend, const char *filename,
                      const int expected_bytes, const int width,
                      const int height)
{
    jo_img_4bits image;
    int sprite;
    image.width = width;
    image.height = height;
    image.data = (unsigned char *)frontend_read(
        frontend, filename, expected_bytes);
    if (image.data == JO_NULL) return -1;
    sprite = jo_sprite_add_4bits_image(&image);
    jo_free(image.data);
    if (sprite < 0) ++frontend->missing_assets;
    return sprite;
}

void avsp_frontend_init(AvspFrontend *frontend,
                        AvspFrontendReadFile read_file,
                        unsigned char *background_bitmap,
                        jo_palette *title_palette,
                        jo_palette *select_palette)
{
    int index;
    memset(frontend, 0, sizeof(*frontend));
    frontend->read_file = read_file;
    frontend->background_bitmap = background_bitmap;
    frontend->title_palette = title_palette;
    frontend->select_palette = select_palette;
    for (index = 0; index < AVSP_FRONTEND_TITLE_OBJECT_COUNT; ++index)
        frontend->title_sprites[index] = -1;
    for (index = 0; index < AVSP_FRONTEND_CURSOR_CEL_COUNT; ++index)
        frontend->cursor_sprites[index] = -1;
    for (index = 0; index < AVSP_FRONTEND_START_INTRO_COUNT; ++index)
        frontend->transition_sprites[index] = -1;
    for (index = 0; index < AVSP_FRONTEND_R1TEXT_OBJECT_COUNT; ++index)
        frontend->r1text_sprites[index] = -1;
    frontend->r1text_fade_row = -1;
    frontend->mask_sprite = -1;
    if (title_palette == JO_NULL || select_palette == JO_NULL ||
        title_palette->data == JO_NULL || select_palette->data == JO_NULL ||
        select_palette->id != title_palette->id + 1)
        ++frontend->palette_errors;
}

int avsp_frontend_load_title_surface(AvspFrontend *frontend)
{
    if (frontend->palette_errors || frontend->background_bitmap == JO_NULL)
        return 0;
    if (!load_surface(frontend, frontend->title_palette,
                      AVSP_FRONTEND_TITLE_PALETTE_FILE,
                      AVSP_FRONTEND_TITLE_RLE_FILE,
                      AVSP_FRONTEND_TITLE_RLE_BYTES))
        return 0;
    frontend->title_surface_ready = 1;
    return 1;
}

int avsp_frontend_load_title_objects(AvspFrontend *frontend)
{
    int index;
    if (!load_subpalette(frontend, frontend->title_palette,
                         AVSP_FRONTEND_TITLE_PALETTE_A_FILE,
                         AVSP_FRONTEND_TITLE_PALETTE_A_SUBBANK) ||
        !load_subpalette(frontend, frontend->title_palette,
                         AVSP_FRONTEND_TITLE_PALETTE_B_FILE,
                         AVSP_FRONTEND_TITLE_PALETTE_B_SUBBANK))
        return 0;
    for (index = 0; index < AVSP_FRONTEND_TITLE_OBJECT_COUNT; ++index)
    {
        const AvspFrontendTitleObject *object =
            &avsp_frontend_title_objects[index];
        frontend->title_sprites[index] = add_sprite(
            frontend, object->filename, object->bytes,
            object->width, object->height);
        if (frontend->title_sprites[index] < 0) return 0;
    }
    frontend->title_objects_ready = 1;
    return 1;
}

int avsp_frontend_load_round1_text(AvspFrontend *frontend)
{
    int index;
    if (frontend->r1text_ready) return 1;
    for (index = 0; index < AVSP_FRONTEND_R1TEXT_OBJECT_COUNT; ++index)
    {
        const AvspFrontendTransitionObject *object =
            &avsp_frontend_r1text_objects[index];
        frontend->r1text_sprites[index] = add_sprite(
            frontend, object->filename, object->bytes,
            object->width, object->height);
        if (frontend->r1text_sprites[index] < 0) return 0;
    }
    if (frontend->r1text_fade == JO_NULL)
    {
        frontend->r1text_fade = (unsigned short *)frontend_read(
            frontend, AVSP_FRONTEND_R1TEXT_PALETTE_FILE,
            AVSP_FRONTEND_R1TEXT_FADE_ROWS *
                AVSP_FRONTEND_R1TEXT_FADE_ROW_BYTES);
        if (frontend->r1text_fade == JO_NULL) return 0;
    }
    frontend->r1text_fade_row = -1;
    frontend->r1text_ready = 1;
    return 1;
}

void avsp_frontend_release_title_objects(AvspFrontend *frontend)
{
    if (!frontend->title_objects_ready) return;
    jo_sprite_free_from(frontend->title_sprites[0]);
    frontend->title_objects_ready = 0;
}

int avsp_frontend_enter_select(AvspFrontend *frontend)
{
    int index;
    if (frontend->select_surface_ready && frontend->cursor_objects_ready)
        return 1;
    avsp_frontend_release_title_objects(frontend);
    if (!load_surface(frontend, frontend->select_palette,
                      AVSP_FRONTEND_SELECT_PALETTE_FILE,
                      AVSP_FRONTEND_SELECT_RLE_FILE,
                      AVSP_FRONTEND_SELECT_RLE_BYTES) ||
        !load_subpalette(frontend, frontend->select_palette,
                         AVSP_FRONTEND_MASK_PALETTE_FILE,
                         AVSP_FRONTEND_MASK_PALETTE_SUBBANK) ||
        !load_subpalette(frontend, frontend->select_palette, "CURSOR.PAL",
                         AVSP_FRONTEND_CURSOR_PALETTE_SUBBANK))
        return 0;
    for (index = 0; index < AVSP_FRONTEND_CURSOR_CEL_COUNT; ++index)
    {
        const AvspFrontendCursorCel *cel = &avsp_frontend_cursor_cels[index];
        frontend->cursor_sprites[index] = add_sprite(
            frontend, cel->filename, cel->bytes, cel->width, cel->height);
        if (frontend->cursor_sprites[index] < 0) return 0;
    }
    frontend->mask_sprite = add_sprite(
        frontend, AVSP_FRONTEND_MASK_FILE, AVSP_FRONTEND_MASK_BYTES, 8, 8);
    if (frontend->mask_sprite < 0) return 0;
    for (index = 0; index < AVSP_FRONTEND_START_INTRO_COUNT; ++index)
    {
        const AvspFrontendTransitionObject *object =
            &avsp_frontend_transition_objects[index];
        frontend->transition_sprites[index] = add_sprite(
            frontend, object->filename, object->bytes,
            object->width, object->height);
        if (frontend->transition_sprites[index] < 0) return 0;
    }
    if (!avsp_frontend_load_round1_text(frontend)) return 0;
    frontend->select_surface_ready = 1;
    frontend->cursor_objects_ready = 1;
    return 1;
}

void avsp_frontend_activate_title(AvspFrontend *frontend)
{
    if (!frontend->title_surface_ready) return;
    slBMPaletteNbg1((unsigned short)frontend->title_palette->id);
    jo_move_background(0, 0);
}

void avsp_frontend_activate_select(AvspFrontend *frontend)
{
    if (!frontend->select_surface_ready) return;
    slBMPaletteNbg1((unsigned short)frontend->select_palette->id);
    jo_move_background(0, 0);
}

/* Horizontal fit of the 384-pixel CPS field into 352 Saturn pixels: the
 * "endpoint-aligned-nearest" mapping recorded in the asset manifest's
 * geometry block. Vertical is 1:1, so all 224 source lines are preserved. */
static int fit_source_x(const int source_x)
{
    return (source_x * AVSP_FRONTEND_WIDTH) / AVSP_FRONTEND_SOURCE_WIDTH;
}

/* Emit one VDP1 quad covering exactly the fitted source rectangle.
 *
 * jo_sprite_draw3D() cannot place these. When the horizontal and vertical
 * scales differ it routes to slDispSpriteHV() with a deliberately non-zero
 * angle, an SGL workaround, which rotates the quad by a fraction of a
 * degree. Read back from the live command table, that placed every object
 * two scanlines too tall and sheared its right edge one pixel below its
 * left. Four explicit corners remove both: the quad is integral and
 * inclusive by construction, so a cel occupies exactly its measured rows. */
static void draw_source_rect(AvspFrontend *frontend, const int sprite,
                             const int source_x, const int source_y,
                             const int width, const int height,
                             const int depth)
{
    jo_pos2D_fixed corners[4];
    int left;
    int right;
    int top;
    int bottom;
    if (sprite < 0 || width <= 0 || height <= 0) return;
    left = fit_source_x(source_x) - AVSP_FRONTEND_WIDTH / 2;
    right = fit_source_x(source_x + width) - 1 - AVSP_FRONTEND_WIDTH / 2;
    top = source_y - AVSP_FRONTEND_HEIGHT / 2;
    bottom = source_y + height - 1 - AVSP_FRONTEND_HEIGHT / 2;
    corners[0].x = jo_int2fixed(left);
    corners[0].y = jo_int2fixed(top);
    corners[1].x = jo_int2fixed(right);
    corners[1].y = jo_int2fixed(top);
    corners[2].x = jo_int2fixed(right);
    corners[2].y = jo_int2fixed(bottom);
    corners[3].x = jo_int2fixed(left);
    corners[3].y = jo_int2fixed(bottom);
    jo_sprite_draw_4p_fixed(sprite, corners, jo_int2fixed(depth), true);
    ++frontend->vdp1_commands_last_frame;
}

void avsp_frontend_draw_title(AvspFrontend *frontend)
{
    int index;
    frontend->vdp1_commands_last_frame = 0;
    if (!frontend->title_objects_ready) return;
    for (index = 0; index < AVSP_FRONTEND_TITLE_OBJECT_COUNT; ++index)
    {
        const AvspFrontendTitleObject *object =
            &avsp_frontend_title_objects[index];
        jo_sprite_set_palette_4bits(frontend->title_palette->id,
                                    object->palette_subbank);
        draw_source_rect(frontend, frontend->title_sprites[index],
                         object->source_x, object->source_y,
                         object->width, object->height, 40 + index);
    }
}

static void draw_mask_bar(AvspFrontend *frontend, const int first_row,
                          const int last_row, const int depth)
{
    int height;
    if (first_row > last_row) return;
    height = last_row - first_row + 1;
    draw_source_rect(frontend, frontend->mask_sprite, 0, first_row,
                     AVSP_FRONTEND_SOURCE_WIDTH, height, depth);
}

void avsp_frontend_draw_start_transition(AvspFrontend *frontend,
                                         int transition_frame)
{
    frontend->vdp1_commands_last_frame = 0;
    if (!frontend->cursor_objects_ready) return;
    if (transition_frame < 0) transition_frame = 0;
    if (transition_frame < AVSP_FRONTEND_START_MASK_FRAMES)
    {
        int top_mask_end;
        int bottom_mask_start;
        if (transition_frame < 5)
        {
            top_mask_end = AVSP_FRONTEND_HEIGHT - 1;
            bottom_mask_start = AVSP_FRONTEND_HEIGHT;
        }
        else if (transition_frame < 25)
        {
            int reveal_frame = transition_frame - 5;
            top_mask_end = 127 - reveal_frame * 4;
            bottom_mask_start = 136 + reveal_frame * 4;
        }
        else if (transition_frame == 25)
        {
            top_mask_end = 51;
            bottom_mask_start = 212;
        }
        else
        {
            top_mask_end = -1;
            bottom_mask_start = AVSP_FRONTEND_HEIGHT;
        }
        jo_sprite_set_palette_4bits(frontend->select_palette->id,
                                    AVSP_FRONTEND_MASK_PALETTE_SUBBANK);
        draw_mask_bar(frontend, 0, top_mask_end, 90);
        draw_mask_bar(frontend, bottom_mask_start,
                      AVSP_FRONTEND_HEIGHT - 1, 91);
    }
    else
    {
        int index = transition_frame - AVSP_FRONTEND_START_MASK_FRAMES;
        if (index < AVSP_FRONTEND_START_INTRO_COUNT)
        {
            const AvspFrontendTransitionObject *object =
                &avsp_frontend_transition_objects[index];
            jo_sprite_set_palette_4bits(frontend->select_palette->id,
                                        AVSP_FRONTEND_CURSOR_PALETTE_SUBBANK);
            draw_source_rect(frontend, frontend->transition_sprites[index],
                             object->source_x, object->source_y,
                             object->width, object->height, 60);
        }
    }
}

/* Place one cursor cel at its measured source rectangle: the position's
 * label anchor plus that cel's own offset from the anchor. */
static void draw_cursor_cel(AvspFrontend *frontend, const int cel,
                            const int cursor, const int depth)
{
    const AvspFrontendCursorCel *definition =
        &avsp_frontend_cursor_cels[cel];
    draw_source_rect(frontend, frontend->cursor_sprites[cel],
                     avsp_frontend_cursor_anchors[cursor][0] +
                         definition->source_offset_x,
                     avsp_frontend_cursor_anchors[cursor][1] +
                         definition->source_offset_y,
                     definition->width, definition->height, depth);
}

void avsp_frontend_draw_cursor(AvspFrontend *frontend, int cursor,
                               int animation_frame, int visible)
{
    int border;
    frontend->vdp1_commands_last_frame = 0;
    if (!frontend->cursor_objects_ready || !visible) return;
    if (cursor < 0 || cursor >= 4) cursor = 0;
    if (animation_frame < 0) animation_frame = 0;
    border = avsp_frontend_cursor_cycle[
        animation_frame % AVSP_FRONTEND_CURSOR_PERIOD];
    jo_sprite_set_palette_4bits(frontend->select_palette->id,
                                AVSP_FRONTEND_CURSOR_PALETTE_SUBBANK);
    draw_cursor_cel(frontend, border, cursor, 60);
    draw_cursor_cel(frontend, AVSP_FRONTEND_CURSOR_LABEL_CEL, cursor, 61);
}

/* Copy one measured fade row of the Round 1 text bank into its sub-bank.
 * The rows are the source's own sixteen per-frame palette states, so the
 * fade is reproduced by lookup rather than by modelling the ramp. */
void avsp_frontend_set_r1text_fade(AvspFrontend *frontend, int row)
{
    jo_color *block;
    jo_color low;
    jo_color high;
    if (!frontend->r1text_ready || frontend->r1text_fade == JO_NULL) return;
    if (row < 0) row = 0;
    if (row >= AVSP_FRONTEND_R1TEXT_FADE_ROWS)
        row = AVSP_FRONTEND_R1TEXT_FADE_ROWS - 1;
    if (row == frontend->r1text_fade_row) return;
    if (!palette_layout_ok(frontend, frontend->select_palette)) return;
    block = palette_block(frontend->select_palette);
    low = block[0];
    high = block[AVSP_CRAM_BLOCK_ENTRIES];
    if (!avsp_cram_copy_subbank(
            (unsigned short *)frontend->select_palette->data,
            frontend->r1text_fade + row *
                (AVSP_FRONTEND_R1TEXT_FADE_ROW_BYTES / 2),
            AVSP_FRONTEND_R1TEXT_PALETTE_SUBBANK))
        ++frontend->palette_errors;
    if (block[0] != low || block[AVSP_CRAM_BLOCK_ENTRIES] != high)
        ++frontend->palette_boundary_writes;
    frontend->r1text_fade_row = row;
}

/* Both measured text lines. Callers zero vdp1_commands_last_frame at the
 * start of the frame, so this only accumulates and can follow the cursor
 * draw inside the confirm state. */
void avsp_frontend_draw_round1_text(AvspFrontend *frontend)
{
    int index;
    if (!frontend->r1text_ready) return;
    jo_sprite_set_palette_4bits(frontend->select_palette->id,
                                AVSP_FRONTEND_R1TEXT_PALETTE_SUBBANK);
    for (index = 0; index < AVSP_FRONTEND_R1TEXT_OBJECT_COUNT; ++index)
    {
        const AvspFrontendTransitionObject *object =
            &avsp_frontend_r1text_objects[index];
        draw_source_rect(frontend, frontend->r1text_sprites[index],
                         object->source_x, object->source_y,
                         object->width, object->height, 60 + index);
    }
}

void avsp_frontend_release_select_objects(AvspFrontend *frontend)
{
    if (!frontend->cursor_objects_ready) return;
    jo_sprite_free_from(frontend->cursor_sprites[0]);
    frontend->cursor_objects_ready = 0;
    frontend->r1text_ready = 0;
}

void avsp_frontend_lock_disc_reads(AvspFrontend *frontend)
{
    frontend->disc_reads_locked = 1;
}
