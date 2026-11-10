/* Wolverine's sounds: see wv_sound.h. One function: send an AvP sound command through the same mailbox the game's own sender fills (saturn/audio/sat_audio.h).
 * The mailbox is 16 bytes at 68000 0x618001, 0x618003, ... (command high, command low, parameter x2, pan mode, pan, span, rates x4) and a write of 0 to 0x61801f publishes the entry
 * to the player's pending list; the game's vblank sender uses the same bytes, so the sequence runs with interrupts masked (the caller's mask is restored). */
#include "wv_sound.h"

void sat_audio_io_write8(unsigned long addr, unsigned long value);

static void mailbox(unsigned i, unsigned v) { sat_audio_io_write8(0x618001UL + 2UL * i, v); }

void wv_sfx_pan(int id, int pan)
{
    unsigned long save, masked, cmd = WV_CMD_BASE + (unsigned long)id;
    unsigned i;
    if ((unsigned)id >= WV_SFX_COUNT) return;
    if ((unsigned)pan > 0x20u) pan = 0x10;
    __asm__ volatile("stc sr,%0" : "=r"(save) : : "memory");
    masked = save | 0xf0UL;
    __asm__ volatile("ldc %0,sr" : : "r"(masked) : "memory", "t");
    mailbox(0, (unsigned)(cmd >> 8)); mailbox(1, (unsigned)(cmd & 0xff));
    for (i = 2; i < 15; i++) mailbox(i, 0);
    mailbox(7, (unsigned)pan);
    sat_audio_io_write8(0x61801fUL, 0);
    __asm__ volatile("ldc %0,sr" : : "r"(save) : "memory", "t");
}

void wv_sfx(int id) { wv_sfx_pan(id, 0x10); }
