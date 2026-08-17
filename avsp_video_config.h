#ifndef AVSP_VIDEO_CONFIG_H
#define AVSP_VIDEO_CONFIG_H

/*
 * CPS2 Alien vs. Predator renders a 384x224 active picture.  The Saturn has
 * no 384-pixel low-resolution mode; 352x224 is its closest native mode and
 * preserves the arcade's 224 scanlines. Full-width presentation reduces the
 * horizontal axis only, while exact mode retains the 1:1 center crop. Jo
 * Engine normally selects 320x240 for NTSC, so this header is force-included
 * for the game and every engine translation unit.
 */
#include <jo/conf.h>

#undef JO_TV_RES
#undef JO_TV_WIDTH
#undef JO_TV_WIDTH_2
#undef JO_TV_WIDTH_4
#undef JO_TV_HEIGHT
#undef JO_TV_HEIGHT_2
#undef JO_TV_HEIGHT_4

#define JO_TV_RES      (TV_352x224)
#define JO_TV_WIDTH    (352)
#define JO_TV_WIDTH_2  (176)
#define JO_TV_WIDTH_4  (88)
#define JO_TV_HEIGHT   (224)
#define JO_TV_HEIGHT_2 (112)
#define JO_TV_HEIGHT_4 (56)

#endif
