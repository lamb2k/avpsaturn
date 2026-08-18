/* S2 exit check: the object-word formula reproduces the game's own output,
 * computed from ROM data alone (dx/dy read from decrypted_program_2m.bin at
 * live-confirmed table addresses), for the parts where the full ROM part-
 * table walk is understood.
 *
 * "Gate" means Capability Gate 1. This is a step check, not a gate.
 *
 * Covers 3 of the street alien's 5 rendered parts at source frame 4214 (parts
 * 0-2; the part-table walk for parts 3-4 has a confirmed, documented gap - a
 * conditional part-skip not yet located, see avsp_emit.h and
 * docs/AGENT_HANDOFF.md). origin_x/origin_y and or_value (actor +0x2E) are
 * taken from live capture, not derived by this test; deriving them from world
 * state is a separate, undecoded routine.
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
    AvspObjectWord w;
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
    printf("S2 object-word formula\n");

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
