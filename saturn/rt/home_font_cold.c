/* Menu font cells and text palettes in the cart tail (SAT_HOME_FONT_COLD, lane perf-reconcile 11-10): same bytes as the arrays in sat_gfx.c, off high work RAM. ROM-derived, from WORK/gen. */
typedef unsigned char u8;
const u8 sat_home_font[58 * 32] __attribute__((aligned(4))) = {
#include "home_font.inc"
};
const u8 sat_home_pal[64] __attribute__((aligned(2))) = {
#include "home_pal.inc"
};
