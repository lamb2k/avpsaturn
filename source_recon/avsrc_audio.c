/* See avsrc_audio.h. Addresses cite the 68000 source; all rings and globals live in source RAM. */
#include "avsrc_audio.h"

#define RING_BASE 0xff0a88u
#define RING_HEAD 0xff801eu            /* next entry to send */
#define RING_TAIL 0xff8020u            /* next entry to fill */
#define RING_MASK 0x3f0u
#define ENTRY_SIZE 16u
#define DEMO_SOUND_ENABLED 0xff81adu   /* saved game option, restored at 0x3d30 */
#define ATTRACT_RUNNING 0xff81b0u      /* set at 0x4580 and 0x46b4 */
#define STEREO_OPTION 0xff81d2u        /* saved game option */
#define MUSIC_DELAY 0xff837cu          /* counts down per vblank; route code polls it */
#define MUSIC_CURRENT 0xff0e9cu        /* u16 selector, u16 request */
#define CAMERA_X 0xff8278u
#define ACTOR_X 0x10u

#define CONTROL_SOUND(control, param) (((u32)(param) << 16) | 0xff00u | (u32)(control))

void audio_ring_clear(AvsrcMem *m)
{
    u32 i;
    for (i = 0; i < 64u * ENTRY_SIZE; i++) RAM8(m, RING_BASE + i) = 0;
}

int audio_enqueue_always(AvsrcMem *m, u32 sound, u32 voice, u32 sweep)
{
    u16 tail = RAM16(m, RING_TAIL);
    u32 entry = RING_BASE + tail;
    if (((RAM16(m, RING_HEAD) - ENTRY_SIZE) & RING_MASK) == tail) return -1;
    RAM32W(m, entry, sound);
    RAM32W(m, entry + 4, voice);
    RAM32W(m, entry + 8, sweep);
    RAM16W(m, RING_TAIL, (tail + ENTRY_SIZE) & RING_MASK);
    return 0;
}

int audio_enqueue(AvsrcMem *m, u32 sound, u32 voice, u32 sweep)
{
    if (!RAM8(m, DEMO_SOUND_ENABLED) && RAM8(m, ATTRACT_RUNNING)) return 0;
    return audio_enqueue_always(m, sound, voice, sweep);
}

/* Z80 mailbox order of an entry. Entry bytes 4 and 12..15 never cross; mailbox 2 and 5 are never written. */
void audio_send_pending(AvsrcMem *m, AudioLink *link)
{
    u16 head = RAM16(m, RING_HEAD);
    const u8 *e = &RAM8(m, RING_BASE + head);
    if (head == RAM16(m, RING_TAIL) || link->mailbox[15] != AUDIO_MAILBOX_READY) return;
    link->mailbox[3] = e[0];           /* sound word high half: control parameter */
    link->mailbox[4] = e[1];
    link->mailbox[0] = e[2];           /* sound number, or 0xff then control code */
    link->mailbox[1] = e[3];
    link->mailbox[6] = e[5];           /* voice: pan mode */
    link->mailbox[7] = e[6];           /* pan */
    link->mailbox[8] = e[7];           /* pan span */
    link->mailbox[11] = e[8];          /* sweep: second rate */
    link->mailbox[12] = e[9];
    link->mailbox[9] = e[10];          /* first rate */
    link->mailbox[10] = e[11];
    link->mailbox[15] = 0;
    RAM16W(m, RING_HEAD, (head + ENTRY_SIZE) & RING_MASK);
}

void audio_vblank_tick(AvsrcMem *m, AudioLink *link)
{
    link->stereo = RAM8(m, STEREO_OPTION) ? 0xff : 0;
    if (RAM16(m, MUSIC_DELAY)) RAM16W(m, MUSIC_DELAY, RAM16(m, MUSIC_DELAY) - 1);
    audio_send_pending(m, link);
}

void audio_stop_all(AvsrcMem *m)
{
    RAM32W(m, MUSIC_CURRENT, 0);
    audio_enqueue_always(m, CONTROL_SOUND(0u, 0u), 0, 0);
}

void audio_key_off_channel(AvsrcMem *m, unsigned channel)
{
    audio_enqueue_always(m, CONTROL_SOUND(2u, channel & 15u), 0, 0);
}

void audio_stop_music(AvsrcMem *m)
{
    RAM32W(m, MUSIC_CURRENT, 0);
    audio_enqueue_always(m, CONTROL_SOUND(5u, 0u), 0, 0);
}

void audio_control(AvsrcMem *m, unsigned control, u16 param)
{
    audio_enqueue_always(m, CONTROL_SOUND(control, param), 0, 0);
}

/* Screen x 0..0x17f to pan 0..0x20: flat at the edges, half slope in the outer quarters, unit slope in the centre. */
unsigned audio_pan_from_screen_x(unsigned x)
{
    unsigned step = x >> 3;
    unsigned pan;
    if (step < 3u) return 0;
    if (step < 16u) return (step - 1u) / 2u;
    if (step < 36u) return step - 8u;
    pan = (step + 19u) / 2u;
    return pan > 0x20u ? 0x20u : pan;
}

u32 audio_voice_with_actor_pan(const AvsrcMem *m, u32 actor, u32 voice)
{
    /* QUIRK: 0x3ac4 tests the true signed difference, so one that overflows a word goes left or right by its real sign. */
    long x = (long)(s16)RAM16(m, actor + ACTOR_X) - (long)(s16)RAM16(m, CAMERA_X);
    unsigned screen = x < 0 ? 0u : (unsigned)(x & 0xffffL);
    if (screen > 0x17fu) screen = 0x17fu;
    return (voice & 0xff00ffu) | ((u32)audio_pan_from_screen_x(screen) << 8);
}

/* Two sound numbers take turns. Each pair's two numbers are distinct channels (see notes), so a repeat can overlap. */
void audio_play_alternating(AvsrcMem *m, u32 actor, u32 toggle, u16 first, u16 second)
{
    u32 voice = audio_voice_with_actor_pan(m, actor, 0);
    u8 turn = RAM8(m, toggle);
    RAM8(m, toggle) = (u8)((turn + 2u) & 2u);
    audio_enqueue(m, turn ? second : first, voice, 0);
}

void audio_music_request(AvsrcMem *m, const AudioMusicFade *fades, u32 request)
{
    const AudioMusicFade *fade;
    u8 flags;
    if (RAM8(m, MUSIC_CURRENT + 3) == (u8)request) return;
    RAM32W(m, MUSIC_CURRENT, request);
    fade = &fades[(request >> 16) / 4u];
    flags = RAM8(m, MUSIC_CURRENT + 2);
    if (flags & 0x80u) {               /* fade the current music out; the route later requests the next one */
        RAM16W(m, MUSIC_DELAY, fade->delay_frames);
        audio_control(m, 7u, fade->rate);
        return;
    }
    audio_enqueue(m, request & 0xffu, 0, 0);
    if (flags) {                       /* start the new music with a fade in */
        RAM16W(m, MUSIC_DELAY, 0);
        audio_control(m, 6u, fade->rate);
    }
}
