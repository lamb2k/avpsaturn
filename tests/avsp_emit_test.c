/* S2 partial check: the object-entry X/Y formula reproduces the game's own
 * output for the parts where the ROM part-table walk is understood. dx/dy are
 * read from decrypted_program_2m.bin at live-confirmed table addresses;
 * origin/or_value come from route-matched live capture; code/attr are supplied
 * from the captured oracle. This is not yet a complete ROM-to-object decoder.
 *
 * "Gate" means Capability Gate 1. This is a step check, not a gate.
 *
 * Covers 3 of the street alien's 5 observed object entries at source frame
 * 4214 (entries 0-2). Two source entries lie between observed entries 2 and 3,
 * but the narrow watchpoint evidence cannot prove whether they emitted outside
 * the watched range or were conditionally suppressed. See avsp_emit.h and
 * docs/AGENT_HANDOFF.md. Deriving origin from world state is separate from
 * this test.
 *
 * C90.
 */

#include <stdio.h>

#include "../avsp_emit.h"

static int failures = 0;

static void check_part(const char *label, unsigned short origin_x, unsigned short origin_y,
                       short dx, short dy, unsigned short code, unsigned short attr,
                       unsigned short or_value, unsigned short want_x, unsigned short want_y)
{
    AvspObjectEntry w;
    avsp_emit_part_flipped(origin_x, origin_y, dx, dy, code, attr, or_value, &w);
    printf("  %-8s X=%04x (want %04x) %s   Y=%04x (want %04x) %s\n",
           label, w.x, want_x, (w.x == want_x) ? "OK" : "FAIL",
           w.y, want_y, (w.y == want_y) ? "OK" : "FAIL");
    if (w.x != want_x || w.y != want_y) {
        ++failures;
    }
}

int main(void)
{
    /* Frame 4214, actor 0xFF9DC0, origin (259,201), or_value 0x8000 - all
     * confirmed live via tools/mame_probe_emitter_pc.lua (untracked
     * diagnostic). dx/dy read from the ROM's own per-part table at the
     * confirmed addresses; code/attr are the oracle's own known values,
     * supplied here as inputs (not computed) since resolving attr from the
     * raw part-table long is part of the still-open part-table walk. */
    printf("S2 object-entry geometry formula\n");

    check_part("part0", 259, 201, -48, -48, 0x4EFE, 0x0131, 0x8000, 0x8113, 0x0099);
    check_part("part1", 259, 201, -48, -32, 0x4EF6, 0x0431, 0x8000, 0x80E3, 0x00A9);
    check_part("part2", 259, 201, -16, -16, 0x4FC8, 0x0131, 0x8000, 0x80F3, 0x00B9);

    printf("\n");
    if (failures != 0) {
        printf("%d check(s) failed\n", failures);
        return 1;
    }
    printf("all checks passed\n");
    return 0;
}
