#define AVSP_FRONTEND_IMPLEMENTATION
#include "avsp_frontend.h"

#include <string.h>

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

static int load_palette(AvspFrontend *frontend, jo_palette *palette,
                        const char *filename)
{
    unsigned short *data = (unsigned short *)frontend_read(
        frontend, filename, AVSP_FRONTEND_PALETTE_BYTES);
    if (data == JO_NULL) return 0;
    jo_palette_to_cram(data, palette->data, 256);
    jo_free(data);
    return 1;
}

static int load_subpalette(AvspFrontend *frontend, jo_palette *palette,
                           const char *filename, const int subbank)
{
    unsigned short *data;
    if (subbank < 0 || subbank >= 16)
    {
        ++frontend->palette_errors;
        return 0;
    }
    data = (unsigned short *)frontend_read(
        frontend, filename, AVSP_FRONTEND_SUBPALETTE_BYTES);
    if (data == JO_NULL) return 0;
    jo_palette_to_cram(data, palette->data + subbank * 16, 16);
    jo_free(data);
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

void avsp_frontend_draw_title(AvspFrontend *frontend)
{
    int index;
    frontend->vdp1_commands_last_frame = 0;
    if (!frontend->title_objects_ready) return;
    jo_sprite_change_sprite_scale_xy(352.0f / 384.0f, 1.0f);
    for (index = 0; index < AVSP_FRONTEND_TITLE_OBJECT_COUNT; ++index)
    {
        const AvspFrontendTitleObject *object =
            &avsp_frontend_title_objects[index];
        jo_sprite_set_palette_4bits(frontend->title_palette->id,
                                    object->palette_subbank);
        jo_sprite_draw3D(frontend->title_sprites[index], object->centre_x,
                         object->centre_y, 40 + index);
        ++frontend->vdp1_commands_last_frame;
    }
    jo_sprite_restore_sprite_scale();
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
    jo_sprite_change_sprite_scale_xy(352.0f / 384.0f, 1.0f);
    jo_sprite_draw3D(frontend->cursor_sprites[border],
                     avsp_frontend_cursor_centres[cursor][0],
                     avsp_frontend_cursor_centres[cursor][1], 60);
    jo_sprite_draw3D(
        frontend->cursor_sprites[AVSP_FRONTEND_CURSOR_LABEL_CEL],
        avsp_frontend_cursor_centres[cursor][0],
        avsp_frontend_cursor_centres[cursor][1], 61);
    jo_sprite_restore_sprite_scale();
    frontend->vdp1_commands_last_frame = 2;
}

void avsp_frontend_release_select_objects(AvspFrontend *frontend)
{
    if (!frontend->cursor_objects_ready) return;
    jo_sprite_free_from(frontend->cursor_sprites[0]);
    frontend->cursor_objects_ready = 0;
}

void avsp_frontend_lock_disc_reads(AvspFrontend *frontend)
{
    frontend->disc_reads_locked = 1;
}
