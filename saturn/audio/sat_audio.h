/* Native sound for the Saturn port: the game's sound commands to SCSP clips and CD audio, with no Z80 and no 68000 program.
 *
 * Integration:
 *   sat_audio_init(pack)   once, with build_pack.py's pack.bin in RAM. Clips are copied to SCSP RAM, after which only the first
 *                          sat_audio_pack_keep(pack) bytes must stay.
 *   IOW8 with a in 0x618000..0x619fff calls sat_audio_io_write8(a, v).
 *   sat_audio_frame()      once per video frame, on the same CPU as the game's vblank tick.
 * The game's sender (lifted 0x1870..0x1914) stays the only consumer of the ring. Reading 0x61801f must give 0xff, which the kernel's io_read
 * already does: a Z80 that is always ready, so the game sends at most one entry per frame, as on the board. Nothing here touches ff801e or ff8020.
 * CD data reads during music are the caller's concern: this library starts CD audio and does not arbitrate the drive. */
#ifndef SAT_AUDIO_H
#define SAT_AUDIO_H

int sat_audio_init(const void *pack);                     /* 1 ok; 0 bad magic or clips larger than SCSP RAM */
unsigned long sat_audio_pack_keep(const void *pack);
void sat_audio_io_write8(unsigned long addr, unsigned long value);
void sat_audio_frame(void);

/* Counters for a debugger. */
typedef struct SatAudioStats {
    unsigned long commands, sfx_started, sfx_refused, sfx_unknown, music_started, controls, frames, cd_sent, cd_status, last_command;
} SatAudioStats;
extern volatile SatAudioStats sat_audio_stats;
#endif
