/* Gate for the sound command path. Own driver: it also carries the Z80 mailbox. Registers appear only here. */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "avsrc_audio.h"
static AvsrcMem g_mem, g_old;
static AudioLink g_link, g_link_old;
static AudioMusicFade g_fades[11];
static u32 r[15];                      /* d0..d7, a0..a6 */
static void load_fades(void)
{
    /* Build data: read from the private image, never committed. */
    FILE *f = fopen("/mnt/c/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-playable-loop-pivot/.deps/mame/actorprobe/decrypted_opcodes_2m.bin", "rb");
    u8 b[44]; int i;
    if (!f || fseek(f, 0x3c32L, SEEK_SET) || fread(b, 1, 44, f) != 44) exit(3);
    fclose(f);
    for (i = 0; i < 11; i++) {
        g_fades[i].delay_frames = (u16)((b[i * 4] << 8) | b[i * 4 + 1]);
        g_fades[i].rate = (u16)((b[i * 4 + 2] << 8) | b[i * 4 + 3]);
    }
}
static void seed(u32 a, unsigned v)
{
    if (a >= 0xff0000u) g_mem.ram[a - 0xff0000u] = (u8)v;
    else if (a == 0x619ffdu) g_link.stereo = (u8)v;
    else if (a >= 0x618001u && a < 0x618020u) g_link.mailbox[(a - 0x618001u) / 2] = (u8)v;
}
static int run(const char *n)
{
    static const struct { const char *name; u32 toggle; u16 first, second; } alts[] = {
        {"audio_alt_1aa6", 0xff0ea4u, 0x35, 0x100}, {"audio_alt_1ad0", 0xff0ea5u, 0x36, 0x101},
        {"audio_alt_1afa", 0xff0ea6u, 0x37, 0x102}, {"audio_alt_1b24", 0xff0ea7u, 0x38, 0x103},
        {"audio_alt_1b4e", 0xff0ea8u, 0x39, 0x104}
    };
    static const struct { const char *name; unsigned control; } ctrl[] = {
        {"audio_control_6", 6}, {"audio_control_7", 7}, {"audio_control_8", 8}, {"audio_control_9", 9},
        {"audio_control_c", 0xc}, {"audio_control_d", 0xd}
    };
    unsigned i;
    for (i = 0; i < sizeof alts / sizeof alts[0]; i++)
        if (!strcmp(n, alts[i].name)) { audio_play_alternating(&g_mem, r[14], alts[i].toggle, alts[i].first, alts[i].second); return 1; }
    for (i = 0; i < sizeof ctrl / sizeof ctrl[0]; i++)
        if (!strcmp(n, ctrl[i].name)) { audio_control(&g_mem, ctrl[i].control, (u16)r[0]); return 1; }
    if (!strcmp(n, "audio_ring_clear")) audio_ring_clear(&g_mem);
    else if (!strcmp(n, "audio_enqueue_always")) audio_enqueue_always(&g_mem, r[1], r[2], r[3]);
    else if (!strcmp(n, "audio_enqueue")) audio_enqueue(&g_mem, r[1], r[2], r[3]);
    else if (!strcmp(n, "audio_send_pending")) audio_send_pending(&g_mem, &g_link);
    else if (!strcmp(n, "audio_vblank_tick")) audio_vblank_tick(&g_mem, &g_link);
    else if (!strcmp(n, "audio_stop_all")) audio_stop_all(&g_mem);
    else if (!strcmp(n, "audio_key_off_channel")) audio_key_off_channel(&g_mem, r[0] & 0xffu);
    else if (!strcmp(n, "audio_stop_music")) audio_stop_music(&g_mem);
    else if (!strcmp(n, "audio_control_a")) audio_control(&g_mem, 0xa, 0);
    else if (!strcmp(n, "audio_control_b")) audio_control(&g_mem, 0xb, 0);
    else if (!strcmp(n, "audio_music_request")) audio_music_request(&g_mem, g_fades, r[0]);
    else return 0;
    return 1;
}
int main(void)
{
    char name[64];
    load_fades();
    while (scanf("%63s", name) == 1) {
        int i, n; u32 k;
        for (i = 0; i < 15; i++) scanf("%x", &r[i]);
        memset(&g_mem, 0, sizeof g_mem);
        memset(&g_link, 0, sizeof g_link);
        scanf("%d", &n);
        for (i = 0; i < n; i++) { u32 a; unsigned v; scanf("%x %x", &a, &v); seed(a, v); }
        g_old = g_mem; g_link_old = g_link;
        if (!run(name)) return 2;
        for (k = 0; k < 16; k++) if (g_link.mailbox[k] != g_link_old.mailbox[k]) printf("m:%x:%x ", 0x618001u + 2 * k, g_link.mailbox[k]);
        if (g_link.stereo != g_link_old.stereo) printf("m:%x:%x ", 0x619ffdu, g_link.stereo);
        for (k = 0; k < AVSRC_RAM_SIZE; k++) if (g_mem.ram[k] != g_old.ram[k] && !(k >= 0x0e88u && k < 0x0e9cu)) printf("m:%x:%x ", 0xff0000u + k, g_mem.ram[k]);
        printf("\n");
    }
    return 0;
}
