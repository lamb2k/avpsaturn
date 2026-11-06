/* Standalone proof image: one scene dump, the library, nothing else. Two game frames then frozen, so a still matches MAME's.
 * ROM-derived data comes in by .incbin at build time from E:\AvP\learning\lane-satgfx; never committed. */
#include "sat_gfx.h"
extern unsigned char __bss_start[], __bss_end[];
extern const unsigned char scene_ram[], scene_gfx[], scene_obj[], scene_pack[];
unsigned char *PAGE[256];
unsigned char RAMB[0x10000] __attribute__((aligned(4)));
static unsigned char OBJ[0x10000] __attribute__((aligned(4)));
volatile unsigned long scene_done;
volatile unsigned long scene_ticks[2];
#define TVSTAT (*(volatile unsigned short *)0x25F80004UL)
#define FRTH (*(volatile unsigned char *)0xFFFFFE12UL)
#define FRTL (*(volatile unsigned char *)0xFFFFFE13UL)
#define TCR (*(volatile unsigned char *)0xFFFFFE16UL)
static void wait_vblank(void) { while (TVSTAT & 8) ; while (!(TVSTAT & 8)) ; }
static void copy(unsigned char *d, const unsigned char *s, unsigned long n) { while (n--) *d++ = *s++; }
static unsigned long ticks(void) { unsigned long h = FRTH; return (h << 8) | FRTL; }
static void timed(int i) { unsigned long a; FRTH = 0; FRTL = 0; a = ticks(); sat_gfx_frame(); scene_ticks[i] = ticks() - a; }
void start(void) __attribute__((section(".text.start")));
void start(void)
{
    int i;
    unsigned char *z;
    for (z = __bss_start; z < __bss_end; z++) *z = 0; /* the BIOS loads the image and no more */
    TCR = 2; /* tick every 128 clocks */
    copy(RAMB, scene_ram, 0x10000);
    for (i = 0; i < 3; i++) PAGE[0x90 + i] = (unsigned char *)scene_gfx + 0x10000UL * i;
    PAGE[0x70] = OBJ;
    /* The whole path runs twice on one state, so the list on show has been through the frame swap. */
    copy(OBJ + 0x8000, scene_obj, 0x2000);
    if (!sat_gfx_init(scene_pack)) { scene_done = 0xbad; for (;;) ; }
    wait_vblank();
    timed(0);
    wait_vblank();
    timed(1);
    wait_vblank();
    wait_vblank();
    scene_done = 1;
    for (;;) ;
}
__asm__(".section .rodata\n.balign 4\n"
        ".global _scene_ram\n_scene_ram: .incbin \"ram.bin\"\n"
        ".balign 4\n.global _scene_gfx\n_scene_gfx: .incbin \"gfx.bin\"\n"
        ".balign 4\n.global _scene_obj\n_scene_obj: .incbin \"obj.bin\"\n"
        ".balign 4\n.global _scene_pack\n_scene_pack: .incbin \"pack.bin\"\n.text\n");
