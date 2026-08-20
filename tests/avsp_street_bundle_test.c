/* Host test for the STRIPS.BIN validator (avsp_street_bundle.c).
 *
 * Builds a small synthetic bundle in the v1 layout, checks the parser
 * accepts it and publishes the exact section offsets, then runs the
 * corrupt-input controls the RP4 correction contract requires: corrupt
 * magic, wrong schema version, short reads at every section boundary,
 * out-of-range plane offsets, oversized counts, a truncated patch list,
 * and a truncated object list. Every control must be rejected with the
 * expected section name. Each case runs against an exact-size heap copy
 * of the bundle, so under AddressSanitizer (test.ps1 compiles this test
 * with -fsanitize=address) any read outside the declared length aborts
 * the test instead of passing silently. */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../avsp_street_bundle.h"

#define MAX_FRAMES 256

static unsigned char buffer[8192];
static unsigned long frame_offsets[MAX_FRAMES];
static int failures;

static void put16(unsigned long at, unsigned int v)
{
    buffer[at] = (unsigned char)(v >> 8);
    buffer[at + 1] = (unsigned char)(v & 0xFF);
}

static void put32(unsigned long at, unsigned long v)
{
    put16(at, (unsigned int)(v >> 16));
    put16(at + 2, (unsigned int)(v & 0xFFFF));
}

/* Valid layout: header 8, plane headers 8..48, palettes 48..1072, cycle
 * header 1072..1078, 2 cycle entries 1078..1090, 3 frames of scroll
 * 1090..1114, patch section (1 patch, 2 cells) 1114..1134, 3 object
 * lists 1134..1160 (counts 1, 0, 1), then plane data: chars at 1160
 * (2 chars = 128 bytes for plane 0, 1 char = 64 for plane 1), PNTs. */
#define FRAMES 3
#define P0_CHARS 1160UL
#define P1_CHARS (P0_CHARS + 2UL * 64UL)
#define P0_PNT (P1_CHARS + 64UL)
#define P1_PNT (P0_PNT + 2UL * 2UL * 2UL)
#define TOTAL (long)(P1_PNT + 2UL * 1UL * 2UL)

/* For truncation controls on the variable sections: park both planes'
 * char and PNT data inside the fixed palette region so a tail cut hits
 * the section under test instead of the plane pools. */
static void point_planes_low(void)
{
    put32(20, 48UL); put32(24, 48UL);
    put32(40, 48UL); put32(44, 48UL);
}

static long build_valid(void)
{
    memset(buffer, 0, sizeof buffer);
    put32(0, 0x41565353UL);
    put16(4, 1);
    put16(6, FRAMES);
    /* plane 0: 2x2 cells, 2 chars */
    put16(8, 2);  put16(10, 2);  put16(12, 100); put16(14, 0);
    put16(16, 2); put32(20, P0_CHARS); put32(24, P0_PNT);
    /* plane 1: 2x1 cells, 1 char */
    put16(28, 2); put16(30, 1); put16(32, 50); put16(34, 0);
    put16(36, 1); put32(40, P1_CHARS); put32(44, P1_PNT);
    /* cycle header at 1072: period 8, first flip 4, 2 entries */
    put16(1072, 8); put16(1074, 4); put16(1076, 2);
    /* scroll table 1090; patch section 1114: count 1, patch header
       (frame_rel 1, plane 0, 2 cells) + 2 cells of 6 bytes */
    put16(1114, 1);
    put16(1116, 1); put16(1118, 0); put16(1120, 2);
    /* objects at 1134: counts 1, 0, 1 */
    put16(1134, 1);
    put16(1144, 0);
    put16(1146, 1);
    return TOTAL;
}

/* Run the parser over an exact-size heap copy so ASan catches any read
 * past the declared length. */
static int parse_exact(long bytes, AvspStreetBundle *bundle,
                       const char **name)
{
    unsigned char *copy = (unsigned char *)malloc(
        bytes > 0 ? (size_t)bytes : 1u);
    int ok;

    if (copy == (unsigned char *)0)
    {
        printf("FAIL out of memory\n");
        exit(1);
    }
    memcpy(copy, buffer, bytes > 0 ? (size_t)bytes : 0u);
    ok = avsp_street_bundle_parse(copy, bytes, bundle, frame_offsets,
                                  MAX_FRAMES, name);
    free(copy);
    return ok;
}

static void expect_reject(const char *label, long bytes,
                          const char *want_name)
{
    AvspStreetBundle bundle;
    const char *name = (const char *)0;
    int ok;

    bundle.frames = 77; /* must be scrubbed by a rejection */
    ok = parse_exact(bytes, &bundle, &name);
    if (ok || name == (const char *)0 || strcmp(name, want_name) != 0 ||
        bundle.frames != 0)
    {
        printf("FAIL %s: ok=%d name=%s (wanted reject '%s')\n",
               label, ok, name ? name : "(null)", want_name);
        ++failures;
        return;
    }
    printf("ok   %s -> rejected as '%s'\n", label, name);
}

int main(void)
{
    AvspStreetBundle bundle;
    const char *name = (const char *)0;
    long total = build_valid();
    long cut;

    if (!parse_exact(total, &bundle, &name))
    {
        printf("FAIL valid bundle rejected as '%s'\n",
               name ? name : "(null)");
        return 1;
    }
    if (bundle.frames != FRAMES || bundle.cycle_entries != 2 ||
        bundle.cycle_offset != 1078UL || bundle.scroll_offset != 1090UL ||
        bundle.patch_offset != 1114UL ||
        bundle.objects_offset != 1134UL ||
        frame_offsets[0] != 1134UL || frame_offsets[1] != 1144UL ||
        frame_offsets[2] != 1146UL)
    {
        printf("FAIL valid bundle offsets wrong: cycle=%lu scroll=%lu "
               "patch=%lu objects=%lu f0=%lu f1=%lu f2=%lu\n",
               bundle.cycle_offset, bundle.scroll_offset,
               bundle.patch_offset, bundle.objects_offset,
               frame_offsets[0], frame_offsets[1], frame_offsets[2]);
        ++failures;
    }
    else
        printf("ok   valid bundle accepted, all section offsets exact\n");

    /* Corrupt magic and version. */
    build_valid(); put32(0, 0x41565354UL);
    expect_reject("corrupt magic", total, "STRIPS.BIN");
    build_valid(); put16(4, 2);
    expect_reject("wrong schema version", total, "STRIPS.BIN");
    build_valid();
    expect_reject("empty read", 0, "STRIPS.BIN");
    expect_reject("header short read", 6, "STRIPS.BIN");

    /* Frame-count range. */
    build_valid(); put16(6, 0);
    expect_reject("zero frames", total, "STRIPS FRAMES");
    build_valid(); put16(6, MAX_FRAMES + 1);
    expect_reject("frame count over limit", total, "STRIPS FRAMES");

    /* Short reads at every fixed-section boundary. */
    build_valid();
    expect_reject("plane header short read", 30, "STRIPS PLANE");
    expect_reject("palette short read", 900, "STRIPS PALETTE");
    expect_reject("cycle header short read", 1075, "STRIPS CYCLE");

    /* Plane sanity and offset range. */
    build_valid(); put16(16, 0);
    expect_reject("zero char count", total, "STRIPS PLANE");
    build_valid(); put16(16, 2049);
    expect_reject("char count over limit", total, "STRIPS PLANE");
    build_valid(); put32(20, (unsigned long)total);
    expect_reject("char offset out of range", total, "STRIPS PLANE");
    build_valid(); put32(24, (unsigned long)total - 2);
    expect_reject("pnt grid out of range", total, "STRIPS PLANE");
    build_valid(); put32(44, 0xFFFFFFFFUL);
    expect_reject("pnt offset wraparound", total, "STRIPS PLANE");

    /* Variable-section counts running past the read. */
    build_valid(); put16(1076, 4000);
    expect_reject("cycle entries out of range", total, "STRIPS CYCLE");
    build_valid(); put16(1076, 0xFFFF);
    expect_reject("cycle entry overflow", total, "STRIPS CYCLE");
    /* Short reads inside the variable sections: repoint the plane data
       into the (always present) palette region first, so the truncation
       is caught by the section it actually cuts, not by the tail-resident
       plane pools. */
    build_valid(); point_planes_low();
    cut = 1100; /* inside the scroll table */
    expect_reject("scroll table short read", cut, "STRIPS SCROLL");
    build_valid(); put16(1114, 200);
    expect_reject("truncated patch list", total, "STRIPS PATCH");
    build_valid(); put16(1120, 10000);
    expect_reject("patch cell count out of range", total, "STRIPS PATCH");
    build_valid(); point_planes_low();
    expect_reject("patch section short read", 1115, "STRIPS PATCH");
    build_valid(); put16(1146, 500);
    expect_reject("truncated object list", total, "STRIPS OBJECTS");
    build_valid(); point_planes_low();
    expect_reject("object list short read", 1145, "STRIPS OBJECTS");
    build_valid(); put16(1134, 0xFFFF);
    expect_reject("object count overflow", total, "STRIPS OBJECTS");

    if (failures)
    {
        printf("street bundle test: %d FAILURES\n", failures);
        return 1;
    }
    printf("street bundle test: valid bundle + 23 corrupt/truncated "
           "controls all behave\n");
    return 0;
}
