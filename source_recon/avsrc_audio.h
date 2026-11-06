/* Sound command path of avspu, 68000 side. Readable reconstruction, private research.
   Gameplay calls an audio_* sender; senders fill a ring of 64 16-byte entries (63 usable);
   the vblank tick moves at most one entry per frame into the Z80 mailbox. See AVP_NOTES_AUDIO.md. */
#ifndef AVSRC_AUDIO_H
#define AVSRC_AUDIO_H
#include "avsrc.h"

#define AUDIO_MAILBOX_READY 0xffu      /* Z80 sets the last mailbox byte to this once it has copied a command */

typedef struct AudioLink {
    u8 mailbox[16];                    /* Z80 0xc000..0xc00f, 68000 0x618001 + 2 * index */
    u8 stereo;                         /* Z80 0xcffe, 68000 0x619ffd: nonzero stereo pan, 0 forces centre */
} AudioLink;

/* A word pair of the music fade table at 0x3c32. Build data, supplied by the caller. */
typedef struct AudioMusicFade { u16 delay_frames; u16 rate; } AudioMusicFade;

void audio_ring_clear(AvsrcMem *m);                                       /* 0x195c */
int audio_enqueue_always(AvsrcMem *m, u32 sound, u32 voice, u32 sweep);   /* 0x1922: nonzero when the ring is full */
int audio_enqueue(AvsrcMem *m, u32 sound, u32 voice, u32 sweep);          /* 0x1916: silent during a muted attract demo */
void audio_send_pending(AvsrcMem *m, AudioLink *link);                    /* 0x188a */
void audio_vblank_tick(AvsrcMem *m, AudioLink *link);                     /* 0x1870 */

void audio_stop_all(AvsrcMem *m);                                         /* 0x1972, control 0 */
void audio_key_off_channel(AvsrcMem *m, unsigned channel);                /* 0x1992, control 2 */
void audio_stop_music(AvsrcMem *m);                                       /* 0x19c4, control 5 */
void audio_control(AvsrcMem *m, unsigned control, u16 param);             /* 0x19d2..0x1a28: 6, 7, 8, 9, a, b, c, d */

unsigned audio_pan_from_screen_x(unsigned x);                             /* 0x3ad2 and table 0x3aec */
u32 audio_voice_with_actor_pan(const AvsrcMem *m, u32 actor, u32 voice);  /* 0x3abc */
void audio_play_alternating(AvsrcMem *m, u32 actor, u32 toggle, u16 first, u16 second); /* 0x1aa6 family */
void audio_music_request(AvsrcMem *m, const AudioMusicFade *fades, u32 request);        /* 0x3bdc */
#endif
