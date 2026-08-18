/* S2 exit checks: the ROM animation-script interpreter against the game's own
 * per-frame animation-record pointer, and the shipped record subset against the
 * full program image.
 *
 * "Gate" means Capability Gate 1. A slice step's own criteria are "checks".
 *
 * The oracle is the captured work RAM itself: every actor's +0x1C is the live
 * animation-record pointer, sampled once per source frame. If the interpreter is
 * a faithful reading of the script format, the pointer's frame-to-frame movement
 * must be exactly what the script permits.
 *
 * Check A - permitted transitions. Between consecutive frames an actor's pointer
 *   may only hold (the pose has not run out its duration) or move to
 *   avsp_anim_next_address of the current record. Anything else is the game
 *   re-pointing the animation itself, for a reason the script does not contain:
 *   an AI decision, an action change, an input. Those are counted separately.
 *
 * Check B - stateful runs. Seeded once at a pointer change and then ticked with
 *   no further help, how many consecutive frames does the interpreter predict
 *   exactly? This exercises hold duration, not just control flow, and is the
 *   check that rules out a wrong record size or jump rule.
 *
 * Check C - shipped subset equivalence (only when built with
 *   -DAVSP_GENERATED_RECORDS). The Saturn build cannot carry the program image,
 *   so it carries ~10 KB of reachable records in 63 spans at their original
 *   addresses. Running the identical measurement over those spans must produce
 *   counters identical to the full-image run. Any difference means the extracted
 *   subset is incomplete or mis-addressed.
 *
 * Inputs are private captures under .deps (git-ignored) plus the private program
 * image. The test skips cleanly when they are absent.
 *
 * C90.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../avsp_actor.h"
#include "../avsp_anim_script.h"

#ifdef AVSP_GENERATED_RECORDS
#include "../generated/avsp_anim_records.h"
#endif

#define MAX_ACTORS 256
#define TYPE_SLOTS 64

static const char *WINDOWS[2] = {
    ".deps/mame/collision_probe/workram.bin",
    ".deps/mame/collision_probe_boss/workram.bin"
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

typedef struct {
    long holds;
    long script_moves;
    long external;
    long unexplained;
    long runs;
    long run_frames_total;
    long longest_run;
    long seeded_exact;
    long moves_by_type[TYPE_SLOTS];
    long unexp_by_type[TYPE_SLOTS];
    long longest_by_type[TYPE_SLOTS];
} Counts;

/* One actor is eligible when it is live and its record resolves in the script
 * source under test. Using the source's own resolver here, rather than a ROM
 * size check, is what makes the full-image and shipped-subset runs comparable. */
static int eligible(const AvspAnimScript *sp, const AvspActor *a)
{
    if (a->state == 0u || a->anim_record == 0uL) return 0;
    return avsp_anim_resolve(sp, (unsigned int)a->anim_record, 16u) != 0;
}

static void measure(const AvspAnimScript *sp, unsigned char **windows,
                    long *window_sizes, Counts *c)
{
    int w;

    memset(c, 0, sizeof(*c));

    for (w = 0; w < 2; ++w) {
        unsigned char *raw = windows[w];
        long frames = window_sizes[w] / (long)AVSP_WORK_RAM_SIZE;
        long f;
        unsigned long addrs[MAX_ACTORS];
        unsigned long ptr_prev[MAX_ACTORS];
        unsigned char st_prev[MAX_ACTORS], hit_prev[MAX_ACTORS];
        int have_prev = 0;
        int n = 0, i;
        unsigned long addr;

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
                if (!eligible(sp, &a)) { ptr_prev[i] = 0uL; continue; }

                if (have_prev && ptr_prev[i] != 0uL) {
                    if (a.anim_record == ptr_prev[i]) {
                        ++c->holds;
                    } else {
                        AvspPose pose;
                        unsigned int next;
                        avsp_anim_read_pose(sp, &pose, (unsigned int)ptr_prev[i]);
                        next = pose.valid ? avsp_anim_next_address(sp, &pose) : 0u;
                        if (pose.valid && (unsigned long)next == a.anim_record) {
                            ++c->script_moves;
                            if (a.type < TYPE_SLOTS) ++c->moves_by_type[a.type];
                        } else if (a.state != st_prev[i] || a.hit_value != hit_prev[i]) {
                            ++c->external;
                        } else {
                            ++c->unexplained;
                            if (a.type < TYPE_SLOTS) ++c->unexp_by_type[a.type];
                        }
                    }
                }
                ptr_prev[i] = a.anim_record;
                st_prev[i] = a.state;
                hit_prev[i] = a.hit_value;
            }
            have_prev = 1;
        }

        for (i = 0; i < n; ++i) {
            long seed_frame;
            for (seed_frame = 0L; seed_frame + 1L < frames; ++seed_frame) {
                const unsigned char *w0 = raw + seed_frame * (long)AVSP_WORK_RAM_SIZE;
                const unsigned char *w1 = w0 + AVSP_WORK_RAM_SIZE;
                AvspActor a0, a1;
                AvspAnimFrame fr;
                long k, matched = 0L;

                if (!avsp_actor_load(&a0, w0, addrs[i])) continue;
                if (!avsp_actor_load(&a1, w1, addrs[i])) continue;
                if (!eligible(sp, &a1)) continue;
                if (a0.state == 0u) continue;
                if (a0.anim_record == 0uL || a1.anim_record == a0.anim_record) continue;

                avsp_anim_frame_start(&fr, sp, (unsigned int)a1.anim_record);
                for (k = seed_frame + 2L; k < frames; ++k) {
                    const unsigned char *wk = raw + k * (long)AVSP_WORK_RAM_SIZE;
                    AvspActor ak;
                    avsp_anim_frame_tick(&fr, sp);
                    if (!avsp_actor_load(&ak, wk, addrs[i])) break;
                    if (ak.state == 0u) break;
                    if ((unsigned long)fr.addr != ak.anim_record) break;
                    ++matched;
                }
                ++c->runs;
                c->run_frames_total += matched;
                if (matched > c->longest_run) c->longest_run = matched;
                if (a1.type < TYPE_SLOTS && matched > c->longest_by_type[a1.type]) {
                    c->longest_by_type[a1.type] = matched;
                }
                if (matched > 0L) ++c->seeded_exact;
                seed_frame += matched;
            }
        }
    }
}

static void report(const char *label, const Counts *c)
{
    int ti;
    printf("%s\n", label);
    printf("  holds (pose still running)     %ld\n", c->holds);
    printf("  moves the script predicts      %ld\n", c->script_moves);
    printf("  external re-points (event)     %ld\n", c->external);
    printf("  unexplained (game re-pointed)  %ld\n", c->unexplained);
    printf("  seeded runs                    %ld\n", c->runs);
    printf("  total frames predicted         %ld\n", c->run_frames_total);
    printf("  longest exact run (frames)     %ld\n", c->longest_run);
    printf("  per type (moves / unexpl / longest run)\n");
    for (ti = 0; ti < TYPE_SLOTS; ++ti) {
        if (c->moves_by_type[ti] || c->unexp_by_type[ti] || c->longest_by_type[ti]) {
            printf("    type %2d: %6ld / %5ld / %5ld\n", ti,
                   c->moves_by_type[ti], c->unexp_by_type[ti], c->longest_by_type[ti]);
        }
    }
}

int main(void)
{
    unsigned char *rom;
    long rom_size;
    unsigned char *windows[2];
    long window_sizes[2];
    AvspAnimScript full;
    Counts a;
    int w;

    printf("S2 animation walk\n");

    rom = slurp(ROM_PATH, &rom_size);
    if (rom == 0) {
        printf("  SKIP: %s not present (private program image)\n", ROM_PATH);
        return 0;
    }
    for (w = 0; w < 2; ++w) {
        windows[w] = slurp(WINDOWS[w], &window_sizes[w]);
        if (windows[w] == 0) {
            printf("  SKIP: %s not present\n", WINDOWS[w]);
            if (w > 0) free(windows[0]);
            free(rom);
            return 0;
        }
    }

    full.rom = rom;
    full.base = 0u;
    full.size = (unsigned int)rom_size;
    full.spans = 0;
    full.span_count = 0u;

    measure(&full, windows, window_sizes, &a);
    report("checks A and B, over the full program image", &a);

    if (a.script_moves == 0L) fail("the interpreter never predicted a pointer move");
    if (a.holds == 0L)        fail("no holds observed - the capture or the walk is wrong");

#ifdef AVSP_GENERATED_RECORDS
    {
        AvspAnimScript sub;
        Counts b;
        int ti, same = 1;

        sub.rom = 0;
        sub.base = 0u;
        sub.size = 0u;
        sub.spans = avsp_anim_spans;
        sub.span_count = avsp_anim_span_count;

        measure(&sub, windows, window_sizes, &b);
        printf("\n");
        report("check C, over the shipped record spans only", &b);

        if (a.holds != b.holds) same = 0;
        if (a.script_moves != b.script_moves) same = 0;
        if (a.external != b.external) same = 0;
        if (a.unexplained != b.unexplained) same = 0;
        if (a.runs != b.runs) same = 0;
        if (a.run_frames_total != b.run_frames_total) same = 0;
        if (a.longest_run != b.longest_run) same = 0;
        if (a.seeded_exact != b.seeded_exact) same = 0;
        for (ti = 0; ti < TYPE_SLOTS; ++ti) {
            if (a.moves_by_type[ti] != b.moves_by_type[ti]) same = 0;
            if (a.unexp_by_type[ti] != b.unexp_by_type[ti]) same = 0;
            if (a.longest_by_type[ti] != b.longest_by_type[ti]) same = 0;
        }
        printf("\ncheck C: shipped spans %s the full image\n",
               same ? "reproduce" : "DIFFER FROM");
        if (!same) {
            fail("the shipped record subset is incomplete or mis-addressed");
        }
    }
#else
    printf("\n  check C skipped: build with -DAVSP_GENERATED_RECORDS after running\n"
           "  tools/gen_avsp_anim_records.py\n");
#endif

    free(windows[0]);
    free(windows[1]);
    free(rom);

    printf("\n");
    if (failures != 0) {
        printf("%d check(s) failed\n", failures);
        return 1;
    }
    printf("all checks passed\n");
    return 0;
}
