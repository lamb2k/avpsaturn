/* Step 4 host falsification: the runtime's input-assembly path, not just the
 * collision library, reproduces the S1 predicate's known contact set.
 *
 * "Gate" means Capability Gate 1. A slice step's own criteria are "checks".
 *
 * tests/avsp_actor_test.c proves the C port of the game's collision predicate
 * (overlap + guards + latch classification) reproduces the Python
 * falsification EXACTLY over the private collision_probe captures, with the
 * selectors assembled the test's own way: read straight off the program image
 * at record+8/+9, and table_set taken from the actor's captured +0x50.
 *
 * This test replays that SAME predicate over those SAME captures, but for the
 * street walk/attack type-12 aliens it drives the collision inputs the way the
 * runtime (main.c rom_actor_tick) now does:
 *   - table_set is the gated constant 0x00130AC8 (Step 1's gate,
 *     data/avsp_table_set_gate.json + data/avsp_table_set_source.json), and
 *   - the selectors come off the live animation record through the anim-script
 *     span view: avsp_anim_resolve(record, 10)[8]/[9], over the same stored
 *     record spans the runtime loads (the generated record subset when built
 *     with -DAVSP_GENERATED_RECORDS, else the full program image).
 * Every other actor keeps the library assembly.
 *
 * Two assertions:
 *
 * Check A - input identity. For every street walk/attack type-12 actor-frame
 *   the runtime assembly must yield the same table_set and the same selector
 *   bytes as the library assembly. Zero mismatches. This is the falsification
 *   of the wiring itself: if the gate's constant were wrong on a single street
 *   frame, or the span view resolved a different selector byte (or failed to
 *   resolve a street record at all), it appears here as a mismatch. A zero
 *   street population is a vacuous failure, not a pass.
 *
 * Check B - the known contact set reproduces. The full predicate over the
 *   runtime-assembled inputs still counts the exact S1 numbers. A different
 *   number is a defect in this port's input path, not a new finding.
 *
 * The street population is the gate's: an active (state 1) type-12 actor whose
 * live record pointer (+0x1C) lies in the walk (0x12EB4C) or attack (0x12D8A0)
 * span, reached by walking the ROM's own control flow. No correlation, no
 * spawn_type.
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
#include "../avsp_collision.h"

#ifdef AVSP_GENERATED_RECORDS
#include "../generated/avsp_anim_records.h"
#endif

#define MAX_ACTORS 256
#define MAX_SPAN   512

#define STREET_TABLE_SET 0x00130AC8uL
#define WALK_SEED        0x12EB4CuL
#define ATTACK_SEED      0x12D8A0uL
#define TARGET_TYPE      12
#define JUMP_REC         20uL

typedef struct {
    const char   *path;
    unsigned long first_frame;
} Window;

static const Window WINDOWS[2] = {
    { ".deps/mame/collision_probe/workram.bin",      4201uL },
    { ".deps/mame/collision_probe_boss/workram.bin", 13000uL }
};

static const char *ROM_PATH = ".deps/mame/actorprobe/decrypted_program_2m.bin";

/* Per-street-frame identity between the runtime assembly and the library
 * assembly (check A). */
typedef struct {
    long street_frames;
    long ts_mismatch;
    long hurt_mismatch;
    long attack_mismatch;
} Identity;

static unsigned char *rom_data = 0;
static long rom_size = 0;
static AvspAnimScript g_script;
static unsigned long street_span[MAX_SPAN];
static int street_span_count = 0;

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

static unsigned short be16_at(const unsigned char *p)
{
    return (unsigned short)(((unsigned short)p[0] << 8) | (unsigned short)p[1]);
}

static unsigned long be32_at(const unsigned char *p)
{
    return ((unsigned long)p[0] << 24) | ((unsigned long)p[1] << 16)
         | ((unsigned long)p[2] << 8)  | (unsigned long)p[3];
}

static int in_span(unsigned long a)
{
    int i;
    for (i = 0; i < street_span_count; ++i) {
        if (street_span[i] == a) return 1;
    }
    return 0;
}

/* Record addresses reachable from `seed` following the script's own control
 * flow (16-byte advance; 20-byte jump to the u32 at +16 when flags bit 15 is
 * set) - the same walker as tools/gate_avsp_table_set.py loop_span and
 * avsp_anim_next_address. Appends to street_span with de-duplication, so the
 * walk and attack loops union into one set just as the gate forms it. */
static void add_span(unsigned long seed)
{
    unsigned long stack[MAX_SPAN];
    int top = 0;

    stack[top++] = seed;
    while (top > 0) {
        unsigned long a = stack[--top];
        unsigned long nxt;
        if (in_span(a)) continue;
        if ((long)(a + JUMP_REC) > rom_size) continue;
        if (street_span_count < MAX_SPAN)
            street_span[street_span_count++] = a;
        if (be16_at(rom_data + a + 2uL) & 0x8000u)
            nxt = be32_at(rom_data + a + 16uL);
        else
            nxt = a + 16uL;
        if (nxt > 0uL && (long)(nxt + JUMP_REC) <= rom_size && !in_span(nxt)) {
            if (top < MAX_SPAN)
                stack[top++] = nxt;
        }
    }
}

/* The script the span view resolves against: the stored record spans the
 * runtime loads, or the full program image when they are not built in. */
static void set_up_script(void)
{
#ifdef AVSP_GENERATED_RECORDS
    g_script.rom = 0;
    g_script.base = 0u;
    g_script.size = 0u;
    g_script.spans = avsp_anim_spans;
    g_script.span_count = avsp_anim_span_count;
#else
    g_script.rom = rom_data;
    g_script.base = 0u;
    g_script.size = (unsigned int)rom_size;
    g_script.spans = 0;
    g_script.span_count = 0u;
#endif
}

/* The gate's street population: active type-12 whose record pointer is in the
 * walk/attack span. */
static int is_street(const AvspActor *a)
{
    if (a->state != 1u) return 0;
    if (a->type != TARGET_TYPE) return 0;
    return in_span(a->anim_record);
}

/* Fill the selectors the library way (straight off the program image). */
static void fill_library_selectors(AvspActor *a)
{
    a->sel_hurt = 0u;
    a->sel_attack = 0u;
    if (rom_data != 0 && a->anim_record != 0uL
        && (long)(a->anim_record + 16uL) < rom_size) {
        a->sel_hurt   = rom_data[a->anim_record + 8uL];
        a->sel_attack = rom_data[a->anim_record + 9uL];
    }
}

/* Assemble this actor's collision inputs. Non-street actors keep the library
 * path (captured table_set, image selectors). Street walk/attack type-12
 * aliens are driven the runtime way (gated constant table_set, span-view
 * selectors) and their runtime values are compared against the library values
 * for check A. On return the actor's fields hold the runtime values either
 * way, which is what check B's predicate consumes. */
static void assemble_inputs(AvspActor *a, Identity *id)
{
    unsigned long lib_ts;
    unsigned char lib_hurt, lib_attack;
    const unsigned char *rec;

    fill_library_selectors(a);
    lib_hurt = a->sel_hurt;
    lib_attack = a->sel_attack;
    lib_ts = a->table_set;

    if (!is_street(a))
        return;

    ++id->street_frames;
    a->table_set = STREET_TABLE_SET;
    rec = avsp_anim_resolve(&g_script, (unsigned int)a->anim_record, 10u);
    a->sel_hurt = (rec != 0) ? rec[8u] : 0u;
    a->sel_attack = (rec != 0) ? rec[9u] : 0u;

    if (a->table_set != lib_ts) ++id->ts_mismatch;
    if (a->sel_hurt != lib_hurt) ++id->hurt_mismatch;
    if (a->sel_attack != lib_attack) ++id->attack_mismatch;
}

int main(void)
{
    long pairs_no_overlap = 0L, pairs_overlap_latched = 0L;
    long pairs_overlap_guarded = 0L, pairs_overlap_unguarded = 0L;
    long latch_defender = 0L, latch_attacker = 0L;
    long latch_broadcast = 0L, latch_unexplained = 0L;
    Identity id;
    int w;

    printf("Step 4: runtime input-assembly\n");

    memset(&id, 0, sizeof(id));

    rom_data = slurp(ROM_PATH, &rom_size);
    if (rom_data == 0) {
        printf("  SKIP: %s not present (private program image)\n", ROM_PATH);
        return 0;
    }

    add_span(WALK_SEED);
    add_span(ATTACK_SEED);
    set_up_script();
    printf("  street span records=%d\n", street_span_count);

    for (w = 0; w < 2; ++w) {
        unsigned char *raw;
        long raw_size;
        long frames, f;
        AvspActor cur[MAX_ACTORS], prev[MAX_ACTORS];
        unsigned long addrs[MAX_ACTORS];
        int live_cur[MAX_ACTORS], live_prev[MAX_ACTORS];
        int n = 0;
        unsigned long addr;
        int have_prev = 0;

        raw = slurp(WINDOWS[w].path, &raw_size);
        if (raw == 0) {
            printf("  SKIP: %s not present\n", WINDOWS[w].path);
            free(rom_data);
            return 0;
        }
        frames = raw_size / (long)AVSP_WORK_RAM_SIZE;

        for (addr = AVSP_ACTOR_GRID_ANCHOR;
             addr + AVSP_ACTOR_STRIDE <= AVSP_WORK_RAM_FIRST + AVSP_WORK_RAM_SIZE
             && n < MAX_ACTORS;
             addr += AVSP_ACTOR_STRIDE) {
            addrs[n++] = addr;
        }

        for (f = 0L; f < frames; ++f) {
            const unsigned char *work = raw + f * (long)AVSP_WORK_RAM_SIZE;
            int i, j;
            int events = 0, broadcast = 0;
            unsigned char broadcast_value = 0u;

            for (i = 0; i < n; ++i) {
                live_cur[i] = avsp_actor_load(&cur[i], work, addrs[i]);
                if (live_cur[i]) {
                    assemble_inputs(&cur[i], &id);
                    /* Participation contract, identical to
                     * tools/verify_avsp_collision.py `actor()` and
                     * tests/avsp_actor_test.c: an actor takes part in
                     * collision only when it is in a live state and carries
                     * both a usable animation record and a usable table-set
                     * pointer. */
                    if (cur[i].state == 0u
                        || cur[i].anim_record == 0uL
                        || cur[i].table_set == 0uL
                        || (long)(cur[i].anim_record + 16uL) > rom_size
                        || (long)(cur[i].table_set + 4uL) > rom_size) {
                        live_cur[i] = 0;
                    }
                }
            }

            if (have_prev) {
                /* Whiff side and guard classification (S1 predicate). */
                for (i = 0; i < n; ++i) {
                    if (!live_cur[i] || cur[i].sel_attack == 0u) continue;
                    for (j = 0; j < n; ++j) {
                        unsigned char v = 0u;
                        if (j == i || !live_cur[j] || cur[j].sel_hurt == 0u) continue;
                        if (!avsp_collision_overlap(&cur[i], &cur[j], &v)) {
                            ++pairs_no_overlap;
                        } else if (live_prev[j] && prev[j].hit_value == 0u
                                   && cur[j].hit_value == v) {
                            ++pairs_overlap_latched;
                        } else if (avsp_collision_guarded(&cur[i], &cur[j])) {
                            ++pairs_overlap_guarded;
                        } else {
                            ++pairs_overlap_unguarded;
                        }
                    }
                }

                /* Hit side: count this frame's latch events first so a
                 * simultaneous same-value broadcast can be separated. */
                for (i = 0; i < n; ++i) {
                    if (!live_cur[i] || !live_prev[i]) continue;
                    if (prev[i].hit_value == 0u && cur[i].hit_value != 0u) {
                        if (events == 0) {
                            broadcast_value = cur[i].hit_value;
                            broadcast = 1;
                        } else if (cur[i].hit_value != broadcast_value) {
                            broadcast = 0;
                        }
                        ++events;
                    }
                }
                if (events < 3) {
                    broadcast = 0;
                }

                for (i = 0; i < n; ++i) {
                    int role = 0; /* 1 defender, 2 attacker */
                    unsigned char value;
                    if (!live_cur[i] || !live_prev[i]) continue;
                    if (!(prev[i].hit_value == 0u && cur[i].hit_value != 0u)) continue;
                    value = cur[i].hit_value;

                    for (j = 0; j < n && role == 0; ++j) {
                        unsigned char v = 0u;
                        if (j == i) continue;
                        if (live_prev[j] && live_prev[i]
                            && avsp_collision_overlap(&prev[j], &prev[i], &v) && v == value) {
                            role = 1;
                        }
                        v = 0u;
                        if (role == 0 && live_cur[j]
                            && avsp_collision_overlap(&cur[j], &cur[i], &v) && v == value) {
                            role = 1;
                        }
                        v = 0u;
                        if (role == 0 && live_prev[j] && live_prev[i]
                            && avsp_collision_overlap(&prev[i], &prev[j], &v) && v == value) {
                            role = 2;
                        }
                        v = 0u;
                        if (role == 0 && live_cur[j]
                            && avsp_collision_overlap(&cur[i], &cur[j], &v) && v == value) {
                            role = 2;
                        }
                    }

                    if (role == 1) ++latch_defender;
                    else if (role == 2) ++latch_attacker;
                    else if (broadcast) ++latch_broadcast;
                    else ++latch_unexplained;
                }
            }

            memcpy(prev, cur, sizeof(prev));
            memcpy(live_prev, live_cur, sizeof(live_prev));
            have_prev = 1;
        }
        free(raw);
    }
    free(rom_data);

    printf("check A: runtime input-assembly identity\n");
    printf("  street walk/attack type-12 actor-frames %ld\n", id.street_frames);
    printf("  table_set mismatches   %ld (expected 0)\n", id.ts_mismatch);
    printf("  sel_hurt   mismatches  %ld (expected 0)\n", id.hurt_mismatch);
    printf("  sel_attack mismatches  %ld (expected 0)\n", id.attack_mismatch);
    if (id.street_frames == 0L) fail("vacuous: no street walk/attack type-12 actor-frame observed");
    if (id.ts_mismatch != 0L)   fail("gated constant table_set differs from the captured value on a street frame");
    if (id.hurt_mismatch != 0L) fail("span-view sel_hurt differs from the program-image byte on a street frame");
    if (id.attack_mismatch != 0L) fail("span-view sel_attack differs from the program-image byte on a street frame");

    printf("check B: known contact set via runtime inputs\n");
    printf("  pairs, no overlap        %ld (expected 21908)\n", pairs_no_overlap);
    printf("  pairs, overlap latched   %ld (expected 25)\n", pairs_overlap_latched);
    printf("  pairs, overlap guarded   %ld (expected 2516)\n", pairs_overlap_guarded);
    printf("  pairs, overlap unguarded %ld (expected 24)\n", pairs_overlap_unguarded);
    printf("  latch explained defender %ld (expected 25)\n", latch_defender);
    printf("  latch explained attacker %ld (expected 19)\n", latch_attacker);
    printf("  latch broadcast          %ld (expected 8)\n", latch_broadcast);
    printf("  latch unexplained        %ld (expected 4)\n", latch_unexplained);

    if (pairs_no_overlap != 21908L)      fail("non-overlapping pair count differs from the library-assembly run");
    if (pairs_overlap_latched != 25L)    fail("latched overlap count differs");
    if (pairs_overlap_guarded != 2516L)  fail("guarded overlap count differs");
    if (pairs_overlap_unguarded != 24L)  fail("unguarded non-latching overlap count differs");
    if (latch_defender != 25L)           fail("defender-side explained latches differ");
    if (latch_attacker != 19L)           fail("attacker-side explained latches differ");
    if (latch_broadcast != 8L)           fail("broadcast latches differ");
    if (latch_unexplained != 4L)         fail("unexplained latches differ");

    printf("\n");
    if (failures != 0) {
        printf("%d check(s) failed\n", failures);
        return 1;
    }
    printf("all checks passed\n");
    return 0;
}
