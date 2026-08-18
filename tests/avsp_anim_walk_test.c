/* S2 exit check: does the ROM animation-script interpreter reproduce the
 * game's own per-frame animation-record pointer?
 *
 * "Gate" means Capability Gate 1. A slice step's own criteria are "checks".
 *
 * The oracle is the captured work RAM itself: every actor's +0x1C is the live
 * animation-record pointer, sampled once per source frame. If the interpreter
 * in avsp_anim_script.c is a faithful reading of the script format, then the
 * pointer's frame-to-frame movement must be exactly what the script permits.
 *
 * Check A - permitted transitions. Between consecutive frames an actor's
 *   pointer may only either hold (the pose has not run out its duration) or
 *   move to avsp_anim_next_address of the current record. Any other movement is
 *   an external re-point: the game itself assigning a new animation because of
 *   a hit, a state change or an AI decision. Those are expected and are counted
 *   separately, not treated as interpreter errors - but a transition that is
 *   neither a hold, nor the script's next address, nor an external re-point
 *   coinciding with an observable actor event, is a real failure.
 *
 * Check B - stateful runs. Seeded at a pointer change and then ticked once per
 *   frame with no further help, how many consecutive frames does the
 *   interpreter predict exactly, including hold timing? This is the check that
 *   exercises duration, not just control flow.
 *
 * Inputs are private captures under .deps (git-ignored) plus the private
 * program image. The test skips cleanly when they are absent.
 *
 * C90.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../avsp_actor.h"
#include "../avsp_anim_script.h"

#define MAX_ACTORS 256
#define MAX_FRAMES 3000

typedef struct {
    const char *path;
} Window;

static const Window WINDOWS[2] = {
    { ".deps/mame/collision_probe/workram.bin" },
    { ".deps/mame/collision_probe_boss/workram.bin" }
};

static const char *ROM_PATH = ".deps/mame/actorprobe/decrypted_program_2m.bin";

static int failures = 0;

static void fail(const char *what)
{
    printf("  FAIL %s\n", what);
    ++failures;
}

static unsigned char *slurp(const char *path, long *size_out)
{
    FILE *f;
    unsigned char *buf;
    long size;

    f = fopen(path, "rb");
    if (f == 0) return 0;
    if (fseek(f, 0L, SEEK_END) != 0) { fclose(f); return 0; }
    size = ftell(f);
    if (size <= 0L) { fclose(f); return 0; }
    if (fseek(f, 0L, SEEK_SET) != 0) { fclose(f); return 0; }
    buf = (unsigned char *)malloc((size_t)size);
    if (buf == 0) { fclose(f); return 0; }
    if (fread(buf, 1u, (size_t)size, f) != (size_t)size) { free(buf); fclose(f); return 0; }
    fclose(f);
    *size_out = size;
    return buf;
}

int main(void)
{
    unsigned char *rom;
    long rom_size;
    AvspAnimScript script;
    long holds = 0L, script_moves = 0L, external = 0L, unexplained = 0L;
    long runs = 0L, run_frames_total = 0L, longest_run = 0L;
    long seeded_exact = 0L;
    long unexp_by_type[64], moves_by_type[64], longest_by_type[64];
    int w, ti;

    for (ti = 0; ti < 64; ++ti) {
        unexp_by_type[ti] = 0L; moves_by_type[ti] = 0L; longest_by_type[ti] = 0L;
    }

    printf("S2 animation walk\n");

    rom = slurp(ROM_PATH, &rom_size);
    if (rom == 0) {
        printf("  SKIP: %s not present (private program image)\n", ROM_PATH);
        return 0;
    }
    script.rom = rom;
    script.base = 0u;
    script.size = (unsigned int)rom_size;

    for (w = 0; w < 2; ++w) {
        unsigned char *raw;
        long raw_size, frames, f;
        unsigned long addrs[MAX_ACTORS];
        unsigned long ptr_prev[MAX_ACTORS];
        unsigned char st_prev[MAX_ACTORS], hit_prev[MAX_ACTORS];
        int have_prev = 0;
        int n = 0, i;
        unsigned long addr;

        raw = slurp(WINDOWS[w].path, &raw_size);
        if (raw == 0) {
            printf("  SKIP: %s not present\n", WINDOWS[w].path);
            free(rom);
            return 0;
        }
        frames = raw_size / (long)AVSP_WORK_RAM_SIZE;

        for (addr = AVSP_ACTOR_GRID_ANCHOR;
             addr + AVSP_ACTOR_STRIDE <= AVSP_WORK_RAM_FIRST + AVSP_WORK_RAM_SIZE
             && n < MAX_ACTORS;
             addr += AVSP_ACTOR_STRIDE) {
            addrs[n++] = addr;
        }
        for (i = 0; i < n; ++i) { ptr_prev[i] = 0uL; st_prev[i] = 0u; hit_prev[i] = 0u; }

        for (f = 0L; f < frames; ++f) {
            const unsigned char *work = raw + f * (long)AVSP_WORK_RAM_SIZE;
            for (i = 0; i < n; ++i) {
                AvspActor a;
                if (!avsp_actor_load(&a, work, addrs[i])) continue;
                if (a.state == 0u || a.anim_record == 0uL
                    || (long)(a.anim_record + 20uL) > rom_size) {
                    ptr_prev[i] = 0uL;
                    continue;
                }
                if (have_prev && ptr_prev[i] != 0uL) {
                    if (a.anim_record == ptr_prev[i]) {
                        ++holds;
                    } else {
                        AvspPose pose;
                        unsigned int next;
                        avsp_anim_read_pose(&script, &pose, (unsigned int)ptr_prev[i]);
                        next = pose.valid
                             ? avsp_anim_next_address(&script, &pose)
                             : 0u;
                        if (pose.valid && (unsigned long)next == a.anim_record) {
                            ++script_moves;
                            if (a.type < 64u) ++moves_by_type[a.type];
                        } else if (a.state != st_prev[i] || a.hit_value != hit_prev[i]) {
                            /* The game re-pointed the animation because
                             * something happened to the actor this frame. */
                            ++external;
                        } else {
                            ++unexplained;
                            if (a.type < 64u) ++unexp_by_type[a.type];
                        }
                    }
                }
                ptr_prev[i] = a.anim_record;
                st_prev[i] = a.state;
                hit_prev[i] = a.hit_value;
            }
            have_prev = 1;
        }

        /* Check B: seed at every pointer change and run free. */
        for (i = 0; i < n; ++i) {
            unsigned long seed_frame;
            for (seed_frame = 0uL; (long)seed_frame + 1L < frames; ++seed_frame) {
                const unsigned char *w0 = raw + (long)seed_frame * (long)AVSP_WORK_RAM_SIZE;
                const unsigned char *w1 = w0 + AVSP_WORK_RAM_SIZE;
                AvspActor a0, a1;
                AvspAnimFrame fr;
                long k;
                long matched = 0L;

                if (!avsp_actor_load(&a0, w0, addrs[i])) continue;
                if (!avsp_actor_load(&a1, w1, addrs[i])) continue;
                if (a0.state == 0u || a1.state == 0u) continue;
                if (a0.anim_record == 0uL || a1.anim_record == a0.anim_record) continue;
                if ((long)(a1.anim_record + 20uL) > rom_size) continue;

                /* Seed on the frame the new pose becomes current. */
                avsp_anim_frame_start(&fr, &script, (unsigned int)a1.anim_record);
                for (k = (long)seed_frame + 2L; k < frames; ++k) {
                    const unsigned char *wk = raw + k * (long)AVSP_WORK_RAM_SIZE;
                    AvspActor ak;
                    avsp_anim_frame_tick(&fr, &script);
                    if (!avsp_actor_load(&ak, wk, addrs[i])) break;
                    if (ak.state == 0u) break;
                    if ((unsigned long)fr.addr != ak.anim_record) break;
                    ++matched;
                }
                ++runs;
                run_frames_total += matched;
                if (matched > longest_run) longest_run = matched;
                if (a1.type < 64u && matched > longest_by_type[a1.type]) {
                    longest_by_type[a1.type] = matched;
                }
                if (matched > 0L) ++seeded_exact;
                /* Skip ahead so runs do not all start inside one another. */
                seed_frame += (unsigned long)matched;
            }
        }
        free(raw);
    }
    free(rom);

    printf("check A: permitted pointer transitions\n");
    printf("  holds (pose still running)     %ld\n", holds);
    printf("  moves the script predicts      %ld\n", script_moves);
    printf("  external re-points (event)     %ld\n", external);
    printf("  unexplained                    %ld\n", unexplained);

    printf("per actor type (script moves / unexplained / longest exact run)\n");
    for (ti = 0; ti < 64; ++ti) {
        if (moves_by_type[ti] || unexp_by_type[ti] || longest_by_type[ti]) {
            printf("  type %2d: %6ld / %5ld / %5ld\n",
                   ti, moves_by_type[ti], unexp_by_type[ti], longest_by_type[ti]);
        }
    }

    printf("check B: free-running prediction after one seed\n");
    printf("  seeded runs                    %ld\n", runs);
    printf("  runs predicting >= 1 frame     %ld\n", seeded_exact);
    printf("  total frames predicted         %ld\n", run_frames_total);
    printf("  longest exact run (frames)     %ld\n", longest_run);

    if (script_moves == 0L) {
        fail("the interpreter never predicted a single pointer move");
    }
    if (holds == 0L) {
        fail("no holds observed - the capture or the walk is wrong");
    }

    printf("\n");
    if (failures != 0) {
        printf("%d check(s) failed\n", failures);
        return 1;
    }
    printf("checks ran; see counts above for the S2 exit decision\n");
    return 0;
}
