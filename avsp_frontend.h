#ifndef AVSP_FRONTEND_H
#define AVSP_FRONTEND_H

#include <jo/jo.h>

#include "generated/avsp_frontend.h"

#define AVSP_FRONTEND_SCENES 2

typedef char *(*AvspFrontendReadFile)(const char *filename,
                                      const char *sub_dir,
                                      int *length);

typedef struct
{
    AvspFrontendReadFile read_file;
    unsigned char *background_bitmap;
    jo_palette *title_palette;
    jo_palette *select_palette;
    int title_sprites[AVSP_FRONTEND_TITLE_OBJECT_COUNT];
    int cursor_sprites[AVSP_FRONTEND_CURSOR_CEL_COUNT];
    int transition_sprites[AVSP_FRONTEND_START_INTRO_COUNT];
    int r1text_sprites[AVSP_FRONTEND_R1TEXT_OBJECT_COUNT];
    /* All sixteen measured fade rows of the text bank, resident so the
       per-frame fade never reads the disc while CDDA owns it. */
    unsigned short *r1text_fade;
    int r1text_fade_row;
    int r1text_ready;
    int mask_sprite;
    int title_surface_ready;
    int title_objects_ready;
    int select_surface_ready;
    int cursor_objects_ready;
    int disc_reads_locked;
    int late_disc_reads;
    int missing_assets;
    int palette_errors;
    /* Live counterpart of tests/avsp_cram_test.c's canaries: a load that
       reached hardware entry 256*id or 256*(id+1) is counted here. */
    int palette_boundary_writes;
    int rle_errors;
    int vdp1_commands_last_frame;
} AvspFrontend;

void avsp_frontend_init(AvspFrontend *frontend,
                        AvspFrontendReadFile read_file,
                        unsigned char *background_bitmap,
                        jo_palette *title_palette,
                        jo_palette *select_palette);
int avsp_frontend_load_title_surface(AvspFrontend *frontend);
int avsp_frontend_load_title_objects(AvspFrontend *frontend);
int avsp_frontend_load_round1_text(AvspFrontend *frontend);
int avsp_frontend_enter_select(AvspFrontend *frontend);
void avsp_frontend_activate_title(AvspFrontend *frontend);
void avsp_frontend_activate_select(AvspFrontend *frontend);
void avsp_frontend_draw_title(AvspFrontend *frontend);
void avsp_frontend_draw_start_transition(AvspFrontend *frontend,
                                         int transition_frame);
void avsp_frontend_draw_cursor(AvspFrontend *frontend, int cursor,
                               int animation_frame, int visible);
void avsp_frontend_set_r1text_fade(AvspFrontend *frontend, int row);
void avsp_frontend_draw_round1_text(AvspFrontend *frontend);
void avsp_frontend_release_title_objects(AvspFrontend *frontend);
void avsp_frontend_release_select_objects(AvspFrontend *frontend);
void avsp_frontend_lock_disc_reads(AvspFrontend *frontend);

#endif
