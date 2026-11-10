/* Host test of wv_sfx(): the bytes it sends to the player's mailbox. The stub plays sat_audio_io_write8's role (saturn/audio/sat_audio.c): mailbox[(addr - 0x618001) >> 1] = value for addr 0x618001..0x61801d,
   and a write of 0 to 0x61801f publishes the entry. Prints one line per published entry: command, pan, and whether bytes 2..6 and 8..14 are zero. */
#include <stdio.h>
#include "../saturn/guests/wolverine/wv_sound.h"
static unsigned char mb[16];
void sat_audio_io_write8(unsigned long addr, unsigned long value)
{
    if (addr == 0x61801fUL) {
        int i, z = 1;
        for (i = 2; i < 15; i++) if (i != 7 && mb[i]) z = 0;
        printf("%02x%02x pan %02x zero %d\n", mb[0], mb[1], mb[7], z);
        return;
    }
    if (addr < 0x618001UL || addr > 0x61801dUL || !(addr & 1)) { printf("BAD ADDRESS %lx\n", addr); return; }
    mb[(addr - 0x618001UL) >> 1] = (unsigned char)value;
}
int main(void)
{
    wv_sfx(WV_SFX_BERSERKER);
    wv_sfx_pan(WV_SFX_KO, 0x03);
    wv_sfx_pan(WV_SFX_KO, 0x99);   /* out of range: centre */
    wv_sfx(WV_SFX_COUNT);          /* unknown id: nothing */
    wv_sfx(-1);
    return 0;
}
