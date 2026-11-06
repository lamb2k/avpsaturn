/* Standalone proof image: recorded sound commands through a copy of the game's ring and sender, into the library. Nothing else runs.
 * script.inc (made by standalone.py from a MAME probe, kept out of git) lists frame, sound, voice, sweep; pack.bin comes in by .incbin. */
#include "sat_audio.h"
extern unsigned char __bss_start[], __bss_end[];
extern const unsigned char audio_pack[];
typedef struct Row { unsigned long frame, sound, voice, sweep; } Row;
static const Row script[] = {
#include "script.inc"
};
#define ROWS (sizeof script / sizeof script[0])
#define RING_MASK 0x3f0u
#define TVMD (*(volatile unsigned short *)0x25F80000UL)
#define TVSTAT (*(volatile unsigned short *)0x25F80004UL)
#define FRTH (*(volatile unsigned char *)0xFFFFFE12UL)
#define FRTL (*(volatile unsigned char *)0xFFFFFE13UL)
#define TCR (*(volatile unsigned char *)0xFFFFFE16UL)
static unsigned char ring[0x400];
static unsigned head, tail;
volatile unsigned long audio_done, audio_frame_now, audio_cost_max, audio_init_ok;
/* What the SCSP and CD block were told and did, read back from the chips each frame, for standalone.py. */
typedef struct Event { unsigned long on_frame, off_frame, slot, word0, sa_low, tl, pan, position_max; } Event;
#define EVENTS 32
volatile Event audio_events[EVENTS];
volatile unsigned long audio_event_count;
volatile unsigned long audio_cd_status_frames[16], audio_cd_fad_first, audio_cd_fad_last, audio_cd_track;
#define SLOT(n, r) (*(volatile unsigned short *)(0x25B00000UL + 0x20UL * (n) + (r)))
#define SCSP_MONITOR_SELECT (*(volatile unsigned short *)0x25B00408UL)
#define CD_CR1 (*(volatile unsigned short *)0x25890018UL)
#define CD_CR2 (*(volatile unsigned short *)0x2589001CUL)
#define CD_CR3 (*(volatile unsigned short *)0x25890020UL)
#define CD_CR4 (*(volatile unsigned short *)0x25890024UL)
#define KEY_ON 0x0800u
static signed char open_event[16];

static void watch_chips(unsigned long f)
{
    int n;
    unsigned status = (CD_CR1 >> 8) & 0xfu;
    audio_cd_status_frames[status]++;
    if (status == 3 || status == 4) {
        unsigned long fad = ((unsigned long)(CD_CR3 & 0xff) << 16) | CD_CR4;
        if (!audio_cd_fad_first) { audio_cd_fad_first = fad; audio_cd_track = CD_CR2; }
        audio_cd_fad_last = fad;
    }
    for (n = 0; n < 16; n++) {
        int on = (SLOT(n, 0) & KEY_ON) != 0;
        int i = open_event[n] - 1;
        if (on && i < 0 && audio_event_count < EVENTS) {
            volatile Event *e = &audio_events[audio_event_count++];
            e->on_frame = f; e->off_frame = 0; e->slot = (unsigned long)n; e->word0 = SLOT(n, 0); e->sa_low = SLOT(n, 2);
            e->tl = SLOT(n, 0x0c); e->pan = SLOT(n, 0x16); e->position_max = 0;
            open_event[n] = (signed char)audio_event_count;
        } else if (!on && i >= 0) {
            audio_events[i].off_frame = f;
            open_event[n] = 0;
        } else if (on) {
            unsigned long pos;
            SCSP_MONITOR_SELECT = (unsigned short)(n << 11);
            pos = (SCSP_MONITOR_SELECT >> 7) & 0xfu;       /* top bits of the slot's play position */
            if (pos > audio_events[i].position_max) audio_events[i].position_max = pos;
        }
    }
}

static void put32(unsigned char *p, unsigned long v) { p[0] = (unsigned char)(v >> 24); p[1] = (unsigned char)(v >> 16); p[2] = (unsigned char)(v >> 8); p[3] = (unsigned char)v; }
static void enqueue(const Row *r) /* 0x1922 */
{
    unsigned next = (tail + 0x10) & RING_MASK;
    if (next == head) return;
    put32(ring + tail, r->sound); put32(ring + tail + 4, r->voice); put32(ring + tail + 8, r->sweep);
    tail = next;
}
static void send_one(void) /* 0x188a, byte order as in the ROM */
{
    static const unsigned char from[] = { 0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11 };
    static const unsigned char to[] = { 3, 4, 0, 1, 6, 7, 8, 11, 12, 9, 10 };
    unsigned i;
    if (head == tail) return;
    for (i = 0; i < sizeof from; i++) sat_audio_io_write8(0x618001UL + 2UL * to[i], ring[head + from[i]]);
    sat_audio_io_write8(0x61801fUL, 0);
    head = (head + 0x10) & RING_MASK;
}
static void wait_vblank(void) { while (TVSTAT & 8) ; while (!(TVSTAT & 8)) ; }
void start(void) __attribute__((section(".text.start")));
void start(void)
{
    unsigned long f = 0, row = 0, cost;
    unsigned char *z;
    for (z = __bss_start; z < __bss_end; z++) *z = 0;
    TCR = 2; /* tick every 128 clocks */
    TVMD = 0x8000;
    audio_init_ok = (unsigned long)sat_audio_init(audio_pack);
    sat_audio_io_write8(0x619ffdUL, 0xff);
    for (;;) {
        wait_vblank();
        audio_frame_now = f;
        while (row < ROWS && script[row].frame <= f) enqueue(&script[row++]);
        FRTH = 0; FRTL = 0;
        send_one();
        sat_audio_frame();
        cost = ((unsigned long)FRTH << 8); cost |= FRTL;
        if (cost > audio_cost_max) audio_cost_max = cost;
        watch_chips(f);
        if (row >= ROWS && head == tail) audio_done = 1;
        f++;
    }
}
__asm__(".section .rodata\n.balign 4\n.global _audio_pack\n_audio_pack: .incbin \"pack.bin\"\n.text\n");
