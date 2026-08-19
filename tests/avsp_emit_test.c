/* S2 check: the complete ROM-to-object pipeline (pose assembly -> selector
 * parse -> group headers -> origin routine -> both loop variants -> four-word
 * entries) reproduces the game's own object output exactly.
 *
 * Every expected value is a live-captured oracle entry from the game's own
 * object RAM (routes and provenance in docs/AGENT_HANDOFF.md); every input is
 * a plain actor-record/camera field plus the decrypted ROM image. Nothing
 * from the oracle feeds the calculation. The same algorithm passes the full
 * 6,010-instance corpus falsification with zero mismatches
 * (tools/verify_avsp_object_corpus.py).
 *
 * Covers: selector-6 single-group poses, the selector-12 two-group
 * composite, both loop variants (facing 1 flipped / facing 0 plain), and
 * three palettes.
 *
 * "Gate" means Capability Gate 1. This is a step check, not a gate.
 *
 * C90.
 */

#include <stdio.h>
#include <stdlib.h>

#include "../avsp_emit.h"

static const char *ROM_PATH = ".deps/mame/actorprobe/decrypted_program_2m.bin";

static int failures = 0;

static unsigned char *slurp(const char *path, unsigned long *size_out)
{
    FILE *f = fopen(path, "rb");
    unsigned char *buf;
    long n;

    if (f == 0) {
        return 0;
    }
    fseek(f, 0, SEEK_END);
    n = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (n <= 0) {
        fclose(f);
        return 0;
    }
    buf = (unsigned char *)malloc((unsigned long)n);
    if (buf != 0 && fread(buf, 1, (unsigned long)n, f) != (unsigned long)n) {
        free(buf);
        buf = 0;
    }
    fclose(f);
    *size_out = (unsigned long)n;
    return buf;
}

static void check_pose(const unsigned char *rom, unsigned long rom_size,
                       const char *label, unsigned long assembly,
                       const AvspEmitActor *actor,
                       const unsigned short *want, int want_count)
{
    AvspObjectEntry got[16];
    int n;
    int i;
    int bad = 0;

    n = avsp_emit_pose(rom, rom_size, assembly, actor, got, 16);
    if (n != want_count) {
        printf("  %-24s count=%d (want %d) FAIL\n", label, n, want_count);
        ++failures;
        return;
    }
    for (i = 0; i < n; ++i) {
        const unsigned short *w = want + i * 4;
        if (got[i].x != w[0] || got[i].y != w[1] ||
            got[i].code != w[2] || got[i].attr != w[3]) {
            printf("  %-24s entry %d: %04x %04x %04x %04x"
                   " (want %04x %04x %04x %04x) FAIL\n",
                   label, i, got[i].x, got[i].y, got[i].code, got[i].attr,
                   w[0], w[1], w[2], w[3]);
            bad = 1;
        }
    }
    if (bad) {
        ++failures;
    } else {
        printf("  %-24s %d entries exact OK\n", label, n);
    }
}

int main(void)
{
    unsigned long rom_size;
    unsigned char *rom = slurp(ROM_PATH, &rom_size);
    AvspEmitActor actor;

    if (rom == 0) {
        printf("SKIP: %s not present (dependency capture)\n", ROM_PATH);
        return 0;
    }

    printf("S2 ROM-to-object emission pipeline\n");

    /* Street alien 0xFF9DC0, source frame 4214: selector-12 composite,
     * two groups, five entries. Actor fields from the route-matched capture;
     * camera anchors are the street-window values at 0xFF8278/0xFF827C. */
    actor.world_x = 1257; actor.world_y = 310;
    actor.facing = 1; actor.palette = 0x11;
    actor.or_value = 0x8000;
    actor.anchor_x = 0x03F0; actor.anchor_y = 0x00FF;
    {
        static const unsigned short want[] = {
            0x8113, 0x0099, 0x4EFE, 0x0131,
            0x80E3, 0x00A9, 0x4EF6, 0x0431,
            0x80F3, 0x00B9, 0x4FC8, 0x0131,
            0x8121, 0x007B, 0x473A, 0x2431,
            0x8111, 0x00AB, 0x479C, 0x1331,
        };
        check_pose(rom, rom_size, "4214 composite (5)", 0x12F72Aul, &actor,
                   want, 5);
    }

    /* Same actor, source frame 4253 (anti-hardcoding control pose). */
    actor.world_x = 1313; actor.world_y = 310;
    {
        static const unsigned short want[] = {
            0x814F, 0x009E, 0x4DF8, 0x0131,
            0x810F, 0x00AE, 0x4EF0, 0x0531,
            0x815B, 0x007B, 0x4B04, 0x2531,
            0x814B, 0x00AB, 0x4A88, 0x1431,
            0x816B, 0x006B, 0x4958, 0x0131,
        };
        check_pose(rom, rom_size, "4253 composite (5)", 0x12FEBCul, &actor,
                   want, 5);
    }

    /* Second, independent actor 0xFFA000: selector-6 single group, other
     * palette, flipped loop. */
    actor.world_x = 1181; actor.world_y = 297;
    actor.facing = 1; actor.palette = 0x10;
    {
        static const unsigned short want[] = {
            0x8085, 0x00C8, 0x46F0, 0x0930,
            0x8095, 0x0098, 0x5060, 0x2630,
        };
        check_pose(rom, rom_size, "actor2 single (2)", 0x12F7CCul, &actor,
                   want, 2);
    }

    /* Third actor 0xFFA0C0, facing 0: the PLAIN (non-flipped) loop -
     * X = origin + dx, no width term, no flip XOR. Oracle entries from the
     * enemy_actions route at source frame 4491 (objram 4492). */
    actor.world_x = 1387; actor.world_y = 241;
    actor.facing = 0; actor.palette = 0x13;
    {
        static const unsigned short want[] = {
            0x8183, 0x0100, 0x46F0, 0x0913,
            0x81A3, 0x00D0, 0x5060, 0x2613,
        };
        check_pose(rom, rom_size, "facing0 single (2)", 0x12F7CCul, &actor,
                   want, 2);
    }

    /* Family-0x0002 records (inline code/attr, single entry each), all
     * corpus-verified against the game's own object RAM. The 2+2 pose at
     * 0x12F5DE is the record that was undecodable before the family-2
     * handler (0x0A9D52) was live-disassembled. */
    actor.world_x = 1292; actor.world_y = 258;
    actor.facing = 1; actor.palette = 0x10;
    {
        static const unsigned short want[] = {
            0x8105, 0x00C7, 0x463D, 0x2230,
            0x8116, 0x00CF, 0x4605, 0x2730,
        };
        check_pose(rom, rom_size, "family2 2+2 (2)", 0x12F5DEul, &actor,
                   want, 2);
    }

    /* Mixed composite: family-6 group then a family-2 record. */
    actor.world_x = 1005; actor.world_y = 334;
    actor.facing = 1; actor.palette = 0x10;
    {
        static const unsigned short want[] = {
            0x83E4, 0x006C, 0x4EFB, 0x0230,
            0x83E4, 0x007C, 0x4BEA, 0x1130,
            0x83D5, 0x0083, 0x4850, 0x2730,
        };
        check_pose(rom, rom_size, "mixed 6x2+2 (3)", 0x12F890ul, &actor,
                   want, 3);
    }

    /* Mixed composite the other way: family-2 then a family-6 group. */
    actor.world_x = 1331; actor.world_y = 308;
    actor.facing = 1; actor.palette = 0x11;
    {
        static const unsigned short want[] = {
            0x812E, 0x009B, 0x4FC0, 0x1431,
            0x816D, 0x006D, 0x499B, 0x2431,
            0x815D, 0x009D, 0x4696, 0x2531,
        };
        check_pose(rom, rom_size, "mixed 2+6x2 (3)", 0x12FD0Aul, &actor,
                   want, 3);
    }

    /* Undecoded layouts must be reported, never guessed at. 0x12F72E holds
     * a record's budget word (0x0009), not a valid top word. */
    {
        AvspObjectEntry tmp[4];
        int n = avsp_emit_pose(rom, rom_size, 0x12F72Eul, &actor, tmp, 4);
        if (n != -1) {
            printf("  unknown top word: got %d (want -1) FAIL\n", n);
            ++failures;
        } else {
            printf("  unknown top word rejected OK\n");
        }
    }

    free(rom);
    printf("\n");
    if (failures != 0) {
        printf("%d check(s) failed\n", failures);
        return 1;
    }
    printf("all checks passed\n");
    return 0;
}
