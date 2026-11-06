/* MAME-tier replay: feed each enqueue measured by tools/learn_audio_probe.lua to the C ring, tick once per frame,
   and require the same send frames and queue contents. usage: audio_ring_replay PROBE.tsv FIRST_READY_FRAME (the Z80 is still booting before it) */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "avsrc_audio.h"
static AvsrcMem m;
static AudioLink link;
int main(int argc, char **argv)
{
    FILE *f;
    char line[256], ev[8];
    long frame = 0, now = 0, sends = 0, enq = 0, bad = 0;
    unsigned long s, v, w;
    unsigned tail;
    u16 head;
    u32 meas_send[64]; int nsend = 0, i;
    long ready_from;
    if (argc < 3 || !(f = fopen(argv[1], "r"))) return 2;
    ready_from = atol(argv[2]);
    if (!fgets(line, sizeof line, f)) return 2;
    memset(meas_send, 0, sizeof meas_send);
    while (fgets(line, sizeof line, f)) {
        if (sscanf(line, "%ld %7s", &frame, ev) != 2) continue;
        while (now < frame) {          /* run every whole frame up to this event's frame */
            now++;
            head = RAM16(&m, 0xff801eu);
            link.mailbox[15] = now >= ready_from ? AUDIO_MAILBOX_READY : 0;   /* Z80 clears within 4 ms; ring backlog at frame end was 0 in both runs */
            audio_vblank_tick(&m, &link);
            if (RAM16(&m, 0xff801eu) != head) { meas_send[nsend & 63] = (u32)now; nsend++; }
        }
        if (!strcmp(ev, "E")) {
            if (sscanf(line, "%*d %*s %x %lx %lx %lx", &tail, &s, &v, &w) != 4) return 2;
            if (RAM16(&m, 0xff8020u) != tail) bad++;
            if (audio_enqueue_always(&m, (u32)s, (u32)v, (u32)w)) bad++;
            enq++;
        } else if (!strcmp(ev, "S")) {
            int hit = 0;
            for (i = 0; i < nsend && i < 64; i++) if ((long)meas_send[i] == frame) { meas_send[i] = 0; hit = 1; break; }
            if (!hit) bad++;
            sends++;
        }
    }
    printf("enqueues %ld sends %ld c_sends %d mismatches %ld\n", enq, sends, nsend, bad);
    return bad || nsend != sends;
}
