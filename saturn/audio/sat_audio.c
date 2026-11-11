/* See sat_audio.h and docs/notes/AVP_NOTES_AUDIO.md. The SH-2 drives the SCSP directly; its 68000 only spins on one instruction, so SCSP RAM is clip space.
 * Each sound is one clip rendered offline through the real driver, so the sequencer's work is already in the sample.
 * Kept from the Z80 driver: a channel is taken when priority >= the occupant's, a losing channel is skipped, music does not stop SFX,
 * the control codes and the pan sweeps.
 * Known differences: music is a CD track, so an SFX cannot suppress a note on its channel. A sound on several channels is one clip, playing on
 * the first channel it wins. Pan modes 5..7 do not apply their second rate. */
#include "sat_audio.h"

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned long u32;
typedef signed short s16;

#define SCSP_RAM ((volatile u16 *)0x25A00000UL)
#define SCSP_RAM_BYTES 0x80000UL
#define SLOT(n, r) (*(volatile u16 *)(0x25B00000UL + 0x20UL * (n) + (r)))
#define SCSP_MIXER (*(volatile u16 *)0x25B00400UL)
#define KEY_EXECUTE 0x1000u
#define KEY_ON 0x0800u
#define PCM8 0x0010u
#define LOOP_NORMAL 0x0020u
#define CD_HIRQ (*(volatile u16 *)0x25890008UL)
#define CD_CR1 (*(volatile u16 *)0x25890018UL)
#define CD_CR2 (*(volatile u16 *)0x2589001CUL)
#define CD_CR3 (*(volatile u16 *)0x25890020UL)
#define CD_CR4 (*(volatile u16 *)0x25890024UL)
#define HIRQ_CMOK 0x0001u
#define CD_STATUS_PLAY 3u
#define SMPC_COM (*(volatile u8 *)0x2010001FUL)
#define SMPC_SF (*(volatile u8 *)0x20100063UL)
#define SMPC_SNDON 0x06u
#define SMPC_SNDOFF 0x07u
#define CLIP_BASE 0x20UL               /* below it: the 68000's vectors and idle loop */

#define SOUND_TABLE_SIZE 0x38du        /* the driver's table size, Z80 0x9000 */
#define CHANNELS 16
#define MAILBOX_BYTES 16
#define STEREO_ADDR 0x619ffdUL
#define HANDSHAKE_ADDR 0x61801fUL
#define PAN_CENTRE 0x10u
#define PAN_MAX 0x20u
#define PENDING_MAX 4                  /* one per frame from the sender; more means frames were skipped */
#define FRAMES_PER_SECOND 60u
#define CLIP_RATE 11025u
#define CD_FRAMES_PER_SECOND 75u
#define PAN_TICK_EXTRA_EVERY 24u       /* the driver steps at 62.5 Hz, this runs at 60 */

typedef struct Sfx { u8 cmd_hi, cmd_lo, prio, mask_hi, mask_lo, tl, flags, pad; u8 offset[4], samples[4]; } Sfx;
typedef struct Music { u8 cmd_hi, cmd_lo, intro_track, loop_track, intro_cd_frames[2], pad[10]; } Music;

typedef struct Channel {
    u32 frames_left;
    long pos;                          /* pan, 8.8 */
    s16 rate;
    u8 prio, pan_mode, target, span, has_clip, looping;
} Channel;

static const Sfx *sfx_table;
static const Music *music_table;
static u32 sfx_count, music_count;
static Channel channel[CHANNELS];
static u8 mailbox[MAILBOX_BYTES];
static u8 pending[PENDING_MAX][MAILBOX_BYTES];
static u8 pending_count, stereo = 1, pan_tick;
static u8 cd_loop_next, cd_want, cd_level_now = 0xff;
static u32 cd_intro_left;              /* video frames of intro still to play, counted once the drive reports play */
static u16 cd_cmd[4];
static u32 fade_level = 0xffffUL;
static s16 fade_dir;
static u16 fade_rate;
volatile SatAudioStats sat_audio_stats;
int sat_audio_clips_loaded;   /* set by a caller whose loader already put the clips in SCSP RAM; then pack need only hold the tables */

#ifdef SAT_AUDIO_MIX
/* Test mode: one mixed stream instead of a slot per channel. Clips are read from SCSP RAM by the SH-2, summed, and written ahead of two static looping slots. */
#define MIX_LEFT 0x70000UL
#define MIX_RIGHT 0x72000UL
#define MIX_RING 8192UL
#define MIX_LEAD 1200UL
typedef struct Voice { u32 at, left; u8 on, loop; u32 start, samples; u16 gl, gr; } Voice;
static Voice voice[CHANNELS];
static u32 mix_pos, mix_frac;
static u16 mix_gain_tl[CHANNELS];
#define RAM8_AT(a) (*(volatile signed char *)(0x25A00000UL + (a)))
static u16 tl_gain(unsigned tl)     /* 256 * 10^(-0.375 tl / 20): halves every 16 steps */
{
    static const u8 frac[16] = { 255, 244, 234, 224, 215, 206, 197, 189, 181, 173, 166, 159, 152, 146, 140, 134 };
    return tl >= 128 ? 0 : (u16)(frac[tl & 15] >> (tl >> 4));
}
static void mix_init(void)
{
    u32 i;
    for (i = 0; i < 2 * MIX_RING; i += 2) SCSP_RAM[(MIX_LEFT + i) >> 1] = 0;
    for (i = 0; i < 2; i++) {
        u32 a = i ? MIX_RIGHT : MIX_LEFT;
        SLOT(i, 0x00) = (u16)(PCM8 | LOOP_NORMAL | (a >> 16));
        SLOT(i, 0x02) = (u16)a; SLOT(i, 0x04) = 0; SLOT(i, 0x06) = (u16)MIX_RING;
        SLOT(i, 0x08) = 0x001fu | 1u << 5; SLOT(i, 0x0a) = 0x001fu; SLOT(i, 0x0c) = 0; SLOT(i, 0x0e) = 0;
        SLOT(i, 0x10) = (u16)(0xeu << 11); SLOT(i, 0x12) = 0; SLOT(i, 0x14) = 0;
        SLOT(i, 0x16) = (u16)(7u << 13 | (i ? 0x00u : 0x10u) << 8);
    }
    SLOT(0, 0) = (u16)(SLOT(0, 0) | KEY_ON); SLOT(1, 0) = (u16)(SLOT(1, 0) | KEY_ON | KEY_EXECUTE);
    mix_pos = MIX_LEAD;
}
static void mix_frame(void)
{
    u32 count = 183;
    u32 i, n;
    mix_frac += 934;                                /* 11025 / 59.94 = 183.934 */
    if (mix_frac >= 1000) { mix_frac -= 1000; count++; }
    for (i = 0; i < count; i++) {
        long l = 0, r = 0;
        for (n = 0; n < CHANNELS; n++) {
            Voice *v = &voice[n];
            long s;
            if (!v->on) continue;
            s = RAM8_AT(v->at++);
            l += s * v->gl; r += s * v->gr;
            if (--v->left == 0) {
                if (v->loop) { v->at = v->start; v->left = v->samples; } else v->on = 0;
            }
        }
        l >>= 8; r >>= 8;
        if (l > 127) l = 127; else if (l < -128) l = -128;
        if (r > 127) r = 127; else if (r < -128) r = -128;
        RAM8_AT(MIX_LEFT + mix_pos) = (signed char)l;
        RAM8_AT(MIX_RIGHT + mix_pos) = (signed char)r;
        if (++mix_pos == MIX_RING) mix_pos = 0;
    }
}
#endif

static u32 be32(const u8 *p) { return ((u32)p[0] << 24) | ((u32)p[1] << 16) | ((u32)p[2] << 8) | p[3]; }
static u32 be16(const u8 *p) { return ((u32)p[0] << 8) | p[1]; }

static void cd_command(unsigned cr1, unsigned cr2, unsigned cr3, unsigned cr4)
{
    cd_cmd[0] = (u16)cr1; cd_cmd[1] = (u16)cr2; cd_cmd[2] = (u16)cr3; cd_cmd[3] = (u16)cr4;
    cd_want = 1;
}

static void cd_play_track(unsigned track, int repeat)
{
    cd_command(0x1000u, track << 8 | 1u, repeat ? 0x0f00u : 0u, track << 8 | 99u);   /* Play Disc, track and index */
}

static void cd_pause(void)
{
    cd_command(0x11ffu, 0xffffu, 0, 0);
    cd_loop_next = 0;
}

static void cd_service(void)
{
    if (!cd_want || !(CD_HIRQ & HIRQ_CMOK)) return;   /* never wait: a busy CD block gets the command next frame */
    CD_HIRQ = (u16)~HIRQ_CMOK;
    CD_CR1 = cd_cmd[0]; CD_CR2 = cd_cmd[1]; CD_CR3 = cd_cmd[2]; CD_CR4 = cd_cmd[3];
    cd_want = 0;
    sat_audio_stats.cd_sent++;
}

static void cd_level(unsigned level)
{
    if (level == cd_level_now) return;
    cd_level_now = (u8)level;
    SLOT(16, 0x16) = (u16)(level << 5 | 0x1fu);       /* the CD's left input, hard left */
    SLOT(17, 0x16) = (u16)(level << 5 | 0x0fu);       /* right input, hard right */
}

static void fade_tick(void)
{
    long next;
    if (!fade_dir) return;
    next = (long)fade_level + (fade_dir > 0 ? (long)fade_rate : -(long)fade_rate);
    if (next < 0 || next > 0xffffL) {
        fade_level = fade_dir > 0 ? 0xffffUL : 0;
        fade_dir = 0;
    } else {
        fade_level = (u32)next;
    }
}

static unsigned scsp_pan(unsigned pan)
{
    if (!stereo) pan = PAN_CENTRE;
    if (pan < PAN_CENTRE) { pan = PAN_CENTRE - pan; return 0x10u | (pan > 15 ? 15 : pan); }
    pan -= PAN_CENTRE;
    return pan > 15 ? 15 : pan;
}

static void slot_pan(int n)
{
#ifdef SAT_AUDIO_MIX
    unsigned pan = scsp_pan((unsigned)(channel[n].pos >> 8)), cut = pan & 15u;
    u16 g = mix_gain_tl[n], c = (u16)(g >> (cut / 2u));   /* the slot's 3 dB steps, to the nearest 6 dB */
    voice[n].gl = pan & 16u ? g : c;
    voice[n].gr = pan & 16u ? c : g;
    return;
#endif
    SLOT(n, 0x16) = (u16)(7u << 13 | scsp_pan((unsigned)(channel[n].pos >> 8)) << 8);
}

/* One step of the driver's pan sweep, 0x111a. Modes 1 and 2 bounce, the rest stop at the target. */
static void pan_step(int n)
{
    Channel *c = &channel[n];
    long p;
    int a;
    if (!c->pan_mode) return;
    p = c->pos + c->rate;
    if (c->pan_mode == 1) {
        if (p < 0 || p >= (long)(PAN_MAX + 1) << 8) { p = c->rate < 0 ? 0 : (long)PAN_MAX << 8; c->rate = (s16)-c->rate; }
    } else if (c->rate >= 0 ? p >> 8 >= c->target : p < (long)c->target << 8) {
        p = (long)c->target << 8;
        if (c->pan_mode == 2) {
            a = c->rate >= 0 ? (int)c->target - c->span : (int)c->target + c->span;
            c->target = (u8)(a < 0 ? 0 : a > (int)PAN_MAX ? (int)PAN_MAX : a);
            c->rate = (s16)-c->rate;
        } else {
            c->pan_mode = 0;
        }
    }
    c->pos = p;
    slot_pan(n);
}

/* The driver's mode setups, table 0x2ad. */
static void pan_setup(Channel *c, const u8 *mb)
{
    unsigned mode = mb[6] & 7u, p = mb[7], span = mb[8];
    s16 r = (s16)(mb[9] << 8 | mb[10]);
    int down = (mode <= 2 && p >= 0x11) || mode == 4 || mode == 6;
    if (p > PAN_MAX) p = PAN_MAX;
    c->pos = (long)p << 8;
    c->pan_mode = (u8)mode;
    c->span = (u8)span;
    c->rate = mode == 0 ? 0 : down ? (s16)-r : r;
    c->target = (u8)(down ? (p > span ? p - span : 0) : (p + span > PAN_MAX ? PAN_MAX : p + span));
}

static void channel_end(int n)
{
    Channel *c = &channel[n];
#ifdef SAT_AUDIO_MIX
    voice[n].on = 0;
#else
    if (c->has_clip) SLOT(n, 0) = (u16)((SLOT(n, 0) & ~KEY_ON) | KEY_EXECUTE);
#endif
    c->prio = 0; c->frames_left = 0; c->has_clip = 0; c->pan_mode = 0;
}

static const Sfx *find_sfx(unsigned cmd)
{
    u32 lo = 0, hi = sfx_count;
    while (lo < hi) {
        u32 mid = (lo + hi) / 2;
        unsigned v = (unsigned)(sfx_table[mid].cmd_hi << 8 | sfx_table[mid].cmd_lo);
        if (v == cmd) return &sfx_table[mid];
        if (v < cmd) lo = mid + 1; else hi = mid;
    }
    return 0;
}

static void start_sfx(const Sfx *s, const u8 *mb)
{
    unsigned mask = (unsigned)(s->mask_hi << 8 | s->mask_lo);
    u32 samples = be32(s->samples), offset = be32(s->offset);
    u32 frames = samples * FRAMES_PER_SECOND / CLIP_RATE + 2;
    int n, clip = -1;
    for (n = 0; n < CHANNELS; n++) {
        if (!(mask >> n & 1) || s->prio < channel[n].prio) continue;   /* a losing channel is skipped; the rest still plays */
        channel_end(n);
        channel[n].prio = s->prio;
        channel[n].frames_left = frames;
        channel[n].looping = s->flags & 1;
        if (clip < 0) clip = n;
    }
    if (clip < 0) { sat_audio_stats.sfx_refused++; return; }
    channel[clip].has_clip = 1;
    pan_setup(&channel[clip], mb);
    offset += CLIP_BASE;
#ifdef SAT_AUDIO_MIX
    voice[clip].start = voice[clip].at = offset; voice[clip].samples = voice[clip].left = samples;
    voice[clip].loop = s->flags & 1; voice[clip].on = 1;
    mix_gain_tl[clip] = tl_gain(s->tl);
    slot_pan(clip);
    sat_audio_stats.sfx_started++;
    return;
#endif
    SLOT(clip, 0x00) = (u16)(PCM8 | (s->flags & 1 ? LOOP_NORMAL : 0) | (offset >> 16));
    SLOT(clip, 0x02) = (u16)offset;
    SLOT(clip, 0x04) = 0;
    SLOT(clip, 0x06) = (u16)(samples > 0xffffUL ? 0xffffUL : samples);
    SLOT(clip, 0x08) = 0x001fu | 1u << 5;              /* attack at once, then hold */
    SLOT(clip, 0x0a) = 0x001fu;                        /* release at once */
    SLOT(clip, 0x0c) = s->tl;
    SLOT(clip, 0x0e) = 0;
    SLOT(clip, 0x10) = (u16)(0xeu << 11);              /* octave -2: 44100 / 4 = 11025 Hz */
    SLOT(clip, 0x12) = 0;
    SLOT(clip, 0x14) = 0;
    slot_pan(clip);
    SLOT(clip, 0x00) = (u16)(SLOT(clip, 0x00) | KEY_ON | KEY_EXECUTE);
    sat_audio_stats.sfx_started++;
}

static unsigned last_music;   /* the music the game last asked for, replayed after a disc load took the drive */
static int music_start(unsigned cmd)
{
    u32 i;
    for (i = 0; i < music_count; i++) {
        const Music *m = &music_table[i];
        if ((unsigned)(m->cmd_hi << 8 | m->cmd_lo) != cmd) continue;
        last_music = cmd;
        fade_level = 0xffffUL; fade_dir = 0;
        cd_play_track(m->intro_track ? m->intro_track : m->loop_track, !m->intro_track);
        cd_loop_next = m->intro_track ? m->loop_track : 0;
        cd_intro_left = be16(m->intro_cd_frames) * FRAMES_PER_SECOND / CD_FRAMES_PER_SECOND;
        sat_audio_stats.music_started++;
        return 1;
    }
    return 0;
}

static void control(unsigned code, unsigned param)
{
    int n;
    sat_audio_stats.controls++;
    switch (code) {
    case 0: for (n = 0; n < CHANNELS; n++) channel_end(n); cd_pause(); last_music = 0; fade_dir = 0; break;
    case 1: for (n = 0; n < CHANNELS; n++) channel_end(n); break;
    case 2: if ((param & 0xffu) < CHANNELS) channel_end((int)(param & 0xffu)); break;
    case 5: cd_pause(); last_music = 0; break;
    case 6:                                            /* fade in; no-op at rate 0 or when already going this way */
        if (!param || fade_dir > 0) break;
        if (!fade_dir) fade_level = 0;
        fade_dir = 1; fade_rate = (u16)param;
        break;
    case 7:
        if (!param || fade_dir < 0) break;
        if (!fade_dir) fade_level = 0xffffUL;
        fade_dir = -1; fade_rate = (u16)param;
        break;
    default: break;                                    /* 3, 4: no table sound uses direct samples. 8, 9: tempo. a, b: pan mirror */
    }
}

static void dispatch(const u8 *mb)
{
    unsigned word = (unsigned)(mb[0] << 8 | mb[1]);
    const Sfx *s;
    sat_audio_stats.commands++;
    sat_audio_stats.last_command = word;
    if (mb[0] == 0xff) { control(mb[1], (unsigned)(mb[3] << 8 | mb[4])); return; }
    word %= SOUND_TABLE_SIZE;
    s = find_sfx(word);
    if (s) start_sfx(s, mb);
    else if (!music_start(word)) sat_audio_stats.sfx_unknown++;
}

void sat_audio_io_write8(unsigned long addr, unsigned long value)
{
    if (addr == STEREO_ADDR) { stereo = value != 0; return; }
    if (addr < 0x618001UL || addr > HANDSHAKE_ADDR) return;
    if (addr == HANDSHAKE_ADDR) {
        if (value == 0 && pending_count < PENDING_MAX) {
            int i;
            for (i = 0; i < MAILBOX_BYTES; i++) pending[pending_count][i] = mailbox[i];
            pending_count++;
        }
        return;
    }
    mailbox[(addr - 0x618001UL) >> 1] = (u8)value;
}

void sat_audio_frame(void)
{
    int n, i;
    unsigned ticks = 1;
    sat_audio_stats.frames++;
    for (i = 0; i < pending_count; i++) dispatch(pending[i]);
    pending_count = 0;
    if (++pan_tick == PAN_TICK_EXTRA_EVERY) { pan_tick = 0; ticks = 2; }
    while (ticks--) {
        fade_tick();
        for (n = 0; n < CHANNELS; n++) if (channel[n].has_clip) pan_step(n);
    }
    for (n = 0; n < CHANNELS; n++) {
        Channel *c = &channel[n];
        if (c->prio && !c->looping && --c->frames_left == 0) channel_end(n);
    }
    cd_level(fade_level >> 13);
    if (cd_loop_next) {
        unsigned status = (CD_CR1 >> 8) & 0xfu;
        sat_audio_stats.cd_status = status;
        if (status == CD_STATUS_PLAY && cd_intro_left) cd_intro_left--;
        if (!cd_intro_left) { cd_play_track(cd_loop_next, 1); cd_loop_next = 0; }
    }
    cd_service();
#ifdef SAT_AUDIO_MIX
    mix_frame();
#endif
}

/* New sound set between rounds. tables: this round's header and tables, in RAM for as long as it is in use. clips: its 8 bit samples, written to SCSP RAM here.
   Running clips are stopped first; the 68000 stays parked. Interrupts masked by the caller. */
int sat_audio_swap(const void *tables, const void *clips)
{
    const u8 *p = tables, *c = clips;
    u32 bytes, i;
    int n;
    if (p[0] != 'S' || p[1] != 'A' || p[2] != 'U' || p[3] != '1') return 0;
    bytes = be32(p + 8);
    if (bytes + CLIP_BASE > SCSP_RAM_BYTES) return 0;
    for (n = 0; n < CHANNELS; n++) channel_end(n);
    for (n = 0; n < 32; n++) for (i = 0; i < 0x18; i += 2) SLOT(n, i) = 0;
    SLOT(0, 0) = KEY_EXECUTE;
    sfx_count = be16(p + 4); music_count = be16(p + 6);
    sfx_table = (const Sfx *)(p + 12);
    music_table = (const Music *)(sfx_table + sfx_count);
    for (i = 0; i + 1 < bytes; i += 2) SCSP_RAM[(CLIP_BASE + i) >> 1] = (u16)(c[i] << 8 | c[i + 1]);
    return 1;
}
/* The drive is free again after a load, so the music the game asked for goes back on. */
void sat_audio_resume_music(void)
{
    cd_want = 0; cd_loop_next = 0;
    cd_level_now = 0xff;
    if (last_music) music_start(last_music);
    cd_level(fade_level >> 13);
}

unsigned long sat_audio_pack_keep(const void *pack)
{
    const u8 *p = pack;
    return 12UL + 16UL * (be16(p + 4) + be16(p + 6));
}

static void smpc(unsigned command)
{
    int wait;
    for (wait = 0; wait < 100000 && (SMPC_SF & 1); wait++) ;   /* wait for idle first: the BIOS polls the SMPC every frame and a command written while it is busy is lost */
    SMPC_SF = 1;
    SMPC_COM = (u8)command;
    for (wait = 0; wait < 100000 && (SMPC_SF & 1); wait++) ;
}

int sat_audio_init(const void *pack)
{
    const u8 *p = pack, *clips;
    u32 bytes, i;
    int n;
    if (p[0] != 'S' || p[1] != 'A' || p[2] != 'U' || p[3] != '1') return 0;
    sfx_count = be16(p + 4); music_count = be16(p + 6); bytes = be32(p + 8);
    if (bytes + CLIP_BASE > SCSP_RAM_BYTES) return 0;
    sfx_table = (const Sfx *)(p + 12);
    music_table = (const Music *)(sfx_table + sfx_count);
    clips = (const u8 *)(music_table + music_count);
    smpc(SMPC_SNDOFF);
    SCSP_RAM[0] = 0x0007u; SCSP_RAM[1] = 0xfffcu;      /* 68000 reset: stack */
    SCSP_RAM[2] = 0x0000u; SCSP_RAM[3] = 0x0010u;      /* pc */
    SCSP_RAM[8] = 0x60feu;                             /* bra.s to itself */
    smpc(SMPC_SNDON);
    SCSP_MIXER = 0x0200u | 0xfu;                       /* 512 KB RAM, master volume full */
    for (n = 0; n < 32; n++) for (i = 0; i < 0x18; i += 2) SLOT(n, i) = 0;
    SLOT(0, 0) = KEY_EXECUTE;
    if (!sat_audio_clips_loaded)
        for (i = 0; i + 1 < bytes; i += 2) SCSP_RAM[(CLIP_BASE + i) >> 1] = (u16)(clips[i] << 8 | clips[i + 1]);
    cd_level(fade_level >> 13);
#ifdef SAT_AUDIO_MIX
    mix_init();
#endif
    return 1;
}
