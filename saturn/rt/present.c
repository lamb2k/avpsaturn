void __attribute__((weak)) sat_gfx_init(void) { }
void __attribute__((weak)) sat_gfx_frame(void) { }
void __attribute__((weak)) sat_present(void) { sat_gfx_frame(); }
