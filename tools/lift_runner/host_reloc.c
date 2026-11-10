/* HOST only (lane wv-native-gfx, plan V2 section 5): the relocated animation block. WVBLOCK=file holds the block as it sits in the 68000 window at 0x300000
   (tools/wolverine/reloc_block.py), WVSLOTS=file the 68000 addresses of the opcode-store slots that hold one of Schaefer's table bases (access_audit.py --emit-host),
   WVDELTA (hex, default 19d070) the block's delta. Each slot gets the delta added, the page table maps 0x30, and wv_anim_delta (read by the code immediates the build
   rewrites to WVB()) is set. Without WVBLOCK nothing happens: the runner is the plain one. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef unsigned char u8; typedef unsigned int u32;
extern u8 *PAGE[256];
extern u8 *OPB;
unsigned wv_anim_delta;
static u8 blk[0x10000];
void wv_reloc_init(void)
{
    const char *b = getenv("WVBLOCK"), *s = getenv("WVSLOTS");
    FILE *f; char l[64]; int n = 0;
    if (!b || !s) return;
    unsigned sd = (unsigned)strtoul(getenv("WVDELTA") ? getenv("WVDELTA") : "19d070", 0, 16);
    wv_anim_delta = getenv("WVNOIMM") ? 0 : sd;   /* WVNOIMM: slots only (bisecting) */
    f = fopen(b, "rb"); if (!f || !fread(blk, 1, sizeof blk, f)) { puts("WVBLOCK unreadable"); exit(9); } fclose(f);
    PAGE[0x30] = blk;
    f = fopen(s, "r"); if (!f) { puts("WVSLOTS unreadable"); exit(9); }
    while (fgets(l, sizeof l, f)) {
        u32 a = (u32)strtoul(l, 0, 16), v;
        if (!a) continue;
        v = (u32)OPB[a] << 24 | (u32)OPB[a + 1] << 16 | (u32)OPB[a + 2] << 8 | OPB[a + 3];
        if (!getenv("WVNOSLOT")) v += sd;
        OPB[a] = (u8)(v >> 24); OPB[a + 1] = (u8)(v >> 16); OPB[a + 2] = (u8)(v >> 8); OPB[a + 3] = (u8)v;
        n++;
    }
    fclose(f);
    if (getenv("WVTNEW")) {   /* his box table T': the per-character entry of character 1 (0x19748) names it */
        u32 a = 0x19748, v = (u32)strtoul(getenv("WVTNEW"), 0, 16);
        OPB[a] = (u8)(v >> 24); OPB[a + 1] = (u8)(v >> 16); OPB[a + 2] = (u8)(v >> 8); OPB[a + 3] = (u8)v;
    }
    printf("relocation: delta %x, %d slots patched, window 0x300000\n", wv_anim_delta, n); fflush(stdout);
}
