/* S1 exit checks.
 *
 * "Gate" is reserved for Capability Gate 1, the seven-condition acceptance
 * contract in docs/PARITY_PLAN.md. A slice step's own criteria are "checks".
 *
 * Check 1: every field of the native actor record matches the captured work RAM
 *          it was loaded from, for every live actor across the capture windows.
 *
 * Check 2: the C port of the collision predicate and its guards reproduces the
 *         Python falsification EXACTLY over the same captures. The expected
 *         numbers come from tools/verify_avsp_collision.py:
 *           21908 non-overlapping active pairs, none of which produced a hit
 *              25 overlapping pairs that latched
 *              44 of 56 latch events explained (25 defender, 19 attacker)
 *               8 belonging to one simultaneous broadcast
 *               4 unexplained singles
 *         A different number here is a defect in this port, not a new finding.
 *
 * Inputs are private captures under .deps (git-ignored) plus the private
 * program image, which supplies the animation records' selector bytes. The
 * test skips with a clear message when they are absent, so the suite still runs
 * on a machine without them.
 *
 * C90.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../avsp_actor.h"
#include "../avsp_collision.h"

#define MAX_ACTORS 256

typedef struct {
    const char   *path;
    unsigned long first_frame;
} Window;

static const Window WINDOWS[2] = {
    { ".deps/mame/collision_probe/workram.bin",      4201uL },
    { ".deps/mame/collision_probe_boss/workram.bin", 13000uL }
};

static const char *ROM_PATH = ".deps/mame/actorprobe/decrypted_program_2m.bin";

static unsigned char *rom_data = 0;
static long rom_size = 0;

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
    if (f == 0) {
        return 0;
    }
    if (fseek(f, 0L, SEEK_END) != 0) { fclose(f); return 0; }
    size = ftell(f);
    if (size <= 0L) { fclose(f); return 0; }
    if (fseek(f, 0L, SEEK_SET) != 0) { fclose(f); return 0; }
    buf = (unsigned char *)malloc((size_t)size);
    if (buf == 0) { fclose(f); return 0; }
    if (fread(buf, 1u, (size_t)size, f) != (size_t)size) {
        free(buf); fclose(f); return 0;
    }
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

/* Check 1: re-read every field straight out of the image and compare. */
static void check_fields(const AvspActor *a, const unsigned char *work, unsigned long addr,
                         long *checked, long *mismatched)
{
    const unsigned char *p = work + (addr - AVSP_WORK_RAM_FIRST);
    int bad = 0;
    int i;

    if (a->state != p[0x00u]) bad = 1;
    if (a->class_id != p[0x02u]) bad = 1;
    if (a->sub_state != be16_at(p + 0x04u)) bad = 1;
    if (a->action_word != be16_at(p + 0x06u)) bad = 1;
    if (a->type != p[0x08u]) bad = 1;
    if (a->facing != p[0x0Fu]) bad = 1;
    if (a->world_x != be16_at(p + 0x10u)) bad = 1;
    if (a->world_y != be16_at(p + 0x14u)) bad = 1;
    if (a->world_z != be16_at(p + 0x18u)) bad = 1;
    if (a->anim_record != be32_at(p + 0x1Cu)) bad = 1;
    if (a->hit_value != p[0x2Cu]) bad = 1;
    if (a->hit_source != p[0x2Du]) bad = 1;
    if (a->table_set != be32_at(p + 0x50u)) bad = 1;
    if (a->attacker_id != p[0x67u]) bad = 1;
    for (i = 0; i < AVSP_ACTOR_LATCH_SLOTS; ++i) {
        if (a->latch[i] != p[0x68u + (unsigned long)i]) bad = 1;
    }
    if (a->suppress != p[0x70u]) bad = 1;
    if (a->latch_index != p[0xD1u]) bad = 1;

    *checked += 1L;
    if (bad) {
        *mismatched += 1L;
    }
}

static void fill_selectors(AvspActor *a)
{
    a->sel_hurt = 0u;
    a->sel_attack = 0u;
    if (rom_data != 0 && a->anim_record != 0uL
        && (long)(a->anim_record + 16uL) < rom_size) {
        a->sel_hurt   = rom_data[a->anim_record + 8uL];
        a->sel_attack = rom_data[a->anim_record + 9uL];
    }
}

int main(void)
{
    long field_checks = 0L, field_mismatches = 0L;
    long pairs_no_overlap = 0L, pairs_overlap_latched = 0L;
    long pairs_overlap_guarded = 0L, pairs_overlap_unguarded = 0L;
    long latch_defender = 0L, latch_attacker = 0L;
    long latch_broadcast = 0L, latch_unexplained = 0L;
    int w;
    unsigned long class_table_set;

    printf("S1 actor spine\n");

    if (!avsp_table_set_for_class(0x00u, &class_table_set)
        || class_table_set != 0x0012CE5CuL) {
        fail("class 0x00 table-set lookup");
    }
    if (!avsp_table_set_for_class(0x06u, &class_table_set)
        || class_table_set != 0x0013E97AuL) {
        fail("class 0x06 table-set lookup");
    }
    if (!avsp_table_set_for_class(0x1Fu, &class_table_set)
        || class_table_set != 0x00130AC8uL) {
        fail("class 0x1F table-set lookup");
    }
    class_table_set = 0xFFFFFFFFuL;
    if (avsp_table_set_for_class(0xFFu, &class_table_set)
        || class_table_set != 0xFFFFFFFFuL) {
        fail("unknown class table-set lookup");
    }

    rom_data = slurp(ROM_PATH, &rom_size);
    if (rom_data == 0) {
        printf("  SKIP: %s not present (private program image)\n", ROM_PATH);
        return 0;
    }

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
                    check_fields(&cur[i], work, addrs[i], &field_checks, &field_mismatches);
                    fill_selectors(&cur[i]);
                    /* Participation contract, identical to
                     * tools/verify_avsp_collision.py `actor()`: an actor takes
                     * part in collision only when it is in a live state and
                     * carries both a usable animation record and a usable
                     * table-set pointer. Without this the two implementations
                     * count different pair populations. */
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
                /* Whiff side and guard classification. */
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

                /* Hit side. Count this frame's latch events first so a
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

    printf("check 1: actor fields\n");
    printf("  actor loads checked      %ld\n", field_checks);
    printf("  field mismatches         %ld\n", field_mismatches);
    if (field_mismatches != 0L) fail("actor record does not match captured work RAM");
    if (field_checks < 10000L) fail("suspiciously few actor loads checked");

    printf("check 2: collision predicate in C\n");
    printf("  pairs, no overlap        %ld (expected 21908)\n", pairs_no_overlap);
    printf("  pairs, overlap latched   %ld (expected 25)\n", pairs_overlap_latched);
    printf("  pairs, overlap guarded   %ld (expected 2516)\n", pairs_overlap_guarded);
    printf("  pairs, overlap unguarded %ld (expected 24)\n", pairs_overlap_unguarded);
    printf("  latch explained defender %ld (expected 25)\n", latch_defender);
    printf("  latch explained attacker %ld (expected 19)\n", latch_attacker);
    printf("  latch broadcast          %ld (expected 8)\n", latch_broadcast);
    printf("  latch unexplained        %ld (expected 4)\n", latch_unexplained);

    if (pairs_no_overlap != 21908L)       fail("non-overlapping pair count differs from the Python falsification");
    if (pairs_overlap_latched != 25L)     fail("latched overlap count differs");
    if (pairs_overlap_guarded != 2516L)   fail("guarded overlap count differs");
    if (pairs_overlap_unguarded != 24L)   fail("unguarded non-latching overlap count differs");
    if (latch_defender != 25L)            fail("defender-side explained latches differ");
    if (latch_attacker != 19L)            fail("attacker-side explained latches differ");
    if (latch_broadcast != 8L)            fail("broadcast latches differ");
    if (latch_unexplained != 4L)          fail("unexplained latches differ");

    printf("\n");
    if (failures != 0) {
        printf("%d check(s) failed\n", failures);
        return 1;
    }
    printf("all checks passed\n");
    return 0;
}
